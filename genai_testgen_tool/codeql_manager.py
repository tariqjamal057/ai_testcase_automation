import os
import yaml
from typing import Dict, Any

class CodeQLManager:
    """Manages CodeQL workflow files for GitHub Actions."""
    
    def __init__(self, repo_path: str):
        self.original_cwd = os.getcwd()
        self.repo_path = os.path.join(self.original_cwd, repo_path)
        self.github_workflows_dir = os.path.join(self.repo_path, '.github', 'workflows')
        self.codeql_file_path = os.path.join(self.github_workflows_dir, 'codeql.yml')
    
    def ensure_codeql_workflow(self, language: str, framework: str = None) -> bool:
        """
        Ensure CodeQL workflow exists, create if missing.
        
        Args:
            language: Programming language (python, typescript)
            framework: Framework name (optional)
            
        Returns:
            bool: True if workflow exists or was created successfully
        """
        if self.codeql_workflow_exists():
            print("✅ CodeQL workflow already exists")
            return True
        
        return self.create_codeql_workflow(language, framework)
    
    def codeql_workflow_exists(self) -> bool:
        """Check if CodeQL workflow file exists."""
        return os.path.exists(self.codeql_file_path)
    
    def create_codeql_workflow(self, language: str, framework: str = None) -> bool:
        """
        Create CodeQL workflow file based on language and framework.
        
        Args:
            language: Programming language
            framework: Framework name
            
        Returns:
            bool: True if created successfully
        """
        try:
            # Ensure .github/workflows directory exists
            os.makedirs(self.github_workflows_dir, exist_ok=True)
            
            # Generate workflow content based on language
            workflow_content = self._generate_workflow_content(language, framework)
            
            # Write workflow file
            with open(self.codeql_file_path, 'w', encoding='utf-8') as f:
                f.write(workflow_content)
            
            print(f"✅ Created CodeQL workflow for {language}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create CodeQL workflow: {e}")
            return False
    
    def _generate_workflow_content(self, language: str, framework: str = None) -> str:
        """Generate CodeQL workflow content based on language."""
        
        if language == 'python':
            return self._get_python_workflow()
        elif language == 'typescript' and framework == 'angular':
            return self._get_angular_workflow()
        else:
            # Default workflow
            return self._get_default_workflow(language)
    
    def _get_python_workflow(self) -> str:
        """Get Python CodeQL workflow content."""
        return '''# For most projects, this workflow file will not need changing; you simply need
# to commit it to your repository.
#
# You may wish to alter this file to override the set of languages analyzed,
# or to provide custom queries or build logic.
#
# ******** NOTE ********
# We have attempted to detect the languages in your repository. Please check
# the `language` matrix defined below to confirm you have the correct set of
# supported CodeQL languages.
#
name: "CodeQL Advanced"

on:
  push:
    branches: [ "main", "master", "test-generation-*" ]
  pull_request:
    branches: [ "main", "master" ]
  schedule:
    - cron: '28 22 * * 3'

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    permissions:
      # required for all workflows
      security-events: write
      # required to fetch internal or private CodeQL packs
      packages: read
      # only required for workflows in private repositories
      actions: read
      contents: read

    strategy:
      fail-fast: false
      matrix:
        include:
        - language: python
          build-mode: none

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}
        build-mode: ${{ matrix.build-mode }}

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      with:
        category: "/language:${{matrix.language}}"
'''

    def _get_angular_workflow(self) -> str:
        """Get Angular/TypeScript CodeQL workflow content."""
        return '''# For most projects, this workflow file will not need changing; you simply need
# to commit it to your repository.
#
# You may wish to alter this file to override the set of languages analyzed,
# or to provide custom queries or build logic.
#
# ******** NOTE ********
# We have attempted to detect the languages in your repository. Please check
# the `language` matrix defined below to confirm you have the correct set of
# supported CodeQL languages.
#
name: "CodeQL Advanced"

on:
  push:
    branches: [ "main", "master", "test-generation-*" ]
  pull_request:
    branches: [ "main", "master" ]
  schedule:
    - cron: '28 22 * * 3'

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    permissions:
      # required for all workflows
      security-events: write
      # required to fetch internal or private CodeQL packs
      packages: read
      # only required for workflows in private repositories
      actions: read
      contents: read

    strategy:
      fail-fast: false
      matrix:
        include:
        - language: javascript-typescript
          build-mode: none

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}
        build-mode: ${{ matrix.build-mode }}

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      with:
        category: "/language:${{matrix.language}}"
'''

    def _get_default_workflow(self, language: str) -> str:
        """Get default CodeQL workflow content."""
        return f'''# For most projects, this workflow file will not need changing; you simply need
# to commit it to your repository.
#
name: "CodeQL Advanced"

on:
  push:
    branches: [ "main", "master", "test-generation-*" ]
  pull_request:
    branches: [ "main", "master" ]
  schedule:
    - cron: '28 22 * * 3'

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      packages: read
      actions: read
      contents: read

    strategy:
      fail-fast: false
      matrix:
        include:
        - language: {language}
          build-mode: none

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Initialize CodeQL
      uses: github/codeql-action/init@v3
      with:
        languages: ${{ matrix.language }}
        build-mode: ${{ matrix.build-mode }}

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v3
      with:
        category: "/language:${{matrix.language}}"
'''

    def get_workflow_file_path(self) -> str:
        """Get the path to the CodeQL workflow file."""
        return self.codeql_file_path
