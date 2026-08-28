import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

content = content.replace("import json\n", "import orjson\n")
content = content.replace("    import json\n", "    import orjson\n")

# Careful with json.dumps and json.loads
content = content.replace("json.dumps(", "orjson.dumps(")
content = content.replace("json.loads(", "orjson.loads(")
content = content.replace("json.dump(", "orjson.dump(")

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
