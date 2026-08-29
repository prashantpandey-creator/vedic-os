import os

def dynamic_route(messages: list) -> str:
    """
    Analyzes the complexity of the conversation history and dynamically load-balances
    between the fast 4B model and the heavy 32B model.
    """
    from config import FAST_MODEL, HEAVY_MODEL
    
    # Heuristic 1: If the user explicitly asks for complex reasoning or tracebacks
    combined_text = "\\n".join([m.get("content", "") for m in messages])
    if "Traceback" in combined_text or "Error:" in combined_text or "refactor" in combined_text.lower():
        return HEAVY_MODEL
        
    # Heuristic 2: If the context window is getting massive
    if len(combined_text) > 8000:
        return HEAVY_MODEL
        
    # Default to blazing fast model for basic tasks (file searching, terminal commands)
    return FAST_MODEL
