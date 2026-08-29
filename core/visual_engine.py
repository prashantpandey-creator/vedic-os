import os
import subprocess
import base64
import tempfile
import requests
from config import VISION_MODEL
from core.ollama_api import OLLAMA_URL

NODE_SCRIPT = """
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({headless: 'new'});
  const page = await browser.newPage();
  await page.goto(process.argv[2], {waitUntil: 'networkidle2'});
  await page.screenshot({path: process.argv[3]});
  await browser.close();
})();
"""

def take_screenshot(url="http://localhost:3000"):
    """
    Screenshot `url` and return it base64-encoded.

    Both artefacts used to be written into the repo root — screenshot.js as a
    generated source file, screenshot.png read back via a CWD-relative open(),
    so a stale PNG from an earlier run would be sent to the model whenever the
    process CWD differed from the repo root. Both now live in a temp dir.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmp = tempfile.mkdtemp(prefix="omni_shot_")
    script_path = os.path.join(tmp, "screenshot.js")
    shot_path = os.path.join(tmp, "screenshot.png")
    with open(script_path, "w") as f:
        f.write(NODE_SCRIPT)

    # node resolves `require('puppeteer')` from the script's directory upward, so
    # run from the repo root where node_modules actually lives.
    subprocess.run(["node", script_path, url, shot_path],
                   cwd=repo_root, check=True, capture_output=True, timeout=120)

    with open(shot_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def debug_ui(url="http://localhost:3000"):
    try:
        b64_image = take_screenshot(url)
        
        prompt = (
            "You are a UI/UX expert. Look at this screenshot of the localhost preview. "
            "Identify any layout issues, CSS bugs, or missing elements."
        )
        
        res = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": VISION_MODEL,
                "messages": [{
                    "role": "user", 
                    "content": prompt,
                    "images": [b64_image]
                }],
                "stream": False
            },
            timeout=120
        ).json()

        # Ollama reports a missing model as a 200 with {"error": ...}. That fell
        # through to "Error reading image.", which told the agent the screenshot
        # was bad when the real problem was that the vision model isn't pulled.
        if "error" in res:
            return (f"Vision model '{VISION_MODEL}' unavailable: {res['error']}. "
                    f"Run `ollama pull {VISION_MODEL}`, or set VISION_MODEL to one you have.")
        content = res.get("message", {}).get("content", "")
        return content or f"Vision model '{VISION_MODEL}' returned nothing."
    except subprocess.CalledProcessError as e:
        return f"Screenshot failed (is anything serving {url}?): {(e.stderr or b'').decode()[:300]}"
    except Exception as e:
        return f"Visual Debugging Failed: {type(e).__name__}: {e}"
