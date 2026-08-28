import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

import re

# 1. Add it to omni_log upon Launch Agent
old_launch = """                    messages, blueprint = init_omni_loop(st.session_state.omni_intent_val, meditate_model, coder_model, workspace_dir, status_container=status_box)
                    st.session_state.omni_messages = messages
                    st.session_state.omni_bp = blueprint
                    st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)
                    st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)
                    st.session_state.intent_prompt = st.session_state.omni_intent_val
                    st.session_state.phase = 1
                    st.session_state.phase_summaries = []"""

new_launch = """                    messages, blueprint = init_omni_loop(st.session_state.omni_intent_val, meditate_model, coder_model, workspace_dir, status_container=status_box)
                    st.session_state.omni_messages = messages
                    st.session_state.omni_bp = blueprint
                    st.session_state.terminal = TerminalEngine(workspace_dir=workspace_dir)
                    st.session_state.registry = ToolRegistry(workspace_dir, st.session_state.terminal)
                    st.session_state.intent_prompt = st.session_state.omni_intent_val
                    st.session_state.phase = 1
                    st.session_state.phase_summaries = []
                    st.session_state.omni_log.append({
                        "step": 0,
                        "type": "blueprint",
                        "blueprint": blueprint
                    })"""
content = content.replace(old_launch, new_launch)

# 2. Add it to omni_log upon Phase Transition
old_phase = """                    # Re-ingest codebase with fresh eyes (files may have changed!)
                    st.info("♻️ Phase {} complete. Re-ingesting codebase for Phase {}...".format(current_phase, current_phase + 1))
                    status_box = st.empty()
                    messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)
                    
                    # Inject prior phase summaries into the new system prompt
                    prior_context = "\\n".join(["Phase {}: {}".format(i+1, s) for i, s in enumerate(st.session_state.phase_summaries)])
                    messages[0]["content"] += "\\n\\nPRIOR PHASE SUMMARIES (your own earlier work):\\n" + prior_context
                    
                    st.session_state.omni_messages = messages
                    st.session_state.omni_log = []"""

new_phase = """                    # Re-ingest codebase with fresh eyes (files may have changed!)
                    st.info("♻️ Phase {} complete. Re-ingesting codebase for Phase {}...".format(current_phase, current_phase + 1))
                    status_box = st.empty()
                    messages, blueprint = init_omni_loop(st.session_state.intent_prompt, meditate_model, coder_model, workspace_dir, status_container=status_box)
                    
                    # Inject prior phase summaries into the new system prompt
                    prior_context = "\\n".join(["Phase {}: {}".format(i+1, s) for i, s in enumerate(st.session_state.phase_summaries)])
                    messages[0]["content"] += "\\n\\nPRIOR PHASE SUMMARIES (your own earlier work):\\n" + prior_context
                    
                    st.session_state.omni_messages = messages
                    st.session_state.omni_log = [{
                        "step": 0,
                        "type": "blueprint",
                        "blueprint": blueprint
                    }]"""
content = content.replace(old_phase, new_phase)

# 3. Render it in the log
old_render = """                elif log.get('type') == 'github_pr':
                    st.success(f"🐙 **Pull Request Raised!**")
                    st.markdown(f"[View PR on GitHub]({log['url']})")"""

new_render = """                elif log.get('type') == 'github_pr':
                    st.success(f"🐙 **Pull Request Raised!**")
                    st.markdown(f"[View PR on GitHub]({log['url']})")
                elif log.get('type') == 'blueprint':
                    st.info("🐍 **Codebase Blueprint Generated:**")
                    st.markdown(log['blueprint'])"""
content = content.replace(old_render, new_render)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Blueprint added to chat history.")
