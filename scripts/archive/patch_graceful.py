import sys

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "r") as f:
    content = f.read()

content = content.replace('res = subprocess.run(["python3"', 'try:\n            res = subprocess.run(["python3"')
content = content.replace('            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED', '            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED')
content = content.replace('if res.returncode != 0:\n            # Revert the file\n            with open(full_path, "w", encoding="utf-8") as f:\n                f.write(old_code)\n            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please carefully review your python syntax and try again.")', 'if res.returncode != 0:\n                with open(full_path, "w", encoding="utf-8") as f:\n                    f.write(old_code)\n                raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please carefully review your python syntax and try again.")\n        except FileNotFoundError:\n            pass')

content = content.replace('res = subprocess.run(["node"', 'try:\n            res = subprocess.run(["node"')
content = content.replace('if res.returncode != 0:\n            with open(full_path, "w", encoding="utf-8") as f:\n                f.write(old_code)\n            raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a JS syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please review your syntax.")', 'if res.returncode != 0:\n                with open(full_path, "w", encoding="utf-8") as f:\n                    f.write(old_code)\n                raise ValueError(f"🚨 SYNTAX ERROR PREVENTED! Your edit introduced a JS syntax error:\\n{res.stderr}\\nThe edit was REVERTED. Please review your syntax.")\n        except FileNotFoundError:\n            pass')

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.write(content)
