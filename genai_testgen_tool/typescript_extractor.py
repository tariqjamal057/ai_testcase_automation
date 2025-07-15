import os
import re
import json
from typing import Dict, List, Any

class TypeScriptExtractor:
    """Extracts functions from TypeScript/Angular files."""
    
    def __init__(self):
        self.angular_indicators = [
            '@Component',
            '@Injectable',
            '@Directive',
            '@Pipe',
            'import { Component',
            'import { Injectable',
            'import { NgModule',
            'from \'@angular/',
            'from "@angular/'
        ]
    
    def _detect_framework_from_code(self, content: str) -> str:
        """Detect framework based on code content."""
        content_lower = content.lower()
        
        angular_score = sum(1 for indicator in self.angular_indicators 
                          if indicator.lower() in content_lower)
        
        if angular_score > 0:
            return 'angular'
        else:
            return 'general'
    
    def _is_angular_component_method(self, function_match: re.Match, content: str) -> bool:
        """Check if a function is an Angular component method."""
        # Get the class context
        before_function = content[:function_match.start()]
        
        # Look for Angular decorators in the class
        class_start = before_function.rfind('class ')
        if class_start == -1:
            return False
        
        class_section = before_function[class_start:]
        
        # Check for Angular decorators
        angular_decorators = ['@Component', '@Injectable', '@Directive', '@Pipe']
        for decorator in angular_decorators:
            if decorator in class_section:
                return True
        
        return False
    
    def _should_extract_function(self, function_match: re.Match, content: str, framework: str) -> bool:
        """Determine if a function should be extracted based on framework."""
        function_name = function_match.group(1) or function_match.group(2)
        
        # Skip private functions and test functions
        if function_name.startswith('_') or function_name.startswith('test'):
            return False
        
        # Skip constructor
        if function_name == 'constructor':
            return False
        
        if framework == 'angular':
            return self._is_angular_component_method(function_match, content)
        else:
            # For general TypeScript, extract all non-private functions
            return True
    
    def extract_typescript_functions(self, repo_path: str, detected_framework: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract TypeScript functions from all TypeScript files in the repository.
        
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
                'node_modules', 'dist', 'build', 'coverage', 'e2e'
            ]]
            
            for file in files:
                if file.endswith('.ts') and not file.endswith('.spec.ts') and not file.endswith('.d.ts'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
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
        """Extract functions from a single TypeScript file."""
        functions = []
        
        try:
            # Regular expressions for different function patterns
            patterns = [
                # Method in class: methodName() { or methodName(): type {
                r'^\s*(?:public|private|protected)?\s*(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
                # Arrow function: functionName = () => { or const functionName = () => {
                r'^\s*(?:const|let|var)?\s*(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{',
                # Function declaration: function functionName() {
                r'^\s*function\s+(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
                # Async functions
                r'^\s*(?:public|private|protected)?\s*async\s+(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
            ]
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                for pattern in patterns:
                    match = re.search(pattern, line, re.MULTILINE)
                    if match:
                        if self._should_extract_function(match, content, framework):
                            func_info = self._extract_function_info(
                                match, content, lines, i, file_path, framework
                            )
                            if func_info:
                                functions.append(func_info)
        
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
        
        return functions
    
    def _extract_function_info(self, match: re.Match, content: str, lines: List[str], 
                             line_number: int, file_path: str, framework: str) -> Dict[str, Any]:
        """Extract detailed information about a function."""
        try:
            function_name = match.group(1)
            
            # Extract function source code
            source_code = self._get_function_source(lines, line_number)
            
            # Extract parameters
            params = self._extract_parameters(match.group(0))
            
            # Extract return type
            return_type = self._extract_return_type(match.group(0))
            
            # Extract decorators (for Angular)
            decorators = self._extract_decorators(lines, line_number)
            
            # Extract JSDoc comment
            jsdoc = self._extract_jsdoc(lines, line_number)
            
            return {
                'name': function_name,
                'file_path': file_path,
                'line_number': line_number + 1,
                'source_code': source_code,
                'jsdoc': jsdoc,
                'parameters': params,
                'return_type': return_type,
                'framework': framework,
                'decorators': decorators
            }
        
        except Exception as e:
            print(f"Error extracting function info: {e}")
            return None
    
    def _get_function_source(self, lines: List[str], start_line: int) -> str:
        """Extract the complete source code of a function."""
        try:
            # Find the opening brace
            brace_count = 0
            function_lines = []
            started = False
            
            for i in range(start_line, len(lines)):
                line = lines[i]
                function_lines.append(line)
                
                # Count braces to find function end
                for char in line:
                    if char == '{':
                        brace_count += 1
                        started = True
                    elif char == '}':
                        brace_count -= 1
                
                # If we've closed all braces, we're done
                if started and brace_count == 0:
                    break
            
            return '\n'.join(function_lines)
        
        except Exception as e:
            print(f"Error extracting function source: {e}")
            return lines[start_line] if start_line < len(lines) else ""
    
    def _extract_parameters(self, function_signature: str) -> List[str]:
        """Extract parameter names from function signature."""
        try:
            # Find parameters between parentheses
            start = function_signature.find('(')
            end = function_signature.find(')')
            
            if start == -1 or end == -1:
                return []
            
            params_str = function_signature[start + 1:end].strip()
            if not params_str:
                return []
            
            # Split by comma and extract parameter names
            params = []
            for param in params_str.split(','):
                param = param.strip()
                if param:
                    # Extract parameter name (before : if type annotation exists)
                    param_name = param.split(':')[0].strip()
                    # Remove default value if exists
                    param_name = param_name.split('=')[0].strip()
                    params.append(param_name)
            
            return params
        
        except Exception as e:
            print(f"Error extracting parameters: {e}")
            return []
    
    def _extract_return_type(self, function_signature: str) -> str:
        """Extract return type from function signature."""
        try:
            # Look for return type after ): 
            match = re.search(r'\):\s*([^{]+)', function_signature)
            if match:
                return match.group(1).strip()
            return 'void'
        
        except Exception as e:
            print(f"Error extracting return type: {e}")
            return 'unknown'
    
    def _extract_decorators(self, lines: List[str], line_number: int) -> List[str]:
        """Extract decorators from lines before the function."""
        decorators = []
        
        try:
            # Look backwards from function line for decorators
            for i in range(line_number - 1, max(0, line_number - 10), -1):
                line = lines[i].strip()
                if line.startswith('@'):
                    decorators.insert(0, line)
                elif line and not line.startswith('//'):
                    # Stop if we hit non-decorator, non-comment line
                    break
        
        except Exception as e:
            print(f"Error extracting decorators: {e}")
        
        return decorators
    
    def _extract_jsdoc(self, lines: List[str], line_number: int) -> str:
        """Extract JSDoc comment from lines before the function."""
        jsdoc_lines = []
        
        try:
            # Look backwards from function line for JSDoc
            in_jsdoc = False
            for i in range(line_number - 1, max(0, line_number - 20), -1):
                line = lines[i].strip()
                
                if line.endswith('*/'):
                    in_jsdoc = True
                    jsdoc_lines.insert(0, line)
                elif in_jsdoc:
                    jsdoc_lines.insert(0, line)
                    if line.startswith('/**'):
                        break
                elif line and not line.startswith('@'):
                    # Stop if we hit non-JSDoc content
                    break
            
            return '\n'.join(jsdoc_lines) if jsdoc_lines else ''
        
        except Exception as e:
            print(f"Error extracting JSDoc: {e}")
            return ''

