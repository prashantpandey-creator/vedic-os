import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# 1. Remove Sidebar Radio
sidebar_code = """st.sidebar.title("Vedic Developer Suite")
app_mode = st.sidebar.radio("Select Engine:", [
    "🦅 Omni-Agent (Autonomous Terminal Loop)",
    "🧬 Coding Agent with Harness (Nidra)",
    "🏗️ App Builder (Vyasa Architect)",
    "💬 Standard Chat (Hybrid Non-Transformers)"
])"""
content = content.replace(sidebar_code, "st.sidebar.title(\"Vedic Developer Suite\")\nst.sidebar.info(\"Choose a stage from the tabs above to explore the evolution of the Vedic AI Engine.\")")

# 2. Setup Tabs at the top of Main View
tab_setup = """tab1, tab2, tab3, tab4 = st.tabs([
    "💬 Stage 1: Bare Model", 
    "🏗️ Stage 2: Sandbox Architect", 
    "🧬 Stage 3: Nidra Harness", 
    "🦅 Stage 4: Omni-Agent"
])"""
content = content.replace("# ----------------- Main View -----------------", f"# ----------------- Main View -----------------\n{tab_setup}")

# 3. Replace the headers directly!
content = content.replace('if app_mode == "💬 Standard Chat (Hybrid Non-Transformers)":', 'with tab1:')
content = content.replace('elif app_mode == "🧬 Coding Agent with Harness (Nidra)":', 'with tab3:')
content = content.replace('elif app_mode == "🦅 Omni-Agent (Autonomous Terminal Loop)":', 'with tab4:')

# For 'else:', we have to be careful as it might match other else blocks.
# In the original file, it was exactly `else:\n    st.markdown("Describe an app below.`
content = content.replace('else:\n    st.markdown("Describe an app below', 'with tab2:\n    st.markdown("Describe an app below')

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)

print("Tabs applied via simple replacement.")
