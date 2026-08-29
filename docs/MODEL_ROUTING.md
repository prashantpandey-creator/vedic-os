# Model routing — are we using the non-transformer correctly?

**Short answer: no. The one non-transformer model is on the wrong job.**
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

1. **Swap the routing.** `INGEST_MODEL = granite4:3b-h`. One line in `config.py`.
   Expect ~2.8× faster blueprints at ~half the memory on any repo above ~20K tokens.
2. **Raise `num_ctx` to 32768** and stop clipping the repo. With the SSM the memory
   cost of the larger window is affordable; with the transformer it is not.
3. **Fix `max_chars` overshoot** — check the budget *before* appending a file, not
   after.
4. **Move the `🐍 Mamba` label** onto whichever model is actually the SSM, or drop it.
5. **Decide `EDITOR_MODEL` after the deferred test below.** Do not move it on a hunch
   — see the open question.
6. **`HEAVY_MODEL` (qwen2.5:32b) is referenced by nothing.** Either wire it as the
   escalation target for the loop-detection path (currently escalates to a Claude
   API model that requires a key, and otherwise just gives up) or delete the config
   entry. Leaving a 20 GB model configured but unreachable is the worst of both.

## Open question — DO NOT claim this is settled

Whole-file rewrite is a **verbatim copy** task, and exact recall from long context
is the known weak spot of state-space models — it is what attention is for. If the
SSM degrades on long files, `EDITOR_MODEL = granite4:3b-h` is the wrong choice even
though it is the right *architecture* for long input.

Measured so far:

| file | lines | granite4:3b-h | qwen3:4b |
|---|---|---|---|
| core/memory_graph.py | 27 | 100% kept, accepted | 100% kept, accepted |
| core/checkpoint.py | 65 | 100% kept, accepted | 100% kept, accepted |
| core/tool_registry.py | 306 | **crashed** | **crashed** |

The 306-line run killed the Ollama connection for *both* models — the long-context
benchmark was running concurrently and the box ran out of memory. That row is
**inconclusive, not a failure**. Nobody has measured copy fidelity above 65 lines.

Re-run `tests/bench_ssm_vs_transformer.py` on an idle machine before touching
`EDITOR_MODEL`.
