import os
import json
import requests
import re
import subprocess
import streamlit as st
from core.terminal_engine import TerminalEngine
from core.ollama_api import OLLAMA_URL, evict_model
from core.file_system import ingest_repository_to_text, apply_search_replace
from core.memory_graph import read_compressed_memory, append_vritti
from core.tool_registry import ToolRegistry

def init_omni_loop(intent_prompt, meditate_model, coder_model, workspace_dir="."):
    repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)
    
    meditate_payload = {
        "model": meditate_model,
        "messages": [
            {"role": "system", "content": "You are the Vedic Blueprint Generator. Read the codebase and output a compressed summary."},
            {"role": "user", "content": f"USER INTENT: {intent_prompt}\\n\\nCODEBASE:\\n{repo_text}"}
        ],
        "stream": False,
        "options": {"num_ctx": 32000}
    }
    
    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload).json()
        blueprint = res.get("message", {}).get("content", "Blueprint failed to generate.")
    except Exception as e:
        blueprint = f"Failed to ingest: {e}"
        
    evict_model(meditate_model)
    
    memory = read_compressed_memory(workspace_dir)
    
    registry = ToolRegistry(workspace_dir, None)
    system = f"""You are the Vedic Omni-Agent. You have native Zsh terminal access to this Mac.
PROJECT MEMORY:
{memory}

ARCHITECTURAL BLUEPRINT:
{blueprint}

You must accomplish the user's intent autonomously.
Output ONLY valid JSON for your next action.
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
    # --- SLIDING WINDOW COMPACTION ---
    # Keep: system prompt (messages[0]) + last 6 messages (3 turn pairs)
    # Compress everything in between into a single summary message
    MAX_CONTEXT_MESSAGES = 10  # system + 4 turn pairs + buffer
    
    if len(messages) > MAX_CONTEXT_MESSAGES:
        system_msg = messages[0]
        old_turns = messages[1:-6]
        recent = messages[-6:]
        
        summary = "PRIOR CONTEXT SUMMARY (older steps compressed to save memory):\n"
        for msg in old_turns:
            role = msg["role"]
            content = msg["content"][:200]
            summary += f"- [{role}]: {content}...\n"
        
        messages.clear()
        messages.append(system_msg)
        messages.append({"role": "user", "content": summary})
        messages.extend(recent)
    
    coder_payload = {
        "model": coder_model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.0, "num_ctx": 8192}
    }
    
    try:
        coder_res = requests.post(f"{OLLAMA_URL}/api/chat", json=coder_payload, stream=True)
        raw_response = ""
        for line in coder_res.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    raw_response += chunk["message"]["content"]
                    step_placeholder.code(raw_response, language="json")
                    
        return raw_response
    except Exception as e:
        return str(e)

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
                return json.loads(inner)
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
                            return json.loads(candidate)
                        except Exception:
                            # Try collapsing whitespace (fixes newlines inside string values)
                            try:
                                collapsed = " ".join(candidate.split())
                                return json.loads(collapsed)
                            except Exception:
                                break
    
    return {"action": "error", "error": f"Could not parse JSON from: {text[:200]}"}
