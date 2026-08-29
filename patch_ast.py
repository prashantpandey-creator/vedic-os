import os

with open("core/tool_registry.py", "r") as f:
    content = f.read()

target = """    def _ask_the_council(self, action_data):
        \"\"\"
        Peer Review Protocol. Spawns the Architect model to audit the JSON.
        Returns True if approved, False if rejected.
        \"\"\"
        from core.llm_gateway import generate_response
        import json"""

replacement = """    def _ask_the_council(self, action_data):
        \"\"\"
        Peer Review Protocol. Spawns the Architect model to audit the JSON.
        Returns True if approved, False if rejected.
        \"\"\"
        import json
        import ast

        # ZERO-TOKEN AST PRE-LINTER
        # Instantly compile Python syntax before burning LLM tokens
        file_path = action_data.get("file", "")
        if action_data.get("action") in ["edit_file", "create_file"] and file_path.endswith(".py"):
            code_to_check = action_data.get("content", action_data.get("replace", ""))
            if code_to_check:
                try:
                    # Strip any unified diff markers if present
                    clean_code = "\\n".join([line for line in code_to_check.split("\\n") if not line.startswith("<<<<") and not line.startswith("====") and not line.startswith(">>>>")])
                    if clean_code.strip():
                        ast.parse(clean_code)
                except SyntaxError as e:
                    self.terminal.run_command(f"echo '🚨 AST PRE-LINTER CAUGHT FATAL SYNTAX ERROR: {e}. Code rejected.'")
                    return False
        
        from core.llm_gateway import generate_response"""

content = content.replace(target, replacement)

with open("core/tool_registry.py", "w") as f:
    f.write(content)
