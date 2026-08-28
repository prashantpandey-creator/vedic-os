import sys

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "r") as f:
    content = f.read()

old_func = """    new_code = old_code.replace(search_block, replace_block, 1)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_code)
    
    # Always return a diff string (never None)
    diff = list(difflib.unified_diff("""

new_func = """    new_code = old_code.replace(search_block, replace_block, 1)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_code)
        
    # --- SELF-HEALING SYNTAX CHECKER ---
    # If it's a python file, ensure we didn't just break the AST.
    if full_path.endswith(".py"):
        import subprocess
        res = subprocess.run(["python3", "-m", "py_compile", full_path], capture_output=True, text=True)
        if res.returncode != 0:
            # Revert the file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(old_code)
            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please carefully review your python syntax and try again.")
            
    # Always return a diff string (never None)
    diff = list(difflib.unified_diff("""

content = content.replace(old_func, new_func)

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.write(content)
