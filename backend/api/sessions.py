import logging
from fastapi import APIRouter, Depends, HTTPException, status
from backend.repositories.base import BaseSessionRepository
from backend.session.schema import SessionCreateRequest

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
