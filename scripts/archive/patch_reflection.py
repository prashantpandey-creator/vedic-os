import sys

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    content = f.read()

old_instruction = "First, write out a detailed, verbose thought process explaining your reasoning. Then, output your chosen action strictly inside a ```json block."
new_instruction = """First, write out a detailed, verbose thought process explaining your reasoning. 
Second, you MUST write a \"CRITIQUE:\" section where you aggressively challenge your own plan. Ask yourself: \"What could go wrong? Is there a safer way? Am I hallucinating a file path?\"
Finally, after your critique, output your chosen action strictly inside a ```json block."""

content = content.replace(old_instruction, new_instruction)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
    f.write(content)
