import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Replace the Antigravity importer logic
old_ag_logic = """                            from core.memory_graph import append_vritti
                            append_vritti(f"Imported Antigravity Context: {selected_ag}", "Antigravity", intelligent_summary, workspace_dir)
                            st.success("✨ Successfully ingested into Local Memory!")
                            
                        except Exception as e:"""

new_ag_logic = """                            from core.memory_graph import append_vritti
                            append_vritti(f"Imported Antigravity Context: {selected_ag}", "Antigravity", intelligent_summary, workspace_dir)
                            st.success("✨ Successfully ingested into Local Memory!")
                            
                            # Auto-detect Workspace Directory from tool calls
                            detected_cwd = None
                            try:
                                with open(transcript_path, 'r') as tf:
                                    cwds = {}
                                    for line in tf:
                                        if '"Cwd"' in line:
                                            try:
                                                step = json.loads(line)
                                                for call in step.get("tool_calls", []):
                                                    cwd = call.get("args", {}).get("Cwd")
                                                    if cwd and cwd != "/Users/badenath":
                                                        cwds[cwd] = cwds.get(cwd, 0) + 1
                                            except: pass
                                    if cwds:
                                        detected_cwd = max(cwds, key=cwds.get)
                            except: pass
                            
                            if detected_cwd and os.path.exists(detected_cwd):
                                st.info(f"📂 Detected active project directory: `{detected_cwd}`")
                                if st.button(f"🚀 Switch to this Project & Resume"):
                                    st.session_state["workspace_dir"] = detected_cwd
                                    st.session_state.intent_prompt = f"Resume session '{selected_ag}' based on the ingested PROJECT_MIND memory."
                                    st.rerun()
                                    
                        except Exception as e:"""

content = content.replace(old_ag_logic, new_ag_logic)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Antigravity resume patched.")
