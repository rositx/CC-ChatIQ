import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.jwt import create_jwt_token

client = TestClient(app)

def test_queue_endpoints_require_auth():
    # 1. GET /api/v1/queue
    res = client.get("/api/v1/queue")
    assert res.status_code == 401

    # 2. POST /api/v1/queue/some-id/claim
    res = client.post(f"/api/v1/queue/{uuid4()}/claim")
    assert res.status_code == 401

    # 3. POST /api/v1/sessions/some-id/resolve
    res = client.post(f"/api/v1/sessions/{uuid4()}/resolve")
    assert res.status_code == 401

    # 4. POST /api/v1/sessions/some-id/escalate
    res = client.post(f"/api/v1/sessions/{uuid4()}/escalate")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_queue_actions_success():
    agent_id = str(uuid4())
    session_id = str(uuid4())
    token = create_jwt_token({"sub": agent_id}, expires_in=3600)
    headers = {"Authorization": f"Bearer {token}"}

    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    mock_repo = MagicMock()
    mock_repo.get_escalated_sessions = AsyncMock(return_value=[])
    mock_repo.claim_session = AsyncMock()
    mock_repo.close_session = AsyncMock()
    mock_repo.mark_escalated = AsyncMock()
    mock_repo.get_session = AsyncMock(return_value=None)

    mock_redis = AsyncMock()
    mock_redis.redis.zrem = AsyncMock()
    mock_redis.redis.zadd = AsyncMock()
    mock_redis.redis.delete = AsyncMock()
    mock_redis.redis.set = AsyncMock()

    with patch("backend.api.queue.async_session_factory", mock_session_factory), \
         patch("backend.api.queue.SessionRepository", return_value=mock_repo), \
         patch("backend.api.queue.RedisSessionManager", return_value=mock_redis):
        
        # Test list queue
        res_list = client.get("/api/v1/queue", headers=headers)
        assert res_list.status_code == 200
        assert res_list.json() == []

        # Test claim session
        res_claim = client.post(f"/api/v1/queue/{session_id}/claim", headers=headers)
        assert res_claim.status_code == 200
        assert res_claim.json() == {"status": "claimed"}
        mock_repo.claim_session.assert_awaited_once()

        # Test resolve session
        res_resolve = client.post(f"/api/v1/sessions/{session_id}/resolve", headers=headers)
        assert res_resolve.status_code == 200
        assert res_resolve.json() == {"status": "resolved"}
        mock_repo.close_session.assert_awaited_once()

        # Test escalate session
        res_esc = client.post(f"/api/v1/sessions/{session_id}/escalate", headers=headers)
        assert res_esc.status_code == 200
        assert res_esc.json() == {"status": "escalated"}
        mock_repo.mark_escalated.assert_awaited_once()

def test_get_analytics_summary():
    headers = {"Authorization": "Bearer sandbox-token"}
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    mock_repo = MagicMock()
    mock_repo.get_analytics_data = AsyncMock(return_value={
        "total_sessions": 5,
        "escalations_by_trigger": {"calmiq": 1, "user_request": 0, "keyword_trigger": 0, "manual_transfer": 0},
        "average_wait_time_seconds": 10.0,
        "rag_fallback_count": 0
    })

    with patch("backend.api.analytics.async_session_factory", mock_session_factory), \
         patch("backend.api.analytics.SessionRepository", return_value=mock_repo):
        res = client.get("/api/v1/analytics/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_sessions"] == 5
        assert data["average_wait_time_seconds"] == 10.0
