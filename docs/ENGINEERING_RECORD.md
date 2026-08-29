# Engineering record — the agent loop audit

One place for what was wrong, what was measured, and what is still open.
Compiled 2026-08-29 from PRs #1–#10.

Rules this record follows, because several entries below exist only because they
were broken earlier: **every claim carries the measurement that proves it**, a
claim reaches no further than the check behind it, and a retracted claim stays
visible rather than being quietly edited out.

Detail lives in the documents this one indexes:

| document | what is in it |
|---|---|
| [`benchmarks/RESULTS.md`](../benchmarks/RESULTS.md) | model benchmarks, four tasks, n≥5, with the noise floor |
| [`benchmarks/METHODOLOGY_AUDIT.md`](../benchmarks/METHODOLOGY_AUDIT.md) | audit of the earlier benchmarks, including two defects this audit committed itself |
| [`docs/MODEL_ROUTING.md`](MODEL_ROUTING.md) | which model belongs on which job, and the SSM crossover measurement |
| [`benchmarks/HOSTING_COSTS.md`](../benchmarks/HOSTING_COSTS.md) | measured GPU hosting costs |

---

## The headline

**The agent had never completed a task.** Not "was unreliable" — had never once
reached a model. `core/llm_gateway.py` routes through litellm, which requires an
explicit provider prefix; every caller passed a bare Ollama tag. So
`generate_next_thought` returned `{"action": "error"}` on every step of every
run, the loop spent all 20 steps on "Malformed JSON. Retrying…", and then tripped
its own repeated-action detector.

Verified against both the old and the new default model before the fix:

| model string | through the gateway |
|---|---|
| `mannix/llama3.1-8b-abliterated:latest` | ❌ gateway failure |
| `qwen3:4b-instruct-2507-q4_K_M` | ❌ gateway failure |
| `ollama/…` either one | ✅ works |

It now completes real tasks end-to-end — verified by running the tests
afterwards, not by trusting the agent's "Task Complete".

---

## Defect ledger

Status is against `main` as of this commit.

### Correctness

| # | defect | evidence | PR | status |
|---|---|---|---|---|
| 1 | Gateway never routed; agent loop never reached a model | old and new defaults both failed, `ollama/`-prefixed both worked | #3, #4, #7 | ✅ fixed |
| 2 | `edit_file` could destroy files — prompt taught `{file, instruction}`, executor read `{search, replace}`, and the whole-file rewrite path wrote model output straight to disk with no syntax check or revert | truncated / empty / syntactically broken rewrites all now refused with the file byte-identical | #1 | ✅ fixed |
| 3 | Context truncation dropped the user's intent at step 4 of 20 | intent lives at `messages[1]`, not in the system prompt; now pinned, survives 15 steps | #1 | ✅ fixed |
| 4 | Context truncation erased the agent's **own actions** | it re-ran a passing test 4× and concluded *"my initial plan to edit stats.py was based on a false premise"* — it had forgotten making the edit | #10 | ✅ fixed |
| 5 | `invoke_subagent` had never worked — missing `"stream": False`, so `.json()` died on Ollama's NDJSON | and the crash was returned to the agent as `"Subagent 'x' completed task."` | #1 | ✅ fixed |
| 6 | `create_file` implemented but absent from the system prompt | only 1 of 7 tools missing; the prompt's `1,2,4,5,6,7` numbering was the scar | #1 | ✅ fixed |
| 7 | `cd X && cmd` — the pattern the prompt recommends — always errored | `[ERROR] Directory does not exist: .../core && ls` | #1 | ✅ fixed |
| 8 | `run_command` results reached the model with literal `\n`; the code fence never opened | `f"…\\nOutput:\\n"` emits backslash-n | #5 | ✅ fixed |
| 9 | Blueprint silently empty (CLI) or fabricated (backend) | CLI used an unpulled model → 404 swallowed into `""`; backend used `architect-compiler`, pinned to emit app specs, which invented `{"name":"TaskManager"}` for this repo | #1 | ✅ fixed |
| 10 | Ingest silently truncated: 17,703 tokens against a hardcoded `num_ctx=16000` | `prompt_eval_count` returns exactly 16000 at the cap, 17,703 when raised | — | ⚠️ **open** |
| 11 | A stalled model call could hang a run indefinitely — litellm's own timeout does not cut a stalled Ollama socket | | #8 | ✅ fixed |

### Safety

| # | defect | evidence | PR | status |
|---|---|---|---|---|
| 12 | Unauthenticated shell execution reachable from the network — `/ws/agent` runs arbitrary commands, no auth, bound `0.0.0.0`; WebSockets are not covered by CORS | now loopback + Origin allowlist enforced in the handler | #1 | ✅ fixed |
| 13 | The "sandbox" blocked **2 of 13** destructive commands | `rm --recursive`, `find -delete`, `shutil.rmtree`, `dd`, `: > ~/.ssh/authorized_keys`, `git push --force`, `curl \| bash`, `base64 -d` + `eval` all passed. Now **13/13**, 0 false positives on 6 ordinary commands | #1 | ✅ fixed — but see note |
| 14 | `init_omni_loop` ran `git init && git add . && git commit` on every first prompt — creating repos in directories that had none, committing whatever was already uncommitted | this repo's log carries **11** `Omni-Agent Checkpoint:` commits whose messages are pasted LeetCode problems | #1 | ✅ fixed |

**Note on 13:** it is a better deny-list, not a sandbox, and the message no longer
claims otherwise. A determined command still walks around it. Real isolation means
running the agent in a container — a design change, not a fix.

---

## Measurements worth keeping

### The noise floor is 2.2× on short prompts

