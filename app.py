import streamlit as st
from config import DEFAULT_WORKSPACE_ROOT, DEFAULT_FALLBACK_DIR, CLAUDE_MEMORY_DIR, ANTIGRAVITY_BRAIN_DIR, FAST_MODEL, HEAVY_MODEL, INGEST_MODEL
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
st.html("""
<style>
    /* Glassmorphism Dark Theme */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background - Deep sophisticated gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        background-attachment: fixed;
        color: #e2e8f0;
    }

    /* Sidebar - Frosted Glass */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.4) !important;
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Headers and Topbar */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Inputs, TextAreas, SelectBoxes - Glassy */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }

    .stTextInput>div>div>input:focus, 
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>div:focus {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(99, 102, 241, 0.5) !important;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.2) !important;
    }

    /* Chat inputs */
    .stChatInputContainer {
        background-color: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
    }
    
    /* Info boxes and Warnings - Glassy variants */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }

    /* Buttons - Sleek Glowing */
    .stButton>button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(99, 102, 241, 0.2);
    }
    .stButton>button:active {
        transform: translateY(0px);
    }
    
    /* Primary buttons */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.6) 0%, rgba(139, 92, 246, 0.6) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.8) 0%, rgba(139, 92, 246, 0.8) 100%) !important;
        box-shadow: 0 5px 20px rgba(139, 92, 246, 0.4);
    }

    /* Containers and Expanders - Glass Cards */
    [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    [data-testid="stExpander"] > div[role="button"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
    }

    /* Code blocks */
    pre {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(5px);
    }

    /* Model Cards (Custom class) */
    .model-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 15px; 
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.3s ease;
    }
    .model-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.3);
    }
    .model-title { color: #818cf8; font-weight: 600; font-size: 1.1em; }
    .model-stat { color: #94a3b8; font-size: 0.9em; }
    .status-active { color: #4ade80; font-weight: 600; }

    /* Tabs Styling - Minimal Pill design */
    [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(0, 0, 0, 0.2);
        padding: 6px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 10px !important;
        border: none !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Hide annoying UI elements */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}

    /* Custom scrollbars */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>
""")

# ----------------- Sidebar -----------------
st.sidebar.title("🪷 Vedic Framework")
st.sidebar.markdown("Local Multi-Agent OS")

models = get_models()
if not models:
    st.sidebar.error("⚠️ Ollama is not running or no models found. Start Ollama and refresh.")
    st.stop()

st.sidebar.markdown("### Navigation")
st.sidebar.info("Use the **4 tabs** above to move between stages of the Vedic AI Engine — from raw model chat to full autonomous terminal execution.")

# ----------------- Main View -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Stage 1: Bare Model", 
    "🏗️ Stage 2: Sandbox Architect", 
    "🧬 Stage 3: Nidra Harness", 
    "🦅 Stage 4: Omni-Agent",
    "🧠 Model Manager"
])



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

@st.cache_data(ttl=300)
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
        return workspace_dir

def render_file_tree(workspace_dir):
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
            tree_str += f"{indent}📂 **{folder}/**\n"
        subindent = ' ' * 4 * (level + 1)
        for f in sorted(files):
            if not f.startswith('.'):
                tree_str += f"{subindent}📄 {f}\n"
                
    if tree_str:
        with st.expander("Explore Workspace Files", expanded=False):
            st.markdown(tree_str)
    else:
        st.info("Workspace is empty.")


