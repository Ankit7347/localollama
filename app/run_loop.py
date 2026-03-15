import requests
import json
import time
import os
import re

# Configuration
API_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-coder:1.3b"
OUTPUT_FILE = "ai_responses.json"
DELAY = 2  # seconds between requests

prompts = [
    "Write a Python quicksort function",
    "Explain the Fibonacci algorithm",
    "Generate a simple REST API in Flask"
]

# Load existing responses if file exists
if os.path.exists(OUTPUT_FILE):
    try:
        with open(OUTPUT_FILE, "r") as f:
            data_store = json.load(f)
    except json.JSONDecodeError:
        data_store = []
else:
    data_store = []

def extract_code(text):
    """
    Extract Python code from text returned by Ollama.
    Removes markdown fences and extra description.
    """
    # Match ```python ... ``` or ``` ... ```
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if code_blocks:
        return "\n".join(code_blocks).strip()
    else:
        # If no code fences, return full text stripped
        return text.strip()

for prompt in prompts:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(API_URL, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()

        full_text = result.get("response", "")
        code_only = extract_code(full_text)

        # Store prompt + cleaned code
        entry = {
            "prompt": prompt,
            "response": code_only
        }

        data_store.append(entry)

        # Save after each generation
        temp_file = OUTPUT_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(data_store, f, indent=2)
        os.replace(temp_file, OUTPUT_FILE)

        print(f"[OK] Prompt processed: {prompt}")

    except Exception as e:
        print(f"[ERROR] Prompt failed: {prompt}")
        print(e)

    time.sleep(DELAY)

print("All prompts completed.")