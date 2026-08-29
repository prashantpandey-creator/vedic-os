import os

# Ollama Connection
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Core Paths
DEFAULT_WORKSPACE_ROOT = os.getenv("VEDIC_WORKSPACES", os.path.expanduser("~/vedic_workspaces"))
DEFAULT_FALLBACK_DIR = os.getenv("DEFAULT_FALLBACK_DIR", os.getcwd())

# External Agent Context Paths
CLAUDE_MEMORY_DIR = os.getenv("CLAUDE_MEMORY_DIR", os.path.expanduser("~/claude-sync/memory"))
ANTIGRAVITY_BRAIN_DIR = os.getenv("ANTIGRAVITY_BRAIN_DIR", os.path.expanduser("~/.gemini/antigravity/brain"))

# Default Models (Users can override these in the UI, but these are the recommended defaults)
FAST_MODEL = os.getenv("FAST_MODEL", "mannix/llama3.1-8b-abliterated:latest")
HEAVY_MODEL = os.getenv("HEAVY_MODEL", "qwen2.5:32b")

# Model that reads the repo and writes the opening blueprint. Must be a GENERAL
# instruct model. It was 'architect-compiler:latest', whose Modelfile pins it to
# emit app specifications — asked to summarise a repo it answered with an invented
# {"name": "TaskManager", ...} spec. cli.py separately hardcoded 'qwen2.5:0.5b',
# which was never pulled, so that path 404'd and produced an empty blueprint.
INGEST_MODEL = os.getenv("INGEST_MODEL", "qwen3:4b-instruct-2507-q4_K_M")

# Small model that performs whole-file rewrites for edit_file + instruction.
EDITOR_MODEL = os.getenv("EDITOR_MODEL", "granite4:3b-h")
