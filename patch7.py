import sys
import os

# 1. Update core/file_system.py
with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "r") as f:
    fs_content = f.read()

fs_content = fs_content.replace('def build_tree_with_hints(intent_prompt=""):', 'def build_tree_with_hints(intent_prompt="", workspace_dir="."):')
fs_content = fs_content.replace('for root, dirs, files in os.walk("."):', 'for root, dirs, files in os.walk(workspace_dir):')
fs_content = fs_content.replace('def ingest_repository_to_text(max_chars=100000):', 'def ingest_repository_to_text(workspace_dir=".", max_chars=100000):')

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.write(fs_content)


# 2. Update agents/omni_agent.py
with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "r") as f:
    omni_content = f.read()

omni_content = omni_content.replace('def run_omni_loop(intent_prompt, meditate_model, coder_model, status, stream_placeholder):', 'def run_omni_loop(intent_prompt, meditate_model, coder_model, status, stream_placeholder, workspace_dir="."):')
omni_content = omni_content.replace('repo_text = ingest_repository_to_text(max_chars=120000)', 'repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)')
omni_content = omni_content.replace('terminal = TerminalEngine()', 'terminal = TerminalEngine(workspace_dir=workspace_dir)')

# Fix git commands in omni_agent to use workspace_dir
omni_content = omni_content.replace('subprocess.run(["git", "init"], capture_output=True)', 'subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True)')
omni_content = omni_content.replace('subprocess.run(["git", "add", "."], capture_output=True)', 'subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True)')
omni_content = omni_content.replace('subprocess.run(["git", "commit"', 'subprocess.run(["git", "commit"') # Will fix below via regex
import re
omni_content = re.sub(r'subprocess\.run\(\["git", "commit", "-m", (.*?)\]\, capture_output=True\)', r'subprocess.run(["git", "commit", "-m", \1], cwd=workspace_dir, capture_output=True)', omni_content)

# File path edits in omni_agent (apply_search_replace)
# Wait, apply_search_replace in file_system.py uses the exact path. So if omni returns relative paths, we need to join them.
# The TerminalEngine returns whatever path it feels like.
# Let's modify file_system.py apply_search_replace to accept workspace_dir.
old_apply = 'def apply_search_replace(file_path, search_block, replace_block):'
new_apply = 'def apply_search_replace(file_path, search_block, replace_block, workspace_dir="."):\n    file_path = os.path.join(workspace_dir, file_path)'
fs_content = fs_content.replace(old_apply, new_apply)
with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.write(fs_content)

omni_content = omni_content.replace('apply_search_replace(filepath, search, replace)', 'apply_search_replace(filepath, search, replace, workspace_dir=workspace_dir)')

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "w") as f:
    f.write(omni_content)


# 3. Update agents/coder_nidra.py
with open("/Users/badenath/projects/local-llm-ui/agents/coder_nidra.py", "r") as f:
    nidra_content = f.read()

nidra_content = nidra_content.replace('def run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder=None):', 'def run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder=None, workspace_dir="."):')
nidra_content = nidra_content.replace('build_tree_with_hints(intent_prompt)', 'build_tree_with_hints(intent_prompt, workspace_dir=workspace_dir)')

nidra_content = nidra_content.replace('subprocess.run(["git", "init"], capture_output=True)', 'subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True)')
nidra_content = nidra_content.replace('subprocess.run(["git", "add", "."], capture_output=True)', 'subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True)')
nidra_content = re.sub(r'subprocess\.run\(\["git", "commit", "-m", (.*?)\]\, capture_output=True\)', r'subprocess.run(["git", "commit", "-m", \1], cwd=workspace_dir, capture_output=True)', nidra_content)

# Fix open() in context loading
nidra_content = nidra_content.replace('with open(f, "r", encoding="utf-8") as file:', 'with open(os.path.join(workspace_dir, f), "r", encoding="utf-8") as file:')

nidra_content = nidra_content.replace('apply_search_replace(edit["file"], edit["search"], edit["replace"])', 'apply_search_replace(edit["file"], edit["search"], edit["replace"], workspace_dir=workspace_dir)')
nidra_content = nidra_content.replace('subprocess.run(["python3", "-m", "py_compile", edit["file"]], capture_output=True, text=True)', 'subprocess.run(["python3", "-m", "py_compile", edit["file"]], cwd=workspace_dir, capture_output=True, text=True)')

with open("/Users/badenath/projects/local-llm-ui/agents/coder_nidra.py", "w") as f:
    f.write(nidra_content)


# 4. Update app.py UI
with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    app_content = f.read()

# Add Workspace selector to Nidra
old_nidra_ui = """elif app_mode == "🧬 Coding Agent with Harness (Nidra)":
    st.markdown("Use this mode to **autonomously modify an existing codebase**. Mamba-2 (SSM) scans the filesystem, your selected Genius Coder writes the unified diff, and the Nidra Harness logs the memory graph.")"""

new_nidra_ui = """elif app_mode == "🧬 Coding Agent with Harness (Nidra)":
    st.markdown("Use this mode to **autonomously modify an existing codebase**. Mamba-2 (SSM) scans the filesystem, your selected Genius Coder writes the unified diff, and the Nidra Harness logs the memory graph.")
    
    st.markdown("### 📁 Workspace Configuration")
    workspace_dir = st.text_input("Target Directory (Absolute Path)", os.getcwd())
    if not os.path.exists(workspace_dir): st.error("Directory does not exist!")"""
app_content = app_content.replace(old_nidra_ui, new_nidra_ui)
app_content = app_content.replace('run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder)', 'run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder, workspace_dir)')

# Add Workspace selector to Omni
old_omni_ui = """elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":
    st.markdown("This is the **Next-Gen Agentic Loop**. Mamba-2 ingests the entire Git repository to build an architectural blueprint. Qwen takes control of your Mac's Zsh terminal, looping autonomously to edit files, run scripts, read stdout errors, and fix bugs until the task is complete.")"""

new_omni_ui = """elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":
    st.markdown("This is the **Next-Gen Agentic Loop**. Mamba-2 ingests the entire Git repository to build an architectural blueprint. Qwen takes control of your Mac's Zsh terminal, looping autonomously to edit files, run scripts, read stdout errors, and fix bugs until the task is complete.")
    
    st.markdown("### 📁 Workspace Configuration")
    workspace_dir = st.text_input("Target Repository Directory (Absolute Path)", os.getcwd())
    if not os.path.exists(workspace_dir): st.error("Directory does not exist!")
    else: st.success(f"Omni-Agent is locked onto: `{workspace_dir}`")"""
app_content = app_content.replace(old_omni_ui, new_omni_ui)
app_content = app_content.replace('run_omni_loop(intent_prompt, meditate_model, coder_model, status, stream_placeholder)', 'run_omni_loop(intent_prompt, meditate_model, coder_model, status, stream_placeholder, workspace_dir)')

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(app_content)

print("UI and Core fully updated with explicit Workspace Directory awareness.")
