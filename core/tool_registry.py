import os
import json
import re
import subprocess
import requests
from core.file_system import apply_search_replace
from core.ollama_api import OLLAMA_URL, evict_model
from config import FAST_MODEL

class ToolRegistry:
    def __init__(self, workspace_dir, terminal_engine):
        self.workspace_dir = workspace_dir
        self.terminal = terminal_engine
        
    def get_system_prompt_addition(self):
        return """
Available Tools (Choose ONE per response):

1. run_command (NOTE: You have access to modern Rust binaries: 'rg', 'fdfind', 'batcat'. WARNING: Each command runs in a fresh shell. You cannot 'cd' and expect it to persist to the next step. Chain commands with &&.)
{"thought": "...", "action": "run_command", "command": "npm test"}

2. edit_file
{"thought": "...", "action": "edit_file", "file": "path", "instruction": "Detailed instruction on what to change"}

4. create_artifact (Generate permanent reports, plans, or full files)
{"thought": "...", "action": "create_artifact", "title": "ArchitecturePlan", "content": "# Markdown Content..."}

5. invoke_subagent (Spawn a fast background agent to do research or recursive tasks)
{"thought": "...", "action": "invoke_subagent", "role": "researcher", "task": "Find all API routes returning 404"}

6. create_pull_request (Push local edits to a new branch and raise a PR on GitHub)
{"thought": "...", "action": "create_pull_request", "branch_name": "fix-auth-bug", "title": "Fix Auth Bug", "body": "Fixed the token expiration issue."}

7. done
{"thought": "...", "action": "done"}
"""

    def execute_tool(self, action_data, fast_model=FAST_MODEL, main_model=None):
        action = action_data.get("action")
        
        if action == "run_command":
            cmd = action_data.get("command", "")
            output = self.terminal.execute(cmd)
            return {"type": "command", "cmd": cmd, "output": output, "msg": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```"}
            
        elif action == "create_file":
            filepath = action_data.get("file")
            content = action_data.get("content", "")
            import os
            full_path = os.path.join(self.workspace_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"type": "edit", "file": filepath, "diff": "File created.", "msg": f"File {filepath} created successfully."}
            
        elif action == "edit_file":
            filepath = action_data.get("file")
            try:
                diff_str = apply_search_replace(filepath, action_data.get("search", ""), action_data.get("replace", ""), self.workspace_dir)
                return {"type": "edit", "file": filepath, "diff": diff_str, "msg": f"File {filepath} edited successfully."}
            except Exception as e:
                return {"type": "error", "msg": f"Edit failed: {e}. Fix search block."}
                
        elif action == "create_artifact":
            title = action_data.get("title", "artifact").replace(" ", "_")
            content = action_data.get("content", "")
            art_dir = os.path.join(self.workspace_dir, "artifacts")
            os.makedirs(art_dir, exist_ok=True)
            path = os.path.join(art_dir, f"{title}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"type": "artifact", "title": title, "path": path, "msg": f"Artifact '{title}' created successfully at artifacts/{title}.md"}
            
        elif action == "create_pull_request":
            branch = action_data.get("branch_name", "agent-update")
            title = action_data.get("title", "Autonomous Agent Update")
            body = action_data.get("body", "Changes pushed by Omni-Agent")
            
            try:
                # 1. Check out new branch
                subprocess.run(["git", "checkout", "-b", branch], cwd=self.workspace_dir, capture_output=True)
                # 2. Add all changes
                subprocess.run(["git", "add", "."], cwd=self.workspace_dir, capture_output=True)
                # 3. Commit
                subprocess.run(["git", "commit", "-m", title], cwd=self.workspace_dir, capture_output=True)
                # 4. Push to remote
                subprocess.run(["git", "push", "-u", "origin", branch], cwd=self.workspace_dir, capture_output=True)
                # 5. Raise PR via GH CLI
                pr_res = subprocess.run(["gh", "pr", "create", "--title", title, "--body", body, "--head", branch], cwd=self.workspace_dir, capture_output=True, text=True)
                
                if pr_res.returncode == 0:
                    pr_url = pr_res.stdout.strip()
                    return {"type": "github_pr", "url": pr_url, "msg": f"✅ Pull Request raised successfully!\nURL: {pr_url}"}
                else:
                    return {"type": "error", "msg": f"Failed to raise PR: {pr_res.stderr}"}
            except Exception as e:
                return {"type": "error", "msg": f"Git/GH Exception: {e}"}

        elif action == "invoke_subagent":
            role = action_data.get("role", "subagent")
            task = action_data.get("task", "")
            
            # VRAM Safety Handoff: evict main model before spawning subagent
            if main_model and main_model != fast_model:
                evict_model(main_model)
                
            sub_msg, sub_log = self._run_headless_subagent(role, task, fast_model)
            
            # Evict subagent and let main model reload
            if main_model and main_model != fast_model:
                evict_model(fast_model)
                
            return {"type": "subagent", "role": role, "task": task, "log": sub_log, "msg": f"Subagent '{role}' completed task. Result:\\n{sub_msg}"}
            
        return {"type": "error", "msg": f"Unknown action: {action}"}

    def _run_headless_subagent(self, role, task, model):
        # A lightweight 3-step loop purely for research/grep
        sys_prompt = f"You are a Subagent (Role: {role}). You have terminal access. Task: {task}. Use run_command to find info. When done, output action: 'done' and 'result': 'summary'."
        messages = [{"role": "system", "content": sys_prompt}]
        
        sub_log = []
        result_msg = "Task failed to yield a specific result."
        
        for _ in range(3):
            try:
                res = requests.post(f"{OLLAMA_URL}/api/chat", json={"model": model, "messages": messages, "options": {"temperature": 0.0}}).json()
                raw = res.get("message", {}).get("content", "")
                messages.append({"role": "assistant", "content": raw})
                
                # Parse JSON quickly
                match = re.search(r'\{\s*"action".*?\}', raw, re.DOTALL)
                if match: 
                    data = json.loads(match.group(0))
                else: 
                    data = {"action": "done", "result": raw} # fallback
                    
                act = data.get("action")
                if act == "done":
                    result_msg = data.get("result", raw)
                    sub_log.append(f"Subagent concluded: {result_msg}")
                    break
                elif act == "run_command":
                    cmd = data.get("command", "")
                    out = self.terminal.execute(cmd)
                    sub_log.append(f"$ {cmd}\\n> {out[:100]}...")
                    messages.append({"role": "user", "content": f"Output: {out}"})
            except Exception as e:
                result_msg = f"Subagent crashed: {e}"
                break
                
        return result_msg, sub_log
