import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

content = content.replace("\\n", "\n")

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
