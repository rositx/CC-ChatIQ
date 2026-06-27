import json
import logging
from typing import Optional, Any
from redis.asyncio import Redis
from backend.config import REDIS_URL, SESSION_TTL_SECONDS, LOCAL_TESTING

logger = logging.getLogger(__name__)

# Global in-memory fallback dictionary for when Redis is unavailable or LOCAL_TESTING is active
_in_memory_redis = {}

class MockRedisClient:
    """In-memory dictionary-based mock client matching a subset of Redis commands."""
    async def get(self, key: str) -> Optional[str]:
        return _in_memory_redis.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> None:
        _in_memory_redis[key] = str(value)

    async def delete(self, *keys: str) -> None:
        for key in keys:
            _in_memory_redis.pop(key, None)

    async def expire(self, key: str, time: int) -> None:
        pass

    async def incrby(self, key: str, amount: int = 1) -> int:
        val = int(_in_memory_redis.get(key, 0)) + amount
        _in_memory_redis[key] = str(val)
        return val

    async def zadd(self, key: str, mapping: dict) -> None:
        if key not in _in_memory_redis or not isinstance(_in_memory_redis[key], dict):
            _in_memory_redis[key] = {}
        for member, score in mapping.items():
            _in_memory_redis[key][member] = score

    async def zrem(self, key: str, *members: str) -> None:
        if key in _in_memory_redis and isinstance(_in_memory_redis[key], dict):
            for member in members:
                _in_memory_redis[key].pop(member, None)

    async def zcard(self, key: str) -> int:
        if key in _in_memory_redis and isinstance(_in_memory_redis[key], dict):
            return len(_in_memory_redis[key])
        return 0

    async def hkeys(self, key: str) -> list:
        if key in _in_memory_redis and isinstance(_in_memory_redis[key], dict):
            return [k.encode("utf-8") if isinstance(k, str) else k for k in _in_memory_redis[key].keys()]
        return []

    async def hset(self, name: str, key: str, value: str) -> None:
        if name not in _in_memory_redis or not isinstance(_in_memory_redis[name], dict):
            _in_memory_redis[name] = {}
        _in_memory_redis[name][key] = value

    async def hdel(self, name: str, *keys: str) -> None:
        if name in _in_memory_redis and isinstance(_in_memory_redis[name], dict):
            for key in keys:
                _in_memory_redis[name].pop(key, None)

class RedisSessionManager:
    """Manages user session state stored in Redis (or in-memory mock client fallback).

    This manager provides asynchronous operations to persist and retrieve session
    state dictionaries as serialized JSON blobs with a configured time-to-live.
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        if redis_client is not None:
            self.redis = redis_client
        elif LOCAL_TESTING:
            self.redis = MockRedisClient()
        else:
            try:
                self.redis = Redis.from_url(REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.warning("Failed to initialize Redis client, falling back to in-memory: %s", e)
                self.redis = MockRedisClient()

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

