import sys

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "r") as f:
    content = f.read()

content = content.replace("from core.ollama_api import OLLAMA_URL, evict_model", "from core.ollama_api import OLLAMA_URL, evict_model\nfrom config import FAST_MODEL")
content = content.replace("def execute_tool(self, action_data, fast_model=\"mannix/llama3.1-8b-abliterated:latest\", main_model=None):", "def execute_tool(self, action_data, fast_model=FAST_MODEL, main_model=None):")

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "w") as f:
    f.write(content)

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    app_content = f.read()

app_content = app_content.replace("result_obj = st.session_state.registry.execute_tool(action_data, fast_model='mannix/llama3.1-8b-abliterated:latest', main_model=coder_model)", "result_obj = st.session_state.registry.execute_tool(action_data, fast_model=FAST_MODEL, main_model=coder_model)")

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(app_content)
    
print("tool_registry patched for portability.")
