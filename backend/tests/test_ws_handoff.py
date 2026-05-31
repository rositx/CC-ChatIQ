import datetime
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.jwt import create_jwt_token

@pytest.fixture
def client():
    return TestClient(app)

def test_websocket_escalates_on_keyword(client):
    session_id = str(uuid4())
    token = create_jwt_token({"sub": session_id, "tenant_id": str(uuid4())}, expires_in=3600)
    
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    
    mock_msg_repo = MagicMock()
    mock_db_msg = MagicMock()
    mock_db_msg.id = uuid4()
    mock_db_msg.created_at = datetime.datetime.now(datetime.timezone.utc)
    mock_msg_repo.save_message = AsyncMock(return_value=mock_db_msg)

    mock_session_repo = MagicMock()
    mock_session_repo.mark_escalated = AsyncMock()

    mock_redis = AsyncMock()
    mock_redis.redis.get = AsyncMock(return_value=None)
    mock_redis.redis.incrby = AsyncMock(return_value=1)
    mock_redis.redis.zadd = AsyncMock()
    mock_redis.redis.zcard = AsyncMock(return_value=2)  # Simulate 2 escalated sessions

    with patch("backend.ws.chat.async_session_factory", mock_session_factory), \
         patch("backend.ws.chat.MessageRepository", return_value=mock_msg_repo), \
         patch("backend.ws.chat.SessionRepository", return_value=mock_session_repo), \
         patch("backend.ws.chat.RedisSessionManager", return_value=mock_redis):
        with client.websocket_connect(f"/ws/chat/{session_id}?token={token}") as websocket:
            # Trigger escalation with keyword
            websocket.send_text(json.dumps({
                "type": "message",
                "payload": {
                    "content": "I want to cancel my account please connect me to a manager"
                }
            }))
            # Receive echo
            res_echo = json.loads(websocket.receive_text())
            assert res_echo["type"] == "message"
            
            # Receive auto-response (escalated waiting message)
            res_esc = json.loads(websocket.receive_text())
            assert res_esc["type"] == "message"
            assert "wait" in res_esc["payload"]["content"] or "queue" in res_esc["payload"]["content"]
            assert "6" in res_esc["payload"]["content"]  # 2 * 3 = 6 minutes wait
