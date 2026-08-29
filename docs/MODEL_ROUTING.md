# Model routing — are we using the non-transformer correctly?

**Short answer: the routing is fine; the JOB is the problem.**

`EDITOR_MODEL = granite4:3b-h` stays exactly where it is (settled below — the SSM
ties the transformer on real edits and costs less memory to hold resident). What
should change is that the long job the SSM would win — the LLM blueprint — should
be **deleted rather than re-routed**, because both architectures produce an unusable
blueprint: 0 of 5 real filenames cited.

> This heading previously read *"no, the one non-transformer model is on the wrong
> job"*, which contradicted this document's own revised plan further down. That
> earlier verdict came from the throughput measurement alone, before anyone checked
> whether the blueprint was usable. Corrected rather than deleted, so the reasoning
> stays visible.

Status: measured 2026-08-29. Nothing here is applied yet — this is the plan.

## What's actually in the box

Pulled from `/api/show` on the live Ollama, not from memory:

| model | architecture | params | ctx | SSM tensors |
|---|---|---|---|---|
| **granite4:3b-h** | **granitehybrid** | 3.2B | **1,048,576** | **yes** — `ssm.conv_kernel`, `ssm.state_size`, `ssm.group_count`, `ssm.inner_size`, `ssm.time_step_rank` |
| qwen3:4b-instruct-2507 | qwen3 | 4.0B | 262,144 | none |
| architect-compiler | qwen3 | 4.0B | 262,144 | none |
| vyasa-compiler | qwen3 | 4.0B | 262,144 | none |
| mannix/llama3.1-8b-abliterated | llama | 8.0B | 131,072 | none |
| qwen2.5:32b | qwen2 | 32.8B | 32,768 | none |

`granite4:3b-h` is the **only** non-transformer. IBM Granite 4.0 Hybrid — Mamba-2
state-space layers interleaved with attention. Everything else is pure attention.

## Where each model runs today

| config key | model | job | length of that job |
|---|---|---|---|
| `INGEST_MODEL` | qwen3:4b (transformer) | read the whole repo, write the blueprint | **17,703 tokens** |
| `EDITOR_MODEL` | granite4:3b-h (**SSM**) | rewrite one file | ~300–3,000 tokens |
| `FAST_MODEL` | llama3.1-8b | the agent loop | capped at 8 messages |
| `HEAVY_MODEL` | qwen2.5:32b | — | **never referenced anywhere** |

The longest job goes to the transformer. The 1M-context linear-time model gets the
shortest job.

## The measurement

Same repo dump, both models, `num_ctx=65536`, `temperature=0`, cold load each time.

| prompt size | granite4:3b-h (SSM) | qwen3:4b (transformer) | winner |
|---|---|---|---|
| 17,460 tok | 358 tok/s prefill, 51.4s | 379 tok/s, 50.3s | level |
| **44,891 tok** | **317 tok/s, 154s, 5.83 GB** | 112 tok/s, 423s, 12.71 GB | **SSM by 2.8× time, 2.2× memory** |

The crossover is between 17K and 44K tokens. Below it the two are
indistinguishable; above it the transformer's prefill collapses (379 → 112 tok/s)
while the SSM barely moves (358 → 317). That is the quadratic-vs-linear curve
showing up on real hardware.

Memory matters more than speed here: 12.71 GB vs 5.83 GB on a machine that has
already had a co-tenancy outage from an idle model holding RAM.

## The compounding bug

`init_omni_loop` hardcodes `"num_ctx": 16000` for the ingest.

- ingest produces **17,703 tokens** (78,675 chars — note `max_chars=60000`
  overshoots by one whole file, since the size check happens *after* appending)
- at `num_ctx=16000`, `prompt_eval_count` comes back as exactly **16000**
- at `num_ctx=32768`, it comes back as **17,703**

So 1,703 tokens — roughly the last 10% of the repo, alphabetically the tail — are
silently thrown away on every single run. Nothing warns.

Net effect: the ingest is clipped to sit just *below* the size at which the SSM
would start beating the transformer. The one workload that justifies owning a
hybrid model has been trimmed to the point where the hybrid looks pointless.

## Cosmetic, but it's how this got missed

The `🐍 Mamba` strings in `omni_state_machine.py` are on the **blueprint path**,
which runs `INGEST_MODEL` — a transformer. Someone labelled the SSM's job on the
transformer's code. The naming has been lying about the routing.

## Plan (not applied)

