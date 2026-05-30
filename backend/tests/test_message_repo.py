import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from backend.repositories.message import MessageRepository

@pytest.mark.asyncio
async def test_message_repo_saves_and_commits():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    repo = MessageRepository(mock_db)
    
    session_id = uuid4()
    msg = await repo.save_message(session_id, "customer", "Help me!")
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    assert msg.content == "Help me!"

@pytest.mark.asyncio
async def test_message_repo_save_rollback_on_error():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit.side_effect = Exception("DB Error")
    
    repo = MessageRepository(mock_db)
    session_id = uuid4()
    
    with pytest.raises(Exception, match="DB Error"):
        await repo.save_message(session_id, "customer", "Help me!")
        
    mock_db.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_message_repo_get_history():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ["msg1", "msg2"]
    mock_db.execute.return_value = mock_result
    
    repo = MessageRepository(mock_db)
    session_id = uuid4()
    tenant_id = uuid4()
    
    history = await repo.get_history(session_id, tenant_id)
    
    mock_db.execute.assert_called_once()
    assert history == ["msg1", "msg2"]
