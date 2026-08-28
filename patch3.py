import sys

with open("/Users/badenath/projects/local-llm-ui/agents/coder_nidra.py", "r") as f:
    content = f.read()

# 1. Update function signature
old_sig = "def run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status):"
new_sig = "def run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder=None):"
content = content.replace(old_sig, new_sig)

# 2. Inject Git tracking before the while loop
old_while = "    while attempt < max_retries and not success:"
new_while = """    # Git Auto-Checkpoint
    status.write("📦 **[GIT]** Checkpointing current state before edits...")
    subprocess.run(["git", "init"], capture_output=True)
    subprocess.run(["git", "add", "."], capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Auto-checkpoint before Nidra Edit: {intent_prompt}"], capture_output=True)
    
    final_edits = []

    while attempt < max_retries and not success:"""
content = content.replace(old_while, new_while)

# 3. Stream the generation
old_gen = """        coder_payload = {
            "model": coder_model,
            "messages": messages,
            "stream": False, "options": {"temperature": 0.0}
        }
        
        coder_res = requests.post(f"{OLLAMA_URL}/api/chat", json=coder_payload)
        raw_response = coder_res.json().get("message", {}).get("content", "")
        messages.append({"role": "assistant", "content": raw_response})"""

new_gen = """        coder_payload = {
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
                        
        messages.append({"role": "assistant", "content": raw_response})"""
content = content.replace(old_gen, new_gen)

# 4. Return edits
old_ret = "            success = True"
new_ret = "            success = True\n            final_edits = edits"
content = content.replace(old_ret, new_ret)

old_fail = "                raise Exception(f\"Failed after {max_retries} retries: {e}\")"
new_fail = "                raise Exception(f\"Failed after {max_retries} retries: {e}\")\n\n    return final_edits"
content = content.replace(old_fail, new_fail)

with open("/Users/badenath/projects/local-llm-ui/agents/coder_nidra.py", "w") as f:
    f.write(content)

print("coder_nidra.py patched.")
