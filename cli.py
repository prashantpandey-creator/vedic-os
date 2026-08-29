import os
import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

# Fix path to load modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.terminal_engine import TerminalEngine
from core.tool_registry import ToolRegistry
from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action
from backend.vram_manager import clear_all_vram_except, enforce_context_window

console = Console()

def run_cli():
    console.print(Panel.fit("[bold blue]Vedic Omni-Agent CLI[/bold blue]\n[dim]Local AI Developer Tool (Claude Code Clone)[/dim]", border_style="blue"))
    
    workspace = os.getcwd()
    coder_model = "mannix/llama3.1-8b-abliterated:latest"
    editor_model = "granite4:3b-h"
    
    # Initialize tools
    terminal = TerminalEngine(workspace_dir=workspace)
    registry = ToolRegistry(workspace, terminal)
    
    # Pre-clear VRAM
    with console.status("[dim]Allocating VRAM...[/dim]"):
        clear_all_vram_except([coder_model, editor_model, "qwen2.5:0.5b"])
    
    history = FileHistory(os.path.join(workspace, ".omni_history"))
    messages = []
    
    while True:
        try:
            # Interactive Prompt
            user_intent = prompt("\n❯ ", history=history)
            if not user_intent.strip():
                continue
            if user_intent.lower() in ["exit", "quit"]:
                break
                
            # Bootstrap if first time
            if not messages:
                with console.status("[dim]Scanning Repository...[/dim]"):
                    messages, blueprint = init_omni_loop(user_intent, "qwen2.5:0.5b", coder_model, workspace, None)
                    console.print(Panel(Markdown(blueprint), title="Blueprint", border_style="cyan"))
            else:
                messages.append({"role": "user", "content": user_intent})
                
            step = 1
            max_steps = 20
            
            while step <= max_steps:
                messages = enforce_context_window(messages, max_turns=6)
                
                with console.status(f"[bold yellow]Thinking (Step {step})...[/bold yellow]", spinner="dots"):
                    raw_response = generate_next_thought(coder_model, messages, step_placeholder=None)
                    messages.append({"role": "assistant", "content": raw_response})
                    

                action_data = parse_action(raw_response)
                
                # --- HYBRID ESCALATION (CRY FOR HELP PROTOCOL) ---
                import json
                current_action_str = json.dumps(action_data, sort_keys=True)
                if 'action_history' not in locals():
                    action_history = []
                action_history.append(current_action_str)
                
                # If the exact same action fails 3 times in a row, escalate!
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

                if not action_data or action_data.get("action") == "error":
                    console.print("[red]Malformed JSON from LLM. Retrying...[/red]")
                    messages.append({"role": "user", "content": "Error: Your JSON block was malformed. Fix it."})
                    step += 1
                    continue
                    
                action = action_data.get("action")
                thought = action_data.get("thought", "")
                
                # Render the agent's thought process cleanly
                console.print(f"\n[dim italic]🤔 {thought}[/dim italic]")
                
                if action == "done":
                    console.print("[bold green]✅ Task Complete.[/bold green]")
                    break
                    
                if action == "ask_user":
                    console.print(f"[bold magenta]❓ Question:[/bold magenta] {action_data.get('question')}")
                    break # Break loop to wait for user input on next iteration
                
                # Render the tool execution
                tool_str = json.dumps({k:v for k,v in action_data.items() if k not in ["thought", "action"]}, indent=2)
                console.print(Panel(tool_str, title=f"🛠️ Tool: {action}", border_style="purple"))
                
                # Multi-Agent Routing for Edit
                if action == "edit_file" and "instruction" in action_data:
                    filepath = os.path.join(workspace, action_data["file"])
                    instruction = action_data["instruction"]
                    
                    with console.status(f"[bold cyan]Granite is editing {action_data['file']}...[/bold cyan]"):
                        try:
                            import requests, re
                            with open(filepath, "r") as f:
                                current_code = f.read()
                            
                            prompt_str = f"Instruction: {instruction}\n\nCURRENT CODE:\n```\n{current_code}\n```\n\nRewrite the code to fulfill the instruction. Output ONLY the complete updated code inside ``` blocks."
                            res = requests.post("http://127.0.0.1:11434/api/chat", json={
                                "model": editor_model,
                                "messages": [{"role": "user", "content": prompt_str}],
                                "stream": False
                            }).json()
                            granite_output = res.get("message", {}).get("content", "")
                            
                            def extract_code(text):
                                match = re.search(r'```[a-zA-Z]*\n(.*?)\n```', text, re.DOTALL)
                                if match: return match.group(1)
                                match = re.search(r'```(.*?)```', text, re.DOTALL)
                                if match: return match.group(1).strip()
                                return text
                                
                            fixed_code = extract_code(granite_output)
                            with open(filepath, "w") as f:
                                f.write(fixed_code)
                            msg = f"Granite successfully updated {filepath}"
                        except Exception as e:
                            msg = f"Granite failed to edit file: {e}"
                else:
                    with console.status("[dim]Executing...[/dim]"):
                        tool_result = registry.execute_tool(action_data)
                        msg = tool_result.get("msg", str(tool_result))
                
                # Render the result
                console.print(f"[dim]Output:[/dim]\n[green]{msg}[/green]")
                messages.append({"role": "user", "content": f"Tool Execution Result:\n```\n{msg}\n```"})
                
                step += 1
                
        except KeyboardInterrupt:
            console.print("\n[red]Operation cancelled.[/red]")
        except EOFError:
            break

if __name__ == "__main__":
    run_cli()
