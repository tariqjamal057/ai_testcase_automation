import os
import shutil
import git
import stat
import time
from urllib.parse import urlparse

class RepoCloner:
    """Handles cloning of GitHub repositories."""
    
    def __init__(self):
        self.cloned_repos = []
    
    def clone_repo(self, repo_url, target_dir=None):
        """
        Clone a GitHub repository to a local directory.
        
        Args:
            repo_url (str): GitHub repository URL
            target_dir (str): Target directory for cloning
            
        Returns:
            str: Path to the cloned repository
        """
        try:
            # Parse repository name from URL
            parsed_url = urlparse(repo_url)
            print(f"Parsed URL: {parsed_url}")
            repo_name = os.path.basename(parsed_url.path).replace('.git', '')
            print(f"Repository name: {repo_name}")
            
            if target_dir is None:
                target_dir = os.path.join(os.getcwd(), repo_name)
            
            # Remove existing directory if it exists (with Windows permission handling)
            if os.path.exists(target_dir):
                print(f"Removing existing directory: {target_dir}")
                self._remove_directory_windows_safe(target_dir)
            
            print(f"Cloning repository: {repo_url}")
            print(f"Target directory: {target_dir}")
            
            # Clone the repository
            git.Repo.clone_from(repo_url, target_dir)
            
            self.cloned_repos.append(target_dir)
            # add init file in root fodler
            init_file_path = os.path.join(target_dir, '__init__.py')
            if not os.path.exists(init_file_path):
                with open(init_file_path, 'w') as init_file:
                    init_file.write('# This is an init file for the cloned repository\n')
            print(f"Successfully cloned repository to: {target_dir}")
            
            return target_dir
            
        except Exception as e:
            print(f"Error cloning repository: {e}")
            raise
    
    def _remove_directory_windows_safe(self, path):
        """
        Remove directory with Windows-safe permission handling.
        """
        def handle_remove_readonly(func, path, exc):
            """
            Error handler for Windows readonly files.
            """
            if os.path.exists(path):
                # Change the file to be writable and try again
                os.chmod(path, stat.S_IWRITE)
                func(path)
        
        try:
            # First attempt: normal removal
            shutil.rmtree(path)
        except PermissionError:
            try:
                # Second attempt: handle readonly files
                shutil.rmtree(path, onerror=handle_remove_readonly)
            except Exception as e:
                print(f"Warning: Could not remove directory {path}: {e}")
                # Try alternative method for stubborn Windows files
                self._force_remove_windows(path)
    
    def _force_remove_windows(self, path):
        """
        Force remove directory on Windows using alternative methods.
        """
        try:
            # Method 1: Use os.system with rmdir command
            if os.name == 'nt':  # Windows
                import subprocess
                subprocess.run(['rmdir', '/s', '/q', path], shell=True, check=False)
            
            # Method 2: Manual recursive removal with permission changes
            if os.path.exists(path):
                for root, dirs, files in os.walk(path, topdown=False):
                    # Remove files
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, stat.S_IWRITE)
                            os.remove(file_path)
                        except Exception:
                            pass
                    
                    # Remove directories
                    for dir in dirs:
                        dir_path = os.path.join(root, dir)
                        try:
                            os.chmod(dir_path, stat.S_IWRITE)
                            os.rmdir(dir_path)
                        except Exception:
                            pass
                
                # Remove the root directory
                try:
                    os.chmod(path, stat.S_IWRITE)
                    os.rmdir(path)
                except Exception:
                    pass
        
        except Exception as e:
            print(f"Warning: Force removal failed for {path}: {e}")
            print("You may need to manually delete the directory")
    
    def cleanup(self):
        """Clean up cloned repositories."""
        for repo_path in self.cloned_repos:
            if os.path.exists(repo_path):
                try:
                    print(f"Cleaning up: {repo_path}")
                    self._remove_directory_windows_safe(repo_path)
                    print(f"Successfully cleaned up: {repo_path}")
                except Exception as e:
                    print(f"Error cleaning up {repo_path}: {e}")
