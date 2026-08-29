# Audit of the earlier benchmarks in this repo

Reviewing `benchmark_architect.py`, `benchmark_base_vs_custom.py`,
`strict_benchmark.py`, `tests/zero_shot_benchmark.py`, and the published
`benchmarks/architect_ingestion_results.md`.

Everything below was checked by running commands against the live Ollama on this
box, not by reading the code alone. Where a published claim is wrong, the
measurement that contradicts it is given in the same line.

---

## What the earlier work got right

Credit first, because two of these are genuinely good and the good parts should
survive into whatever gets published.

**`strict_benchmark.py` is the correct shape.** It warms the model into VRAM
before timing, and it reads Ollama's own separated timers (`load_duration`,
`prompt_eval_duration`, `eval_duration`) instead of dividing tokens by wall
clock. That is the right instinct and most people never get there.

**Its Part 2 conclusion is right, and self-correcting.** The published doc says
the earlier "3× speedup" for `architect-compiler` was an illusion caused by
Ollama reusing the KV cache, and that the custom model shares the base model's
throughput ceiling. That is correct — the two share byte-identical weights
(`architect-compiler`'s parent is `qwen3:4b-instruct-2507-q4_K_M`) and cannot
differ in throughput. Publishing a retraction of your own earlier number is the
hardest thing on this list.

**`tests/zero_shot_benchmark.py` is the best-designed file in the suite.** Real
repair tasks, real `unittest` pass/fail, machine-scored. That is a benchmark;
the others are demos.

---

## What has to be fixed before publishing

### 1. The headline verdict on Granite is attributed to a cause that cannot exist

Published:

> **granite4:3b-h (IBM)** — *Failed.* Hallucinated halfway through the file due
> to **context limits**.

and the winner's reason:

> Its 256K token context window easily swallows the entire repository.

Measured, on the exact corpus `benchmark_architect.py` builds:

| Model | prompt tokens used | model's real context window |
|---|---|---|
| `architect-compiler:latest` | 1,614 | 262,144 |
| `granite4:3b-h` | **1,433** | **1,048,576** |
| `mannix/llama3.1-8b-abliterated` | 1,441 | 131,072 |

The harness also capped everything at `num_ctx: 8000` anyway.

Nothing was context-limited — the corpus used **0.14 %** of Granite's window.
And Granite has the **largest** context of the three, four times the winner's.
It was ranked last for the one property on which it ranks first. The failure may
well be real; the stated cause is off by 730×, and context capacity was never
exercised by this test at all.

### 2. The two models in Part 2 are the same model

`architect-compiler:latest` reports `parent_model:
qwen3:4b-instruct-2507-q4_K_M`. Identical weights. It differs only by a baked
`SYSTEM` prompt and sampling params (`top_k 20`, `top_p 0.8`,
`repeat_penalty 1`, `temperature 0.7`).

Both benchmarks then send **their own** system message — which overrides the
Modelfile `SYSTEM` — and pass `"temperature": 0.1` in options, which overrides
the baked sampling. So every distinguishing feature was neutralised at call
time. Part 2 benchmarked one model against itself. Its finding that they perform
identically is therefore true but circular.

*This matters in production too:* `init_omni_loop` sends its own system message,
so the baked architectural-graph SYSTEM in `architect-compiler` never applies
there either. Measured side effect: when no system message is sent,
`architect-compiler` silently prepends ~390 tokens of unrelated instructions.

### 3. n = 1, and the noise floor is 2.2×

Every earlier run measured each model exactly once.

Measured here at n=5, `qwen3:4b-instruct` vs `architect-compiler` — **the same
weights, so any gap is pure measurement noise**:

| Task | qwen3:4b median prefill | architect-compiler median prefill | apparent gap |
|---|---|---|---|
| T1 ingest | 204 t/s | 398 t/s | 1.95× |
| T2 JSON action | 408 t/s | 189 t/s | 2.16× **(rank flips)** |
| T3 rewrite | 319 t/s | 291 t/s | 1.10× |

Worst within-model spread across 5 runs: **3.2×**.

So on this box, **any throughput difference under roughly 2.2× is noise**, and
the ranking can invert between tasks for identical models. The published
comparisons — 8.04 s vs 9.91 s vs 24.93 s, 8.1 vs 14.3 vs 4.0 t/s, 395.1 vs
395.1 t/s — all sit at or below that floor. None of them are measurable at n=1.

### 4. Speed was computed from wall clock, folding in model load time

`benchmark_architect.py` and `benchmark_base_vs_custom.py` both do
`speed = eval_count / (time.time() - start)`. That denominator includes the HTTP
round trip and, for a cold model, the multi-second VRAM load. Models are tested
in sequence, so whoever runs first pays the load and looks slowest. This is the
most likely source of `llama3.1-8b`'s reported "4.0 tokens/sec" and its verdict
of "extreme prompt processing lag".

`strict_benchmark.py` already avoids this. The other two were not updated.

### 5. The KV cache was never actually defeated

`benchmark_base_vs_custom.py` carries the comment *"slightly different to prevent
caching"* — but it changes the corpus **between models**, not between runs, which
does nothing about caching and instead breaks comparability (see 6).

This one is subtle enough that **this harness fell into it too on its first
run**: a per-run nonce was placed in the *user* message while the *system*
message stayed identical, and llama.cpp still cached the shared system prefix.
That produced 6,030 t/s for a model that really runs at ~240. Moving the nonce
to the front of the *first* message fixed it — and T1 went from 198 s to 611 s,
which is the proof the cache had been doing the work. Any prefill number above
~450 t/s on this hardware is a cache hit, not a measurement.

### 6. Part 1 and Part 2 use different corpora and are presented as one study

Part 1 ingests 100 `Module` classes. Part 2 ingests 120 `Service` classes. The
published doc puts them in a single report under one conclusion. Different
inputs measure different things.

### 7. "Accuracy Verdict" is prose, not a score

*Perfect* / *Failed* / *off-by-one hallucination* were written by hand from
reading truncated 150-character output snippets. The corpus is synthetic with
exact ground truth available — the number of classes is known, so the check can
be automatic. This harness scores it: does the summary state the correct count.

### 8. A published comparison column is hardcoded

`tests/zero_shot_benchmark.py` prints a table whose **"Score (With Harness)"**
column is:

```python
harness_score = "1/2 (Logic Only)" if "llama3.1" in model else "TBD"
```

That is a literal, not a measurement, printed into a results table next to real
measured numbers.

### 9. "We directly hooked into the GPU metrics"

The published Part 2 says it bypassed Ollama's VRAM caching by hooking GPU
metrics. `strict_benchmark.py` does a warm-up call and reads Ollama's JSON
timing fields. That is a reasonable method and it is **not** GPU metrics. The
description overstates what the script does.

### 10. `tests/coder_benchmark.py` does nothing

```python
def run_benchmark(verbose=False):
    print("Running Benchmark...")
```

It defines a VRAM-clearing helper that is never called, then prints a string. It
is in the tests directory as though it measures something.

---

## Fix list, in order of how much a published claim depends on it

1. Retract the "context limits" explanation for Granite — measured 1,433 tokens
   against a 1,048,576 window.
2. Stop comparing `architect-compiler` to `qwen3:4b-instruct` as two models.
3. n ≥ 5, report median and spread; treat anything under 2.2× as a tie.
4. Use Ollama's separated timers everywhere, not wall clock.
5. Defeat the cache with a nonce in the **first** message.
6. One corpus per comparison.
7. Score accuracy by machine against known ground truth.
8. Delete the hardcoded harness column or measure it.
