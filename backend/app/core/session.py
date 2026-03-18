"""Session management without authentication."""
import uuid
import hashlib
from typing import Optional
from fastapi import Header, HTTPException
from app.core.cache import cache
from app.config import settings


class SessionManager:
    """Manage user sessions without authentication."""

    SESSION_PREFIX = "session:"
    SESSION_TTL = 30 * 24 * 60 * 60  # 30 days in seconds

    @staticmethod
    def generate_session_id() -> str:
        """Generate a new unique session ID."""
        return str(uuid.uuid4())

    @staticmethod
    def generate_fingerprint(ip: str, user_agent: str) -> str:
        """Generate a browser fingerprint from IP and user agent."""
        data = f"{ip}:{user_agent}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    async def create_session(session_id: str, data: dict = None) -> bool:
        """Create a new session in Redis."""
        key = f"{SessionManager.SESSION_PREFIX}{session_id}"
        session_data = data or {"created_at": str(uuid.uuid1().time)}
        return await cache.set(key, session_data, SessionManager.SESSION_TTL)

    @staticmethod
    async def get_session(session_id: str) -> Optional[dict]:
        """Retrieve session data from Redis."""
        key = f"{SessionManager.SESSION_PREFIX}{session_id}"
        return await cache.get(key)

    @staticmethod
    async def update_session(session_id: str, data: dict) -> bool:
        """Update session data in Redis."""
        key = f"{SessionManager.SESSION_PREFIX}{session_id}"
        # Refresh TTL on update
        return await cache.set(key, data, SessionManager.SESSION_TTL)

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """Delete a session from Redis."""
        key = f"{SessionManager.SESSION_PREFIX}{session_id}"
        return await cache.delete(key)

    @staticmethod
    async def refresh_session(session_id: str) -> bool:
        """Refresh session TTL without changing data."""
        session_data = await SessionManager.get_session(session_id)
        if session_data:
            return await SessionManager.update_session(session_id, session_data)
        return False


async def get_session_id(
    x_session_id: Optional[str] = Header(None),
    x_forwarded_for: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
) -> str:
    """Dependency to get or create session ID.

    Priority:
    1. X-Session-ID header (from client)
    2. Create new session from fingerprint
    3. Create completely new session

    Args:
        x_session_id: Session ID from client header
        x_forwarded_for: Client IP address
        user_agent: Client user agent

    Returns:
        session_id: Valid session identifier
    """
    # Check if Redis is available
    from app.core.cache import cache
    redis_available = cache._redis is not None

    # Trust the session ID from the client header directly
    if x_session_id:
        if redis_available:
            session_data = await SessionManager.get_session(x_session_id)
            if session_data:
                await SessionManager.refresh_session(x_session_id)
            else:
                # First time seeing this client session — register it
                await SessionManager.create_session(x_session_id, {})
        return x_session_id

    # Create new session
    session_id = SessionManager.generate_session_id()

    # Store fingerprint for reference (optional)
    if redis_available:
        session_data = {}
        if x_forwarded_for and user_agent:
            fingerprint = SessionManager.generate_fingerprint(x_forwarded_for, user_agent)
            session_data["fingerprint"] = fingerprint

        await SessionManager.create_session(session_id, session_data)

    return session_id


async def require_session_id(
    x_session_id: Optional[str] = Header(None)
) -> str:
    """Dependency that requires a valid session ID.

    Raises HTTPException if no valid session provided.

    In development mode without Redis, accepts any session ID for testing.
    """
    if not x_session_id:
        raise HTTPException(
            status_code=401,
            detail="Session ID required. Please provide X-Session-ID header."
        )

    # Check if Redis is available
    from app.core.cache import cache
    if cache._redis is None:
        # Redis not available - accept any session ID in development
        # In production with Redis, this would validate the session
        return x_session_id

    session_data = await SessionManager.get_session(x_session_id)
    if not session_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session ID."
        )

    # Refresh session
    await SessionManager.refresh_session(x_session_id)
    return x_session_id
