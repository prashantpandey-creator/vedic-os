import sys
import re

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Remove the Sidebar Radio
sidebar_code = """st.sidebar.title("Vedic Developer Suite")
app_mode = st.sidebar.radio("Select Engine:", [
    "🦅 Omni-Agent (Autonomous Terminal Loop)",
    "🧬 Coding Agent with Harness (Nidra)",
    "🏗️ App Builder (Vyasa Architect)",
    "💬 Standard Chat (Hybrid Non-Transformers)"
])"""
content = content.replace(sidebar_code, "st.sidebar.title(\"Vedic Developer Suite\")\nst.sidebar.info(\"Choose a stage from the tabs above to explore the evolution of the Vedic AI Engine.\")")

# 2. Setup Tabs
tab_setup = """tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Stage 1: Bare Model", 
    "🏗️ Stage 2: Sandbox Architect", 
    "🧬 Stage 3: Nidra Harness", 
    "🦅 Stage 4: Omni-Agent"
])"""

content = content.replace("# ----------------- Main View -----------------", f"# ----------------- Main View -----------------\n{tab_setup}")

def extract_and_indent(source, start_marker, end_marker=None):
    start_idx = source.find(start_marker)
    if start_idx == -1: return ""
    
    if end_marker:
        end_idx = source.find(end_marker, start_idx)
        if end_idx == -1: end_idx = len(source)
    else:
        end_idx = len(source)
        
    block = source[start_idx:end_idx]
    
    # Remove the if/elif condition line itself
    lines = block.split('\n')
    lines = lines[1:] # skip 'if app_mode == ...'
    
    # Unindent everything by 4 spaces
    unindented = []
    for line in lines:
        if line.startswith("    "): unindented.append(line[4:])
        else: unindented.append(line)
        
    # Re-indent by 4 spaces to fit inside `with tabX:`
    indented = ["    " + line for line in unindented if line is not None]
    return "\n".join(indented)

# Extract blocks
chat_block = extract_and_indent(content, 'if app_mode == "💬 Standard Chat (Hybrid Non-Transformers)":', 'elif app_mode == "🧬 Coding Agent with Harness (Nidra)":')
nidra_block = extract_and_indent(content, 'elif app_mode == "🧬 Coding Agent with Harness (Nidra)":', 'elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":')
omni_block = extract_and_indent(content, 'elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":', 'else:')
arch_block = extract_and_indent(content, 'else:', None)

# Assemble new content
prefix = content[:content.find('if app_mode == "💬 Standard Chat')]

new_content = prefix + "\n" + "with tab1:\n" + chat_block + "\nwith tab2:\n" + arch_block + "\nwith tab3:\n" + nidra_block + "\nwith tab4:\n" + omni_block

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(new_content)

print("UI patched to use Tabs.")
