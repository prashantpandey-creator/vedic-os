import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

tree_func = """def render_file_tree(workspace_dir):
    import os
    st.markdown("### 🗂️ Project File Tree")
    
    ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__', '.next', 'dist', 'build'}
    tree_str = ""
    
    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        level = root.replace(workspace_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        folder = os.path.basename(root)
        if folder:
            tree_str += f"{indent}📂 **{folder}/**\\n"
        subindent = ' ' * 4 * (level + 1)
        for f in sorted(files):
            if not f.startswith('.'):
                tree_str += f"{subindent}📄 {f}\\n"
                
    if tree_str:
        with st.expander("Explore Workspace Files", expanded=False):
            st.markdown(tree_str)
    else:
        st.info("Workspace is empty.")

# ----------------- Main View -----------------"""
content = content.replace("# ----------------- Main View -----------------", tree_func)

# Inject tree render call in Omni Mode UI
old_omni = """    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    
    from agents.omni_agent import run_omni_loop"""

new_omni = """    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    render_file_tree(workspace_dir)
    
    from agents.omni_agent import run_omni_loop"""
content = content.replace(old_omni, new_omni)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("File Tree UI patched in app.py")
