import sys

with open("/Users/badenath/projects/local-llm-ui/core/ollama_api.py", "a") as f:
    f.write("""
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
""")
print("Added model manager functions to ollama_api.py")
