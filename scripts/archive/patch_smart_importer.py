import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

old_importer = """                        try:
                            with open(transcript_path, 'r') as tf:
                                lines = tf.readlines()[-20:] # Read last 20 steps
                                for line in lines:
                                    step = json.loads(line)
                                    if step.get("type") in ["USER_INPUT", "PLANNER_RESPONSE"]:
                                        summary += f"- {step.get('type')}: {str(step.get('content'))[:200]}...\\n"
                        except Exception as e:
                            summary += f"Error parsing: {e}"
                        from core.memory_graph import append_vritti
                        append_vritti("Imported Antigravity Context", "Antigravity", summary, workspace_dir)
                        st.success(f"Ingested Antigravity session into Local Agent Memory!")"""

new_importer = """                        try:
                            with open(transcript_path, 'r') as tf:
                                # We can read the whole thing, but let's safely take the last 1000 lines 
                                # to fit in Mamba's 32k window
                                raw_lines = tf.readlines()[-1000:]
                                raw_transcript = "".join(raw_lines)
                                
                            with st.spinner("🧠 Local LLM is synthesizing Antigravity context..."):
                                import requests
                                from config import OLLAMA_URL, INGEST_MODEL
                                
                                payload = {
                                    "model": INGEST_MODEL,
                                    "messages": [
                                        {"role": "system", "content": "You are a Memory Synthesizer. Read this JSONL transcript from an advanced AI session. Extract all core architectural decisions, user instructions, and technical context into a clean, concise Markdown summary. Do not output JSON."},
                                        {"role": "user", "content": raw_transcript[-80000:]} # safe cap
                                    ],
                                    "stream": False,
                                    "options": {"num_ctx": 32000, "temperature": 0.1}
                                }
                                
                                res = requests.post(f"{OLLAMA_URL}/api/chat", json=payload).json()
                                intelligent_summary = res.get("message", {}).get("content", "Failed to summarize.")
                                
                                from core.ollama_api import evict_model
                                evict_model(INGEST_MODEL)
                                
                                from core.memory_graph import append_vritti
                                append_vritti(f"Imported Antigravity Context: {selected_ag}", "Antigravity", intelligent_summary, workspace_dir)
                                st.success("✨ Local LLM successfully synthesized and ingested the external session!")
                                
                        except Exception as e:
                            st.error(f"Error during intelligent extraction: {e}")"""
                            
content = content.replace(old_importer, new_importer)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Smart Importer UI patched.")
