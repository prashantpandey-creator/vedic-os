import sys

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "r") as f:
    content = f.read()

hint = """Available Tools (Choose ONE per response):

1. run_command (NOTE: You have access to modern Rust binaries: 'rg' for searching code, 'fdfind' for finding files, and 'batcat' for reading.)"""

content = content.replace("Available Tools (Choose ONE per response):\n\n1. run_command", hint)

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "w") as f:
    f.write(content)
