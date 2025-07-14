import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AITestGenerator:
    """Generates test cases using OpenAI's GPT model."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("GENAI_MODEL", "gpt-4")
        self.temperature = float(os.getenv("GENAI_TEMPERATURE", "0.2"))
        self.prompt_template = None

    def _load_prompt_template(self, language, framework):
        """
        Load the prompt template based on language and framework.
        Path convention: prompts/{language}/{framework}.txt
        """
        prompt_dir = os.path.join(
            os.path.dirname(__file__), "prompts", language.lower()
        )
        prompt_file_name = f"{framework.lower()}.txt"
        prompt_path = os.path.join(prompt_dir, prompt_file_name)
        print(prompt_dir)
        print(prompt_path)

        if not os.path.exists(prompt_path):
            print(
                f"Warning: Specific prompt for {language}/{framework} not found at {prompt_path}. Falling back to general prompt."
            )
            prompt_path = os.path.join(
                prompt_dir, "general.txt"
            )  # Fallback to general prompt

        if not os.path.exists(prompt_path):
            raise FileNotFoundError(
                f"No prompt template found for {language}/{framework} or general at {prompt_path}"
            )

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _detect_framework_with_ai(self, functions_by_file):
        """Use AI to detect the framework based on function patterns."""
        try:
            # Collect sample code from functions
            sample_code = ""
            for file_path, functions in list(functions_by_file.items())[
                :3
            ]:  # Sample first 3 files
                for func in functions[:2]:  # Sample first 2 functions per file
                    sample_code += f"{func['source_code']}\n\n"

            prompt = f"""
            Analyze the following Python code and determine the web framework being used.
            Return ONLY the framework name in lowercase (flask, django, fastapi, or general).
            
            Code to analyze:
            {sample_code[:2000]}  # Limit to first 2000 chars
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Python framework detection expert. Analyze code and return only the framework name: flask, django, fastapi, or general.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=50,
            )

            detected_framework = response.choices[0].message.content.strip().lower()

            # Validate the response
            valid_frameworks = ["flask", "django", "fastapi", "general"]
            if detected_framework in valid_frameworks:
                print(f"AI detected framework: {detected_framework}")
                return detected_framework
            else:
                print(
                    f"AI returned invalid framework: {detected_framework}, using general"
                )
                return "general"

        except Exception as e:
            print(f"Error in AI framework detection: {e}")
            return "general"

    def generate_tests_for_file(self, file_path, functions, language, framework):
        """
        Generate test cases for all functions in a single file.

        Args:
            file_path (str): Path to the source file
            functions (list): List of function information from the file
            language (str): Programming language
            framework (str): Framework name

        Returns:
            str: Generated test code for all functions
        """
        try:
            # # Load the appropriate prompt template
            # if not self.prompt_template:
            #     self.prompt_template = self._load_prompt_template(language, framework)

            # Prepare all functions code with better formatting
            all_functions_code = ""
            for i, func in enumerate(functions, 1):
                all_functions_code += f"\n# Function {i}: {func['name']}\n"
                all_functions_code += f"# Arguments: {func['args']}\n"
                if func["docstring"]:
                    all_functions_code += f"# Docstring: {func['docstring']}\n"
                all_functions_code += f"```python\n{func['source_code']}\n```\n"
                all_functions_code += "-" * 50 + "\n"

            # Prepare the prompt
            print(language)
            print(framework)
            prompt_template = self._load_prompt_template(language, framework)
            print(f"promt {prompt_template=}")
            prompt = prompt_template.format(
                all_functions_code=all_functions_code, file_path=file_path
            )

            print(f"Sending prompt to AI for {len(functions)} functions...")
            print(f"Functions: {[func['name'] for func in functions]}")

            # Generate framework-specific system message
            system_messages = {
                "flask": "You are an expert Python Flask test engineer. Generate high-quality pytest unit tests for Flask applications using proper test client patterns. Mock external functions like random.randint(), uuid4(), datetime.now(), etc. using unittest.mock.patch. Use existing data from the application for testing. You MUST return ONLY valid Python test code. Do NOT provide explanations, comments, or ask questions. Generate test functions that start with 'def test_' and use client.get(), client.post(), etc. to test the provided Flask routes.",
                "django": "You are an expert Python Django test engineer. Generate high-quality pytest-django unit tests using proper Django test patterns. Return only the test code without any explanations or markdown formatting.",
                "fastapi": "You are an expert Python FastAPI test engineer. Generate high-quality pytest unit tests for FastAPI applications using TestClient. Return only the test code without any explanations or markdown formatting.",
                "general": "You are an expert Python test engineer. Generate high-quality pytest unit tests. Return only the test code without any explanations or markdown formatting.",
            }

            system_message = system_messages.get(framework, system_messages["general"])

            # Generate test using OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=4000,
            )

            test_code = response.choices[0].message.content

            # Clean up the response (remove markdown formatting if present)
            test_code = self._clean_ai_response(test_code)

            print(f"Generated test code length: {len(test_code)} characters")

            return test_code.strip()

        except Exception as e:
            print(f"Error generating tests for file {file_path}: {e}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            return None

    def _clean_ai_response(self, response):
        """Clean the AI response to extract only the test code."""
        # Remove markdown code blocks
        if "```python" in response:
            # Extract content between ```python and ```
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end != -1:
                response = response[start:end]
        elif "```" in response:
            # Extract content between ``` and ```
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                response = response[start:end]

        # Remove any leading/trailing whitespace
        response = response.strip()

        # Check if the response contains error messages
        error_phrases = [
            "Sorry, you didn't provide",
            "Please provide a Python function",
            "I need the function code",
            "No function provided",
            "In order to provide",
            "Could you please provide",
            "I would need to see",
        ]

        for phrase in error_phrases:
            if phrase.lower() in response.lower():
                print(f"AI returned error message: {response[:100]}...")
                return None

        return response

    def generate_tests_for_functions(self, functions_by_file, language, framework):
        """
        Generate tests for multiple files.

        Args:
            functions_by_file (dict): Functions grouped by file path
            language (str): Programming language
            framework (str): Framework name

        Returns:
            dict: Generated tests mapped by file path
        """
        # Use AI to detect framework if not already detected or if it's 'general'
        if framework == "general" or framework == "unknown":
            framework = self._detect_framework_with_ai(functions_by_file)

        generated_tests = {}

        for file_path, functions in functions_by_file.items():
            print(
                f"Generating tests for file: {file_path} ({len(functions)} functions)"
            )

            # Debug: Print function names
            function_names = [func["name"] for func in functions]
            print(f"Function names: {function_names}")

            test_code = self.generate_tests_for_file(
                file_path, functions, language, framework
            )

            if test_code:
                generated_tests[file_path] = {
                    "test_code": test_code,
                    "functions": functions,
                    "file_path": file_path,
                    "framework": framework,
                }
                print(
                    f"✅ Generated tests for {len(functions)} functions in {os.path.basename(file_path)}"
                )
            else:
                print(f"❌ Failed to generate tests for file: {file_path}")

        return generated_tests
