import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from backend.handoff.triggers import evaluate_escalation
from backend.handoff.executor import execute_handoff
from backend.session.state import RedisSessionManager

@pytest.mark.asyncio
async def test_escalation_triggers_at_third_fallback():
    """Verify that evaluate_escalation increments fallback tally and triggers at 3."""
    mock_redis = AsyncMock()
    # Mock incrby to return consecutive counts
    mock_redis.incrby = AsyncMock(side_effect=[1, 2, 3])
    
    redis_manager = RedisSessionManager(redis_client=mock_redis)
    session_id = str(uuid4())
    
    r1 = await evaluate_escalation(session_id, "hello", True, redis_manager)
    r2 = await evaluate_escalation(session_id, "world", True, redis_manager)
    r3 = await evaluate_escalation(session_id, "help", True, redis_manager)
    
    assert r1 is False
    assert r2 is False
    assert r3 is True
    
    assert mock_redis.incrby.call_count == 3

@pytest.mark.asyncio
async def test_escalation_keyword_trigger():
    """Verify that keyword trigger escalates immediately."""
    mock_redis = AsyncMock()
    redis_manager = RedisSessionManager(redis_client=mock_redis)
    session_id = str(uuid4())
    
    r = await evaluate_escalation(session_id, "please connect to human", False, redis_manager)
    assert r is True

@pytest.mark.asyncio
async def test_execute_handoff_silences_bot_and_enqueues():
    """Verify execute_handoff transactionally silences bot, flags session, and zadds to queue."""
    mock_redis = AsyncMock()
    mock_session_repo = AsyncMock()
    
    redis_manager = RedisSessionManager(redis_client=mock_redis)
    session_id = str(uuid4())
    
    await execute_handoff(session_id, "rag_fallback", mock_session_repo, redis_manager)
    
    # Verify AI silenced
    mock_redis.set.assert_called_once_with(f"session:{session_id}:ai_silenced", "true")
    # Verify DB marked as escalated
    mock_session_repo.mark_escalated.assert_awaited_once()
    # Verify enqueued in Redis sorted set
    mock_redis.zadd.assert_called_once()
