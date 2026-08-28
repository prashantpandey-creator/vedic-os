import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Add Max Steps Slider
old_intent = 'intent_prompt = st.text_area("What do you want the Omni-Agent to do?", "Run \'npm test\', find the failing tests, and fix the codebase.")'
new_intent = """intent_prompt = st.text_area("What do you want the Omni-Agent to do?", "Run 'npm test', find the failing tests, and fix the codebase.")
    max_steps = st.slider("Max Autonomous Steps", min_value=1, max_value=30, value=10, help="How many times the agent is allowed to run a command, read the error, and try again before giving up.")"""
content = content.replace(old_intent, new_intent)

# 2. Pass st.container and max_steps
old_launch = """    if st.button("🚀 Launch Autonomous Loop", type="primary"):
        status = st.empty()
        stream_placeholder = st.empty()
        
        try:
            exec_log, blueprint = run_omni_loop(intent_prompt, meditate_model, coder_model, status, stream_placeholder, workspace_dir)"""
            
new_launch = """    if st.button("🚀 Launch Autonomous Loop", type="primary"):
        status = st.empty()
        ui_container = st.container()
        
        try:
            exec_log, blueprint = run_omni_loop(intent_prompt, meditate_model, coder_model, status, ui_container, workspace_dir, max_steps)"""
content = content.replace(old_launch, new_launch)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("app.py UI patched.")
