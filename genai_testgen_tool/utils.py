import re
import os
from typing import Dict, List, Any

def clean_function_name(name: str) -> str:
    """Clean function name for test generation."""
    # Remove special characters and make it suitable for test names
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    return cleaned

def get_framework_from_functions(functions: List[Dict[str, Any]]) -> str:
    """Determine framework from function list."""
    if not functions:
        return 'general'
    
    # Check if any function has framework info
    frameworks = [func.get('framework', 'general') for func in functions]
    
    # Return the most common framework
    framework_counts = {}
    for fw in frameworks:
        framework_counts[fw] = framework_counts.get(fw, 0) + 1
    
    return max(framework_counts, key=framework_counts.get)

def extract_imports_from_code(code: str) -> List[str]:
    """Extract import statements from code."""
    imports = []
    lines = code.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('import ') or line.startswith('from '):
            imports.append(line)
    
    return imports

def is_flask_route_function(func_info: Dict[str, Any]) -> bool:
    """Check if a function is a Flask route."""
    decorators = func_info.get('decorators', [])
    return any('route' in decorator or 'get' in decorator or 'post' in decorator 
              for decorator in decorators)

def is_django_view_function(func_info: Dict[str, Any]) -> bool:
    """Check if a function is a Django view."""
    args = func_info.get('args', [])
    return len(args) > 0 and args[0] == 'request'

def is_fastapi_endpoint_function(func_info: Dict[str, Any]) -> bool:
    """Check if a function is a FastAPI endpoint."""
    decorators = func_info.get('decorators', [])
    fastapi_decorators = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']
    return any(decorator.split('.')[-1] in fastapi_decorators for decorator in decorators)

def generate_test_function_name(original_name: str, test_type: str = '') -> str:
    """Generate a proper test function name."""
    clean_name = clean_function_name(original_name)
    
    if test_type:
        return f"test_{clean_name}_{test_type}"
    else:
        return f"test_{clean_name}"

def get_relative_import_path(source_file: str, repo_root: str) -> str:
    """Get the relative import path for a source file."""
    rel_path = os.path.relpath(source_file, repo_root)
    # Convert file path to module path
    module_path = rel_path.replace(os.sep, '.').replace('.py', '')
    return module_path

def validate_test_code(test_code: str) -> Dict[str, Any]:
    """Validate generated test code."""
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    if not test_code or not test_code.strip():
        validation_result['valid'] = False
        validation_result['errors'].append('Test code is empty')
        return validation_result
    
    # Check for basic test structure
    if 'def test_' not in test_code:
        validation_result['warnings'].append('No test functions found (should start with test_)')
    
    # Check for imports
    if 'import' not in test_code:
        validation_result['warnings'].append('No import statements found')
    
    # Check for assertions
    if 'assert' not in test_code:
        validation_result['warnings'].append('No assertions found in test code')
    
    return validation_result
