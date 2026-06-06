import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_calmiq_webhook_invalid_secret_fails():
    # Send request with invalid signature secret header
    response = client.post(
        "/api/v1/webhooks/calmiq",
        headers={"X-CalmIQ-Secret": "wrong_secret_key"},
        json={
            "session_id": "7168d3b2-b6bb-4aca-976e-4c24c4dee3ed",
            "customer_id": "023c0764-432a-4897-b1d0-4651f1c4029e",
            "message": "refund immediately",
            "history": "customer: refund",
            "escalate": True
        }
    )
    assert response.status_code == 401
    assert "Invalid webhook signature" in response.json()["detail"]

def test_calmiq_webhook_missing_secret_fails():
    # Send request without secret header
    response = client.post(
        "/api/v1/webhooks/calmiq",
        json={
            "session_id": "7168d3b2-b6bb-4aca-976e-4c24c4dee3ed",
            "customer_id": "023c0764-432a-4897-b1d0-4651f1c4029e",
            "message": "angry",
            "history": "",
            "escalate": True
        }
    )
    assert response.status_code == 401

def test_calmiq_webhook_stores_peak_score():
    from unittest.mock import AsyncMock
    from backend.config import CALMIQ_WEBHOOK_SECRET
    from backend.api.webhooks import get_session_repo
    from uuid import UUID
    
    mock_repo = AsyncMock()
    app.dependency_overrides[get_session_repo] = lambda: mock_repo
    
    try:
        response = client.post(
            "/api/v1/webhooks/calmiq",
            headers={"X-CalmIQ-Secret": CALMIQ_WEBHOOK_SECRET},
            json={
                "session_id": "7168d3b2-b6bb-4aca-976e-4c24c4dee3ed",
                "customer_id": "023c0764-432a-4897-b1d0-4651f1c4029e",
                "message": "terrible support",
                "history": "",
                "escalate": False,
                "frustration_score": 0.95
            }
        )
        assert response.status_code == 200
        mock_repo.update_peak_score.assert_called_once_with(
            UUID("7168d3b2-b6bb-4aca-976e-4c24c4dee3ed"),
            0.95
        )
    finally:
        app.dependency_overrides.clear()


