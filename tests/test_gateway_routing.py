#!/usr/bin/env python3
"""
Every model string this repo can hand the gateway must reach a provider litellm
recognises.

This test exists because two separate bugs of the same shape shipped:

  1. Every caller passed a bare Ollama tag ("qwen3:4b-instruct-2507-q4_K_M").
     litellm answers "LLM Provider NOT provided", generate_response swallowed it
     into {"action": "error"}, and the agent loop burned all 20 steps on
     "Malformed JSON. Retrying..." without ever reaching a model.

  2. After that was fixed, the escalation path still hardcoded
     "claude/claude-3-5-sonnet". "claude" is NOT a litellm provider — it is
     "anthropic" — so escalation stayed dead.

Both hid the same way: the failure looked like a bad model response rather than a
routing error, and nobody ran the loop end to end. Unit-testing the tools
individually could not catch either, because the tools are downstream of the
gateway.

    python3 tests/test_gateway_routing.py

Needs Ollama running for the live check; the routing checks are offline.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from litellm import completion  # noqa: E402

import config  # noqa: E402
from core.llm_gateway import KNOWN_PROVIDERS, generate_response, normalize_model  # noqa: E402

NOT_A_PROVIDER = "LLM Provider NOT provided"
failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
    if not ok:
        failures.append(name)


def litellm_accepts_prefix(prefix):
    """True if litellm recognises `prefix` as a provider. A missing API key or an
    unknown model is fine — that means the prefix parsed. Only 'LLM Provider NOT
    provided' means the prefix itself is bogus."""
    try:
        completion(model=f"{prefix}/probe-model",
                   messages=[{"role": "user", "content": "x"}], max_tokens=1)
        return True
    except Exception as e:
        return NOT_A_PROVIDER not in str(e)


print("--- 1. every entry in KNOWN_PROVIDERS is a real litellm provider ---")
bogus = [p for p in sorted(KNOWN_PROVIDERS) if not litellm_accepts_prefix(p)]
check("KNOWN_PROVIDERS has no bogus entries", not bogus, f"bogus={bogus}" if bogus else "")

print("\n--- 2. every model string in config routes somewhere real ---")
for attr in ["FAST_MODEL", "HEAVY_MODEL", "INGEST_MODEL", "EDITOR_MODEL",
             "EMBED_MODEL", "VISION_MODEL", "ESCALATION_MODEL"]:
    tag = getattr(config, attr, None)
    if tag is None:
        continue
    routed = normalize_model(tag)
    prefix = routed.split("/", 1)[0]
    check(f"{attr} routes to a real provider", litellm_accepts_prefix(prefix),
          f"{tag!r} -> {routed!r}")

print("\n--- 3. the escalation string specifically ---")
esc = normalize_model(config.ESCALATION_MODEL)
check("ESCALATION_MODEL is not the dead 'claude/' prefix", not esc.startswith("claude/"), esc)
check("ESCALATION_MODEL prefix is real", litellm_accepts_prefix(esc.split("/", 1)[0]), esc)
check("a legacy 'claude/...' string is remapped, not sent to Ollama",
      normalize_model("claude/claude-3-5-sonnet").startswith("anthropic/"),
      normalize_model("claude/claude-3-5-sonnet"))

print("\n--- 4. the slash trap: an Ollama tag containing a slash ---")
tricky = "mannix/llama3.1-8b-abliterated:latest"
check("slash-containing Ollama tag is NOT mistaken for a provider",
      normalize_model(tricky) == f"ollama/{tricky}", normalize_model(tricky))

print("\n--- 5. LIVE: the gateway actually returns text, not a swallowed error ---")
try:
    out = generate_response(config.FAST_MODEL,
                            [{"role": "user", "content": "Reply with the single word: OK"}])
    check("FAST_MODEL reaches a model through the real gateway",
          "API Gateway Failure" not in out, repr(out.strip()[:40]))
except Exception as e:
    check("FAST_MODEL reaches a model through the real gateway", False, str(e)[:60])

print("\n" + "=" * 60)
if failures:
    print(f"FAILED: {failures}")
    sys.exit(1)
print("All gateway routing checks passed.")
