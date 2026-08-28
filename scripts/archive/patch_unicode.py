import sys

with open("/Users/badenath/projects/local-llm-ui/core/terminal_engine.py", "r") as f:
    content = f.read()

content = content.replace("capture_output=True, text=True, timeout=60", 'capture_output=True, text=True, timeout=60, errors="replace"')

with open("/Users/badenath/projects/local-llm-ui/core/terminal_engine.py", "w") as f:
    f.write(content)
