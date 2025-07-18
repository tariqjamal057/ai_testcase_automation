from setuptools import setup, find_packages

setup(
    name="genai-testgen-tool",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "gitpython>=3.1.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "click>=8.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "genai-create-tests=genai_testgen_tool.cli:main",
            "genai-testgen-tool=genai_testgen_tool.cli:main",  # Add this line
        ],
    },
    author="GenAI TestGen Tool",
    description="AI-powered test case generator for Python repositories",
    python_requires=">=3.8",
)
