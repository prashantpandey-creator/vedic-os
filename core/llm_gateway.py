import json
import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from litellm import completion

# Ensure LiteLLM knows where the local Ollama instance is
os.environ["OLLAMA_API_BASE"] = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

# litellm defaults to 600s. Observed live: one stalled Ollama call ate ten minutes
# of a twelve-step run, then returned "Connection timed out after 600.0 seconds"
# and cost the step anyway.
#
# 300s, not lower. Measured on this box: a trivial "say OK" took 56.8s with two
# models resident and other sessions competing, and a legitimate whole-file
# rewrite of a 306-line file took 212s. A first attempt at 120s killed real work
# — the ceiling has to clear a cold model load under contention, not just a warm
# token stream. Raise it further for genuinely slow hosted models.
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "300"))

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
        # The deadline is enforced HERE, not by litellm.
        #
        # litellm's own timeout does not cut a stalled Ollama socket. Verified
        # against a server that accepts the connection and never replies:
        # completion(timeout=5), completion(request_timeout=5) and
        # litellm.request_timeout = 5 all hung past a 20s cap — SIGALRM did not
        # break it either, because the block is below the Python bytecode loop.
        # Observed in production as "Connection timed out after 600.0 seconds",
        # ten minutes of a twelve-step run gone.
        #
        # A worker thread we can walk away from is the thing that actually works.
        # The orphan dies when its socket finally errors; the agent loop gets its
        # step back either way.
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                completion,
                model=routed,
                messages=messages,
                temperature=temperature,
                timeout=LLM_TIMEOUT,
            )
            try:
                response = future.result(timeout=LLM_TIMEOUT)
            except FuturesTimeout:
                raise TimeoutError(
                    f"no response from {routed} in {LLM_TIMEOUT:.0f}s "
                    f"(raise LLM_TIMEOUT if the model is genuinely this slow)"
                )
            finally:
                pool._threads.clear()  # don't block on the orphan at exit
        return response.choices[0].message.content
    except Exception as e:
        print(f"[GATEWAY ERROR] Failed to route to {routed}: {e}")
        # Carry the real reason. The loops used to reply "Your JSON block was
        # malformed. Fix it." to a TRANSPORT failure — telling the model to fix
        # output it never produced, which is how a stalled connection looked like
        # a model defect for months.
        return json.dumps({
            "action": "error",
            "thought": "API Gateway Failure.",
            "gateway_error": f"{type(e).__name__}: {e}"[:300],
        })


async def generate_response_stream(model_name: str, messages: list, temperature: float = 0.1):
    """
    Streaming twin of generate_response, for the /ws/agent token feed.

    Carries BOTH properties the buffered call has, because the merge that brought
    this function in had each on a different branch:

    1. ROUTING. normalize_model, for the same reason the buffered call needs it —
       every caller hands it a bare Ollama tag (config's FAST_MODEL, the value
       core/router.dynamic_route returns, the /ws/agent `model` field). Without
       it litellm raised "LLM Provider NOT provided" on the first chunk and the
       WebSocket loop never reached a model at all.

    2. A DEADLINE. The sync side had to escape litellm's timeout into a worker
       thread because a stalled socket blocks below the bytecode loop. Async does
       not have that problem — the awaits are real suspension points, so
       asyncio.wait_for actually fires. The deadline is applied twice: once on
       connect, and once per chunk, so a stream that opens and then goes silent
       is cut too. Both use the same LLM_TIMEOUT as the buffered path.
    """
    import asyncio

    from litellm import acompletion
    routed = normalize_model(model_name)
    try:
        response = await asyncio.wait_for(
            acompletion(
                model=routed,
                messages=messages,
                temperature=temperature,
                stream=True,
                timeout=LLM_TIMEOUT,
            ),
            timeout=LLM_TIMEOUT,
        )
        stream = response.__aiter__()
        while True:
            try:
                chunk = await asyncio.wait_for(stream.__anext__(), timeout=LLM_TIMEOUT)
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"{routed} opened a stream then went silent for "
                    f"{LLM_TIMEOUT:.0f}s (raise LLM_TIMEOUT if it is genuinely "
                    f"this slow)"
                )
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[GATEWAY STREAM ERROR] Failed to route to {routed}: {e}")
        # Same as the buffered path: carry the transport reason so the loop does
        # not tell the model to fix JSON it never got to produce.
        yield json.dumps({
            "action": "error",
            "thought": "API Gateway Failure.",
            "gateway_error": f"{type(e).__name__}: {e}"[:300],
        })
