import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    lines = f.readlines()

# Remove the second st.tabs definition
new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip().startswith('tab1, tab2, tab3, tab4 = st.tabs(['):
        if i > 100:  # The second one is around line 357
            skip = True
            continue
    if skip:
        if line.strip() == '])':
            skip = False
            continue
        continue
    new_lines.append(line)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.writelines(new_lines)
print("Removed duplicate st.tabs definition.")
