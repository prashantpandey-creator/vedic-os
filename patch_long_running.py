import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Add checkpoint import
old_import = "from core.tool_registry import ToolRegistry"
new_import = """from core.tool_registry import ToolRegistry
    from core.checkpoint import save_checkpoint, load_checkpoint, clear_checkpoints, build_phase_summary"""
content = content.replace(old_import, new_import, 1)  # Only in first occurrence (tab4)

# 2. Replace the IDLE state with checkpoint-aware resume + long-running toggle
old_idle = """    if st.session_state.omni_state == "IDLE":
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
                st.rerun()"""

new_idle = """    if st.session_state.omni_state == "IDLE":
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

        intent_prompt = st.text_area("What do you want the Omni-Agent to do?", "Run 'npm test', find the failing tests, and fix the codebase.")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            max_steps = st.slider("Max Autonomous Steps", 1, 30, 10)
        with col_s2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.session_state.hitl_enabled = st.checkbox("🛡️ Require Human Approval", value=True)
        with col_s3:
            st.markdown("<br>", unsafe_allow_html=True)
            long_running = st.checkbox("♾️ Long-Running Harness (Unlimited)", value=False)
        
        if st.button("🚀 Launch Autonomous Loop", type="primary"):
            with st.spinner("🐍 Mamba is ingesting codebase and generating blueprint..."):
                messages, blueprint = init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir)
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
                st.rerun()"""
content = content.replace(old_idle, new_idle)

# 3. Add phase transition + checkpointing in the GENERATING state
# After max_steps, instead of terminating, trigger a phase transition
old_max_check = """            if st.session_state.omni_step > st.session_state.max_steps:
                st.error("Max steps reached. Terminating loop.")
                st.session_state.omni_state = "DONE"
                st.rerun()"""

new_max_check = """            if st.session_state.omni_step > st.session_state.max_steps:
                current_phase = st.session_state.get("phase", 1)
                
                if st.session_state.max_steps >= 999:
                    # LONG-RUNNING MODE: Phase transition instead of termination
                    phase_summary = build_phase_summary(st.session_state.omni_log)
                    if "phase_summaries" not in st.session_state:
                        st.session_state.phase_summaries = []
                    st.session_state.phase_summaries.append(phase_summary)
                    
                    # Save checkpoint before phase transition
                    save_checkpoint(workspace_dir, dict(st.session_state))
                    
                    # Re-ingest codebase with fresh eyes (files may have changed!)
                    with st.spinner("♻️ Phase {} complete. Re-ingesting codebase for Phase {}...".format(current_phase, current_phase + 1)):
                        messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir)
                    
                    # Inject prior phase summaries into the new system prompt
                    prior_context = "\\n".join(["Phase {}: {}".format(i+1, s) for i, s in enumerate(st.session_state.phase_summaries)])
                    messages[0]["content"] += "\\n\\nPRIOR PHASE SUMMARIES (your own earlier work):\\n" + prior_context
                    
                    st.session_state.omni_messages = messages
                    st.session_state.omni_log = []
                    st.session_state.omni_step = 1
                    st.session_state.action_history = []
                    st.session_state.phase = current_phase + 1
                    st.session_state.max_steps = 999  # keep going
                    st.info("♻️ Phase {} -> Phase {}. Fresh context window, persistent memory.".format(current_phase, current_phase + 1))
                    st.rerun()
                else:
                    # Normal mode: terminate
                    save_checkpoint(workspace_dir, dict(st.session_state))
                    st.error("Max steps reached. Session checkpointed.")
                    st.session_state.omni_state = "DONE"
                    st.rerun()"""
content = content.replace(old_max_check, new_max_check)

# 4. Add checkpoint save after every step
old_step_inc = """                st.session_state.omni_step += 1
                st.rerun()

        elif st.session_state.omni_state == "AWAITING_APPROVAL":"""

new_step_inc = """                st.session_state.omni_step += 1
                # Auto-checkpoint every 5 steps
                if st.session_state.omni_step % 5 == 0:
                    save_checkpoint(workspace_dir, dict(st.session_state))
                st.rerun()

        elif st.session_state.omni_state == "AWAITING_APPROVAL":"""
content = content.replace(old_step_inc, new_step_inc)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Long-running harness patched.")
