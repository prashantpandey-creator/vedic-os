import requests
from config import OLLAMA_URL

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

def pull_model(model_name):
    try:
        response = requests.post(f"{OLLAMA_URL}/api/pull", json={"name": model_name}, stream=True)
        return response
    except Exception:
        return None

def delete_model(model_name):
    try:
        response = requests.delete(f"{OLLAMA_URL}/api/delete", json={"name": model_name})
        return response.status_code == 200
    except Exception:
        return False

def evict_all_models():
    loaded = get_loaded_models()
    for m in loaded:
        evict_model(m.get("name"))
