import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Replace render_workspace_config with the GitHub Auth version
old_render = """def render_workspace_config():
    st.markdown("### 📂 Workspace Target")
    st.info("Point the AI to the directory you want to modify.")
    
    workspace_dir = st.text_input("Absolute Path to Project Directory:", "/Users/badenath/projects/local-llm-ui")
    
    if not os.path.exists(workspace_dir):
        st.warning("⚠️ Directory does not exist. The agent may fail to read files.")
        
    return workspace_dir"""

new_render = """def render_workspace_config():
    import subprocess
    import json
    
    st.markdown("### 🐙 GitHub Workspace Mounter")
    
    # Check for GitHub CLI Auth
    gh_auth = False
    repos = []
    try:
        res = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if "Logged in to github.com" in res.stdout or "Logged in to github.com" in res.stderr:
            gh_auth = True
            repo_res = subprocess.run(["gh", "repo", "list", "--json", "nameWithOwner", "--limit", "20"], capture_output=True, text=True)
            if repo_res.returncode == 0:
                repos = [r["nameWithOwner"] for r in json.loads(repo_res.stdout)]
    except Exception:
        pass
        
    if gh_auth and repos:
        st.success("✅ **GitHub Authenticated:** Secure connection to GitHub CLI established.")
        repo_target = st.selectbox("Select Repository to Mount:", ["(Local Path)"] + repos)
        
        if repo_target != "(Local Path)":
            workspace_dir = os.path.join(os.path.expanduser("~/vedic_workspaces"), repo_target.split("/")[1])
            if not os.path.exists(workspace_dir):
                if st.button(f"⬇️ Clone {repo_target} Now"):
                    with st.spinner("Cloning..."):
                        os.makedirs(os.path.dirname(workspace_dir), exist_ok=True)
                        subprocess.run(["gh", "repo", "clone", repo_target, workspace_dir])
                    st.rerun()
                return None
            st.info(f"📂 Mounted at: `{workspace_dir}`")
            return workspace_dir
            
    st.info("Fallback: Point the AI to a local directory.")
    workspace_dir = st.text_input("Absolute Path to Project Directory:", "/Users/badenath/projects/local-llm-ui")
    
    if not os.path.exists(workspace_dir):
        st.warning("⚠️ Directory does not exist.")
        
    return workspace_dir"""
content = content.replace(old_render, new_render)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("GitHub Mounter UI Patched")
