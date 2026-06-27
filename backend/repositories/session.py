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
            from sqlalchemy import func
            query = (
                update(SessionModel)
                .where(
                    SessionModel.id == session_id,
                    SessionModel.tenant_id == tenant_id
                )
                .values(
                    status="resolved",
                    resolution_type=resolution_type,
                    resolved_at=func.now()
                )
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

    async def claim_session(self, session_id: UUID, agent_id: UUID) -> None:
        """Updates session agent assignment and sets status to active."""
        try:
            from sqlalchemy import func
            query = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(agent_id=agent_id, status="active", claimed_at=func.now())
            )
            await self.db.execute(query)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def update_summary(self, session_id: UUID, summary: str) -> None:
        """Updates the session's summary field."""
        try:
            query = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(summary=summary)
            )
            await self.db.execute(query)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def get_escalated_sessions(self) -> list:
        """Fetches all escalated sessions ordered by escalation timestamp."""
        query = select(SessionModel).where(SessionModel.status == "escalated").order_by(SessionModel.escalated_at.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_peak_score(self, session_id: UUID, score: float) -> None:
        """Updates the session's peak frustration score."""
        try:
            query = (
                update(SessionModel)
                .where(SessionModel.id == session_id)
                .values(peak_score=score)
            )
            await self.db.execute(query)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def get_analytics_data(self, tenant_id: UUID) -> dict:
        """Computes metrics from PostgreSQL for analytics."""
        from sqlalchemy import func
        
        # 1. Total sessions
        total_stmt = select(func.count(SessionModel.id)).where(SessionModel.tenant_id == tenant_id)
        total_res = await self.db.execute(total_stmt)
        total_sessions = total_res.scalar() or 0
        
        # 2. Wait times: AVG(epoch(claimed_at) - epoch(escalated_at))
        wait_stmt = select(
            func.avg(
                func.extract('epoch', SessionModel.claimed_at) - 
                func.extract('epoch', SessionModel.escalated_at)
            )
        ).where(
            SessionModel.tenant_id == tenant_id,
            SessionModel.claimed_at.is_not(None),
            SessionModel.escalated_at.is_not(None)
        )
        wait_res = await self.db.execute(wait_stmt)
        avg_wait = wait_res.scalar() or 0.0
        
        # 3. Escalation triggers count
        trigger_stmt = select(
            SessionModel.escalation_trigger,
            func.count(SessionModel.id)
        ).where(
            SessionModel.tenant_id == tenant_id,
            SessionModel.escalation_trigger.is_not(None)
        ).group_by(SessionModel.escalation_trigger)
        
        trigger_res = await self.db.execute(trigger_stmt)
        triggers = {row[0]: row[1] for row in trigger_res.all()}
        
        standard_triggers = ["calmiq", "user_request", "keyword_trigger", "manual_transfer"]
        triggers_dict = {t: triggers.get(t, 0) for t in standard_triggers}
        
        rag_fallback_count = triggers.get("rag_fallback", 0)
        
        return {
            "total_sessions": total_sessions,
            "escalations_by_trigger": triggers_dict,
            "average_wait_time_seconds": float(avg_wait),
            "rag_fallback_count": rag_fallback_count
        }


