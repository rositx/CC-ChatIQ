import logging
from backend.config import AGENT_QUEUE_MAX_DEPTH
from backend.session.state import RedisSessionManager

logger = logging.getLogger("handoff")

async def get_queue_status(redis_manager: RedisSessionManager) -> dict:
    """Check agent queue depth limit and estimate wait time."""
    queue_len = await redis_manager.redis.zcard("queue:escalated")
    max_depth = int(AGENT_QUEUE_MAX_DEPTH)
    
    if queue_len > max_depth:
        return {
            "is_full": True,
            "message": "Our queue is currently full. Please leave your email and message, and an agent will follow up with you directly."
        }
    
    wait_minutes = queue_len * 3
    return {
        "is_full": False,
        "queue_len": queue_len,
        "wait_minutes": wait_minutes,
        "message": f"I'm connecting you with a human agent now. The current queue length is {queue_len}. Estimated wait time is {wait_minutes} minutes."
    }
