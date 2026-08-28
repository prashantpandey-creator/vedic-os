import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Update the tabs definition
old_tabs = """tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Stage 1: Bare Model", 
    "🏗️ Stage 2: Sandbox Architect", 
    "🧬 Stage 3: Nidra Harness", 
    "🦅 Stage 4: Omni-Agent"
])"""

new_tabs = """tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Stage 1: Bare Model", 
    "🏗️ Stage 2: Sandbox Architect", 
    "🧬 Stage 3: Nidra Harness", 
    "🦅 Stage 4: Omni-Agent",
    "🧠 Model Manager"
])"""
content = content.replace(old_tabs, new_tabs)

# 2. Append tab5 at the end
# We need to make sure we don't accidentally break indentation, since it's at the root level.
tab5_code = """

with tab5:
    st.header("🧠 Local Model Manager")
    st.markdown("Pull, delete, and manage your local Ollama models directly from this UI.")
    
    from core.ollama_api import pull_model, delete_model, evict_all_models
    
    col_m1, col_m2 = st.columns([2, 1])
    
    with col_m1:
        st.subheader("📥 Download New Model")
        new_model_name = st.text_input("Enter Ollama model name (e.g. `llama3.1:8b`, `qwen2.5:32b`)")
        if st.button("Pull Model", type="primary"):
            if new_model_name:
                pull_box = st.empty()
                pull_box.info(f"Downloading `{new_model_name}`... This may take a while.")
                res = pull_model(new_model_name)
                if res and res.status_code == 200:
                    import json
                    for line in res.iter_lines():
                        if line:
                            data = json.loads(line)
                            status = data.get("status", "")
                            if "total" in data and "completed" in data:
                                pct = (data["completed"] / data["total"]) * 100
                                pull_box.info(f"Downloading `{new_model_name}`: {pct:.1f}% - {status}")
                            else:
                                pull_box.info(f"Downloading `{new_model_name}`: {status}")
                    pull_box.success(f"Successfully pulled `{new_model_name}`!")
                    time.sleep(1)
                    st.rerun()
                else:
                    pull_box.error(f"Failed to pull `{new_model_name}`. Check your internet or Ollama connection.")
            else:
                st.warning("Please enter a model name.")
                
        st.markdown("---")
        st.subheader("🧹 VRAM Management")
        if st.button("Unload All Models from VRAM (Free Memory)"):
            evict_all_models()
            st.success("All models evicted from VRAM.")
            time.sleep(1)
            st.rerun()

    with col_m2:
        st.subheader("📦 Installed Models")
        for m in models:
            details = get_model_details(m)
            if details:
                size_gb = details.get("size", 0) / (1024**3)
                param_size = details.get("details", {}).get("parameter_size", "Unknown")
                quant = details.get("details", {}).get("quantization_level", "Unknown")
                
                with st.expander(f"🤖 {m} ({size_gb:.1f} GB)"):
                    st.write(f"**Parameters:** {param_size}")
                    st.write(f"**Quantization:** {quant}")
                    if st.button(f"🗑️ Delete {m}", key=f"del_{m}"):
                        if delete_model(m):
                            st.success(f"Deleted {m}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to delete {m}")
"""

content += tab5_code

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Model Manager tab added.")
