from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import INGEST_MODEL, EDITOR_MODEL, FAST_MODEL, ESCALATION_MODEL

from core.terminal_engine import TerminalEngine
from core.tool_registry import ToolRegistry
from agents.omni_state_machine import init_omni_loop, generate_next_thought, parse_action
from backend.vram_manager import clear_all_vram_except, enforce_context_window

app = FastAPI(title="Vedic Omni-Agent Engine")

# /ws/agent runs arbitrary shell on this machine. Only these origins may reach it.
# WebSockets are NOT covered by CORS, so the check is enforced in the handler too —
# without it, any page the user visited could open ws://localhost:8000/ws/agent and
# drive the terminal. Set OMNI_ALLOWED_ORIGINS to override.
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "OMNI_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/agent")
async def agent_loop(websocket: WebSocket):
    # Browsers always send Origin; native clients (the CLI, tests) send none.
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008, reason="origin not allowed")
        print(f"[SECURITY] Rejected /ws/agent from origin {origin!r}")
        return

    await websocket.accept()
    try:
        config = await websocket.receive_json()
        intent = config.get("intent", "Analyze the repository")
        workspace = config.get("workspace", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        coder_model = config.get("model", FAST_MODEL)
        editor_model = EDITOR_MODEL

        await websocket.send_json({"type": "status", "msg": "🧹 Freeing up VRAM..."})
        clear_all_vram_except([coder_model, editor_model, INGEST_MODEL])
        await websocket.send_json({"type": "status", "msg": "🚀 Initializing Vedic Omni-Agent..."})
        
        messages, blueprint = init_omni_loop(intent, INGEST_MODEL, coder_model, workspace_dir=workspace, status_container=None)
        await websocket.send_json({"type": "blueprint", "msg": blueprint})
        
        terminal = TerminalEngine(workspace_dir=workspace)
        registry = ToolRegistry(workspace, terminal)
        
        step = 1
        max_steps = 20
        
        while step <= max_steps:
            messages = enforce_context_window(messages, max_turns=6)
            
            # DYNAMIC ROUTING
            from core.router import dynamic_route
            routed_model = dynamic_route(messages)
            if routed_model != coder_model:
                await websocket.send_json({"type": "status", "msg": f"🔄 Dynamic Router switching to {routed_model} for complex task..."})
                coder_model = routed_model
                
            await websocket.send_json({"type": "status", "msg": f"⏳ Llama is Thinking (Step {step}) via {coder_model}..."})
            
            from core.llm_gateway import generate_response_stream
            raw_response = ""
            async for chunk in generate_response_stream(coder_model, messages):
                raw_response += chunk
                await websocket.send_json({"type": "token", "msg": chunk})
            
            messages.append({"role": "assistant", "content": raw_response})
            await websocket.send_json({"type": "thought", "msg": raw_response})
            
            action_data = parse_action(raw_response)
            if not action_data or action_data.get("action") == "error":
                await websocket.send_json({"type": "error", "msg": "Malformed JSON. Retrying..."})
                messages.append({"role": "user", "content": "Error: Your JSON block was malformed. Fix it."})
                step += 1
                continue
                
            
            # --- HYBRID ESCALATION (CRY FOR HELP PROTOCOL) ---
            import json
            action_data_no_thought = {k: v for k, v in action_data.items() if k != 'thought'}
            current_action_str = json.dumps(action_data_no_thought, sort_keys=True)
            if 'action_history' not in locals():
                action_history = []
            action_history.append(current_action_str)
            
            if len(action_history) >= 3 and action_history[-1] == action_history[-2] == action_history[-3]:
                if os.environ.get("ANTHROPIC_API_KEY"):
                    await websocket.send_json({"type": "status", "msg": "🚨 RECURSIVE LOOP DETECTED. ESCALATING TO CLAUDE..."})
                    coder_model = ESCALATION_MODEL
                    action_history.clear()
                    messages.append({"role": "user", "content": "SYSTEM ESCALATION: Your local Llama model got stuck in an infinite loop failing to execute the above tool. You are Claude 3.5 Sonnet. Read the tracebacks, break the loop, and solve the problem."})
                    step += 1
                    continue
                else:
                    await websocket.send_json({"type": "status", "msg": "⚠️ Loop Detected, but Local Mode enforced. Halting."})
                    await websocket.send_json({"type": "error", "msg": "Stuck in a recursive loop without API keys."})
                    break

            action = action_data.get("action")

            await websocket.send_json({"type": "action", "action": action, "args": action_data})
            
            if action == "done":
                accepted, done_msg = registry.check_done(action_data)
                if accepted:
                    await websocket.send_json({"type": "status", "msg": f"✅ Task Complete! {done_msg}"})
                    break
                await websocket.send_json({"type": "status", "msg": f"↩ {done_msg}"})
                messages.append({"role": "user", "content": done_msg})
                step += 1
                continue
            
            # All tools — including the editor-model rewrite — go through the
            # registry, which routes every write through write_verified().
            if action == "edit_file" and "instruction" in action_data:
                await websocket.send_json({"type": "status", "msg": "🛠️ Delegating to the editor model..."})
            tool_result = registry.execute_tool(action_data, main_model=coder_model)
            msg = tool_result.get("msg", str(tool_result))


            await websocket.send_json({"type": "tool_result", "msg": msg})
            messages.append({"role": "user", "content": f"Tool Execution Result:\n```\n{msg}\n```"})
            step += 1
            
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Agent Loop Error: {e}")
        await websocket.send_json({"type": "error", "msg": str(e)})

import asyncio

async def background_cron_agent():
    """
    Wakes up periodically to check for broken tests, linting errors, or 
    hygiene tasks, and spawns a headless agent loop to fix them autonomously.
    """
    while True:
        await asyncio.sleep(1800)  # Sleep for 30 minutes
        print("[CRON] Waking up Omni-Agent for background project hygiene...")
        try:
            # Here it would invoke the agent_loop headlessly.
            # We simulate the hook for now.
            pass
        except Exception as e:
            print(f"[CRON ERROR] {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(background_cron_agent())

if __name__ == "__main__":
    import uvicorn
    # Loopback only. This endpoint executes shell commands with no authentication;
    # 0.0.0.0 handed that to every machine on the LAN. Override deliberately with
    # OMNI_HOST if you know what you are exposing.
    uvicorn.run(app, host=os.getenv("OMNI_HOST", "127.0.0.1"), port=int(os.getenv("OMNI_PORT", "8000")))
