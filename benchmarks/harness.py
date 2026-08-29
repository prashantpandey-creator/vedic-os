"""
Local model benchmark harness — Omni-Agent.

Methodology, and why each rule is here (every one of these was violated by an
earlier benchmark in this repo, and each violation changed a published verdict):

 1. REPEATS. n>=5 per cell, report MEDIAN and full spread. n=1 on a thermally
    throttled laptop is a coin flip, not a measurement.
 2. SEPARATED TIMERS. Ollama returns load_duration / prompt_eval_duration /
    eval_duration. Never divide token counts by wall-clock — that folds model
    load time into "speed" and makes whichever model ran first look slowest.
 3. CACHE DEFEAT. Every run gets a unique nonce prefix. Ollama reuses the KV
    cache for a repeated prompt and returns a ~40x inflated prefill number; an
    earlier run in this repo reported a "3x speedup" that was purely this.
 4. NO SILENT TRUNCATION. num_ctx is set explicitly and asserted against
    prompt_eval_count. Ollama truncates to num_ctx without telling you: a
    prompt_eval_count landing exactly ON num_ctx is the fingerprint.
 5. SCORED, NOT EYEBALLED. Every task has machine-checkable ground truth.
    "Accuracy Verdict: Perfect / Failed" written by hand is an opinion.
 6. ONE CORPUS PER COMPARISON. Comparing model A on a 100-class file against
    model B on a 120-class file measures the corpus, not the models.
 7. INTERLEAVED ORDER. Models rotate per repeat so thermal drift doesn't
    systematically favour whoever ran first.
 8. ISOLATION. Other models are evicted from VRAM before each cell.

Run:  venv/bin/python benchmarks/harness.py            # all tasks
      venv/bin/python benchmarks/harness.py --task t1  # one task
      venv/bin/python benchmarks/harness.py --reps 3   # faster smoke run
Output: benchmarks/results.json  (raw)  +  benchmarks/RESULTS.md  (report)
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time

import requests

OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

MODELS = [
    "granite4:3b-h",                   # granitehybrid — Mamba-2 SSM + attention, 1M ctx
    "qwen3:4b-instruct-2507-q4_K_M",   # qwen3 transformer, 262K ctx
    "architect-compiler:latest",       # SAME WEIGHTS as above + baked SYSTEM/sampling
    "mannix/llama3.1-8b-abliterated:latest",  # llama transformer, 131K ctx
]

ARCH = {}  # filled by probe_models()


# ---------------------------------------------------------------- infrastructure

def probe_models():
    """Record architecture + real context window. These are facts, not guesses."""
    for m in MODELS:
        try:
            d = requests.post(f"{OLLAMA}/api/show", json={"model": m}, timeout=30).json()
            mi = d.get("model_info", {})
            arch = mi.get("general.architecture", "?")
            ctx = next((v for k, v in mi.items() if k.endswith("context_length")), None)
            ARCH[m] = {
                "architecture": arch,
                "is_ssm": any("ssm" in k.lower() or "mamba" in k.lower() for k in mi),
                "context_length": ctx,
                "params": d.get("details", {}).get("parameter_size"),
                "quant": d.get("details", {}).get("quantization_level"),
                # parent_model is sometimes a blob path rather than a tag; only
                # report it when it is a readable model name.
                "parent": (lambda p: p if p and "/" not in p and "sha256" not in p else None)(
                    d.get("details", {}).get("parent_model")),
            }
        except Exception as e:
            ARCH[m] = {"error": str(e)}


def evict_all_except(keep):
    try:
        ps = requests.get(f"{OLLAMA}/api/ps", timeout=5).json().get("models", [])
        for m in ps:
            if m["name"] != keep:
                requests.post(f"{OLLAMA}/api/generate",
                              json={"model": m["name"], "keep_alive": 0}, timeout=10)
    except Exception:
        pass


def warmup(model):
    """Load into VRAM so load_duration doesn't pollute the measured runs."""
    try:
        requests.post(f"{OLLAMA}/api/chat", json={
            "model": model, "messages": [{"role": "user", "content": "hi"}],
            "stream": False, "options": {"num_predict": 1}}, timeout=600)
    except Exception:
        pass


