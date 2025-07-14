import os
import subprocess
import sys
from typing import List, Dict

class TestRunner:
    """Runs tests and generates coverage reports."""
    
    def __init__(self, repo_path):
        self.repo_path = os.path.abspath(repo_path)
        self.test_dir = os.path.join(self.repo_path, 'tests')
    
    def run_tests(self, test_files: List[str] = None):
        """
        Run pytest tests with coverage.
        
        Args:
            test_files (List[str]): Specific test files to run
            
        Returns:
            Dict: Test results and coverage information
        """
        try:
            # Change to repository directory
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            # Check if tests directory exists
            if not os.path.exists(self.test_dir):
                print(f"Tests directory not found: {self.test_dir}")
                return {'success': False, 'error': 'Tests directory not found'}
            
            # Check if there are any test files
            test_files_found = []
            for root, dirs, files in os.walk(self.test_dir):
                for file in files:
                    if file.startswith('test_') and file.endswith('.py'):
                        test_files_found.append(os.path.join(root, file))
            
            if not test_files_found:
                print("No test files found in tests directory")
                return {'success': False, 'error': 'No test files found'}
            
            print(f"Found test files: {test_files_found}")
            
            # Prepare pytest command
            cmd = [
                sys.executable, '-m', 'pytest',
                '--cov=.',
                '--cov-report=html:htmlcov',
                '--cov-report=term-missing',
                '--cov-report=xml:coverage.xml',
                '-v',
                '--tb=short'
            ]
            
            # Add specific test files if provided
            if test_files:
                cmd.extend(test_files)
            else:
                cmd.append('tests/')
            
            print(f"Running command: {' '.join(cmd)}")
            
            # Run pytest
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse results
            test_results = self._parse_test_results(result)
            
            return test_results
            
        except subprocess.TimeoutExpired:
            print("Test execution timed out after 5 minutes")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            print(f"Error running tests: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            os.chdir(original_cwd)
    
    def _parse_test_results(self, result):
        """Parse pytest results."""
        success = result.returncode == 0
        
        test_results = {
            'success': success,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'coverage_info': self._extract_coverage_info(result.stdout)
        }
        
        # Print results
        print("\n" + "="*50)
        print("TEST RESULTS")
        print("="*50)
        print(result.stdout)
        
        if result.stderr:
            print("\nERRORS:")
            print(result.stderr)
        
        return test_results
    
    def _extract_coverage_info(self, stdout):
        """Extract coverage information from pytest output."""
        coverage_info = {}
        
        try:
            lines = stdout.split('\n')
            for line in lines:
                if 'TOTAL' in line and '%' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_info['total_coverage'] = parts[-1]
                        break
        except Exception as e:
            print(f"Error extracting coverage info: {e}")
        
        return coverage_info
    
    def generate_coverage_report(self):
        """Generate detailed coverage report."""
        try:
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            # Generate coverage report
            cmd = [sys.executable, '-m', 'coverage', 'report', '--show-missing']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            print("\n" + "="*50)
            print("COVERAGE REPORT")
            print("="*50)
            print(result.stdout)
            
            return result.stdout
            
        except Exception as e:
            print(f"Error generating coverage report: {e}")
            return None
        finally:
            os.chdir(original_cwd)
