import asyncio
from backend.storage.db import async_session_factory
from sqlalchemy import select
from backend.storage.schema import MessageModel, SessionModel

async def dump():
    async with async_session_factory() as session:
        msgs = (await session.execute(select(MessageModel))).scalars().all()
        print("--- MESSAGES ---")
        for m in msgs:
            print(f"[{m.created_at}] {m.role}: {m.content}")
            
        sessions = (await session.execute(select(SessionModel))).scalars().all()
        print("\n--- SESSIONS ---")
        for s in sessions:
            print(f"ID: {s.id}, Status: {s.status}, Escalation Trigger: {s.escalation_trigger}")

if __name__ == "__main__":
    asyncio.run(dump())
