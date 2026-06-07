"""
Redis cache client using aioredis.
"""
import json
import hashlib
from typing import Any, Optional

import aioredis
from aioredis import Redis

from backend.config import settings


class RedisClient:
    """Async Redis client wrapper."""
    
    _client: Optional[Redis] = None
    
    @classmethod
    async def connect(cls) -> Redis:
        """
        Connect to Redis.
        
        Returns:
            Redis client.
        """
        if cls._client is None:
            cls._client = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._client
    
    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from Redis."""
        if cls._client:
            await cls._client.close()
            cls._client = None
    
    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            key: Cache key.
        
        Returns:
            Cached value or None.
        """
        client = await cls.connect()
        return await client.get(key)
    
    @classmethod
    async def get_json(cls, key: str) -> Optional[Any]:
        """
        Get JSON value from cache.
        
        Args:
            key: Cache key.
        
        Returns:
            Parsed JSON or None.
        """
        value = await cls.get(key)
        if value:
            return json.loads(value)
        return None
    
    @classmethod
    async def set(
        cls,
        key: str,
        value: str,
        ttl: int = 3600
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds.
        
        Returns:
            True if successful.
        """
        client = await cls.connect()
        return await client.setex(key, ttl, value)
    
    @classmethod
    async def set_json(
        cls,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Set JSON value in cache.
        
        Args:
            key: Cache key.
            value: Value to serialize and cache.
            ttl: Time to live in seconds.
        
        Returns:
            True if successful.
        """
        json_str = json.dumps(value)
        return await cls.set(key, json_str, ttl)
    
    @classmethod
    async def delete(cls, key: str) -> int:
        """
        Delete key from cache.
        
        Args:
            key: Cache key.
        
        Returns:
            Number of keys deleted.
        """
        client = await cls.connect()
        return await client.delete(key)
    
    @classmethod
    async def exists(cls, key: str) -> bool:
        """
        Check if key exists.
        
        Args:
            key: Cache key.
        
        Returns:
            True if key exists.
        """
        client = await cls.connect()
        return await client.exists(key)
    
    @classmethod
    async def increment(cls, key: str, amount: int = 1) -> int:
        """
        Increment integer value.
        
        Args:
            key: Cache key.
            amount: Amount to increment.
        
        Returns:
            New value.
        """
        client = await cls.connect()
        return await client.incrby(key, amount)
    
    @classmethod
    async def flush_all(cls) -> bool:
        """
        Flush all keys from cache.
        
        Returns:
            True if successful.
        """
        client = await cls.connect()
        return await client.flushall()


def compute_hash(value: Any) -> str:
    """
    Compute MD5 hash of a value.
    
    Args:
        value: Value to hash.
    
    Returns:
        MD5 hash.
    """
    if isinstance(value, dict):
        value = json.dumps(value, sort_keys=True)
    elif not isinstance(value, str):
        value = str(value)
    
    return hashlib.md5(value.encode()).hexdigest()
