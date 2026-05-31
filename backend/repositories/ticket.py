from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.storage.schema import SupportTicketModel

class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(self, session_id: UUID | None, email: str, message: str) -> SupportTicketModel:
        """Create and persist a new support ticket."""
        ticket = SupportTicketModel(
            session_id=session_id,
            email=email,
            message=message
        )
        self.session.add(ticket)
        await self.session.commit()
        return ticket
