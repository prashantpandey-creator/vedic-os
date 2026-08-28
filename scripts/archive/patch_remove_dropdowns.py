import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Tab 3 Replacement
old_tab3 = """    col1, col2 = st.columns(2)
    with col1:
        med_idx = models.index(INGEST_MODEL) if INGEST_MODEL in models else 0
        meditate_model = st.selectbox("🧘 Meditate Layer (Scanner)", models, index=med_idx)
    with col2:
        target = FAST_MODEL
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if HEAVY_MODEL in models else 0)
        coder_model = st.selectbox("🧠 Coder Layer (Fast Abliterated)", models, index=cod_idx)"""

new_tab3 = """    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🧘 **Meditate Layer (Scanner):** `{INGEST_MODEL}`")
        meditate_model = INGEST_MODEL
    with col2:
        st.info(f"🧠 **Coder Layer (Abliterated):** `{FAST_MODEL}`")
        coder_model = FAST_MODEL"""
content = content.replace(old_tab3, new_tab3)

# Tab 4 Replacement
old_tab4 = """    col1, col2 = st.columns(2)
    with col1:
        med_idx = models.index(INGEST_MODEL) if INGEST_MODEL in models else 0
        meditate_model = st.selectbox("🐍 SSM Ingestion Engine (Mamba)", models, index=med_idx)
    with col2:
        target = FAST_MODEL
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if HEAVY_MODEL in models else 0)
        coder_model = st.selectbox("🦅 Omni-Agent Typist (Llama-3 Abliterated)", models, index=cod_idx)"""

new_tab4 = """    col1, col2 = st.columns(2)
    with col1:
        st.info(f"🐍 **SSM Ingestion Engine:** `{INGEST_MODEL}`")
        meditate_model = INGEST_MODEL
    with col2:
        st.info(f"🦅 **Omni-Agent Typist:** `{FAST_MODEL}`")
        coder_model = FAST_MODEL"""
content = content.replace(old_tab4, new_tab4)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Removed model dropdowns.")
