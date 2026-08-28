import sys

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "r") as f:
    content = f.read()

# Add to prompt addition
old_prompt = """2. edit_file (Apply a search-and-replace to an existing file)
{"thought": "...", "action": "edit_file", "file": "app.py", "search": "old code", "replace": "new code"}"""

new_prompt = """2. edit_file (Apply a search-and-replace to an existing file)
{"thought": "...", "action": "edit_file", "file": "app.py", "search": "old code", "replace": "new code"}

3. create_file (Create a brand new file with content)
{"thought": "...", "action": "create_file", "file": "new_script.py", "content": "print('hello world')"}"""

content = content.replace(old_prompt, new_prompt)

# Renumber the others
content = content.replace("3. create_artifact", "4. create_artifact")
content = content.replace("4. invoke_subagent", "5. invoke_subagent")
content = content.replace("5. create_pull_request", "6. create_pull_request")
content = content.replace("6. done", "7. done")

# Add execution logic
old_exec = """        elif action == "edit_file":
            filepath = action_data.get("file")"""

new_exec = """        elif action == "create_file":
            filepath = action_data.get("file")
            content = action_data.get("content", "")
            import os
            full_path = os.path.join(self.workspace_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"type": "edit", "file": filepath, "diff": "File created.", "msg": f"File {filepath} created successfully."}
            
        elif action == "edit_file":
            filepath = action_data.get("file")"""

content = content.replace(old_exec, new_exec)

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "w") as f:
    f.write(content)