def render_brain_importer(workspace_dir):
    import os
    import json
    
    with st.expander("🧠 Import External Agent Memory", expanded=False):
        st.markdown("Import context from cloud agents (Claude Code, Antigravity) directly into your Local Omni-Agent's memory.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Claude Code Memory**")
            claude_dir = CLAUDE_MEMORY_DIR
            claude_projects = []
            if os.path.exists(claude_dir):
                claude_projects = [d for d in os.listdir(claude_dir) if os.path.isdir(os.path.join(claude_dir, d)) and d.startswith("-")]
            
            if claude_projects:
                selected_claude = st.selectbox("Select Claude Project:", ["(None)"] + claude_projects)
                if selected_claude != "(None)" and st.button("📥 Ingest Claude Context"):
                    # Find MEMORY.md or first .md file
                    target_dir = os.path.join(claude_dir, selected_claude)
                    md_files = [f for f in os.listdir(target_dir) if f.endswith('.md')]
                    
                    if not md_files:
                        st.error("No .md files found in this Claude project directory.")
                    else:
                        mem_file = "MEMORY.md" if "MEMORY.md" in md_files else md_files[0]
                        with open(os.path.join(target_dir, mem_file), 'r') as mf:
                            raw_context = mf.read()
                            
                        st.info("🧠 Model pre-filling Claude context...")
                        synthesized_box = st.empty()
                        intelligent_summary = ""
                        
                        import requests
                        from config import OLLAMA_URL, INGEST_MODEL
                        
                        payload = {
                            "model": INGEST_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a Memory Synthesizer. Read this memory file from Claude Code. Extract the core architectural rules, findings, and context into a highly dense Markdown summary."},
                                {"role": "user", "content": raw_context[-12000:]}
                            ],
                            "stream": True,
                            "options": {"num_ctx": 4096, "temperature": 0.1}
                        }
                        
                        try:
                            res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True)
                            for line in res.iter_lines():
                                if line:
                                    chunk = json.loads(line)
                                    if "message" in chunk and "content" in chunk["message"]:
                                        intelligent_summary += chunk["message"]["content"]
                                        synthesized_box.markdown(f"**Synthesizing:**\n{intelligent_summary}▌")
                                        
                            synthesized_box.markdown(f"**Synthesis Complete:**\n{intelligent_summary}")
                            
                            from core.ollama_api import evict_model
                            evict_model(INGEST_MODEL)
                            
                            from core.memory_graph import append_vritti
                            append_vritti(f"Imported Claude Context: {selected_claude}", "Claude-Code", intelligent_summary, workspace_dir)
                            st.success(f"✨ Synthesized and ingested {selected_claude} into Memory!")
                            
                            # Auto-detect Workspace Directory from Claude slug
                            # Convert e.g. -Users-badenath-projects-vedic-puran to /Users/badenath/projects/vedic puran
                            parts = selected_claude.strip("-").split("-")
                            detected_cwd = None
                            if len(parts) >= 2:
                                # Try a few combinations of spaces vs hyphens in the last folder
                                base_path = "/" + "/".join(parts[:-1])
                                last_part = parts[-1]
                                
                                # 1. Literal translation
                                p1 = os.path.join(base_path, last_part)
                                # 2. Space instead of hyphen (common for claude slug)
                                p2 = os.path.join("/" + "/".join(parts[:-2]), parts[-2] + " " + parts[-1]) if len(parts) >= 3 else p1
                                
                                if os.path.exists(p2): detected_cwd = p2
                                elif os.path.exists(p1): detected_cwd = p1
                                
                            if detected_cwd:
                                st.info(f"📂 Detected active project directory: `{detected_cwd}`")
                                if st.button(f"🚀 Switch to this Project & Resume", key="claude_resume"):
                                    st.session_state["workspace_dir"] = detected_cwd
                                    st.session_state.intent_prompt = f"Resume session from Claude project '{selected_claude}' based on ingested MEMORY."
                                    st.rerun()
                            else:
                                st.warning(f"Could not automatically locate the workspace directory on disk. You may need to set it manually.")
                                
                        except Exception as e:
                            st.error(f"Error streaming Claude synthesis: {e}")
            else:
                st.info("No Claude projects found in ~/claude-sync/memory/")
                
        with col2:
            st.markdown("**Antigravity Transcripts**")
            ag_dir = ANTIGRAVITY_BRAIN_DIR
            ag_sessions = []
            if os.path.exists(ag_dir):
                # Just show the last 5 modified sessions for simplicity
                ag_sessions = sorted([d for d in os.listdir(ag_dir) if os.path.isdir(os.path.join(ag_dir, d)) and d != "tempmediaStorage"], key=lambda x: os.path.getmtime(os.path.join(ag_dir, x)), reverse=True)[:5]
                
            if ag_sessions:
                selected_ag = st.selectbox("Select Antigravity Session:", ["(None)"] + ag_sessions)
                if selected_ag != "(None)" and st.button("📥 Ingest Antigravity Context"):
                    transcript_path = os.path.join(ag_dir, selected_ag, ".system_generated", "logs", "transcript.jsonl")
                    if os.path.exists(transcript_path):
                        summary = f"Imported Antigravity Session: {selected_ag}\n"
                        try:
                            # PRE-FILTER: Don't send massive tool outputs to the LLM.
                            # Only send the Agent's thoughts and the User's intents.
                            filtered_transcript = ""
                            with open(transcript_path, 'r') as tf:
                                lines = tf.readlines()[-100:] # Just last 100 steps
                                for line in lines:
                                    try:
                                        step = json.loads(line)
                                        t = step.get("type", "")
                                        if t in ["USER_INPUT", "PLANNER_RESPONSE", "SYSTEM_MESSAGE"]:
                                            content = str(step.get("content", ""))
                                            # Truncate massive file reads from planner responses
                                            if len(content) > 1000: content = content[:1000] + "...[truncated]"
                                            filtered_transcript += f"\n[{t}]: {content}"
                                    except: pass
                                
                            st.info("🧠 Model pre-filling context...")
                            synthesized_box = st.empty()
                            intelligent_summary = ""
                            
                            import requests
                            from config import OLLAMA_URL, INGEST_MODEL
                            
                            payload = {
                                "model": INGEST_MODEL,
                                "messages": [
                                    {"role": "system", "content": "You are a Memory Synthesizer. Read this filtered transcript from an AI session. Extract the core architectural decisions and user intents into a concise Markdown summary."},
                                    {"role": "user", "content": filtered_transcript}
                                ],
                                "stream": True,
                                "options": {"num_ctx": 4096, "temperature": 0.1} # Much smaller context window
                            }
                            
                            res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True)
                            for line in res.iter_lines():
                                if line:
                                    chunk = json.loads(line)
                                    if "message" in chunk and "content" in chunk["message"]:
                                        intelligent_summary += chunk["message"]["content"]
                                        synthesized_box.markdown(f"**Synthesizing:**\n{intelligent_summary}▌")
                            
                            synthesized_box.markdown(f"**Synthesis Complete:**\n{intelligent_summary}")
                            
                            from core.ollama_api import evict_model
                            evict_model(INGEST_MODEL)
                            
                            from core.memory_graph import append_vritti
                            append_vritti(f"Imported Antigravity Context: {selected_ag}", "Antigravity", intelligent_summary, workspace_dir)
                            st.success("✨ Successfully ingested into Local Memory!")
                            
                            # Auto-detect Workspace Directory from tool calls
                            detected_cwd = None
                            try:
                                with open(transcript_path, 'r') as tf:
                                    cwds = {}
                                    for line in tf:
                                        if '"Cwd"' in line:
                                            try:
                                                step = json.loads(line)
                                                for call in step.get("tool_calls", []):
                                                    cwd = call.get("args", {}).get("Cwd")
                                                    if cwd and cwd != "/Users/badenath":
                                                        cwds[cwd] = cwds.get(cwd, 0) + 1
                                            except: pass
                                    if cwds:
                                        detected_cwd = max(cwds, key=cwds.get)
                            except: pass
                            
                            if detected_cwd and os.path.exists(detected_cwd):
                                st.info(f"📂 Detected active project directory: `{detected_cwd}`")
                                if st.button(f"🚀 Switch to this Project & Resume"):
                                    st.session_state["workspace_dir"] = detected_cwd
                                    st.session_state.intent_prompt = f"Resume session '{selected_ag}' based on the ingested PROJECT_MIND memory."
                                    st.rerun()
                                    
                        except Exception as e:
                            st.error(f"Error during intelligent extraction: {e}")
                    else:
                        st.error("Transcript not found for this session.")
            else:
                st.info("No Antigravity sessions found.")

