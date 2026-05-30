from typing import List, Optional, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.base import BaseMessageRepository
from backend.storage.schema import MessageModel, SessionModel

class MessageRepository(BaseMessageRepository):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> MessageModel:
        """Persists and commits a new message internally with error handling."""
        try:
            msg = MessageModel(
                session_id=session_id,
                role=role,
                content=content,
                metadata_=metadata
            )
            self.db.add(msg)
            await self.db.commit()
            await self.db.refresh(msg)
            return msg
        except Exception:
            await self.db.rollback()
            raise

    async def get_history(
        self,
        session_id: UUID,
        tenant_id: UUID,
        limit: int = 50
    ) -> List[MessageModel]:
        """Retrieves history of messages with strict tenant isolation."""
        query = (
            select(MessageModel)
            .join(SessionModel)
            .where(
                MessageModel.session_id == session_id,
                SessionModel.tenant_id == tenant_id
            )
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
