import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "r") as f:
    content = f.read()

# Import the new TerminalEngine
import_block = """import subprocess
from core.ollama_api import OLLAMA_URL, evict_model"""
new_import = """import subprocess
from core.terminal_engine import TerminalEngine
from core.ollama_api import OLLAMA_URL, evict_model"""
content = content.replace(import_block, new_import)

# Initialize the engine
old_loop_start = """    max_steps = 10
    execution_log = []"""
new_loop_start = """    # Initialize Revolutionary Terminal Engine
    terminal = TerminalEngine()
    
    max_steps = 10
    execution_log = []"""
content = content.replace(old_loop_start, new_loop_start)

# Replace naive subprocess with terminal.execute
old_exec = """                # Execute on Mac
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                output = (result.stdout + "\\n" + result.stderr).strip()
                if not output: output = "[Command executed silently with exit code 0]"
                
                # Truncate massive outputs
                if len(output) > 4000: output = output[:4000] + "... [TRUNCATED]"
                
                messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```\\nWhat is your next step? Output the JSON action."})"""

new_exec = """                # Execute via Revolutionary Terminal Engine
                output = terminal.execute(cmd)
                messages.append({"role": "user", "content": f"Command Executed.\\nOutput:\\n```\\n{output}\\n```\\nWhat is your next step? Output the JSON action."})"""
content = content.replace(old_exec, new_exec)

# Cleanup daemons on exit
old_return = """    return execution_log, blueprint"""
new_return = """    terminal.cleanup()
    return execution_log, blueprint"""
content = content.replace(old_return, new_return)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "w") as f:
    f.write(content)

print("omni_agent.py patched to use TerminalEngine.")
