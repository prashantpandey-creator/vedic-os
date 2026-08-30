# The done-gate does not work. Measured, n=40 tasks per arm.

PR #20 added a gate: `done` must carry `verified_by`, and the loop re-runs that
command before accepting. It shipped on a 5×5 result. At 20 runs per arm the
effect disappears.

## Result

Interleaved A/B — base, gate, base, gate… so machine drift hits both arms
equally. Same tree apart from the gate (`61960c9` vs its parent `f3730a5`).
Same model, `qwen3:4b-instruct-2507-q4_K_M`. Raw rows: `done_gate_ab40.csv`.

| arm | tasks passed | **false dones** | declared done | mean steps | mean secs |
|---|---|---|---|---|---|
| base (no gate) | 24/40 — 60% | **6** | 23/40 | 9.0 | 130 |
| gate | 25/40 — 62% | **6** | 29/40 | 8.6 | 132 |

**Pass rate: one task apart on n=40. Noise.**
**False dones: identical. Six and six.**

The gate's only measurable effect is that the agent declares done more often
(23 → 29) — more declarations, not more accurate ones.

## Why it fails, confirmed 6/6

Every one of the gate arm's six false dones is `fix_bug`, and **every one used
`create_file` first**. The agent writes its own test, names that file in
`verified_by`, and the gate accepts a genuine exit 0 against a test the agent
authored.

The gate re-runs *the command the agent chooses*. So it blocks a done with **no**
evidence and waves through a done with **self-authored** evidence. That second
case is the one that matters, and it is the common one.

This is the same trick `test_agent_completes_task.py` already defends against by
hash-checking its verifier. The gate is vulnerable to it one level down.

## What the earlier number was

The 5×5 run reported 7/10 → 9/10 and false dones 1 → 0. Both were small-sample
luck. At n=40 the pass rate is 60% vs 62% and false dones are 6 vs 6. The 5×5
was flagged at the time as "consistent with, but not established by" — it should
have been flagged harder, because it was then used to justify the merge.

## The fix this points at

`verified_by` must name something the agent did not author. The registry already
tracks every `create_file` and `edit_file` it performs, so it can refuse a
verification command that references a file written during the run. Until that
exists, the gate is decoration: it costs one extra command execution per `done`
and stops nothing that actually happens.

**Options, in order of honesty:**
1. Add the provenance check — refuse `verified_by` naming a file the agent wrote.
2. Revert the gate. It is not harmful, but it claims a guarantee it does not
   provide, and an unearned guarantee is worse than none.

Doing neither leaves a gate in the loop that reads like a safety property and is
not one.
