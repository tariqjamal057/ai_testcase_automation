import os
import re
from typing import Dict, List

class TestFileManager:
    """Manages test file creation and organization."""
    
    def __init__(self, repo_path: str, framework: str = 'general'):
        self.repo_path = repo_path
        self.framework = framework
        self.tests_dir = os.path.join(repo_path, 'tests')
        self.conftest_created = False
    
    def create_test_files(self, generated_tests: Dict) -> List[str]:
        """
        Create test files from generated test code.
        
        Args:
            generated_tests (Dict): Generated tests mapped by file path
            
        Returns:
            List[str]: List of created test file paths
        """
        created_files = []
        
        # Ensure tests directory exists
        os.makedirs(self.tests_dir, exist_ok=True)
        # Create conftest.py first
        conftest_path = self._create_conftest_file()
        if conftest_path:
            created_files.append(conftest_path)
        
        # Create individual test files
        for source_file_path, test_info in generated_tests.items():
            test_file_path = self._create_test_file(source_file_path, test_info)
            if test_file_path:
                created_files.append(test_file_path)
        
        return created_files
    
    def _create_conftest_file(self) -> str:
        """Create conftest.py with framework-specific fixtures."""
        conftest_path = os.path.join(self.tests_dir, 'conftest.py')
        
        if os.path.exists(conftest_path):
            print(f"conftest.py already exists at {conftest_path}")
            return conftest_path
        
        conftest_content = self._get_conftest_content()
        
        try:
            with open(conftest_path, 'w', encoding='utf-8') as f:
                f.write(conftest_content)
            
            print(f"Created conftest.py at {conftest_path}")
            self.conftest_created = True
            return conftest_path
        
        except Exception as e:
            print(f"Error creating conftest.py: {e}")
            return None
    
    def _get_conftest_content(self) -> str:
        """Get framework-specific conftest.py content."""
        if self.framework == 'flask':
            return self._get_flask_conftest()
        elif self.framework == 'django':
            return self._get_django_conftest()
        elif self.framework == 'fastapi':
            return self._get_fastapi_conftest()
        else:
            return self._get_general_conftest()
    
    def _get_flask_conftest(self) -> str:
        """Generate Flask-specific conftest.py content."""
        return '''import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app import create_app, db
except ImportError:
    try:
        from main import create_app, db
    except ImportError:
        try:
            from application import create_app, db
        except ImportError:
            # Fallback for basic Flask apps
            from flask import Flask
            
            def create_app():
                app = Flask(__name__)
                app.config.update({
                    "TESTING": True,
                    "SECRET_KEY": "test-secret-key"
                })
                return app
            
            db = None

@pytest.fixture()
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "WTF_CSRF_ENABLED": False,
    })
    
    # Add database configuration if db exists
    if db is not None:
        app.config.update({
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    else:
        yield app

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture()
def auth_headers():
    """Common authentication headers for testing."""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
    }
'''
    
    def _get_django_conftest(self) -> str:
        """Generate Django-specific conftest.py content."""
        return '''import pytest
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Django settings module if not already set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import django
from django.conf import settings

# Configure Django if settings are not configured
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key-for-testing-only',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'article',
        ],
        USE_TZ=True,
        ROOT_URLCONF='urls',
    )

django.setup()

from django.test import Client
from django.contrib.auth.models import User

@pytest.fixture
def client():
    return Client()

@pytest.fixture
@pytest.mark.django_db
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
@pytest.mark.django_db
def authenticated_client(client, user):
    client.force_login(user)
    return client
'''


    def _get_fastapi_conftest(self) -> str:
        """Generate FastAPI-specific conftest.py content."""
        return '''import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
    from database import get_db, Base
except ImportError:
    try:
        from app.main import app
        from app.database import get_db, Base
    except ImportError:
        try:
            from src.main import app
            from src.database import get_db, Base
        except ImportError:
            # Fallback for basic FastAPI apps
            from fastapi import FastAPI
            app = FastAPI()
            get_db = None
            Base = None

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    """FastAPI test client."""
    if get_db is not None:
        app.dependency_overrides[get_db] = override_get_db
    
    if Base is not None:
        Base.metadata.create_all(bind=engine)
    
    with TestClient(app) as test_client:
        yield test_client
    
    if Base is not None:
        Base.metadata.drop_all(bind=engine)
    
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    """Common authentication headers for testing."""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
    }

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }
'''
    
    def _get_general_conftest(self) -> str:
        """Generate general Python conftest.py content."""
        return '''import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        "test_string": "hello world",
        "test_number": 42,
        "test_list": [1, 2, 3, 4, 5],
        "test_dict": {"key": "value"}
    }

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("test content")
    return str(file_path)

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "debug": True,
        "testing": True,
        "database_url": "sqlite:///:memory:"
    }
'''
    
    def _create_test_file(self, source_file_path: str, test_info: Dict) -> str:
        """Create a test file for a source file."""
        # Generate test file name
        source_filename = os.path.basename(source_file_path)
        test_filename = f"test_{source_filename}"
        test_file_path = os.path.join(self.tests_dir, test_filename)
        
        # Get the test code
        test_code = test_info['test_code']
        
        # Add proper imports and structure
        final_test_code = self._structure_test_code(test_code, source_file_path, test_info)
        
        try:
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(final_test_code)
            
            print(f"Created test file: {os.path.relpath(test_file_path, self.repo_path)}")
            return test_file_path
        
        except Exception as e:
            print(f"Error creating test file {test_file_path}: {e}")
            return None
        
    def _create_pytest_ini(self) -> str:
        """Create pytest.ini file for Django configuration."""
        if self.framework != 'django':
            return None
            
        pytest_ini_path = os.path.join(self.repo_path, 'pytest.ini')
        
        if os.path.exists(pytest_ini_path):
            print(f"pytest.ini already exists at {pytest_ini_path}")
            return pytest_ini_path
        
        pytest_ini_content = '''[tool:pytest]
DJANGO_SETTINGS_MODULE = settings
python_files = tests.py test_*.py *_tests.py
addopts = --tb=short --strict-markers
markers =
    django_db: mark test to use django database
'''
        
        try:
            with open(pytest_ini_path, 'w', encoding='utf-8') as f:
                f.write(pytest_ini_content)
            
            print(f"Created pytest.ini at {pytest_ini_path}")
            return pytest_ini_path
        
        except Exception as e:
            print(f"Error creating pytest.ini: {e}")
            return None

    
    def _structure_test_code(self, test_code: str, source_file_path: str, test_info: Dict) -> str:
        """Structure the test code with proper imports and formatting."""
        imports = self._get_framework_imports()
        
        # Add source code imports
        source_imports = self._generate_source_imports(source_file_path, test_info['functions'])
        
        # Combine everything
        structured_code = f"""# Test file generated by GenAI Test Generator
# Source file: {os.path.relpath(source_file_path, self.repo_path)}
# Framework: {self.framework}

{imports}

{source_imports}

{test_code}
"""
        
        return structured_code
    
    def _get_framework_imports(self) -> str:
        """Get framework-specific imports."""
        if self.framework == 'flask':
            return '''import pytest
from flask import json
'''
        elif self.framework == 'django':
            return '''import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
'''
        elif self.framework == 'fastapi':
            return '''import pytest
from fastapi.testclient import TestClient
'''
        else:
            return '''import pytest
import sys
import os
'''
    
    def _generate_source_imports(self, source_file_path: str, functions: List) -> str:
        """Generate imports for the source code being tested."""
        # Get relative path from repo root
        rel_path = os.path.relpath(source_file_path, self.repo_path)
        
        # Convert file path to module path
        module_path = rel_path.replace(os.sep, '.').replace('.py', '')
        
        # Extract function names
        function_names = [func['name'] for func in functions]
        
        if len(function_names) > 5:
            # If too many functions, import the module
            return f"import {module_path}"
        else:
            # Import specific functions
            functions_str = ', '.join(function_names)
            return f"from {module_path} import {functions_str}"
    
    def _has_proper_imports(self, test_code: str) -> bool:
        """Check if test code has proper imports."""
        lines = test_code.split('\n')
        has_pytest = any('import pytest' in line for line in lines[:15])
        has_sys_path = any('sys.path' in line for line in lines[:20])
        
        return has_pytest or has_sys_path
