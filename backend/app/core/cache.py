"""Redis cache wrapper for caching expensive operations."""
import json
from typing import Optional, Any, Callable
from functools import wraps
import hashlib
import redis.asyncio as aioredis
from app.config import settings


class CacheManager:
    """Async Redis cache manager."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initialize Redis connection."""
        try:
            self._redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            print(f"✓ Connected to Redis at {settings.REDIS_URL}")
        except Exception as e:
            print(f"⚠ Redis not available: {e}")
            print(f"  → Running without cache. Install Redis or use Docker for full functionality.")
            self._redis = None

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL in seconds."""
        if not self._redis:
            return False

        try:
            serialized = json.dumps(value)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._redis:
            return False

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._redis:
            return False

        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._redis:
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear_pattern error for pattern {pattern}: {e}")
            return 0


# Global cache instance
cache = CacheManager()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    # Create a string representation of args and kwargs
    key_data = f"{args}:{sorted(kwargs.items())}"
    # Hash it for consistent key length
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = None, key_prefix: str = ""):
    """Decorator for caching function results.

    Args:
        ttl: Time to live in seconds (None = use default from settings)
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            func_key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = await cache.get(func_key)
            if cached_result is not None:
                return cached_result

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache_ttl = ttl if ttl is not None else settings.CACHE_TTL_SECONDS
            await cache.set(func_key, result, cache_ttl)

            return result
        return wrapper
    return decorator
