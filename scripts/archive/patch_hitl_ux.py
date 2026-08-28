import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Fix 1: Loop Detection missing from log
old_loop = """            if current_action_str in st.session_state.action_history[-3:]:
                st.session_state.omni_messages.append({"role": "user", "content": "🚨 SYSTEM OVERRIDE: You just attempted the exact same action you already tried. You MUST try a completely different approach or declare 'done'."})
                st.session_state.action_history.append("FORCED_PIVOT")
                st.warning("⚠️ Loop detected. Forcing agent to pivot.")
                st.session_state.omni_step += 1
                st.button("Continue to next step")
                st.stop()"""

new_loop = """            if current_action_str in st.session_state.action_history[-3:]:
                st.session_state.omni_messages.append({"role": "user", "content": "🚨 SYSTEM OVERRIDE: You just attempted the exact same action you already tried. You MUST try a completely different approach or declare 'done'."})
                st.session_state.action_history.append("FORCED_PIVOT")
                
                # Save to log so UI doesn't lose it
                st.session_state.omni_log.append({
                    "step": st.session_state.omni_step,
                    "type": "loop_intercept",
                    "raw": raw_response,
                    "output": "🚨 CRITICAL LOOP DETECTED. The engine intercepted the duplicate action and forced a pivot."
                })
                
                st.warning("⚠️ Loop detected. Forcing agent to pivot.")
                st.session_state.omni_step += 1
                st.button("Continue to next step")
                st.stop()"""
content = content.replace(old_loop, new_loop)


# Fix 2: Render HitL properly
# In the historical log render loop, handle 'pending_command' and 'loop_intercept'
old_historical = """        for log in st.session_state.omni_log:
            with st.expander(f"🦅 Step {log['step']}: {log.get('type', 'Action')}", expanded=False):
                if 'raw' in log: st.code(log['raw'], language="json")
                if log.get('type') == 'command':
                    st.markdown(f"**💻 Terminal Output (Command: `{log['cmd']}`)**")
                    st.code(log['output'], language="bash")
                elif log.get('type') == 'edit':
                    st.success(f"📝 Edited `{log['file']}`")
                    if 'diff' in log: st.code(log['diff'], language="diff")"""

new_historical = """        for log in st.session_state.omni_log:
            with st.expander(f"🦅 Step {log['step']}: {log.get('type', 'Action').upper()}", expanded=(log['step'] == st.session_state.omni_step - 1)):
                if 'raw' in log: st.code(log['raw'], language="json")
                
                if log.get('type') == 'command':
                    st.markdown(f"**💻 Terminal Output (Command: `{log['cmd']}`)**")
                    st.code(log['output'], language="bash")
                elif log.get('type') == 'pending_command':
                    st.warning(f"**⏳ Awaiting Approval for Command: `{log['cmd']}`**")
                elif log.get('type') == 'edit':
                    st.success(f"📝 Edited `{log['file']}`")
                    if 'diff' in log: st.code(log['diff'], language="diff")
                elif log.get('type') == 'loop_intercept':
                    st.error(log['output'])"""
content = content.replace(old_historical, new_historical)

# Fix 3: Save pending command to log BEFORE rerun
old_hitl_save = """            elif action == "run_command":
                if st.session_state.hitl_enabled:
                    st.session_state.omni_state = "AWAITING_APPROVAL"
                    st.rerun()"""

new_hitl_save = """            elif action == "run_command":
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
                    st.rerun()"""
content = content.replace(old_hitl_save, new_hitl_save)


# Fix 4: Awaiting Approval execution updates the existing log instead of making a new one
old_hitl_exec = """        elif st.session_state.omni_state == "AWAITING_APPROVAL":
            cmd = st.session_state.current_action.get("command")
            st.warning(f"🚨 **Human-in-the-Loop Approval Required**")
            st.code(f"$ {cmd}", language="bash")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Approve & Execute", type="primary"):
                    output = st.session_state.terminal.execute(cmd)
                    st.session_state.omni_log.append({"step": st.session_state.omni_step, "type": "command", "cmd": cmd, "raw": st.session_state.current_raw, "output": output})
                    st.session_state.omni_messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```"})
                    st.session_state.omni_step += 1
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()
            with col_b:
                steer_input = st.text_input("Reject & Steer Agent:", placeholder="No, run 'npm install' instead.")
                if st.button("🚫 Reject"):
                    st.session_state.omni_messages.append({"role": "user", "content": f"USER REJECTED COMMAND. Feedback: {steer_input}"})
                    st.session_state.omni_step += 1
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()"""

new_hitl_exec = """        elif st.session_state.omni_state == "AWAITING_APPROVAL":
            cmd = st.session_state.current_action.get("command")
            st.warning(f"🚨 **Human-in-the-Loop Approval Required**")
            st.info("The agent's thought process for this command is preserved in the log above.")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Approve & Execute", type="primary"):
                    output = st.session_state.terminal.execute(cmd)
                    
                    # Update the pending log entry
                    for log in reversed(st.session_state.omni_log):
                        if log.get("type") == "pending_command":
                            log["type"] = "command"
                            log["output"] = output
                            break
                            
                    st.session_state.omni_messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```"})
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()
            with col_b:
                steer_input = st.text_input("Reject & Steer Agent:", placeholder="No, run 'npm install' instead.")
                if st.button("🚫 Reject"):
                    for log in reversed(st.session_state.omni_log):
                        if log.get("type") == "pending_command":
                            log["type"] = "rejected_command"
                            log["output"] = f"🚫 User rejected execution. Feedback: {steer_input}"
                            break
                            
                    st.session_state.omni_messages.append({"role": "user", "content": f"USER REJECTED COMMAND. Feedback: {steer_input}"})
                    st.session_state.omni_state = "GENERATING"
                    st.rerun()"""
content = content.replace(old_hitl_exec, new_hitl_exec)


with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("HitL UI bugs patched.")
