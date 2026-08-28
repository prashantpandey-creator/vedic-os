import argparse
import json
import os
import requests
import subprocess
import time
from pathlib import Path

OLLAMA_URL = "http://127.0.0.1:11434"
MEMORY_FILE = "PROJECT_MIND.md"
RESEARCH_MODEL = "granite4:3b-h" # Mamba for context
CODER_MODEL = "qwen2.5:32b" # The Genius for execution

def llm_call(model, system, user):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "stream": False,
        "options": {"temperature": 0.0}
    }
    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
    return response.json().get("message", {}).get("content", "")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return f.read()
    return "No established memories yet. The project mind is empty."

def save_memory(intent, files, status="pramana"):
    # Pramana = proven truth, Viparyaya = drifted
    entry = f"\n- **Intent:** {intent}\n  - **Files:** {', '.join(files)}\n  - **Status:** [{status.upper()}] Settled\n"
    with open(MEMORY_FILE, "a") as f:
        f.write(entry)

def build_file_tree():
    tree = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp']]
        for f in files:
            if not f.startswith('.'):
                path = os.path.relpath(os.path.join(root, f), ".")
                tree.append(path)
    return "\n".join(tree)

def meditate(intent):
    print("🧘 [MEDITATE] Stilling the workspace mind. Scanning local filesystem...")
    
    file_tree = build_file_tree()
    
    system = f"""You are the Meditate Layer. You have access to the following files in the user's repository:

{file_tree}

Identify which of these specific files would need to be modified to fulfill the user's intent. Return ONLY a comma-separated list of the EXACT filenames from the list above. Do not hallucinate files that do not exist."""
    
    files_str = llm_call(RESEARCH_MODEL, system, intent)
    files = [f.strip() for f in files_str.split(",") if f.strip() and os.path.exists(f.strip())]
    
    if not files: 
        print("⚠️ Mamba returned no valid files. Defaulting to app.py.")
        files = ["app.py"]
        
    print(f"🧘 Found Vrittis (Tangled Threads): {files}")
    return files

def read_files(files):
    context = ""
    for f in files:
        if os.path.exists(f):
            with open(f, "r") as file:
                context += f"\n--- {f} ---\n{file.read()[:2000]}\n" # Truncated for safety
    return context

def execute_coder(intent, context, memory):
    print("🧠 [GENIUS CODER] Reading context and generating unified diff...")
    system = f"""You are the Genius Coder.
PROJECT MEMORY (Nidra):
{memory}

You have the following files:
{context}

Output ONLY valid JSON representing the file edits:
[
  {{"file": "filename.py", "content": "the completely rewritten file content"}}
]"""
    return llm_call(CODER_MODEL, system, intent)

def apply_edits(json_edits):
    try:
        if "```json" in json_edits:
            json_edits = json_edits.split("```json")[1].split("```")[0].strip()
        elif "```" in json_edits:
            json_edits = json_edits.split("```")[1].split("```")[0].strip()
            
        edits = json.loads(json_edits)
        for edit in edits:
            with open(edit["file"], "w") as f:
                f.write(edit["content"])
            print(f"✅ Applied edit to {edit['file']}")
        return True
    except Exception as e:
        print(f"❌ Failed to parse or apply edits: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Puran Code: Local Autonomous Agent")
    parser.add_argument("intent", type=str, help="What do you want the agent to build/fix?")
    args = parser.parse_args()

    memory = load_memory()
    
    # 1. Meditate Layer (Mamba Context)
    files = meditate(args.intent)
    context = read_files(files)
    
    # 2. Coder Layer (Qwen 32B)
    edits = execute_coder(args.intent, context, memory)
    
    # 3. Apply Edits
    success = apply_edits(edits)
    
    # 4. Nidra Memory Node Generation
    if success:
        print("🌙 [NIDRA] Consolidating memory into Pramana (Proven Truth)...")
        save_memory(args.intent, files, "pramana")
        print("🎉 Task Complete.")

if __name__ == "__main__":
    main()
