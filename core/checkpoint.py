import os
import json
import time

CHECKPOINT_DIR = ".omni_checkpoints"

def save_checkpoint(workspace_dir, state):
    cp_dir = os.path.join(workspace_dir, CHECKPOINT_DIR)
    os.makedirs(cp_dir, exist_ok=True)
    checkpoint = {
        "timestamp": time.time(),
        "intent": state.get("intent_prompt", ""),
        "step": state.get("omni_step", 1),
        "phase": state.get("phase", 1),
        "state": state.get("omni_state", "IDLE"),
        "messages": state.get("omni_messages", []),
        "log": state.get("omni_log", []),
        "action_history": state.get("action_history", []),
        "phase_summaries": state.get("phase_summaries", []),
    }
    cp_file = os.path.join(cp_dir, "checkpoint_phase_{}.json".format(checkpoint["phase"]))
    with open(cp_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, default=str)
    latest_file = os.path.join(cp_dir, "latest.json")
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, default=str)
    return cp_file

def load_checkpoint(workspace_dir):
    latest_file = os.path.join(workspace_dir, CHECKPOINT_DIR, "latest.json")
    if not os.path.exists(latest_file):
        return None
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def clear_checkpoints(workspace_dir):
    cp_dir = os.path.join(workspace_dir, CHECKPOINT_DIR)
    if os.path.exists(cp_dir):
        for f in os.listdir(cp_dir):
            os.remove(os.path.join(cp_dir, f))

def build_phase_summary(log_entries):
    summary = ""
    for entry in log_entries:
        step = entry.get("step", "?")
        action_type = entry.get("type", "unknown")
        if action_type == "command":
            cmd = entry.get("cmd", "")
            output = entry.get("output", "")[:200]
            summary += "- Step {}: Ran '{}' -> {}\n".format(step, cmd, output)
        elif action_type == "edit":
            summary += "- Step {}: Edited '{}'\n".format(step, entry.get("file", "?"))
        elif action_type == "artifact":
            summary += "- Step {}: Created artifact '{}'\n".format(step, entry.get("title", "?"))
        elif action_type == "github_pr":
            summary += "- Step {}: Raised PR -> {}\n".format(step, entry.get("url", "?"))
        elif action_type == "loop_intercept":
            summary += "- Step {}: Loop detected, forced pivot\n".format(step)
        elif action_type == "subagent":
            summary += "- Step {}: Subagent ({}) completed\n".format(step, entry.get("role", "?"))
    return summary if summary else "No actions recorded in this phase."
