import sys

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "r") as f:
    content = f.read()

old_hint = "1. run_command (NOTE: You have access to modern Rust binaries: 'rg' for searching code, 'fdfind' for finding files, and 'batcat' for reading.)"
new_hint = "1. run_command (NOTE: You have access to modern Rust binaries: 'rg', 'fdfind', 'batcat'. WARNING: Each command runs in a fresh shell. You cannot 'cd' and expect it to persist to the next step. Chain commands with &&.)"

content = content.replace(old_hint, new_hint)

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "w") as f:
    f.write(content)
