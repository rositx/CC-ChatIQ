import json
from typing import Optional
from redis.asyncio import Redis
from backend.config import REDIS_URL, SESSION_TTL_SECONDS

class RedisSessionManager:
    """Manages user session state stored in Redis.

    This manager provides asynchronous operations to persist and retrieve session
    state dictionaries as serialized JSON blobs with a configured time-to-live.
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client or Redis.from_url(REDIS_URL, decode_responses=True)

    async def set_session_state(self, session_id: str, state: dict) -> None:
        """Saves active session state JSON blob in Redis.

        Args:
            session_id: The unique identifier for the user session.
            state: The dictionary representing the session state to save.

        Raises:
            TypeError: If the state dictionary is not JSON serializable.
            redis.exceptions.RedisError: If there is an error communicating with Redis.
        """
        key = f"session:{session_id}"
        await self.redis.set(key, json.dumps(state), ex=SESSION_TTL_SECONDS)

    async def get_session_state(self, session_id: str) -> Optional[dict]:
        """Retrieves active session state JSON blob from Redis.

        Args:
            session_id: The unique identifier for the user session.

        Returns:
            The session state dictionary if found, or None if the session does not exist.

        Raises:
            json.JSONDecodeError: If the retrieved data cannot be parsed as JSON.
            redis.exceptions.RedisError: If there is an error communicating with Redis.
        """
        key = f"session:{session_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

