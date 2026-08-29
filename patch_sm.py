import sys

with open("agents/omni_state_machine.py", "r") as f:
    lines = f.readlines()

new_lines = []
in_generate = False

for idx, line in enumerate(lines):
    if line.startswith("def generate_next_thought"):
        in_generate = True
        new_lines.append(line)
        new_lines.append("    from core.llm_gateway import generate_response\n")
        new_lines.append("    # Offload everything to the Hybrid Gateway\n")
        new_lines.append("    return generate_response(coder_model, messages)\n")
        continue
    
    if in_generate:
        # Skip until the next top-level function
        if line.startswith("def ") or line.startswith("class "):
            in_generate = False
        else:
            continue
            
    new_lines.append(line)

with open("agents/omni_state_machine.py", "w") as f:
    f.writelines(new_lines)

