import json
import pytest
from unittest.mock import AsyncMock
from backend.session.state import RedisSessionManager
from backend.config import SESSION_TTL_SECONDS

@pytest.mark.asyncio
async def test_session_manager_crud():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"status": "active", "ai_silenced": false}'
    
    manager = RedisSessionManager(mock_redis)
    await manager.set_session_state("session_123", {"status": "active", "ai_silenced": False})
    
    mock_redis.set.assert_called_once_with(
        "session:session_123",
        '{"status": "active", "ai_silenced": false}',
        ex=SESSION_TTL_SECONDS
    )
    
    state = await manager.get_session_state("session_123")
    assert state["status"] == "active"
    mock_redis.get.assert_called_once_with("session:session_123")

@pytest.mark.asyncio
async def test_session_manager_non_existent():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    manager = RedisSessionManager(mock_redis)
    state = await manager.get_session_state("non_existent_session")
    
    assert state is None
    mock_redis.get.assert_called_once_with("session:non_existent_session")

@pytest.mark.asyncio
async def test_session_manager_malformed_json():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"status": "active", "invalid_json'
    
    manager = RedisSessionManager(mock_redis)
    with pytest.raises(json.JSONDecodeError):
        await manager.get_session_state("session_malformed")
    
    mock_redis.get.assert_called_once_with("session:session_malformed")