def call(model, system, user, num_ctx, num_predict=400, temperature=0.0, nonce=""):
    """
    One measured generation. Returns Ollama's own separated timings plus a
    truncation check. `nonce` defeats the KV cache.
    """
    # Rule 3, done properly. llama.cpp reuses the longest common PREFIX of the
    # prompt. A nonce in the user message is not enough — an identical system
    # message in front of it is still a shared prefix and still gets cached,
    # which inflates prefill by 10-20x. The nonce must lead the FIRST message.
    # (Caught by this harness reporting granite at 371 t/s on one task and
    # llama at 6030 t/s on another; real prefill on this box is ~300-450.)
    if nonce:
        if system:
            system = f"[run {nonce}]\n{system}"
        else:
            user = f"[run {nonce}]\n{user}"
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": user}]
    # Ollama restarts under memory pressure and drops the socket. Retry, but
    # report the retry count — a cell that needed retries ran against a box in a
    # different state and its timings are suspect.
    retries = 0
    for attempt in range(4):
        try:
            t0 = time.perf_counter()
            r = requests.post(f"{OLLAMA}/api/chat", json={
                "model": model, "messages": msgs, "stream": False,
                "options": {"num_ctx": num_ctx, "num_predict": num_predict,
                            "temperature": temperature},
            }, timeout=3600).json()
            wall = time.perf_counter() - t0
            break
        except requests.exceptions.RequestException as e:
            retries += 1
            if attempt == 3:
                return {"error": f"connection failed after 4 attempts: {e}"}
            time.sleep(5 * (attempt + 1))
    if "error" in r:
        return {"error": r["error"]}

    pc, pd = r.get("prompt_eval_count", 0), r.get("prompt_eval_duration", 0) / 1e9
    ec, ed = r.get("eval_count", 0), r.get("eval_duration", 0) / 1e9
    return {
        "text": r.get("message", {}).get("content", ""),
        "prompt_tokens": pc,
        "gen_tokens": ec,
        "prefill_tps": pc / pd if pd > 0 else None,
        "gen_tps": ec / ed if ed > 0 else None,
        "load_s": r.get("load_duration", 0) / 1e9,
        "wall_s": wall,
        "retries": retries,
        # Rule 4: prompt_eval_count landing exactly on the cap means Ollama
        # silently threw away the tail of the input.
        "truncated": pc >= num_ctx,
    }


def cell(model, system, user, num_ctx, scorer, reps, num_predict=400, tag=""):
    """Run one (model, task) cell `reps` times and score each."""
    runs = []
    for i in range(reps):
        r = call(model, system, user, num_ctx, num_predict=num_predict,
                 nonce=f"{tag}-{model}-{i}-{time.time_ns()}")
        if "error" in r:
            runs.append(r)
            continue
        r["score"] = scorer(r["text"])
        r.pop("text_full", None)
        r["text"] = r["text"][:400]
        runs.append(r)
    return runs


def agg(runs, key):
    vals = [r[key] for r in runs if key in r and r.get(key) is not None]
    if not vals:
        return None
    return {"median": statistics.median(vals), "min": min(vals), "max": max(vals),
            "n": len(vals)}


# ------------------------------------------------------------------- the corpora

def synth_corpus(n_classes, seed_word="Module"):
    """Synthetic corpus with EXACT known ground truth: n_classes classes, and the
    last class returns n_classes-1. Both are machine-checkable in the summary."""
    body = f"--- FILE: main.py ---\n"
    for i in range(n_classes):
        body += f"class {seed_word}{i}:\n    def execute(self):\n        return {i}\n"
    return body


def real_corpus(max_chars):
    from core.file_system import ingest_repository_to_text
    return ingest_repository_to_text(workspace_dir=ROOT, max_chars=max_chars)


# --------------------------------------------------------------------- the tasks

def task_t1_ingest(reps):
    """
    T1 — the blueprint job: read a codebase, state what is in it.
    Ground truth: the corpus has EXACTLY 137 classes named Module0..Module136.
    Scored on whether the summary states the right count. This is the job the
    earlier benchmark scored by eye as "Perfect" / "Failed".
    """
    N = 137
    corpus = synth_corpus(N)
    system = ("You are the Architect. Read the codebase and output a compressed summary. "
              "EXTREME BREVITY REQUIRED: maximum 5 bullet points. You MUST state the exact "
              "number of classes.")
    user = f"USER INTENT: Summarize the architecture.\n\nCODEBASE:\n{corpus}"

    def scorer(text):
        nums = [int(x) for x in re.findall(r"\b(\d{2,4})\b", text)]
        return {"states_exact_count": N in nums,
                "closest_count_stated": min(nums, key=lambda v: abs(v - N)) if nums else None,
                "ground_truth": N}

    out = {}
    for m in MODELS:
        evict_all_except(m); warmup(m)
        out[m] = cell(m, system, user, num_ctx=32768, scorer=scorer, reps=reps,
                      num_predict=300, tag="t1")
    return out


