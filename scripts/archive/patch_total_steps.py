import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

guard_code = """    if "omni_state" not in st.session_state:
        st.session_state.omni_state = "IDLE"
        st.session_state.omni_step = 1
        st.session_state.total_steps = 1
        st.session_state.omni_log = []
        st.session_state.omni_messages = []
        st.session_state.terminal = None
        st.session_state.action_history = []
        st.session_state.hitl_enabled = True

    if "total_steps" not in st.session_state:
        st.session_state.total_steps = st.session_state.get("omni_step", 1)
"""

old_code = """    if "omni_state" not in st.session_state:
        st.session_state.omni_state = "IDLE"
        st.session_state.omni_step = 1
        st.session_state.total_steps = 1
        st.session_state.omni_log = []
        st.session_state.omni_messages = []
        st.session_state.terminal = None
        st.session_state.action_history = []
        st.session_state.hitl_enabled = True"""

content = content.replace(old_code, guard_code)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
