import os

with open("app.py", "r") as f:
    content = f.read()

target = """st.sidebar.markdown("---")
details = get_model_details(selected_model)"""

replacement = """st.sidebar.markdown("---")

st.sidebar.markdown("### ⏪ Time Travel")
if st.sidebar.button("Undo Last Agent Action", help="Instantly git reset the repository if the agent hallucinated."):
    import subprocess
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=os.getenv("VEDIC_WORKSPACES", os.getcwd()))
    subprocess.run(["git", "clean", "-fd"], cwd=os.getenv("VEDIC_WORKSPACES", os.getcwd()))
    st.sidebar.success("Repo successfully restored to previous state!")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Context Uploader")
uploaded_files = st.sidebar.file_uploader("Drop PDFs, docs, or logs here", accept_multiple_files=True)
if uploaded_files:
    context_text = "\\n".join([f.read().decode('utf-8', errors='ignore') for f in uploaded_files])
    system_prompt += f"\\n\\n[USER PROVIDED CONTEXT FILES]:\\n{context_text}"
    st.sidebar.success(f"Injected {len(uploaded_files)} files into agent memory!")

st.sidebar.markdown("---")
details = get_model_details(selected_model)"""

content = content.replace(target, replacement)

with open("app.py", "w") as f:
    f.write(content)
