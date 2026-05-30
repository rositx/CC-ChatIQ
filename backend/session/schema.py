from pydantic import BaseModel
from uuid import UUID

class SessionCreateRequest(BaseModel):
    customer_id: UUID
    tenant_id: UUID
