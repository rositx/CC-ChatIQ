from typing import Optional
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.base import BaseSessionRepository
from backend.storage.schema import SessionModel

class SessionRepository(BaseSessionRepository):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_session(self, customer_id: UUID, tenant_id: UUID) -> SessionModel:
        """Persists and commits a new customer session internally."""
        try:
            new_session = SessionModel(
                customer_id=customer_id,
                tenant_id=tenant_id,
                status="active"
            )
            self.db.add(new_session)
            await self.db.commit()
            await self.db.refresh(new_session)
            return new_session
        except Exception:
            await self.db.rollback()
            raise

    async def get_session(self, session_id: UUID, tenant_id: UUID) -> Optional[SessionModel]:
        """Retrieves session details enforcing strict tenant isolation filters."""
        query = select(SessionModel).where(
            SessionModel.id == session_id,
            SessionModel.tenant_id == tenant_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def close_session(self, session_id: UUID, tenant_id: UUID, resolution_type: str) -> None:
        """Flags an active session as resolved and seals the transactional state."""
        try:
            query = (
                update(SessionModel)
                .where(
                    SessionModel.id == session_id,
                    SessionModel.tenant_id == tenant_id
                )
                .values(status="resolved", resolution_type=resolution_type)
            )
            await self.db.execute(query)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def mark_escalated(self, session_id: UUID, trigger_reason: str) -> None:
        """Flags an active session as escalated, recording the trigger reason."""
        try:
            from sqlalchemy import func
            query = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(
                    status="escalated",
                    escalation_trigger=trigger_reason,
                    escalated_at=func.now()
                )
            )
            await self.db.execute(query)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

