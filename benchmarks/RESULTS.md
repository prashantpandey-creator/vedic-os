# Local Model Benchmarks — Omni-Agent

Run on the development Mac against Ollama 0.15.1, 2026-08-29.
Harness: [`benchmarks/harness.py`](harness.py) · raw data: [`results.json`](results.json)
Audit of the previous benchmarks in this repo: [`METHODOLOGY_AUDIT.md`](METHODOLOGY_AUDIT.md)

Every number is a **median over n repeats** from Ollama's own separated timers
(`prompt_eval_duration` / `eval_duration`), with the KV cache defeated by a
unique nonce leading the first message, and `num_ctx` asserted against
`prompt_eval_count` so nothing was silently truncated. 0 retries, 0 errors,
0 truncated runs across the whole set.

## Read the noise floor before you read anything else

`architect-compiler:latest` and `qwen3:4b-instruct-2507-q4_K_M` are **byte-identical
weights** — the first is a Modelfile wrapper around the second. Any measured gap
between them is pure noise. Measured at n=5:

| Task | qwen3:4b | architect-compiler | apparent gap |
|---|---|---|---|
| T1 ingest | 204 t/s | 398 t/s | 1.95× |
| T2 JSON action | 408 t/s | 189 t/s | 2.16× — **rank flips** |
| T3 rewrite | 319 t/s | 291 t/s | 1.10× |

**On short prompts, treat any throughput difference below ~2.2× as a tie.**
Worst within-model spread across 5 runs was 3.2×. This box runs other workloads.

The floor is task-dependent: on the long-context runs (T4) prefill is
compute-bound and dominates the jitter, and spread collapses to **1.00–1.13×**.
Differences there are real at much smaller ratios.

**Accuracy has no such problem** — the scores below were identical across two
independent full runs.

## Models under test

| Model | Architecture | Params | Context | Note |
|---|---|---|---|---|
| `granite4:3b-h` | granitehybrid | 3.2B | 1,048,576 | **non-transformer — Mamba-2 SSM + attention** |
| `qwen3:4b-instruct-2507-q4_K_M` | qwen3 | 4.0B | 262,144 | transformer |
| `architect-compiler:latest` | qwen3 | 4.0B | 262,144 | transformer · **same weights as the row above** |
| `mannix/llama3.1-8b-abliterated` | llama | 8.0B | 131,072 | transformer |

---

## T1 — Codebase ingest (the blueprint job) · n=5

Read a synthetic repo of exactly 137 classes, summarise in 5 bullets.
Scored by machine: did the summary state the correct count.

| Model | prefill t/s | gen t/s | prompt tok | **stated the exact count** |
|---|---|---|---|---|
| `granite4:3b-h` | 266 | 17.5 | 2,011 | **0/5** |
| `qwen3:4b-instruct` | 204 | 20.8 | 2,360 | **5/5** |
| `architect-compiler` | 398 | 38.3 | 2,350 | **5/5** |
| `mannix/llama3.1-8b-abliterated` | 241 | 18.9 | 2,097 | **0/5** |

The 4B transformers count correctly every time. Granite and the 8B Llama never
do — they approximate ("about 100 modules") on a corpus that is 0.14 % of
Granite's context window. This is not a context-capacity failure.

## T2 — JSON tool action (the agent-loop job) · n=5

Given the real tool schema and a failing test, emit one valid action. Scored by
the tool's **own** `parse_action`, plus a valid-action check against the set
parsed **out of the prompt the model was shown**.

| Model | prefill t/s | gen t/s | prompt tok | **valid action emitted** | chose |
|---|---|---|---|---|---|
| `granite4:3b-h` | 369 | 32.8 | 793 | **5/5** | `query_memory` |
| `qwen3:4b-instruct` | 398 | 40.2 | 843 | **5/5** | `run_command` |
| `architect-compiler` | 412 | 41.7 | 833 | **5/5** | `run_command` |
| `mannix/llama3.1-8b-abliterated` | 281 | 31.4 | 1,560 | **5/5** | `query_memory` |

All four emit parseable, valid tool actions every time. This task does not
discriminate on validity.

It does show a **judgment** split that this harness does not score: asked to find
which file defines a login handler, the two Qwen models reach for `run_command`
(grep the tree) while Granite and Llama reach for `query_memory` (ask the
episodic store). Both are legal; only one can answer the question from a cold
start. Scoring action *appropriateness* would need a rubric this harness does not
have — noted as unmeasured rather than folded into the pass rate.

> ### ⚠️ Correction — this table previously read 0/5 for Granite and Llama
>
> The first published version of this section scored both at **0/5** and called it
> "the sharpest result in the set." **That was wrong, and the bug was mine.** The
> scorer held a hardcoded 7-tool allowlist while the prompt advertised 13 — a
> concurrent change had added `query_memory`, `commit_memory`, `visual_debug`,
> `git_snapshot` and `revert_checkpoint`. Both models chose `query_memory`, a
> perfectly valid tool, and my stale constant marked it invalid.
>
> This is the same defect class this repo's audit flags in
> `tests/zero_shot_benchmark.py` (a hardcoded value in a results path), committed
> by the audit itself. The scorer now derives the valid set from
> `get_system_prompt_addition()` with an assertion on its size, so it cannot go
> stale again. Both runs are in `results.json` under `corrections`.
>
> Caught by running the same task through the live production path, where Llama
> scored 5/5 — a result that contradicted the bench and turned out to be right.

## T3 — Whole-file rewrite (the editor job) · n=5

Rewrite a 5-function file to an instruction. Scored on the two things that
matter: does the result compile, and did it preserve the four functions it was
not asked to touch.

