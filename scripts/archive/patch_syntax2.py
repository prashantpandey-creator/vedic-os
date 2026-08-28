import sys

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "r") as f:
    content = f.read()

old_func = """            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please carefully review your python syntax and try again.")
            
    # Always return a diff string (never None)"""

new_func = """            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please carefully review your python syntax and try again.")
            
    elif full_path.endswith(".js") or full_path.endswith(".jsx"):
        import subprocess
        res = subprocess.run(["node", "--check", full_path], capture_output=True, text=True)
        if res.returncode != 0:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(old_code)
            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a JS syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please review your syntax.")
            
    # Always return a diff string (never None)"""

content = content.replace(old_func, new_func)

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.write(content)
