import os

MEMORY_FILE = "PROJECT_MIND.md"

def read_compressed_memory(workspace_dir=".", max_chars=2000):
    memory = "No memory."
    memory_path = os.path.join(workspace_dir, MEMORY_FILE)
    if os.path.exists(memory_path):
        with open(memory_path, "r", encoding="utf-8") as f:
            full_memory = f.read()
            if len(full_memory) > max_chars:
                # Keep the beginning (project identity) and the end (recent actions)
                head = full_memory[:500]
                tail = full_memory[-(max_chars - 600):]
                memory = head + "\n\n... [OLDER VRITTIS COMPRESSED] ...\n\n" + tail
            else:
                memory = full_memory
    return memory

def append_vritti(intent, files_str, status_tag, extra="", workspace_dir="."):
    entry = f"\n- **Intent:** {intent}\n  - **Files Edited:** {files_str}\n  - **Status:** {status_tag}\n"
    if extra:
        entry += f"  - **Note:** {extra}\n"
        
    memory_path = os.path.join(workspace_dir, MEMORY_FILE)
    with open(memory_path, "a", encoding="utf-8") as f:
        f.write(entry)
