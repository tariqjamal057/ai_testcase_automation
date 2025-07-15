import os
import subprocess
import json
import shutil
from pathlib import Path
import sys

class AngularTestFileManager:
    """Manages Angular test file creation and configuration."""
    
    def __init__(self, repo_path: str, framework: str):
        self.repo_path = repo_path
        self.framework = framework
        self.src_path = os.path.join(repo_path, 'src', 'app')
    
    def _run_command(self, cmd_list, **kwargs):
        """Run a command with proper Windows handling."""
        try:
            # On Windows, try with shell=True first
            result = subprocess.run(
                cmd_list,
                shell=True,
                capture_output=True,
                text=True,
                **kwargs
            )
            return result
        except Exception as e:
            print(f"Error running command {cmd_list}: {e}")
            return None
    
    def _check_node_npm(self):
        """Check if Node.js and npm are available."""
        try:
            # Test Node.js
            print("🔍 Testing Node.js...")
            node_result = self._run_command(['node', '--version'], timeout=10)
            
            if not node_result or node_result.returncode != 0:
                print("❌ Node.js not accessible")
                print("Please ensure Node.js is installed and accessible from command line")
                return False
            
            print(f"✅ Node.js version: {node_result.stdout.strip()}")
            
            # Test npm
            print("🔍 Testing npm...")
            npm_result = self._run_command(['npm', '--version'], timeout=10)
            
            if not npm_result or npm_result.returncode != 0:
                print("❌ npm not accessible")
                print("Please ensure npm is installed and accessible from command line")
                return False
            
            print(f"✅ npm version: {npm_result.stdout.strip()}")
            return True
                
        except Exception as e:
            print(f"❌ Error testing Node.js/npm: {e}")
            return False
    
    def setup_angular_dependencies(self):
        """Set up Angular project dependencies."""
        print("📦 Setting up Angular dependencies...")
        
        # Check if Node.js and npm are available
        if not self._check_node_npm():
            print("❌ Skipping dependency installation due to missing Node.js/npm")
            return False
        
        # Check if package.json exists
        package_json_path = os.path.join(self.repo_path, 'package.json')
        if not os.path.exists(package_json_path):
            print("❌ package.json not found. This doesn't appear to be an Angular project.")
            return False
        
        try:
            # Install dependencies
            print("📦 Installing Angular dependencies...")
            print(f"Working directory: {self.repo_path}")
            
            result = self._run_command(
                ['npm', 'install'],
                cwd=self.repo_path,
                timeout=300  # 5 minutes timeout
            )
            
            if not result:
                print("❌ Failed to run npm install command")
                return False
            
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                return True
            else:
                print(f"❌ Error installing dependencies:")
                print(f"Return code: {result.returncode}")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Dependency installation timed out")
            return False
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def ensure_test_dependencies(self):
        """Ensure required test dependencies are installed."""
        if not self._check_node_npm():
            return False
        
        # Check if node_modules exists first
        node_modules_path = os.path.join(self.repo_path, 'node_modules')
        if not os.path.exists(node_modules_path):
            print("📦 node_modules not found, running npm install first...")
            if not self.setup_angular_dependencies():
                return False
        
        required_packages = [
            'karma-chrome-headless',
            'karma-coverage'
        ]
        
        try:
            # Check which packages are missing
            missing_packages = []
            for package in required_packages:
                check_result = self._run_command(
                    ['npm', 'list', package],
                    cwd=self.repo_path,
                    timeout=30
                )
                if not check_result or check_result.returncode != 0:
                    missing_packages.append(package)
            
            if missing_packages:
                print(f"📦 Installing missing test dependencies: {missing_packages}")
                install_result = self._run_command(
                    ['npm', 'install', '--save-dev'] + missing_packages,
                    cwd=self.repo_path,
                    timeout=180
                )
                
                if install_result and install_result.returncode == 0:
                    print("✅ Test dependencies installed successfully")
                    return True
                else:
                    print(f"❌ Error installing packages:")
                    if install_result:
                        print(f"Return code: {install_result.returncode}")
                        if install_result.stdout:
                            print(f"STDOUT: {install_result.stdout}")
                        if install_result.stderr:
                            print(f"STDERR: {install_result.stderr}")
                    return False
            else:
                print("✅ All test dependencies are already installed")
                return True
                
        except Exception as e:
            print(f"❌ Error checking/installing test dependencies: {e}")
            return False
        
    def update_test_config(self):
        """Public method to update test configuration files."""
        return self._update_test_config()
    
    def create_test_files(self, generated_tests):
        """Create Angular test files."""
        created_files = []
        
        for file_path, test_info in generated_tests.items():
            try:
                # Convert file path to test file path
                test_file_path = self._get_test_file_path(file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
                
                # Write test file
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(test_info['test_code'])
                
                created_files.append(test_file_path)
                print(f"✅ Created test file: {os.path.relpath(test_file_path, self.repo_path)}")
                
            except Exception as e:
                print(f"❌ Error creating test file for {file_path}: {e}")
        
        # Update test configuration files
        self._update_test_config()
        
        return created_files
    
    def _get_test_file_path(self, source_file_path):
        """Convert source file path to test file path."""
        # Convert .ts to .spec.ts
        if source_file_path.endswith('.ts'):
            return source_file_path.replace('.ts', '.spec.ts')
        else:
            return source_file_path + '.spec.ts'
    
    def _update_test_config(self):
        """Update Angular test configuration files."""
        self._ensure_tsconfig_spec()
        self._ensure_test_ts()
        self._ensure_karma_config()
    
    def _ensure_tsconfig_spec(self):
        """Ensure tsconfig.spec.json exists."""
        tsconfig_spec_path = os.path.join(self.repo_path, 'tsconfig.spec.json')
        
        if os.path.exists(tsconfig_spec_path):
            print("✅ tsconfig.spec.json already exists")
            return
        
        tsconfig_spec_content = {
            "extends": "./tsconfig.json",
            "compilerOptions": {
                "outDir": "./out-tsc/spec",
                "types": ["jasmine", "node"]
            },
            "files": ["src/test.ts"],
            "include": ["src/**/*.spec.ts", "src/**/*.d.ts"]
        }
        
        try:
            with open(tsconfig_spec_path, 'w', encoding='utf-8') as f:
                json.dump(tsconfig_spec_content, f, indent=2)
            print("✅ Created tsconfig.spec.json")
        except Exception as e:
            print(f"❌ Error creating tsconfig.spec.json: {e}")
    
    def _ensure_test_ts(self):
        """Ensure src/test.ts exists."""
        test_ts_path = os.path.join(self.repo_path, 'src', 'test.ts')
        
        if os.path.exists(test_ts_path):
            print("✅ test.ts already exists")
            return
        
        test_ts_content = '''// This file is required by karma.conf.js and loads recursively all the .spec and framework files

import 'zone.js/dist/zone-testing';
import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing';

declare const require: {
  context(path: string, deep?: boolean, filter?: RegExp): {
    keys(): string[];
    <T>(id: string): T;
  };
};

// First, initialize the Angular testing environment.
getTestBed().initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting(),
);

// Then we find all the tests.
const context = require.context('./', true, /\.spec\.ts$/);
// And load the modules.
context.keys().map(context);
'''
        
        try:
            os.makedirs(os.path.dirname(test_ts_path), exist_ok=True)
            with open(test_ts_path, 'w', encoding='utf-8') as f:
                f.write(test_ts_content)
            print("✅ Created test.ts")
        except Exception as e:
            print(f"❌ Error creating test.ts: {e}")
    
    def _ensure_karma_config(self):
        """Ensure karma.conf.js exists."""
        karma_config_path = os.path.join(self.repo_path, 'karma.conf.js')
        
        if os.path.exists(karma_config_path):
            print("✅ Karma configuration already exists")
            return
        
        karma_config_content = '''// Karma configuration file, see link for more information
// https://karma-runner.github.io/1.0/config/configuration-file.html

module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine', '@angular-devkit/build-angular'],
    plugins: [
      require('karma-jasmine'),
      require('karma-chrome-headless'),
      require('karma-jasmine-html-reporter'),
      require('karma-coverage'),
      require('@angular-devkit/build-angular/plugins/karma')
    ],
    client: {
      clearContext: false // leave Jasmine Spec Runner output visible in browser
    },
    coverageReporter: {
      dir: require('path').join(__dirname, './coverage'),
      subdir: '.',
      reporters: [
        { type: 'html' },
        { type: 'text-summary' },
        { type: 'lcovonly' }
      ]
    },
    reporters: ['progress', 'kjhtml', 'coverage'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    browsers: ['ChromeHeadless'],
    singleRun: false,
    restartOnFileChange: true
  });
};
'''
        
        try:
            with open(karma_config_path, 'w', encoding='utf-8') as f:
                f.write(karma_config_content)
            print("✅ Created karma.conf.js")
        except Exception as e:
            print(f"❌ Error creating karma.conf.js: {e}")

    def _create_test_ts_file(self):
        """Create test.ts file if it doesn't exist."""
        test_ts_path = os.path.join(self.src_path, 'test.ts')
        
        if os.path.exists(test_ts_path):
            print("✅ test.ts already exists")
            return True
        
        # Fix the invalid escape sequence by using raw string or double backslash
        test_ts_content = r'''// This file is required by karma.conf.js and loads recursively all the .spec and framework files

import 'zone.js/testing';
import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing';

declare const require: {
  context(path: string, deep?: boolean, filter?: RegExp): {
    keys(): string[];
    <T>(id: string): T;
  };
};

// First, initialize the Angular testing environment.
getTestBed().initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting(),
);

// Then we find all the tests.
const context = require.context('./', true, /\.spec\.ts$/);
// And load the modules.
context.keys().map(context);
'''
        
        try:
            with open(test_ts_path, 'w', encoding='utf-8') as f:
                f.write(test_ts_content)
            print(f"✅ Created test.ts file: {test_ts_path}")
            return True
        except Exception as e:
            print(f"❌ Error creating test.ts file: {e}")
            return False
