from config import INGEST_MODEL, EDITOR_MODEL, FAST_MODEL, ESCALATION_MODEL
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
    coder_model = FAST_MODEL
    editor_model = EDITOR_MODEL
    
    # Initialize tools
    terminal = TerminalEngine(workspace_dir=workspace)
    registry = ToolRegistry(workspace, terminal)
    
    # Pre-clear VRAM
    with console.status("[dim]Allocating VRAM...[/dim]"):
        clear_all_vram_except([coder_model, editor_model, INGEST_MODEL])
    
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
                    messages, blueprint = init_omni_loop(user_intent, INGEST_MODEL, coder_model, workspace, None)
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
                # Remove thought from loop detection so minor text changes don't bypass the guard
                action_data_no_thought = {k: v for k, v in action_data.items() if k != 'thought'}
                current_action_str = json.dumps(action_data_no_thought, sort_keys=True)
                if 'action_history' not in locals():
                    action_history = []
                action_history.append(current_action_str)
                
                # If the exact same action fails 3 times in a row, escalate!
                if len(action_history) >= 3 and action_history[-1] == action_history[-2] == action_history[-3]:
                    # GUARDRAIL: Only escalate if we are explicitly allowed to leave Local Mode (API keys present)
                    if os.environ.get("ANTHROPIC_API_KEY"):
                        console.print("[bold red]🚨 RECURSIVE LOOP DETECTED. ESCALATING TO CLAUDE 3.5 SONNET...[/bold red]")
                        coder_model = ESCALATION_MODEL
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
                    err = action_data.get("gateway_error") if isinstance(action_data, dict) else None
                    messages.append({"role": "user", "content":
                        f"The model call itself failed ({err}). This is not your fault — "
                        f"repeat your last action." if err else
                        "Error: Your JSON block was malformed. Output exactly one ```json block."})
                    step += 1
                    continue
                    
                action = action_data.get("action")
                thought = action_data.get("thought", "")
                
                # Render the agent's thought process cleanly
                console.print(f"\n[dim italic]🤔 {thought}[/dim italic]")
                
                if action == "done":
                    accepted, done_msg = registry.check_done(action_data)
                    if accepted:
                        console.print(f"[bold green]✅ Task Complete.[/bold green] [dim]{done_msg}[/dim]")
                        break
                    console.print(f"[bold yellow]↩ {done_msg}[/bold yellow]")
                    messages.append({"role": "user", "content": done_msg})
                    step += 1
                    continue
                    
                if action == "ask_user":
                    console.print(f"[bold magenta]❓ Question:[/bold magenta] {action_data.get('question')}")
                    break # Break loop to wait for user input on next iteration
                
                # Render the tool execution
                tool_str = json.dumps({k:v for k,v in action_data.items() if k not in ["thought", "action"]}, indent=2)
                console.print(Panel(tool_str, title=f"🛠️ Tool: {action}", border_style="purple"))
                
                # All tools — including the editor-model rewrite — go through the
                # registry, which routes every write through write_verified().
                with console.status("[dim]Executing...[/dim]"):
                    tool_result = registry.execute_tool(action_data, main_model=coder_model)
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
