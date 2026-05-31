import pytest
from backend.ai.mock import MockAdapter

@pytest.mark.asyncio
async def test_mock_adapter_streams_predictably():
    adapter = MockAdapter()
    tokens = []
    async for token in adapter.stream_response("Hey"):
        tokens.append(token)
    
    full_response = "".join(tokens)
    assert "Hello" in full_response
