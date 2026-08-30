import os
import json
import re
import subprocess
import requests
from core.episodic_memory import query_memory, commit_to_memory
from core.visual_engine import debug_ui
from core.file_system import apply_search_replace, write_verified
from core.ollama_api import OLLAMA_URL, evict_model
from config import FAST_MODEL, EDITOR_MODEL

def extract_code(text):
    """Pull the code out of a model's ```-fenced answer. Single copy — cli.py and
    backend/main.py each had their own before."""
    match = re.search(r'```[a-zA-Z]*\n(.*?)\n```', text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'```(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


class ToolRegistry:
    def __init__(self, workspace_dir, terminal_engine):
        self.workspace_dir = workspace_dir
        self.terminal = terminal_engine
        
    def get_system_prompt_addition(self):
        return """
Available Tools (Choose ONE per response):

1. run_command (You have modern Rust binaries: 'rg', 'fdfind', 'batcat'. A bare 'cd <dir>' persists across steps. Anything else runs in a fresh shell rooted at the current directory, so 'cd sub && npm test' works too.)
{"thought": "...", "action": "run_command", "command": "npm test"}

2. edit_file — PREFERRED: exact search/replace. 'search' must be text copied verbatim from the file.
{"thought": "...", "action": "edit_file", "file": "path", "search": "def old():\\n    pass", "replace": "def new():\\n    return 1"}

3. edit_file (fallback: whole-file rewrite by a second model). Only use when the change is too sweeping to express as search/replace — it rewrites the ENTIRE file and is rejected if the result is truncated.
{"thought": "...", "action": "edit_file", "file": "path", "instruction": "Detailed instruction on what to change"}

4. create_file (Write a NEW file. Fails if the file already exists — use edit_file for existing files.)
{"thought": "...", "action": "create_file", "file": "src/utils.py", "content": "def helper():\\n    return 1"}

5. create_artifact (Generate permanent reports, plans, or full files)
{"thought": "...", "action": "create_artifact", "title": "ArchitecturePlan", "content": "# Markdown Content..."}

6. invoke_subagent (Spawn a fast background agent to do research or recursive tasks)
{"thought": "...", "action": "invoke_subagent", "role": "researcher", "task": "Find all API routes returning 404"}

7. create_pull_request (Push local edits to a new branch and raise a PR on GitHub)
{"thought": "...", "action": "create_pull_request", "branch_name": "fix-auth-bug", "title": "Fix Auth Bug", "body": "Fixed the token expiration issue."}

8. git_snapshot (Record a restore point BEFORE a risky edit. Any pre-existing uncommitted changes are stashed, not committed.)
{"thought": "...", "action": "git_snapshot"}

9. revert_checkpoint (Time Travel: reset the codebase to the snapshot recorded by git_snapshot. Requires a git_snapshot first — it will refuse otherwise. The discarded state is stashed, not destroyed.)
{"thought": "...", "action": "revert_checkpoint"}

10. query_memory (Search the Vyasa Episodic Brain for solutions to recurring bugs or architecture quirks)
{"thought": "...", "action": "query_memory", "query": "How do we fix the API route 404 error in this project?"}

11. commit_memory (Permanently save a hard-earned lesson, bug fix, or codebase rule into the Episodic Brain)
{"thought": "...", "action": "commit_memory", "content": "The Next.js frontend uses Pages router, not App router. Always put API routes in /pages/api/."}

12. visual_debug (Take a screenshot of the Next.js localhost and use Llama Vision to critique the layout and find CSS bugs)
{"thought": "...", "action": "visual_debug", "url": "http://localhost:3000"}

13. done (Finish the job. You MUST supply 'verified_by': the exact shell command
that proves the work — a test run, a build, whatever the task's success actually
is. That command is RE-RUN before done is accepted; if it exits non-zero the done
is refused and you keep working, so there is nothing to gain by claiming early.
Verifying is a run_command like any other — there is no 'execute_test' tool. Once
your check passes, emit done on the next turn rather than looking for more work.)
{"thought": "...", "action": "done", "verified_by": "python3 -m unittest test_calc"}
"""

    def check_done(self, action_data):
        """
        Decide whether a 'done' is real. Returns (accepted: bool, msg: str).

        Both loops used to `break` on done unconditionally, which made stopping a
        matter of the model's opinion. Measured both ways it fails: with no
        guidance the agent ran 12/12 steps past a passing verifier and never
        declared; told plainly to stop when finished, it declared at step 4 with
        the verifier still red. Encouragement cannot fix a self-report — the loop
        has to check.

        So done carries the command that proves it, and we re-run that command.
        The agent cannot pass by asserting; it can only pass by being right.
        """
        cmd = (action_data.get("verified_by") or "").strip()
        if not cmd:
            return False, ("done REFUSED: no 'verified_by'. Supply the exact shell "
                           "command that proves the work — the test run, the build, "
                           "whatever success actually is — then emit done again.")
        if self.terminal is None:
            return True, "done accepted (no terminal available to verify)."

        self.terminal.last_returncode = None
        output = self.terminal.execute(cmd)
        code = self.terminal.last_returncode
        if code is None:
            return False, (f"done REFUSED: '{cmd}' produced no exit code — it was "
                           f"blocked, or it is a 'cd'/daemon command, so it proves "
                           f"nothing. Give a command that actually runs the check.\n"
                           f"{output}")
        if code != 0:
            return False, (f"done REFUSED: '{cmd}' exited {code}, so the job is not "
                           f"finished. Keep working.\nOutput:\n```\n{output}\n```")
        return True, f"done accepted: '{cmd}' passed (exit 0)."

    def execute_tool(self, action_data, fast_model=FAST_MODEL, main_model=None):
        action = action_data.get("action")
        
        if action == "run_command":
            cmd = action_data.get("command", "")
            output = self.terminal.execute(cmd)
            # \n, not \\n. The escaped version emitted a literal backslash-n, so
            # every command result reached the model as one unbroken line with a
            # code fence that never opened:
            #   Command Executed.\nOutput:\n```\ntotal 3
            return {"type": "command", "cmd": cmd, "output": output,
                    "msg": f"Command Executed.\nOutput:\n```\n{output}\n```"}
            
        elif action == "query_memory":
            res = query_memory(action_data.get("query", ""))
            return {"type": "memory", "msg": f"🧠 Vyasa Episodic Memory Retrieval:\n\n{res}"}

            
        elif action == "commit_memory":
            res = commit_to_memory(action_data.get("content", ""))
            return {"type": "memory", "msg": res}

        elif action == "visual_debug":
            res = debug_ui(action_data.get("url", "http://localhost:3000"))
            return {"type": "vision", "msg": f"👁️ Llama Vision Critique:\n\n{res}"}


        elif action == "git_snapshot":
            return self._git_snapshot()

        elif action == "revert_checkpoint":
            return self._revert_checkpoint()
        elif action == "create_file":
            filepath = action_data.get("file")
            content = action_data.get("content", "")
            full_path = os.path.join(self.workspace_dir, filepath)
            if os.path.exists(full_path):
                return {"type": "error", "msg": f"create_file refused: {filepath} already exists. Use edit_file."}
            parent = os.path.dirname(full_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            try:
                # New file, so old_code is "" — the syntax gate still applies.
                write_verified(full_path, content, "", filepath)
            except Exception as e:
                if os.path.exists(full_path):
                    os.remove(full_path)
                return {"type": "error", "msg": f"create_file failed: {e}"}
            return {"type": "edit", "file": filepath, "diff": "File created.", "msg": f"File {filepath} created successfully."}
        elif action == "edit_file":
            filepath = action_data.get("file")
            try:
                if action_data.get("search"):
                    diff_str = apply_search_replace(
                        filepath, action_data["search"], action_data.get("replace", ""), self.workspace_dir
                    )
                elif action_data.get("instruction"):
                    diff_str = self._rewrite_file_with_editor_model(filepath, action_data["instruction"])
                else:
                    return {"type": "error", "msg": "edit_file needs either 'search'+'replace' or 'instruction'."}
                return {"type": "edit", "file": filepath, "diff": diff_str, "msg": f"File {filepath} edited successfully.\nDiff:\n```diff\n{diff_str[:2000]}\n```"}
            except Exception as e:
                return {"type": "error", "msg": f"Edit failed: {e}"}
                
        elif action == "create_artifact":
            title = action_data.get("title", "artifact").replace(" ", "_")
            content = action_data.get("content", "")
            art_dir = os.path.join(self.workspace_dir, "artifacts")
            os.makedirs(art_dir, exist_ok=True)
            path = os.path.join(art_dir, f"{title}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"type": "artifact", "title": title, "path": path, "msg": f"Artifact '{title}' created successfully at artifacts/{title}.md"}
            
        elif action == "create_pull_request":
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
                    return {"type": "github_pr", "url": pr_url, "msg": f"✅ Pull Request raised successfully!\nURL: {pr_url}"}
                else:
                    return {"type": "error", "msg": f"Failed to raise PR: {pr_res.stderr}"}
            except Exception as e:
                return {"type": "error", "msg": f"Git/GH Exception: {e}"}

        elif action == "invoke_subagent":
            role = action_data.get("role", "subagent")
            task = action_data.get("task", "")
            
            # VRAM Safety Handoff: evict main model before spawning subagent
            if main_model and main_model != fast_model:
                evict_model(main_model)
                
            sub_msg, sub_log, ok = self._run_headless_subagent(role, task, fast_model)

            # Evict subagent and let main model reload
            if main_model and main_model != fast_model:
                evict_model(fast_model)

            verb = "completed task" if ok else "FAILED"
            return {"type": "subagent", "role": role, "task": task, "log": sub_log,
                    "msg": f"Subagent '{role}' {verb}. Result:\n{sub_msg}"}
            
        return {"type": "error", "msg": f"Unknown action: {action}"}


    # ------------------------------------------------------------------
    # Git time travel.
    #
    # The originals were `git add . && git commit` and `git reset --hard HEAD^`.
    # Measured 2026-08-29 in a throwaway repo:
    #   - revert_checkpoint with no snapshot taken ate a real user commit and
    #     reported "✅ successfully time-traveled to the previous snapshot!"
    #   - it destroyed an uncommitted edit to a tracked file, no stash, no warning
    #   - called repeatedly it walked back one real commit per call: 5→4→3→2→1
    #   - git_snapshot swept another session's untracked files into its commit
    # HEAD^ is not "the last snapshot"; it is just "one commit ago". The two are
    # only the same if the snapshot is the most recent commit, which nothing
    # enforced. Now the snapshot SHA is recorded and reverting targets it.
    # ------------------------------------------------------------------
    SNAPSHOT_FILE = ".omni_snapshot"

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.workspace_dir,
                              capture_output=True, text=True)

    def _git_snapshot(self):
        if self._git("rev-parse", "--is-inside-work-tree").returncode != 0:
            return {"type": "error", "msg": "Not a git repository — cannot snapshot."}

        foreign = [l for l in self._git("status", "--porcelain").stdout.splitlines()
                   if l.strip() and not l.split()[-1].startswith(self.SNAPSHOT_FILE)]

        # `git add .` here used to sweep in whatever else was in the tree —
        # including another session's in-flight work. Stash instead: the tree is
        # left clean for the agent, and nothing of anyone else's is committed.
        if foreign:
            res = self._git("stash", "push", "--include-untracked",
                            "-m", "omni-agent: pre-snapshot stash")
            if res.returncode != 0:
                return {"type": "error", "msg": f"Could not stash existing changes: {res.stderr}"}
            stashed = len(foreign)
        else:
            stashed = 0

        sha = self._git("rev-parse", "HEAD").stdout.strip()
        if not sha:
            return {"type": "error", "msg": "Repository has no commits yet — commit once before snapshotting."}
        with open(os.path.join(self.workspace_dir, self.SNAPSHOT_FILE), "w") as f:
            f.write(sha)

        note = (f" {stashed} pre-existing change(s) were stashed first (`git stash pop` to restore) —"
                f" they are NOT part of the snapshot." if stashed else "")
        return {"type": "snapshot", "msg":
                f"✅ Snapshot recorded at {sha[:8]}.{note} revert_checkpoint will return here and no further."}

    def _revert_checkpoint(self):
        snap_path = os.path.join(self.workspace_dir, self.SNAPSHOT_FILE)
        if not os.path.exists(snap_path):
            return {"type": "error", "msg":
                    "No snapshot to revert to. Call git_snapshot BEFORE the risky edit. "
                    "Refusing to reset — without a recorded snapshot this would delete "
                    "the user's own last commit."}
        sha = open(snap_path).read().strip()
        if self._git("cat-file", "-e", sha + "^{commit}").returncode != 0:
            return {"type": "error", "msg": f"Recorded snapshot {sha[:8]} no longer exists. Refusing to reset."}

        if self._git("rev-parse", "HEAD").stdout.strip() == sha and not self._git("status", "--porcelain").stdout.strip():
            return {"type": "revert", "msg": f"Already at snapshot {sha[:8]} with a clean tree. Nothing to undo."}

        # Park the current state before the hard reset so it is recoverable.
        self._git("stash", "push", "--include-untracked", "-m", f"omni-agent: pre-revert {sha[:8]}")
        res = self._git("reset", "--hard", sha)
        if res.returncode != 0:
            return {"type": "error", "msg": f"Failed to revert: {res.stderr}"}
        return {"type": "revert", "msg":
                f"⏪ Reverted to snapshot {sha[:8]}. The discarded state was stashed first "
                f"(`git stash list` / `git stash pop` to recover it)."}

    def _ask_the_council(self, action_data):
        """
        UNWIRED 2026-08-29. Kept for reference; nothing calls it. Do not put it
        back in front of edit_file/create_file without re-running
        tests/test_agent_completes_task.py first.

        It gated every write, and it was the single reason the agent could not
        finish a job. On the fix_bug acceptance task it blocked FIVE consecutive
        valid edits (steps 3, 5, 7, 9, 11); the agent burned all 12 steps and
        calc.py ended byte-identical to the fixture — not one character written.

        An earlier pass here cut false rejects from 5/8 to 0/8, but that was
        measured on eight edits written by hand. Real agent output is longer and
        messier, and it still got blocked. Improving a gate is not the same as
        fixing it, and hand-written cases are the confirming case.

        The deeper problem is that it is redundant. Everything it claims to catch
        is already caught deterministically, a few microseconds later, by code
        that cannot be wrong about it:

          hallucinated search text -> apply_search_replace raises
             "Search block not found in calc.py. The model hallucinated the
              search text."   (observed at step 1 of the same run)
          syntax error / truncation -> write_verified reverts and rejects

        A 4B model guessing in front of a certainty can only subtract accuracy.

        Second-opinion review before an edit runs.

        Measured 2026-08-29: the original version rejected 5 of 8 obviously-valid
        edits (62%). It was shown only the JSON fragment — no file — and asked
        whether the edit "contains hallucinations". It cannot check whether the
        search text exists without the file, so a 4B model answered the
        unanswerable question with a flat 'REJECT'.

        Two changes: the reviewer now SEES the file, so the question is
        answerable; and it must name a specific reason to block, because a
        review that cannot say what is wrong is not a review. Anything
        ambiguous approves — matching the existing behaviour when the reviewer
        is unreachable.

        Note this is a second line only. The deterministic checks catch the
        cases this was built for and catch them exactly: apply_search_replace
        raises when the search text is not in the file ("the model hallucinated
        the search text"), and write_verified reverts on syntax error and
        rejects truncation.
        """
        import requests
        from config import INGEST_MODEL
        print(f"🏛️ Calling The Council ({INGEST_MODEL}) for Peer Review...")

        try:
            filepath = action_data.get("file", "")
            try:
                with open(os.path.join(self.workspace_dir, filepath), "r", encoding="utf-8") as f:
                    current = f.read()[:8000]
            except Exception:
                current = "(file not readable — judge the edit on its own terms)"

            prompt = (
                "You are a code reviewer. Approve unless something is definitely wrong.\n\n"
                f"FILE: {filepath}\n```\n{current}\n```\n\n"
                f"PROPOSED EDIT:\n```json\n{json.dumps(action_data, indent=2)}\n```\n\n"
                "Block ONLY if one of these is definitely true:\n"
                "  - the 'search' text does not appear in the file above\n"
                "  - the 'replace' text has a clear syntax error\n"
                "  - the edit deletes or destroys unrelated code\n\n"
                "Small, ordinary changes (renames, constants, comments, added arguments, "
                "docstrings) are NORMAL — approve them.\n"
                "Reply 'APPROVE', or 'REJECT: <the specific reason>'."
            )
            res = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": INGEST_MODEL, "messages": [{"role": "user", "content": prompt}],
                      "stream": False, "options": {"temperature": 0.0}},
                timeout=30,
            ).json()
            answer = res.get("message", {}).get("content", "").strip()

            # Must be an explicit, reasoned rejection. A bare "REJECT", or the word
            # appearing anywhere in prose, is not enough to destroy a valid edit.
            head = answer.upper().lstrip("*_# ").split("\n")[0]
            if head.startswith("REJECT") and len(answer.split(":", 1)[-1].strip()) > 12:
                print(f"🏛️ Council blocked it: {answer[:160]}")
                return False
            return True
        except Exception as e:
            print(f"Council unavailable: {e}. Bypassing review.")
            return True

    def _rewrite_file_with_editor_model(self, filepath, instruction, model=EDITOR_MODEL):
        """
        Whole-file rewrite by the small editor model.

        This used to live duplicated in cli.py and backend/main.py, writing the
        model's output straight to disk with no check. It now returns through
        write_verified(), which reverts on syntax error and rejects truncation.
        """
        full_path = os.path.join(self.workspace_dir, filepath)
        with open(full_path, "r", encoding="utf-8") as f:
            old_code = f.read()

        prompt = (
            f"Instruction: {instruction}\n\nCURRENT CODE:\n```\n{old_code}\n```\n\n"
            "Rewrite the code to fulfill the instruction. Output ONLY the complete "
            "updated code inside ``` blocks. Do not omit any part of the file."
        )
        res = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
            timeout=300,
        ).json()
        if "error" in res:
            raise ValueError(f"Editor model '{model}' failed: {res['error']}")

        new_code = extract_code(res.get("message", {}).get("content", ""))
        return write_verified(full_path, new_code, old_code, filepath)

    def _run_headless_subagent(self, role, task, model):
        # A lightweight 3-step loop purely for research/grep
        sys_prompt = f"You are a Subagent (Role: {role}). You have terminal access. Task: {task}. Use run_command to find info. When done, output action: 'done' and 'result': 'summary'."
        messages = [{"role": "system", "content": sys_prompt}]
        
        sub_log = []
        result_msg = "Task failed to yield a specific result."
        ok = False

        for _ in range(3):
            try:
                # "stream": False is REQUIRED — Ollama streams NDJSON by default and
                # .json() then dies on "Extra data: line 2". Without it this loop
                # crashed on its first request every single time.
                res = requests.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={"model": model, "messages": messages, "stream": False,
                          "options": {"temperature": 0.0}},
                    timeout=300,
                ).json()
                if "error" in res:
                    result_msg = f"Subagent model '{model}' unavailable: {res['error']}"
                    break
                raw = res.get("message", {}).get("content", "")
                messages.append({"role": "assistant", "content": raw})

                # Parse JSON quickly
                match = re.search(r'\{\s*"action".*?\}', raw, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                else:
                    data = {"action": "done", "result": raw}  # fallback

                act = data.get("action")
                if act == "done":
                    result_msg = data.get("result", raw)
                    ok = True
                    sub_log.append(f"Subagent concluded: {result_msg}")
                    break
                elif act == "run_command":
                    cmd = data.get("command", "")
                    out = self.terminal.execute(cmd)
                    sub_log.append(f"$ {cmd}\n> {out[:100]}...")
                    messages.append({"role": "user", "content": f"Output: {out}"})
            except Exception as e:
                result_msg = f"Subagent crashed: {e}"
                break

        return result_msg, sub_log, ok
