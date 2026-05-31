from abc import ABC, abstractmethod
from typing import AsyncGenerator

class AIProviderAdapter(ABC):
    @abstractmethod
    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Yields token chunks asynchronously to prevent blocking frame loops."""
        pass
