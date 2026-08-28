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
Output ONLY valid JSON for your next action. Choose ONE action per response:
1. Run a terminal command (e.g. to run tests, list files, or start a build).
2. Edit a file.
3. Finish the task.

Format MUST be exactly one of these:
{{"thought": "reasoning", "action": "run_command", "command": "npm test"}}
{{"thought": "reasoning", "action": "edit_file", "file": "path", "search": "exact old text", "replace": "new text"}}
{{"thought": "reasoning", "action": "done"}}
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
    coder_payload = {
        "model": coder_model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.0}
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
    json_str = raw_response
    if "```json" in json_str: json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str: json_str = json_str.split("```")[1].split("```")[0].strip()
    else:
        match = re.search(r'\{\s*"thought".*?\}', json_str, re.DOTALL)
        if match: json_str = match.group(0)
        
    try:
        return json.loads(json_str)
    except:
        return {"action": "error", "error": "Failed to parse JSON."}
