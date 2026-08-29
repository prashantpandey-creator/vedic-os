import os

with open("core/llm_gateway.py", "r") as f:
    content = f.read()

new_content = content + """

async def generate_response_stream(model_name: str, messages: list, temperature: float = 0.1):
    from litellm import acompletion
    try:
        response = await acompletion(
            model=model_name,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[GATEWAY STREAM ERROR] {e}")
        yield '{"action": "error", "thought": "API Gateway Failure."}'
"""

with open("core/llm_gateway.py", "w") as f:
    f.write(new_content)
