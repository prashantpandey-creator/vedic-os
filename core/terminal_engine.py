import os
import subprocess
import tempfile
import re

class TerminalEngine:
    def __init__(self, workspace_dir="."):
        self.cwd = os.path.abspath(workspace_dir)
        self.background_processes = {}
        
        # Blocked commands. THIS IS A DENY-LIST, NOT A SANDBOX — it stops the
        # obvious ways an agent wrecks a machine, and a determined command can
        # still walk around it (base64, a python one-liner, an unlisted binary).
        # Do not point this at anything you would mind losing.
        self.dangerous_patterns = [
            # recursive / forced deletion, long and short flags
            r"\brm\s+(-\w*[rf]\w*|--recursive|--force)",
            r"\bfind\b.*\s-delete\b", r"\bfind\b.*-exec\s+rm\b",
            r"\bxargs\b.*\brm\b",
            r"\bshutil\.rmtree\b", r"\bos\.remove\b", r"\bos\.unlink\b",
            r"\btrash\b\s+-", r"\bshred\b",
            # privilege escalation
            r"\bsudo\s+", r"\bsu\s+-", r"\bdoas\s+",
            # disk / filesystem destruction
            r"\bmkfs\b", r"\bdd\s+if=", r"\bfdisk\b", r"\bdiskutil\s+(erase|reformat)",
            r">\s*/dev/(sd|disk|nvme)",
            # truncation / clobbering existing files
            r"\btruncate\s+-s\s*0", r"^\s*:?\s*>\s*[^>\s]", r"\bmv\b.*\s/dev/null",
            r"\btee\b\s+(-a\s+)?/etc/",
            # credential + config paths
            r"~/\.ssh", r"\bauthorized_keys\b", r"/etc/(passwd|shadow|sudoers)",
            r"~/\.(zshrc|bashrc|profile|aws|gnupg)\b",
            # database destruction
            r"\bdrop\s+(table|database|schema)\b", r"\btruncate\s+table\b",
            # irreversible git
            r"\bgit\s+push\b.*(--force|-f)\b", r"\bgit\s+reset\s+--hard\b",
            r"\bgit\s+clean\s+-\w*[fd]", r"\bgit\s+branch\s+-D\b",
            # permission blowouts
            r"\bchmod\s+(-R\s+)?777", r"\bchown\s+-R",
            # remote code execution
            r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba|z|)sh\b",
            r"\bbase64\s+(-d|--decode)", r"\beval\s*[\$\(`]",
            # process / system kill
            r"\bkillall\b", r"\bpkill\s+-9\b", r"\bshutdown\b", r"\breboot\b",
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
        # 1. Deny-list intercept
        if self._is_dangerous(cmd):
            return ("🚨 [BLOCKED] This command matches the destructive-command deny-list "
                    "and was not run. Achieve the goal a non-destructive way, or ask the "
                    "user to run it themselves.")

        # 2. Stateful directory tracking — ONLY for a bare 'cd <path>'.
        #    'cd sub && npm test' must fall through to the shell below, which already
        #    runs with cwd=self.cwd. Treating it as a path produced
        #    "[ERROR] Directory does not exist: .../sub && npm test".
        stripped = cmd.strip()
        if stripped.startswith("cd ") and not re.search(r"[&|;\n]", stripped):
            target_dir = os.path.expanduser(stripped[3:].strip())
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

