from abc import ABC, abstractmethod
from typing import AsyncGenerator

class AIProviderAdapter(ABC):
    @abstractmethod
    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Yields token chunks asynchronously to prevent blocking frame loops."""
        pass

_PROVIDER_REGISTRY = {
    "openai": "backend.ai.openai.OpenAIAdapter",
    "anthropic": "backend.ai.anthropic.AnthropicAdapter",
    "azure": "backend.ai.azure.AzureOpenAIAdapter",
    "groq": "backend.ai.groq.GroqAdapter",
    "mock": "backend.ai.mock.MockAdapter"
}

def get_active_ai_provider() -> AIProviderAdapter:
    """
    Factory resolving and injecting the active AI adapter at application startup
    without conditional code branch modification.
    """
    from backend.config import AI_PROVIDER
    import importlib

    target_path = _PROVIDER_REGISTRY.get(AI_PROVIDER.lower())
    if not target_path:
        raise ValueError(f"Unsupported provider specified in AI_PROVIDER: {AI_PROVIDER}")

    # Dynamically extract module properties to respect abstraction isolation guidelines
    module_path, class_name = target_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    adapter_class = getattr(module, class_name)
    
    return adapter_class()
