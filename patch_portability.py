import sys
import os

# --- PATCH OLLAMA API ---
with open("/Users/badenath/projects/local-llm-ui/core/ollama_api.py", "r") as f:
    o_content = f.read()
o_content = o_content.replace('OLLAMA_URL = "http://localhost:11434"', 'from config import OLLAMA_URL')
with open("/Users/badenath/projects/local-llm-ui/core/ollama_api.py", "w") as f:
    f.write(o_content)

# --- PATCH APP.PY ---
with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    app_content = f.read()

# Add import
app_content = app_content.replace("import streamlit as st", "import streamlit as st\nfrom config import DEFAULT_WORKSPACE_ROOT, DEFAULT_FALLBACK_DIR, CLAUDE_MEMORY_DIR, ANTIGRAVITY_BRAIN_DIR, FAST_MODEL, HEAVY_MODEL, INGEST_MODEL")

# Replace Github Mounter workspace logic
app_content = app_content.replace('workspace_dir = os.path.join(os.path.expanduser("~/vedic_workspaces")', 'workspace_dir = os.path.join(DEFAULT_WORKSPACE_ROOT')
app_content = app_content.replace('workspace_dir = st.text_input("Absolute Path to Project Directory:", "/Users/badenath/projects/local-llm-ui")', 'workspace_dir = st.text_input("Absolute Path to Project Directory:", DEFAULT_FALLBACK_DIR)')

# Replace Importer paths
app_content = app_content.replace('claude_dir = os.path.expanduser("~/claude-sync/memory/")', 'claude_dir = CLAUDE_MEMORY_DIR')
app_content = app_content.replace('ag_dir = os.path.expanduser("~/.gemini/antigravity/brain/")', 'ag_dir = ANTIGRAVITY_BRAIN_DIR')

# Replace Model Defaults
app_content = app_content.replace('target = "mannix/llama3.1-8b-abliterated:latest"', 'target = FAST_MODEL')
app_content = app_content.replace('if "qwen2.5:32b" in models else 0)', 'if HEAVY_MODEL in models else 0)')
app_content = app_content.replace('"granite4:3b-h"', 'INGEST_MODEL')

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(app_content)
    
print("app.py and ollama_api patched for portability.")
