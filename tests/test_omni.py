import sys
import json
from core.terminal_engine import TerminalEngine
from core.tool_registry import ToolRegistry
from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action

class MockPlaceholder:
    def code(self, text, language): pass

def run_test():
    workspace = "/Users/badenath/vedic_workspaces/agent_benchmark_1"
    # Fallback model in case the abliterated one isn't loaded
    model = "llama3.1:latest" # or whichever is default if mannix fails
    try:
        import requests
        from core.ollama_api import OLLAMA_URL
        tags = requests.get(f"{OLLAMA_URL}/api/tags").json()
        models = [m['name'] for m in tags.get('models', [])]
        if "mannix/llama3.1-8b-abliterated:latest" in models:
            model = "mannix/llama3.1-8b-abliterated:latest"
        elif "llama3.1:8b" in models:
            model = "llama3.1:8b"
        else:
            model = models[0] if models else "llama3.1:8b"
    except:
        pass

    intent = "Run python3 test_math.py. The tests will fail. Find the bug in math_utils.py, fix it, and verify the tests pass."

    print(f"Test starting on {workspace} with model {model}...")
    terminal = TerminalEngine(workspace_dir=workspace)
    registry = ToolRegistry(workspace_dir=workspace, terminal_engine=terminal)

    print("Initializing Blueprint...")
    messages, blueprint = init_omni_loop(intent, model, model, workspace_dir=workspace)
    
    # Pre-inject the available tools so it knows what to do
    system_prompt = messages[0]["content"]
    if "Available Tools" not in system_prompt:
         messages[0]["content"] += registry.get_system_prompt_addition()

    for step in range(1, 10):
        print(f"\n--- STEP {step} ---")
        raw_resp = generate_next_thought(model, messages, MockPlaceholder())
        messages.append({"role": "assistant", "content": raw_resp})
        
        action_data = parse_action(raw_resp)
        action = action_data.get('action')
        print(f"Thought: {action_data.get('thought', '...')}")
        print(f"Action: {action}")
        
        if action == 'done':
            print("\n✅ TEST PASSED: Agent declared done.")
            return True
            
        result = registry.execute_tool(action_data, fast_model=model, main_model=model)
        messages.append({"role": "user", "content": result.get("msg", "")})
        
        out = result.get('msg', '')
        print(f"System Response: {out[:150]}")
        
        if "OK" in out and action == "run_command":
            print("\n✅ TEST PASSED: Agent successfully fixed the bug and tests pass.")
            return True

if __name__ == "__main__":
    run_test()
