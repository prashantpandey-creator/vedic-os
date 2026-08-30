import orjson
import re
import subprocess
from core.file_system import build_tree_with_hints
from core.memory_graph import read_compressed_memory
from core.tool_registry import ToolRegistry

def init_omni_loop(intent_prompt, meditate_model=None, coder_model=None, workspace_dir=".", status_container=None):
    """
    Build the opening message list for a run.

    `meditate_model` is accepted and IGNORED. It used to name a model that read
    the whole repo and wrote a prose "blueprint" into the system prompt. That call
    is gone. Measured, on this repo's own ingest (17,703 tokens):

      - it cost 80.1s median per session, every session
      - both the SSM and the transformer cited **0 of 5** real filenames from this
        codebase. granite paraphrased PROJECT_MIND.md — the memory file, not the
        code; qwen3 cited `launch.sh`, which does not exist here.

    So the section headed "use this to understand WHAT files exist" was being
    filled with invented paths. Routing it to a faster model buys a faster wrong
    answer, so it is deleted rather than re-routed.

    `build_tree_with_hints` already supplies the file list, deterministically, in
    well under a second. It cannot be empty and it cannot be wrong.

    The parameter stays in the signature because six call sites pass it
    positionally; dropping it would break app.py and other sessions' tests for no
    gain. Removing three defects with it:
      - the hardcoded `num_ctx: 16000` that silently truncated a 17,703-token
        ingest to exactly 16000, dropping ~1,703 tokens of the repo tail
      - `max_chars=60000` overshooting to 78,675 chars (the budget was checked
        after appending a whole file, not before)
      - the `🐍 Mamba` status strings, which sat on this path while it ran a
        transformer
    """
    if status_container:
        status_container.info("📂 Reading the file tree...")

    memory = read_compressed_memory(workspace_dir)

    # Ground truth about what exists. Deterministic — no model, so it cannot come
    # back empty or invented the way the LLM blueprint could.
    file_tree = build_tree_with_hints(intent_prompt, workspace_dir)

    if status_container:
        status_container.success(f"📂 {len(file_tree.splitlines())} files on disk.")

    registry = ToolRegistry(workspace_dir, None)
    system = f"""You are the Vedic Omni-Agent. You have native Zsh terminal access to this Mac.

TEST-DRIVEN DEVELOPMENT ENFORCEMENT:
If the user asks you to build a feature or fix a bug, you MUST create a unit test file (using pytest or jest) FIRST. 
You must then run the test (it should fail), write the code, and repeatedly run the test until it passes. 
Do not output "action": "done" until the tests pass green in the terminal.


=========================================
1. HISTORICAL PROJECT MEMORY (Context)
=========================================
The following is historical context, user preferences, and past conversational memory. Use this to understand WHY you are doing things.
{memory}

=========================================
2. FILES ON DISK (ground truth — read this before naming any path)
=========================================
Every file in the workspace right now. If a path is not in this list, it does not exist.
{file_tree}
=========================================

You must accomplish the user's intent autonomously.
First, write out a detailed, verbose thought process explaining your reasoning. 
Second, you MUST write a "CRITIQUE:" section where you aggressively challenge your own plan. Ask yourself: "What could go wrong? Is there a safer way? Am I hallucinating a file path?"
Finally, after your critique, output your chosen action strictly inside a ```json block.
{registry.get_system_prompt_addition()}
"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": intent_prompt}
    ]
    
    _warn_if_workspace_unprotected(workspace_dir)

    # Second return value kept: cli.py, app.py and backend/main.py all unpack two
    # values and display it. They now show the real file tree instead of a model's
    # guess about it, which is strictly more useful to a human watching the run.
    return messages, file_tree


def _warn_if_workspace_unprotected(workspace_dir):
    """
    Report whether the agent's edits will be recoverable. Warn only — never write.

    This replaces an unconditional `git init && git add . && git commit`, which
    created repos inside directories that had none and committed whatever was
    already sitting uncommitted in the tree — including work belonging to someone
    else. This repo's own log still carries 11 "Omni-Agent Checkpoint:" commits
    whose messages are pasted LeetCode problems.
    """
    inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                            cwd=workspace_dir, capture_output=True, text=True)
    if inside.returncode != 0:
        print(f"[CHECKPOINT] ⚠️  {workspace_dir} is not a git repo. Agent edits will "
              f"NOT be recoverable. `git init && git commit` first if you care about them.")
        return None

    head = subprocess.run(["git", "rev-parse", "HEAD"],
                          cwd=workspace_dir, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"],
                           cwd=workspace_dir, capture_output=True, text=True).stdout.strip()
    if dirty:
        print(f"[CHECKPOINT] ⚠️  Working tree has {len(dirty.splitlines())} uncommitted "
              f"change(s). Those are NOT checkpointed — the agent's edits will mix into "
              f"them. Commit or stash first to keep the two separable.")
    print(f"[CHECKPOINT] Pre-agent HEAD is {head[:8]}. Undo everything with: "
          f"git diff {head[:8]}  /  git checkout {head[:8]} -- .")
    return head

def generate_next_thought(coder_model, messages, step_placeholder):
    from core.llm_gateway import generate_response
    # Offload everything to the Hybrid Gateway
    return generate_response(coder_model, messages)
def parse_action(raw_response):
    """
    Extracts and parses a JSON action from raw model output.
    Handles: clean JSON, ```json blocks, bare ``` blocks, 
    inline JSON with surrounding prose, and multiline JSON.
    """
    if not raw_response or not raw_response.strip():
        return {"action": "error", "error": "Empty model response."}
    
    text = raw_response.strip()

    # 1. Try markdown code fence first
    for fence in ["```json", "```"]:
        if fence in text:
            inner = text.split(fence)[1].split("```")[0].strip()
            for candidate in (inner, _escape_raw_control_chars(inner)):
                try:
                    return orjson.loads(candidate)
                except Exception:
                    pass

    # 2. Brace-counting extractor — handles multiline JSON
    start = text.find("{")
    if start != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i, ch in enumerate(text[start:], start):
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
            if not in_string:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:i + 1]
                        for attempt in (candidate, _escape_raw_control_chars(candidate)):
                            try:
                                return orjson.loads(attempt)
                            except Exception:
                                pass
                        break

    return {"action": "error", "error": f"Could not parse JSON from: {text[:200]}"}


def _escape_raw_control_chars(candidate):
    """
    Repair the one thing small models get wrong constantly: a literal newline
    inside a JSON string value. Strict JSON forbids it, so orjson rejects the
    whole block.

    This REPLACES a `" ".join(candidate.split())` fallback that collapsed every
    run of whitespace in the document. That turned

        "search": "def add(a, b):
            return a - b"

    into "def add(a, b): return a - b" — newline and indentation gone. It could
    never match indented Python, so every search/replace edit failed with
    "Search block not found ... The model hallucinated the search text." The
    model had not hallucinated; the parser had flattened its output and the error
    blamed the model. Measured on the fix_bug acceptance task: 5 of 5 edits lost
    this way, the target file left byte-identical.

    Escaping instead of collapsing preserves the text exactly, which is the whole
    point of a search block.
    """
    out = []
    in_string = False
    escape_next = False
    for ch in candidate:
        if escape_next:
            out.append(ch)
            escape_next = False
            continue
        if ch == "\\" and in_string:
            out.append(ch)
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in "\n\r\t\b\f":
            out.append({"\n": "\\n", "\r": "\\r", "\t": "\\t",
                        "\b": "\\b", "\f": "\\f"}[ch])
            continue
        out.append(ch)
    return "".join(out)
