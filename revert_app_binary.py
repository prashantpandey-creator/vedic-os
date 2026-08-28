import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

content = content.replace("import orjson\n", "import json\n")
content = content.replace("    import orjson\n", "    import json\n")

content = content.replace("orjson.dumps(", "json.dumps(")
content = content.replace("orjson.loads(", "json.loads(")
content = content.replace("orjson.dump(", "json.dump(")

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
