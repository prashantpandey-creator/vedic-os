with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    lines = f.readlines()

start = -1
for i, line in enumerate(lines):
    if line.startswith("def generate_blueprint("):
        start = i
        break

if start != -1:
    end = start + 1
    while end < len(lines) and (lines[end].startswith(" ") or lines[end].startswith("\t") or lines[end].strip() == ""):
        end += 1
    print("".join(lines[start:end]))
