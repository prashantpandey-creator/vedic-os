import sys

with open("agents/omni_state_machine.py", "r") as f:
    content = f.read()

content = content.replace("repo_text, f_count, c_count = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)", "repo_text = ingest_repository_to_text(workspace_dir=workspace_dir, max_chars=120000)")

with open("agents/omni_state_machine.py", "w") as f:
    f.write(content)

print("ingest_repository_to_text unpacking bug fixed.")
