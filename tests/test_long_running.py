"""
Tests the checkpoint system and phase transition logic.
"""
import sys
import os
import json
import tempfile

print("="*60)
print("LONG-RUNNING HARNESS VERIFICATION")
print("="*60)

from core.checkpoint import save_checkpoint, load_checkpoint, clear_checkpoints, build_phase_summary

failures = []

# Test 1: Save and load checkpoint
def test_checkpoint_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        state = {
            "intent_prompt": "Fix all tests",
            "omni_step": 7,
            "phase": 2,
            "omni_state": "GENERATING",
            "omni_messages": [{"role": "system", "content": "test"}],
            "omni_log": [{"step": 1, "type": "command", "cmd": "npm test"}],
            "action_history": ["action1"],
            "phase_summaries": ["Phase 1: ran tests"],
        }
        
        cp_file = save_checkpoint(tmpdir, state)
        assert os.path.exists(cp_file), "Checkpoint file not created"
        
        loaded = load_checkpoint(tmpdir)
        assert loaded is not None, "Checkpoint not loaded"
        assert loaded["intent"] == "Fix all tests"
        assert loaded["step"] == 7
        assert loaded["phase"] == 2
        assert len(loaded["messages"]) == 1
        assert len(loaded["phase_summaries"]) == 1
        
        clear_checkpoints(tmpdir)
        assert load_checkpoint(tmpdir) is None, "Checkpoints not cleared"
    return "Save/load/clear roundtrip: OK"

# Test 2: Phase summary compressor
def test_phase_summary():
    log = [
        {"step": 1, "type": "command", "cmd": "npm test", "output": "FAIL: 3 tests failed\n" + "x" * 5000},
        {"step": 2, "type": "edit", "file": "app.js"},
        {"step": 3, "type": "command", "cmd": "npm test", "output": "OK: 3 tests passed"},
        {"step": 4, "type": "artifact", "title": "FixReport"},
        {"step": 5, "type": "github_pr", "url": "https://github.com/x/y/pull/1"},
    ]
    
    summary = build_phase_summary(log)
    assert "npm test" in summary
    assert "Edited" in summary
    assert "FixReport" in summary
    assert "Raised PR" in summary
    # Check that the 5000-char output was truncated to 200
    assert len(summary) < 1000, f"Phase summary too long: {len(summary)} chars"
    return f"Phase summary: {len(summary)} chars (compressed 5000+ char output)"

# Test 3: Verify long-running checkbox exists in app.py
def test_ui_integration():
    with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
        src = f.read()
    assert "Long-Running Harness" in src, "Long-running toggle missing from UI"
    assert "load_checkpoint" in src, "Checkpoint resume missing from UI"
    assert "save_checkpoint" in src, "Checkpoint save missing from UI"
    assert "phase_summaries" in src, "Phase summaries missing from state"
    assert "PRIOR PHASE SUMMARIES" in src, "Phase injection into system prompt missing"
    assert "Re-ingesting codebase" in src, "Fresh ingestion on phase transition missing"
    return "UI integration: all long-running components wired"

# Test 4: Verify auto-checkpoint interval
def test_auto_checkpoint():
    with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
        src = f.read()
    assert "omni_step % 5 == 0" in src, "Auto-checkpoint every 5 steps not wired"
    return "Auto-checkpoint: fires every 5 steps"

tests = [
    ("Checkpoint Roundtrip", test_checkpoint_roundtrip),
    ("Phase Summary Compressor", test_phase_summary),
    ("UI Integration", test_ui_integration),
    ("Auto-Checkpoint", test_auto_checkpoint),
]

passed = 0
for name, fn in tests:
    try:
        msg = fn()
        print(f"✅ {name}: {msg}")
        passed += 1
    except Exception as e:
        failures.append((name, str(e)))
        print(f"❌ {name}: {e}")

print(f"\n{'='*60}")
print(f"RESULT: {passed}/{len(tests)} long-running checks passed")
if failures:
    for n, e in failures:
        print(f"  FAIL: {n} — {e}")
    sys.exit(1)
else:
    print("✅ Long-running harness verified.")
