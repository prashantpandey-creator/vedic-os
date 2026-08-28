import sys

# Patch Omni
with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "r") as f:
    content = f.read()

content = content.replace("memory = read_compressed_memory()", "memory = read_compressed_memory(workspace_dir)")
content = content.replace("append_vritti(intent_prompt, \"Omni-Loop\", \"[PRAMANA] Done\", extra=f\"Completed in {step} steps.\")", "append_vritti(intent_prompt, \"Omni-Loop\", \"[PRAMANA] Done\", extra=f\"Completed in {step} steps.\", workspace_dir=workspace_dir)")

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "w") as f:
    f.write(content)

# Patch Nidra
with open("/Users/badenath/projects/local-llm-ui/agents/coder_nidra.py", "r") as f:
    content = f.read()

content = content.replace("memory = read_compressed_memory()", "memory = read_compressed_memory(workspace_dir)")
content = content.replace("append_vritti(intent_prompt, edit[\"file\"], \"[INVALID] Search Block Hallucination\")", "append_vritti(intent_prompt, edit[\"file\"], \"[INVALID] Search Block Hallucination\", workspace_dir=workspace_dir)")
content = content.replace("append_vritti(intent_prompt, edit[\"file\"], \"[INVALID] Syntax Error\")", "append_vritti(intent_prompt, edit[\"file\"], \"[INVALID] Syntax Error\", workspace_dir=workspace_dir)")
content = content.replace("append_vritti(intent_prompt, ', '.join(files), \"[PRAMANA] Settled\")", "append_vritti(intent_prompt, ', '.join(files), \"[PRAMANA] Settled\", workspace_dir=workspace_dir)")

with open("/Users/badenath/projects/local-llm-ui/agents/coder_nidra.py", "w") as f:
    f.write(content)

# Update UI memory readout
with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()
content = content.replace('if os.path.exists("PROJECT_MIND.md"):', 'memory_path = os.path.join(workspace_dir, "PROJECT_MIND.md")\n                if os.path.exists(memory_path):')
content = content.replace('with open("PROJECT_MIND.md", "r", encoding="utf-8") as f:', 'with open(memory_path, "r", encoding="utf-8") as f:')
with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
