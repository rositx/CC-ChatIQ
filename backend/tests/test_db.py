import pytest
from backend.storage.schema import SessionModel, MessageModel

def test_session_model_attributes():
    session = SessionModel()
    assert session.status == "active"
    assert session.escalation_trigger is None
    assert session.peak_score is None
    assert session.resolution_type is None
    assert session.summary is None
    assert session.claimed_at is None

def test_message_model_attributes():
    message = MessageModel()
    assert message.role is None
    assert message.content is None
    assert message.rag_sources is None
