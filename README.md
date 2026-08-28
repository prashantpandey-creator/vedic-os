# Local Omni-Agent (Vedic)

A commercial-grade, fully local AI software engineering framework. It uses an SSM (Mamba) for rapid architectural codebase ingestion, and an LLM (Qwen/Llama3) for an autonomous terminal loop.

## Features
- **GitHub Mounter**: Automatically connects to your GitHub CLI (`gh`) to clone repos natively.
- **Omni-Agent Terminal Loop**: Safely executes commands, edits files via Regex diffs, and raises Pull Requests.
- **Human-in-the-Loop (HitL)**: Approves or rejects terminal commands in real-time.
- **Swarm Subagents**: Spawns fast, headless background agents to do deep research while managing VRAM handoffs safely to prevent Swap Death.
- **Cross-Agent Brain Importer**: Inherits memory and context directly from Antigravity and Claude Code transcripts.

## Prerequisites
1. [Ollama](https://ollama.com/) installed and running (`http://localhost:11434`).
2. GitHub CLI (`gh`) authenticated (`gh auth login`).
3. Python 3.9+

## Installation
```bash
git clone <this-repo>
cd local-llm-ui
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Edit `config.py` to change default model targets and paths, or set environment variables:
- `FAST_MODEL` (default: `mannix/llama3.1-8b-abliterated:latest`)
- `HEAVY_MODEL` (default: `qwen2.5:32b`)
- `INGEST_MODEL` (default: `granite4:3b-h`)

## Running the Engine
```bash
streamlit run app.py
```
