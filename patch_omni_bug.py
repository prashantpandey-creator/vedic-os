import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    content = f.read()

content = content.replace(
    'step_placeholder.markdown(f"**💭 Agent Thoughts:**\\n{raw_response}▌")',
    'if step_placeholder: step_placeholder.markdown(f"**💭 Agent Thoughts:**\\n{raw_response}▌")'
)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
    f.write(content)
