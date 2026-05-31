import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from backend.repositories.ticket import TicketRepository

@pytest.mark.asyncio
async def test_ticket_save_calls_commit():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    
    repo = TicketRepository(mock_db)
    
    session_id = uuid4()
    ticket = await repo.create_ticket(
        session_id=session_id,
        email="test@example.com",
        message="My issue details"
    )
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    assert ticket.email == "test@example.com"
    assert ticket.message == "My issue details"
    assert ticket.session_id == session_id
