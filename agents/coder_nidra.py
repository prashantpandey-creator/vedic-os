import os
import json
import requests
import re
import subprocess
from core.ollama_api import OLLAMA_URL, evict_model
from core.file_system import build_tree_with_hints, apply_search_replace
from core.memory_graph import read_compressed_memory, append_vritti

def run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder=None, workspace_dir="."):
    # 1. Meditate (Scanner)
    status.write(f"🧘 **[MEDITATE]** Stilling the workspace. {meditate_model} is scanning local files...")
    
    file_tree = build_tree_with_hints(intent_prompt, workspace_dir=workspace_dir)
    med_sys = f"You are the Meditate Layer. You have access to these files:\n{file_tree}\nIdentify which of these specific files need modifying to fulfill the user's intent. Return ONLY a comma-separated list of EXACT filenames from this list. Do not hallucinate."
    meditate_payload = {
        "model": meditate_model,
        "messages": [{"role": "system", "content": med_sys}, {"role": "user", "content": intent_prompt}],
        "stream": False
    }
    
    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload).json()
        files_str = res.get("message", {}).get("content", "")
        files = [f.strip() for f in files_str.split(",") if f.strip() and os.path.exists(f.strip())]
        if not files: files = ["app.py"]
    except: files = ["app.py"]
    
    # [VRAM MANAGEMENT]
    status.write(f"🧹 **[VRAM]** Evicting {meditate_model} to clear Unified Memory...")
    evict_model(meditate_model)
    
    # 2. Read Context & Memory
    status.write(f"📂 **[CONTEXT]** Found Vrittis (Threads): `{', '.join(files)}`. Loading into {coder_model}...")
    context = ""
    for f in files:
        with open(os.path.join(workspace_dir, f), "r", encoding="utf-8") as file:
            context += f"\n--- {f} ---\n{file.read()[:2000]}\n"
            
    memory = read_compressed_memory(workspace_dir)
            
    # 3. Code Generation (Selected Coder) with Self-Healing Loop
    system = f"You are the Genius Coder. \nPROJECT MEMORY:\n{memory}\n\nFILES:\n{context}\n\nOutput ONLY valid JSON representing file edits. Do NOT rewrite the whole file. Use SEARCH and REPLACE blocks.\nYour 'search' block must contain enough surrounding context lines to be 100% mathematically unique in the file.\nFormat: [{{'file': 'filename', 'search': 'exact old code to replace', 'replace': 'new code'}}] "
    messages = [{"role": "system", "content": system}, {"role": "user", "content": intent_prompt}]
    
    max_retries = 3
    attempt = 0
    success = False
    
    # Git Auto-Checkpoint
    status.write("📦 **[GIT]** Checkpointing current state before edits...")
    subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Auto-checkpoint before Nidra Edit: {intent_prompt}"], cwd=workspace_dir, capture_output=True)
    
    final_edits = []

    while attempt < max_retries and not success:
        attempt += 1
        if attempt == 1:
            status.write(f"🧠 **[GENIUS CODER]** {coder_model} is generating the unified diff...")
        else:
            status.write(f"⚠️ **[SELF-HEALING]** Attempt {attempt}: Feeding error back to Coder...")
            
        coder_payload = {
            "model": coder_model,
            "messages": messages,
            "stream": True, "options": {"temperature": 0.0}
        }
        
        coder_res = requests.post(f"{OLLAMA_URL}/api/chat", json=coder_payload, stream=True)
        raw_response = ""
        
        for line in coder_res.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    raw_response += chunk["message"]["content"]
                    if stream_placeholder:
                        stream_placeholder.code(raw_response, language="json")
                        
        messages.append({"role": "assistant", "content": raw_response})
        
        json_edits = raw_response
        if "```json" in json_edits: json_edits = json_edits.split("```json")[1].split("```")[0].strip()
        elif "```" in json_edits: json_edits = json_edits.split("```")[1].split("```")[0].strip()
        else:
            match = re.search(r'\[\s*\{.*?\}\s*\]', json_edits, re.DOTALL)
            if match: json_edits = match.group(0)
        
        # 4. Apply, Verify, & Consolidate Memory
        try:
            edits = json.loads(json_edits)
            for edit in edits:
                try:
                    apply_search_replace(edit["file"], edit["search"], edit["replace"], workspace_dir=workspace_dir)
                except ValueError as ve:
                    append_vritti(intent_prompt, edit["file"], "[INVALID] Search Block Hallucination", workspace_dir=workspace_dir)
                    raise Exception(f"Coder hallucinated the search block for {edit['file']}. Ensure you include enough surrounding lines to make the search string perfectly unique.")
                
                # [VERIFICATION NODE]
                if edit["file"].endswith(".py"):
                    status.write(f"🔬 **[VERIFY]** Compiling {edit['file']} to check for syntax errors...")
                    check = subprocess.run(["python3", "-m", "py_compile", edit["file"]], cwd=workspace_dir, capture_output=True, text=True)
                    if check.returncode != 0:
                        append_vritti(intent_prompt, edit["file"], "[INVALID] Syntax Error", workspace_dir=workspace_dir)
                        raise Exception(f"Syntax Error generated by Coder:\n{check.stderr}")
            
            status.write("🌙 **[NIDRA]** Consolidating edits into Pramana (Proven Truth) memory graph...")
            append_vritti(intent_prompt, ', '.join(files), "[PRAMANA] Settled", workspace_dir=workspace_dir)
            success = True
            final_edits = edits
            
        except Exception as e:
            messages.append({"role": "user", "content": f"Your previous code failed with this error:\n{e}\nPlease analyze the error, fix the search block or syntax, and output the correct JSON."})
            if attempt == max_retries:
                raise Exception(f"Failed after {max_retries} retries: {e}")

    return final_edits
