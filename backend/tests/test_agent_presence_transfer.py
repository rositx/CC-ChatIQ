import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_get_online_agents_unauthorized():
    response = client.get("/api/v1/agents/online")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_transfer_session_unauthorized():
    session_id = str(uuid.uuid4())
    response = client.post(
        f"/api/v1/sessions/{session_id}/transfer",
        json={"target_agent_id": str(uuid.uuid4())}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_online_agents_authorized_sandbox():
    headers = {"Authorization": "Bearer sandbox-token"}
    
    mock_redis = AsyncMock()
    mock_redis.redis.hkeys = AsyncMock(return_value=[b"00000000-0000-0000-0000-000000000000"])
    
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    
    # Mock execute return value for active chat counts query
    mock_result = MagicMock()
    mock_result.__iter__.return_value = [(uuid.UUID("00000000-0000-0000-0000-000000000000"), 2)]
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("backend.api.queue.RedisSessionManager", return_value=mock_redis), \
         patch("backend.api.queue.async_session_factory", mock_session_factory):
        response = client.get("/api/v1/agents/online", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["active_chats"] == 2
        assert data[0]["agent_id"] == "00000000-0000-0000-0000-000000000000"

@pytest.mark.asyncio
async def test_transfer_session_success():
    headers = {"Authorization": "Bearer sandbox-token"}
    session_id = str(uuid.uuid4())
    target_agent_id = str(uuid.uuid4())
    
    mock_redis = AsyncMock()
    mock_redis.redis.zrem = AsyncMock()
    mock_redis.redis.set = AsyncMock()
    
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    
    mock_session.execute = AsyncMock()
    
    # Mock MessageRepository save_message
    mock_msg_repo = MagicMock()
    mock_msg_repo.save_message = AsyncMock()
    
    with patch("backend.api.queue.RedisSessionManager", return_value=mock_redis), \
         patch("backend.api.queue.async_session_factory", mock_session_factory), \
         patch("backend.api.queue.MessageRepository", return_value=mock_msg_repo):
        response = client.post(
            f"/api/v1/sessions/{session_id}/transfer",
            headers=headers,
            json={"target_agent_id": target_agent_id}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "transferred"}
        mock_msg_repo.save_message.assert_awaited_once()
