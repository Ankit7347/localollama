import requests
import json
import time

# Configuration
API_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-coder:6.7b"
OUTPUT_FILE = "ai_responses.json"
DELAY = 2  # seconds between requests

prompts = [
    "Write a Python quicksort function",
    "Explain the Fibonacci algorithm",
    "Generate a simple REST API in Flask"
]

# Load existing responses if file exists
try:
    with open(OUTPUT_FILE, "r") as f:
        data_store = json.load(f)
except FileNotFoundError:
    data_store = []

for prompt in prompts:
    payload = {
        "model": MODEL,
        "prompt": prompt
    }

    try:
        # Use stream=True for real-time reading
        with requests.post(API_URL, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()
            full_text = ""

            # Read each line as Ollama streams output
            for line in response.iter_lines():
                if line:
                    try:
                        obj = json.loads(line.decode("utf-8"))
                        # Ollama usually returns {"text": "..."} in each chunk
                        if "text" in obj:
                            full_text += obj["text"]
                    except json.JSONDecodeError:
                        # Fallback: append raw line if not JSON
                        full_text += line.decode("utf-8")

        # Store prompt + response
        data_store.append({
            "prompt": prompt,
            "response": full_text
        })

        # Save to file after each prompt
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data_store, f, indent=2)

        print(f"[OK] Prompt processed: {prompt}")

    except Exception as e:
        print(f"[ERROR] Prompt failed: {prompt}, error: {e}")

    time.sleep(DELAY)