import os
import json
from pathlib import Path
from typing import Tuple

class LanguageDetector:
    """Detects programming language and framework from repository structure."""
    
    def __init__(self):
        self.framework_indicators = {
            'flask': [
                'from flask import',
                'Flask(__name__)',
                'app = Flask',
                '@app.route',
                'flask.Flask'
            ],
            'django': [
                'from django',
                'django.http',
                'HttpResponse',
                'DJANGO_SETTINGS_MODULE',
                'manage.py',
                'settings.py'
            ],
            'fastapi': [
                'from fastapi',
                'FastAPI()',
                'app = FastAPI',
                '@app.get',
                '@app.post',
                'fastapi.FastAPI'
            ]
        }
    
    def detect_language(self, repo_path: str) -> Tuple[str, str]:
        """
        Detect programming language and framework.
        
        Args:
            repo_path (str): Path to the repository
            
        Returns:
            Tuple[str, str]: (language, framework)
        """

        # Check for Angular/TypeScript first
        if self._is_angular_project(repo_path):
            return 'typescript', 'angular'

        # Check for Python files
        if self._has_python_files(repo_path):
            framework = self._detect_python_framework(repo_path)
            return 'python', framework
        
        # Check for other languages (future expansion)
        # if self._has_javascript_files(repo_path):
        #     return 'javascript', 'general'
        
        # if self._has_csharp_files(repo_path):
        #     return 'csharp', 'general'
        
        return 'unknown', 'general'
    
    def _is_angular_project(self, repo_path):
        """Check if the repository is an Angular project."""
        # Check for package.json with Angular dependencies
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # Check dependencies and devDependencies for Angular
                dependencies = package_data.get('dependencies', {})
                dev_dependencies = package_data.get('devDependencies', {})
                all_deps = {**dependencies, **dev_dependencies}
                
                angular_indicators = [
                    '@angular/core',
                    '@angular/cli',
                    '@angular/common',
                    '@angular/platform-browser'
                ]
                
                if any(dep in all_deps for dep in angular_indicators):
                    return True
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Check for angular.json
        if os.path.exists(os.path.join(repo_path, 'angular.json')):
            return True
        
        # Check for TypeScript files with Angular patterns
        ts_files = list(Path(repo_path).rglob('*.ts'))
        if ts_files:
            for ts_file in ts_files[:5]:  # Check first 5 TS files
                try:
                    with open(ts_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if any(pattern in content for pattern in [
                            '@Component',
                            '@Injectable',
                            '@NgModule',
                            'import { Component }',
                            'import { Injectable }'
                        ]):
                            return True
                except:
                    continue
        
        return False
    def _has_python_files(self, repo_path: str) -> bool:
        """Check if repository contains Python files."""
        for root, dirs, files in os.walk(repo_path):
            if any(file.endswith('.py') for file in files):
                return True
        return False
    
    def _has_javascript_files(self, repo_path: str) -> bool:
        """Check if repository contains JavaScript files."""
        for root, dirs, files in os.walk(repo_path):
            if any(file.endswith(('.js', '.ts', '.jsx', '.tsx')) for file in files):
                return True
        return False
    
    def _has_csharp_files(self, repo_path: str) -> bool:
        """Check if repository contains C# files."""
        for root, dirs, files in os.walk(repo_path):
            if any(file.endswith('.cs') for file in files):
                return True
        return False
    
    def _detect_python_framework(self, repo_path: str) -> str:
        """Detect Python web framework."""
        framework_scores = {
            'flask': 0,
            'django': 0,
            'fastapi': 0
        }
        
        # Check files for framework indicators
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                        
                        # Score each framework based on indicators
                        for framework, indicators in self.framework_indicators.items():
                            for indicator in indicators:
                                if indicator.lower() in content:
                                    framework_scores[framework] += 1
                    
                    except Exception:
                        continue
        
        # Check for framework-specific files
        framework_scores.update(self._check_framework_files(repo_path))
        
        # Return the framework with the highest score
        if max(framework_scores.values()) > 0:
            return max(framework_scores, key=framework_scores.get)
        
        return 'general'
    
    def _check_framework_files(self, repo_path: str) -> dict:
        """Check for framework-specific files and directories."""
        scores = {'flask': 0, 'django': 0, 'fastapi': 0}
        
        # Check for specific files
        files_to_check = {
            'flask': ['app.py', 'application.py', 'run.py'],
            'django': ['manage.py', 'settings.py', 'wsgi.py', 'asgi.py'],
            'fastapi': ['main.py', 'app.py']
        }
        
        for framework, files in files_to_check.items():
            for file_name in files:
                if self._file_exists_in_repo(repo_path, file_name):
                    scores[framework] += 2
        
        # Check for directories
        dirs_to_check = {
            'django': ['migrations', 'templates', 'static'],
            'flask': ['templates', 'static'],
            'fastapi': ['routers', 'models', 'schemas']
        }
        
        for framework, dirs in dirs_to_check.items():
            for dir_name in dirs:
                if self._dir_exists_in_repo(repo_path, dir_name):
                    scores[framework] += 1
        
        # Check requirements.txt or pyproject.toml
        requirements_path = os.path.join(repo_path, 'requirements.txt')
        pyproject_path = os.path.join(repo_path, 'pyproject.toml')
        
        if os.path.exists(requirements_path):
            scores.update(self._check_requirements_file(requirements_path))
        
        if os.path.exists(pyproject_path):
            scores.update(self._check_pyproject_file(pyproject_path))
        
        return scores
    
    def _file_exists_in_repo(self, repo_path: str, filename: str) -> bool:
        """Check if a file exists anywhere in the repository."""
        for root, dirs, files in os.walk(repo_path):
            if filename in files:
                return True
        return False
    
    def _dir_exists_in_repo(self, repo_path: str, dirname: str) -> bool:
        """Check if a directory exists anywhere in the repository."""
        for root, dirs, files in os.walk(repo_path):
            if dirname in dirs:
                return True
        return False
    
    def _check_requirements_file(self, requirements_path: str) -> dict:
        """Check requirements.txt for framework dependencies."""
        scores = {'flask': 0, 'django': 0, 'fastapi': 0}
        
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            if 'flask' in content:
                scores['flask'] += 3
            if 'django' in content:
                scores['django'] += 3
            if 'fastapi' in content:
                scores['fastapi'] += 3
        
        except Exception:
            pass
        
        return scores
    
    def _check_pyproject_file(self, pyproject_path: str) -> dict:
        """Check pyproject.toml for framework dependencies."""
        scores = {'flask': 0, 'django': 0, 'fastapi': 0}
        
        try:
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            if 'flask' in content:
                scores['flask'] += 3
            if 'django' in content:
                scores['django'] += 3
            if 'fastapi' in content:
                scores['fastapi'] += 3
        
        except Exception:
            pass
        
        return scores

