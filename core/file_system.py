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
    import difflib
    full_path = os.path.join(workspace_dir, file_path)
    with open(full_path, "r", encoding="utf-8") as f:
        old_code = f.read()
    
    search_block = search_block.replace("\r\n", "\n")
    replace_block = replace_block.replace("\r\n", "\n")
    
    if search_block not in old_code:
        raise ValueError(f"Search block not found in {file_path}. The model hallucinated the search text.")
        
    new_code = old_code.replace(search_block, replace_block, 1)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_code)
    
    # Always return a diff string (never None)
    diff = list(difflib.unified_diff(
        old_code.splitlines(keepends=True),
        new_code.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    ))
    return "".join(diff) if diff else f"# No visible diff — whitespace or identical content."

def ingest_repository_to_text(workspace_dir=".", max_chars=100000):
    repo_text = ""
    allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".html", ".css", ".sh"}
    skip_dirs = {'.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp', 'build', 'dist', 'artifacts'}
    
    workspace_dir = os.path.abspath(workspace_dir)
    
    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in sorted(files):
            if not fname.startswith('.') and any(fname.endswith(ext) for ext in allowed_exts):
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, workspace_dir)  # FIXED: relative to workspace, not CWD
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                        content = file.read()
                        repo_text += f"\n\n--- FILE: {rel_path} ---\n{content}\n"
                        if len(repo_text) > max_chars:
                            repo_text += "\n\n... [TRUNCATED: max_chars reached] ..."
                            return repo_text
                except Exception:
                    pass
    return repo_text
