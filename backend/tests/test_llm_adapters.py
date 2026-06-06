import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from backend.ai.openai import OpenAIAdapter
from backend.ai.anthropic import AnthropicAdapter

@pytest.mark.asyncio
async def test_openai_adapter_streams_correctly():
    mock_response = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello "))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="world!"))])
    ]
    
    async def async_iter():
        for item in mock_response:
            yield item

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=async_iter())

    with patch("backend.ai.openai.AsyncOpenAI", return_value=mock_client):
        adapter = OpenAIAdapter()
        tokens = []
        async for token in adapter.stream_response("test"):
            tokens.append(token)
        assert "".join(tokens) == "Hello world!"

@pytest.mark.asyncio
async def test_anthropic_adapter_streams_correctly():
    async def text_stream_iter():
        yield "Hi "
        yield "there!"

    mock_stream = AsyncMock()
    mock_stream.text_stream = text_stream_iter()
    
    mock_client = MagicMock()
    # Mock the context manager returning mock_stream
    mock_client.messages.stream.return_value.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_client.messages.stream.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.ai.anthropic.AsyncAnthropic", return_value=mock_client):
        adapter = AnthropicAdapter()
        tokens = []
        async for token in adapter.stream_response("test"):
            tokens.append(token)
        assert "".join(tokens) == "Hi there!"
