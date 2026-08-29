import os
from litellm import completion

# Ensure LiteLLM knows where the local Ollama instance is
os.environ["OLLAMA_API_BASE"] = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

# Providers this project routes to. Anything whose first path segment is NOT in
# here is assumed to be a local Ollama tag.
KNOWN_PROVIDERS = {
    "ollama", "ollama_chat", "openai", "anthropic", "gemini",
    "openrouter", "cerebras", "azure", "vertex_ai", "bedrock", "together_ai",
    "deepseek", "mistral", "xai",
}


def normalize_model(model_name: str) -> str:
    """
    LiteLLM requires an explicit provider prefix and errors out without one:
      "LLM Provider NOT provided. You passed model=qwen3:4b-instruct-2507-q4_K_M"

    Every caller in this repo passes a bare Ollama tag (config.py's FAST_MODEL,
    core/router.py's dynamic_route return, the /ws/agent `model` field, the CLI).
    So every call failed, the gateway swallowed it into {"action": "error"}, and
    the agent loop burned all 20 steps on "Malformed JSON. Retrying..." without
    ever reaching a model.

    Note the trap: a bare tag can still CONTAIN a slash — `mannix/llama3.1-8b-
    abliterated:latest` is an Ollama tag, not the provider "mannix". Presence of
    a slash is not the test; membership in KNOWN_PROVIDERS is.
    """
    if not model_name:
        return model_name
    head = model_name.split("/", 1)[0].lower()
    if head in KNOWN_PROVIDERS:
        return model_name
    # "claude/..." reads like a provider but litellm has no such prefix — it is
    # "anthropic/". The escalation path hardcoded "claude/claude-3-5-sonnet", so
    # escalation stayed dead even after bare Ollama tags were fixed. Remap rather
    # than silently sending it to Ollama, which would be a worse wrong answer.
    if head == "claude":
        return "anthropic/" + model_name.split("/", 1)[1]
    return f"ollama/{model_name}"


def generate_response(model_name: str, messages: list, temperature: float = 0.1) -> str:
    """
    Universal LLM Gateway.

    A bare name ('qwen3:4b-instruct', 'mannix/llama3.1-8b-abliterated:latest') is
    routed to local Ollama. Prefix explicitly to reach a hosted provider, e.g.
    'anthropic/claude-3-5-sonnet-20240620' or 'openrouter/...'.
    """
    routed = normalize_model(model_name)
    try:
        response = completion(
            model=routed,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[GATEWAY ERROR] Failed to route to {routed}: {e}")
        return '{"action": "error", "thought": "API Gateway Failure."}'


async def generate_response_stream(model_name: str, messages: list, temperature: float = 0.1):
    """
    Streaming twin of generate_response, for the /ws/agent token feed.

    Routes through normalize_model for the same reason the buffered call does —
    every caller hands it a bare Ollama tag. Without this it raised
    "LLM Provider NOT provided" on the first chunk and yielded the error action,
    so the WebSocket loop never reached a model at all.
    """
    from litellm import acompletion
    routed = normalize_model(model_name)
    try:
        response = await acompletion(
            model=routed,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[GATEWAY STREAM ERROR] Failed to route to {routed}: {e}")
        yield '{"action": "error", "thought": "API Gateway Failure."}'
