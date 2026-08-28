import os
import re

def build_tree_with_hints(intent_prompt="", workspace_dir="."):
    tree = []
    intent_words = set(re.findall(r'\b\w{4,}\b', intent_prompt.lower()))
    allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".html"}
    
    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp']]
        for f in files:
            if not f.startswith('.'):
                rel_path = os.path.relpath(os.path.join(root, f), ".")
                hints = ""
                if intent_words and any(f.endswith(ext) for ext in allowed_exts):
                    try:
                        with open(rel_path, "r", encoding="utf-8") as file:
                            content = file.read().lower()
                            matches = [w for w in intent_words if w in content]
                            if matches:
                                hints = f" (Contains keywords: {', '.join(matches)})"
                    except: pass
                tree.append(f"{rel_path}{hints}")
    return "\n".join(tree)

def apply_search_replace(file_path, search_block, replace_block, workspace_dir="."):
    file_path = os.path.join(workspace_dir, file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        old_code = f.read()
    
    if search_block not in old_code:
        raise ValueError(f"Search block hallucination in {file_path}")
        
    new_code = old_code.replace(search_block, replace_block, 1)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)

def ingest_repository_to_text(workspace_dir=".", max_chars=100000):
    repo_text = ""
    allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".html", ".css", ".sh"}
    
    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp', 'build', 'dist']]
        for f in files:
            if not f.startswith('.') and any(f.endswith(ext) for ext in allowed_exts):
                rel_path = os.path.relpath(os.path.join(root, f), ".")
                try:
                    with open(rel_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        repo_text += f"\n\n--- FILE: {rel_path} ---\n{content}\n"
                        if len(repo_text) > max_chars:
                            repo_text += "\n\n... [TRUNCATED] ..."
                            return repo_text
                except: pass
    return repo_text
