import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_ingest_text_file_accepted():
    """Verify that uploading a text file parses contents and dispatches the Celery task."""
    with patch("backend.api.knowledge.ingest_document_task") as mock_task:
        response = client.post(
            "/api/v1/knowledge/ingest",
            data={"document_title": "Refund Policy"},
            files={"file": ("refunds.txt", b"This is the official refund policy. Standard refunds take 5 days.")}
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        
        # Verify the Celery task was dispatched with parsed string content
        mock_task.delay.assert_called_once_with(
            "00000000-0000-0000-0000-000000000000",
            "Refund Policy",
            None,
            "This is the official refund policy. Standard refunds take 5 days."
        )