# ----------------- Main View -----------------


# Sidebar globals used by Stage 1 chat and Stage 2 Architect
selected_model = st.sidebar.selectbox("Default Model", models, index=0)
system_prompt = st.sidebar.text_area("Global System Prompt", "You are an elite, highly intelligent AI assistant.")
st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 VRAM Monitor")
loaded_models = get_loaded_models()
if not loaded_models:
    st.sidebar.info("All models unloaded. Zero footprint. 🍃")
else:
    for m in loaded_models:
        name = m.get("name", "Unknown")
        size_gb = m.get("size", 0) / (1024**3)
        st.sidebar.warning(f"**{name}** — {size_gb:.2f} GB")
st.sidebar.markdown("---")
details = get_model_details(selected_model)
if details:
    st.sidebar.markdown(f"**Arch:** `{details.get('details', {}).get('family', 'Unknown')}` · **Quant:** `{details.get('details', {}).get('quantization_level', 'Unknown')}`")


with tab1:
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

with tab3:
    st.markdown("Use this mode to **autonomously modify an existing codebase**. Mamba-2 (SSM) scans the filesystem, your selected Genius Coder writes the unified diff, and the Nidra Harness logs the memory graph.")
    
    workspace_dir = render_workspace_config(key_prefix='tab3')
    if not workspace_dir: st.stop()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🧘 **Meditate Layer (Scanner):** `{INGEST_MODEL}`")
        meditate_model = INGEST_MODEL
    with col2:
        st.info(f"🧠 **Coder Layer (Abliterated):** `{FAST_MODEL}`")
        coder_model = FAST_MODEL

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

