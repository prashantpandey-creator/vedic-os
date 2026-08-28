import sys

with open("/Users/badenath/projects/local-llm-ui/Dockerfile", "r") as f:
    content = f.read()

content = content.replace("    npm \\", "    npm \\\n    ripgrep \\\n    fd-find \\\n    bat \\")

with open("/Users/badenath/projects/local-llm-ui/Dockerfile", "w") as f:
    f.write(content)
