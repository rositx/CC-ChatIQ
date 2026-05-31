from abc import ABC, abstractmethod
from typing import Optional, Any, List
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

    @abstractmethod
    async def mark_escalated(self, session_id: UUID, trigger_reason: str) -> None:
        pass

class BaseMessageRepository(ABC):
    @abstractmethod
    async def save_message(self, session_id: UUID, role: str, content: str, metadata: Optional[dict] = None) -> Any:
        pass

    @abstractmethod
    async def get_history(self, session_id: UUID, tenant_id: UUID, limit: int = 50) -> List[Any]:
        pass

class BaseKnowledgeRepository(ABC):
    @abstractmethod
    async def save_chunk(self, tenant_id: UUID, title: str, content: str, embedding: List[float], index: int, source_url: Optional[str] = None) -> Any:
        pass

    @abstractmethod
    async def search_similar(self, query_vector: List[float], tenant_id: UUID, top_k: int = 5) -> List[Any]:
        pass
