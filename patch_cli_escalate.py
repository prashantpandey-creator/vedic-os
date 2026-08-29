import sys

with open("cli.py", "r") as f:
    content = f.read()

# We want to inject an action_history tracking mechanism and the escalation logic.
# Look for where `action_data = parse_action(raw_response)` happens

replacement = """
                action_data = parse_action(raw_response)
                
                # --- HYBRID ESCALATION (CRY FOR HELP PROTOCOL) ---
                import json
                current_action_str = json.dumps(action_data, sort_keys=True)
                if 'action_history' not in locals():
                    action_history = []
                action_history.append(current_action_str)
                
                # If the exact same action fails 3 times in a row, escalate!
                if len(action_history) >= 3 and action_history[-1] == action_history[-2] == action_history[-3]:
                    console.print("[bold red]🚨 RECURSIVE LOOP DETECTED. ESCALATING TO CLAUDE 3.5 SONNET...[/bold red]")
                    # Hot-swap the brain to Claude
                    coder_model = "claude/claude-3-5-sonnet"
                    # Reset the history so it doesn't loop infinitely
                    action_history.clear()
                    # Tell Claude exactly what happened
                    messages.append({"role": "user", "content": "SYSTEM ESCALATION: Your local Llama model got stuck in an infinite loop failing to execute the above tool. You are Claude 3.5 Sonnet. Read the tracebacks, break the loop, and solve the problem."})
                    step += 1
                    continue
"""

content = content.replace("                action_data = parse_action(raw_response)", replacement)

with open("cli.py", "w") as f:
    f.write(content)
