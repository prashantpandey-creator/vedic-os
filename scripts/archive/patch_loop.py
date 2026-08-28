import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "r") as f:
    content = f.read()

# Add loop detection variables
old_init = """    execution_log = []"""
new_init = """    execution_log = []
    action_history = []
    stuck_warnings = 0"""
content = content.replace(old_init, new_init)

# Check for identical actions
old_action_check = """            action = action_data.get("action")
            
            if action == "done":"""
new_action_check = """            action = action_data.get("action")
            
            # Intelligent Loop Detection
            current_action_str = json.dumps(action_data, sort_keys=True)
            if current_action_str in action_history[-3:]:
                stuck_warnings += 1
                if stuck_warnings >= 2:
                    step_expander.error("🚨 **[CRITICAL LOOP DETECTED]** The agent has repeatedly attempted the exact same action and is stuck. Terminating loop for safety.")
                    messages.append({"role": "user", "content": "You are repeating the same failed action endlessly. The system has terminated you."})
                    break
                else:
                    step_expander.warning("⚠️ **[STUCK STATE PREVENTED]** Agent attempted a duplicate action. Forcing pivot...")
                    messages.append({"role": "user", "content": "🚨 SYSTEM OVERRIDE: You just attempted the exact same action you already tried recently. It did not work. You MUST try a completely different approach, edit a different file, or declare 'done'."})
                    action_history.append("FORCED_PIVOT")
                    continue
            else:
                action_history.append(current_action_str)
                stuck_warnings = 0

            if action == "done":"""
content = content.replace(old_action_check, new_action_check)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_agent.py", "w") as f:
    f.write(content)

print("Intelligent Loop Detection patched.")
