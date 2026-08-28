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
            claude_memories = []
            if os.path.exists(claude_dir):
                claude_memories = [f for f in os.listdir(claude_dir) if f.endswith('.md')]
            
            if claude_memories:
                selected_claude = st.selectbox("Select Claude Memory:", ["(None)"] + claude_memories)
                if selected_claude != "(None)" and st.button("📥 Ingest Claude Context"):
                    with open(os.path.join(claude_dir, selected_claude), 'r') as mf:
                        raw_context = mf.read()
                        
                    with st.spinner("🧠 Local LLM is synthesizing Claude's memory..."):
                        import requests
                        from config import OLLAMA_URL, INGEST_MODEL
                        
                        payload = {
                            "model": INGEST_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a Memory Synthesizer. Read this memory file from Claude Code. Extract the core architectural rules, findings, and context into a highly dense Markdown summary."},
                                {"role": "user", "content": raw_context[-80000:]}
                            ],
                            "stream": False,
                            "options": {"num_ctx": 32000, "temperature": 0.1}
                        }
                        
                        res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload).json()
                        intelligent_summary = res.get("message", {}).get("content", "Failed to summarize.")
                        
                        from core.ollama_api import evict_model
                        evict_model(INGEST_MODEL)
                        
                        from core.memory_graph import append_vritti
                        append_vritti(f"Imported Claude Context: {selected_claude}", "Claude-Code", intelligent_summary, workspace_dir)
                        st.success(f"✨ Synthesized and ingested {selected_claude} into Memory!")
            else:
                st.info("No Claude memory found in ~/claude-sync/memory/")
                
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
                            with open(transcript_path, 'r') as tf:
                                # We can read the whole thing, but let's safely take the last 1000 lines 
                                # to fit in Mamba's 32k window
                                raw_lines = tf.readlines()[-1000:]
                                raw_transcript = "".join(raw_lines)
                                
                            with st.spinner("🧠 Local LLM is synthesizing Antigravity context..."):
                                import requests
                                from config import OLLAMA_URL, INGEST_MODEL
                                
                                payload = {
                                    "model": INGEST_MODEL,
                                    "messages": [
                                        {"role": "system", "content": "You are a Memory Synthesizer. Read this JSONL transcript from an advanced AI session. Extract all core architectural decisions, user instructions, and technical context into a clean, concise Markdown summary. Do not output JSON."},
                                        {"role": "user", "content": raw_transcript[-80000:]} # safe cap
                                    ],
                                    "stream": False,
                                    "options": {"num_ctx": 32000, "temperature": 0.1}
                                }
                                
                                res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload).json()
                                intelligent_summary = res.get("message", {}).get("content", "Failed to summarize.")
                                
                                from core.ollama_api import evict_model
                                evict_model(INGEST_MODEL)
                                
                                from core.memory_graph import append_vritti
                                append_vritti(f"Imported Antigravity Context: {selected_ag}", "Antigravity", intelligent_summary, workspace_dir)
                                st.success("✨ Local LLM successfully synthesized and ingested the external session!")
                                
                        except Exception as e:
                            st.error(f"Error during intelligent extraction: {e}")
                    else:
                        st.error("Transcript not found for this session.")
            else:
                st.info("No Antigravity sessions found.")

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
        med_idx = models.index(INGEST_MODEL) if INGEST_MODEL in models else 0
        meditate_model = st.selectbox("🧘 Meditate Layer (Scanner)", models, index=med_idx)
    with col2:
        target = FAST_MODEL
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if HEAVY_MODEL in models else 0)
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
    st.markdown("This is the **Next-Gen Agentic Loop**. Mamba-2 ingests the codebase, and Qwen iterates through your terminal.")
    
    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    render_file_tree(workspace_dir)
    render_brain_importer(workspace_dir)
    
    from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action
    from core.terminal_engine import TerminalEngine
    from core.tool_registry import ToolRegistry
    from core.file_system import apply_search_replace
    from core.memory_graph import append_vritti
    import json
    
    col1, col2 = st.columns(2)
    with col1:
        med_idx = models.index(INGEST_MODEL) if INGEST_MODEL in models else 0
        meditate_model = st.selectbox("🐍 SSM Ingestion Engine (Mamba)", models, index=med_idx)
    with col2:
        target = FAST_MODEL
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if HEAVY_MODEL in models else 0)
        coder_model = st.selectbox("🦅 Omni-Agent Typist (Llama-3 Abliterated)", models, index=cod_idx)

    # State Machine Initialization
    if "omni_state" not in st.session_state:
        st.session_state.omni_state = "IDLE"
        st.session_state.omni_step = 1
        st.session_state.omni_log = []
        st.session_state.omni_messages = []
        st.session_state.terminal = None
        st.session_state.action_history = []
        st.session_state.hitl_enabled = True

    if st.session_state.omni_state == "IDLE":
        intent_prompt = st.text_area("What do you want the Omni-Agent to do?", "Run 'npm test', find the failing tests, and fix the codebase.")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            max_steps = st.slider("Max Autonomous Steps", 1, 30, 10)
        with col_s2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.session_state.hitl_enabled = st.checkbox("🛡️ Require Human Approval for Terminal Commands", value=True)
        
        if st.button("🚀 Launch Autonomous Loop", type="primary"):
            with st.spinner("🐍 Mamba is ingesting codebase and generating blueprint..."):
                messages, blueprint = init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir)
                st.session_state.omni_messages = messages
                st.session_state.omni_bp = blueprint
                st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)
                st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)
                st.session_state.intent_prompt = intent_prompt
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

        # Handle current state
        if st.session_state.omni_state == "GENERATING":
            if st.session_state.omni_step > st.session_state.max_steps:
                st.error("Max steps reached. Terminating loop.")
                st.session_state.omni_state = "DONE"
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
                st.button("Continue to next step")
                st.stop()
            else:
                st.session_state.action_history.append(current_action_str)
            
            action = action_data.get("action")
            
            if action == "done":
                st.session_state.omni_state = "DONE"
                append_vritti(st.session_state.intent_prompt, "Omni-Loop", "[PRAMANA] Done", workspace_dir=workspace_dir)
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
            st.success("🎉 Omni-Agent has completed the task!")
            if st.button("Start New Task"):
                if st.session_state.terminal: st.session_state.terminal.cleanup()
                st.session_state.omni_state = "IDLE"
                st.rerun()
                
        # The Steer / Interrupt Button
        if st.session_state.omni_state != "DONE":
            st.markdown("---")
            steer = st.chat_input("🚨 Intervene / Steer the Agent mid-loop...")
            if steer:
                st.session_state.omni_messages.append({"role": "user", "content": f"🚨 USER OVERRIDE / STEER: {steer}"})
                st.toast("Feedback injected into Agent's memory!")


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
