from typing import Optional
import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, Header, status
from backend.repositories.session import SessionRepository
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
