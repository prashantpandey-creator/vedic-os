# Local Model Benchmarks — Omni-Agent

Every number below is a **median of n repeats**, taken from Ollama's own
separated timers (`prompt_eval_duration` / `eval_duration`), with the KV
cache defeated by a unique per-run nonce and `num_ctx` asserted against
`prompt_eval_count` so nothing was silently truncated.

## Models under test

| Model | Architecture | Params | Context | Note |
|---|---|---|---|---|
| `granite4:3b-h` | granitehybrid | 3.2B | 1,048,576 | **non-transformer (Mamba-2 SSM + attention)** |
| `qwen3:4b-instruct-2507-q4_K_M` | qwen3 | 4.0B | 262,144 | transformer |
| `architect-compiler:latest` | qwen3 | 4.0B | 262,144 | transformer · same weights as `qwen3:4b-instruct-2507-q4_K_M` |
| `mannix/llama3.1-8b-abliterated:latest` | llama | 8.0B | 131,072 | transformer |

## T1 — Codebase ingest (the blueprint job)

| Model | prefill tok/s | gen tok/s | prompt tok | accuracy | n |
|---|---|---|---|---|---|
| `granite4:3b-h` | 266 | 17.5 | 2011 | 0/5 stated exact count | 5 |
| `qwen3:4b-instruct-2507-q4_K_M` | 204 | 20.8 | 2360 | 5/5 stated exact count | 5 |
| `architect-compiler:latest` | 398 | 38.3 | 2350 | 5/5 stated exact count | 5 |
| `mannix/llama3.1-8b-abliterated:latest` | 241 | 18.9 | 2097 | 0/5 stated exact count | 5 |

## T2 — JSON tool action (the agent-loop job)

| Model | prefill tok/s | gen tok/s | prompt tok | accuracy | n |
|---|---|---|---|---|---|
| `granite4:3b-h` | 165 | 16.1 | 793 | 0/5 valid action | 5 |
| `qwen3:4b-instruct-2507-q4_K_M` | 408 | 42.2 | 843 | 5/5 valid action | 5 |
| `architect-compiler:latest` | 189 | 14.1 | 833 | 5/5 valid action | 5 |
| `mannix/llama3.1-8b-abliterated:latest` | 179 | 17.7 | 1560 | 0/5 valid action | 5 |

## T3 — Whole-file rewrite (the editor job)

| Model | prefill tok/s | gen tok/s | prompt tok | accuracy | n |
|---|---|---|---|---|---|
| `granite4:3b-h` | 187 | 16.7 | 195 | 5/5 compiled + kept all fns | 5 |
| `qwen3:4b-instruct-2507-q4_K_M` | 319 | 22.6 | 217 | 5/5 compiled + kept all fns | 5 |
| `architect-compiler:latest` | 291 | 34.1 | 207 | 5/5 compiled + kept all fns | 5 |
| `mannix/llama3.1-8b-abliterated:latest` | 315 | 33.3 | 250 | 5/5 compiled + kept all fns | 5 |
