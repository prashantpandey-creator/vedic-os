import os

MEMORY_FILE = "PROJECT_MIND.md"

def read_compressed_memory(workspace_dir="."):
    memory = "No memory."
    memory_path = os.path.join(workspace_dir, MEMORY_FILE)
    if os.path.exists(memory_path):
        with open(memory_path, "r", encoding="utf-8") as f:
            memory_lines = f.readlines()
            if len(memory_lines) > 50:
                memory = "".join(memory_lines[:10]) + "\n\n... [OLDER VRITTIS COMPRESSED TO PROTECT VRAM] ...\n\n" + "".join(memory_lines[-30:])
            else:
                memory = "".join(memory_lines)
    return memory

def append_vritti(intent, files_str, status_tag, extra="", workspace_dir="."):
    entry = f"\n- **Intent:** {intent}\n  - **Files Edited:** {files_str}\n  - **Status:** {status_tag}\n"
    if extra:
        entry += f"  - **Note:** {extra}\n"
        
    memory_path = os.path.join(workspace_dir, MEMORY_FILE)
    with open(memory_path, "a", encoding="utf-8") as f:
        f.write(entry)
