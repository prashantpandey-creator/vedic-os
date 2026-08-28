import sys

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "r") as f:
    content = f.read()

# 1. Add schema to prompt
old_schema = """4. invoke_subagent (Spawn a fast background agent to do research or recursive tasks)
{"thought": "...", "action": "invoke_subagent", "role": "researcher", "task": "Find all API routes returning 404"}

5. done
{"thought": "...", "action": "done"}"""

new_schema = """4. invoke_subagent (Spawn a fast background agent to do research or recursive tasks)
{"thought": "...", "action": "invoke_subagent", "role": "researcher", "task": "Find all API routes returning 404"}

5. create_pull_request (Push local edits to a new branch and raise a PR on GitHub)
{"thought": "...", "action": "create_pull_request", "branch_name": "fix-auth-bug", "title": "Fix Auth Bug", "body": "Fixed the token expiration issue."}

6. done
{"thought": "...", "action": "done"}"""
content = content.replace(old_schema, new_schema)

# 2. Add execution logic
old_exec = """        elif action == "invoke_subagent":
            role = action_data.get("role", "subagent")"""

new_exec = """        elif action == "create_pull_request":
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
                    return {"type": "github_pr", "url": pr_url, "msg": f"✅ Pull Request raised successfully!\\nURL: {pr_url}"}
                else:
                    return {"type": "error", "msg": f"Failed to raise PR: {pr_res.stderr}"}
            except Exception as e:
                return {"type": "error", "msg": f"Git/GH Exception: {e}"}

        elif action == "invoke_subagent":
            role = action_data.get("role", "subagent")"""
content = content.replace(old_exec, new_exec)

with open("/Users/badenath/projects/local-llm-ui/core/tool_registry.py", "w") as f:
    f.write(content)

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    app_content = f.read()

# Add UI rendering for github_pr
old_hist = """                elif log.get('type') == 'subagent':
                    st.info(f"🤖 Subagent ({log['role']}) Task: {log['task']}")
                    for entry in log['log']:
                        st.code(entry, language="bash")
                    st.success(f"Result: {log['msg']}")"""

new_hist = """                elif log.get('type') == 'subagent':
                    st.info(f"🤖 Subagent ({log['role']}) Task: {log['task']}")
                    for entry in log['log']:
                        st.code(entry, language="bash")
                    st.success(f"Result: {log['msg']}")
                elif log.get('type') == 'github_pr':
                    st.success(f"🐙 **Pull Request Raised!**")
                    st.markdown(f"[View PR on GitHub]({log['url']})")"""
app_content = app_content.replace(old_hist, new_hist)

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(app_content)

print("Pull Request Tool added.")
