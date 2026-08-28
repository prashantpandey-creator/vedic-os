with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith("                    with col_s2:"):
        new_lines.append("        with col_s2:\n")
    else:
        new_lines.append(line)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.writelines(new_lines)
