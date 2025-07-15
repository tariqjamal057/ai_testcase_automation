import os
import re
import ast
from pathlib import Path

class AngularExtractor:
    """Extracts Angular components, services, and functions for test generation."""
    
    def extract_angular_functions(self, repo_path):
        """
        Extract Angular components, services, and methods from TypeScript files.
        
        Args:
            repo_path (str): Path to the repository
            
        Returns:
            dict: Functions grouped by file path
        """
        functions_by_file = {}
        
        # Find TypeScript files (excluding test files and node_modules)
        ts_files = self._find_typescript_files(repo_path)
        
        for ts_file in ts_files:
            try:
                functions = self._extract_from_typescript_file(ts_file)
                if functions:
                    functions_by_file[ts_file] = functions
            except Exception as e:
                print(f"Error processing {ts_file}: {e}")
                continue
        
        return functions_by_file
    
    def _find_typescript_files(self, repo_path):
        """Find relevant TypeScript files for testing."""
        ts_files = []
        
        # Common Angular source directories
        source_dirs = ['src/app', 'src', 'app']
        
        for source_dir in source_dirs:
            full_source_path = os.path.join(repo_path, source_dir)
            if os.path.exists(full_source_path):
                # Find .ts files but exclude .spec.ts and .test.ts
                for ts_file in Path(full_source_path).rglob('*.ts'):
                    if not any(pattern in str(ts_file) for pattern in [
                        '.spec.ts', '.test.ts', 'node_modules', '.d.ts'
                    ]):
                        ts_files.append(str(ts_file))
        
        return ts_files
    
    def _extract_from_typescript_file(self, file_path):
        """Extract Angular components, services, and methods from a TypeScript file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
        
        functions = []
        
        # Extract Angular components
        component_matches = re.finditer(
            r'@Component\s*\(\s*{[^}]*}\s*\)\s*export\s+class\s+(\w+)',
            content,
            re.MULTILINE | re.DOTALL
        )
        
        for match in component_matches:
            class_name = match.group(1)
            class_info = self._extract_class_info(content, class_name, 'component')
            if class_info:
                functions.append(class_info)
        
        # Extract Angular services
        service_matches = re.finditer(
            r'@Injectable\s*\(\s*{[^}]*}\s*\)\s*export\s+class\s+(\w+)',
            content,
            re.MULTILINE | re.DOTALL
        )
        
        for match in service_matches:
            class_name = match.group(1)
            class_info = self._extract_class_info(content, class_name, 'service')
            if class_info:
                functions.append(class_info)
        
        # Extract regular classes and functions
        class_matches = re.finditer(
            r'export\s+class\s+(\w+)',
            content
        )
        
        for match in class_matches:
            class_name = match.group(1)
            # Skip if already processed as component or service
            if not any(f['name'] == class_name for f in functions):
                class_info = self._extract_class_info(content, class_name, 'class')
                if class_info:
                    functions.append(class_info)
        
        # Extract standalone functions
        function_matches = re.finditer(
            r'export\s+function\s+(\w+)\s*\([^)]*\)',
            content
        )
        
        for match in function_matches:
            func_name = match.group(1)
            func_info = self._extract_function_info(content, func_name)
            if func_info:
                functions.append(func_info)
        
        return functions
    
    def _extract_class_info(self, content, class_name, class_type):
        """Extract information about an Angular class."""
        # Find the class definition
        class_pattern = rf'export\s+class\s+{re.escape(class_name)}[^{{]*{{'
        class_match = re.search(class_pattern, content)
        
        if not class_match:
            return None
        
        # Find the class body
        start_pos = class_match.end() - 1  # Position of opening brace
        class_body = self._extract_class_body(content, start_pos)
        
        # Extract methods from the class
        methods = self._extract_methods_from_class(class_body)
        
        # Extract imports and dependencies
        imports = self._extract_imports(content)
        
        return {
            'name': class_name,
            'type': class_type,
            'methods': methods,
            'source_code': class_body,
            'imports': imports,
            'framework': 'angular'
        }
    
    def _extract_function_info(self, content, func_name):
        """Extract information about a standalone function."""
        func_pattern = rf'export\s+function\s+{re.escape(func_name)}\s*\([^)]*\)[^{{]*{{'
        func_match = re.search(func_pattern, content)
        
        if not func_match:
            return None
        
        # Extract function body
        start_pos = func_match.end() - 1
        func_body = self._extract_function_body(content, start_pos)
        
        # Extract parameters
        param_pattern = rf'function\s+{re.escape(func_name)}\s*\(([^)]*)\)'
        param_match = re.search(param_pattern, content)
        params = param_match.group(1).strip() if param_match else ''
        
        return {
            'name': func_name,
            'type': 'function',
            'args': params,
            'source_code': func_body,
            'framework': 'angular'
        }
    
    def _extract_class_body(self, content, start_pos):
        """Extract the complete class body using brace matching."""
        brace_count = 1
        pos = start_pos + 1
        
        while pos < len(content) and brace_count > 0:
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        return content[start_pos:pos] if brace_count == 0 else content[start_pos:]
    
    def _extract_function_body(self, content, start_pos):
        """Extract function body using brace matching."""
        return self._extract_class_body(content, start_pos)
    
    def _extract_methods_from_class(self, class_body):
        """Extract method information from class body."""
        methods = []
        
        # Pattern for methods (including async, private, public, etc.)
        method_pattern = r'(async\s+)?(private\s+|public\s+|protected\s+)?(\w+)\s*\([^)]*\)\s*[:{]'
        
        for match in re.finditer(method_pattern, class_body):
            method_name = match.group(3)
            # Skip constructor and common lifecycle methods for now
            if method_name not in ['constructor', 'ngOnInit', 'ngOnDestroy']:
                methods.append({
                    'name': method_name,
                    'is_async': bool(match.group(1)),
                    'visibility': match.group(2).strip() if match.group(2) else 'public'
                })
        
        return methods
    
    def _extract_imports(self, content):
        """Extract import statements from the file."""
        imports = []
        import_pattern = r'import\s+{[^}]+}\s+from\s+[\'"][^\'"]+[\'"]'
        
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(0))
        
        return imports
