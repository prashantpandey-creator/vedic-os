import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

old_claude = """                    with st.spinner("🧠 Local LLM is synthesizing Claude's memory..."):
                        import requests
                        from config import OLLAMA_URL, INGEST_MODEL
                        
                        payload = {
                            "model": INGEST_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a Memory Synthesizer. Read this memory file from Claude Code. Extract the core architectural rules, findings, and context into a highly dense Markdown summary."},
                                {"role": "user", "content": raw_context[-80000:]}
                            ],
                            "stream": False,
                            "options": {"num_ctx": 32000, "temperature": 0.1}
                        }
                        
                        res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload).json()
                        intelligent_summary = res.get("message", {}).get("content", "Failed to summarize.")
                        
                        from core.ollama_api import evict_model
                        evict_model(INGEST_MODEL)
                        
                        from core.memory_graph import append_vritti
                        append_vritti(f"Imported Claude Context: {selected_claude}", "Claude-Code", intelligent_summary, workspace_dir)
                        st.success(f"✨ Synthesized and ingested {selected_claude} into Memory!")"""

new_claude = """                    st.info("🧠 Model pre-filling Claude context...")
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
                        st.error(f"Error streaming Claude synthesis: {e}")"""
                        
content = content.replace(old_claude, new_claude)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Claude importer sped up.")
