import os
import re

with open("backend/main.py", "r") as f:
    content = f.read()

target = """            raw_response = generate_next_thought(coder_model, messages, step_placeholder=None)
            messages.append({"role": "assistant", "content": raw_response})
            await websocket.send_json({"type": "thought", "msg": raw_response})"""

replacement = """            from core.llm_gateway import generate_response_stream
            raw_response = ""
            async for chunk in generate_response_stream(coder_model, messages):
                raw_response += chunk
                await websocket.send_json({"type": "token", "msg": chunk})
            
            messages.append({"role": "assistant", "content": raw_response})
            await websocket.send_json({"type": "thought", "msg": raw_response})"""

content = content.replace(target, replacement)

with open("backend/main.py", "w") as f:
    f.write(content)
