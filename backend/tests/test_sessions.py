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
