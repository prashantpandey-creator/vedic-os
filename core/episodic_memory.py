import os
import json
import numpy as np
import requests
from config import INGEST_MODEL
from core.ollama_api import OLLAMA_URL

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "..", "vyasa_memory_db.json")

def _get_embedding(text):
    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": INGEST_MODEL, "prompt": text},
            timeout=120
        ).json()
        return res.get("embedding", [])
    except:
        return []

def commit_to_memory(memory_text):
    vector = _get_embedding(memory_text)
    if not vector:
        return "Error: Failed to generate vector embeddings."
    
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
        return "Error generating query vector."
    
    results = []
    for item in db:
        v = np.array(item["vector"])
        # Cosine similarity
        sim = np.dot(query_vec, v) / (np.linalg.norm(query_vec) * np.linalg.norm(v))
        results.append((sim, item["text"]))
        
    results.sort(reverse=True, key=lambda x: x[0])
    
    # Filter out low relevance
    relevant = [text for sim, text in results[:top_k] if sim > 0.4]
    if not relevant:
        return "No relevant memories found."
    
    return "\n\n---\n\n".join(relevant)
