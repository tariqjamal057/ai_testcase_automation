import os
import json
import subprocess
import sys

class AngularDependencyManager:
    """Manages Angular project dependencies and setup."""
    
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.package_json_path = os.path.join(repo_path, 'package.json')
    
    def install_dependencies(self):
        """Install Angular project dependencies."""
        try:
            print("📦 Installing Angular dependencies...")
            print(f"Using package.json at: {self.package_json_path}")
            # Check if package.json exists
            if not os.path.exists(self.package_json_path):
                print("❌ package.json not found")
                return False
            
            # Change to repo directory
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            try:
                # Try npm install first
                result = subprocess.run(
                    ['npm', 'install'],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                if result.returncode == 0:
                    print("✅ Dependencies installed successfully with npm")
                    return True
                else:
                    print(f"❌ npm install failed: {result.stderr}")
                    
                    # Try yarn as fallback
                    print("🔄 Trying yarn as fallback...")
                    result = subprocess.run(
                        ['yarn', 'install'],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        print("✅ Dependencies installed successfully with yarn")
                        return True
                    else:
                        print(f"❌ yarn install also failed: {result.stderr}")
                        return False
                        
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            print("❌ Dependency installation timed out")
            return False
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            return False
    
    def ensure_test_dependencies(self):
        """Ensure required testing dependencies are installed."""
        try:
            with open(self.package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            dev_dependencies = package_data.get('devDependencies', {})
            dependencies = package_data.get('dependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            # Required testing dependencies
            required_test_deps = {
                'jasmine-core': '^4.0.0',
                'karma': '^6.0.0',
                'karma-chrome-headless': '^3.0.0',
                'karma-coverage': '^2.0.0',
                'karma-jasmine': '^5.0.0',
                'karma-jasmine-html-reporter': '^2.0.0',
                '@angular-devkit/build-angular': '*'
            }
            
            missing_deps = []
            for dep, version in required_test_deps.items():
                if dep not in all_deps:
                    missing_deps.append(f"{dep}@{version}")
            
            if missing_deps:
                print(f"📦 Installing missing test dependencies: {missing_deps}")
                return self._install_packages(missing_deps, dev=True)
            
            print("✅ All required test dependencies are present")
            return True
            
        except Exception as e:
            print(f"❌ Error checking test dependencies: {e}")
            return False
    
    def _install_packages(self, packages, dev=False):
        """Install specific npm packages."""
        try:
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            try:
                dev_flag = ['--save-dev'] if dev else ['--save']
                cmd = ['npm', 'install'] + dev_flag + packages
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                
                if result.returncode == 0:
                    print(f"✅ Installed packages: {packages}")
                    return True
                else:
                    print(f"❌ Failed to install packages: {result.stderr}")
                    return False
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            print(f"❌ Error installing packages: {e}")
            return False
    
    def setup_karma_config(self):
        """Setup or verify Karma configuration for headless testing."""
        karma_config_path = os.path.join(self.repo_path, 'karma.conf.js')
        
        if os.path.exists(karma_config_path):
            print("✅ Karma configuration already exists")
            return True
        
        # Create basic karma configuration
        karma_config = """
module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine', '@angular-devkit/build-angular'],
    plugins: [
      require('karma-jasmine'),
      require('karma-chrome-launcher'),
      require('karma-jasmine-html-reporter'),
      require('karma-coverage'),
      require('@angular-devkit/build-angular/plugins/karma')
    ],
    client: {
      jasmine: {
        // you can add configuration options for Jasmine here
        // the possible options are listed at https://jasmine.github.io/api/edge/Configuration.html
        // for example, you can disable the random execution order
        random: false
      },
      clearContext: false // leave Jasmine Spec Runner output visible in browser
    },
    jasmineHtmlReporter: {
      suppressAll: true // removes the duplicated traces
    },
    coverageReporter: {
      dir: require('path').join(__dirname, './coverage/'),
      subdir: '.',
      reporters: [
        { type: 'html' },
        { type: 'text-summary' },
        { type: 'lcov' }
      ]
    },
    reporters: ['progress', 'kjhtml', 'coverage'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    browsers: ['ChromeHeadless'],
    singleRun: true,
    restartOnFileChange: true
  });
};
"""
        
        try:
            with open(karma_config_path, 'w', encoding='utf-8') as f:
                f.write(karma_config)
            print("✅ Created Karma configuration")
            return True
        except Exception as e:
            print(f"❌ Error creating Karma config: {e}")
            return False
