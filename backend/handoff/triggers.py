from backend.config import RAG_FALLBACK_ESCALATION_THRESHOLD, KEYWORD_TRIGGER_LIST
from backend.session.state import RedisSessionManager

async def evaluate_escalation(
    session_id: str, 
    message_content: str, 
    trigger_fallback: bool,
    redis_manager: RedisSessionManager
) -> bool:
    """
    Evaluates keyword triggers and fallback statistics atomically in Redis.
    Returns True if human escalation criteria are met.
    """
    # Trigger Source 1: Keyword list matching
    content_lower = message_content.lower()
    if any(keyword in content_lower for keyword in KEYWORD_TRIGGER_LIST):
        return True

    # Trigger Source 2: RAG Consecutive Fallbacks
    # Store counter in separate key to prevent type conflict with JSON session state
    counter_key = f"session:{session_id}:rag_fallback_count"
    
    if trigger_fallback:
        # Atomic Redis increment prevents WebSocket concurrency race conditions
        current_count = await redis_manager.redis.incrby(counter_key, 1)
        await redis_manager.redis.expire(counter_key, 86400)  # Matches session TTL
        if current_count >= int(RAG_FALLBACK_ESCALATION_THRESHOLD):
            return True
    else:
        # Successful RAG answer resets consecutive fallbacks
        await redis_manager.redis.set(counter_key, 0)
        
    return False
