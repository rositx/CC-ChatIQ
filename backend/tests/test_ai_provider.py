import pytest
from unittest.mock import patch
from backend.ai.base import get_active_ai_provider
from backend.ai.mock import MockAdapter
from backend import config

def test_factory_resolves_mock_provider():
    """Verify that MockAdapter is successfully returned by factory."""
    with patch("backend.config.AI_PROVIDER", "mock"):
        provider = get_active_ai_provider()
        assert isinstance(provider, MockAdapter)

def test_factory_resolves_openai_provider():
    """Verify that OpenAIAdapter class is imported and loaded by factory."""
    with patch("backend.config.AI_PROVIDER", "openai"):
        provider = get_active_ai_provider()
        from backend.ai.openai import OpenAIAdapter
        assert isinstance(provider, OpenAIAdapter)

def test_factory_resolves_anthropic_provider():
    """Verify that AnthropicAdapter class is imported and loaded by factory."""
    with patch("backend.config.AI_PROVIDER", "anthropic"):
        provider = get_active_ai_provider()
        from backend.ai.anthropic import AnthropicAdapter
        assert isinstance(provider, AnthropicAdapter)

def test_factory_resolves_groq_provider():
    """Verify that GroqAdapter class is imported and loaded by factory."""
    with patch("backend.config.AI_PROVIDER", "groq"):
        provider = get_active_ai_provider()
        from backend.ai.groq import GroqAdapter
        assert isinstance(provider, GroqAdapter)

def test_factory_raises_value_error_for_invalid_provider():
    """Verify that invalid provider names raise ValueError."""
    with patch("backend.config.AI_PROVIDER", "non_existent_provider"):
        with pytest.raises(ValueError, match="Unsupported provider specified in AI_PROVIDER"):
            get_active_ai_provider()
