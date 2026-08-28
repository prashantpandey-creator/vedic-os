import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# First occurrence is the initial launch
old_launch = """        if st.button("🚀 Launch Autonomous Loop", type="primary"):
            with st.spinner("🐍 Mamba is ingesting codebase and generating blueprint..."):
                messages, blueprint = init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir)"""

new_launch = """        if st.button("🚀 Launch Autonomous Loop", type="primary"):
            status_box = st.empty()
            with st.spinner("Initializing Phase 1..."):
                messages, blueprint = init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)"""
content = content.replace(old_launch, new_launch)

# Second occurrence is the phase transition
old_phase = """                    # Re-ingest codebase with fresh eyes (files may have changed!)
                    with st.spinner("♻️ Phase {} complete. Re-ingesting codebase for Phase {}...".format(current_phase, current_phase + 1)):
                        messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir)"""

new_phase = """                    # Re-ingest codebase with fresh eyes (files may have changed!)
                    st.info("♻️ Phase {} complete. Re-ingesting codebase for Phase {}...".format(current_phase, current_phase + 1))
                    status_box = st.empty()
                    messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)"""
content = content.replace(old_phase, new_phase)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
