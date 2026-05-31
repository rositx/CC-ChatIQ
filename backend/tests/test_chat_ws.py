import datetime
import json
import pytest
import uuid
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from backend.main import app
from backend.utils.jwt import create_jwt_token

@pytest.fixture
def client():
    return TestClient(app)

def test_websocket_no_token_fails(client):
    # Missing token query parameter during handshake
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/chat/some-session-id") as websocket:
            pass

def test_websocket_invalid_token_fails(client):
    # Invalid token signature/segments should close connection with 4001 code
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect("/ws/chat/some-session-id?token=invalid-token") as websocket:
            websocket.receive_text()
    assert exc_info.value.code == 4001

def test_websocket_session_mismatch_fails(client):
    # Correct token signature, but for a different session_id
    session_id = str(uuid4())
    mismatched_session_id = str(uuid4())
    token = create_jwt_token({"sub": mismatched_session_id, "tenant_id": str(uuid4())}, expires_in=3600)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/chat/{session_id}?token={token}") as websocket:
            websocket.receive_text()
    assert exc_info.value.code == 4001

def test_websocket_connect_success(client):
    # Valid JWT token and correct session_id connection
    session_id = str(uuid4())
    token = create_jwt_token({"sub": session_id, "tenant_id": str(uuid4())}, expires_in=3600)
    with client.websocket_connect(f"/ws/chat/{session_id}?token={token}") as websocket:
        # Connection accepts without raising any exceptions
        pass

def test_websocket_ping_pong(client):
    # Connect successfully and exchange ping-pong frame
    session_id = str(uuid4())
    token = create_jwt_token({"sub": session_id, "tenant_id": str(uuid4())}, expires_in=3600)
    with client.websocket_connect(f"/ws/chat/{session_id}?token={token}") as websocket:
        websocket.send_text(json.dumps({"type": "ping"}))
        response = websocket.receive_text()
        data = json.loads(response)
        assert data.get("type") == "pong"

def test_websocket_message_persisted_and_echoed(client):
    # Connect successfully, send message, mock-persist and verify echo back
    session_id = str(uuid4())
    session_uuid = uuid.UUID(session_id)
    token = create_jwt_token({"sub": session_id, "tenant_id": str(uuid4())}, expires_in=3600)
    
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    
    mock_repo = MagicMock()
    mock_db_msg = MagicMock()
    msg_id = uuid4()
    msg_created_at = datetime.datetime.now(datetime.timezone.utc)
    mock_db_msg.id = msg_id
    mock_db_msg.created_at = msg_created_at
    mock_repo.save_message = AsyncMock(return_value=mock_db_msg)
    
    with patch("backend.ws.chat.async_session_factory", mock_session_factory), \
         patch("backend.ws.chat.MessageRepository", return_value=mock_repo):
        with client.websocket_connect(f"/ws/chat/{session_id}?token={token}") as websocket:
            websocket.send_text(json.dumps({
                "type": "message",
                "payload": {
                    "content": "Hello, world!"
                }
            }))
            response = websocket.receive_text()
            data = json.loads(response)
            
            assert data["type"] == "message"
            assert data["payload"]["id"] == str(msg_id)
            assert data["payload"]["session_id"] == session_id
            assert data["payload"]["role"] == "customer"
            assert data["payload"]["content"] == "Hello, world!"
            assert data["payload"]["created_at"] == msg_created_at.isoformat()
            
            # Verify save_message was called with the converted session UUID and content
            mock_repo.save_message.assert_called_once_with(session_uuid, "customer", "Hello, world!")
