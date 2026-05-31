import asyncio
from typing import AsyncGenerator
from backend.ai.base import AIProviderAdapter

class MockAdapter(AIProviderAdapter):
    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Yields deterministic responses chunk by chunk to simulate active LLM networks."""
        response_text = f"Hello! This is a mock support response to your message: '{prompt}'. How can I help you today?"
        words = response_text.split(" ")
        for word in words:
            yield word + " "
            await asyncio.sleep(0.02)  # Yield delay mimics socket streaming
