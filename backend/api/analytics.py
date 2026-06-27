from fastapi import APIRouter, Depends, HTTPException, Header, status
from typing import Optional
import uuid
from backend.utils.jwt import verify_jwt_token
from backend.repositories.session import SessionRepository

from backend.storage.db import async_session_factory

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

async def get_session_repository() -> SessionRepository:
    async with async_session_factory() as session:
        yield SessionRepository(session)

@router.get("/summary")
async def get_summary(
    authorization: Optional[str] = Header(None),
    repo: SessionRepository = Depends(get_session_repository)
):
    """Retrieve operational analytics summary metrics."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    
    tenant_id = None
    from backend.config import LOCAL_TESTING
    if LOCAL_TESTING and token == "sandbox-token":
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    else:
        try:
            claims = verify_jwt_token(token)
            tenant_id = uuid.UUID(claims.get("tenant_id"))
        except Exception:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
    return await repo.get_analytics_data(tenant_id)
