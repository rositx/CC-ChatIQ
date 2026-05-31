from typing import AsyncGenerator
from openai import AsyncAzureOpenAI
from backend.ai.base import AIProviderAdapter
from backend.config import (
    AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, 
    AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION,
    AI_TEMPERATURE, AI_MAX_TOKENS
)

class AzureOpenAIAdapter(AIProviderAdapter):
    def __init__(self):
        import os
        self.client = AsyncAzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT or "https://mock.azure.com",
            api_key=AZURE_OPENAI_API_KEY or "mock_key_for_testing",
            api_version=AZURE_OPENAI_API_VERSION
        )

    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams generation chunks safely from Azure OpenAI Endpoint."""
        response = await self.client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
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
