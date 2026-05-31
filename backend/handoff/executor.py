import time
from uuid import UUID
from backend.repositories.session import SessionRepository
from backend.session.state import RedisSessionManager

async def execute_handoff(
    session_id: str, 
    trigger_reason: str,
    session_repo: SessionRepository,
    redis_manager: RedisSessionManager
) -> None:
    """Executes the agent handoff sequence, silences the AI bot, and enqueues real-time states."""
    # 1. Silence the AI dynamically in Redis for this session context
    silence_key = f"session:{session_id}:ai_silenced"
    await redis_manager.redis.set(silence_key, "true")
    await redis_manager.redis.expire(silence_key, 86400)  # TTL matching session duration

    # 2. Update persistent storage session tracking metadata in Postgres
    session_uuid = UUID(session_id)
    await session_repo.mark_escalated(session_uuid, trigger_reason)

    # 3. Enqueue session into the active agent sorted set using epoch timestamp score
    current_time_epoch = time.time()
    await redis_manager.redis.zadd("queue:escalated", {session_id: current_time_epoch})
