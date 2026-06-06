from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select
from backend.storage.db import async_session_factory
from backend.storage.schema import TenantApiKeyModel

router = APIRouter(tags=["widget"])

@router.get("/api/v1/widget/config")
async def get_widget_config(request: Request, api_key: str = Query(...)):
    async with async_session_factory() as session:
        stmt = select(TenantApiKeyModel).where(TenantApiKeyModel.api_key == api_key)
        result = await session.execute(stmt)
        key_record = result.scalar_one_or_none()
        if not key_record:
            raise HTTPException(status_code=403, detail="Invalid API Key")

        origin = request.headers.get("origin") or request.headers.get("referer") or ""
        if key_record.domain_whitelist:
            allowed_domains = [d.strip() for d in key_record.domain_whitelist.split(",")]
            # Allow requests that have none or empty origin/referer under development, but enforce matches if specified
            if origin:
                if not any(domain in origin for domain in allowed_domains):
                    raise HTTPException(status_code=403, detail="Origin not authorized")

        return {
            "tenant_id": str(key_record.tenant_id),
            "primary_color": "#4F46E5",
            "widget_url": "http://localhost:5173"
        }
