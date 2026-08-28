import os
import sys
import json
import requests
import time
from core.ollama_api import get_loaded_models, evict_model, OLLAMA_URL

def run_architect_pipeline(app_prompt, status_text, progress_bar, selected_model):
    # 1. Unload everything
    status_text.write("🧹 Clearing memory...")
    for m in get_loaded_models():
        evict_model(m.get("name"))
        
    # 2. Architect
    status_text.write("🧠 [THE ARCHITECT] Generating Blueprint...")
    progress_bar.progress(10)
    
    architect_payload = {"model": "architect-compiler", "prompt": app_prompt, "stream": False}
    arch_res = requests.post(f"{OLLAMA_URL}/api/generate", json=architect_payload)
    raw_json = arch_res.json().get("response", "")
    
    if "```json" in raw_json: raw_json = raw_json.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_json: raw_json = raw_json.split("```")[1].split("```")[0].strip()
        
    try:
        graph = json.loads(raw_json)
        # We assume the caller handles UI rendering of success
    except Exception as e:
        raise Exception("Architect failed to generate valid JSON.")
        
    progress_bar.progress(30)
    
    # 3. Swap to Coder
    status_text.write("🧹 Swapping to Genius Coder...")
    evict_model("architect-compiler")
    
    # 4. Generate Code
    entities = [e for e in graph.get("entities", []) if e.get("type") in ["page", "component", "api_route", "data_model"]]
    if not entities:
        raise Exception("No codeable entities found in blueprint.")
        
    app_name = graph.get("name", "GeneratedApp").replace(" ", "_")
    os.makedirs(app_name, exist_ok=True)
    generated_files = []
    
    for i, entity in enumerate(entities):
        entity_id = entity.get("id", "unknown_file")
        entity_type = entity.get("type", "unknown_type")
        
        status_text.write(f"👨‍💻 [THE CODER] Writing {entity_type}: {entity_id}...")
        
        system_prompt = "You are an elite software engineer. The System Architect has handed you a JSON blueprint node. Your job is to write the complete, production-ready code for this specific node. Do NOT output markdown. Do NOT output chat. Output ONLY the raw code."
        coder_payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Write the code for this architectural node:\n{json.dumps(entity, indent=2)}"}
            ],
            "stream": False
        }
        
        coder_res = requests.post(f"{OLLAMA_URL}/api/chat", json=coder_payload)
        code = coder_res.json().get("message", {}).get("content", "")
        
        if "```" in code:
            parts = code.split("```")
            if len(parts) >= 3:
                code = parts[1]
                if code.startswith("typescript\n") or code.startswith("javascript\n") or code.startswith("python\n") or code.startswith("tsx\n"):
                    code = "\n".join(code.split("\n")[1:])
        
        filename = f"{app_name}/{entity_id}"
        if entity_type in ["page", "component"]: filename += ".tsx"
        elif entity_type == "api_route": filename += "/route.ts"
        elif entity_type == "data_model": filename += ".prisma"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(code)
            
        generated_files.append({"filename": filename, "code": code})
        progress = 30 + int(((i + 1) / len(entities)) * 50)
        progress_bar.progress(progress)
        
    # [EXECUTION NODE]: Inject deployment script
    deploy_script = "#!/bin/bash\necho 'Setting up Native Execution...'\nnpm init -y\nnpm install react react-dom next\nnpm run dev"
    deploy_path = f"{app_name}/deploy.sh"
    with open(deploy_path, "w") as f: f.write(deploy_script)
    generated_files.append({"filename": deploy_path, "code": deploy_script})
    
    # 5. Vyasa Renderer
    status_text.write(f"🎉 Build Complete! All files saved to the `{app_name}` directory.")
    
    vyasa_path = os.path.expanduser("~/vyasa")
    if vyasa_path not in sys.path:
        sys.path.append(vyasa_path)
    
    try:
        from engine.self_contained import manifest_self_contained
        if "services" not in graph:
            vyasa_graph = {"name": graph.get("name", "LocalApp"), "services": [{"name": "core", "graph": graph}]}
        else:
            vyasa_graph = graph
            
        status_text.write("✨ [VYASA] Rendering interactive sandbox...")
        html_content = manifest_self_contained(vyasa_graph, title="Live Sandbox")
    except Exception as e:
        html_content = None
        
    return graph, generated_files, html_content
