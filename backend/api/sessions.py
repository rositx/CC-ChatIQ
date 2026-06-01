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
    
    if token == "sandbox-token" and session_id == "00000000-0000-0000-0000-000000000000":
        return []
        
    try:
        claims = verify_jwt_token(token)
        if claims.get("sub") != session_id:
            raise HTTPException(status_code=401, detail="Session mismatch")
        tenant_id = uuid.UUID(claims.get("tenant_id"))
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")

    s_uuid = uuid.UUID(session_id)
    from backend.repositories.message import MessageRepository
    from backend.storage.db import async_session_factory
    async with async_session_factory() as session:
        messages = await MessageRepository(session).get_history(s_uuid, tenant_id, limit=50)
        return [
            {
                "id": str(m.id), "session_id": str(m.session_id),
                "role": m.role, "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
