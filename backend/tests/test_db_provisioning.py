import pytest
from backend.storage.schema import KnowledgeChunkModel

def test_knowledge_chunk_model_attributes():
    """Verify that KnowledgeChunkModel attributes are mapped correctly."""
    chunk = KnowledgeChunkModel()
    assert chunk.document_title is None
    assert chunk.source_url is None
    assert chunk.content is None
    assert chunk.chunk_index is None
