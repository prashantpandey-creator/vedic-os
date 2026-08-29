import os
import json
import numpy as np
import requests
from config import EMBED_MODEL, MEMORY_MIN_SIM
from core.ollama_api import OLLAMA_URL

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "vyasa_memory_db.json")

_LAST_ERROR = ""


def _get_embedding(text):
    """
    Embed one string.

    Was hardcoded to INGEST_MODEL, which is a chat/instruct model. Ollama answers
    those with {"error": "this model does not support embeddings"} — verified for
    both architect-compiler and qwen3:4b — so every vector came back empty and the
    whole RAG memory returned "Failed to generate vector embeddings" from the day
    it was written. A bare `except:` plus `.get("embedding", [])` hid the reason.
    granite4:3b-h (2048 dims) and llama3.1:8b (4096) do support it.
    """
    global _LAST_ERROR
    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=120,
        ).json()
        if "error" in res:
            _LAST_ERROR = f"model '{EMBED_MODEL}' cannot embed: {res['error']}"
            return []
        vec = res.get("embedding", [])
        if not vec:
            _LAST_ERROR = f"model '{EMBED_MODEL}' returned an empty vector"
        return vec
    except Exception as e:
        _LAST_ERROR = f"{type(e).__name__}: {e}"
        return []

def commit_to_memory(memory_text):
    if not memory_text.strip():
        return "Error: commit_memory needs 'content'."
    vector = _get_embedding(memory_text)
    if not vector:
        return f"Error: could not embed the memory — {_LAST_ERROR}"
    
    db = []
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            db = json.load(f)
            
    db.append({"text": memory_text, "vector": vector})
    
    with open(MEMORY_FILE, "w") as f:
        json.dump(db, f)
    return "✅ Successfully committed experience to Vyasa RAG Memory."

def query_memory(query_text, top_k=3):
    if not os.path.exists(MEMORY_FILE):
        return "No memories recorded yet."
    with open(MEMORY_FILE, "r") as f:
        db = json.load(f)
    if not db:
        return "No memories recorded yet."
    
    query_vec = np.array(_get_embedding(query_text))
    if query_vec.size == 0:
        return f"Error: could not embed the query — {_LAST_ERROR}"
    
    results = []
    for item in db:
        v = np.array(item["vector"])
        # Vectors from different models have different widths; a stored memory
        # written under an older EMBED_MODEL would blow up np.dot. Skip it.
        if v.shape != query_vec.shape:
            continue
        denom = np.linalg.norm(query_vec) * np.linalg.norm(v)
        if denom == 0:
            continue
        results.append((float(np.dot(query_vec, v) / denom), item["text"]))
        
    if not results:
        return "No comparable memories (all stored vectors came from a different embedding model)."
    results.sort(reverse=True, key=lambda x: x[0])
    
    # The original gate was `sim > 0.4`, which filtered nothing. Measured with
    # granite4:3b-h embeddings against "where do API routes go in this project?":
    #   0.822 the actual answer          0.766 "a swallow's airspeed is 11 m/s"
    #   0.855 a same-domain build note   0.730 "Beethoven composed nine symphonies"
    #                                    0.686 a bread recipe
    # Everything scores 0.69-0.86, so 0.4 passed 3/3 unrelated memories. Vectors
    # from a generative model are like that — they encode "is text" more than
    # topic. The real fix is a purpose-built embedder (`ollama pull
    # nomic-embed-text` or mxbai-embed-large, then set EMBED_MODEL); the gate
    # below is calibrated for what is actually installed, and the score is shown
    # so the agent can discount a weak match instead of trusting it blindly.
    relevant = [(sim, text) for sim, text in results[:top_k] if sim > MEMORY_MIN_SIM]
    if not relevant:
        return (f"No memory scored above {MEMORY_MIN_SIM:.2f} (best was "
                f"{results[0][0]:.2f}). Treat this as no relevant memory.")

    return "\n\n---\n\n".join(f"[similarity {sim:.2f}] {text}" for sim, text in relevant)
