import os
import re

def build_tree_with_hints(intent_prompt="", workspace_dir=".", max_files=400):
    """
    Deterministic file listing, with a note on which files mention words from the
    intent. This is what tells the agent WHAT EXISTS — no model in the loop, so it
    cannot be empty, stale, or hallucinated.
    """
    tree = []
    intent_words = set(re.findall(r'\b\w{4,}\b', intent_prompt.lower()))
    allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".html"}
    workspace_dir = os.path.abspath(workspace_dir)

    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in
                   ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp',
                    'build', 'dist', '.omni_checkpoints']]
        for f in sorted(files):
            if f.startswith('.'):
                continue
            full_path = os.path.join(root, f)
            # relpath against the workspace, NOT the process CWD — the old version
            # then tried to open() that CWD-relative path and silently found nothing.
            rel_path = os.path.relpath(full_path, workspace_dir)
            hints = ""
            if intent_words and any(f.endswith(ext) for ext in allowed_exts):
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                        content = file.read().lower()
                    matches = sorted(w for w in intent_words if w in content)
                    if matches:
                        hints = f"  (mentions: {', '.join(matches[:6])})"
                except Exception:
                    pass
            tree.append(f"{rel_path}{hints}")
            if len(tree) >= max_files:
                tree.append(f"... [truncated at {max_files} files]")
                return "\n".join(tree)
    return "\n".join(tree)

def _unified_diff(old_code, new_code, file_path):
    import difflib
    diff = list(difflib.unified_diff(
        old_code.splitlines(keepends=True),
        new_code.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    ))
    return "".join(diff) if diff else "# No visible diff — whitespace or identical content."


def write_verified(full_path, new_code, old_code, file_path=None):
    """
    The ONE write path for agent edits. Writes new_code, then proves the file is
    still parseable; reverts to old_code and raises if it is not.

    Every agent edit — search/replace or whole-file model rewrite — goes through
    here. Nothing writes to disk behind its back.
    """
    file_path = file_path or full_path

    # A model that returns nothing (or a stub) is truncation, not an edit.
    if not new_code.strip():
        raise ValueError(
            f"🚨 EMPTY OUTPUT REJECTED for {file_path}. The model returned no code. "
            f"The file was left untouched."
        )
    if old_code.strip() and len(new_code) < len(old_code) * 0.4:
        raise ValueError(
            f"🚨 TRUNCATION REJECTED for {file_path}. The model returned "
            f"{len(new_code)} chars to replace {len(old_code)} (<40%). This is almost "
            f"always a cut-off response, not a real edit. The file was left untouched. "
            f"Use a search/replace edit on the specific lines instead of a full rewrite."
        )

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_code)

    checkers = {
        ".py": ["python3", "-m", "py_compile", full_path],
        ".js": ["node", "--check", full_path],
        ".jsx": ["node", "--check", full_path],
    }
    cmd = checkers.get(os.path.splitext(full_path)[1])
    if cmd:
        import subprocess
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(old_code)
                raise ValueError(
                    f"🚨 SYNTAX ERROR PREVENTED in {file_path}:\n{res.stderr}\n"
                    f"The edit was REVERTED. Review the syntax and try again."
                )
        except FileNotFoundError:
            pass  # checker binary absent — write stands, unverified

    return _unified_diff(old_code, new_code, file_path)


def apply_search_replace(file_path, search_block, replace_block, workspace_dir="."):
    full_path = os.path.join(workspace_dir, file_path)
    with open(full_path, "r", encoding="utf-8") as f:
        old_code = f.read()

    search_block = search_block.replace("\r\n", "\n")
    replace_block = replace_block.replace("\r\n", "\n")

    # An empty search block matches at position 0 and silently PREPENDS.
    if not search_block:
        raise ValueError(
            f"Empty search block for {file_path}. Supply the exact existing text to replace."
        )
    if search_block in old_code:
        new_code = old_code.replace(search_block, replace_block, 1)
    else:
        span = _find_block_ignoring_blank_lines(old_code, search_block)
        if span is None:
            # Point at the escape hatch. Without this the model retries
            # search/replace forever — which is exactly what it did when asked to
            # ADD a function, because there is no existing text to anchor to.
            raise ValueError(
                f"Search block not found in {file_path}.\n"
                f"The file's ACTUAL content is:\n---\n{old_code[:1200]}\n---\n"
                f"Either copy those lines byte-for-byte into 'search', or — if you are "
                f"ADDING new code rather than changing existing code — use the "
                f"instruction form instead:\n"
                f'{{"action": "edit_file", "file": "{file_path}", "instruction": '
                f'"describe the change; the whole file will be rewritten"}}'
            )
        s, e = span
        new_code = old_code[:s] + replace_block + old_code[e:]

    return write_verified(full_path, new_code, old_code, file_path)


def _find_block_ignoring_blank_lines(haystack, needle):
    """
    Locate `needle` in `haystack` when the only difference is blank-line count or
    trailing whitespace. Returns (start, end) char offsets, or None.

    Small models reproduce code almost right and spacing almost never. Measured
    on the fix_bug acceptance task: the model emitted

        def add(a, b):
            return a - b
        <ONE blank line>
        def multiply(a, b):

    against a PEP8 file with TWO blank lines between functions. Byte-exact
    matching rejected it, apply_search_replace reported "the model hallucinated
    the search text", and the agent burned every step retrying an edit that was
    substantively correct.

    Indentation is deliberately NOT relaxed — it is semantic in Python, and a
    match that ignored it would apply the edit to the wrong block. Only blank
    lines between content lines and trailing whitespace are forgiven.
    """
    def content_lines(text):
        return [(i, ln.rstrip()) for i, ln in enumerate(text.split("\n")) if ln.strip()]

    hay = text_lines = haystack.split("\n")
    h_content = content_lines(haystack)
    n_content = content_lines(needle)
    if not n_content:
        return None

    n_stripped = [ln for _, ln in n_content]
    for start in range(len(h_content) - len(n_content) + 1):
        window = [ln for _, ln in h_content[start:start + len(n_content)]]
        if window != n_stripped:
            continue
        first_line = h_content[start][0]
        last_line = h_content[start + len(n_content) - 1][0]
        # char offsets: start of first matched line .. end of last matched line
        s = sum(len(l) + 1 for l in text_lines[:first_line])
        e = sum(len(l) + 1 for l in text_lines[:last_line]) + len(hay[last_line])
        return s, e
    return None

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
