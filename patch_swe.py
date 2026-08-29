import sys

with open("/Users/badenath/projects/local-llm-ui/tests/run_swe_lite.py", "r") as f:
    content = f.read()

# Fix imports
content = content.replace(
    "from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action, get_omni_system_prompt",
    "from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action"
)

# Fix init_omni_loop call
old_init = """        # Init State Machine
        initial_state = init_omni_loop(task["intent"], "qwen2.5:0.5b", coder_model, workspace_dir=workspace, status_container=None)
        
        sys_prompt = get_omni_system_prompt(task["intent"], initial_state["blueprint"], initial_state["memory"])
        messages = [{"role": "system", "content": sys_prompt}]"""
        
new_init = """        # Init State Machine
        messages, blueprint = init_omni_loop(task["intent"], "qwen2.5:0.5b", coder_model, workspace_dir=workspace, status_container=None)"""

content = content.replace(old_init, new_init)

with open("/Users/badenath/projects/local-llm-ui/tests/run_swe_lite.py", "w") as f:
    f.write(content)
