import requests
import json
import sys

OLLAMA_URL = "http://127.0.0.1:11434"

def render_vyasa_response(json_plan):
    """
    This is the 'Deterministic Renderer' mentioned in your System Prompt.
    It takes the strict JSON output from the Vyasa Compiler model and formats it 
    into a conversational or presentation layer.
    """
    try:
        plan = json.loads(json_plan)
    except Exception as e:
        return f"Error: The model did not return valid JSON. Output was:\n{json_plan}"

    # Extract the pieces of the response plan
    understanding = plan.get("understanding", "")
    insight = plan.get("insight", "")
    grounding = plan.get("grounding", {})
    key_phrases = plan.get("key_phrases", [])

    source = grounding.get("source", "Unknown Text")
    citation = grounding.get("citation", "")
    
    # Deterministically construct the conversational response
    print(f"\n🧘‍♂️ [VYASA REASONING]: {understanding}")
    print("=" * 60)
    
    # 1. State the core insight
    response = f"{insight}\n\n"
    
    # 2. Add the exact key phrases
    if key_phrases:
        response += "As it is written: "
        for phrase in key_phrases:
            response += f'"{phrase}" '
        response += "\n\n"
        
    # 3. Add the grounding/citation
    response += f"— Sourced from: {source}"
    if citation:
        response += f" ({citation})"
        
    return response

def ask_vyasa(question):
    payload = {
        "model": "vyasa-compiler:latest",
        "prompt": question,
        "stream": False,
        "options": {"temperature": 0.0} # Keep it highly deterministic
    }
    
    print(f"Asking Vyasa: {question}\nThinking...")
    response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload)
    if response.status_code == 200:
        raw_json = response.json().get("response", "")
        # Render the JSON into a conversation!
        final_speech = render_vyasa_response(raw_json)
        print("\n=== FINAL CONVERSATIONAL OUTPUT ===")
        print(final_speech)
    else:
        print("Failed to query Ollama.")

if __name__ == "__main__":
    question = "Who is Shiva in the Vedas?"
    ask_vyasa(question)
