import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Update Mode Selector
old_radio = """app_mode = st.sidebar.radio("Select Framework Pillar:", [
    "💬 Standard Chat (Hybrid Non-Transformers)",
    "🏗️ Code Compiler Manifestor (Vyasa Sandbox)",
    "🧬 Coding Agent with Harness (Nidra)"
])"""
new_radio = """app_mode = st.sidebar.radio("Select Framework Pillar:", [
    "💬 Standard Chat (Hybrid Non-Transformers)",
    "🏗️ Code Compiler Manifestor (Vyasa Sandbox)",
    "🧬 Coding Agent with Harness (Nidra)",
    "🦅 Omni-Agent (Autonomous Terminal Loop)"
])"""
content = content.replace(old_radio, new_radio)

# 2. Add Omni-Agent logic
omni_logic = """elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":
    st.markdown("This is the **Next-Gen Agentic Loop**. Mamba-2 ingests the entire Git repository to build an architectural blueprint. Qwen takes control of your Mac's Zsh terminal, looping autonomously to edit files, run scripts, read stdout errors, and fix bugs until the task is complete.")
    
    from agents.omni_agent import run_omni_loop
    
    col1, col2 = st.columns(2)
    with col1:
        med_idx = models.index("granite4:3b-h") if "granite4:3b-h" in models else 0
        meditate_model = st.selectbox("🐍 SSM Ingestion Engine (Mamba)", models, index=med_idx)
    with col2:
        cod_idx = models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0
        coder_model = st.selectbox("🦅 Omni-Agent Engine (Qwen)", models, index=cod_idx)

    intent_prompt = st.text_area("What do you want the Omni-Agent to do?", "Run 'npm test', find the failing tests, and fix the codebase.")
    
    if st.button("🚀 Launch Autonomous Loop", type="primary"):
        status = st.empty()
        stream_placeholder = st.empty()
        
        try:
            exec_log, blueprint = run_omni_loop(intent_prompt, meditate_model, coder_model, status, stream_placeholder)
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
    st.markdown("Describe an app below. The **Architect** will design it, and the **Coder** will manifest it into the sandbox.")"""

# Replace the 'else' (which was architect) to add the elif block before it
old_else = "else:\n    st.markdown(\"Describe an app below. The **Architect** will design it, and the **Coder** will manifest it into the sandbox.\")"
content = content.replace(old_else, omni_logic)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("app.py patched with Omni-Agent.")
