import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from backend.repositories.session import SessionRepository

@pytest.mark.asyncio
async def test_claim_session_updates_db():
    mock_db = AsyncMock()
    repo = SessionRepository(mock_db)
    session_id = uuid4()
    agent_id = uuid4()
    await repo.claim_session(session_id, agent_id)
    # Assert database query execution and commit
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_escalated_sessions_queries_db():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result
    repo = SessionRepository(mock_db)
    sessions = await repo.get_escalated_sessions()
    assert sessions == []
    mock_db.execute.assert_called_once()
