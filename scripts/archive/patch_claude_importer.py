import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

old_claude = """                if selected_claude != "(None)" and st.button("📥 Ingest Claude Context"):
                    with open(os.path.join(claude_dir, selected_claude), 'r') as mf:
                        context = mf.read()
                    from core.memory_graph import append_vritti
                    append_vritti("Imported Claude Context", "Claude-Code", context, workspace_dir)
                    st.success(f"Ingested {selected_claude} into Local Agent Memory!")"""

new_claude = """                if selected_claude != "(None)" and st.button("📥 Ingest Claude Context"):
                    with open(os.path.join(claude_dir, selected_claude), 'r') as mf:
                        raw_context = mf.read()
                        
                    with st.spinner("🧠 Local LLM is synthesizing Claude's memory..."):
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
                        
content = content.replace(old_claude, new_claude)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Claude Importer UI patched.")
