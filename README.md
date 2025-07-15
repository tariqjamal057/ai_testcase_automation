# GenAI Test Generator Tool

A Python CLI tool that:
1. Clones a public GitHub repo
2. Detects its language/framework
3. Uses OpenAI GPT-4 to generate test cases
4. Runs them using `pytest`, `xUnit`, or `Jasmine`

### 🔧 Install
```bash
pip install git+https://github.com/yourusername/genai-testgen-tool.git
```

### 🚀 Usage
```bash
genai-create-tests --repo https://github.com/example/project
```

---
