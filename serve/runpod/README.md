# Deploying the frank-and-unfiltered lane on RunPod

All prices fetched from runpod.io/pricing on 2026-08-29. All VRAM figures
measured on the dev box with Ollama — see "Re-measure before you price" below.

---

## The model

`mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated` — safetensors, the format vLLM
serves. (Ollama's `mannix/llama3.1-8b-abliterated` is a GGUF of the same idea;
GGUF under vLLM is slow and second-class, so switch weights for production.)

**Sizing gotcha that decides your GPU.** At bf16 an 8B model is **~16 GB of
weights alone**. On a 24 GB card that leaves ~5 GB for KV cache — 1–2 concurrent
sessions, which wrecks the economics. Two ways out:

| Approach | Card | $/hr | Weights | KV headroom |
|---|---|---|---|---|
| bf16 | RTX A6000 48GB | 0.33 | ~16 GB | ~27 GB → good concurrency |
| AWQ 4-bit | RTX A5000 24GB | 0.16 | ~5.5 GB | ~16 GB → also good |

**Start on the A6000 at bf16** ($241/month). It removes quantisation as a
variable while you find out whether anyone wants this. Move to a quantised
A5000 ($117/month) once traffic justifies the tuning.

## Launch

```bash
python -m vllm.entrypoints.openai.api_server \
  --model mlabonne/Meta-Llama-3.1-8B-Instruct-abliterated \
  --served-model-name frank-8b \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.90 \
  --host 0.0.0.0 --port 8000 \
  --api-key "$SERVE_API_KEY"
```

`--api-key` is not optional. An open inference endpoint on a rented GPU gets
found and drained within days.

## The edge is not optional

Traffic must go **through** `serve/policy.py`, never straight to vLLM. The model
is abliterated: it has no refusals of its own, so the edge is the only thing
between one user and account termination. RunPod terminates "as determined by
us, at our sole discretion" — there is no appeal you can engineer around.

Measured on the current eval set (`serve/eval_policy.py`):

```
false positives (frank content refused):  0/20   <- would kill the product
false negatives (fatal content allowed):  0/11   <- would kill the account
classifier latency: median 213 ms, max 740 ms
```

That eval is **31 prompts**. It shows the approach works; it does **not** show
it survives adversarial users. Grow the set from real traffic and re-run it in
CI before every deploy.

## Legal obligations you must actually ship

Not advice — these are the words in the documents:

- **"Built with Llama"** attribution, visible in the product.
- **Disclose that output is AI-generated.** The Llama AUP prohibits
  "Representing that the use of Llama 3.1 or outputs are human-generated".
- **Disclose known dangers.** The AUP names failure to do so as a violation.
  `REQUIRED_DISCLOSURE` in `serve/policy.py` is drafted for this.
- Commercial use is permitted under 700M MAU. Not your problem yet.

## Unit economics

Measured KV overhead for llama-8b at 16K context: **2.98 GB per session** (weights
load once and are shared; only KV is per-session — do not divide card VRAM by
total model VRAM, which double-counts).

| Card | $/hr | concurrent @16K | $/session-hr |
|---|---|---|---|
| RTX A6000 48GB | 0.33 | 12 | 0.028 |
| A40 48GB | 0.35 | 12 | 0.029 |
| RTX A5000 24GB | 0.16 | 5 | 0.032 |

One A6000 at 12 concurrent, derated 4× for peak-vs-average:

| user load | subscribers | MRR @ $15 | gross margin |
|---|---|---|---|
| light, 10 h/mo | 219 | $3,285 | 93% |
| typical, 20 h/mo | 109 | $1,635 | 85% |
| heavy, 60 h/mo | 36 | $540 | 55% |

**Compute is not the constraint on this business.** Distribution and payment
processing are.

## Re-measure before you price

Every VRAM and throughput number above came from Ollama on Apple Silicon under
load. vLLM's paged attention allocates KV per *token* rather than per full
window, so real concurrency is **several times higher** — the table is a floor,
not a forecast. Rent one A6000 for an hour (~$0.33) and re-run
`benchmarks/harness.py` against the vLLM endpoint before quoting anyone.

## Start serverless

RunPod serverless bills per second and scales to zero. Against a $241/month
A6000 pod, the A6000-class serverless rate of $1.22/hr breaks even at **198
GPU-hours/month ≈ 6.6 busy hours/day**. You are nowhere near that on day one, so
serverless is strictly cheaper until you are. Watch cold-start latency — it is
the usual reason serverless fails for interactive chat.
