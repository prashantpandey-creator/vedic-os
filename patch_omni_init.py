import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    content = f.read()

old_func = """def init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir="."):
    repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)
    
    meditate_payload = {
        "model": meditate_model,
        "messages": [
            {"role": "system", "content": "You are the Vedic Blueprint Generator. Read the codebase and output a compressed summary."},
            {"role": "user", "content": f"USER INTENT: {intent_prompt}\\n\\nCODEBASE:\\n{repo_text}"}
        ],
        "stream": False,
        "options": {"num_ctx": 32000}
    }
    
    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload).json()
        blueprint = res.get("message", {}).get("content", "Blueprint failed to generate.")
    except Exception as e:
        blueprint = f"Failed to ingest: {e}"
        
    evict_model(meditate_model)"""

new_func = """def init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir=".", status_container=None):
    if status_container:
        status_container.info("📂 Scanning filesystem and extracting active codebase...")
    repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)
    
    file_count = repo_text.count("--- FILE:")
    char_count = len(repo_text)
    
    if status_container:
        status_container.info(f"🐍 Passed {file_count} files ({char_count} chars) to Mamba model `{meditate_model}`. Synthesizing blueprint...")
        
    meditate_payload = {
        "model": meditate_model,
        "messages": [
            {"role": "system", "content": "You are the Vedic Blueprint Generator. Read the codebase and output a compressed summary."},
            {"role": "user", "content": f"USER INTENT: {intent_prompt}\\n\\nCODEBASE:\\n{repo_text}"}
        ],
        "stream": True,
        "options": {"num_ctx": 32000}
    }
    
    blueprint = ""
    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload, stream=True)
        for line in res.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    blueprint += chunk["message"]["content"]
                    if status_container:
                        status_container.markdown(f"**🐍 Mamba is writing Blueprint:**\\n{blueprint}▌")
        if status_container:
            status_container.success(f"**🐍 Mamba Blueprint Complete!**\\n{blueprint}")
    except Exception as e:
        blueprint = f"Failed to ingest: {e}"
        if status_container:
            status_container.error(blueprint)
        
    evict_model(meditate_model)"""

content = content.replace(old_func, new_func)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
    f.write(content)
