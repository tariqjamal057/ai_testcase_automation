import os
import subprocess
import json
import re
from typing import Dict, Any

class AngularTestRunner:
    """Runs Angular tests and generates coverage reports."""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.coverage_dir = os.path.join(repo_path, 'coverage')
    
    def _run_command(self, cmd_list, **kwargs):
        """Run a command with proper Windows handling."""
        try:
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
    
    def run_tests(self) -> Dict[str, Any]:
        """Run Angular tests with coverage."""
        print("🧪 Running Angular tests...")
        # imstall npm dependencies
        
        # Check if Angular CLI is available
        ng_result = self._run_command(['ng', 'version'], cwd=self.repo_path, timeout=30)
        # ng_result = self._run_command(['npm', 'install'], cwd=self.repo_path, timeout=30)
    
        
        if ng_result and ng_result.returncode == 0:
            # Try with ng test
            result = self._run_ng_test()
            if result['success']:
                return result
        
        print("❌ ng test failed. Trying Karma fallback...")
        
        # Fallback to direct Karma
        result = self._run_karma_test()
        if result['success']:
            return result
        
        print("❌ Tests failed with both ng test and Karma.")
        return {
            'success': False,
            'return_code': -1,
            'output': 'Both ng test and Karma failed',
            'coverage_info': None
        }
    
    def _run_ng_test(self) -> Dict[str, Any]:
        """Run tests using Angular CLI."""
        try:
            cmd = ['ng', 'test', '--watch=false', '--code-coverage=true', '--browsers=ChromeHeadless']
            
            print(f"Running command: {' '.join(cmd)}")
            result = self._run_command(cmd, cwd=self.repo_path, timeout=300)
            
            if not result:
                return {
                    'success': False,
                    'return_code': -1,
                    'output': 'Failed to execute ng test command',
                    'error': 'Command execution failed',
                    'coverage_info': None
                }
            
            success = result.returncode == 0
            coverage_info = self._parse_coverage_output(result.stdout) if success else None
            
            return {
                'success': success,
                'return_code': result.returncode,
                'output': result.stdout,
                'error': result.stderr,
                'coverage_info': coverage_info
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'return_code': -1,
                'output': 'Test execution timed out',
                'error': 'Timeout after 5 minutes',
                'coverage_info': None
            }
        except Exception as e:
            return {
                'success': False,
                'return_code': -1,
                'output': f'Error running ng test: {e}',
                'error': str(e),
                'coverage_info': None
            }
    
    def _run_karma_test(self) -> Dict[str, Any]:
        """Run tests using Karma directly."""
        try:
            # Check if karma.conf.js exists
            karma_config = os.path.join(self.repo_path, 'karma.conf.js')
            if not os.path.exists(karma_config):
                return {
                    'success': False,
                    'return_code': -1,
                    'output': 'karma.conf.js not found',
                    'error': 'No Karma configuration file',
                    'coverage_info': None
                }
            
            # Try to run karma
            cmd = ['npx', 'karma', 'start', '--single-run', '--code-coverage']
            
            print(f"Running command: {' '.join(cmd)}")
            result = self._run_command(cmd, cwd=self.repo_path, timeout=300)
            
            if not result:
                return {
                    'success': False,
                    'return_code': -1,
                    'output': 'Failed to execute karma command',
                    'error': 'Command execution failed',
                    'coverage_info': None
                }
            
            success = result.returncode == 0
            coverage_info = self._parse_coverage_output(result.stdout) if success else None
            
            return {
                'success': success,
                'return_code': result.returncode,
                'output': result.stdout,
                'error': result.stderr,
                'coverage_info': coverage_info
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'return_code': -1,
                'output': 'Karma test execution timed out',
                'error': 'Timeout after 5 minutes',
                'coverage_info': None
            }
        except Exception as e:
            return {
                'success': False,
                'return_code': -1,
                'output': f'Error running karma: {e}',
                'error': str(e),
                'coverage_info': None
            }
    
    def _parse_coverage_output(self, output: str) -> Dict[str, Any]:
        """Parse coverage information from test output."""
        coverage_info = {}
        
        try:
            # Look for coverage summary in output
            lines = output.split('\n')
            
            for i, line in enumerate(lines):
                if 'Coverage summary' in line or '=======' in line:
                    # Try to find coverage percentages
                    for j in range(i, min(i + 10, len(lines))):
                        coverage_line = lines[j]
                        
                        # Look for patterns like "Statements: 85.5% (123/144)"
                        if 'Statements:' in coverage_line:
                            match = re.search(r'Statements:\s*(\d+\.?\d*)%', coverage_line)
                            if match:
                                coverage_info['statements'] = match.group(1) + '%'
                        
                        if 'Branches:' in coverage_line:
                            match = re.search(r'Branches:\s*(\d+\.?\d*)%', coverage_line)
                            if match:
                                coverage_info['branches'] = match.group(1) + '%'
                        
                        if 'Functions:' in coverage_line:
                            match = re.search(r'Functions:\s*(\d+\.?\d*)%', coverage_line)
                            if match:
                                coverage_info['functions'] = match.group(1) + '%'
                        
                        if 'Lines:' in coverage_line:
                            match = re.search(r'Lines:\s*(\d+\.?\d*)%', coverage_line)
                            if match:
                                coverage_info['lines'] = match.group(1) + '%'
            
            # Calculate total coverage (average of available metrics)
            if coverage_info:
                percentages = []
                for key in ['statements', 'branches', 'functions', 'lines']:
                    if key in coverage_info:
                        try:
                            percentages.append(float(coverage_info[key].replace('%', '')))
                        except:
                            pass
                
                if percentages:
                    total_coverage = sum(percentages) / len(percentages)
                    coverage_info['total_coverage'] = f"{total_coverage:.1f}%"
            
        except Exception as e:
            print(f"Error parsing coverage output: {e}")
        
        return coverage_info
    
    def generate_coverage_report(self) -> str:
        """Generate HTML coverage report."""
        try:
            # Check if coverage directory exists
            if not os.path.exists(self.coverage_dir):
                print("❌ Coverage directory not found")
                return None
            
            # Look for HTML coverage report
            html_report_path = os.path.join(self.coverage_dir, 'index.html')
            if os.path.exists(html_report_path):
                print(f"✅ Coverage report generated: {html_report_path}")
                return html_report_path
            
            # Look for lcov report
            lcov_report_path = os.path.join(self.coverage_dir, 'lcov.info')
            if os.path.exists(lcov_report_path):
                print(f"✅ LCOV coverage report found: {lcov_report_path}")
                return lcov_report_path
            
            print("❌ No coverage report found")
            return None
            
        except Exception as e:
            print(f"❌ Error generating coverage report: {e}")
            return None
