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

# Model used for the episodic-memory vectors. MUST support /api/embeddings —
# chat/instruct models answer "this model does not support embeddings", which is
# what silently killed the RAG memory (it was pointed at INGEST_MODEL).
# Verified working: granite4:3b-h (2048 dims), llama3.1:8b (4096 dims).
EMBED_MODEL = os.getenv("EMBED_MODEL", "granite4:3b-h")

# Cosine-similarity floor for episodic memory. The original 0.4 filtered nothing —
# embeddings from a generative model cluster in a narrow 0.69-0.86 band, so
# unrelated memories all passed. Lower this if you switch EMBED_MODEL to a real
# embedder (nomic-embed-text, mxbai-embed-large), which separates properly.
MEMORY_MIN_SIM = float(os.getenv("MEMORY_MIN_SIM", "0.80"))

# Vision model for visual_debug. Not pulled by default — `ollama pull llama3.2-vision`.
VISION_MODEL = os.getenv("VISION_MODEL", "llama3.2-vision")
