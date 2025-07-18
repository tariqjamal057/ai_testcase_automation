# GenAI Test Generator Tool

A Python CLI tool that:
1. Clones a public GitHub repo
2. Detects its language/framework
3. Uses OpenAI GPT-4 to generate test cases
4. Runs them using `pytest`, `xUnit`, or `Jasmine`

### 🔧 Install
```bash
pip install git+https://github.com/tariqjamal057/ai_testcase_automation.git
```

### 📝 Create .env in project directory and add below fields in env
```bash
OPENAI_API_KEY=secret_key
GENAI_MODEL=gpt-4
GENAI_TEMPERATURE=0.8
```

### 🚀 Usage
```bash
genai-create-tests --repo https://github.com/tariqjamal057/acculer_task.git --target-dir cloner --branch feat/testcase --commit-message "add test files"
```

---
