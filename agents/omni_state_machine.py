import os
import orjson
import requests
import re
import subprocess
import streamlit as st
from core.terminal_engine import TerminalEngine
from core.ollama_api import OLLAMA_URL, evict_model
from core.file_system import ingest_repository_to_text, apply_search_replace
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
                if "message" in chunk and "content" in chunk["message"]:
                    blueprint += chunk["message"]["content"]
                    if status_container:
                        status_container.markdown(f"**🐍 Mamba is writing Blueprint:**\n{blueprint}▌")
        if status_container:
            status_container.success(f"**🐍 Mamba Blueprint Complete!**\n{blueprint}")
    except Exception as e:
        blueprint = f"Failed to ingest: {e}"
        if status_container:
            status_container.error(blueprint)
        
    evict_model(meditate_model)
    
    memory = read_compressed_memory(workspace_dir)
    
    registry = ToolRegistry(workspace_dir, None)
    system = f"""You are the Vedic Omni-Agent. You have native Zsh terminal access to this Mac.

=========================================
1. HISTORICAL PROJECT MEMORY (Context)
=========================================
The following is historical context, user preferences, and past conversational memory. Use this to understand WHY you are doing things.
{memory}

=========================================
2. CURRENT CODEBASE BLUEPRINT (State)
=========================================
The following is the real-time structure of the Git repository/codebase as it exists on the hard drive right now. Use this to understand WHAT files exist.
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
    
    subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Omni-Agent Checkpoint: {intent_prompt}"], cwd=workspace_dir, capture_output=True)
    
    return messages, blueprint

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
