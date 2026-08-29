import os
from litellm import completion

# Ensure LiteLLM knows where the local Ollama instance is
os.environ["OLLAMA_API_BASE"] = "http://127.0.0.1:11434"

def generate_response(model_name: str, messages: list, temperature: float = 0.1) -> str:
    """
    Universal LLM Gateway.
    Prefix model_name with the provider (e.g., 'ollama/llama3.1-8b', 'gemini/gemini-1.5-pro', 'anthropic/claude-3-5-sonnet-20240620').
    LiteLLM handles the routing and formats automatically.
    """
    try:
        # LiteLLM abstracts the REST APIs for us
        response = completion(
            model=model_name,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[GATEWAY ERROR] Failed to route to {model_name}: {e}")
        return '{"action": "error", "thought": "API Gateway Failure."}'
