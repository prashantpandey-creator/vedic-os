import os

with open("app.py", "r") as f:
    content = f.read()

target = """tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Stage 1: Bare Model", 
    "🏗️ Stage 2: Sandbox Architect", 
    "🧬 Stage 3: Nidra Harness", 
    "🦅 Stage 4: Omni-Agent",
    "🧠 Model Manager"
])"""

replacement = """tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 Stage 1: Bare Model", 
    "🏗️ Stage 2: Sandbox Architect", 
    "🧬 Stage 3: Nidra Harness", 
    "🦅 Stage 4: Omni-Agent",
    "🧠 Model Manager",
    "💻 Live Terminal"
])"""

content = content.replace(target, replacement)

target2 = """with tab5:
    render_model_manager()"""

replacement2 = """with tab5:
    render_model_manager()

with tab6:
    st.markdown("### 💻 Live Background Terminal")
    st.markdown("Watch the agent execute commands in real-time.")
    import time
    log_path = os.path.join(os.getenv("VEDIC_WORKSPACES", os.getcwd()), "terminal.log")
    if os.path.exists(log_path):
        st.code(open(log_path).read(), language="bash")
    else:
        st.info("No terminal commands have been executed yet in this workspace.")"""

content = content.replace(target2, replacement2)

with open("app.py", "w") as f:
    f.write(content)
