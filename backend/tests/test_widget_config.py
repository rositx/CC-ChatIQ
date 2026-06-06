import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_widget_config_invalid_key():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    with patch("backend.api.widget.async_session_factory", mock_session_factory):
        response = client.get("/api/v1/widget/config?api_key=invalid-key")
        assert response.status_code == 403

def test_get_widget_config_sandbox_key():
    from uuid import UUID
    mock_session = AsyncMock()
    mock_record = MagicMock()
    mock_record.tenant_id = UUID("00000000-0000-0000-0000-000000000000")
    mock_record.api_key = "sandbox-api-key"
    mock_record.domain_whitelist = None
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_record
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    with patch("backend.api.widget.async_session_factory", mock_session_factory):
        response = client.get("/api/v1/widget/config?api_key=sandbox-api-key")
        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == "00000000-0000-0000-0000-000000000000"
        assert data["primary_color"] == "#4F46E5"
