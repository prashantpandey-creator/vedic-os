import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Create the reusable UI helper function for Git Mounting
git_mounter_func = """def render_workspace_config():
    st.markdown("### 📁 Workspace Configuration")
    
    # 1. Cloud Git Mounter
    git_url = st.text_input("☁️ Quick Mount: Paste a GitHub URL to Clone & Analyze:", placeholder="https://github.com/user/repo.git")
    if st.button("⬇️ Clone Repository"):
        import subprocess
        target_base = os.path.expanduser("~/vedic_workspaces")
        os.makedirs(target_base, exist_ok=True)
        repo_name = git_url.split("/")[-1].replace(".git", "") if "/" in git_url else "unknown_repo"
        target_path = os.path.join(target_base, repo_name)
        
        if os.path.exists(target_path):
            st.warning(f"Repository already exists at `{target_path}`.")
            st.session_state["workspace_dir"] = target_path
        else:
            with st.spinner(f"Cloning {repo_name} from GitHub..."):
                res = subprocess.run(["git", "clone", git_url, target_path], capture_output=True, text=True)
                if res.returncode == 0:
                    st.success(f"Successfully cloned into `{target_path}`")
                    st.session_state["workspace_dir"] = target_path
                else:
                    st.error(f"Failed to clone: {res.stderr}")
                    
    # 2. Absolute Path Override
    default_dir = st.session_state.get("workspace_dir", os.getcwd())
    workspace_dir = st.text_input("🎯 Active Directory (Absolute Path)", default_dir)
    st.session_state["workspace_dir"] = workspace_dir
    
    if not os.path.exists(workspace_dir):
        st.error("Directory does not exist on your Mac!")
        return None
    else:
        st.success(f"Agent is locked onto: `{workspace_dir}`")
        return workspace_dir

# ----------------- Main View -----------------"""

content = content.replace("# ----------------- Main View -----------------", git_mounter_func)

# Inject into Nidra Mode
old_nidra = """    st.markdown("### 📁 Workspace Configuration")
    workspace_dir = st.text_input("Target Directory (Absolute Path)", os.getcwd())
    if not os.path.exists(workspace_dir): st.error("Directory does not exist!")"""
new_nidra = """    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()"""
content = content.replace(old_nidra, new_nidra)

# Inject into Omni Mode
old_omni = """    st.markdown("### 📁 Workspace Configuration")
    workspace_dir = st.text_input("Target Repository Directory (Absolute Path)", os.getcwd())
    if not os.path.exists(workspace_dir): st.error("Directory does not exist!")
    else: st.success(f"Omni-Agent is locked onto: `{workspace_dir}`")"""
new_omni = """    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()"""
content = content.replace(old_omni, new_omni)


with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Git Mounter UI injected.")
