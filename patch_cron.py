import os

with open("backend/main.py", "r") as f:
    content = f.read()

target = """if __name__ == "__main__":"""

replacement = """import asyncio

async def background_cron_agent():
    \"\"\"
    Wakes up periodically to check for broken tests, linting errors, or 
    hygiene tasks, and spawns a headless agent loop to fix them autonomously.
    \"\"\"
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

if __name__ == "__main__":"""

content = content.replace(target, replacement)

with open("backend/main.py", "w") as f:
    f.write(content)
