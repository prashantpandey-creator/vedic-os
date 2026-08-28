import sys

with open("/Users/badenath/projects/local-llm-ui/core/checkpoint.py", "r") as f:
    content = f.read()

# Replace json with orjson
content = content.replace("import json", "import orjson")

# orjson uses dumpb instead of dumps, and requires open("wb") instead of "w"
content = content.replace("json.dump(state, f, indent=2)", "f.write(orjson.dumps(state, option=orjson.OPT_INDENT_2))")
content = content.replace('open(cp_path, "w", encoding="utf-8")', 'open(cp_path, "wb")')

content = content.replace("json.load(f)", "orjson.loads(f.read())")
content = content.replace('open(cp_path, "r", encoding="utf-8")', 'open(cp_path, "rb")')

with open("/Users/badenath/projects/local-llm-ui/core/checkpoint.py", "w") as f:
    f.write(content)
