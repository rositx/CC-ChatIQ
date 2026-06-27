from typing import Optional
import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, UUID4
from sqlalchemy import update, select, func
from backend.repositories.session import SessionRepository
from backend.repositories.message import MessageRepository
from backend.storage.schema import SessionModel
from backend.session.state import RedisSessionManager
from backend.storage.db import async_session_factory
from backend.utils.jwt import verify_jwt_token

router = APIRouter(prefix="/api/v1", tags=["queue"])

def get_agent_id(authorization: Optional[str] = Header(None)) -> uuid.UUID:
    """Dependency extracting agent sub claim UUID from Bearer Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    try:
        token = authorization.split(" ")[1]
        from backend.config import LOCAL_TESTING
        if LOCAL_TESTING and token == "sandbox-token":
            return uuid.UUID("00000000-0000-0000-0000-000000000000")
        payload = verify_jwt_token(token)
        return uuid.UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized token claims")

@router.get("/queue")
async def list_queue(agent_id: uuid.UUID = Depends(get_agent_id)):
    """Retrieve all active escalated queue session entries."""
    async with async_session_factory() as session:
        repo = SessionRepository(session)
        sessions = await repo.get_escalated_sessions()
        return [
            {
                "id": str(s.id),
                "trigger": s.escalation_trigger,
                "escalated_at": s.escalated_at.isoformat() if s.escalated_at else None
            }
            for s in sessions
        ]

@router.post("/queue/{session_id}/claim")
async def claim_session(session_id: str, agent_id: uuid.UUID = Depends(get_agent_id)):
    """Claim an escalated queue session, assigning it to the requesting agent."""
    s_uuid = uuid.UUID(session_id)
    async with async_session_factory() as session:
        repo = SessionRepository(session)
        await repo.claim_session(s_uuid, agent_id)
    
    redis = RedisSessionManager()
    await redis.redis.zrem("queue:escalated", session_id)
    
    try:
        from backend.ws.agent import agent_manager
        await agent_manager.broadcast({
            "type": "queue_update",
            "payload": {"session_id": session_id, "status": "claimed", "agent_id": str(agent_id)}
        })
    except Exception:
        pass
    return {"status": "claimed"}

@router.post("/sessions/{session_id}/resolve")
async def resolve_session(session_id: str, agent_id: uuid.UUID = Depends(get_agent_id)):
    """Marks a claimed session as resolved and cleans up enqueued Redis states."""
    s_uuid = uuid.UUID(session_id)
    async with async_session_factory() as session:
        repo = SessionRepository(session)
        db_sess = await repo.get_session(s_uuid, s_uuid)
        tenant_id = db_sess.tenant_id if db_sess else s_uuid
        await repo.close_session(s_uuid, tenant_id, "resolved")
    
    redis = RedisSessionManager()
    await redis.redis.zrem("queue:escalated", session_id)
    await redis.redis.delete(f"session:{session_id}:ai_silenced")
    
    try:
        from backend.tasks.summaries import generate_summary_task
        generate_summary_task.delay(session_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Failed to enqueue summary task: %s", e)

    try:
        from backend.ws.agent import agent_manager
        await agent_manager.broadcast({
            "type": "queue_update",
            "payload": {"session_id": session_id, "status": "resolved"}
        })
    except Exception:
        pass
    return {"status": "resolved"}

@router.post("/sessions/{session_id}/escalate")
async def manual_escalate(session_id: str, agent_id: uuid.UUID = Depends(get_agent_id)):
    """Manually redirect and escalate an ongoing support session back into the queue."""
    s_uuid = uuid.UUID(session_id)
    async with async_session_factory() as session:
        repo = SessionRepository(session)
        await repo.mark_escalated(s_uuid, "manual_agent")
    
    redis = RedisSessionManager()
    await redis.redis.zadd("queue:escalated", {session_id: time.time()})
    await redis.redis.set(f"session:{session_id}:ai_silenced", "true")
    
    try:
        from backend.ws.agent import agent_manager
        await agent_manager.broadcast({
            "type": "queue_update",
            "payload": {"session_id": session_id, "status": "escalated"}
        })
    except Exception:
        pass
    return {"status": "escalated"}

@router.get("/agents/online")
async def list_online_agents(agent_id: uuid.UUID = Depends(get_agent_id)):
    """List all online agents with their active chat counts."""
    redis = RedisSessionManager()
    online_agent_bytes = await redis.redis.hkeys("agents:online")
    online_agents = [uuid.UUID(uid.decode("utf-8")) for uid in online_agent_bytes]
    
    async with async_session_factory() as session:
        stmt = (
            select(SessionModel.agent_id, func.count(SessionModel.id))
            .where(SessionModel.status == "active")
            .where(SessionModel.agent_id.in_(online_agents))
            .group_by(SessionModel.agent_id)
        )
        result = await session.execute(stmt)
        counts = {row[0]: row[1] for row in result}
        
    return [
        {
            "agent_id": str(uid),
            "active_chats": counts.get(uid, 0)
        }
        for uid in online_agents
    ]

class TransferRequest(BaseModel):
    target_agent_id: UUID4

@router.post("/sessions/{session_id}/transfer")
async def transfer_session(
    session_id: str, 
    payload: TransferRequest, 
    agent_id: uuid.UUID = Depends(get_agent_id)
):
    """Transfer an active support session to a colleague agent."""
    s_uuid = uuid.UUID(session_id)
    target_uuid = payload.target_agent_id
    
    async with async_session_factory() as session:
        query = (
            update(SessionModel)
            .where(SessionModel.id == s_uuid)
            .values(agent_id=target_uuid, status="active")
        )
        await session.execute(query)
        
        transfer_text = "You have been transferred to a senior agent."
        msg_repo = MessageRepository(session)
        await msg_repo.save_message(s_uuid, "system", transfer_text)
        await session.commit()
        
    redis = RedisSessionManager()
    await redis.redis.zrem("queue:escalated", session_id)
    await redis.redis.set(f"session:{session_id}:ai_silenced", "true")
    
    try:
        from backend.ws.agent import agent_manager
        await agent_manager.broadcast({
            "type": "session_transferred",
            "payload": {
                "session_id": session_id,
                "from_agent_id": str(agent_id),
                "to_agent_id": str(target_uuid)
            }
        })
    except Exception:
        pass
        
    return {"status": "transferred"}
