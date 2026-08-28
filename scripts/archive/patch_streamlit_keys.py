import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Update function definition and add keys to elements
old_func = """def render_workspace_config():
    st.markdown("### 📁 Workspace Configuration")
    
    # 1. Cloud Git Mounter
    git_url = st.text_input("☁️ Quick Mount: Paste a GitHub URL to Clone & Analyze:", placeholder="https://github.com/user/repo.git")
    if st.button("⬇️ Clone Repository"):"""

new_func = """def render_workspace_config(key_prefix=""):
    st.markdown("### 📁 Workspace Configuration")
    
    # 1. Cloud Git Mounter
    git_url = st.text_input("☁️ Quick Mount: Paste a GitHub URL to Clone & Analyze:", placeholder="https://github.com/user/repo.git", key=f"git_url_{key_prefix}")
    if st.button("⬇️ Clone Repository", key=f"clone_btn_{key_prefix}"):"""
content = content.replace(old_func, new_func)

old_text = """    # 2. Absolute Path Override
    default_dir = st.session_state.get("workspace_dir", os.getcwd())
    workspace_dir = st.text_input("🎯 Active Directory (Absolute Path)", default_dir)"""
    
new_text = """    # 2. Absolute Path Override
    default_dir = st.session_state.get("workspace_dir", os.getcwd())
    workspace_dir = st.text_input("🎯 Active Directory (Absolute Path)", default_dir, key=f"workspace_dir_{key_prefix}")"""
content = content.replace(old_text, new_text)

# 2. Update callers
content = content.replace("workspace_dir = render_workspace_config()", "workspace_dir = render_workspace_config(key_prefix='tab3')", 1)
content = content.replace("workspace_dir = render_workspace_config()", "workspace_dir = render_workspace_config(key_prefix='tab4')", 1)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Streamlit Duplicate ID Keys fixed.")
