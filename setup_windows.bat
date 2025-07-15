@echo off
echo GenAI Test Generator Tool - Windows Setup
echo ========================================

echo Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed or not in PATH
    echo Please install Node.js from: https://nodejs.org/
    echo After installation, restart your command prompt and run this script again
    pause
    exit /b 1
)

echo Node.js is installed
node --version

echo Checking npm installation...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo npm is not installed or not in PATH
    echo npm should come with Node.js installation
    pause
    exit /b 1
)

echo npm is installed
npm --version

echo Installing Python dependencies...
pip install -r requirements.txt

echo Setup completed successfully!
echo You can now run the tool with:
echo python -m genai_testgen_tool.cli --repo YOUR_REPO_URL

pause
