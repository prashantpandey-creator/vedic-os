import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Improve the 'done' memory persistence
old_done_action = """            if action == "done":
                st.session_state.omni_state = "DONE"
                append_vritti(st.session_state.intent_prompt, "Omni-Loop", "[PRAMANA] Done", workspace_dir=workspace_dir)
                st.rerun()"""

new_done_action = """            if action == "done":
                st.session_state.omni_state = "DONE"
                from core.checkpoint import build_phase_summary
                summary = build_phase_summary(st.session_state.omni_log)
                append_vritti(st.session_state.intent_prompt, "Omni-Loop", "[PRAMANA] Done", extra="**Marathon Session Summary:**\\n" + summary, workspace_dir=workspace_dir)
                st.rerun()"""
content = content.replace(old_done_action, new_done_action)

# 2. Fix the "Start Completely New Task" button to clear checkpoints
old_new_task = """            with col_d1:
                if st.button("Start Completely New Task"):
                    if st.session_state.terminal: st.session_state.terminal.cleanup()
                    st.session_state.omni_state = "IDLE"
                    st.rerun()"""

new_new_task = """            with col_d1:
                if st.button("Start Completely New Task"):
                    if st.session_state.terminal: st.session_state.terminal.cleanup()
                    from core.checkpoint import clear_checkpoints
                    clear_checkpoints(workspace_dir)
                    st.session_state.omni_state = "IDLE"
                    # Wipe the intent to encourage fresh auto-suggest
                    if "omni_intent_val" in st.session_state:
                        del st.session_state["omni_intent_val"]
                    st.rerun()"""
content = content.replace(old_new_task, new_new_task)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Marathon lifecycle patched.")
