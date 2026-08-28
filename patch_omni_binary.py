import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    content = f.read()

content = content.replace("import json", "import orjson")
content = content.replace("json.loads(", "orjson.loads(")

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
    f.write(content)
