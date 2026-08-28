import os
import json
import requests
import re
import subprocess
from core.terminal_engine import TerminalEngine
from core.ollama_api import OLLAMA_URL, evict_model
from core.file_system import ingest_repository_to_text, apply_search_replace
from core.memory_graph import read_compressed_memory, append_vritti

def run_omni_loop(intent_prompt, meditate_model, coder_model, status, stream_placeholder, workspace_dir="."):
    # 1. Massive Git Ingestion (Mamba)
    repo_text, f_count, c_count = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)
    status.write(f"🐍 **[MAMBA INGESTION]** {meditate_model} swallowed {f_count} files ({c_count:,} characters)... Generating Blueprint...")
    
    meditate_payload = {
        "model": meditate_model,
        "messages": [
            {"role": "system", "content": "You are the Vedic Blueprint Generator. Read the provided codebase. Output a dense, highly compressed summary of the architecture, key files, and exactly how they relate to the user's intent. Do not write code. Just write the blueprint."},
            {"role": "user", "content": f"USER INTENT: {intent_prompt}\n\nCODEBASE:\n{repo_text}"}
        ],
        "stream": False,
        "options": {"num_ctx": 32000} # Expand context window for SSM
    }
    
    try:
        res = requests.post(f"{OLLAMA_URL}/api/chat", json=meditate_payload).json()
        blueprint = res.get("message", {}).get("content", "Blueprint failed to generate.")
    except Exception as e:
        blueprint = f"Failed to ingest: {e}"
        
    status.write(f"🧹 **[VRAM]** Evicting {meditate_model} to clear Unified Memory...")
    evict_model(meditate_model)
    
    # 2. Terminal Execution Loop (Qwen)
    status.write(f"🦅 **[OMNI-AGENT]** {coder_model} taking control of Mac Terminal...")
    memory = read_compressed_memory(workspace_dir)
    
    system = f"""You are the Vedic Omni-Agent. You have native Zsh terminal access to this Mac.
PROJECT MEMORY:
{memory}

ARCHITECTURAL BLUEPRINT (from Mamba):
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
    
    # Git Auto-Checkpoint before Omni-Loop
    status.write("📦 **[GIT]** Checkpointing state before Autonomous Loop...")
    subprocess.run(["git", "init"], cwd=workspace_dir, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=workspace_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Omni-Agent Checkpoint: {intent_prompt}"], cwd=workspace_dir, capture_output=True)
    
    # Initialize Revolutionary Terminal Engine
    terminal = TerminalEngine(workspace_dir=workspace_dir)
    
    max_steps = 10
    execution_log = []
    
    for step in range(1, max_steps + 1):
        status.write(f"🦅 **[STEP {step}/{max_steps}]** {coder_model} is deciding next action...")
        
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
                        stream_placeholder.code(raw_response, language="json")
                        
            messages.append({"role": "assistant", "content": raw_response})
            
            # Parse JSON
            json_str = raw_response
            if "```json" in json_str: json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str: json_str = json_str.split("```")[1].split("```")[0].strip()
            else:
                match = re.search(r'\{\s*"thought".*?\}', json_str, re.DOTALL)
                if match: json_str = match.group(0)
                
            action_data = json.loads(json_str)
            action = action_data.get("action")
            
            if action == "done":
                status.write("🎉 **[OMNI-AGENT]** Task declared complete!")
                append_vritti(intent_prompt, "Omni-Loop", "[PRAMANA] Done", extra=f"Completed in {step} steps.", workspace_dir=workspace_dir)
                break
                
            elif action == "run_command":
                cmd = action_data.get("command", "echo 'No command'")
                status.write(f"💻 **[TERMINAL]** Executing: `{cmd}`")
                execution_log.append({"step": step, "type": "command", "cmd": cmd})
                
                # Execute via Revolutionary Terminal Engine
                output = terminal.execute(cmd)
                messages.append({"role": "user", "content": f"Command Executed.\nOutput:\n```\n{output}\n```\nWhat is your next step? Output the JSON action."})
                
            elif action == "edit_file":
                filepath = action_data.get("file")
                search = action_data.get("search", "")
                replace = action_data.get("replace", "")
                status.write(f"📝 **[FILE IO]** Editing `{filepath}`...")
                execution_log.append({"step": step, "type": "edit", "file": filepath})
                
                try:
                    apply_search_replace(filepath, search, replace, workspace_dir=workspace_dir)
                    messages.append({"role": "user", "content": f"File {filepath} edited successfully. What is your next step? Output the JSON action."})
                except Exception as e:
                    messages.append({"role": "user", "content": f"Edit failed: {e}\nPlease fix your search block and try again."})
                    
        except Exception as e:
            status.write(f"⚠️ **[ERROR]** Omni-Loop stumbled: {e}")
            messages.append({"role": "user", "content": f"System Error processing your JSON: {e}. Output exactly valid JSON."})
            
    terminal.cleanup()
    return execution_log, blueprint
