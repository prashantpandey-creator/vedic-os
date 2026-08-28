import sys
import re

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    app_code = f.read()

# 1. Remove the max_steps slider
app_code = re.sub(r'max_steps = st\.slider\("Max Autonomous Steps".*?\n', '', app_code)

# 2. Fix the hardcoded "npm test" prompt
app_code = app_code.replace('"Run \'npm test\', find the failing tests, and fix the codebase."', '""')

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(app_code)


with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "r") as f:
    omni_code = f.read()

# 3. Meaningfully separate Memory vs Blueprint in the prompt
old_prompt = """    system = f\"\"\"You are the Vedic Omni-Agent. You have native Zsh terminal access to this Mac.
PROJECT MEMORY:
{memory}

ARCHITECTURAL BLUEPRINT:
{blueprint}"""

new_prompt = """    system = f\"\"\"You are the Vedic Omni-Agent. You have native Zsh terminal access to this Mac.

=========================================
1. HISTORICAL PROJECT MEMORY (Context)
=========================================
The following is historical context, user preferences, and past conversational memory. Use this to understand WHY you are doing things.
{memory}

=========================================
2. CURRENT CODEBASE BLUEPRINT (State)
=========================================
The following is the real-time structure of the Git repository/codebase as it exists on the hard drive right now. Use this to understand WHAT files exist.
{blueprint}
========================================="""

omni_code = omni_code.replace(old_prompt, new_prompt)

with open("/Users/badenath/projects/local-llm-ui/agents/omni_state_machine.py", "w") as f:
    f.write(omni_code)