with tab4:
    st.markdown("This is the **Next-Gen Agentic Loop**. Mamba-2 ingests the codebase, and Qwen iterates through your terminal.")
    
    workspace_dir = render_workspace_config(key_prefix='tab4')
    if not workspace_dir: st.stop()
    render_file_tree(workspace_dir)
    render_brain_importer(workspace_dir)
    
    from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action
    from core.terminal_engine import TerminalEngine
    from core.tool_registry import ToolRegistry
    from core.checkpoint import save_checkpoint, load_checkpoint, clear_checkpoints, build_phase_summary
    from core.file_system import apply_search_replace
    from core.memory_graph import append_vritti
    import json
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🐍 **SSM Ingestion Engine:** `{INGEST_MODEL}`")
        meditate_model = INGEST_MODEL
    with col2:
        st.info(f"🦅 **Omni-Agent Typist:** `{FAST_MODEL}`")
        coder_model = FAST_MODEL

    # State Machine Initialization
    if "omni_state" not in st.session_state:
        st.session_state.omni_state = "IDLE"
        st.session_state.omni_step = 1
        st.session_state.total_steps = 1
        st.session_state.omni_log = []
        st.session_state.omni_messages = []
        st.session_state.terminal = None
        st.session_state.action_history = []
        st.session_state.hitl_enabled = True

    if "total_steps" not in st.session_state:
        st.session_state.total_steps = st.session_state.get("omni_step", 1)


    if st.session_state.omni_state == "IDLE":
        # Check for resumable checkpoint
        existing_cp = load_checkpoint(workspace_dir)
        if existing_cp:
            st.warning("📦 **Resumable Session Found!** The agent was previously working on this workspace.")
            st.info("Intent: _{}_  |  Phase: {} | Step: {}".format(existing_cp.get("intent","?"), existing_cp.get("phase",1), existing_cp.get("step",1)))
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if st.button("♻️ Resume Previous Session", type="primary"):
                    st.session_state.omni_messages = existing_cp.get("messages", [])
                    st.session_state.omni_log = existing_cp.get("log", [])
                    st.session_state.omni_step = existing_cp.get("step", 1)
                    st.session_state.total_steps = existing_cp.get("total_steps", existing_cp.get("step", 1))
                    st.session_state.action_history = existing_cp.get("action_history", [])
                    st.session_state.intent_prompt = existing_cp.get("intent", "")
                    st.session_state.phase = existing_cp.get("phase", 1)
                    st.session_state.phase_summaries = existing_cp.get("phase_summaries", [])
                    st.session_state.max_steps = 999
                    st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)
                    st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()
            with col_r2:
                if st.button("🗑️ Discard & Start Fresh"):
                    clear_checkpoints(workspace_dir)
                    st.rerun()
            st.markdown("---")

        if "omni_intent_val" not in st.session_state:
            st.session_state.omni_intent_val = ""
            
        col_t1, col_t2 = st.columns([5, 1])
        with col_t1:
            intent_prompt = st.text_area("What do you want the Omni-Agent to do?", key="omni_intent_val", height=100)
        with col_t2:
            st.html("<br>")
            if st.button("💡 Auto-Suggest"):
                with st.spinner("Analyzing repo..."):
                    context_data = ""
                    for fname in ["README.md", "PROJECT_MIND.md", "package.json"]:
                        fpath = os.path.join(workspace_dir, fname)
                        if os.path.exists(fpath):
                            with open(fpath, "r", errors="ignore") as mf:
                                context_data += f"\n--- {fname} ---\n" + mf.read()[:5000]
                    
                    if not context_data.strip():
                        try:
                            files = [f for f in os.listdir(workspace_dir) if os.path.isfile(os.path.join(workspace_dir, f)) and not f.startswith(".")]
                            for f in files[:5]:
                                with open(os.path.join(workspace_dir, f), "r", errors="ignore") as mf:
                                    context_data += f"\n--- {f} ---\n" + mf.read()[:1000]
                        except: pass

                    import requests
                    from config import OLLAMA_URL, INGEST_MODEL
                    
                    payload = {
                        "model": INGEST_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are an AI task suggester. Read the provided repo context and generate EXACTLY 1 actionable, specific sentence for what the AI agent should do next. DO NOT use markdown, DO NOT use bullet points, just output the raw sentence."},
                            {"role": "user", "content": context_data[-12000:]}
                        ],
                        "stream": False,
                        "options": {"num_ctx": 4096, "temperature": 0.8}
                    }
                    try:
                        res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload).json()
                        suggestion = res.get("message", {}).get("content", "").strip()
                        # Clean up markdown formatting if the LLM ignores instructions
                        suggestion = suggestion.replace("**", "").replace("*", "").replace("`", "")
                        if suggestion:
                            st.session_state.omni_intent_val = suggestion
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to auto-suggest: {e}")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            pass
        with col_s2:
            st.html("<br>")
            st.session_state.hitl_enabled = st.checkbox("🛡️ Require Human Approval", value=True)
        with col_s3:
            st.html("<br>")
            long_running = st.checkbox("♾️ Long-Running Harness (Unlimited)", value=False)
        
        if st.button("🚀 Launch Autonomous Loop", type="primary"):
            status_box = st.empty()
            with st.spinner("Initializing Phase 1..."):
                messages, blueprint = init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)
                st.session_state.omni_messages = messages
                st.session_state.omni_bp = blueprint
                st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)
                st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)
                st.session_state.intent_prompt = intent_prompt
                st.session_state.phase = 1
                st.session_state.phase_summaries = []
                if long_running:
                    st.session_state.max_steps = 999  # effectively unlimited
                    st.session_state.hitl_enabled = False
                else:
                    st.session_state.max_steps = max_steps
                st.session_state.omni_state = "GENERATING"
                st.rerun()

    else:
        # Render historical log
        st.markdown("---")
        st.subheader("🦅 Living Agent Transcript")
        
        # Render previous steps
        for log in st.session_state.omni_log:
            with st.expander(f"🦅 Step {log['step']}: {log.get('type', 'Action').upper()}", expanded=(log['step'] == st.session_state.omni_step - 1)):
                if 'raw' in log: st.code(log['raw'], language="json")
                
                if log.get('type') == 'command':
                    st.markdown(f"**💻 Terminal Output (Command: `{log['cmd']}`)**")
                    st.code(log['output'], language="bash")
                elif log.get('type') == 'pending_command':
                    st.warning(f"**⏳ Awaiting Approval for Command: `{log['cmd']}`**")
                elif log.get('type') == 'edit':
                    st.success(f"📝 Edited `{log['file']}`")
                    if 'diff' in log: st.code(log['diff'], language="diff")
                elif log.get('type') == 'loop_intercept':
                    st.error(log['output'])
                elif log.get('type') == 'artifact':
                    st.success(f"📄 Generated Artifact: `{log['title']}`")
                    with open(log['path'], 'r') as art_f:
                        st.markdown(art_f.read())
                elif log.get('type') == 'subagent':
                    st.info(f"🤖 Subagent ({log['role']}) Task: {log['task']}")
                    for entry in log['log']:
                        st.code(entry, language="bash")
                    st.success(f"Result: {log['msg']}")
                elif log.get('type') == 'github_pr':
                    st.success(f"🐙 **Pull Request Raised!**")
                    st.markdown(f"[View PR on GitHub]({log['url']})")
                elif log.get('type') == 'blueprint':
                    st.info("🐍 **Codebase Blueprint Generated:**")
                    st.markdown(log['blueprint'])

        # Handle current state
        if st.session_state.omni_state == "GENERATING":
            # 1. Absolute Termination Guard
            if st.session_state.total_steps > st.session_state.max_steps:
                save_checkpoint(workspace_dir, dict(st.session_state))
                st.error(f"Max total steps ({st.session_state.max_steps}) reached across all phases.")
                st.session_state.omni_state = "DONE"
                st.rerun()
                
            # 2. Context Window Overflow Guard (Phase Transition)
            # A typical local model context window (8k) overflows around 10-15 deep tool steps.
            # We flush at 10 steps to guarantee stability.
            if st.session_state.omni_step > 10:
                current_phase = st.session_state.get("phase", 1)
                
                phase_summary = build_phase_summary(st.session_state.omni_log)
                if "phase_summaries" not in st.session_state:
                    st.session_state.phase_summaries = []
                st.session_state.phase_summaries.append(phase_summary)
                
                # Save checkpoint before phase transition
                save_checkpoint(workspace_dir, dict(st.session_state))
                
                st.info(f"♻️ Context window nearing capacity (10 steps). Compressing Phase {current_phase} and re-ingesting codebase...")
                status_box = st.empty()
                messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)
                
                # Inject compressed memory of all prior phases
                prior_context = "\n".join([f"Phase {i+1}: {s}" for i, s in enumerate(st.session_state.phase_summaries)])
                messages[0]["content"] += "\n\nPRIOR PHASE SUMMARIES (your own earlier work):\n" + prior_context
                
                st.session_state.omni_messages = messages
                st.session_state.omni_log = [{
                    "step": 0,
                    "type": "blueprint",
                    "blueprint": blueprint
                }]
                st.session_state.omni_step = 1
                st.session_state.action_history = []
                st.session_state.phase = current_phase + 1
                st.info(f"♻️ Phase {current_phase} -> Phase {current_phase + 1}. Context flushed. Memory preserved.")
                st.rerun()
                
            st.write(f"🦅 **[STEP {st.session_state.omni_step}/{st.session_state.max_steps}]** Thinking...")
            step_container = st.container()
            step_placeholder = step_container.empty()
            
            raw_response = generate_next_thought(coder_model, st.session_state.omni_messages, step_placeholder)
            st.session_state.omni_messages.append({"role": "assistant", "content": raw_response})
            action_data = parse_action(raw_response)
            
            st.session_state.current_action = action_data
            st.session_state.current_raw = raw_response
            
            # Loop Detection
            current_action_str = json.dumps(action_data, sort_keys=True)
            if current_action_str in st.session_state.action_history[-3:]:
                st.session_state.omni_messages.append({"role": "user", "content": "🚨 SYSTEM OVERRIDE: You just attempted the exact same action you already tried. You MUST try a completely different approach or declare 'done'."})
                st.session_state.action_history.append("FORCED_PIVOT")
                
                # Save to log so UI doesn't lose it
                st.session_state.omni_log.append({
                    "step": st.session_state.omni_step,
                    "type": "loop_intercept",
                    "raw": raw_response,
                    "output": "🚨 CRITICAL LOOP DETECTED. The engine intercepted the duplicate action and forced a pivot."
                })
                
                st.warning("⚠️ Loop detected. Forcing agent to pivot.")
                st.session_state.omni_step += 1
                st.session_state.total_steps += 1
                st.button("Continue to next step")
                st.stop()
            else:
                st.session_state.action_history.append(current_action_str)
            
            action = action_data.get("action")
            
            if action == "done":
                st.session_state.omni_state = "DONE"
                from core.checkpoint import build_phase_summary
                summary = build_phase_summary(st.session_state.omni_log)
                append_vritti(st.session_state.intent_prompt, "Omni-Loop", "[PRAMANA] Done", extra="**Marathon Session Summary:**\n" + summary, workspace_dir=workspace_dir)
                st.rerun()
                
            elif action == "run_command" and st.session_state.hitl_enabled:
                cmd = action_data.get("command", "")
                st.session_state.omni_log.append({
                    "step": st.session_state.omni_step, 
                    "type": "pending_command", 
                    "cmd": cmd, 
                    "raw": raw_response
                })
                st.session_state.omni_step += 1
                st.session_state.total_steps += 1
                st.session_state.omni_state = "AWAITING_APPROVAL"
                st.rerun()
            else:
                # Dynamic Tool Registry Execution
                result_obj = st.session_state.registry.execute_tool(action_data, fast_model=FAST_MODEL, main_model=coder_model)
                
                log_entry = {"step": st.session_state.omni_step, "raw": raw_response}
                log_entry.update(result_obj)
                st.session_state.omni_log.append(log_entry)
                
                st.session_state.omni_messages.append({"role": "user", "content": result_obj.get("msg", "")})
                st.session_state.omni_step += 1
                st.session_state.total_steps += 1
                # Auto-checkpoint every 5 steps
                if st.session_state.omni_step % 5 == 0:
                    save_checkpoint(workspace_dir, dict(st.session_state))
                st.rerun()

        elif st.session_state.omni_state == "AWAITING_APPROVAL":
            cmd = st.session_state.current_action.get("command")
            st.warning(f"🚨 **Human-in-the-Loop Approval Required**")
            st.info("The agent's thought process for this command is preserved in the log above.")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Approve & Execute", type="primary"):
                    output = st.session_state.terminal.execute(cmd)
                    
                    # Update the pending log entry
                    for log in reversed(st.session_state.omni_log):
                        if log.get("type") == "pending_command":
                            log["type"] = "command"
                            log["output"] = output
                            break
                            
                    st.session_state.omni_messages.append({"role": "user", "content": f"Command Executed.\nOutput:\n```\n{output}\n```"})
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()
            with col_b:
                steer_input = st.text_input("Reject & Steer Agent:", placeholder="No, run 'npm install' instead.")
                if st.button("🚫 Reject"):
                    for log in reversed(st.session_state.omni_log):
                        if log.get("type") == "pending_command":
                            log["type"] = "rejected_command"
                            log["output"] = f"🚫 User rejected execution. Feedback: {steer_input}"
                            break
                            
                    st.session_state.omni_messages.append({"role": "user", "content": f"USER REJECTED COMMAND. Feedback: {steer_input}"})
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()
                    
        elif st.session_state.omni_state == "DONE":
            st.success("🎉 Agent is standing by.")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("Start Completely New Task"):
                    if st.session_state.terminal: st.session_state.terminal.cleanup()
                    from core.checkpoint import clear_checkpoints
                    clear_checkpoints(workspace_dir)
                    st.session_state.omni_state = "IDLE"
                    # Wipe the intent to encourage fresh auto-suggest
                    if "omni_intent_val" in st.session_state:
                        del st.session_state["omni_intent_val"]
                    st.rerun()
            
            # Allow conversational follow-ups without wiping context
            st.markdown("---")
            follow_up = st.chat_input("Ask a follow-up question or assign a new task...")
            if follow_up:
                st.session_state.omni_messages.append({"role": "user", "content": follow_up})
                st.session_state.max_steps += 5 # Give it more steps to complete the follow-up
                st.session_state.omni_state = "GENERATING"
                st.rerun()
                
        # The Steer / Interrupt Button
        if st.session_state.omni_state in ["GENERATING", "AWAITING_APPROVAL"]:
            st.markdown("---")
            steer = st.chat_input("🚨 Intervene / Steer the Agent mid-loop...")
            if steer:
                st.session_state.omni_messages.append({"role": "user", "content": f"🚨 USER OVERRIDE / STEER: {steer}"})
                st.toast("Feedback injected into Agent's memory!")


