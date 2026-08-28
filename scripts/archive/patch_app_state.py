import sys
import re

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Find the start of the Omni-Agent block
omni_start_marker = 'elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":'
arch_start_marker = 'else:\n    st.markdown("Describe an app below.'

omni_code = """elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":
    st.markdown("This is the **Next-Gen Agentic Loop**. Mamba-2 ingests the codebase, and Qwen iterates through your terminal.")
    
    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    render_file_tree(workspace_dir)
    
    from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action
    from core.terminal_engine import TerminalEngine
    from core.file_system import apply_search_replace
    from core.memory_graph import append_vritti
    import json
    
    col1, col2 = st.columns(2)
    with col1:
        med_idx = models.index("granite4:3b-h") if "granite4:3b-h" in models else 0
        meditate_model = st.selectbox("🐍 SSM Ingestion Engine (Mamba)", models, index=med_idx)
    with col2:
        target = "mannix/llama3.1-8b-abliterated:latest"
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0)
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
            with st.expander(f"🦅 Step {log['step']}: {log.get('type', 'Action')}", expanded=False):
                if 'raw' in log: st.code(log['raw'], language="json")
                if log.get('type') == 'command':
                    st.markdown(f"**💻 Terminal Output (Command: `{log['cmd']}`)**")
                    st.code(log['output'], language="bash")
                elif log.get('type') == 'edit':
                    st.success(f"📝 Edited `{log['file']}`")
                    if 'diff' in log: st.code(log['diff'], language="diff")

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
                
            elif action == "edit_file":
                filepath = action_data.get("file")
                search = action_data.get("search", "")
                replace = action_data.get("replace", "")
                
                try:
                    diff_str = apply_search_replace(filepath, search, replace, workspace_dir=workspace_dir)
                    st.session_state.omni_log.append({"step": st.session_state.omni_step, "type": "edit", "file": filepath, "raw": raw_response, "diff": diff_str})
                    st.session_state.omni_messages.append({"role": "user", "content": f"File {filepath} edited successfully."})
                except Exception as e:
                    st.session_state.omni_messages.append({"role": "user", "content": f"Edit failed: {e}\\nPlease fix your search block and try again."})
                    
                st.session_state.omni_step += 1
                st.rerun()
                
            elif action == "run_command":
                if st.session_state.hitl_enabled:
                    st.session_state.omni_state = "AWAITING_APPROVAL"
                    st.rerun()
                else:
                    cmd = action_data.get("command", "echo 'No command'")
                    output = st.session_state.terminal.execute(cmd)
                    st.session_state.omni_log.append({"step": st.session_state.omni_step, "type": "command", "cmd": cmd, "raw": raw_response, "output": output})
                    st.session_state.omni_messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```"})
                    st.session_state.omni_step += 1
                    st.rerun()

        elif st.session_state.omni_state == "AWAITING_APPROVAL":
            cmd = st.session_state.current_action.get("command")
            st.warning(f"🚨 **Human-in-the-Loop Approval Required**")
            st.code(f"$ {cmd}", language="bash")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Approve & Execute", type="primary"):
                    output = st.session_state.terminal.execute(cmd)
                    st.session_state.omni_log.append({"step": st.session_state.omni_step, "type": "command", "cmd": cmd, "raw": st.session_state.current_raw, "output": output})
                    st.session_state.omni_messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```"})
                    st.session_state.omni_step += 1
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()
            with col_b:
                steer_input = st.text_input("Reject & Steer Agent:", placeholder="No, run 'npm install' instead.")
                if st.button("🚫 Reject"):
                    st.session_state.omni_messages.append({"role": "user", "content": f"USER REJECTED COMMAND. Feedback: {steer_input}"})
                    st.session_state.omni_step += 1
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

"""

prefix = content[:content.find(omni_start_marker)]
suffix = content[content.find(arch_start_marker):]

new_content = prefix + omni_code + "\n" + suffix

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(new_content)

print("Omni State Machine UI patched in app.py")
