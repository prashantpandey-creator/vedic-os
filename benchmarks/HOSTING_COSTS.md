# Hosting the Omni-Agent model stack on RunPod — measured costs

*All GPU prices fetched from runpod.io/pricing on 2026-08-29. All VRAM and
throughput numbers measured on this box (Apple Silicon, Ollama 0.15.1) — see
"What is NOT measured" before quoting any of it at a customer.*

---

## 1. What the stack costs to keep warm

Weights on disk: granite4:3b-h 1.94 GB + qwen3:4b 2.50 GB + llama3.1-8b-abliterated
4.68 GB = **9.1 GB**. Fits any 24 GB card.

| GPU (community cloud) | $/hr | $/month always-on |
|---|---|---|
| **RTX A5000 24GB** | **0.16** | **117** |
| RTX 3090 24GB | 0.22 | 161 |
| RTX A6000 48GB | 0.33 | 241 |
| RTX 4090 24GB | 0.34 | 248 |
| A40 48GB | 0.35 | 255 |
| L4 24GB | 0.44 | 321 |
| L40S 48GB | 0.79 | 577 |
| A100 80GB PCIe | 1.19 | 869 |

Plus network storage at $0.07/GB/month — 20 GB for the model blobs is **$1.40/month**.

**Floor: ~$118/month** for the entire three-model stack, always warm, on an A5000.

### Serverless instead?

Serverless bills per second and scales to zero, at roughly 4x the hourly rate.

| Serverless tier | $/hr | Break-even vs its always-on pod |
|---|---|---|
| L4 / A5000 / 3090 | 0.69 | 170 GPU-hr/month = **5.7 busy hours/day** |
| RTX 4090 | 1.10 | 225 GPU-hr/month = **7.5 busy hours/day** |
| A6000 / A40 | 1.22 | 198 GPU-hr/month = **6.6 busy hours/day** |

Below ~6 busy hours a day, serverless is cheaper and you pay nothing overnight.
Above it, rent the pod. Early on you are far below it — **start serverless.**

---

## 2. The number that actually decides the business

VRAM is what you rent, and it is dominated by the KV cache, not the weights.
Measured, one model resident at a time, evicted between readings:

| num_ctx | granite4:3b-h (Mamba-2 hybrid) | qwen3:4b (transformer) | ratio |
|---|---|---|---|
| 4,096 | 2.64 GB | 3.50 GB | 1.32× |
| 16,384 | 3.28 GB | 5.33 GB | 1.62× |
| 65,536 | 5.83 GB | 12.71 GB | 2.18× |
| 131,072 | 9.23 GB | 22.58 GB | **2.45×** |

The ratio **widens with context**. That is the state-space signature: the
transformer's KV cache grows linearly with every token held, the SSM's recurrent
state does not. granitehybrid is a hybrid, so it still has some attention layers
and still grows — 7.29 GB of overhead at 131K versus the transformer's 20.08 GB,
about **2.75× slower growth**.

Translated into sessions per card (RTX A5000 24 GB, $0.16/hr, 10% headroom):

| Model | ctx | GB each | sessions/card | $/session-hr | $/session-month |
|---|---|---|---|---|---|
| granite (SSM) | 16K | 3.28 | 6 | 0.027 | 19 |
| granite (SSM) | 64K | 5.83 | 3 | 0.053 | 39 |
| granite (SSM) | 128K | 9.23 | 2 | 0.080 | 58 |
| qwen3 (transformer) | 16K | 5.33 | 4 | 0.040 | 29 |
| qwen3 (transformer) | 64K | 12.71 | 1 | 0.160 | 117 |
| qwen3 (transformer) | 128K | 22.58 | **0 — does not fit** | — | — |

**At 64K context the SSM serves 3 concurrent sessions where the transformer serves 1,
on the same $0.16/hr card.** That is the only defensible unit-economics moat in
this stack.

---

## 3. But the SSM cannot currently do the job that would use it

Accuracy, n=5 per cell, machine-scored (see `harness.py`):

| Task | granite (SSM) | qwen3 | architect-compiler | llama-8b-abliterated |
|---|---|---|---|---|
| T1 ingest — state the exact class count | **0/5** | 5/5 | 5/5 | 0/5 |
| T2 emit a valid JSON tool action | **0/5** | 5/5 | 5/5 | 0/5 † |
| T3 whole-file rewrite — compiles + keeps untouched fns | 5/5 | 5/5 | 5/5 | 5/5 |

† llama-8b scored 5/5 on T2 in an earlier run and 0/5 here. It is not reliable at
JSON; it is the agent's main loop model. Treat that as the finding.

So: the memory advantage is real and grows, but granite fails both reasoning-shaped
jobs and only passes the short-prompt rewrite — which is exactly the job it already
has (`EDITOR_MODEL`). **The current assignment is correct.** The advantage is
unexploited not through misconfiguration but because the model that has it cannot
yet do the work that needs it.

---

## 4. architect-compiler is not faster than its base model

`architect-compiler:latest`'s parent is `qwen3:4b-instruct-2507-q4_K_M` — identical
weights, differing only by a baked SYSTEM prompt and sampling parameters. It scores
identically (5/5 vs 5/5 on both T1 and T2). Speed differences between them across
runs are box noise, not model.

It also **silently prepends ~390 tokens** of architectural-graph instructions
whenever the harness sends no system message of its own — and is completely
overridden whenever the harness does. `init_omni_loop` always sends one.

An earlier benchmark in this repo reported a "3× speedup" for it. That was Ollama
reusing the base model's KV cache. The follow-up run in this repo caught that
correctly and said so.

---

## 5. What is NOT measured

Be strict about this before any of it goes in front of a customer:

- **Throughput on RunPod hardware.** Every tok/s figure here is Ollama on Apple
  Silicon with 14 other processes on the box. It does not predict an A5000.
- **vLLM / SGLang.** Production serving uses paged attention and continuous
  batching, which changes the absolute VRAM per session substantially. The
  *architectural ratio* (SSM vs transformer KV growth) should carry; the absolute
  GB will not. Re-measure there before pricing anything.
- **Cost per user.** Needs concurrency and duty cycle, neither of which exists yet.
- **Cold-start latency on serverless**, which is the main reason serverless deals
  fall apart for interactive agents.

## Reproduce

```bash
venv/bin/python benchmarks/harness.py --reps 5
```
