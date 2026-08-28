import os
import sys
import json
import time
import requests
import argparse

OLLAMA_URL = "http://127.0.0.1:11434"
ARCHITECT_MODEL = "architect-compiler"
CODER_MODEL = "qwen3:4b-instruct-2507-q4_K_M"

def clear_vram(model_name):
    print(f"🧹 Clearing VRAM for {model_name}...")
    try:
        requests.post(f"{OLLAMA_URL}/api/generate", json={"model": model_name, "keep_alive": 0}, timeout=5)
        time.sleep(0.5)
    except:
        pass

def generate_architecture(prompt):
    print(f"\n🧠 [THE ARCHITECT] Designing Blueprint for: '{prompt}'")
    payload = {
        "model": ARCHITECT_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
    response.raise_for_status()
    raw_json = response.json().get("response", "")
    
    # Strip markdown if present
    if "```json" in raw_json:
        raw_json = raw_json.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_json:
        raw_json = raw_json.split("```")[1].split("```")[0].strip()
        
    try:
        return json.loads(raw_json)
    except Exception as e:
        print("❌ The Architect failed to generate valid JSON!")
        print("Raw Output:", raw_json)
        sys.exit(1)

def write_code(entity):
    entity_id = entity.get("id", "unknown_file")
    entity_type = entity.get("type", "unknown_type")
    
    print(f"👨‍💻 [THE CODER] Writing code for {entity_type}: {entity_id}...")
    
    system_prompt = (
        "You are an elite software engineer. "
        "The System Architect has handed you a JSON blueprint node. "
        "Your job is to write the complete, production-ready code for this specific node. "
        "Do NOT output markdown. Do NOT output chat. Output ONLY the raw code."
    )
    
    payload = {
        "model": CODER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Write the code for this architectural node:\n{json.dumps(entity, indent=2)}"}
        ],
        "stream": False
    }
    
    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
    response.raise_for_status()
    code = response.json().get("message", {}).get("content", "")
    
    # Strip markdown if the coder hallucinated it
    if "```" in code:
        parts = code.split("```")
        if len(parts) >= 3:
            code = parts[1].split("\n", 1)[-1].strip()
            
    return code

def main():
    parser = argparse.ArgumentParser(description="Hybrid Multi-Agent Coder")
    parser.add_argument("prompt", type=str, help="The app description")
    args = parser.parse_args()
    
    # Phase 1: Architecture
    clear_vram(CODER_MODEL) # Make sure coder is unloaded
    graph = generate_architecture(args.prompt)
    
    app_name = graph.get("name", "GeneratedApp").replace(" ", "_")
    print(f"✅ Architecture generated! Found {len(graph.get('entities', []))} entities.")
    
    # Create project directory
    os.makedirs(app_name, exist_ok=True)
    
    # Save the raw blueprint
    with open(f"{app_name}/blueprint.json", "w") as f:
        json.dump(graph, f, indent=2)
        
    # Phase 2: Execution
    print(f"\n🚀 Initiating Execution Engine...")
    clear_vram(ARCHITECT_MODEL) # Make room for the Genius Coder
    
    for entity in graph.get("entities", []):
        entity_type = entity.get("type", "")
        # Only code actionable entities
        if entity_type in ["page", "component", "api_route", "data_model"]:
            code = write_code(entity)
            
            # Simple extension guesser
            ext = ".ts" if entity_type == "api_route" else ".tsx"
            filename = f"{entity.get('id')}{ext}"
            
            filepath = os.path.join(app_name, filename)
            with open(filepath, "w") as f:
                f.write(code)
            print(f"   💾 Saved to {filepath}")
            
    print(f"\n🎉 Build Complete! Check the '{app_name}' directory.")

if __name__ == "__main__":
    main()
