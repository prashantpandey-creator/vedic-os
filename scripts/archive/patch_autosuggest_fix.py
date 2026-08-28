import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Replace the previous bad implementation
old_block = """        if "suggested_intent" not in st.session_state:
            st.session_state.suggested_intent = "Run 'npm test', find the failing tests, and fix the codebase."
            
        col_t1, col_t2 = st.columns([5, 1])
        with col_t1:
            intent_prompt = st.text_area("What do you want the Omni-Agent to do?", value=st.session_state.suggested_intent, height=100)
        with col_t2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💡 Auto-Suggest"):
                with st.spinner("Analyzing repo..."):
                    context_data = ""
                    for fname in ["README.md", "PROJECT_MIND.md"]:
                        fpath = os.path.join(workspace_dir, fname)
                        if os.path.exists(fpath):
                            with open(fpath, "r") as mf:
                                context_data += f"\\n--- {fname} ---\\n" + mf.read()[:5000]
                    
                    if not context_data.strip():
                        # Fallback to reading first 5 files
                        try:
                            files = [f for f in os.listdir(workspace_dir) if os.path.isfile(os.path.join(workspace_dir, f)) and not f.startswith(".")]
                            for f in files[:5]:
                                with open(os.path.join(workspace_dir, f), "r", errors="ignore") as mf:
                                    context_data += f"\\n--- {f} ---\\n" + mf.read()[:1000]
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
                        "options": {"num_ctx": 4096, "temperature": 0.7}
                    }
                    try:
                        res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload).json()
                        suggestion = res.get("message", {}).get("content", "").strip()
                        if suggestion:
                            st.session_state.suggested_intent = suggestion
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to auto-suggest: {e}")"""

new_block = """        if "omni_intent_val" not in st.session_state:
            st.session_state.omni_intent_val = "Run 'npm test', find the failing tests, and fix the codebase."
            
        col_t1, col_t2 = st.columns([5, 1])
        with col_t1:
            intent_prompt = st.text_area("What do you want the Omni-Agent to do?", key="omni_intent_val", height=100)
        with col_t2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💡 Auto-Suggest"):
                with st.spinner("Analyzing repo..."):
                    context_data = ""
                    for fname in ["README.md", "PROJECT_MIND.md", "package.json"]:
                        fpath = os.path.join(workspace_dir, fname)
                        if os.path.exists(fpath):
                            with open(fpath, "r", errors="ignore") as mf:
                                context_data += f"\\n--- {fname} ---\\n" + mf.read()[:5000]
                    
                    if not context_data.strip():
                        try:
                            files = [f for f in os.listdir(workspace_dir) if os.path.isfile(os.path.join(workspace_dir, f)) and not f.startswith(".")]
                            for f in files[:5]:
                                with open(os.path.join(workspace_dir, f), "r", errors="ignore") as mf:
                                    context_data += f"\\n--- {f} ---\\n" + mf.read()[:1000]
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
                        st.error(f"Failed to auto-suggest: {e}")"""
content = content.replace(old_block, new_block)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Auto-suggest bound to key.")