| Model | prefill t/s | gen t/s | **compiled + kept all 4 fns** |
|---|---|---|---|
| `granite4:3b-h` | 187 | 16.7 | **5/5** |
| `qwen3:4b-instruct` | 319 | 22.6 | **5/5** |
| `architect-compiler` | 291 | 34.1 | **5/5** |
| `mannix/llama3.1-8b-abliterated` | 315 | 33.3 | **5/5** |

Everything passes. This job does not discriminate between these models.

## T4 — Long context: does the SSM's linear attention pay off? · n=3

Same corpus, growing. A transformer's attention is O(n²); granitehybrid's
Mamba-2 layers are O(n). If that matters on this box, the gap must widen.

| chars | prompt tok | `granite4:3b-h` (SSM) | `qwen3:4b` (transformer) | SSM advantage |
|---|---|---|---|---|
| 4,000 | 1,139 | 378 t/s | 422 t/s | 0.90× |
| 16,000 | 3,783 | 378 t/s | 373 t/s | 1.01× |
| 64,000 | 14,456 | **369 t/s** | **241 t/s** | **1.53×** |

Per-run ranges at 64,000 chars: Granite **367–369**, qwen3 **240–241**. Not
overlapping, spread ≤ 1.01× on both — this gap is real, not jitter.

The shape is the evidence, not the ratio: **Granite is flat** (378 → 378 → 369,
a 1.02× decay across a 13× longer prompt) while **qwen3 decays monotonically**
(422 → 373 → 241, 1.75×). That is the linear-vs-quadratic signature showing up
exactly where theory says it should.

Scope: measured to 14.5K tokens only. Granite's window is 1,048,576. The
divergence at 100K+ is unmeasured here and the trend should not be extrapolated
to it without running it.

---

## Found while validating the swap: the agent loop had never reached a model

Benchmarks call Ollama directly. Production calls it through
`core/llm_gateway.py` → litellm. Running T2 through the **production** path
instead surfaced this:

```
[GATEWAY ERROR] Failed to route to qwen3:4b-instruct-2507-q4_K_M:
litellm.BadRequestError: LLM Provider NOT provided.
```

litellm requires an explicit provider prefix. Every caller in this repo passes a
bare Ollama tag — `config.py`'s `FAST_MODEL`, the `/ws/agent` `model` field, the
CLI. Verified against **both** the old and the new default:

| model string | through the gateway |
|---|---|
| `mannix/llama3.1-8b-abliterated:latest` (old default) | ❌ gateway failure |
| `qwen3:4b-instruct-2507-q4_K_M` (new default) | ❌ gateway failure |
| `ollama/mannix/llama3.1-8b-abliterated:latest` | ✅ works |
| `ollama/qwen3:4b-instruct-2507-q4_K_M` | ✅ works |

So this predates the swap and is not caused by it. `generate_next_thought`
returned `{"action": "error", "thought": "API Gateway Failure."}` on **every step
of every run**, the loop fell into its "Malformed JSON. Retrying…" branch, burned
all 20 steps without ever reaching a model, and then tripped the repeated-action
detector. That is the real reason the agent never accomplished anything.

The trap that hides it: a bare Ollama tag can still contain a slash —
`mannix/llama3.1-8b-abliterated:latest` looks prefixed but `mannix` is not a
provider. `normalize_model()` now checks membership in a known-provider set
rather than the presence of a slash, and defaults everything else to `ollama/`.
After the fix, the full loop emits valid actions 5/5 on both models.

---

## What this means for the harness

**The non-transformer is on the right job — but for the wrong reason, and it is
one config change from being on the wrong one.**

`granite4:3b-h` is `EDITOR_MODEL`, doing whole-file rewrites (T3), where it
scores 5/5 and its architecture is irrelevant — those prompts are ~200 tokens.
Meanwhile the job that actually needs linear-time attention is the blueprint
ingest, which reads 60,000 characters of repository. Granite is the only model
that holds throughput flat as that prompt grows.

The obvious move is to hand Granite the ingest job. **Do not** — T1 says it
states the wrong count 5 times out of 5. It is the right architecture for that
job and the wrong model for it. Throughput would be won and correctness lost.

Three things follow:

1. **Keep the current assignment.** Granite edits, Qwen ingests. It is correct
   on accuracy, which is the constraint that binds.
2. **`FAST_MODEL` — a weaker case than this document first made.** The original
   version claimed the 8B abliterated Llama emitted a valid tool action 0/5.
   That was a scorer bug (see the T2 correction); it is 5/5, and so is everything
   else. What survives is narrower: on **T1** Llama states the wrong count 5/5
   while `qwen3:4b` gets it right 5/5, and qwen3 is 4B vs 8B (2.5 GB vs 4.68 GB
   on disk). Live end-to-end it ran 4.3 s/step vs 4.9 s/step — a 12 % gap, well
   under this box's noise floor, so **do not** claim a speed win.
   Against that: Llama is the *abliterated* model. Swapping `FAST_MODEL` to
   `qwen3:4b` trades refusal-free behaviour for counting accuracy and half the
   footprint. That is a judgement call, not a measurement — the env var
   `FAST_MODEL` overrides it either way.
3. **`architect-compiler` is not faster than its base model** and cannot be —
   same weights. Its 5/5 vs 5/5 on both scored tasks confirms it. It is still
   worth keeping for what it genuinely does: baking sampling params and a system
   prompt into the blob so the harness need not send them. That is packaging,
   not capability. (This repo's own earlier benchmark reached the same
   conclusion and retracted its "3× speedup" — that retraction was correct.)

## Reproducing

```bash
venv/bin/python benchmarks/harness.py --reps 5
```

~25 min for T1–T3 at n=5 plus ~10 min for T4 at n=3 on this box. Cheaper smoke
run: `--task t2 --reps 3`.
