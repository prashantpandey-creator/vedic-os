#!/usr/bin/env python3
"""
Deferred benchmark — RUN ON AN IDLE MACHINE.

Loads two ~4B models at long context. Peak resident memory is roughly 13 GB for
the transformer arm. Do not run this while you are working; the first attempt
killed the Ollama connection mid-run and produced one inconclusive row.

    python3 tests/bench_ssm_vs_transformer.py            # both suites
    python3 tests/bench_ssm_vs_transformer.py --copy     # copy fidelity only
    python3 tests/bench_ssm_vs_transformer.py --speed    # long-context only

Answers two questions, in order of what they decide:

  1. COPY FIDELITY (open — decides EDITOR_MODEL)
     Whole-file rewrite is a verbatim copy task, the known weak spot of
     state-space models. If granite degrades on long files it is the wrong
     EDITOR_MODEL regardless of its context window. Untested above 65 lines.

  2. LONG-CONTEXT THROUGHPUT (already answered — confirms INGEST_MODEL)
     At 44,891 tokens: granite 317 tok/s / 154s / 5.83GB
                       qwen3   112 tok/s / 423s / 12.71GB
     Re-run only to confirm on an idle box.

Writes docs/bench_results.md. See docs/MODEL_ROUTING.md for what to do with it.
"""
import argparse
import difflib
import os
import subprocess
import sys
import tempfile
import time

import requests

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from core.file_system import ingest_repository_to_text  # noqa: E402
from core.tool_registry import extract_code  # noqa: E402

OLLAMA = "http://127.0.0.1:11434"
SSM = "granite4:3b-h"                       # granitehybrid — Mamba-2 + attention
XFMR = "qwen3:4b-instruct-2507-q4_K_M"      # pure attention, comparable size/quant
MODELS = [SSM, XFMR]


def unload(model):
    """Evict so each arm pays its own cold-load cost. Without this the second
    arm reads as artificially fast off a warm KV cache — that contaminated the
    first run's 10K row (14,674 tok/s was a cache hit, not a measurement)."""
    try:
        requests.post(f"{OLLAMA}/api/generate", json={"model": model, "keep_alive": 0}, timeout=10)
    except Exception:
        pass
    time.sleep(3)


def resident_gb(model):
    for m in requests.get(f"{OLLAMA}/api/ps", timeout=5).json().get("models", []):
        if m["name"] == model:
            return m.get("size", 0) / 1e9
    return 0.0


def chat(model, content, num_predict, num_ctx):
    return requests.post(
        f"{OLLAMA}/api/chat",
        json={"model": model, "messages": [{"role": "user", "content": content}],
              "stream": False,
              "options": {"num_predict": num_predict, "num_ctx": num_ctx, "temperature": 0}},
        timeout=3600,
    ).json()


def bench_speed(out):
    out.append("\n## Long-context throughput\n")
    out.append("| tokens | model | prefill tok/s | wall s | resident GB |")
    out.append("|---|---|---|---|---|")

    full = ingest_repository_to_text(workspace_dir=REPO, max_chars=60000)
    # Repeat the dump to reach sizes past the quadratic-vs-linear crossover.
    # 17K showed no gap; 44K showed 2.8x. 90K should widen it further.
    sizes = [(len(full), full), (200_000, (full * 3)[:200_000]), (390_000, (full * 5)[:390_000])]
    print(f"{'tokens':>8} {'model':<32}{'tok/s':>8}{'wall s':>9}{'GB':>7}", flush=True)

    for _, payload in sizes:
        for model in MODELS:
            unload(model)
            r = chat(model, payload + "\n\nList 5 bullets describing this codebase.", 40, 131072)
            if "error" in r:
                print(f"  {model}: ERROR {r['error'][:60]}", flush=True)
                out.append(f"| ? | {model} | ERROR | {r['error'][:40]} | |")
                continue
            pt = r["prompt_eval_count"]
            rate = pt / (r["prompt_eval_duration"] / 1e9)
            wall = r["total_duration"] / 1e9
            gb = resident_gb(model)
            print(f"{pt:>8} {model:<32}{rate:>8.0f}{wall:>9.1f}{gb:>7.2f}", flush=True)
            out.append(f"| {pt} | {model} | {rate:.0f} | {wall:.1f} | {gb:.2f} |")


