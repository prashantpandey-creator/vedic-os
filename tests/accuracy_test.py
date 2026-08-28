import requests
import json

OLLAMA_URL = "http://127.0.0.1:11434"
PROMPT = "Write a Python function to extract all email addresses from a given text string, but ONLY if they belong to a '.edu' domain. Return the emails as a list. Do not include any other explanation, just the code."

models_to_test = ["phi3:latest", "qwen3:4b-instruct-2507-q4_K_M"]

print("Running Accuracy & Instruction Following Test...\n")

for m in models_to_test:
    print(f"--- MODEL: {m} ---")
    payload = {
        "model": m,
        "prompt": PROMPT,
        "stream": False,
        "options": {"temperature": 0.0} # Zero temperature for deterministic output
    }
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        data = response.json()
        print(data.get("response", "").strip())
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Failed to query {m}: {e}")
