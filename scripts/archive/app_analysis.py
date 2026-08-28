import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    lines = f.readlines()

def find_func(func_name):
    start = -1
    for i, line in enumerate(lines):
        if line.startswith(f"def {func_name}"):
            start = i
            break
    if start == -1:
        return ""
    end = start + 1
    while end < len(lines) and (lines[end].startswith(" ") or lines[end].startswith("\t") or lines[end].strip() == ""):
        end += 1
    return "".join(lines[start:end])

print("--- render_workspace_config ---")
print(find_func("render_workspace_config"))

print("--- render_brain_importer ---")
print(find_func("render_brain_importer"))
