import pytest
from backend.utils.embedder import generate_embedding
from backend import config

@pytest.mark.asyncio
async def test_local_embedding_generation():
    """Verify that local fastembed produces 384-dimensional embeddings."""
    config.EMBEDDING_PROVIDER = "local"
    vector = await generate_embedding("  Hello   world!  ")
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(val, float) for val in vector)

@pytest.mark.asyncio
async def test_mock_embedding_generation():
    """Verify that mock embedding fallback produces EMBEDDING_DIMENSIONS."""
    config.EMBEDDING_PROVIDER = "mock"
    config.EMBEDDING_DIMENSIONS = 1536
    vector = await generate_embedding("Hello world")
    assert len(vector) == 1536
    assert all(val == 0.0 for val in vector)
