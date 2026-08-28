from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import orjson
import asyncio
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.terminal_engine import TerminalEngine
from core.tool_registry import ToolRegistry
from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action, get_omni_system_prompt

app = FastAPI(title="Vedic Omni-Agent Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.websocket("/ws/agent")
async def agent_loop(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Wait for initialization configuration
        config = await websocket.receive_json()
        intent = config.get("intent", "Analyze the repository")
        workspace = config.get("workspace", "/Users/badenath/projects/local-llm-ui")
        coder_model = config.get("model", "mannix/llama3.1-8b-abliterated:latest")
        
        await websocket.send_json({"type": "status", "msg": "🚀 Initializing Vedic Omni-Agent..."})
        
        # Init Phase 1 (Blueprint)
        messages, blueprint = init_omni_loop(intent, "qwen2.5:0.5b", coder_model, workspace_dir=workspace, status_container=None)
        
        await websocket.send_json({"type": "blueprint", "msg": blueprint})
        
        terminal = TerminalEngine(workspace_dir=workspace)
        registry = ToolRegistry(workspace, terminal)
        
        step = 1
        max_steps = 20
        
        while step <= max_steps:
            await websocket.send_json({"type": "status", "msg": f"⏳ Computing Step {step}..."})
            
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
