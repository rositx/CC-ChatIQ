from typing import AsyncGenerator
from openai import AsyncOpenAI
from backend.ai.base import AIProviderAdapter
from backend.config import AI_MODEL_OPENAI, AI_TEMPERATURE, AI_MAX_TOKENS

class OpenAIAdapter(AIProviderAdapter):
    def __init__(self):
        import os
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock_key_for_testing"))

    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams generation chunks safely handling partial delta packets."""
        response = await self.client.chat.completions.create(
            model=AI_MODEL_OPENAI,
            messages=[{"role": "user", "content": prompt}],
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS,
            stream=True
        )
        async for chunk in response:
            if not chunk.choices:
                continue
            token = chunk.choices[0].delta.content
            if token:
                yield token
