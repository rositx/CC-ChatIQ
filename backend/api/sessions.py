import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from backend.repositories.base import BaseSessionRepository
from backend.session.schema import SessionCreateRequest
from backend.utils.jwt import verify_jwt_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

async def get_session_repository() -> BaseSessionRepository:
    from backend.storage.db import async_session_factory
    from backend.repositories.session import SessionRepository
    async with async_session_factory() as session:
        yield SessionRepository(session)

@router.post("", status_code=status.HTTP_201_CREATED)
async def initialize_session(
    payload: SessionCreateRequest,
    repo: BaseSessionRepository = Depends(get_session_repository)
):
    try:
        session = await repo.create_session(
            customer_id=payload.customer_id,
            tenant_id=payload.tenant_id
        )
        return {"session_id": str(session.id), "status": session.status}
    except Exception as e:
        logger.exception("Session initialization failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session initialization failed due to an internal server error"
        )

@router.get("/{session_id}")
async def get_session_history(
    session_id: str,
    authorization: Optional[str] = Header(None)
):
    """Retrieve historical messages for a session to restore conversation state."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    
    s_uuid = uuid.UUID(session_id)
    is_agent = False
    tenant_id = None
    
    from backend.config import LOCAL_TESTING
    if LOCAL_TESTING and token == "sandbox-token":
        is_agent = True
    else:
        try:
            claims = verify_jwt_token(token)
            if claims.get("sub") == session_id:
                tenant_id = uuid.UUID(claims.get("tenant_id"))
            else:
                is_agent = True
                if "tenant_id" in claims:
                    tenant_id = uuid.UUID(claims.get("tenant_id"))
        except Exception:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from backend.repositories.message import MessageRepository
    from backend.storage.db import async_session_factory
    from backend.storage.schema import SessionModel
    from sqlalchemy import select

    async with async_session_factory() as session:
        if is_agent:
            query = select(SessionModel).where(SessionModel.id == s_uuid)
            res = await session.execute(query)
            db_sess = res.scalar_one_or_none()
            if not db_sess:
                raise HTTPException(status_code=404, detail="Session not found")
            
            if tenant_id and db_sess.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Tenant mismatch")
            
            tenant_id = db_sess.tenant_id

        messages = await MessageRepository(session).get_history(s_uuid, tenant_id, limit=50)
        return [
            {
                "id": str(m.id), "session_id": str(m.session_id),
                "role": m.role, "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]

@router.get("/{session_id}/metadata")
async def get_session_metadata(
    session_id: str,
    authorization: Optional[str] = Header(None)
):
    """Retrieve session metadata (such as peak frustration score) for the agent dashboard."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    
    s_uuid = uuid.UUID(session_id)
    is_agent = False
    tenant_id = None
    
    from backend.config import LOCAL_TESTING
    if LOCAL_TESTING and token == "sandbox-token":
        is_agent = True
    else:
        try:
            claims = verify_jwt_token(token)
            if claims.get("sub") == session_id:
                tenant_id = uuid.UUID(claims.get("tenant_id"))
            else:
                is_agent = True
                if "tenant_id" in claims:
                    tenant_id = uuid.UUID(claims.get("tenant_id"))
        except Exception:
            raise HTTPException(status_code=401, detail="Unauthorized")

    from backend.storage.db import async_session_factory
    from backend.storage.schema import SessionModel
    from sqlalchemy import select

    async with async_session_factory() as session:
        query = select(SessionModel).where(SessionModel.id == s_uuid)
        res = await session.execute(query)
        db_sess = res.scalar_one_or_none()
        if not db_sess:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not is_agent:
            if db_sess.id != s_uuid or db_sess.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Forbidden")
        else:
            if tenant_id and db_sess.tenant_id != tenant_id:
                raise HTTPException(status_code=403, detail="Tenant mismatch")
        
        return {
            "id": str(db_sess.id),
            "customer_id": str(db_sess.customer_id),
            "agent_id": str(db_sess.agent_id) if db_sess.agent_id else None,
            "tenant_id": str(db_sess.tenant_id),
            "status": db_sess.status,
            "escalation_trigger": db_sess.escalation_trigger,
            "peak_score": db_sess.peak_score,
            "started_at": db_sess.started_at.isoformat() if db_sess.started_at else None,
            "escalated_at": db_sess.escalated_at.isoformat() if db_sess.escalated_at else None,
            "resolved_at": db_sess.resolved_at.isoformat() if db_sess.resolved_at else None
        }

@router.post("/push-token")
async def register_push_token(payload: dict, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        claims = verify_jwt_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    session_id = claims.get("sub")
    if not session_id:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    from backend.storage.db import async_session_factory
    from backend.storage.schema import SessionModel, CustomerPushTokenModel
    from sqlalchemy import select
    from uuid import UUID
    
    async with async_session_factory() as session:
        res = await session.execute(select(SessionModel).where(SessionModel.id == UUID(session_id)))
        sess_model = res.scalar_one_or_none()
        if not sess_model:
            raise HTTPException(status_code=404, detail="Session not found")

        push_token = payload.get("push_token")
        if not push_token:
            raise HTTPException(status_code=400, detail="Missing push_token")
            
        stmt = select(CustomerPushTokenModel).where(CustomerPushTokenModel.push_token == push_token)
        res_token = await session.execute(stmt)
        token_record = res_token.scalar_one_or_none()
        if not token_record:
            token_record = CustomerPushTokenModel(
                customer_id=sess_model.customer_id,
                push_token=push_token,
                platform=payload.get("platform", "expo")
            )
            session.add(token_record)
        else:
            token_record.customer_id = sess_model.customer_id
            token_record.platform = payload.get("platform", "expo")
        await session.commit()
        return {"status": "registered"}

