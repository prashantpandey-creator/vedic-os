import requests

OLLAMA_URL = "http://127.0.0.1:11434"

def get_loaded_models():
    """Returns a list of currently loaded models in VRAM."""
    try:
        res = requests.get(f"{OLLAMA_URL}/api/ps", timeout=2)
        if res.status_code == 200:
            return [m["name"] for m in res.json().get("models", [])]
    except Exception as e:
        print(f"[VRAM] Failed to reach Ollama: {e}")
    return []

def evict_model(model_name: str):
    """Evicts a specific model from VRAM by setting keep_alive to 0."""
    print(f"[VRAM] 🧹 Evicting {model_name} from memory...")
    try:
        requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model_name,
            "keep_alive": 0
        }, timeout=2)
    except: pass

def clear_all_vram_except(allowed_models: list):
    """Purges all heavy/unused models from VRAM to prevent system hanging."""
    loaded = get_loaded_models()
    for model in loaded:
        if model not in allowed_models:
            evict_model(model)
            
def enforce_context_window(messages: list, max_turns=6):
    """
    Prevents Context Bloat: Keeps the system prompt + the last `max_turns` messages.
    Everything in the middle is brutally truncated to save VRAM and compute.
    """
    if len(messages) > (max_turns + 2):
        print("[MEMORY] ✂️ Truncating context to prevent memory leak...")
        system_prompt = messages[0]
        recent = messages[-max_turns:]
        messages.clear()
        messages.append(system_prompt)
        messages.extend(recent)
    return messages

