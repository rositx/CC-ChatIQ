from typing import AsyncGenerator
from openai import AsyncOpenAI
from backend.ai.base import AIProviderAdapter
from backend.config import AI_MODEL_GROQ, AI_TEMPERATURE, AI_MAX_TOKENS, GROQ_API_KEY

class GroqAdapter(AIProviderAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY
        )

    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams generation chunks safely handling partial delta packets from Groq."""
        response = await self.client.chat.completions.create(
            model=AI_MODEL_GROQ,
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
