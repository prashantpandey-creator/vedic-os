import os
import subprocess
import tempfile
import re

class TerminalEngine:
    def __init__(self, workspace_dir="."):
        self.cwd = os.path.abspath(workspace_dir)
        self.background_processes = {}
        
        # Dangerous commands that trigger the Sandbox Lexer
        self.dangerous_patterns = [
            r"rm\s+-r", r"rm\s+-f", r"sudo\s+", r"mkfs", r"drop\s+(table|database)",
            r">\s*/dev/sda", r"chmod\s+-R\s+777", r"chown\s+-R"
        ]
        
    def _is_dangerous(self, cmd):
        for pattern in self.dangerous_patterns:
            if re.search(pattern, cmd, re.IGNORECASE):
                return True
        return False
        
    def _is_long_running(self, cmd):
        long_running_keywords = ["npm run dev", "npm start", "python -m http.server", "streamlit run", "uvicorn", "flask run"]
        return any(keyword in cmd for keyword in long_running_keywords)

    def execute(self, cmd):
        # 1. Sandbox Intercept
        if self._is_dangerous(cmd):
            return "🚨 [SANDBOX INTERCEPT] PERMISSION DENIED: Destructive command detected. The Vedic Sandbox blocked this execution."
            
        # 2. Stateful Directory Tracking (The 'cd' amnesia fix)
        if cmd.strip().startswith("cd "):
            target_dir = cmd.strip()[3:].strip()
            new_cwd = os.path.abspath(os.path.join(self.cwd, target_dir))
            if os.path.isdir(new_cwd):
                self.cwd = new_cwd
                return f"[STATE] Changed directory to: {self.cwd}"
            else:
                return f"[ERROR] Directory does not exist: {new_cwd}"
                
        # 3. Background Daemon Spawner
        if self._is_long_running(cmd) or cmd.strip().endswith("&"):
            clean_cmd = cmd.strip().rstrip("&").strip()
            process = subprocess.Popen(
                clean_cmd, shell=True, cwd=self.cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            self.background_processes[process.pid] = process
            return f"🔌 [DAEMON HOOK] Spawned long-running process in background.\nPID: {process.pid}\nUse 'kill {process.pid}' to terminate it."
            
        # 4. Standard Execution
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=self.cwd,
                capture_output=True, text=True, timeout=60, errors="replace"
            )
            output = result.stdout + "\n" + result.stderr
            output = output.strip()
            
            if not output:
                return "[Command executed silently with exit code 0]"
                
            # 5. Semantic Pager
            if len(output.splitlines()) > 100:
                # Write full output to a temp log file
                temp_log = tempfile.NamedTemporaryFile(delete=False, suffix=".log", mode="w", encoding="utf-8")
                temp_log.write(output)
                temp_log.close()
                
                # Feed a truncated summary back to the agent
                summary = "\n".join(output.splitlines()[:20])
                return f"{summary}\n\n... [STDOUT OVERFLOW: Massive output detected. Full output saved to {temp_log.name}. Use 'grep', 'head', or 'tail' on that file to parse it safely.]"
                
            return output
            
        except subprocess.TimeoutExpired:
            return "⏳ [TIMEOUT] Command exceeded 60 seconds and was killed."
        except Exception as e:
            return f"⚠️ [EXECUTION FATAL] {e}"
            
    def cleanup(self):
        # Kill all background daemons when agent finishes
        for pid, process in self.background_processes.items():
            try:
                process.terminate()
            except: pass
        self.background_processes.clear()

