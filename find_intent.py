with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "intent_prompt = st.text_area" in line:
        print(f"Line {i}: {line.strip()}")
