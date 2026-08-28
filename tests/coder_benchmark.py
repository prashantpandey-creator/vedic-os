# Test from Puran Code
import requests
import json
import time
import argparse

OLLAMA_URL = "http://127.0.0.1:11434"

def clear_all_vram_except(model_to_keep=None):
    try:
        ps_res = requests.get(f"{OLLAMA_URL}/api/ps")
        if ps_res.status_code == 200:
            for m in ps_res.json().get("models", []):
                name = m.get("name")
                if name != model_to_keep:
                    requests.post(f"{OLLAMA_URL}/api/generate", json={"model": name, "keep_alive": 0})
    except: pass

def run_benchmark(verbose=False):
    print("Running Benchmark...")
    if verbose:
        print('Verbose mode enabled')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    run_benchmark(args.verbose)
