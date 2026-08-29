import requests

OLLAMA_URL = "http://127.0.0.1:11434"

def get_loaded_models():
    """Returns a list of currently loaded models in VRAM."""
    try:
        res = requests.get(f"{OLLAMA_URL}/api/ps", timeout=2)
        if res.status_code == 200:
            return [m["name"] for m in res.json().get("models", [])]
    except Exception as e:
        print(f"[VRAM] Failed to reach Ollama: {e}")
    return []

def evict_model(model_name: str):
    """Evicts a specific model from VRAM by setting keep_alive to 0."""
    print(f"[VRAM] 🧹 Evicting {model_name} from memory...")
    try:
        requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": model_name,
            "keep_alive": 0
        }, timeout=2)
    except: pass

def clear_all_vram_except(allowed_models: list):
    """Purges all heavy/unused models from VRAM to prevent system hanging."""
    loaded = get_loaded_models()
    for model in loaded:
        if model not in allowed_models:
            evict_model(model)
            
# Wording is load-bearing, not cosmetic. The first version read
#   "[ACTIONS ALREADY TAKEN — these are done; do not repeat them]"
# and paired each action with its raw result, e.g.
#   "edit_file: shipping.py  →  File shipping.py edited successfully."
# The agent read "done" + "successfully" as "the task is solved" and emitted
# `done` after 4 steps without ever re-running the tests. Measured: 2 of 3
# end-to-end failures in that arm were exactly this, claiming completion with
# the tests still red. A tool call succeeding says the WRITE landed, nothing
# about whether it was correct — so the header now says that outright.
LEDGER_MARK = ("[HISTORY — actions already attempted this session. "
               "A tool call that succeeded means only that the call ran; it does NOT mean "
               "the task is solved. Do not repeat these actions, and do not finish until "
               "you have VERIFIED the goal yourself.]")
MAX_LEDGER_ENTRIES = 20


def _action_line(content: str):
    """One compact line describing the action an assistant message chose."""
    # Local import: keeps this module free of an import-time dependency on agents/,
    # and reuses the one JSON extractor rather than growing a second one.
    from agents.omni_state_machine import parse_action
    data = parse_action(content)
    action = (data or {}).get("action")
    if not action or action == "error":
        return None
    detail = next((data[k] for k in
                   ("command", "file", "title", "query", "task", "url", "content")
                   if data.get(k)), "")
    detail = " ".join(str(detail).split())[:80]
    return f"- {action}: {detail}" if detail else f"- {action}"


def _outcome(content: str) -> str:
    """The gist of a tool result, flattened to one short line."""
    fenced = content.split("```")
    body = fenced[1] if len(fenced) > 1 else content
    return " ".join(body.split())[:100]


def enforce_context_window(messages: list, max_turns=6):
    """
    Bound the context without erasing what the agent has already done.

    Keeps: [system, original intent] + a compact ledger of dropped actions +
    the last `max_turns` messages.

    Two failures this has to prevent, both observed in real runs:

    1. Losing the TASK. messages[1] is the user's intent and it is not repeated
       in the system prompt. Keeping only messages[0] meant the agent forgot what
       it had been asked to do on the 4th pass through a 20-step loop.

    2. Losing its OWN ACTIONS. Dropping the middle wholesale erased the agent's
       history of what it had already run. Observed: after its edit made the
       tests pass, an agent re-ran the identical test command four more times,
       then re-read the file it had just written, then concluded "the test
       passes, so my initial plan to edit stats.py was based on a false premise"
       — it had forgotten making the edit. Correct answers, most of the step
       budget burned re-establishing known facts.

    The ledger replaces the dropped block rather than adding a new layer: many
    verbose message pairs collapse into one line each, and it is capped at
    MAX_LEDGER_ENTRIES so it cannot grow without bound. It is rebuilt from the
    messages being dropped, so both cli.py and backend/main.py get it with no
    call-site change.
    """
    pinned = messages[:2]  # [system, original intent]
    if len(messages) <= (max_turns + len(pinned)):
        return messages

    middle = messages[len(pinned):-max_turns]
    recent = messages[-max_turns:]

    lines = []
    for m in middle:
        content = m.get("content", "") or ""
        if content.startswith(LEDGER_MARK):
            lines.extend(content.splitlines()[1:])          # carry the old ledger forward
        elif m.get("role") == "assistant":
            line = _action_line(content)
            if line:
                lines.append(line)
        elif m.get("role") == "user" and "Tool Execution Result" in content and lines:
            lines[-1] += f"  →  {_outcome(content)}"        # attach the result to its action

    lines = lines[-MAX_LEDGER_ENTRIES:]
    ledger = [{"role": "user", "content": LEDGER_MARK + "\n" + "\n".join(lines)}] if lines else []

    # Don't duplicate a pinned message that is still inside the recent window.
    recent = [m for m in recent if not any(m is p for p in pinned)]

    print(f"[MEMORY] ✂️ Truncating context — {len(lines)} action(s) kept in the ledger.")
    messages[:] = pinned + ledger + recent
    return messages

