import sys

with open("/Users/badenath/projects/local-llm-ui/tests/run_swe_lite.py", "r") as f:
    content = f.read()

content = content.replace(
    """                print(f"[{action_data.get('action')}]")""",
    """                print(f"[{action_data.get('action')}]")\n                if action_data.get("action") == "error":\n                    print(f"    Raw: {raw_response[:200]}...")"""
)

with open("/Users/badenath/projects/local-llm-ui/tests/run_swe_lite.py", "w") as f:
    f.write(content)
