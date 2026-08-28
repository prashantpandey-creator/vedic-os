import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "r") as f:
    content = f.read()

# Add streamlit import
content = content.replace("import subprocess", "import subprocess\nimport streamlit as st")

# Change parameter name
content = content.replace("stream_placeholder, workspace_dir=\".\"):", "ui_container, workspace_dir=\".\", max_steps=10):")

# Remove hardcoded max_steps
content = content.replace("    max_steps = 10\n    execution_log = []", "    execution_log = []")

# Wrap the step loop in an expander
old_loop_start = """    for step in range(1, max_steps + 1):
        status.write(f"🦅 **[STEP {step}/{max_steps}]** {coder_model} is deciding next action...")
        
        coder_payload = {"""

new_loop_start = """    for step in range(1, max_steps + 1):
        status.write(f"🦅 **[STEP {step}/{max_steps}]** {coder_model} is deciding next action...")
        
        step_expander = ui_container.expander(f"🦅 Omni-Agent Step {step}", expanded=True)
        step_placeholder = step_expander.empty()
        
        coder_payload = {"""
content = content.replace(old_loop_start, new_loop_start)

# Update where it writes
content = content.replace('stream_placeholder.code(raw_response, language="json")', 'step_placeholder.code(raw_response, language="json")')

# When executing a command, append it to the expander!
old_cmd_exec = """                # Execute via Revolutionary Terminal Engine
                output = terminal.execute(cmd)
                messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```\\nWhat is your next step? Output the JSON action."})"""

new_cmd_exec = """                # Execute via Revolutionary Terminal Engine
                output = terminal.execute(cmd)
                step_expander.markdown(f"**💻 Terminal Output:**")
                step_expander.code(output, language="bash")
                messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```\\nWhat is your next step? Output the JSON action."})"""
content = content.replace(old_cmd_exec, new_cmd_exec)

# When editing a file, append it to the expander!
old_file_exec = """                try:
                    apply_search_replace(filepath, search, replace, workspace_dir=workspace_dir)
                    messages.append({"role": "user", "content": f"File {filepath} edited successfully. What is your next step? Output the JSON action."})
                except Exception as e:
                    messages.append({"role": "user", "content": f"Edit failed: {e}\\nPlease fix your search block and try again."})"""

new_file_exec = """                try:
                    apply_search_replace(filepath, search, replace, workspace_dir=workspace_dir)
                    step_expander.success(f"Successfully edited `{filepath}`")
                    messages.append({"role": "user", "content": f"File {filepath} edited successfully. What is your next step? Output the JSON action."})
                except Exception as e:
                    step_expander.error(f"Failed to edit `{filepath}`: {e}")
                    messages.append({"role": "user", "content": f"Edit failed: {e}\\nPlease fix your search block and try again."})"""
content = content.replace(old_file_exec, new_file_exec)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "w") as f:
    f.write(content)

print("Omni Agent UI transcript patched.")
