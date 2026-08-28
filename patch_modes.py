import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

import re

old_controls = """        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            max_steps = st.slider("Max Autonomous Steps", 1, 30, 10)
        with col_s2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.session_state.hitl_enabled = st.checkbox("🛡️ Require Human Approval", value=True)
        with col_s3:
            st.markdown("<br>", unsafe_allow_html=True)
            long_running = st.checkbox("♾️ Long-Running Harness (Unlimited)", value=False)
        
        if st.button("🚀 Launch Autonomous Loop", type="primary"):
            status_box = st.empty()
            with st.spinner("Initializing Phase 1..."):
                messages, blueprint = init_omni_loop(st.session_state.omni_intent_val, meditate_model, coder_model, workspace_dir, status_container=status_box)
                st.session_state.omni_messages = messages
                st.session_state.omni_bp = blueprint
                st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)
                st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)
                st.session_state.intent_prompt = st.session_state.omni_intent_val
                st.session_state.phase = 1
                st.session_state.phase_summaries = []
                if long_running:
                    st.session_state.max_steps = 999  # effectively unlimited
                    st.session_state.hitl_enabled = False
                else:
                    st.session_state.max_steps = max_steps
                st.session_state.omni_state = "GENERATING"
                st.rerun()"""

new_controls = """        agent_mode = st.radio("🤖 Select Agent Mode:", [
            "💬 Chat / Q&A (Analyze code and answer questions)",
            "🛡️ Step-by-Step (Execute tasks with my explicit approval)",
            "♾️ Fully Autonomous (Run continuously until goal is met)"
        ], index=1)
        
        col_b1, col_b2 = st.columns([1, 4])
        with col_b1:
            if st.button("🚀 Launch Agent", type="primary"):
                status_box = st.empty()
                with st.spinner("Initializing Phase 1..."):
                    messages, blueprint = init_omni_loop(st.session_state.omni_intent_val, meditate_model, coder_model, workspace_dir, status_container=status_box)
                    st.session_state.omni_messages = messages
                    st.session_state.omni_bp = blueprint
                    st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)
                    st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)
                    st.session_state.intent_prompt = st.session_state.omni_intent_val
                    st.session_state.phase = 1
                    st.session_state.phase_summaries = []
                    
                    if "Chat" in agent_mode:
                        st.session_state.max_steps = 3
                        st.session_state.hitl_enabled = True
                    elif "Step-by-Step" in agent_mode:
                        st.session_state.max_steps = 20
                        st.session_state.hitl_enabled = True
                    elif "Fully Autonomous" in agent_mode:
                        st.session_state.max_steps = 999
                        st.session_state.hitl_enabled = False
                        
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()"""

content = content.replace(old_controls, new_controls)

old_done = """        elif st.session_state.omni_state == "DONE":
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
                st.toast("Feedback injected into Agent's memory!")"""

new_done = """        elif st.session_state.omni_state == "DONE":
            st.success("🎉 Agent is standing by.")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("Start Completely New Task"):
                    if st.session_state.terminal: st.session_state.terminal.cleanup()
                    st.session_state.omni_state = "IDLE"
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
                st.toast("Feedback injected into Agent's memory!")"""

content = content.replace(old_done, new_done)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Modes patched.")
