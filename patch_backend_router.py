import os

with open("backend/main.py", "r") as f:
    content = f.read()

target = """            messages = enforce_context_window(messages, max_turns=6)
            await websocket.send_json({"type": "status", "msg": f"⏳ Llama is Thinking (Step {step})..."})"""

replacement = """            messages = enforce_context_window(messages, max_turns=6)
            
            # DYNAMIC ROUTING
            from core.router import dynamic_route
            routed_model = dynamic_route(messages)
            if routed_model != coder_model:
                await websocket.send_json({"type": "status", "msg": f"🔄 Dynamic Router switching to {routed_model} for complex task..."})
                coder_model = routed_model
                
            await websocket.send_json({"type": "status", "msg": f"⏳ Llama is Thinking (Step {step}) via {coder_model}..."})"""

content = content.replace(target, replacement)

with open("backend/main.py", "w") as f:
    f.write(content)
