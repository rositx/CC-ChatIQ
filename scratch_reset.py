import asyncio
from backend.session.state import RedisSessionManager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    print("=================== CC-ChatIQ SANDBOX CLEAN RESET ===================")
    
    # 1. Reset Redis state
    redis = RedisSessionManager()
    session_id = "00000000-0000-0000-0000-000000000000"
    
    await redis.redis.delete(f"session:{session_id}:ai_silenced")
    await redis.redis.delete(f"session:{session_id}:rag_fallback_count")
    await redis.redis.delete("queue:escalated")
    print("Redis sandbox keys cleared successfully!")
    
    # 2. Reset database state
    url = "postgresql+asyncpg://postgres:password@localhost:5432/postgres"
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            # Delete message history
            await conn.execute(text("DELETE FROM messages;"))
            print("PostgreSQL messages history cleared successfully!")
            
            # Reset session state to active
            await conn.execute(text("""
                UPDATE sessions 
                SET status = 'active', agent_id = NULL, escalation_trigger = NULL, escalated_at = NULL, resolved_at = NULL
                WHERE id = '00000000-0000-0000-0000-000000000000'::uuid;
            """))
            print("PostgreSQL sandbox session status reset to 'active' successfully!")
    except Exception as e:
        print("Database reset failed:", e)
    finally:
        await engine.dispose()
    print("====================================================================")

if __name__ == "__main__":
    asyncio.run(main())
