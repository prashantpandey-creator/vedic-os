import sys
import os

with open("cli.py", "r") as f:
    content = f.read()

# Make escalation safe and optional
old_escalation = """
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

new_escalation = """
                if len(action_history) >= 3 and action_history[-1] == action_history[-2] == action_history[-3]:
                    # GUARDRAIL: Only escalate if we are explicitly allowed to leave Local Mode (API keys present)
                    if os.environ.get("ANTHROPIC_API_KEY"):
                        console.print("[bold red]🚨 RECURSIVE LOOP DETECTED. ESCALATING TO CLAUDE 3.5 SONNET...[/bold red]")
                        coder_model = "claude/claude-3-5-sonnet"
                        action_history.clear()
                        messages.append({"role": "user", "content": "SYSTEM ESCALATION: Your local Llama model got stuck in an infinite loop failing to execute the above tool. You are Claude 3.5 Sonnet. Read the tracebacks, break the loop, and solve the problem."})
                        step += 1
                        continue
                    else:
                        console.print("[bold yellow]⚠️ Loop Detected, but Local Mode is strictly enforced (No API Keys). Asking Human for help...[/bold yellow]")
                        console.print(f"[bold magenta]❓ Question:[/bold magenta] I am stuck in a recursive error loop. How should I proceed?")
                        break
"""

if old_escalation in content:
    content = content.replace(old_escalation, new_escalation)
    with open("cli.py", "w") as f:
        f.write(content)
    print("Safeguards applied.")
else:
    print("Could not find the exact escalation block to patch. It might have already been modified.")
