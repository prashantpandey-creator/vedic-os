import os

with open("app.py", "r") as f:
    content = f.read()

target = """        # Render the log
        st.markdown("### 🧠 Agent Stream")
        for log in st.session_state.omni_log:"""

replacement = """        # Render the log
        st.markdown("### 🧠 Agent Stream")
        
        # Component 4: Agent Step Tracker
        total = st.session_state.get('max_steps', 20)
        curr = st.session_state.get('total_steps', 1)
        progress = min(curr / total, 1.0)
        st.progress(progress, text=f"**Agent Brain Activity:** Step {curr} of {total}")
        if curr > total * 0.8:
            st.warning("⚠️ High step count detected. Agent might be caught in a loop.")
            
        for log in st.session_state.omni_log:"""

content = content.replace(target, replacement)

target_edit = """                elif log.get('type') == 'edit':
                    st.success(f"📝 Edited `{log['file']}`")
                    if 'diff' in log: st.code(log['diff'], language="diff")"""

replacement_edit = """                elif log.get('type') == 'edit':
                    st.success(f"📝 Edited `{log['file']}`")
                    
                    # Component 5: Dedicated Diff Viewer with difflib
                    import difflib
                    if 'old_content' in log and 'new_content' in log:
                        diff = list(difflib.unified_diff(
                            log['old_content'].splitlines(keepends=True),
                            log['new_content'].splitlines(keepends=True),
                            fromfile='old', tofile='new'
                        ))
                        diff_text = "".join(diff)
                        st.code(diff_text, language="diff")
                    elif 'diff' in log:
                        st.code(log['diff'], language="diff")"""

content = content.replace(target_edit, replacement_edit)

with open("app.py", "w") as f:
    f.write(content)
