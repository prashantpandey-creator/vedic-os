with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("        if res.returncode != 0:"):
        new_lines.append("            if res.returncode != 0:\n")
    else:
        new_lines.append(line)

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.writelines(new_lines)