`architect-compiler:latest` and `qwen3:4b-instruct-2507-q4_K_M` are **byte-identical
weights** — the first is a Modelfile wrapper around the second. Any gap between
them is pure measurement noise. At n=5:

| task | qwen3:4b | architect-compiler | apparent gap |
|---|---|---|---|
| ingest | 204 t/s | 398 t/s | 1.95× |
| JSON action | 408 t/s | 189 t/s | 2.16× — **rank flips** |
| rewrite | 319 t/s | 291 t/s | 1.10× |

**Treat any short-prompt throughput difference under ~2.2× as a tie.** On
long-context runs, prefill dominates the jitter and spread collapses to 1.00–1.13×,
so differences there are real at much smaller ratios.

### The context ledger — and how the wording nearly sank it

Truncation now replaces the dropped block with a compact ledger of the actions it
contained. Getting this right took three rounds:

**Round 1 — the first probes were incapable of detecting the effect.** Both left
the decisive fact (tests are green) in the *recent* window in both arms, so the
ledger had nothing to add and both scored 5/5. Rebuilt with the information only
in the dropped region:

| scenario | control | ledger |
|---|---|---|
| work **is** done → `done` correct | **0/12**; 9/12 tried to re-edit an already-fixed file | **12/12** |
| work **not** done → `done` would be wrong | 5/10 wasted a step re-reading | **0/10** wrong stops, 10/10 right action |

**Round 2 — end-to-end disagreed, and it was right.** Ledger v1 solved 5/8 vs
control 7/8. Two of three failures claimed completion with the tests still red.
Cause was the wording: a header saying *"these are done"* over lines reading
*"edit_file → File shipping.py edited successfully"* got read as *task solved*.

**Round 3 — reworded to say a successful call is not a solved task, and verify
before finishing.** 32 paired runs, fresh scratch repo each, arms alternating,
success verified by running the tests:

| arm | solved | premature stops | stuck |
|---|---|---|---|
| control (unmodified main, 16 runs) | 11/16 | 0 | 4 |
| ledger v1 (8 runs) | 5/8 | **2** | 0 |
| ledger v2 (8 runs, shipped) | **8/8** | **0** | **0** |

Fisher exact, v2 vs control, one-sided **p = 0.103** — suggestive, not conclusive
at this sample size. Reliability is the win; median steps is a wash.

### Where the non-transformer belongs

`granite4:3b-h` is the only non-transformer in the box — IBM Granite 4.0 Hybrid,
Mamba-2 state-space layers plus attention, 1,048,576 context. Full detail in
[`docs/MODEL_ROUTING.md`](MODEL_ROUTING.md). The short version:

- **The crossover is between 17K and 44K tokens.** At 44,891 tokens the SSM wins
  by 2.8× on time and 2.2× on memory (5.83 GB vs 12.71 GB); below 17K they are
  indistinguishable.
- **`EDITOR_MODEL = granite4:3b-h` stays.** On six real whole-file rewrites both
  models scored 5/6 usable, with no length curve — the copy-fidelity worry was not
  supported. The SSM is cheaper to keep resident.
- **The blueprint should be deleted, not re-routed.** Both models cited **0 of 5**
  real filenames from this repo. Routing it to a faster model buys a faster wrong
  answer; `build_tree_with_hints` already supplies the file list deterministically.

### Two defects this audit committed itself

Recorded because an audit that only finds other people's mistakes is not being
run honestly. Both are written up in
[`benchmarks/METHODOLOGY_AUDIT.md`](../benchmarks/METHODOLOGY_AUDIT.md).

1. **The same KV-cache trap it flagged in the earlier benchmarks.** A per-run
   nonce in the *user* message while the *system* message stayed identical — the
   shared prefix was still cached, reporting 6,030 t/s for a model that runs at
   ~240. Caught before publishing; the fix took T1 from 198s to 611s, which is the
   proof.
2. **A hardcoded constant in a scoring path** — the exact defect it criticised in
   `tests/zero_shot_benchmark.py`. The T2 scorer held a literal 7-tool allowlist
   while the prompt advertised 13, so two models choosing `query_memory` (valid)
   were scored **0/5** and that wrong number was published as "the sharpest result
   in the set." All four models actually score 5/5.

   What caught it: running the same task through the **live production path**,
   which disagreed with the bench. n=5 reproduced the wrong answer five times
   because the fault was in the scorer, not the sampling. **Repeats defend against
   noise; a second path defends against being wrong.**

---

## Still open

See the GitHub issues opened alongside this document. Ranked by leverage:

1. **Delete the LLM blueprint call** — saves ~100s and 17,703 tokens of prefill
   every session, and removes a section of the system prompt currently filled with
   invented filenames. Fixes defect 10 by subtraction.
2. **`generate_response_stream` has the original gateway bug** — it calls
   `acompletion` with the raw model name, no `normalize_model`. The streaming path
   in `backend/main.py` will fail the moment it is used.
3. **`HEAVY_MODEL` (qwen2.5:32b) is referenced by nothing** — 20 GB configured and
   unreachable. Wire it as the loop-detection escalation target or delete the entry.
4. **`git_snapshot` / `revert_checkpoint`** reintroduce the blind `git add .` of
   defect 14, and `revert_checkpoint` runs `git reset --hard HEAD^`.
5. **`max_chars=60000` overshoots to 78,675** — the budget is checked after
   appending a whole file, not before.
6. **The `🐍 Mamba` labels sit on the transformer's path.**
7. **Raise n on the ledger result** — p = 0.103 is suggestive, not settled.
8. **Real isolation for the agent** — the deny-list is honest now, but a container
   is the actual answer.
