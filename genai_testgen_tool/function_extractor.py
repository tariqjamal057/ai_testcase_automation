import ast
import os
import re
from typing import Dict, List, Any

class FunctionExtractor:
    """Extracts functions from source code files."""
    
    def __init__(self):
        self.flask_indicators = [
            'Flask(__name__)',
            'app = Flask',
            '@app.route',
            'from flask import',
            'flask.Flask'
        ]
        self.django_indicators = [
            'from django',
            'django.http',
            'HttpResponse',
            'render',
            'redirect'
        ]
        self.fastapi_indicators = [
            'from fastapi',
            'FastAPI()',
            'app = FastAPI',
            '@app.get',
            '@app.post'
        ]
    
    def _detect_framework_from_code(self, content: str) -> str:
        """Detect framework based on code content."""
        content_lower = content.lower()
        
        flask_score = sum(1 for indicator in self.flask_indicators if indicator.lower() in content_lower)
        django_score = sum(1 for indicator in self.django_indicators if indicator.lower() in content_lower)
        fastapi_score = sum(1 for indicator in self.fastapi_indicators if indicator.lower() in content_lower)
        
        if flask_score > 0:
            return 'flask'
        elif django_score > 0:
            return 'django'
        elif fastapi_score > 0:
            return 'fastapi'
        else:
            return 'general'
    
    def _is_flask_endpoint(self, node: ast.FunctionDef, content: str) -> bool:
        """Check if a function is a Flask endpoint."""
        # Check for route decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ['route', 'get', 'post', 'put', 'delete', 'patch']:
                        return True
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr in ['route', 'get', 'post', 'put', 'delete', 'patch']:
                    return True
        
        # Check function content for Flask patterns
        func_source = self._get_function_source(content, node)
        flask_patterns = [
            'request.',
            'session.',
            'render_template',
            'redirect',
            'url_for',
            'jsonify',
            'make_response'
        ]
        
        return any(pattern in func_source for pattern in flask_patterns)
    
    def _is_django_view(self, node: ast.FunctionDef, content: str) -> bool:
        """Check if a function is a Django view."""
        # Check function signature for request parameter
        if node.args.args and node.args.args[0].arg == 'request':
            return True
        
        # Check function content for Django patterns
        func_source = self._get_function_source(content, node)
        django_patterns = [
            'HttpResponse',
            'render',
            'redirect',
            'JsonResponse',
            'request.',
            'get_object_or_404'
        ]
        
        return any(pattern in func_source for pattern in django_patterns)
    
    def _is_fastapi_endpoint(self, node: ast.FunctionDef, content: str) -> bool:
        """Check if a function is a FastAPI endpoint."""
        # Check for FastAPI decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                        return True
        
        # Check function content for FastAPI patterns
        func_source = self._get_function_source(content, node)
        fastapi_patterns = [
            'Depends(',
            'HTTPException',
            'status_code',
            'response_model'
        ]
        
        return any(pattern in func_source for pattern in fastapi_patterns)
    
    def _should_extract_function(self, node: ast.FunctionDef, content: str, framework: str) -> bool:
        """Determine if a function should be extracted based on framework."""
        # Skip private functions and test functions
        if node.name.startswith('_') or node.name.startswith('test_'):
            return False
        
        # Skip common utility functions that don't need testing
        skip_functions = ['main', '__init__', '__str__', '__repr__']
        if node.name in skip_functions:
            return False
        
        if framework == 'flask':
            return self._is_flask_endpoint(node, content)
        elif framework == 'django':
            return self._is_django_view(node, content)
        elif framework == 'fastapi':
            return self._is_fastapi_endpoint(node, content)
        else:
            # For general Python, extract all non-private functions
            return True
    
    def extract_python_functions(self, repo_path: str, detected_framework: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract Python functions from all Python files in the repository.
        
        Args:
            repo_path (str): Path to the repository
            detected_framework (str): Pre-detected framework (optional)
            
        Returns:
            Dict[str, List[Dict]]: Functions grouped by file path
        """
        functions_by_file = {}
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories that don't contain source code
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
                '__pycache__', 'node_modules', 'venv', 'env', 'tests', 'test',
                '.git', '.pytest_cache', 'htmlcov', 'coverage', 'dist', 'build'
            ]]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('test_') and file != 'conftest.py':
                    file_path = os.path.join(root, file)
                    
                    # Skip common non-source files
                    if any(skip_file in file for skip_file in [
                        'setup.py', 'manage.py', 'wsgi.py', 'asgi.py', 'settings.py'
                    ]):
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Skip empty files or files with only imports
                        if len(content.strip()) < 50:
                            continue
                        
                        # Detect framework for this file if not already detected
                        file_framework = detected_framework or self._detect_framework_from_code(content)
                        
                        functions = self._extract_functions_from_file(file_path, content, file_framework)
                        
                        if functions:
                            functions_by_file[file_path] = functions
                            print(f"Extracted {len(functions)} functions from {os.path.relpath(file_path, repo_path)} (framework: {file_framework})")
                    
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
        
        return functions_by_file
    
    def _extract_functions_from_file(self, file_path: str, content: str, framework: str) -> List[Dict[str, Any]]:
        """Extract functions from a single file."""
        functions = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if self._should_extract_function(node, content, framework):
                        func_info = {
                            'name': node.name,
                            'file_path': file_path,
                            'line_number': node.lineno,
                            'source_code': self._get_function_source(content, node),
                            'docstring': ast.get_docstring(node) or '',
                            'args': [arg.arg for arg in node.args.args],
                            'framework': framework,
                            'decorators': self._extract_decorators(node),
                            'return_type': self._extract_return_type(node),
                            'is_async': isinstance(node, ast.AsyncFunctionDef),
                            'complexity': self._calculate_complexity(node)
                        }
                        functions.append(func_info)
        
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
        
        return functions
    
    def _extract_decorators(self, node: ast.FunctionDef) -> List[str]:
        """Extract decorator information from a function."""
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                if hasattr(decorator.value, 'id'):
                    decorators.append(f"{decorator.value.id}.{decorator.attr}")
                else:
                    decorators.append(decorator.attr)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if hasattr(decorator.func.value, 'id'):
                        decorators.append(f"{decorator.func.value.id}.{decorator.func.attr}")
                    else:
                        decorators.append(decorator.func.attr)
                elif isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
        return decorators
    
    def _extract_return_type(self, node: ast.FunctionDef) -> str:
        """Extract return type annotation if present."""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return str(node.returns.value)
            elif isinstance(node.returns, ast.Attribute):
                return f"{node.returns.value.id}.{node.returns.attr}" if hasattr(node.returns.value, 'id') else node.returns.attr
        return None
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _get_function_source(self, content: str, node: ast.FunctionDef) -> str:
        """Extract the source code of a function."""
        lines = content.split('\n')
        start_line = node.lineno - 1
        
        # Find the end of the function
        if hasattr(node, 'end_lineno') and node.end_lineno:
            end_line = node.end_lineno
        else:
            # Fallback: find end by indentation
            end_line = start_line + 1
            if start_line < len(lines):
                indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
                
                for i in range(start_line + 1, len(lines)):
                    line = lines[i]
                    if line.strip() == '':
                        continue
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= indent_level and line.strip():
                        end_line = i
                        break
                else:
                    end_line = len(lines)
        
        return '\n'.join(lines[start_line:end_line])
    
    def get_function_dependencies(self, node: ast.FunctionDef, content: str) -> List[str]:
        """Extract function dependencies (imports, global variables, etc.)."""
        dependencies = []
        
        # Extract imports from the file
        tree = ast.parse(content)
        for child in ast.walk(tree):
            if isinstance(child, ast.Import):
                for alias in child.names:
                    dependencies.append(alias.name)
            elif isinstance(child, ast.ImportFrom):
                module = child.module or ''
                for alias in child.names:
                    dependencies.append(f"{module}.{alias.name}" if module else alias.name)
        
        # Extract function calls within the function
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    if hasattr(child.func.value, 'id'):
                        dependencies.append(f"{child.func.value.id}.{child.func.attr}")
        
        return list(set(dependencies))  # Remove duplicates
    
    def analyze_function_patterns(self, functions_by_file: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze patterns in extracted functions for better test generation."""
        analysis = {
            'total_functions': 0,
            'frameworks': {},
            'complexity_distribution': {'low': 0, 'medium': 0, 'high': 0},
            'async_functions': 0,
            'decorated_functions': 0,
            'common_patterns': []
        }
        
        all_decorators = []
        
        for file_path, functions in functions_by_file.items():
            analysis['total_functions'] += len(functions)
            
            for func in functions:
                # Framework distribution
                framework = func.get('framework', 'general')
                analysis['frameworks'][framework] = analysis['frameworks'].get(framework, 0) + 1
                
                # Complexity distribution
                complexity = func.get('complexity', 1)
                if complexity <= 3:
                    analysis['complexity_distribution']['low'] += 1
                elif complexity <= 7:
                    analysis['complexity_distribution']['medium'] += 1
                else:
                    analysis['complexity_distribution']['high'] += 1
                
                # Async functions
                if func.get('is_async', False):
                    analysis['async_functions'] += 1
                
                # Decorated functions
                decorators = func.get('decorators', [])
                if decorators:
                    analysis['decorated_functions'] += 1
                    all_decorators.extend(decorators)
        
        # Find common decorator patterns
        from collections import Counter
        decorator_counts = Counter(all_decorators)
        analysis['common_decorators'] = decorator_counts.most_common(10)
        
        return analysis
