import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    content = f.read()

# Modify the system prompt to encourage prose thinking before the JSON block
old_prompt = "You must accomplish the user's intent autonomously.\nOutput ONLY valid JSON for your next action."
new_prompt = "You must accomplish the user's intent autonomously.\nFirst, write out a detailed, verbose thought process explaining your reasoning. Then, output your chosen action strictly inside a ```json block."

content = content.replace(old_prompt, new_prompt)

# Also update the stream renderer to stream as markdown instead of a raw json block
# so the user can read the prose nicely.
content = content.replace('step_placeholder.code(raw_response, language="json")', 'step_placeholder.markdown(f"**💭 Agent Thoughts:**\\n{raw_response}▌")')

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
    f.write(content)
