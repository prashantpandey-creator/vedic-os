from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import asyncio
import requests
import re
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.terminal_engine import TerminalEngine
from core.tool_registry import ToolRegistry
from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action
from backend.vram_manager import clear_all_vram_except, enforce_context_window

app = FastAPI(title="Vedic Omni-Agent Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_code(text):
    match = re.search(r'```[a-zA-Z]*\n(.*?)\n```', text, re.DOTALL)
    if match: return match.group(1)
    match = re.search(r'```(.*?)```', text, re.DOTALL)
    if match: return match.group(1).strip()
    return text

@app.websocket("/ws/agent")
async def agent_loop(websocket: WebSocket):
    await websocket.accept()
    try:
        config = await websocket.receive_json()
        intent = config.get("intent", "Analyze the repository")
        workspace = config.get("workspace", "/Users/badenath/projects/local-llm-ui")
        coder_model = config.get("model", "mannix/llama3.1-8b-abliterated:latest")
        editor_model = "granite4:3b-h" # IBM Granite routing target
        
        await websocket.send_json({"type": "status", "msg": "🧹 Freeing up VRAM..."})
        clear_all_vram_except([coder_model, editor_model, "qwen2.5:0.5b"])
        await websocket.send_json({"type": "status", "msg": "🚀 Initializing Vedic Omni-Agent..."})
        
        messages, blueprint = init_omni_loop(intent, "qwen2.5:0.5b", coder_model, workspace_dir=workspace, status_container=None)
        await websocket.send_json({"type": "blueprint", "msg": blueprint})
        
        terminal = TerminalEngine(workspace_dir=workspace)
        registry = ToolRegistry(workspace, terminal)
        
        step = 1
        max_steps = 20
        
        while step <= max_steps:
            messages = enforce_context_window(messages, max_turns=6)
            await websocket.send_json({"type": "status", "msg": f"⏳ Llama is Thinking (Step {step})..."})
            
            raw_response = generate_next_thought(coder_model, messages, step_placeholder=None)
            messages.append({"role": "assistant", "content": raw_response})
            await websocket.send_json({"type": "thought", "msg": raw_response})
            
            action_data = parse_action(raw_response)
            if not action_data or action_data.get("action") == "error":
                await websocket.send_json({"type": "error", "msg": "Malformed JSON. Retrying..."})
                messages.append({"role": "user", "content": "Error: Your JSON block was malformed. Fix it."})
                step += 1
                continue
                
            action = action_data.get("action")
            await websocket.send_json({"type": "action", "action": action, "args": action_data})
            
            if action == "done":
                await websocket.send_json({"type": "status", "msg": "✅ Task Complete!"})
                break
            
            # --- MULTI-AGENT ROUTER ---
            if action == "edit_file" and "instruction" in action_data:
                filepath = os.path.join(workspace, action_data["file"])
                instruction = action_data["instruction"]
                
                await websocket.send_json({"type": "status", "msg": f"🛠️ Delegating to Granite for code editing..."})
                
                try:
                    with open(filepath, "r") as f:
                        current_code = f.read()
                        
                    prompt = f"Instruction: {instruction}\n\nCURRENT CODE:\n```\n{current_code}\n```\n\nRewrite the code to fulfill the instruction. Output ONLY the complete updated code inside ``` blocks."
                    
                    res = requests.post("http://127.0.0.1:11434/api/chat", json={
                        "model": editor_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }).json()
                    
                    granite_output = res.get("message", {}).get("content", "")
                    fixed_code = extract_code(granite_output)
                    
                    with open(filepath, "w") as f:
                        f.write(fixed_code)
                    
                    msg = f"Granite successfully updated {filepath} based on your instruction."
                except Exception as e:
                    msg = f"Granite failed to edit file: {e}"
            else:
                tool_result = registry.execute_tool(action_data)
                msg = tool_result.get("msg", str(tool_result))
            
            await websocket.send_json({"type": "tool_result", "msg": msg})
            messages.append({"role": "user", "content": f"Tool Execution Result:\n```\n{msg}\n```"})
            step += 1
            
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Agent Loop Error: {e}")
        await websocket.send_json({"type": "error", "msg": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
