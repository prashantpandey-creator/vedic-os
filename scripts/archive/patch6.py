import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Update Nidra Mode Defaults
old_nidra_coder = """        cod_idx = models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0
        coder_model = st.selectbox("🧠 Genius Coder Layer (Generator)", models, index=cod_idx)"""
new_nidra_coder = """        target = "mannix/llama3.1-8b-abliterated:latest"
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0)
        coder_model = st.selectbox("🧠 Coder Layer (Fast Abliterated)", models, index=cod_idx)"""
content = content.replace(old_nidra_coder, new_nidra_coder)

# Update Omni-Agent Mode Defaults
old_omni_coder = """        cod_idx = models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0
        coder_model = st.selectbox("🦅 Omni-Agent Engine (Qwen)", models, index=cod_idx)"""
new_omni_coder = """        target = "mannix/llama3.1-8b-abliterated:latest"
        cod_idx = models.index(target) if target in models else (models.index("qwen2.5:32b") if "qwen2.5:32b" in models else 0)
        coder_model = st.selectbox("🦅 Omni-Agent Typist (Llama-3 Abliterated)", models, index=cod_idx)"""
content = content.replace(old_omni_coder, new_omni_coder)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Default models updated to Abliterated Llama 3.1 8B.")
