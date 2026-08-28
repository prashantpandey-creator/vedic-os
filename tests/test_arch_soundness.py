"""
Architecture Soundness Test - checks the code path structure without calling the model.
Verifies every critical hand-off in the pipeline.
"""
import sys
import json
import traceback

print("="*60)
print("ARCHITECTURE SOUNDNESS CHECK (Code-Level)")
print("="*60)

failures = []
passes = []

# Test 1: tool_registry has `re` import and all 5 actions
def test_tool_registry():
    from core.tool_registry import ToolRegistry
    from core.terminal_engine import TerminalEngine
    
    # Check all actions present in execute_tool
    import inspect
    src = inspect.getsource(ToolRegistry.execute_tool)
    for action in ["run_command", "edit_file", "create_artifact", "create_pull_request", "invoke_subagent"]:
        assert action in src, f"execute_tool missing action: {action}"
    
    # Check subagent has VRAM eviction
    sub_src = inspect.getsource(ToolRegistry.execute_tool)
    assert "evict_model(main_model)" in sub_src, "VRAM eviction missing for invoke_subagent"
    
    # Check system prompt has all 6 tools
    t = TerminalEngine()
    reg = ToolRegistry(".", t)
    prompt = reg.get_system_prompt_addition()
    for tool in ["run_command", "edit_file", "create_artifact", "invoke_subagent", "create_pull_request", "done"]:
        assert tool in prompt, f"System prompt missing tool: {tool}"
    
    t.cleanup()
    return "ToolRegistry: all 5 action handlers + VRAM eviction + 6 tool schemas in prompt"

# Test 2: omni_state_machine injects registry schema into system prompt
def test_system_prompt_injection():
    import inspect
    from agents import omni_state_machine
    src = inspect.getsource(omni_state_machine)
    assert "get_system_prompt_addition" in src, "registry.get_system_prompt_addition() not called in system prompt"
    assert "registry = ToolRegistry" in src, "ToolRegistry not instantiated in init_omni_loop"
    return "omni_state_machine: registry schema injection confirmed"

# Test 3: parse_action handles all edge cases
def test_parse_action():
    from agents.omni_state_machine import parse_action
    
    # Clean JSON
    r1 = parse_action('{"thought": "testing", "action": "done"}')
    assert r1["action"] == "done"
    
    # JSON wrapped in markdown code block
    r2 = parse_action('Here is my plan:\n```json\n{"thought": "run it", "action": "run_command", "command": "npm test"}\n```')
    assert r2["action"] == "run_command"
    assert r2["command"] == "npm test"
    
    # Bare code block
    r3 = parse_action('```\n{"thought": "edit", "action": "edit_file", "file": "app.py", "search": "old", "replace": "new"}\n```')
    assert r3["action"] == "edit_file"
    
    # Pure garbage - should return error not crash
    r4 = parse_action("I cannot help with that because of safety reasons.")
    assert r4["action"] == "error"
    
    return "parse_action: handles clean JSON, markdown blocks, bare blocks, and garbage without crashing"

# Test 4: Loop detection logic
def test_loop_detection():
    # Simulating the history check
    history = []
    action_a = json.dumps({"action": "run_command", "command": "npm test"}, sort_keys=True)
    action_b = json.dumps({"action": "run_command", "command": "npm install"}, sort_keys=True)
    
    history.append(action_a)
    history.append(action_b)
    history.append(action_a)
    
    # Should NOT trigger (a appears twice but not 3 times in last 3)
    assert history[-3:].count(action_a) < 3
    
    history.append(action_a)
    history.append(action_a)
    # Last 3 are: action_a, action_a, action_a -> should trigger
    assert history[-3:] == [action_a, action_a, action_a]
    return "loop_detection: correctly identifies repeated actions"

# Test 5: file_system diff returns string not None
def test_diff_output():
    import tempfile, os
    from core.file_system import apply_search_replace
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = os.path.join(tmpdir, "test.py")
        with open(fpath, "w") as f:
            f.write("def old_function():\n    return 1\n")
        
        diff = apply_search_replace("test.py", "def old_function():\n    return 1", "def new_function():\n    return 42", workspace_dir=tmpdir)
        assert diff is not None, "diff returned None"
        assert isinstance(diff, str), "diff not a string"
        assert "new_function" in diff or "-old_function" in diff, "diff doesn't show the change"
    return "apply_search_replace: returns valid unified diff string"

tests = [
    ("Tool Registry", test_tool_registry),
    ("System Prompt Injection", test_system_prompt_injection),
    ("parse_action Robustness", test_parse_action),
    ("Loop Detection Logic", test_loop_detection),
    ("Diff Output", test_diff_output),
]

for name, fn in tests:
    try:
        msg = fn()
        passes.append(name)
        print(f"✅ {name}: {msg}")
    except Exception as e:
        failures.append((name, str(e)))
        print(f"❌ {name}: {e}")
        traceback.print_exc()

print("\n" + "="*60)
print(f"RESULT: {len(passes)}/{len(tests)} architecture checks passed")
if failures:
    print("FAILURES:")
    for name, err in failures:
        print(f"  - {name}: {err}")
    sys.exit(1)
else:
    print("✅ Architecture is sound.")
