import sys

with open("/Users/badenath/projects/local-llm-ui/app.py", "r") as f:
    content = f.read()

# Replace the master CSS injection
content = content.replace('""", unsafe_allow_html=True)', '""")')
content = content.replace('st.markdown("""\n<style>', 'st.html("""\n<style>')

# Replace the manual <br> tags
content = content.replace('st.markdown("<br>", unsafe_allow_html=True)', 'st.html("<br>")')

with open("/Users/badenath/projects/local-llm-ui/app.py", "w") as f:
    f.write(content)
