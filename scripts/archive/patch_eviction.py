import sys

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "r") as f:
    content = f.read()

# Add import
if "from core.ollama_api import evict_model" not in content:
    content = content.replace("from core.ollama_api import OLLAMA_URL", "from core.ollama_api import OLLAMA_URL, evict_model")

old_exec = """    def execute_tool(self, action_data, fast_model="mannix/llama3.1-8b-abliterated:latest"):"""
new_exec = """    def execute_tool(self, action_data, fast_model="mannix/llama3.1-8b-abliterated:latest", main_model=None):"""
content = content.replace(old_exec, new_exec)

old_subagent = """        elif action == "invoke_subagent":
            role = action_data.get("role", "subagent")
            task = action_data.get("task", "")
            # Headless autonomous mini-loop for the subagent
            sub_msg, sub_log = self._run_headless_subagent(role, task, fast_model)
            return {"type": "subagent", "role": role, "task": task, "log": sub_log, "msg": f"Subagent '{role}' completed task. Result:\\n{sub_msg}"}"""

new_subagent = """        elif action == "invoke_subagent":
            role = action_data.get("role", "subagent")
            task = action_data.get("task", "")
            
            # --- VRAM SAFETY HANDOFF ---
            if main_model and main_model != fast_model:
                evict_model(main_model)  # Flush main model to prevent Swap Death
                
            # Headless autonomous mini-loop for the subagent
            sub_msg, sub_log = self._run_headless_subagent(role, task, fast_model)
            
            # --- VRAM RESTORE ---
            if main_model and main_model != fast_model:
                evict_model(fast_model)  # Flush subagent so main model can wake up
                
            return {"type": "subagent", "role": role, "task": task, "log": sub_log, "msg": f"Subagent '{role}' completed task. Result:\\n{sub_msg}"}"""
content = content.replace(old_subagent, new_subagent)

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "w") as f:
    f.write(content)

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    app_content = f.read()
app_content = app_content.replace("result_obj = st.session_state.registry.execute_tool(action_data, fast_model=coder_model)", "result_obj = st.session_state.registry.execute_tool(action_data, fast_model='mannix/llama3.1-8b-abliterated:latest', main_model=coder_model)")
with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(app_content)

print("VRAM Safety Handoff patched.")
