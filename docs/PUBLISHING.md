# Publishing plan — `prashantpandey-creator/vedic-os`

Plan only. Nothing below is applied. Ordered so the blocking work comes first.

The repo is already *packaged* (README, LICENSE, Makefile, Dockerfile, run.sh,
requirements.txt — commit `d51bacc`). What it is not is *clean*: it currently
ships your working directory, your work history, and your home path.

---

## Phase 0 — stop leaking before anything else

These are the reasons the repo cannot go public as-is. All measured, not guessed.

### 0.1 `PROJECT_MIND.md` is your work journal, and it's tracked
19 KB of running session history — every intent you ever gave the agent, files
touched, marathon summaries, and `/Users/badenath/projects/local-llm-ui` written
into it 8 times. It's the agent's memory file (`core/memory_graph.py` reads it),
so it *grows with every run*. Publishing it publishes your work log, forever, and
every future run adds more.

**Do:** untrack it, gitignore it, ship `PROJECT_MIND.example.md` with two dummy
entries so the format is documented. `read_compressed_memory` already returns
`"No memory."` when the file is absent, so nothing breaks.

### 0.2 `.omni_checkpoints/*.json` are full conversation transcripts
`checkpoint_phase_1.json` and `latest.json` are tracked and contain complete
system prompts, your raw intents, model output, and phase summaries — including a
run where the agent looped 7 times in a row. Anyone reading them sees exactly how
your machine is laid out and what you were doing.

**Do:** untrack, gitignore `.omni_checkpoints/`.

### 0.3 86 tracked files contain `badenath`
Mostly `scripts/archive/*.py` — throwaway patch scripts with your absolute home
path hardcoded (`open("/Users/badenath/projects/local-llm-ui/app.py")`), plus
`app.py:380` and `app.py:486`.

**Do:** delete `scripts/archive/` outright (single-use patch scripts, already
applied, zero value to a reader). Replace the two `app.py` occurrences with
`config.DEFAULT_WORKSPACE_ROOT`. Then `git grep -c badenath` must return 0 — that
is the gate.

### 0.4 `.gitignore` is missing the things that keep re-appearing
Currently ignores `venv/ logs/ artifacts/ __pycache__/ node_modules/ .env`.
Missing, all of which are tracked or untracked-noisy right now:

```
.omni_checkpoints/
.omni_history
PROJECT_MIND.md
*.pid
run.pid
WeatherDashboard/
patch_*.py
fix_*.py
benchmarks/
```

`.pyc` files are tracked despite `__pycache__/` being ignored — they were added
before the rule, so the rule never applied to them. `git rm -r --cached` is
needed, ignoring alone won't do it.

**Gate for Phase 0:** `git ls-files | xargs grep -l badenath` returns nothing, and
`git ls-files | grep -E '\.pyc|omni_checkpoints|PROJECT_MIND'` returns nothing.

### 0.5 Decide about the history
The above cleans the *tip*. The 11 `Omni-Agent Checkpoint:` commits (with pasted
LeetCode problems as messages) and every prior copy of `PROJECT_MIND.md` stay in
the history and remain readable on GitHub forever.

Two honest options:

- **Squash to a fresh initial commit.** Clean, simple, loses the history. For a
  tool nobody has cloned yet, this is almost certainly right.
- **`git filter-repo` the sensitive paths out.** Keeps history, rewrites hashes,
  requires a force-push.

**This is your call and it is irreversible — I won't do either without you saying
which.** Recommendation: squash. Nothing in that history is worth the risk.

---

## Phase 1 — make it run on a machine that isn't yours

Right now a fresh clone cannot work. Verified gaps:

1. **Model names are assumed, not checked.** `config.py` names five specific
   Ollama tags. A new user has none of them. The CLI's failure mode used to be a
   silent empty blueprint; it's now loud, but "loud" still isn't "helpful".
   **Do:** a `make doctor` / `run.sh --check` that hits `/api/tags`, diffs against
   the configured models, and prints the exact `ollama pull` lines to run.
2. **`requirements.txt` is incomplete.** It lists streamlit, requests, orjson,
   uvloop. The CLI additionally imports `rich`, `prompt_toolkit`, `litellm`, and
   the backend needs `fastapi` + `uvicorn`. A clean `pip install -r` then
   `python cli.py` fails on import.
   **Do:** regenerate from a fresh venv, pin majors.
3. **`agents/omni_state_machine.py` imports streamlit** but never uses it, so the
   CLI drags in the whole Streamlit tree to start. **Do:** drop the import.
4. **`backend/main.py` defaulted the workspace to your absolute path** — already
   fixed on the open PR branch, listed here so the checklist stays honest.

**Gate:** clone into a clean container, `pip install -r requirements.txt`,
`python cli.py`, type one instruction, get one tool execution. That's the demo.

---

## Phase 2 — the honest README

The current README predates everything measured this week. Rewrite around what is
actually true and provable:

- **What it is:** a local, offline coding agent driving Ollama models. No cloud
  call in the default path.
- **The real architecture claim:** it routes across a *hybrid* model
  (`granite4:3b-h`, Mamba-2 + attention) and pure transformers. Once
  `docs/MODEL_ROUTING.md` phase 1 is applied, you can state a measured number:
  **2.8× faster repo ingest at 2.2× less memory than the same-size transformer at
  44K tokens.** That is a genuinely interesting differentiator and nobody else's
  README has it. Do not publish the claim until the routing swap is actually
  applied — right now the code does the opposite.
- **Safety, stated plainly:** the command filter is a deny-list, not a sandbox.
  Say so. Point at Docker for real isolation. Publishing an agent with terminal
  access and calling its regex filter a "sandbox" is how people get burned.
- **Delete the "Claude Code Clone" line** from the CLI banner before publishing.
  It invites a comparison the tool loses and it reads as someone else's trademark.

---

## Phase 3 — sequence

```
1. merge PR #1 (the ten fixes)            ← done and open, blocking nothing else
2. Phase 0 cleanup, single commit
3. decide squash-vs-filter-repo           ← YOUR CALL, irreversible
4. Phase 1 runnability + fresh-clone test
5. apply docs/MODEL_ROUTING.md steps 1–4
6. run tests/bench_ssm_vs_transformer.py on an idle box, paste real numbers
7. rewrite README against those numbers
8. flip public
```

Steps 2, 4, 5, 7 are mechanical and I can do them in one pass.
Step 3 is yours. Step 6 needs the machine free.

---

## Not blocking, but worth knowing before strangers read the code

- `app.py` is 1,125 lines in one file and duplicates agent logic that now lives in
  `core/`. It is the first thing a reviewer will open. Consider not shipping the
  Streamlit UI in v1 — the CLI is the better story and a third of the surface area.
- `HEAVY_MODEL` (qwen2.5:32b, ~20 GB) is configured and referenced by nothing.
- `tests/` mixes real tests with ad-hoc benchmark scripts; several have no
  `__main__` guard and silently no-op. `pytest` isn't in the venv.
- `frontend/` has a `node_modules` directory — confirm it isn't tracked before
  going public, it will dominate the clone size if it is.
