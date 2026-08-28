import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

old_block = """    if st.button("🚀 Execute Edit", type="primary"):
        status = st.empty()
        try:
            run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status)
            st.success("🎉 Edit applied successfully and Memory Graph updated!")
            with st.expander("View Memory Graph (PROJECT_MIND.md)"):
                if os.path.exists("PROJECT_MIND.md"):
                    with open("PROJECT_MIND.md", "r", encoding="utf-8") as f:
                        st.markdown(f.read())
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Execution Failed: {e}")"""

new_block = """    if st.button("🚀 Execute Edit", type="primary"):
        status = st.empty()
        stream_placeholder = st.empty()
        
        try:
            final_edits = run_nidra_pipeline(intent_prompt, meditate_model, coder_model, status, stream_placeholder)
            st.session_state["last_nidra_edits"] = final_edits
            
            st.success("🎉 Edit applied successfully and Memory Graph updated!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Execution Failed: {e}")

    if "last_nidra_edits" in st.session_state and st.session_state["last_nidra_edits"]:
        st.markdown("---")
        st.subheader("🛠️ Modified Files")
        st.info("💡 **Git Tracking:** A checkpoint was created automatically. Run `git diff HEAD~1` in your terminal to see the exact unified diff, or `git reset --hard HEAD~1` to undo this change.")
        
        for edit in st.session_state["last_nidra_edits"]:
            with st.expander(f"📄 {edit['file']} (Modified)"):
                st.markdown("**Search Block Replaced:**")
                st.code(edit['search'], language="python")
                st.markdown("**New Code:**")
                st.code(edit['replace'], language="python")
                
        with st.expander("View Memory Graph (PROJECT_MIND.md)"):
            if os.path.exists("PROJECT_MIND.md"):
                with open("PROJECT_MIND.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())"""

content = content.replace(old_block, new_block)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("app.py patched.")
