import logging
from fastapi import APIRouter, Header, HTTPException, status, Depends
from pydantic import BaseModel, UUID4
from backend.config import CALMIQ_WEBHOOK_SECRET
from backend.repositories.session import SessionRepository
from backend.session.state import RedisSessionManager
from backend.handoff.executor import execute_handoff

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

class CalmIQWebhookPayload(BaseModel):
    session_id: UUID4
    customer_id: UUID4
    message: str
    history: str
    escalate: bool

async def get_session_repo():
    from backend.storage.db import async_session_factory
    async with async_session_factory() as session:
        yield SessionRepository(session)

@router.post("/calmiq")
async def handle_calmiq_webhook(
    payload: CalmIQWebhookPayload,
    x_calmiq_secret: str = Header(None, alias="X-CalmIQ-Secret"),
    session_repo: SessionRepository = Depends(get_session_repo)
):
    """Handle incoming scoring webhook messages from CalmIQ."""
    if not x_calmiq_secret or x_calmiq_secret != CALMIQ_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature secret header"
        )

    if payload.escalate:
        redis_manager = RedisSessionManager()
        await execute_handoff(
            session_id=str(payload.session_id),
            trigger_reason="calmiq_webhook",
            session_repo=session_repo,
            redis_manager=redis_manager
        )
    
    return {"status": "processed"}
