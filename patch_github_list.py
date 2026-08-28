import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

old_func = """def render_workspace_config(key_prefix=""):
    st.markdown("### 📁 Workspace Configuration")
    
    # 1. Cloud Git Mounter
    git_url = st.text_input("☁️ Quick Mount: Paste a GitHub URL to Clone & Analyze:", placeholder="https://github.com/user/repo.git", key=f"git_url_{key_prefix}")
    if st.button("⬇️ Clone Repository", key=f"clone_btn_{key_prefix}"):
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
    workspace_dir = st.text_input("🎯 Active Directory (Absolute Path)", default_dir, key=f"workspace_dir_{key_prefix}")
    st.session_state["workspace_dir"] = workspace_dir
    
    if not os.path.exists(workspace_dir):
        st.error("Directory does not exist on your Mac!")
        return None
    else:
        st.success(f"Agent is locked onto: `{workspace_dir}`")
        return workspace_dir"""

new_func = """@st.cache_data(ttl=300)
def fetch_github_repos():
    import subprocess
    import json
    try:
        res = subprocess.run(["gh", "repo", "list", "--json", "nameWithOwner,url", "--limit", "20"], capture_output=True, text=True)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except: pass
    return []

def render_workspace_config(key_prefix=""):
    st.markdown("### 📁 Workspace Configuration")
    
    import subprocess
    target_base = os.path.expanduser("~/vedic_workspaces")
    os.makedirs(target_base, exist_ok=True)
    
    # 1. GitHub Account Connector
    repos = fetch_github_repos()
    if repos:
        repo_options = ["(Select a GitHub Repository)"] + [r["nameWithOwner"] for r in repos]
        selected_repo = st.selectbox("🐙 GitHub Projects (Authenticated via gh CLI):", repo_options, key=f"gh_repo_{key_prefix}")
        
        if selected_repo != "(Select a GitHub Repository)":
            repo_data = next((r for r in repos if r["nameWithOwner"] == selected_repo), None)
            if repo_data:
                repo_name = repo_data["nameWithOwner"].split("/")[-1]
                target_path = os.path.join(target_base, repo_name)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🚀 Mount & Resume", key=f"resume_btn_{key_prefix}"):
                        if not os.path.exists(target_path):
                            with st.spinner(f"Cloning {repo_name} from GitHub..."):
                                subprocess.run(["git", "clone", repo_data["url"], target_path], capture_output=True)
                        st.session_state["workspace_dir"] = target_path
                        st.rerun()
                with col2:
                    if os.path.exists(target_path):
                        st.success(f"Available locally: `{target_path}`")
                    else:
                        st.info(f"Will clone to: `{target_path}`")
    else:
        st.info("💡 Install and authenticate `gh` CLI to auto-list your GitHub repositories.")
    
    # 2. Cloud Git URL Fallback
    git_url = st.text_input("☁️ Manual Git Mount (Paste URL):", placeholder="https://github.com/user/repo.git", key=f"git_url_{key_prefix}")
    if git_url and st.button("⬇️ Clone Repository", key=f"clone_btn_{key_prefix}"):
        repo_name = git_url.split("/")[-1].replace(".git", "") if "/" in git_url else "unknown_repo"
        target_path = os.path.join(target_base, repo_name)
        if not os.path.exists(target_path):
            with st.spinner(f"Cloning {repo_name}..."):
                subprocess.run(["git", "clone", git_url, target_path], capture_output=True)
        st.session_state["workspace_dir"] = target_path
        st.rerun()
                    
    # 3. Absolute Path Override
    default_dir = st.session_state.get("workspace_dir", os.getcwd())
    workspace_dir = st.text_input("🎯 Active Directory (Absolute Path)", default_dir, key=f"workspace_dir_{key_prefix}")
    st.session_state["workspace_dir"] = workspace_dir
    
    if not os.path.exists(workspace_dir):
        st.error("Directory does not exist on your Mac!")
        return None
    else:
        st.success(f"Agent is locked onto: `{workspace_dir}`")
        return workspace_dir"""

content = content.replace(old_func, new_func)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("GitHub Repo List added to Workspace Config.")