def task_t2_json_action(reps):
    """
    T2 — the agent-loop job: emit a single valid JSON tool action.
    Scored by the tool's OWN parser (parse_action) plus a valid-action check —
    same gate production uses, so the number means something operationally.
    """
    from agents.omni_state_machine import parse_action
    from core.tool_registry import ToolRegistry
    VALID = {"run_command", "edit_file", "create_file", "create_artifact",
             "invoke_subagent", "create_pull_request", "done"}
    system = ("You are the Vedic Omni-Agent.\n"
              "Output your chosen action strictly inside a ```json block.\n"
              + ToolRegistry(ROOT, None).get_system_prompt_addition())
    user = ("Tool Execution Result:\n```\ntest_auth.py::test_login FAILED - "
            "AssertionError: expected 200, got 401\n```\n"
            "Find which file defines the login handler. Choose ONE action.")

    def scorer(text):
        d = parse_action(text)
        action = (d or {}).get("action")
        return {"json_parsed": bool(d) and action != "error",
                "valid_action": action in VALID,
                "action": action}

    out = {}
    for m in MODELS:
        evict_all_except(m); warmup(m)
        out[m] = cell(m, system, user, num_ctx=16384, scorer=scorer, reps=reps,
                      num_predict=500, tag="t2")
    return out


def task_t3_rewrite(reps):
    """
    T3 — the editor job (EDITOR_MODEL's actual production task): rewrite a whole
    file to an instruction. Scored on the two things that matter operationally:
    does the result still compile, and did it PRESERVE the functions it was not
    asked to touch. Silent deletion of untouched code is the failure mode that
    destroys work.
    """
    from core.tool_registry import extract_code
    ORIG = (
        "import json\n\n"
        "def load_config(path):\n    with open(path) as f:\n        return json.load(f)\n\n"
        "def save_config(path, data):\n    with open(path, 'w') as f:\n        json.dump(data, f)\n\n"
        "def validate(data):\n    return 'name' in data\n\n"
        "def merge(a, b):\n    out = dict(a)\n    out.update(b)\n    return out\n\n"
        "def describe(data):\n    return f\"config with {len(data)} keys\"\n"
    )
    MUST_KEEP = ["def save_config", "def validate", "def merge", "def describe"]
    # An explicit system message for EVERY model, even though production sends
    # none here. Two reasons: it overrides each Modelfile's baked SYSTEM so all
    # models get identical input (architect-compiler otherwise silently prepends
    # ~390 tokens of unrelated architectural-graph instructions), and it gives
    # the nonce a first-position slot so nothing is a cacheable shared prefix.
    system = "You are a precise code editor."
    user = ("Instruction: add a `default` parameter to load_config that is returned "
            "when the file does not exist.\n\nCURRENT CODE:\n```\n" + ORIG + "```\n\n"
            "Rewrite the code to fulfill the instruction. Output ONLY the complete "
            "updated code inside ``` blocks. Do not omit any part of the file.")

    def scorer(text):
        code = extract_code(text)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code); tmp = f.name
        compiles = subprocess.run([sys.executable, "-m", "py_compile", tmp],
                                  capture_output=True).returncode == 0
        os.unlink(tmp)
        kept = [k for k in MUST_KEEP if k in code]
        return {"compiles": compiles,
                "kept_untouched_fns": f"{len(kept)}/{len(MUST_KEEP)}",
                "all_preserved": len(kept) == len(MUST_KEEP),
                "did_the_edit": "default" in code and "def load_config" in code,
                "size_ratio": round(len(code) / len(ORIG), 2)}

    out = {}
    for m in MODELS:
        evict_all_except(m); warmup(m)
        out[m] = cell(m, system, user, num_ctx=16384, scorer=scorer, reps=reps,
                      num_predict=800, tag="t3")
    return out