def bench_copy(out):
    """THE ONE THAT DECIDES EDITOR_MODEL. Rewrite whole files of increasing length
    with a trivial change; measure how much survives verbatim and whether
    write_verified() would accept the result."""
    out.append("\n## Copy fidelity (whole-file rewrite)\n")
    out.append("| file | lines | model | out lines | kept % | write_verified |")
    out.append("|---|---|---|---|---|---|")

    targets = [
        ("core/memory_graph.py", "add a one-line docstring to append_vritti"),
        ("core/checkpoint.py", "add a one-line docstring to clear_checkpoints"),
        ("core/terminal_engine.py", "add a one-line docstring to cleanup"),
        ("core/file_system.py", "add a one-line docstring to build_tree_with_hints"),
        ("core/tool_registry.py", "add a one-line docstring to get_system_prompt_addition"),
        ("cli.py", "add a one-line docstring to run_cli"),
    ]
    print(f"{'file':<26}{'lines':>6} {'model':<32}{'kept':>7}  verdict", flush=True)

    for rel, instr in targets:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            continue
        orig = open(path).read()
        old_lines = orig.splitlines()
        for model in MODELS:
            unload(model)
            prompt = (f"Instruction: {instr}\n\nCURRENT CODE:\n```\n{orig}\n```\n\n"
                      "Rewrite the code to fulfill the instruction. Output ONLY the "
                      "complete updated code inside ``` blocks. Do not omit any part "
                      "of the file.")
            try:
                r = chat(model, prompt, 16384, 65536)
                new = extract_code(r.get("message", {}).get("content", ""))
            except Exception as e:
                print(f"{rel:<26}{len(old_lines):>6} {model:<32}  CRASH {str(e)[:30]}", flush=True)
                out.append(f"| {rel} | {len(old_lines)} | {model} | — | — | CRASHED |")
                continue

            new_lines = new.splitlines()
            kept = sum(b.size for b in difflib.SequenceMatcher(None, old_lines, new_lines)
                       .get_matching_blocks())
            pct = 100 * kept / max(len(old_lines), 1)

            # Mirror write_verified()'s gates exactly.
            if not new.strip():
                verdict = "REJECT empty"
            elif len(new) < len(orig) * 0.4:
                verdict = f"REJECT truncated {len(new)}/{len(orig)}"
            else:
                tf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
                tf.write(new)
                tf.close()
                rc = subprocess.run(["python3", "-m", "py_compile", tf.name], capture_output=True)
                verdict = "ACCEPT" if rc.returncode == 0 else "REJECT syntax"
                os.unlink(tf.name)

            print(f"{rel:<26}{len(old_lines):>6} {model:<32}{pct:>6.0f}%  {verdict}", flush=True)
            out.append(f"| {rel} | {len(old_lines)} | {model} | {len(new_lines)} | {pct:.0f}% | {verdict} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--copy", action="store_true", help="copy fidelity only")
    ap.add_argument("--speed", action="store_true", help="long-context only")
    args = ap.parse_args()

    try:
        have = {m["name"] for m in requests.get(f"{OLLAMA}/api/tags", timeout=5).json()["models"]}
    except Exception as e:
        sys.exit(f"Ollama unreachable at {OLLAMA}: {e}")
    missing = [m for m in MODELS if m not in have]
    if missing:
        sys.exit(f"Missing models: {missing}. Pull them first.")

    out = [f"# Benchmark results\n\nSSM: `{SSM}` (granitehybrid) vs transformer: `{XFMR}`\n"]
    if not args.copy:
        bench_speed(out)
    if not args.speed:
        bench_copy(out)

    dest = os.path.join(REPO, "docs", "bench_results.md")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w") as f:
        f.write("\n".join(out) + "\n")
    print(f"\nWrote {dest}")


if __name__ == "__main__":
    main()
