import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from backend.repositories.session import SessionRepository

@pytest.mark.asyncio
async def test_create_session_calls_commit():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()  # Synchronous DB operation
    
    repo = SessionRepository(mock_db)
    
    cust_id = uuid4()
    tenant_id = uuid4()
    
    session = await repo.create_session(cust_id, tenant_id)
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(session)
    assert session.customer_id == cust_id
    assert session.tenant_id == tenant_id
    assert session.status == "active"

@pytest.mark.asyncio
async def test_create_session_rollback_on_error():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit.side_effect = Exception("DB Error")
    
    repo = SessionRepository(mock_db)
    
    cust_id = uuid4()
    tenant_id = uuid4()
    
    with pytest.raises(Exception, match="DB Error"):
        await repo.create_session(cust_id, tenant_id)
        
    mock_db.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_session_filters_by_tenant():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "mock_session"
    mock_db.execute.return_value = mock_result
    
    repo = SessionRepository(mock_db)
    session_id = uuid4()
    tenant_id = uuid4()
    
    result = await repo.get_session(session_id, tenant_id)
    
    mock_db.execute.assert_called_once()
    assert result == "mock_session"

@pytest.mark.asyncio
async def test_close_session_updates_status():
    mock_db = AsyncMock()
    repo = SessionRepository(mock_db)
    
    session_id = uuid4()
    tenant_id = uuid4()
    resolution_type = "resolved_by_agent"
    
    await repo.close_session(session_id, tenant_id, resolution_type)
    
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_close_session_rollback_on_error():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("Update error")
    repo = SessionRepository(mock_db)
    
    session_id = uuid4()
    tenant_id = uuid4()
    
    with pytest.raises(Exception, match="Update error"):
        await repo.close_session(session_id, tenant_id, "resolved_by_agent")
        
    mock_db.rollback.assert_awaited_once()

@pytest.mark.asyncio
async def test_session_repo_update_peak_score():
    mock_db = AsyncMock()
    repo = SessionRepository(mock_db)
    session_id = uuid4()
    score = 0.85
    await repo.update_peak_score(session_id, score)
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_session_repo_claim_updates_claimed_at():
    mock_db = AsyncMock()
    repo = SessionRepository(mock_db)
    session_id = uuid4()
    agent_id = uuid4()
    await repo.claim_session(session_id, agent_id)
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_session_repo_update_summary():
    mock_db = AsyncMock()
    repo = SessionRepository(mock_db)
    session_id = uuid4()
    summary = "A test summary."
    await repo.update_summary(session_id, summary)
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_analytics_data():
    mock_db = AsyncMock()
    mock_total_res = MagicMock()
    mock_total_res.scalar.return_value = 10
    
    mock_wait_res = MagicMock()
    mock_wait_res.scalar.return_value = 120.0
    
    mock_trigger_res = MagicMock()
    mock_trigger_res.all.return_value = [("keyword_trigger", 5), ("rag_fallback", 2)]
    
    mock_db.execute.side_effect = [mock_total_res, mock_wait_res, mock_trigger_res]
    
    repo = SessionRepository(mock_db)
    tenant_id = uuid4()
    result = await repo.get_analytics_data(tenant_id)
    
    assert result["total_sessions"] == 10
    assert result["average_wait_time_seconds"] == 120.0
    assert result["escalations_by_trigger"]["keyword_trigger"] == 5
    assert result["rag_fallback_count"] == 2

