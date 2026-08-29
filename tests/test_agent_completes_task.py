#!/usr/bin/env python3
"""
Acceptance test: can the agent actually finish a real job?

Everything else in tests/ checks a part in isolation. This drives the real loop
against a fixture repo containing a genuine bug, and judges the result the only
way that means anything: by running a verifier the agent did not write and is
told not to touch.

    python3 tests/test_agent_completes_task.py            # default task
    python3 tests/test_agent_completes_task.py --task fix_bug --steps 12
    python3 tests/test_agent_completes_task.py --model qwen3:4b-instruct-2507-q4_K_M

Pass means: verifier exits 0, and the verifier file is byte-identical to what it
started as. Editing the test to make it pass is a fail, not a pass.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.omni_state_machine import (  # noqa: E402
    generate_next_thought, init_omni_loop, parse_action,
)
from backend.vram_manager import enforce_context_window  # noqa: E402
from config import FAST_MODEL, INGEST_MODEL  # noqa: E402
from core.terminal_engine import TerminalEngine  # noqa: E402
from core.tool_registry import ToolRegistry  # noqa: E402

# ---------------------------------------------------------------- fixtures

BUGGY_CALC = '''\
"""Tiny arithmetic helpers."""


def add(a, b):
    return a - b


def multiply(a, b):
    return a + b
'''

VERIFIER = '''\
"""Verifier. The agent must make this exit 0 WITHOUT editing this file."""
import sys
from calc import add, multiply

failures = []
for name, got, want in [
    ("add(2, 3)", add(2, 3), 5),
    ("add(-1, 1)", add(-1, 1), 0),
    ("multiply(3, 4)", multiply(3, 4), 12),
    ("multiply(0, 9)", multiply(0, 9), 0),
]:
    if got != want:
        failures.append(f"{name} == {got}, expected {want}")

if failures:
    print("FAIL")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
'''

MISSING_FN_MOD = '''\
"""String helpers used across the project."""


def shout(text):
    return text.upper() + "!"
'''

MISSING_FN_VERIFIER = '''\
"""Verifier. The agent must make this exit 0 WITHOUT editing this file."""
import sys
from strings import shout, titlecase

failures = []
for name, got, want in [
    ("shout('hi')", shout("hi"), "HI!"),
    ("titlecase('hello world')", titlecase("hello world"), "Hello World"),
    ("titlecase('a')", titlecase("a"), "A"),
]:
    if got != want:
        failures.append(f"{name} == {got!r}, expected {want!r}")

if failures:
    print("FAIL")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
'''

TASKS = {
    "fix_bug": {
        "files": {"calc.py": BUGGY_CALC, "check.py": VERIFIER},
        "verifier": "check.py",
        "prompt": (
            "The file calc.py has two bugs: add() subtracts and multiply() adds. "
            "Run `python3 check.py` to see the failures, then fix calc.py so the "
            "checks pass. Do NOT edit check.py. When `python3 check.py` prints "
            "ALL CHECKS PASSED, output action done."
        ),
    },
    "add_function": {
        "files": {"strings.py": MISSING_FN_MOD, "check.py": MISSING_FN_VERIFIER},
        "verifier": "check.py",
        "prompt": (
            "check.py imports a function `titlecase` from strings.py that does not "
            "exist yet. Run `python3 check.py` to see the error, then add titlecase "
            "to strings.py so every check passes. It should capitalise the first "
            "letter of each word. Do NOT edit check.py. When `python3 check.py` "
            "prints ALL CHECKS PASSED, output action done."
        ),
    },
}


def build_fixture(task):
    ws = tempfile.mkdtemp(prefix="omni_task_")
    for name, body in task["files"].items():
        with open(os.path.join(ws, name), "w") as f:
            f.write(body)
    subprocess.run(["git", "init", "-q"], cwd=ws)
    for k, v in [("user.email", "t@t"), ("user.name", "t")]:
        subprocess.run(["git", "config", k, v], cwd=ws)
    subprocess.run(["git", "add", "-A"], cwd=ws)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=ws)
    return ws


def verifier_passes(ws, verifier):
    r = subprocess.run([sys.executable, verifier], cwd=ws, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def run_task(task_name, model, max_steps, verbose):
    task = TASKS[task_name]
    ws = build_fixture(task)
    vpath = os.path.join(ws, task["verifier"])
    verifier_sha_before = sha(vpath)

    ok, out = verifier_passes(ws, task["verifier"])
    assert not ok, "fixture is broken — the verifier passes before the agent runs"
    print(f"  fixture ready, verifier fails as expected: {out.splitlines()[0]}")

    messages, _ = init_omni_loop(task["prompt"], INGEST_MODEL, model, ws, None)
    registry = ToolRegistry(ws, TerminalEngine(ws))

    said_done = False
    steps_used = 0
    gateway_failures = 0
    t0 = time.time()

    for step in range(1, max_steps + 1):
        steps_used = step
        messages = enforce_context_window(messages, max_turns=6)
        raw = generate_next_thought(model, messages, None)
        messages.append({"role": "assistant", "content": raw})
        if "API Gateway Failure" in raw:
            gateway_failures += 1

        data = parse_action(raw)
        action = data.get("action")
        if verbose:
            print(f"  step {step:>2}: {action!r}")

        if action == "done":
            said_done = True
            break
        if not action or action == "error":
            messages.append({"role": "user", "content": "Your JSON was malformed. Output one ```json block."})
            continue
        if action == "ask_user":
            messages.append({"role": "user", "content": "No human is available. Decide yourself and continue."})
            continue

        result = registry.execute_tool(data, main_model=model)
        msg = result.get("msg", str(result))
        if verbose:
            print(f"           -> {msg[:100].splitlines()[0] if msg else ''}")
        messages.append({"role": "user", "content": f"Tool Execution Result:\n```\n{msg}\n```"})

    elapsed = time.time() - t0
    passed, out = verifier_passes(ws, task["verifier"])
    untouched = sha(vpath) == verifier_sha_before

    print(f"\n  verifier passes:   {passed}   ({out.splitlines()[0] if out else ''})")
    print(f"  verifier untouched: {untouched}")
    print(f"  agent said done:   {said_done}   steps={steps_used}/{max_steps}  {elapsed:.0f}s")
    if gateway_failures:
        print(f"  GATEWAY FAILURES:  {gateway_failures}")

    if not passed and verbose:
        print("\n  --- final state of the code the agent was asked to fix ---")
        for name in task["files"]:
            if name != task["verifier"]:
                print(f"  {name}:")
                for line in open(os.path.join(ws, name)).read().splitlines()[:20]:
                    print(f"    {line}")
    shutil.rmtree(ws, ignore_errors=True)
    return passed and untouched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=list(TASKS) + ["all"], default="all")
    ap.add_argument("--model", default=FAST_MODEL)
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    names = list(TASKS) if args.task == "all" else [args.task]
    results = {}
    for n in names:
        print(f"\n=== TASK: {n}   model={args.model} ===")
        results[n] = run_task(n, args.model, args.steps, not args.quiet)

    print("\n" + "=" * 62)
    for n, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {n}")
    passed = sum(results.values())
    print(f"  {passed}/{len(results)} tasks completed")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
