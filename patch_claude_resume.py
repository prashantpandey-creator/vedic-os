import sys
import os

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

old_claude = """        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Claude Code Memory**")
            claude_dir = CLAUDE_MEMORY_DIR
            claude_memories = []
            if os.path.exists(claude_dir):
                claude_memories = [f for f in os.listdir(claude_dir) if f.endswith('.md')]
            
            if claude_memories:
                selected_claude = st.selectbox("Select Claude Memory:", ["(None)"] + claude_memories)
                if selected_claude != "(None)" and st.button("📥 Ingest Claude Context"):
                    with open(os.path.join(claude_dir, selected_claude), 'r') as mf:
                        raw_context = mf.read()
                        
                    st.info("🧠 Model pre-filling Claude context...")
                    synthesized_box = st.empty()
                    intelligent_summary = ""
                    
                    import requests
                    from config import OLLAMA_URL, INGEST_MODEL
                    
                    payload = {
                        "model": INGEST_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a Memory Synthesizer. Read this memory file from Claude Code. Extract the core architectural rules, findings, and context into a highly dense Markdown summary."},
                            {"role": "user", "content": raw_context[-12000:]}
                        ],
                        "stream": True,
                        "options": {"num_ctx": 4096, "temperature": 0.1}
                    }
                    
                    try:
                        res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True)
                        for line in res.iter_lines():
                            if line:
                                chunk = json.loads(line)
                                if "message" in chunk and "content" in chunk["message"]:
                                    intelligent_summary += chunk["message"]["content"]
                                    synthesized_box.markdown(f"**Synthesizing:**\\n{intelligent_summary}▌")
                                    
                        synthesized_box.markdown(f"**Synthesis Complete:**\\n{intelligent_summary}")
                        
                        from core.ollama_api import evict_model
                        evict_model(INGEST_MODEL)
                        
                        from core.memory_graph import append_vritti
                        append_vritti(f"Imported Claude Context: {selected_claude}", "Claude-Code", intelligent_summary, workspace_dir)
                        st.success(f"✨ Synthesized and ingested {selected_claude} into Memory!")
                    except Exception as e:
                        st.error(f"Error streaming Claude synthesis: {e}")
            else:
                st.info("No Claude memory found in ~/claude-sync/memory/")"""

new_claude = """        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Claude Code Memory**")
            claude_dir = CLAUDE_MEMORY_DIR
            claude_projects = []
            if os.path.exists(claude_dir):
                claude_projects = [d for d in os.listdir(claude_dir) if os.path.isdir(os.path.join(claude_dir, d)) and d.startswith("-")]
            
            if claude_projects:
                selected_claude = st.selectbox("Select Claude Project:", ["(None)"] + claude_projects)
                if selected_claude != "(None)" and st.button("📥 Ingest Claude Context"):
                    # Find MEMORY.md or first .md file
                    target_dir = os.path.join(claude_dir, selected_claude)
                    md_files = [f for f in os.listdir(target_dir) if f.endswith('.md')]
                    
                    if not md_files:
                        st.error("No .md files found in this Claude project directory.")
                    else:
                        mem_file = "MEMORY.md" if "MEMORY.md" in md_files else md_files[0]
                        with open(os.path.join(target_dir, mem_file), 'r') as mf:
                            raw_context = mf.read()
                            
                        st.info("🧠 Model pre-filling Claude context...")
                        synthesized_box = st.empty()
                        intelligent_summary = ""
                        
                        import requests
                        from config import OLLAMA_URL, INGEST_MODEL
                        
                        payload = {
                            "model": INGEST_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a Memory Synthesizer. Read this memory file from Claude Code. Extract the core architectural rules, findings, and context into a highly dense Markdown summary."},
                                {"role": "user", "content": raw_context[-12000:]}
                            ],
                            "stream": True,
                            "options": {"num_ctx": 4096, "temperature": 0.1}
                        }
                        
                        try:
                            res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True)
                            for line in res.iter_lines():
                                if line:
                                    chunk = json.loads(line)
                                    if "message" in chunk and "content" in chunk["message"]:
                                        intelligent_summary += chunk["message"]["content"]
                                        synthesized_box.markdown(f"**Synthesizing:**\\n{intelligent_summary}▌")
                                        
                            synthesized_box.markdown(f"**Synthesis Complete:**\\n{intelligent_summary}")
                            
                            from core.ollama_api import evict_model
                            evict_model(INGEST_MODEL)
                            
                            from core.memory_graph import append_vritti
                            append_vritti(f"Imported Claude Context: {selected_claude}", "Claude-Code", intelligent_summary, workspace_dir)
                            st.success(f"✨ Synthesized and ingested {selected_claude} into Memory!")
                            
                            # Auto-detect Workspace Directory from Claude slug
                            # Convert e.g. -Users-badenath-projects-vedic-puran to /Users/badenath/projects/vedic puran
                            parts = selected_claude.strip("-").split("-")
                            detected_cwd = None
                            if len(parts) >= 2:
                                # Try a few combinations of spaces vs hyphens in the last folder
                                base_path = "/" + "/".join(parts[:-1])
                                last_part = parts[-1]
                                
                                # 1. Literal translation
                                p1 = os.path.join(base_path, last_part)
                                # 2. Space instead of hyphen (common for claude slug)
                                p2 = os.path.join("/" + "/".join(parts[:-2]), parts[-2] + " " + parts[-1]) if len(parts) >= 3 else p1
                                
                                if os.path.exists(p2): detected_cwd = p2
                                elif os.path.exists(p1): detected_cwd = p1
                                
                            if detected_cwd:
                                st.info(f"📂 Detected active project directory: `{detected_cwd}`")
                                if st.button(f"🚀 Switch to this Project & Resume", key="claude_resume"):
                                    st.session_state["workspace_dir"] = detected_cwd
                                    st.session_state.intent_prompt = f"Resume session from Claude project '{selected_claude}' based on ingested MEMORY."
                                    st.rerun()
                            else:
                                st.warning(f"Could not automatically locate the workspace directory on disk. You may need to set it manually.")
                                
                        except Exception as e:
                            st.error(f"Error streaming Claude synthesis: {e}")
            else:
                st.info("No Claude projects found in ~/claude-sync/memory/")"""

content = content.replace(old_claude, new_claude)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Claude resume patched.")
