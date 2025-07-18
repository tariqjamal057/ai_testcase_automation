import os
import subprocess
import sys
import click
import tempfile
from dotenv import load_dotenv

from .angular_dependency_manager import AngularDependencyManager
from .angular_extractor import AngularExtractor
from .angular_test_manager import AngularTestFileManager
from .angular_test_runner import AngularTestRunner
from genai_testgen_tool.git_manager import GitManager

from .repo_cloner import RepoCloner
from .language_detector import LanguageDetector
from .function_extractor import FunctionExtractor
# from .angular_extractor import AngularExtractor
from .ai_generator import AITestGenerator
from .test_manager import TestFileManager
# from .angular_test_manager import AngularTestFileManager
from .test_runner import TestRunner
# from .angular_test_runner import AngularTestRunner
# from .angular_dependency_manager import AngularDependencyManager


def check_prerequisites(language, framework):
    """Check if required tools are available."""
    missing_tools = []
    NODE_PATH = os.environ.get('NODE_PATH', 'node')
    NPM_BIN_PATH = os.environ.get('NPM_BIN_PATH', 'npm')
    
    if language == 'typescript' and framework == 'angular':
        # Test Node.js
        try:
            result = subprocess.run([os.environ.get(NODE_PATH, 'node'), '--version'], 
                                  capture_output=True, text=True, timeout=10, shell=True)
            if result.returncode != 0:
                missing_tools.append('Node.js')
            else:
                print(f"✅ Node.js version: {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            missing_tools.append('Node.js (timeout)')
        except Exception as e:
            missing_tools.append(f'Node.js ({str(e)})')
        
        # Test npm
        try:
            result = subprocess.run([NPM_BIN_PATH, '--version'], 
                                  capture_output=True, text=True, timeout=10, shell=True)
            if result.returncode != 0:
                missing_tools.append(NPM_BIN_PATH)
            else:
                print(f"✅ npm version: {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            missing_tools.append('npm (timeout)')
        except Exception as e:
            missing_tools.append(f'npm ({str(e)})')
    
    return missing_tools

# Load environment variables
load_dotenv()

@click.command()
@click.option('--repo', required=True, help='GitHub repository URL')
@click.option('--target-dir', default=None, help='Target directory for cloning (default: temp directory)')
@click.option('--branch', default='main', help='Branch to use for cloning (default: main)')
@click.option('--commit-message', default=None, help='Commit message for the generated test files')
@click.option('--run-tests', is_flag=True, default=True, help='Run tests after generation')
@click.option('--cleanup', is_flag=True, default=False, help='Clean up cloned repository after completion')
@click.option('--use-temp', is_flag=True, default=False, help='Use temporary directory for cloning')
@click.option('--framework', default=None, help='Force specific framework (flask, django, fastapi, angular, general)')
@click.option('--skip-deps', is_flag=True, default=False, help='Skip dependency installation')
def main(repo, target_dir, branch, commit_message, run_tests, cleanup, use_temp, framework, skip_deps):
    """
    GenAI Test Generator Tool - Generate AI-powered test cases for Python and Angular repositories.
    
    Example:
        python -m genai_testgen_tool.cli --repo https://github.com/example/python-project
        python -m genai_testgen_tool.cli --repo https://github.com/example/flask-app --framework flask
        python -m genai_testgen_tool.cli --repo https://github.com/example/angular-app --framework angular
    """
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        click.echo("Error: OPENAI_API_KEY environment variable is required.")
        click.echo("Please set your OpenAI API key in the .env file or environment variables.")
        sys.exit(1)
    
    cloner = RepoCloner()
    
    try:
        main_directory = os.getcwd()
        # Use temporary directory if requested or if target_dir causes issues
        if use_temp or target_dir is None:
            temp_dir = tempfile.mkdtemp(prefix='genai_testgen_')
            repo_name = repo.rstrip('/').split('/')[-1].replace('.git', '')
            target_dir = os.path.join(temp_dir, repo_name)
            click.echo(f"Using temporary directory: {target_dir}")
        
        # Step 1: Clone repository
        click.echo(f"🔄 Cloning repository: {repo}")
        repo_path = cloner.clone_repo(repo, target_dir)
        
        # Step 2: Detect language and framework
        click.echo("🔍 Detecting language and framework...")
        detector = LanguageDetector()
        language, detected_framework = detector.detect_language(repo_path)
        
        # Use forced framework if provided, otherwise use detected
        final_framework = framework.lower() if framework else detected_framework

        missing_tools = check_prerequisites(language, final_framework)
        if missing_tools:
            click.echo(f"⚠️ Warning: Missing required tools: {', '.join(missing_tools)}")
            if language == 'typescript' and final_framework == 'angular':
                click.echo("For Angular projects, you need:")
                click.echo("  • Node.js: https://nodejs.org/")
                click.echo("  • npm (comes with Node.js)")
                click.echo("Some features may not work without these tools.")
                
                if not click.confirm("Continue anyway?"):
                    sys.exit(1)
        
        # Validate supported languages
        supported_languages = ['python', 'typescript']
        if language not in supported_languages:
            click.echo(f"❌ Error: Currently only Python and TypeScript/Angular repositories are supported. Detected: {language}")
            return
        
        click.echo(f"✅ Detected: {language} with {final_framework}")
        if framework:
            click.echo(f"🔧 Framework overridden to: {final_framework}")
        
        # Step 3: Install dependencies based on language
        if language == 'typescript' and final_framework == 'angular':
            click.echo("📦 Setting up Angular dependencies...")
            dep_manager = AngularDependencyManager(repo_path, main_directory)
            
            if not dep_manager.install_dependencies():
                click.echo("❌ Failed to install dependencies. Continuing anyway...")
            
            if not dep_manager.ensure_test_dependencies():
                click.echo("❌ Failed to ensure test dependencies. Continuing anyway...")
            
            if not dep_manager.setup_karma_config():
                click.echo("❌ Failed to setup Karma config. Continuing anyway...")

        
        # Step 4: Extract functions based on language
        click.echo("📝 Extracting functions from source code...")
        
        if language == 'python':
            extractor = FunctionExtractor()
            functions_by_file = extractor.extract_python_functions(repo_path, final_framework)
        elif language == 'typescript' and final_framework == 'angular':
            extractor = AngularExtractor()
            functions_by_file = extractor.extract_angular_functions(repo_path)
        else:
            click.echo(f"❌ Unsupported combination: {language} with {final_framework}")
            return
        
        if not functions_by_file:
            click.echo("❌ No functions found to generate tests for.")
            return
        
        total_functions = sum(len(funcs) for funcs in functions_by_file.values())
        click.echo(f"✅ Found {total_functions} functions across {len(functions_by_file)} files")
        
        # Display file summary with framework info
        for file_path, functions in functions_by_file.items():
            relative_path = os.path.relpath(file_path, repo_path)
            framework_info = functions[0].get('framework', final_framework) if functions else final_framework
            click.echo(f"  📄 {relative_path}: {len(functions)} functions ({framework_info})")
        
        # Step 5: Generate tests using AI for all files
        click.echo("🤖 Generating test cases using AI...")
        ai_generator = AITestGenerator()
        generated_tests = ai_generator.generate_tests_for_functions(functions_by_file, language, final_framework)
        
        if not generated_tests:
            click.echo("❌ No tests were generated.")
            return
        
        click.echo(f"✅ Generated tests for {len(generated_tests)} files")
        
        # Step 6: Create test files based on language
        click.echo("📁 Creating test files...")
        
        if language == 'python':
            test_manager = TestFileManager(repo_path, final_framework)
            test_files = test_manager.create_test_files(generated_tests)
        elif language == 'typescript' and final_framework == 'angular':
            test_manager = AngularTestFileManager(repo_path, final_framework)
            test_files = test_manager.create_test_files(generated_tests)
            # Update test configuration
            test_manager.update_test_config()
        
        click.echo(f"✅ Created {len(test_files)} test files")
        for test_file in test_files:
            relative_test_path = os.path.relpath(test_file, repo_path)
            click.echo(f"  📝 {relative_test_path}")
        
        # Step 7: Run tests based on language (if requested)
        if run_tests:
            click.echo("🧪 Running tests with coverage...")
            
            if language == 'python':
                test_runner = TestRunner(repo_path)
                results = test_runner.run_tests()
                
                if results['success']:
                    click.echo("✅ All tests passed!")
                else:
                    click.echo("❌ Some tests failed. Check the output above.")
                    click.echo(f"Return code: {results.get('return_code', 'Unknown')}")
                
                # Generate coverage report
                click.echo("📊 Generating coverage report...")
                coverage_report = test_runner.generate_coverage_report()
                
                # Display coverage summary
                if 'coverage_info' in results and results['coverage_info']:
                    coverage = results['coverage_info'].get('total_coverage', 'Unknown')
                    click.echo(f"📈 Total Coverage: {coverage}")
            
            elif language == 'typescript' and final_framework == 'angular':
                test_runner = AngularTestRunner(repo_path)
                results = test_runner.run_tests()
                
                if results['success']:
                    click.echo("✅ All tests passed!")
                else:
                    click.echo("❌ Some tests failed. Trying Karma fallback...")
                    # Try Karma as fallback
                    karma_results = test_runner.run_tests_with_karma()
                    if karma_results['success']:
                        click.echo("✅ Tests passed with Karma!")
                        results = karma_results
                    else:
                        click.echo("❌ Tests failed with both ng test and Karma.")
                        click.echo(f"Return code: {results.get('return_code', 'Unknown')}")
                
                # Generate coverage report
                click.echo("📊 Generating coverage report...")
                coverage_report = test_runner.generate_coverage_report()
                
                # Display coverage summary
                if 'coverage_info' in results and results['coverage_info']:
                    coverage = results['coverage_info'].get('total_coverage', 'Unknown')
                    click.echo(f"📈 Total Coverage: {coverage}")
        
        click.echo("\n🎉 Test generation completed successfully!")
        click.echo(f"📂 Repository location: {repo_path}")
        
        if language == 'python':
            click.echo(f"📁 Tests location: {os.path.join(repo_path, 'tests')}")
            if os.path.exists(os.path.join(repo_path, 'htmlcov')):
                click.echo(f"📊 Coverage report: {os.path.join(repo_path, 'htmlcov', 'index.html')}")
        elif language == 'typescript' and final_framework == 'angular':
            click.echo(f"📁 Tests location: {os.path.join(repo_path, 'src', 'app')} (*.spec.ts files)")
            if os.path.exists(os.path.join(repo_path, 'coverage')):
                click.echo(f"📊 Coverage report: {os.path.join(repo_path, 'coverage', 'index.html')}")
        
        # Summary statistics
        click.echo("\n📊 Summary:")
        click.echo(f"  • Language: {language}")
        click.echo(f"  • Framework: {final_framework}")
        click.echo(f"  • Files processed: {len(functions_by_file)}")
        click.echo(f"  • Functions found: {total_functions}")
        click.echo(f"  • Test files created: {len(test_files)}")

        # GitHub push functionality
        click.echo("🚀 Pushing test files to GitHub...")
        click.echo()
        
        # Use context manager to handle directory navigation
        # Pass both repo_path and repo_url to GitManager
        with GitManager(repo_path, repo) as git_manager:
            # Connect to existing repository
            if not git_manager.connect_to_existing_repo():
                click.echo("❌ Failed to connect to Git repository")
                sys.exit(1)
            
            # Ensure origin remote is set correctly
            if not git_manager.ensure_origin_remote():
                click.echo("❌ Failed to set up origin remote")
                sys.exit(1)
            
            # Show current status
            git_manager.show_status()
            click.echo()
            
            # Create branch for test files
            test_branch = f"test-generation-{branch}-{language}"
            if not git_manager.create_branch(test_branch):
                click.echo("❌ Failed to create branch")
                sys.exit(1)
            
            # Stage test files
            if not git_manager.stage_files(test_files):
                click.echo("❌ Failed to stage test files")
                sys.exit(1)
            
            # Commit test files
            final_commit_message = commit_message or f"Add AI-generated {language} test files for {final_framework} project"
            if not git_manager.commit_changes(final_commit_message):
                click.echo("❌ Failed to commit changes")
                sys.exit(1)
            
            # Push to GitHub (use origin as the remote)
            if not git_manager.push_to_remote(test_branch, 'origin'):
                click.echo("❌ Failed to push to GitHub")
                sys.exit(1)
            
            click.echo(f"✅ Successfully pushed test files to origin on branch '{test_branch}'")
            click.echo(f"🔗 You can view the changes at: {repo}/tree/{test_branch}")
            click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        import traceback
        click.echo(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
    
    finally:
        # Cleanup if requested
        if cleanup:
            click.echo("🧹 Cleaning up...")
            cloner.cleanup()

if __name__ == '__main__':
    main()

