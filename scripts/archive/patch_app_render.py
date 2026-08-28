import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

content = content.replace("if 'raw' in log: st.code(log['raw'], language=\"json\")", "if 'raw' in log: st.markdown(log['raw'])")

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
