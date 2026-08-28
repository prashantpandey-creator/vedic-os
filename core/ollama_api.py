import requests

OLLAMA_URL = "http://127.0.0.1:11434"

def get_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        return []
    except Exception:
        return []

def get_loaded_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/ps")
        if response.status_code == 200:
            return response.json().get("models", [])
        return []
    except Exception:
        return []

def get_model_details(model_name):
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            for m in response.json().get("models", []):
                if m.get("name") == model_name:
                    return m
        return None
    except:
        return None

def evict_model(model_name, timeout=2):
    try:
        requests.post(f"{OLLAMA_URL}/api/generate", json={"model": model_name, "keep_alive": 0}, timeout=timeout)
    except:
        pass
