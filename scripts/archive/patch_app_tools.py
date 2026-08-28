import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Imports
content = content.replace("from core.terminal_engine import TerminalEngine", "from core.terminal_engine import TerminalEngine\n    from core.tool_registry import ToolRegistry")

# 2. Add registry to state
content = content.replace("st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)", "st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)\n                st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)")

# 3. Handle historical rendering of artifacts and subagents
old_hist = """                elif log.get('type') == 'loop_intercept':
                    st.error(log['output'])"""

new_hist = """                elif log.get('type') == 'loop_intercept':
                    st.error(log['output'])
                elif log.get('type') == 'artifact':
                    st.success(f"📄 Generated Artifact: `{log['title']}`")
                    with open(log['path'], 'r') as art_f:
                        st.markdown(art_f.read())
                elif log.get('type') == 'subagent':
                    st.info(f"🤖 Subagent ({log['role']}) Task: {log['task']}")
                    for entry in log['log']:
                        st.code(entry, language="bash")
                    st.success(f"Result: {log['msg']}")"""
content = content.replace(old_hist, new_hist)

# 4. Refactor Action Execution
# Find the big if/elif block starting at `elif action == "edit_file":`
old_exec_block = """            elif action == "edit_file":
                filepath = action_data.get("file")
                search = action_data.get("search", "")
                replace = action_data.get("replace", "")
                
                try:
                    diff_str = apply_search_replace(filepath, search, replace, workspace_dir=workspace_dir)
                    st.session_state.omni_log.append({"step": st.session_state.omni_step, "type": "edit", "file": filepath, "raw": raw_response, "diff": diff_str})
                    st.session_state.omni_messages.append({"role": "user", "content": f"File {filepath} edited successfully."})
                except Exception as e:
                    st.session_state.omni_messages.append({"role": "user", "content": f"Edit failed: {e}\\nPlease fix your search block and try again."})
                    
                st.session_state.omni_step += 1
                st.rerun()
                
            elif action == "run_command":
                if st.session_state.hitl_enabled:
                    cmd = action_data.get("command", "")
                    st.session_state.omni_log.append({
                        "step": st.session_state.omni_step, 
                        "type": "pending_command", 
                        "cmd": cmd, 
                        "raw": raw_response
                    })
                    st.session_state.omni_step += 1
                    st.session_state.omni_state = "AWAITING_APPROVAL"
                    st.rerun()
                else:
                    cmd = action_data.get("command", "echo 'No command'")
                    output = st.session_state.terminal.execute(cmd)
                    st.session_state.omni_log.append({"step": st.session_state.omni_step, "type": "command", "cmd": cmd, "raw": raw_response, "output": output})
                    st.session_state.omni_messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```"})
                    st.session_state.omni_step += 1
                    st.rerun()"""

new_exec_block = """            elif action == "run_command" and st.session_state.hitl_enabled:
                cmd = action_data.get("command", "")
                st.session_state.omni_log.append({
                    "step": st.session_state.omni_step, 
                    "type": "pending_command", 
                    "cmd": cmd, 
                    "raw": raw_response
                })
                st.session_state.omni_step += 1
                st.session_state.omni_state = "AWAITING_APPROVAL"
                st.rerun()
            else:
                # Dynamic Tool Registry Execution
                result_obj = st.session_state.registry.execute_tool(action_data, fast_model=coder_model)
                
                log_entry = {"step": st.session_state.omni_step, "raw": raw_response}
                log_entry.update(result_obj)
                st.session_state.omni_log.append(log_entry)
                
                st.session_state.omni_messages.append({"role": "user", "content": result_obj.get("msg", "")})
                st.session_state.omni_step += 1
                st.rerun()"""
content = content.replace(old_exec_block, new_exec_block)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("app.py UI patched for dynamic tools.")
