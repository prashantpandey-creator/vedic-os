import sys

with open("app.py", "r") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    # Add import
    if "from agents.omni_state_machine import" in line and "vram_manager" not in "".join(lines):
        new_lines.append(line)
        new_lines.append("    from backend.vram_manager import enforce_context_window\n")
        continue
    
    if "raw_response = generate_next_thought" in line:
        indent = line.split("raw_response")[0]
        new_lines.append(f"{indent}st.session_state.omni_messages = enforce_context_window(st.session_state.omni_messages, max_turns=8)\n")
    
    new_lines.append(line)

with open("app.py", "w") as f:
    f.writelines(new_lines)
