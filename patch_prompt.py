import sys

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "r") as f:
    content = f.read()

# Replace the edit_file doc
old_edit = '{"thought": "...", "action": "edit_file", "file": "path", "search": "old text", "replace": "new text"}'
new_edit = '{"thought": "...", "action": "edit_file", "file": "path", "instruction": "Detailed instruction on what to change"}'

content = content.replace(old_edit, new_edit)

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "w") as f:
    f.write(content)
