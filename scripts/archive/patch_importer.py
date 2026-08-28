import sys
import os

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Create the importer function
importer_code = """
def render_brain_importer(workspace_dir):
    import os
    import json
    
    with st.expander("🧠 Import External Agent Memory", expanded=False):
        st.markdown("Import context from cloud agents (Claude Code, Antigravity) directly into your Local Omni-Agent's memory.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Claude Code Memory**")
            claude_dir = os.path.expanduser("~/claude-sync/memory/")
            claude_memories = []
            if os.path.exists(claude_dir):
                claude_memories = [f for f in os.listdir(claude_dir) if f.endswith('.md')]
            
            if claude_memories:
                selected_claude = st.selectbox("Select Claude Memory:", ["(None)"] + claude_memories)
                if selected_claude != "(None)" and st.button("📥 Ingest Claude Context"):
                    with open(os.path.join(claude_dir, selected_claude), 'r') as mf:
                        context = mf.read()
                    from core.memory_graph import append_vritti
                    append_vritti("Imported Claude Context", "Claude-Code", context, workspace_dir)
                    st.success(f"Ingested {selected_claude} into Local Agent Memory!")
            else:
                st.info("No Claude memory found in ~/claude-sync/memory/")
                
        with col2:
            st.markdown("**Antigravity Transcripts**")
            ag_dir = os.path.expanduser("~/.gemini/antigravity/brain/")
            ag_sessions = []
            if os.path.exists(ag_dir):
                # Just show the last 5 modified sessions for simplicity
                ag_sessions = sorted([d for d in os.listdir(ag_dir) if os.path.isdir(os.path.join(ag_dir, d)) and d != "tempmediaStorage"], key=lambda x: os.path.getmtime(os.path.join(ag_dir, x)), reverse=True)[:5]
                
            if ag_sessions:
                selected_ag = st.selectbox("Select Antigravity Session:", ["(None)"] + ag_sessions)
                if selected_ag != "(None)" and st.button("📥 Ingest Antigravity Context"):
                    transcript_path = os.path.join(ag_dir, selected_ag, ".system_generated", "logs", "transcript.jsonl")
                    if os.path.exists(transcript_path):
                        summary = f"Imported Antigravity Session: {selected_ag}\\n"
                        try:
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
                        st.success(f"Ingested Antigravity session into Local Agent Memory!")
                    else:
                        st.error("Transcript not found for this session.")
            else:
                st.info("No Antigravity sessions found.")

# ----------------- Main View -----------------
"""

# Insert the importer code
content = content.replace("# ----------------- Main View -----------------", importer_code)

# Render it right after the file tree
old_omni = """    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    render_file_tree(workspace_dir)"""

new_omni = """    workspace_dir = render_workspace_config()
    if not workspace_dir: st.stop()
    render_file_tree(workspace_dir)
    render_brain_importer(workspace_dir)"""
content = content.replace(old_omni, new_omni)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Brain Importer UI patched.")
