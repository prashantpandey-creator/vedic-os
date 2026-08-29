# 🏛️ Phase 1 Ingestion Benchmark (Architect Models)

*Generated: 2026-08-29*

This document publishes the automated benchmark results evaluating the optimal model for **Phase 1: Codebase Ingestion** in the Omni-Agent harness.

The models were evaluated on their ability to ingest a massive synthetic codebase (120 classes) and output a perfectly formatted 5-point architectural summary.

---

## 🏆 Part 1: Architecture Showdown (Qwen vs Granite vs Llama)

| Model | Size | Time to Complete | Speed | Accuracy Verdict |
|-------|------|-----------------|-------|------------------|
| **architect-compiler:latest (Qwen 3)** | 4.0B | **8.04s** | 8.1 t/s | **Perfect.** Accurately mapped all classes without truncating. (262k context) |
| **granite4:3b-h (IBM)** | 3.0B | 9.91s | 14.3 t/s | **Failed.** Hallucinated halfway through the file due to context limits. |
| **llama3.1-8b-abliterated (Meta)** | 8.0B | 24.93s | 4.0 t/s | **Failed.** Extreme prompt processing lag and an off-by-one hallucination error. |

**Conclusion:** The custom Qwen 3 architecture is uncontested for repository ingestion. Its 256K token context window easily swallows the entire repository in a single shot.

---

## 🔬 Part 2: The "VRAM Cache" Illusion (Base vs Custom)

We conducted a second, highly rigorous hardware test to determine if the custom `architect-compiler` Modelfile was inherently faster than the raw `qwen3:4b-instruct` base model. 

*We directly hooked into the GPU metrics to bypass Ollama's VRAM caching mechanism.*

| Metric | qwen3:4b-instruct (Raw) | architect-compiler (Custom) |
|--------|-------------------------|------------------------------|
| **Prompt Reading Speed** | 395.1 tokens/sec | 395.1 tokens/sec |
| **Token Generation Speed** | 38.5 tokens/sec | 38.9 tokens/sec |
| **VRAM Load Time** | 1.75s | 1.47s |

**Conclusion:** The custom model is *not* magically faster than the base model (they share the identical 39 token/sec ceiling). Earlier observations of a "3x speedup" were simply an illusion caused by Ollama reusing the base model's KV Cache in VRAM. 

However, **architect-compiler:latest** remains the superior choice in production because baking the system prompt and strict sampling parameters (`top_k 20`, `repeat_penalty 1`) directly into the model blob guarantees highly deterministic architectural output without requiring the frontend harness to transmit bloated API payloads.
