import sys
import os

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "r") as f:
    fs_content = f.read()

old_ingest = """def ingest_repository_to_text(workspace_dir=".", max_chars=100000):
    repo_text = ""
    allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".html", ".css", ".sh"}
    
    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp', 'build', 'dist']]
        for f in files:
            if not f.startswith('.') and any(f.endswith(ext) for ext in allowed_exts):
                rel_path = os.path.relpath(os.path.join(root, f), workspace_dir)
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        repo_text += f"\\n\\n--- FILE: {rel_path} ---\\n{content}\\n"
                        if len(repo_text) > max_chars:
                            repo_text += "\\n\\n... [TRUNCATED] ..."
                            return repo_text
                except: pass
    return repo_text"""

new_ingest = """def ingest_repository_to_text(workspace_dir=".", max_chars=100000):
    repo_text = ""
    file_count = 0
    allowed_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".html", ".css", ".sh"}
    
    for root, dirs, files in os.walk(workspace_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', 'venv', 'node_modules', '__pycache__', '.next', 'GeneratedApp', 'build', 'dist']]
        for f in files:
            if not f.startswith('.') and any(f.endswith(ext) for ext in allowed_exts):
                rel_path = os.path.relpath(os.path.join(root, f), workspace_dir)
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        repo_text += f"\\n\\n--- FILE: {rel_path} ---\\n{content}\\n"
                        file_count += 1
                        if len(repo_text) > max_chars:
                            repo_text += "\\n\\n... [TRUNCATED DUE TO 120,000 CHARACTER CONTEXT LIMIT] ..."
                            return repo_text, file_count, len(repo_text)
                except: pass
    return repo_text, file_count, len(repo_text)"""
fs_content = fs_content.replace(old_ingest, new_ingest)

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.write(fs_content)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "r") as f:
    omni = f.read()

old_omni = """    # 1. Massive Git Ingestion (Mamba)
    status.write(f"🐍 **[MAMBA INGESTION]** {meditate_model} is swallowing the entire repository...")
    repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)"""

new_omni = """    # 1. Massive Git Ingestion (Mamba)
    repo_text, f_count, c_count = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)
    status.write(f"🐍 **[MAMBA INGESTION]** {meditate_model} swallowed {f_count} files ({c_count:,} characters)... Generating Blueprint...")"""
omni = omni.replace(old_omni, new_omni)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "w") as f:
    f.write(omni)

print("Ingestion logging patched.")
