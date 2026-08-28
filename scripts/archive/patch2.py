import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Fix 1 & 2: VRAM Eviction & JSON parsing & replace(1)
old_block = """        try:
            res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload).json()
            files_str = res.get("message", {}).get("content", "")
            files = [f.strip() for f in files_str.split(",") if f.strip() and os.path.exists(f.strip())]
            if not files: files = ["app.py"] # fallback
        except: files = ["app.py"]"""

new_block = """        try:
            res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload).json()
            files_str = res.get("message", {}).get("content", "")
            files = [f.strip() for f in files_str.split(",") if f.strip() and os.path.exists(f.strip())]
            if not files: files = ["app.py"] # fallback
        except: files = ["app.py"]
        
        # [VRAM MANAGEMENT] Evict Meditate model to free up Unified Memory for Qwen
        status.write(f"🧹 **[VRAM]** Evicting {meditate_model} to clear Unified Memory...")
        try: requests.post(f"{OLLAMA_URL}/api/generate", json={"model": meditate_model, "keep_alive": 0}, timeout=2)
        except: pass"""

if old_block in content:
    content = content.replace(old_block, new_block)

old_block2 = """            json_edits = raw_response
            if "```json" in json_edits: json_edits = json_edits.split("```json")[1].split("```")[0].strip()
            elif "```" in json_edits: json_edits = json_edits.split("```")[1].split("```")[0].strip()
            
            # 4. Apply, Verify, & Consolidate Memory
            try:
                import subprocess
                edits = json.loads(json_edits)
                for edit in edits:
                    with open(edit["file"], "r") as f:
                        old_code = f.read()
                    
                    if edit["search"] not in old_code:
                        with open("PROJECT_MIND.md", "a") as f:
                            f.write(f"\\n- **Intent:** {intent_prompt}\\n  - **Files Edited:** {edit['file']}\\n  - **Status:** [INVALID] Search Block Hallucination\\n")
                        raise Exception(f"Coder hallucinated the search block for {edit['file']}. The exact text was not found in the file.")
                        
                    new_code = old_code.replace(edit["search"], edit["replace"])"""

new_block2 = """            import re
            json_edits = raw_response
            if "```json" in json_edits: json_edits = json_edits.split("```json")[1].split("```")[0].strip()
            elif "```" in json_edits: json_edits = json_edits.split("```")[1].split("```")[0].strip()
            else:
                match = re.search(r'\[\s*\{.*?\}\s*\]', json_edits, re.DOTALL)
                if match: json_edits = match.group(0)
            
            # 4. Apply, Verify, & Consolidate Memory
            try:
                import subprocess
                edits = json.loads(json_edits)
                for edit in edits:
                    with open(edit["file"], "r") as f:
                        old_code = f.read()
                    
                    if edit["search"] not in old_code:
                        with open("PROJECT_MIND.md", "a") as f:
                            f.write(f"\\n- **Intent:** {intent_prompt}\\n  - **Files Edited:** {edit['file']}\\n  - **Status:** [INVALID] Search Block Hallucination\\n")
                        raise Exception(f"Coder hallucinated the search block for {edit['file']}. Ensure you include enough surrounding lines to make the search string perfectly unique.")
                        
                    new_code = old_code.replace(edit["search"], edit["replace"], 1)"""

if old_block2 in content:
    content = content.replace(old_block2, new_block2)


old_block3 = """        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp']]
            for f in files:
                if not f.startswith('.'):
                    rel_path = os.path.relpath(os.path.join(root, f), ".")
                    hints = ""
                    try:
                        with open(rel_path, "r", encoding="utf-8") as file:"""

new_block3 = """        allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".html"}
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp']]
            for f in files:
                if not f.startswith('.'):
                    rel_path = os.path.relpath(os.path.join(root, f), ".")
                    hints = ""
                    if any(f.endswith(ext) for ext in allowed_exts):
                        try:
                            with open(rel_path, "r", encoding="utf-8") as file:"""

if old_block3 in content:
    content = content.replace(old_block3, new_block3)
    
old_block4 = """        system = f"You are the Genius Coder. \\nPROJECT MEMORY:\\n{memory}\\n\\nFILES:\\n{context}\\n\\nOutput ONLY valid JSON representing file edits. Do NOT rewrite the whole file. Use SEARCH and REPLACE blocks.\\nFormat: [{{'file': 'filename', 'search': 'exact old code to replace', 'replace': 'new code'}}] \""""
new_block4 = """        system = f"You are the Genius Coder. \\nPROJECT MEMORY:\\n{memory}\\n\\nFILES:\\n{context}\\n\\nOutput ONLY valid JSON representing file edits. Do NOT rewrite the whole file. Use SEARCH and REPLACE blocks.\\nYour 'search' block must contain enough surrounding context lines to be 100% mathematically unique in the file.\\nFormat: [{{'file': 'filename', 'search': 'exact old code to replace', 'replace': 'new code'}}] \""""

if old_block4 in content:
    content = content.replace(old_block4, new_block4)


with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Patch applied successfully.")