with tab2:
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


with tab5:
    st.header("🧠 Local Model Manager")
    st.markdown("Pull, delete, and manage your local Ollama models directly from this UI.")
    
    from core.ollama_api import pull_model, delete_model, evict_all_models
    
    col_m1, col_m2 = st.columns([2, 1])
    
    with col_m1:
        st.subheader("📥 Download New Model")
        new_model_name = st.text_input("Enter Ollama model name (e.g. `llama3.1:8b`, `qwen2.5:32b`)")
        if st.button("Pull Model", type="primary"):
            if new_model_name:
                pull_box = st.empty()
                pull_box.info(f"Downloading `{new_model_name}`... This may take a while.")
                res = pull_model(new_model_name)
                if res and res.status_code == 200:
                    import json
                    for line in res.iter_lines():
                        if line:
                            data = json.loads(line)
                            status = data.get("status", "")
                            if "total" in data and "completed" in data:
                                pct = (data["completed"] / data["total"]) * 100
                                pull_box.info(f"Downloading `{new_model_name}`: {pct:.1f}% - {status}")
                            else:
                                pull_box.info(f"Downloading `{new_model_name}`: {status}")
                    pull_box.success(f"Successfully pulled `{new_model_name}`!")
                    time.sleep(1)
                    st.rerun()
                else:
                    pull_box.error(f"Failed to pull `{new_model_name}`. Check your internet or Ollama connection.")
            else:
                st.warning("Please enter a model name.")
                
        st.markdown("---")
        st.subheader("🧹 VRAM Management")
        if st.button("Unload All Models from VRAM (Free Memory)"):
            evict_all_models()
            st.success("All models evicted from VRAM.")
            time.sleep(1)
            st.rerun()

    with col_m2:
        st.subheader("📦 Installed Models")
        for m in models:
            details = get_model_details(m)
            if details:
                size_gb = details.get("size", 0) / (1024**3)
                param_size = details.get("details", {}).get("parameter_size", "Unknown")
                quant = details.get("details", {}).get("quantization_level", "Unknown")
                
                with st.expander(f"🤖 {m} ({size_gb:.1f} GB)"):
                    st.write(f"**Parameters:** {param_size}")
                    st.write(f"**Quantization:** {quant}")
                    if st.button(f"🗑️ Delete {m}", key=f"del_{m}"):
                        if delete_model(m):
                            st.success(f"Deleted {m}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to delete {m}")
# force trigger streamlit hot-reload
