"""
Critical path test: Does the 8B model actually produce parseable JSON actions?
This test runs the full output pipeline end-to-end WITHOUT a UI.
"""
import sys
import json
import requests
from core.ollama_api import OLLAMA_URL
from agents.omni_state_machine import parse_action

DIVIDER = "\n" + "="*60 + "\n"

def get_available_model():
    tags = requests.get(f"{OLLAMA_URL}/api/tags").json()
    models = [m['name'] for m in tags.get('models', [])]
    print(f"Available: {models}")
    # Prefer fast abliterated, fallback to any 8b, fallback to first
    for candidate in ["mannix/llama3.1-8b-abliterated:latest", "llama3.1:8b", "llama3.1:latest"]:
        if candidate in models: return candidate
    return models[0] if models else None

def test_json_output_reliability(model, n_trials=5):
    """
    Runs the model n times asking for a JSON action.
    Checks: 1) Does it output JSON? 2) Is the action valid? 3) Are fields correct?
    """
    print(f"Testing JSON output reliability on model: {model}")
    
    system = """You are the Vedic Omni-Agent. You must output ONLY valid JSON.
Available Tools (Choose ONE per response):

1. run_command
{"thought": "...", "action": "run_command", "command": "npm test"}

2. edit_file
{"thought": "...", "action": "edit_file", "file": "path", "search": "old text", "replace": "new text"}

3. create_artifact (Generate permanent reports, plans, or full files)
{"thought": "...", "action": "create_artifact", "title": "ArchitecturePlan", "content": "# Markdown Content..."}

4. invoke_subagent (Spawn a fast background agent to do research or recursive tasks)
{"thought": "...", "action": "invoke_subagent", "role": "researcher", "task": "Find all API routes returning 404"}

5. create_pull_request (Push local edits to a new branch and raise a PR on GitHub)
{"thought": "...", "action": "create_pull_request", "branch_name": "fix-auth-bug", "title": "Fix Auth Bug", "body": "Fixed the token expiration issue."}

6. done
{"thought": "...", "action": "done"}
"""

    test_prompts = [
        "Run the test suite to check for failures.",
        "The tests failed with: TypeError: cannot read property of undefined. Fix it.",
        "Create an architecture analysis artifact for this Node.js project.",
        "All tests are passing now. We are done.",
        "Find all files that import from './utils' and list them."
    ]
    
    valid_actions = {"run_command", "edit_file", "create_artifact", "invoke_subagent", "create_pull_request", "done"}
    
    results = []
    for i, prompt in enumerate(test_prompts[:n_trials]):
        print(f"\nTrial {i+1}: '{prompt[:60]}...'")
        try:
            res = requests.post(f"{OLLAMA_URL}/api/chat", json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "options": {"temperature": 0.0},
                "stream": False
            }, timeout=60).json()
            
            raw = res.get("message", {}).get("content", "")
            print(f"  Raw output ({len(raw)} chars): {raw[:150]}")
            
            parsed = parse_action(raw)
            action = parsed.get("action")
            thought = parsed.get("thought", "")
            
            is_valid_action = action in valid_actions
            has_thought = bool(thought)
            
            result = {
                "trial": i+1,
                "prompt": prompt[:50],
                "action": action,
                "valid_action": is_valid_action,
                "has_thought": has_thought,
                "parse_success": action != "error"
            }
            results.append(result)
            
            status = "✅" if is_valid_action else "❌"
            print(f"  {status} Action: {action} | Thought: {thought[:80]}")
        except Exception as e:
            results.append({"trial": i+1, "error": str(e), "parse_success": False})
            print(f"  ❌ Exception: {e}")
    
    print(DIVIDER)
    total = len(results)
    passed = sum(1 for r in results if r.get("parse_success"))
    valid = sum(1 for r in results if r.get("valid_action"))
    
    print(f"JSON Parse Success: {passed}/{total}")
    print(f"Valid Action Names: {valid}/{total}")
    print(f"Score: {valid/total*100:.0f}%")
    return valid / total if total > 0 else 0

if __name__ == "__main__":
    model = get_available_model()
    if not model:
        print("ERROR: No models available in Ollama!")
        sys.exit(1)
    
    score = test_json_output_reliability(model)
    
    if score >= 0.8:
        print(f"\n✅ ARCHITECTURE SOUND: Model produces valid JSON actions {score*100:.0f}% of the time.")
    elif score >= 0.5:
        print(f"\n⚠️ ARCHITECTURE FRAGILE: {score*100:.0f}% success. Need JSON repair logic.")
    else:
        print(f"\n❌ ARCHITECTURE BROKEN: Only {score*100:.0f}% valid. Need stronger prompting or model change.")
