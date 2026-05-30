from abc import ABC, abstractmethod
from typing import Optional, Any
from uuid import UUID

class BaseSessionRepository(ABC):
    @abstractmethod
    async def create_session(self, customer_id: UUID, tenant_id: UUID) -> Any:
        pass

    @abstractmethod
    async def get_session(self, session_id: UUID, tenant_id: UUID) -> Optional[Any]:
        pass

    @abstractmethod
    async def close_session(self, session_id: UUID, tenant_id: UUID, resolution_type: str) -> None:
        pass
