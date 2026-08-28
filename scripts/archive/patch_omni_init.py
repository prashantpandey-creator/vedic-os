import sys
import os

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    content = f.read()

import re

# Find the exact block we want to replace
pattern = re.compile(r"def init_omni_loop.*?evict_model\(meditate_model\)", re.DOTALL)

new_block = """def init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir=".", status_container=None):
    if status_container:
        status_container.info("📂 Scanning filesystem and extracting active codebase...")
        
    # OPTIMIZATION 1: Cut max chars in half (120k -> 60k). Reduces prompt context to ~15k tokens.
    # This halves the time-to-first-token for Mamba.
    repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=60000)
    
    file_count = repo_text.count("--- FILE:")
    char_count = len(repo_text)
    
    if status_container:
        status_container.info(f"🐍 Passed {file_count} files ({char_count} chars) to Mamba model `{meditate_model}`. Synthesizing blueprint...")
        
    # OPTIMIZATION 2: Demand extreme brevity. Generation of tokens is the slowest part.
    meditate_payload = {
        "model": meditate_model,
        "messages": [
            {"role": "system", "content": "You are the Vedic Blueprint Generator. Read the codebase and output a compressed summary. EXTREME BREVITY REQUIRED: Output a maximum of 5 bullet points. Do not write paragraphs."},
            {"role": "user", "content": f"USER INTENT: {intent_prompt}\\n\\nCODEBASE:\\n{repo_text}"}
        ],
        "stream": True,
        "options": {"num_ctx": 16000}
    }
    
    blueprint = ""
    try:
        # OPTIMIZATION 3: Stream the output so the user sees progress instantly instead of waiting.
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

if pattern.search(content):
    content = pattern.sub(new_block, content)
    with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
        f.write(content)
    print("Successfully optimized Mamba ingestion and enabled streaming.")
else:
    print("Could not find block to replace.")
