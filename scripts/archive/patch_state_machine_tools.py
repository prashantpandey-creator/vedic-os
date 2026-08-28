import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    content = f.read()

# Add import
import_block = "from core.memory_graph import read_compressed_memory, append_vritti"
new_import = "from core.memory_graph import read_compressed_memory, append_vritti\nfrom core.tool_registry import ToolRegistry"
content = content.replace(import_block, new_import)

# Replace the hardcoded prompt block
old_prompt = """You must accomplish the user's intent autonomously.
Output ONLY valid JSON for your next action. Choose ONE action per response:
1. Run a terminal command (e.g. to run tests, list files, or start a build).
2. Edit a file.
3. Finish the task.

Format MUST be exactly one of these:
{"thought": "reasoning", "action": "run_command", "command": "npm test"}
{"thought": "reasoning", "action": "edit_file", "file": "path", "search": "exact old text", "replace": "new text"}
{"thought": "reasoning", "action": "done"}
"""

new_prompt = """You must accomplish the user's intent autonomously.
Output ONLY valid JSON for your next action.

{tool_schemas}
"""
content = content.replace(old_prompt, new_prompt)

# Instantiate dummy registry just to get schemas in init
old_init = "    system = f\"\"\"You are the Vedic Omni-Agent"
new_init = """    registry = ToolRegistry(workspace_dir, None)
    system = f\"\"\"You are the Vedic Omni-Agent"""
content = content.replace(old_init, new_init)

content = content.replace("{tool_schemas}", "{registry.get_system_prompt_addition()}")

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
    f.write(content)

print("omni_state_machine.py patched for Tool Registry.")
