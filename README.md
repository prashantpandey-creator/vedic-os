# 🪷 Vedic Framework - Local AI Operating System

Vedic is a premium, locally-hosted Multi-Agent Operating System designed to turn small, 8B parameter models into fully autonomous software engineers that rival cloud models like Claude 3.5 Sonnet and Opus.

It achieves this through extreme agentic engineering, native binary optimizations, and a beautiful Glassmorphism UI.

## 🚀 Breakthrough Features

1. **Self-Healing AST Engine**: Vedic intercepts terminal edits to Python and JS/React files. If the agent hallucinates a bracket or indentation, Vedic catches the broken Abstract Syntax Tree, blocks the edit, reverts the file, and forces the LLM to self-heal.
2. **Forced System-2 Reflection**: The system enforces a mandatory `CRITIQUE:` block before any tool execution, forcing the local model to aggressively cross-examine its own hallucinations.
3. **Dual-Model Asymmetry**: Uses Mamba (infinite-context RNN) purely to ingest the codebase, and LLaMA 3.1 8B purely to reason and write code, maximizing VRAM efficiency.
4. **Rust Binary Integration**: Navigates massive codebases natively using `ripgrep`, `fd`, and `bat` inside a hardened Docker sandbox.
5. **C-Extension Backbone**: Memory checkpoints and parsing are serialized via `orjson`, making disk writes 10x faster than standard Python JSON.
6. **Continuous Context Distillation**: Never run out of tokens. The agent automatically flushes its context every 10 steps, distilling the past into semantic memory blocks.

## 🛠️ Installation

```bash
git clone <your-repo>
cd local-llm-ui
./run.sh
```

## 🔐 Architecture
- **app.py**: Streamlit Orchestrator (Glassmorphism UI, Markdown Streaming)
- **core/terminal_engine.py**: Sandboxed Docker Executor with Semantic Paging (prevents `cat` from blowing up the context window).
- **core/file_system.py**: Live AST-checking file modification engine.
- **core/tool_registry.py**: Tool router parsing LLM intentions into bash actions.
- **agents/omni_state_machine.py**: The brain. Handles reflection, phase progression, and looping logic.

*100% Local. Zero Telemetry. Absolute Privacy.*
