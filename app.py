import streamlit as st
import json
import requests
import time
import os

from core.ollama_api import get_models, get_loaded_models, get_model_details, OLLAMA_URL
from agents.architect import run_architect_pipeline
from agents.coder_nidra import run_nidra_pipeline

# ----------------- UI Config -----------------
st.set_page_config(page_title="Vedic Framework OS", page_icon="🪷", layout="wide")

# Custom CSS for glowing dark mode
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .stTextInput>div>div>input { background-color: #161b22; color: #c9d1d9; }
    .stSelectbox>div>div>div { background-color: #161b22; color: #c9d1d9; }
    .stDeployButton {display:none;}
    [data-testid="stHeader"] {background-color: transparent;}
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .model-card {
        background-color: #21262d; border: 1px solid #30363d; border-radius: 8px; padding: 15px; margin-bottom: 10px;
    }
    .model-title { color: #58a6ff; font-weight: bold; font-size: 1.1em; }
    .model-stat { color: #8b949e; font-size: 0.9em; }
    .status-active { color: #3fb950; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ----------------- Sidebar -----------------
st.sidebar.title("🪷 Vedic Framework")
st.sidebar.markdown("Local Multi-Agent OS")

models = get_models()
if not models:
    st.sidebar.error("⚠️ Ollama is not running or no models found. Start Ollama and refresh.")
    st.stop()

st.sidebar.markdown("### Architecture Mode")
app_mode = st.sidebar.radio("Select Framework Pillar:", [
    "💬 Standard Chat (Hybrid Non-Transformers)",
    "🏗️ Code Compiler Manifestor (Vyasa Sandbox)",
    "🧬 Coding Agent with Harness (Nidra)",
    "🦅 Omni-Agent (Autonomous Terminal Loop)"
])

st.sidebar.markdown("### Global Settings")
selected_model = st.sidebar.selectbox("Default Model", models, index=0)
system_prompt = st.sidebar.text_area("Global System Prompt", "You are an elite, highly intelligent AI assistant.")

# Active Memory Monitor
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Active Memory Monitor")
loaded_models = get_loaded_models()

if not loaded_models:
    st.sidebar.info("All models unloaded. Zero footprint. 🍃")
else:
    for m in loaded_models:
        name = m.get("name", "Unknown")
        size_gb = m.get("size", 0) / (1024**3)
        st.sidebar.warning(f"**{name}**\n\nTaking up **{size_gb:.2f} GB** of RAM")

# Model Details Panel
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔬 Model Details")
details = get_model_details(selected_model)
if details:
    st.sidebar.markdown(f"**Architecture:** `{details.get('details', {}).get('family', 'Unknown')}`")
    st.sidebar.markdown(f"**Params:** `{details.get('details', {}).get('parameter_size', 'Unknown')}`")
    st.sidebar.markdown(f"**Quantization:** `{details.get('details', {}).get('quantization_level', 'Unknown')}`")

def render_vyasa_response(json_plan):
    try:
        plan = json.loads(json_plan)
    except Exception as e:
        return f"*Error: Model did not return valid JSON. Output was:* {json_plan}"
    
    response = f"**🧘‍♂️ Vyasa's Understanding:** _{plan.get('understanding', '')}_\n\n---\n\n"
    response += f"**Core Insight:**\n{plan.get('insight', '')}\n\n"
    
    if plan.get("key_phrases"):
        response += "**As it is written:** " + ' '.join([f'"{p}"' for p in plan.get("key_phrases")]) + "\n\n"
        
    return response

def render_workspace_config():
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

# ----------------- Main View -----------------
st.title(app_mode)
st.markdown("---")

if app_mode == "💬 Standard Chat (Hybrid Non-Transformers)":
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    mount_context = st.checkbox("Mount Local Workspace (Feed Infinite Context)", value=False)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Message your local model..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            status_placeholder = st.empty()
            tps_placeholder = st.empty()
            
            full_response = ""
            messages = st.session_state.messages.copy()
            final_system_prompt = system_prompt
            
            if mount_context:
                from core.file_system import build_tree_with_hints
                try:
                    file_tree = build_tree_with_hints()
                    final_system_prompt += f"\n\n[SYSTEM]: The user has mounted their local workspace. Here is the directory tree for context:\n{file_tree}"
                except: pass
            
            if "vyasa" not in selected_model.lower() and final_system_prompt:
                messages = [{"role": "system", "content": final_system_prompt}] + messages
            
            payload = {"model": selected_model, "messages": messages, "stream": True}
            
            try:
                with status_placeholder, st.spinner("Loading model into memory & thinking..."):
                    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=120)
                    response.raise_for_status()
                    status_placeholder.empty() 
                    
                    start_time = None
                    token_count = 0
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                if start_time is None: start_time = time.time()
                                token_count += 1
                                full_response += chunk["message"]["content"]
                                message_placeholder.markdown(full_response + "▌")
                                
                                if start_time:
                                    elapsed = time.time() - start_time
                                    if elapsed > 0.5:
                                        tps = token_count / elapsed
                                        color = "green" if tps >= 20 else ("orange" if tps >= 10 else "red")
                                        tps_placeholder.markdown(f"**Speed:** :{color}[{tps:.1f} tokens/sec]")
                
                if "vyasa" in selected_model.lower():
                    rendered = render_vyasa_response(full_response)
                    final_display = f"**[RAW JSON]:**\n```json\n{full_response}\n```\n\n**[RENDERED SPEECH]:**\n\n{rendered}"
                    message_placeholder.markdown(final_display)
                    full_response = final_display
                else:
                    message_placeholder.markdown(full_response)
                    
                tps_placeholder.empty()
            except Exception as e:
                status_placeholder.empty()
                st.error(f"Failed to connect: {e}")
                full_response = "Error communicating with the model."
            
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()

elif app_mode == "🧬 Coding Agent with Harness (Nidra)":
    st.markdown("Use this mode to **autonomously modify an existing codebase**. Mamba-2 (SSM) scans the filesystem, your selected Genius Coder writes the unified diff, and the Nidra Harness logs the memory graph.")
    
    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    
    col1, col2 = st.columns(2)
    with col1:
        med_idx = models.index("granite4:3b-h") if "granite4:3b-h" in models else 0
        meditate_model = st.selectbox("🧘 Meditate Layer (Scanner)", models, index=med_idx)
    with col2:
        target = "mannix/llama3.1-8b-abliterated:latest"
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0)
        coder_model = st.selectbox("🧠 Coder Layer (Fast Abliterated)", models, index=cod_idx)

    intent_prompt = st.text_area("What do you want to change or fix?", "Add a dark mode toggle to the sidebar in app.py")
    
    if st.button("🚀 Execute Edit", type="primary"):
        status = st.empty()
        stream_placeholder = st.empty()
        
        try:
            final_edits = run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder, workspace_dir)
            st.session_state["last_nidra_edits"] = final_edits
            
            st.success("🎉 Edit applied successfully and Memory Graph updated!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Execution Failed: {e}")

    if "last_nidra_edits" in st.session_state and st.session_state["last_nidra_edits"]:
        st.markdown("---")
        st.subheader("🛠️ Modified Files")
        st.info("💡 **Git Tracking:** A checkpoint was created automatically. Run `git diff HEAD~1` in your terminal to see the exact unified diff, or `git reset --hard HEAD~1` to undo this change.")
        
        for edit in st.session_state["last_nidra_edits"]:
            with st.expander(f"📄 {edit['file']} (Modified)"):
                st.markdown("**Search Block Replaced:**")
                st.code(edit['search'], language="python")
                st.markdown("**New Code:**")
                st.code(edit['replace'], language="python")
                
        with st.expander("View Memory Graph (PROJECT_MIND.md)"):
            memory_path = os.path.join(workspace_dir, "PROJECT_MIND.md")
            if os.path.exists(memory_path):
                with open(memory_path, "r", encoding="utf-8") as f:
                    st.markdown(f.read())

elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":
    st.markdown("This is the **Next-Gen Agentic Loop**. Mamba-2 ingests the entire Git repository to build an architectural blueprint. Qwen takes control of your Mac's Zsh terminal, looping autonomously to edit files, run scripts, read stdout errors, and fix bugs until the task is complete.")
    
    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    
    from agents.omni_agent import run_omni_loop
    
    col1, col2 = st.columns(2)
    with col1:
        med_idx = models.index("granite4:3b-h") if "granite4:3b-h" in models else 0
        meditate_model = st.selectbox("🐍 SSM Ingestion Engine (Mamba)", models, index=med_idx)
    with col2:
        target = "mannix/llama3.1-8b-abliterated:latest"
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0)
        coder_model = st.selectbox("🦅 Omni-Agent Typist (Llama-3 Abliterated)", models, index=cod_idx)

    intent_prompt = st.text_area("What do you want the Omni-Agent to do?", "Run 'npm test', find the failing tests, and fix the codebase.")
    max_steps = st.slider("Max Autonomous Steps", min_value=1, max_value=30, value=10, help="How many times the agent is allowed to run a command, read the error, and try again before giving up.")
    
    if st.button("🚀 Launch Autonomous Loop", type="primary"):
        status = st.empty()
        ui_container = st.container()
        
        try:
            exec_log, blueprint = run_omni_loop(intent_prompt, meditate_model, coder_model, status, ui_container, workspace_dir, max_steps)
            st.session_state["last_omni_log"] = exec_log
            st.session_state["last_omni_bp"] = blueprint
            
            st.success("🎉 Omni-Agent has completed the execution loop!")
            import time
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Execution Failed: {e}")

    if "last_omni_log" in st.session_state:
        st.markdown("---")
        st.subheader("🛠️ Agent Execution Log")
        st.info("💡 **Git Tracking:** A checkpoint was created before the loop started. Run `git reset --hard HEAD~1` to undo everything.")
        
        with st.expander("🐍 View Mamba's Architectural Blueprint"):
            st.markdown(st.session_state["last_omni_bp"])
            
        for log in st.session_state["last_omni_log"]:
            if log["type"] == "command":
                st.code(f"$ {log['cmd']}", language="bash")
            elif log["type"] == "edit":
                st.code(f"📝 Edited file: {log['file']}", language="markdown")

else:
    st.markdown("Describe an app below. The **Architect** will design it, and the **Coder** will manifest it into the sandbox.")
    app_prompt = st.text_area("What do you want to build?", "Build a simple weather dashboard with an API route to fetch current weather data")
    
    if st.button("🚀 Build App Now", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            graph, generated_files, html_content = run_architect_pipeline(app_prompt, status_text, progress_bar, selected_model)
            
            if html_content:
                import streamlit.components.v1 as components
                components.html(html_content, height=700, scrolling=True)
                
            st.session_state["last_app_html"] = html_content
            st.session_state["last_app_files"] = generated_files
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"Build Failed: {e}")

    # --- Render persisted App Builder state ---
    if "last_app_files" in st.session_state and st.session_state["last_app_files"]:
        st.markdown("---")
        st.subheader("🛠️ Persisted Application")
        if st.session_state.get("last_app_html"):
            import streamlit.components.v1 as components
            st.success("✨ Restored Vyasa Sandbox from Memory")
            components.html(st.session_state["last_app_html"], height=700, scrolling=True)
            
        st.write("📄 **Generated Source Code**")
        st.info("💡 **Native Execution:** To execute the actual compiled React/FastAPI code locally, run the following in your terminal:")
        try:
            app_dir = st.session_state["last_app_files"][0]["filename"].split("/")[0] if st.session_state["last_app_files"] else "GeneratedApp"
            st.code(f"cd {app_dir} && chmod +x deploy.sh && ./deploy.sh", language="bash")
        except: pass

        for f in st.session_state["last_app_files"]:
            with st.expander(f"📄 {f['filename']}"):
                language = "typescript" if f['filename'].endswith(".ts") or f['filename'].endswith(".tsx") else "javascript"
                if f['filename'].endswith(".sh"): language = "bash"
                st.code(f['code'], language=language)
