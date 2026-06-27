import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import AsyncMock
from backend.main import app
from backend.api.sessions import get_session_repository

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def clean_dependencies():
    yield
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_initialize_session_endpoint(client):
    mock_repo = AsyncMock()
    
    # Mocking create_session response object
    class MockSession:
        def __init__(self):
            self.id = uuid4()
            self.status = "active"
    
    mock_repo.create_session.return_value = MockSession()
    
    # Override FastAPI repository dependency mapping to use mock repository
    app.dependency_overrides[get_session_repository] = lambda: mock_repo
    
    payload = {
        "customer_id": str(uuid4()),
        "tenant_id": str(uuid4())
    }
    
    response = client.post("/api/v1/sessions", json=payload)
    
    assert response.status_code == 201
    assert "session_id" in response.json()
    assert response.json()["status"] == "active"

def test_get_session_history_agent_sandbox_token(client):
    from backend.storage.schema import SessionModel, MessageModel
    from uuid import uuid4
    import datetime
    from unittest.mock import patch, MagicMock, AsyncMock
    
    session_id = uuid4()
    tenant_id = uuid4()
    
    mock_session_obj = SessionModel(
        id=session_id,
        customer_id=uuid4(),
        tenant_id=tenant_id,
        status="escalated"
    )
    
    mock_msg = MessageModel(
        id=uuid4(),
        session_id=session_id,
        role="customer",
        content="help me",
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    mock_db = AsyncMock()
    mock_res_session = MagicMock()
    mock_res_session.scalar_one_or_none.return_value = mock_session_obj
    
    mock_res_messages = MagicMock()
    mock_res_messages.scalars.return_value.all.return_value = [mock_msg]
    
    mock_db.execute.side_effect = [mock_res_session, mock_res_messages]
    
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_db
    
    with patch("backend.storage.db.async_session_factory", mock_session_factory):
        response = client.get(
            f"/api/v1/sessions/{session_id}",
            headers={"Authorization": "Bearer sandbox-token"}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "help me"
    assert data[0]["role"] == "customer"

def test_get_session_metadata_agent_sandbox_token(client):
    from backend.storage.schema import SessionModel
    from uuid import uuid4
    from unittest.mock import patch, MagicMock, AsyncMock
    
    session_id = uuid4()
    tenant_id = uuid4()
    
    mock_session_obj = SessionModel(
        id=session_id,
        customer_id=uuid4(),
        tenant_id=tenant_id,
        status="escalated",
        escalation_trigger="calmiq_webhook",
        peak_score=0.92
    )
    
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_session_obj
    mock_db.execute.return_value = mock_res
    
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_db
    
    with patch("backend.storage.db.async_session_factory", mock_session_factory):
        response = client.get(
            f"/api/v1/sessions/{session_id}/metadata",
            headers={"Authorization": "Bearer sandbox-token"}
        )

        
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(session_id)
    assert data["status"] == "escalated"
    assert data["escalation_trigger"] == "calmiq_webhook"
    assert data["peak_score"] == 0.92

@pytest.mark.asyncio
async def test_session_summary_generation_task():
    from unittest.mock import patch, AsyncMock, MagicMock
    from backend.tasks.summaries import async_generate_summary
    
    mock_db = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_db
    
    mock_msg = MagicMock()
    mock_msg.role = "customer"
    mock_msg.content = "I need refund help"
    
    mock_msg_res = MagicMock()
    mock_msg_res.scalars.return_value.all.return_value = [mock_msg]
    mock_db.execute.return_value = mock_msg_res
    
    async def mock_send_message(*args, **kwargs):
        yield "Refund "
        yield "denied."
        
    mock_ai = MagicMock()
    mock_ai.send_message = mock_send_message
    
    with patch("backend.tasks.summaries.async_session_factory", mock_session_factory), \
         patch("backend.tasks.summaries.MockAdapter", return_value=mock_ai):
         
        await async_generate_summary("00000000-0000-0000-0000-000000000000")
        
        assert mock_db.execute.call_count >= 2
        mock_db.commit.assert_awaited()

def test_reset_sandbox_api(client):
    from unittest.mock import patch, MagicMock, AsyncMock
    mock_db = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_db
    
    with patch("backend.api.sessions.async_session_factory", mock_session_factory):
        response = client.post("/api/v1/sessions/reset", headers={"Authorization": "Bearer sandbox-token"})
        
    assert response.status_code == 200
    assert response.json() == {"status": "reset"}
    mock_db.execute.assert_called()
    mock_db.commit.assert_awaited()