> **Revised 2026-08-29 after running the models on real tasks.** An earlier draft
> of this section said "swap `INGEST_MODEL` to granite4:3b-h". That was wrong, and
> it was wrong in an interesting way: the throughput measurement was right, but I
> had never checked whether the blueprint the model produces is *usable*. It isn't
> — from either architecture. See "The blueprint is worthless from both" below.
> Do not make a model faster at a job that shouldn't exist.

1. **Delete the LLM blueprint. Do not re-route it.** The deterministic file tree
   (`build_tree_with_hints`, already shipped) is what actually tells the agent
   what exists. Removing the model call saves **87–109s and 17,703 tokens of
   prefill every session** and removes the last reason `num_ctx` and `max_chars`
   matter here. This is the whole of items 2 and 3 below, by subtraction.
2. ~~Raise `num_ctx` to 32768~~ — moot once the model call is gone. If the LLM
   orientation summary is kept anyway, it must be raised: the ingest is 17,703
   tokens against a hardcoded 16,000, silently dropping ~1,703.
3. ~~Fix `max_chars` overshoot~~ — same; only matters if the ingest survives.
   (`max_chars=60000` produced 78,675 chars: the budget is checked after
   appending a file, not before.)
4. **Move or drop the `🐍 Mamba` label.** It sits on the transformer's path.
5. **Leave `EDITOR_MODEL = granite4:3b-h` where it is.** Settled below — the SSM
   ties the transformer on real edits, so there is no reason to move it, and it is
   the cheaper model to keep resident.
6. **`HEAVY_MODEL` (qwen2.5:32b) is referenced by nothing.** Either wire it as the
   escalation target for the loop-detection path (currently escalates to a Claude
   API model that requires a key, and otherwise just gives up) or delete the config
   entry. Leaving a 20 GB model configured but unreachable is the worst of both.

## Settled: the SSM does NOT pay a copy-fidelity penalty

The worry was that whole-file rewrite is a verbatim copy task — attention's
strength, an SSM's known weak spot — so `EDITOR_MODEL = granite4:3b-h` might be
wrong even though the architecture suits long input.

Measured on six real files, real instructions ("add a docstring to X"), scored by
whether `write_verified` would accept the result and whether the target function
survived:

| file | lines | granite4:3b-h (SSM) | qwen3:4b (transformer) |
|---|---|---|---|
| core/memory_graph.py | 27 | 100% kept, ACCEPT, 14s | 100% kept, ACCEPT, 20s |
| core/checkpoint.py | 65 | 100% kept, ACCEPT, 30s | 100% kept, ACCEPT, 41s |
| core/ollama_api.py | 57 | 96% kept, ACCEPT, 49s | 100% kept, ACCEPT, 36s |
| core/terminal_engine.py | 125 | 100% kept, ACCEPT, 112s | 98% kept, ACCEPT, 53s |
| core/file_system.py | 144 | **23% — REJECT truncated 1778/6441** | 100% kept, ACCEPT, 89s |
| core/tool_registry.py | 306 | 99% kept, ACCEPT, 212s | **13% — REJECT truncated 2980/16104** |
| | | **5/6 usable** | **5/6 usable** |

Dead tie. And there is **no length curve**: granite fails at 144 lines and
succeeds at 306; qwen3 does the reverse. Both truncate sometimes; neither
truncates predictably. The architecture hypothesis is not supported — this is
run-to-run variance in small quantised models, not attention vs. state-space.

Two useful consequences:

- `EDITOR_MODEL` stays. The SSM costs less memory to hold resident and performs
  the same.
- **`write_verified` caught both failures** — its first live catches on real model
  output. Before it existed, both of those runs would have written a truncated
  file straight over the original.

## The blueprint is worthless from both — this is the real finding

Both models were given the actual repo ingest (17.7K tokens) and the actual
blueprint prompt, then scored on how many of five real filenames from this
codebase they cited:

| model | wall | real filenames cited |
|---|---|---|
| granite4:3b-h | 87s | **0 / 5** |
| qwen3:4b | 109s | **0 / 5** |

granite described "dynamic system-prompt injection pulling tool schemas from
ToolRegistry" — which is a paraphrase of `PROJECT_MIND.md`, the memory file, not a
reading of the code. qwen3 cited `app.py`, `config.py` and `launch.sh`; the third
does not exist in this repo.

So the section of the system prompt headed *"use this to understand WHAT files
exist"* was being filled, at a cost of ~100 seconds and 17.7K tokens per session,
by a model that names files that aren't there. Swapping in a faster model buys a
faster wrong answer.

The deterministic file tree already replaces it and cannot be wrong. Delete the
model call.

