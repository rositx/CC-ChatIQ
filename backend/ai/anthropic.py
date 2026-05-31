from typing import AsyncGenerator
from anthropic import AsyncAnthropic
from backend.ai.base import AIProviderAdapter
from backend.config import AI_MODEL_ANTHROPIC, AI_TEMPERATURE, AI_MAX_TOKENS

class AnthropicAdapter(AIProviderAdapter):
    def __init__(self):
        import os
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", "mock_key_for_testing"))

    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams generation chunks safely from Anthropic Messages API."""
        async with self.client.messages.stream(
            model=AI_MODEL_ANTHROPIC,
            max_tokens=AI_MAX_TOKENS,
            temperature=AI_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text
