"""Configuration settings for the GenAI Test Generator Tool."""

import os
from typing import Dict, Any

class Config:
    """Configuration class for the tool."""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('GENAI_MODEL', 'gpt-4')
    OPENAI_TEMPERATURE = float(os.getenv('GENAI_TEMPERATURE', '0.2'))
    OPENAI_MAX_TOKENS = int(os.getenv('GENAI_MAX_TOKENS', '2000'))
    
    # Test Configuration
    TEST_TIMEOUT = int(os.getenv('TEST_TIMEOUT', '300'))  # 5 minutes
    MAX_FUNCTIONS_PER_RUN = int(os.getenv('MAX_FUNCTIONS_PER_RUN', '50'))
    
    # Coverage Configuration
    COVERAGE_THRESHOLD = float(os.getenv('COVERAGE_THRESHOLD', '80.0'))
    
    # File Patterns
    IGNORE_PATTERNS = [
        '__pycache__',
        '.git',
        '.pytest_cache',
        'venv',
        'env',
        '.env',
        'node_modules',
        '.DS_Store'
    ]
    
    PYTHON_TEST_PATTERNS = [
        'test_*.py',
        '*_test.py'
    ]
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return status."""
        issues = []
        
        if not cls.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY is required")
        
        if cls.OPENAI_TEMPERATURE < 0 or cls.OPENAI_TEMPERATURE > 1:
            issues.append("GENAI_TEMPERATURE must be between 0 and 1")
        
        if cls.COVERAGE_THRESHOLD < 0 or cls.COVERAGE_THRESHOLD > 100:
            issues.append("COVERAGE_THRESHOLD must be between 0 and 100")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
