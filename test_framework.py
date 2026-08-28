import sys
import os

# Create mock streamlit objects
class MockStatus:
    def write(self, msg): print(f"[UI] {msg}")

class MockProgressBar:
    def progress(self, val): print(f"[UI Progress] {val}%")

try:
    print("--- Testing Core Imports ---")
    from core.ollama_api import get_models
    from core.file_system import build_tree_with_hints
    from core.memory_graph import read_compressed_memory
    print("Core Imports OK")
    
    print("--- Testing Agent Imports ---")
    from agents.architect import run_architect_pipeline
    from agents.coder_nidra import run_nidra_pipeline
    print("Agent Imports OK")
    
    print("--- Testing execution of functions ---")
    print(f"Models: {get_models()}")
    print("Memory check OK.")
    
except Exception as e:
    import traceback
    print(f"FAILED: {e}")
    traceback.print_exc()
