import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.jwt import create_jwt_token

client = TestClient(app)

def test_register_push_token_unauthorized():
    response = client.post("/api/v1/sessions/push-token", json={"push_token": "token"})
    assert response.status_code == 401

def test_register_push_token_success():
    session_id = str(uuid.uuid4())
    customer_id = uuid.uuid4()
    token = create_jwt_token({"sub": session_id, "tenant_id": str(uuid.uuid4())}, expires_in=3600)
    
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    
    # 1. Mock Session lookup
    mock_sess_record = MagicMock()
    mock_sess_record.customer_id = customer_id
    mock_sess_result = MagicMock()
    mock_sess_result.scalar_one_or_none.return_value = mock_sess_record
    
    # 2. Mock Token lookup (return None to trigger creation)
    mock_token_result = MagicMock()
    mock_token_result.scalar_one_or_none.return_value = None
    
    mock_session.execute = AsyncMock(side_effect=[mock_sess_result, mock_token_result])
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    headers = {"Authorization": f"Bearer {token}"}
    with patch("backend.storage.db.async_session_factory", mock_session_factory):
        response = client.post(
            "/api/v1/sessions/push-token",
            headers=headers,
            json={"push_token": "ExponentPushToken[123456]", "platform": "expo"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "registered"}
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
