import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

old_ag_logic = """                        try:
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

new_ag_logic = """                        try:
                            # PRE-FILTER: Don't send massive tool outputs to the LLM.
                            # Only send the Agent's thoughts and the User's intents.
                            filtered_transcript = ""
                            with open(transcript_path, 'r') as tf:
                                lines = tf.readlines()[-100:] # Just last 100 steps
                                for line in lines:
                                    try:
                                        step = json.loads(line)
                                        t = step.get("type", "")
                                        if t in ["USER_INPUT", "PLANNER_RESPONSE", "SYSTEM_MESSAGE"]:
                                            content = str(step.get("content", ""))
                                            # Truncate massive file reads from planner responses
                                            if len(content) > 1000: content = content[:1000] + "...[truncated]"
                                            filtered_transcript += f"\\n[{t}]: {content}"
                                    except: pass
                                
                            st.info("🧠 Model pre-filling context...")
                            synthesized_box = st.empty()
                            intelligent_summary = ""
                            
                            import requests
                            from config import OLLAMA_URL, INGEST_MODEL
                            
                            payload = {
                                "model": INGEST_MODEL,
                                "messages": [
                                    {"role": "system", "content": "You are a Memory Synthesizer. Read this filtered transcript from an AI session. Extract the core architectural decisions and user intents into a concise Markdown summary."},
                                    {"role": "user", "content": filtered_transcript}
                                ],
                                "stream": True,
                                "options": {"num_ctx": 4096, "temperature": 0.1} # Much smaller context window
                            }
                            
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
                            append_vritti(f"Imported Antigravity Context: {selected_ag}", "Antigravity", intelligent_summary, workspace_dir)
                            st.success("✨ Successfully ingested into Local Memory!")
                            
                        except Exception as e:
                            st.error(f"Error during intelligent extraction: {e}")"""
                            
content = content.replace(old_ag_logic, new_ag_logic)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Antigravity importer sped up.")
