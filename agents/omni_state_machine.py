import os
import orjson
import requests
import re
import subprocess
import streamlit as st
from core.terminal_engine import TerminalEngine
from core.ollama_api import OLLAMA_URL, evict_model
from core.file_system import ingest_repository_to_text, apply_search_replace, build_tree_with_hints
from core.memory_graph import read_compressed_memory, append_vritti
from core.tool_registry import ToolRegistry

def init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir=".", status_container=None):
    if status_container:
        status_container.info("📂 Scanning filesystem and extracting active codebase...")
        
    repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=60000)
    
    file_count = repo_text.count("--- FILE:")
    char_count = len(repo_text)
    
    if status_container:
        status_container.info(f"🐍 Passed {file_count} files ({char_count} chars) to Mamba model `{meditate_model}`. Synthesizing blueprint...")
        
    meditate_payload = {
        "model": meditate_model,
        "messages": [
            {"role": "system", "content": "You are the Vedic Blueprint Generator. Read the codebase and output a compressed summary. EXTREME BREVITY REQUIRED: Output a maximum of 5 bullet points. Do not write paragraphs."},
            {"role": "user", "content": f"USER INTENT: {intent_prompt}\n\nCODEBASE:\n{repo_text}"}
        ],
        "stream": True,
        "options": {"num_ctx": 16000}
    }
    
    blueprint = ""
    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload, stream=True)
        for line in res.iter_lines():
            if line:
                chunk = orjson.loads(line)
                # Ollama reports a missing model as a 200 with an {"error": ...} line.
                # This used to fall through the "message" check silently, leaving the
                # blueprint empty and the agent blind about which files exist.
                if "error" in chunk:
                    raise RuntimeError(f"Ollama rejected model '{meditate_model}': {chunk['error']}")
                if "message" in chunk and "content" in chunk["message"]:
                    blueprint += chunk["message"]["content"]
                    if status_container:
                        status_container.markdown(f"**🐍 Writing Blueprint:**\n{blueprint}▌")
        if not blueprint.strip():
            raise RuntimeError(f"model '{meditate_model}' returned an empty blueprint")
        if status_container:
            status_container.success(f"**🐍 Blueprint Complete!**\n{blueprint}")
    except Exception as e:
        # Loud, and loud INSIDE the system prompt — the agent must know it is blind.
        blueprint = (
            f"[BLUEPRINT UNAVAILABLE: {e}]\n"
            f"You do NOT have a summary of this codebase. Do not guess at file paths. "
            f"Start by running a command such as `ls -R` or `rg --files` to discover "
            f"what actually exists before editing anything."
        )
        print(f"[BLUEPRINT] ⚠️  {e}")
        if status_container:
            status_container.error(blueprint)

    evict_model(meditate_model)
    
    memory = read_compressed_memory(workspace_dir)

    # Ground truth about what exists. Deterministic — no model, so it cannot come
    # back empty or invented the way the LLM blueprint could.
    file_tree = build_tree_with_hints(intent_prompt, workspace_dir)

    registry = ToolRegistry(workspace_dir, None)
    system = f"""You are the Vedic Omni-Agent. You have native Zsh terminal access to this Mac.

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
3. ORIENTATION (a model's read of the codebase — may be wrong, the list above is not)
=========================================
{blueprint}
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

    return messages, blueprint


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
            try:
                inner = text.split(fence)[1].split("```")[0].strip()
                return orjson.loads(inner)
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
                        candidate = text[start:i+1]
                        try:
                            return orjson.loads(candidate)
                        except Exception:
                            # Try collapsing whitespace (fixes newlines inside string values)
                            try:
                                collapsed = " ".join(candidate.split())
                                return orjson.loads(collapsed)
                            except Exception:
                                break
    
    return {"action": "error", "error": f"Could not parse JSON from: {text[:200]}"}
