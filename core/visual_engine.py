import os
import subprocess
import base64
import requests
from core.ollama_api import OLLAMA_URL

NODE_SCRIPT = """
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({headless: 'new'});
  const page = await browser.newPage();
  await page.goto(process.argv[2], {waitUntil: 'networkidle2'});
  await page.screenshot({path: 'screenshot.png'});
  await browser.close();
})();
"""

def take_screenshot(url="http://localhost:3000"):
    script_path = os.path.join(os.path.dirname(__file__), "..", "screenshot.js")
    if not os.path.exists(script_path):
        with open(script_path, "w") as f:
            f.write(NODE_SCRIPT)
            
    subprocess.run(["node", "screenshot.js", url], cwd=os.path.dirname(script_path), check=True)
    
    with open("screenshot.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

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
                "model": "llama3.2-vision",
                "messages": [{
                    "role": "user", 
                    "content": prompt,
                    "images": [b64_image]
                }],
                "stream": False
            },
            timeout=120
        ).json()
        
        return res.get("message", {}).get("content", "Error reading image.")
    except Exception as e:
        return f"Visual Debugging Failed: {e}"
