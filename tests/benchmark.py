import requests
import json
import time

OLLAMA_URL = "http://127.0.0.1:11434"
PROMPT = "Write a python function to compute the fibonacci sequence."

def get_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        if response.status_code == 200:
            return [m["name"] for m in response.json().get("models", [])]
    except:
        pass
    return []

def benchmark_model(model_name):
    print(f"\n--- Benchmarking {model_name} ---")
    payload = {
        "model": model_name,
        "prompt": PROMPT,
        "stream": False,
        "options": {"num_predict": 100} # limit output for faster testing
    }
    
    start_time = time.time()
    try:
        # Pre-load or just measure full time
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        total_duration = data.get("total_duration", 0) / 1e9 # seconds
        load_duration = data.get("load_duration", 0) / 1e9 # seconds
        eval_count = data.get("eval_count", 0)
        eval_duration = data.get("eval_duration", 0) / 1e9 # seconds
        
        tps = eval_count / eval_duration if eval_duration > 0 else 0
        
        print(f"Total Time: {total_duration:.2f}s")
        print(f"Load Time: {load_duration:.2f}s")
        print(f"Tokens/sec: {tps:.2f} tokens/s")
        print(f"Output preview: {data.get('response', '')[:100]}...")
        
        return {
            "model": model_name,
            "total_time": total_duration,
            "load_time": load_duration,
            "tps": tps,
            "response": data.get("response", "")
        }
    except Exception as e:
        print(f"Failed: {e}")
        return None

if __name__ == "__main__":
    models = get_models()
    print(f"Found models: {models}")
    
    results = []
    for m in models:
        res = benchmark_model(m)
        if res:
            results.append(res)
    
    print("\n\n=== FINAL SUMMARY ===")
    results.sort(key=lambda x: x["tps"], reverse=True)
    for r in results:
        print(f"{r['model']}: {r['tps']:.2f} tokens/sec | Load: {r['load_time']:.2f}s | Quality Preview: {r['response'][:40].strip()}...")
