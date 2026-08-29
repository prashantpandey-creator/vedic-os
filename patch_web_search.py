import os
import re

with open("core/tool_registry.py", "r") as f:
    content = f.read()

# Add web_search to system prompt
target_prompt = """9. query_memory (Retrieve past bugs, architectural decisions, and fixes from the Vyasa RAG Vector Database)
{"thought": "...", "action": "query_memory", "query": "How did we fix the JWT token issue last time?"}

10. commit_memory (Save a hard-won bug fix or architectural decision to the permanent Vyasa RAG database)
{"thought": "...", "action": "commit_memory", "fact": "The Next.js frontend runs on port 3000, not 8080."}

11. visual_debug (Spawns a headless browser, takes a screenshot of localhost, and critiques the UI with Vision)
{"thought": "...", "action": "visual_debug", "url": "http://localhost:3000"}"""

replacement_prompt = target_prompt + """

12. web_search (Bypass your training cutoff by scraping DuckDuckGo and live documentation)
{"thought": "...", "action": "web_search", "query": "Litellm python example"}"""

content = content.replace(target_prompt, replacement_prompt)

# Add execute block
target_execute = """        elif action == "visual_debug":
            url = action_data.get("url", "http://localhost:3000")
            return debug_ui(url)"""

replacement_execute = target_execute + """

        elif action == "web_search":
            query = action_data.get("query", "")
            try:
                import urllib.request
                import urllib.parse
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                html = urllib.request.urlopen(req).read().decode('utf-8')
                
                # Super lightweight regex extractor to grab snippet text
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
                clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets]
                
                if not clean_snippets:
                    return {"type": "info", "msg": "No results found for that query."}
                    
                result_text = "\\n\\n".join([f"Result {i+1}: {s}" for i, s in enumerate(clean_snippets[:5])])
                return {"type": "info", "msg": f"Web Search Results:\\n{result_text}"}
            except Exception as e:
                return {"type": "error", "msg": f"Web Search Failed: {e}"}"""

content = content.replace(target_execute, replacement_execute)

with open("core/tool_registry.py", "w") as f:
    f.write(content)