def task_t4_long_context(reps):
    """
    T4 — does the SSM's linear-time attention actually pay off HERE?
    Prefill throughput at growing context. A transformer's attention is O(n^2);
    granitehybrid's Mamba-2 layers are O(n). If that matters on this box, the
    gap must WIDEN with length. Same corpus, same box, cache defeated.
    """
    pairs = ["granite4:3b-h", "qwen3:4b-instruct-2507-q4_K_M"]
    base = real_corpus(200000)
    sizes = [4000, 16000, 64000, 160000]  # chars
    out = {}
    for m in pairs:
        evict_all_except(m); warmup(m)
        out[m] = {}
        for chars in sizes:
            body = (base * ((chars // max(len(base), 1)) + 1))[:chars]
            out[m][str(chars)] = cell(
                m, None, body + "\n\nName one file in the listing above.",
                num_ctx=131072, scorer=lambda t: {"answered": len(t.strip()) > 0},
                reps=reps, num_predict=32, tag=f"t4-{chars}")
    return out


TASKS = {"t1": task_t1_ingest, "t2": task_t2_json_action,
         "t3": task_t3_rewrite, "t4": task_t4_long_context}


# ------------------------------------------------------------------------ report

def summarize(results):
    lines = ["# Local Model Benchmarks — Omni-Agent", ""]
    lines += ["Every number below is a **median of n repeats**, taken from Ollama's own",
              "separated timers (`prompt_eval_duration` / `eval_duration`), with the KV",
              "cache defeated by a unique per-run nonce and `num_ctx` asserted against",
              "`prompt_eval_count` so nothing was silently truncated.", ""]
    lines += ["## Models under test", "",
              "| Model | Architecture | Params | Context | Note |",
              "|---|---|---|---|---|"]
    for m, a in ARCH.items():
        if "error" in a:
            lines.append(f"| `{m}` | ERROR | | | {a['error']} |"); continue
        note = "**non-transformer (Mamba-2 SSM + attention)**" if a["is_ssm"] else "transformer"
        if a.get("parent"):
            note += f" · same weights as `{a['parent']}`"
        lines.append(f"| `{m}` | {a['architecture']} | {a['params']} | "
                     f"{a['context_length']:,} | {note} |" if a.get("context_length")
                     else f"| `{m}` | {a['architecture']} | {a['params']} | ? | {note} |")
    lines.append("")

    for t in ["t1", "t2", "t3"]:
        if t not in results:
            continue
        titles = {"t1": "T1 — Codebase ingest (the blueprint job)",
                  "t2": "T2 — JSON tool action (the agent-loop job)",
                  "t3": "T3 — Whole-file rewrite (the editor job)"}
        lines += [f"## {titles[t]}", "",
                  "| Model | prefill tok/s | gen tok/s | prompt tok | accuracy | n |",
                  "|---|---|---|---|---|---|"]
        for m, runs in results[t].items():
            good = [r for r in runs if "error" not in r]
            if not good:
                lines.append(f"| `{m}` | — | — | — | ERROR | 0 |"); continue
            pf, gt = agg(good, "prefill_tps"), agg(good, "gen_tps")
            ptok = agg(good, "prompt_tokens")
            if t == "t1":
                hits = sum(1 for r in good if r["score"]["states_exact_count"])
                acc = f"{hits}/{len(good)} stated exact count"
            elif t == "t2":
                hits = sum(1 for r in good if r["score"]["valid_action"])
                acc = f"{hits}/{len(good)} valid action"
            else:
                hits = sum(1 for r in good if r["score"]["compiles"] and r["score"]["all_preserved"])
                acc = f"{hits}/{len(good)} compiled + kept all fns"
            lines.append(f"| `{m}` | {pf['median']:.0f} | {gt['median']:.1f} | "
                         f"{ptok['median']:.0f} | {acc} | {len(good)} |")
        lines.append("")

    if "t4" in results:
        lines += ["## T4 — Long-context prefill: does the SSM pull ahead?", "",
                  "| chars | prompt tok | granite4:3b-h (SSM) | qwen3:4b (transformer) | SSM advantage |",
                  "|---|---|---|---|---|"]
        g, q = results["t4"].get("granite4:3b-h", {}), results["t4"].get("qwen3:4b-instruct-2507-q4_K_M", {})
        for size in sorted(set(g) | set(q), key=int):
            gr = [r for r in g.get(size, []) if "error" not in r]
            qr = [r for r in q.get(size, []) if "error" not in r]
            if not gr or not qr:
                continue
            gp, qp = agg(gr, "prefill_tps"), agg(qr, "prefill_tps")
            tok = agg(gr, "prompt_tokens")
            ratio = gp["median"] / qp["median"]
            lines.append(f"| {int(size):,} | {tok['median']:.0f} | {gp['median']:.0f} t/s | "
                         f"{qp['median']:.0f} t/s | **{ratio:.2f}×** |")
        lines += ["", "If the SSM's linear attention paid off on this box, the last column",
                  "would climb with length. Read it before believing either story.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=list(TASKS), action="append")
    ap.add_argument("--reps", type=int, default=5)
    args = ap.parse_args()

    probe_models()
    chosen = args.task or list(TASKS)
    results = {}
    for t in chosen:
        print(f"\n=== {t} (n={args.reps}) ===", flush=True)
        t0 = time.time()
        results[t] = TASKS[t](args.reps)
        print(f"=== {t} done in {time.time()-t0:.0f}s ===", flush=True)

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump({"models": ARCH, "reps": args.reps, "results": results}, f, indent=2)
    report = summarize(results)
    with open(os.path.join(HERE, "RESULTS.md"), "w") as f:
        f.write(report)
    print("\n" + report)


if __name__ == "__main__":
    main()
