
import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Setup path to load backend modules if needed, but here we just need dotenv
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
load_dotenv(os.path.join(project_root, ".env"))

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key present: {bool(api_key)}")
if api_key:
    print(f"API Key (last 4): ...{api_key[-4:]}")

def test_model(model_name):
    print(f"\nTesting model: {model_name}")
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        result = llm.invoke("Hello, are you working?")
        print(f"Success! Response: {result.content}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

models_to_test = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
    "gemini-1.0-pro"
]

print("--- Starting LLM Debug ---")
for m in models_to_test:
    if test_model(m):
        break # Stop after first success
