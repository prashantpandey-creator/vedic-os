with open("/Users/badenath/projects/local-llm-ui/README.md", "r") as f:
    content = f.read()

content = content.replace("## Running the Engine\\n```bash\\nstreamlit run app.py\\n```", "## Running the Engine\\nThe easiest way to start is with the automated boot script:\\n```bash\\n./launch.sh\\n```\\n\\nOr manually:\\n```bash\\nstreamlit run app.py\\n```")

with open("/Users/badenath/projects/local-llm-ui/README.md", "w") as f:
    f.write(content)
