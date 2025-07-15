import os
import subprocess
import git
from typing import Optional, List
from datetime import datetime

class GitManager:
    """Manages Git operations for pushing test code to GitHub."""
    
    def __init__(self, repo_path: str, repo_url: str):
        self.repo_path = repo_path
        self.repo_url = repo_url
        self.repo = None
        self.original_cwd = os.getcwd()
        
    def __enter__(self):
        """Context manager entry - navigate to repo directory."""
        os.chdir(self.repo_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - return to original directory."""
        os.chdir(self.original_cwd)
        
    def connect_to_existing_repo(self) -> bool:
        """Connect to existing Git repository."""
        try:
            print(f"🔍 Checking for Git repository at {self.repo_path}...")
            print(f"Current working directory: {os.getcwd()}")
            
            git_dir = os.path.join(self.repo_path, '.git')
            print(f"Looking for .git at: {git_dir}")
            print(f"Repo path exists: {os.path.exists(self.repo_path)}")
            print(f"Git directory exists: {os.path.exists(git_dir)}")
            
            if not os.path.exists(self.repo_path):
                print(f"❌ Repository path does not exist: {self.repo_path}")
                return False
                
            if not os.path.exists(git_dir):
                print(f"❌ No Git repository found at {self.repo_path}")
                print(f"   Looking for .git directory at: {git_dir}")
                # List contents of repo_path for debugging
                if os.path.exists(self.repo_path):
                    contents = os.listdir(self.repo_path)
                    print(f"   Directory contents: {contents}")
                return False
            
            self.repo = git.Repo(self.repo_path)
            print(f"✅ Connected to existing Git repository at {self.repo_path}")
            
            # Show current branch and status
            current_branch = self.repo.active_branch.name
            print(f"📍 Current branch: {current_branch}")
            
            # Show remotes
            remotes = [remote.name for remote in self.repo.remotes]
            if remotes:
                print(f"🔗 Remotes: {', '.join(remotes)}")
                # Show remote URLs
                for remote in self.repo.remotes:
                    print(f"   {remote.name}: {remote.url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to Git repository: {e}")
            print(f"   Repository path: {self.repo_path}")
            print(f"   Current working directory: {os.getcwd()}")
            return False
    
    def ensure_origin_remote(self) -> bool:
        """Ensure origin remote points to the correct URL."""
        try:
            if not self.repo:
                return False
            
            # Check if origin remote exists
            try:
                origin_remote = self.repo.remote('origin')
                if origin_remote.url != self.repo_url:
                    print(f"🔧 Updating origin remote from {origin_remote.url} to {self.repo_url}")
                    origin_remote.set_url(self.repo_url)
                else:
                    print(f"✅ Origin remote already points to correct URL: {self.repo_url}")
            except git.exc.InvalidGitRepositoryError:
                print(f"➕ Adding origin remote: {self.repo_url}")
                self.repo.create_remote('origin', self.repo_url)
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up origin remote: {e}")
            return False
    
    def add_remote(self, remote_url: str, remote_name: str = 'test-origin') -> bool:
        """Add a remote repository for pushing test files."""
        try:
            if not self.repo:
                return False
                
            # Check if remote already exists
            try:
                existing_remote = self.repo.remote(remote_name)
                if existing_remote.url != remote_url:
                    self.repo.delete_remote(existing_remote)
                    self.repo.create_remote(remote_name, remote_url)
                    print(f"✅ Updated remote '{remote_name}' to {remote_url}")
                else:
                    print(f"✅ Remote '{remote_name}' already exists with correct URL")
            except git.exc.InvalidGitRepositoryError:
                self.repo.create_remote(remote_name, remote_url)
                print(f"✅ Added remote '{remote_name}': {remote_url}")
                
            return True
        except Exception as e:
            print(f"❌ Error adding remote: {e}")
            return False
    
    def create_branch(self, branch_name: str) -> bool:
        """Create and checkout a new branch."""
        try:
            if not self.repo:
                return False
            
            # Check if branch already exists
            existing_branches = [ref.name.split('/')[-1] for ref in self.repo.refs]
            
            if branch_name in existing_branches:
                print(f"⚠️ Branch '{branch_name}' already exists, switching to it")
                self.repo.git.checkout(branch_name)
            else:
                # Create new branch from current HEAD
                current_branch = self.repo.active_branch
                new_branch = self.repo.create_head(branch_name, current_branch.commit)
                new_branch.checkout()
                print(f"✅ Created and switched to branch '{branch_name}'")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating branch: {e}")
            return False
    
    def stage_files(self, files: List[str]) -> bool:
        """Stage specific files for commit."""
        try:
            if not self.repo:
                return False
            
            staged_files = []
            for file_path in files:
                # Convert absolute path to relative path from repo root
                if os.path.isabs(file_path):
                    rel_path = os.path.relpath(file_path, self.repo_path)
                else:
                    rel_path = file_path
                
                # Check if file exists
                full_path = os.path.join(self.repo_path, rel_path)
                if os.path.exists(full_path):
                    self.repo.index.add([rel_path])
                    staged_files.append(rel_path)
                    print(f"📝 Staged: {rel_path}")
                else:
                    print(f"⚠️ File not found: {rel_path}")
            
            if staged_files:
                print(f"✅ Staged {len(staged_files)} files")
                return True
            else:
                print("❌ No files were staged")
                return False
                
        except Exception as e:
            print(f"❌ Error staging files: {e}")
            return False
    
    def commit_changes(self, commit_message: str) -> bool:
        """Commit staged changes."""
        try:
            if not self.repo:
                return False
            
            # Check if there are staged changes
            if not self.repo.index.diff("HEAD"):
                print("⚠️ No staged changes to commit")
                return True
            
            # Create commit
            commit = self.repo.index.commit(commit_message)
            print(f"✅ Committed changes: {commit.hexsha[:8]} - {commit_message}")
            return True
            
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            return False
    
    def push_to_remote(self, branch: str, remote_name: str = 'origin') -> bool:
        """Push current branch to remote."""
        try:
            if not self.repo:
                return False
            
            # Get the remote
            try:
                remote = self.repo.remote(remote_name)
            except git.exc.InvalidGitRepositoryError:
                print(f"❌ Remote '{remote_name}' not found")
                return False
            
            # Push to the specified branch
            print(f"🚀 Pushing to {remote_name}/{branch}...")
            push_info = remote.push(f'HEAD:{branch}')
            
            for info in push_info:
                if info.flags & info.ERROR:
                    print(f"❌ Push failed: {info.summary}")
                    return False
                elif info.flags & info.REJECTED:
                    print(f"❌ Push rejected: {info.summary}")
                    return False
                else:
                    print(f"✅ Successfully pushed to {remote_name}/{branch}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error pushing to remote: {e}")
            return False
    
    def get_repo_status(self) -> dict:
        """Get repository status information."""
        try:
            if not self.repo:
                return {}
            
            status = {
                'branch': self.repo.active_branch.name,
                'is_dirty': self.repo.is_dirty(),
                'untracked_files': self.repo.untracked_files,
                'modified_files': [item.a_path for item in self.repo.index.diff(None)],
                'staged_files': [item.a_path for item in self.repo.index.diff('HEAD')],
                'remotes': [remote.name for remote in self.repo.remotes]
            }
            
            return status
            
        except Exception as e:
            print(f"❌ Error getting repo status: {e}")
            return {}
    
    def show_status(self):
        """Display current repository status."""
        status = self.get_repo_status()
        if status:
            print(f"📊 Repository Status:")
            print(f"  • Branch: {status['branch']}")
            print(f"  • Dirty: {status['is_dirty']}")
            print(f"  • Untracked files: {len(status['untracked_files'])}")
            print(f"  • Modified files: {len(status['modified_files'])}")
            print(f"  • Staged files: {len(status['staged_files'])}")
            print(f"  • Remotes: {', '.join(status['remotes'])}")
