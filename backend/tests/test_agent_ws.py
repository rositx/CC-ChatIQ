import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from backend.main import app
from backend.utils.jwt import create_jwt_token

client = TestClient(app)

def test_agent_ws_unauthorized():
    # Attempt connecting without token query param
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/agent/some-agent") as ws:
            pass

def test_agent_ws_invalid_token():
    agent_id = str(uuid4())
    # Connect with invalid token query parameter
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/agent/{agent_id}?token=invalid-token") as ws:
            ws.receive_text()
    assert exc_info.value.code == 4001

def test_agent_ws_mismatched_agent_id():
    agent_id = str(uuid4())
    mismatched_agent_id = str(uuid4())
    token = create_jwt_token({"sub": mismatched_agent_id}, expires_in=3600)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws/agent/{agent_id}?token={token}") as ws:
            ws.receive_text()
    assert exc_info.value.code == 4001

def test_agent_ws_connect_and_ping():
    agent_id = str(uuid4())
    token = create_jwt_token({"sub": agent_id}, expires_in=3600)
    with client.websocket_connect(f"/ws/agent/{agent_id}?token={token}") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        response = json.loads(ws.receive_text())
        assert response.get("type") == "pong"
