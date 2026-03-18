"""Authentication utilities for JWT token handling."""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.db.models import User

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token for user."""
    expiration = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    Returns None if no token is provided (for optional auth endpoints).
    Raises HTTPException if token is invalid.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


def require_auth(user: Optional[User] = Depends(get_current_user)) -> User:
    """
    Require authentication - raises 401 if user is not authenticated.
    Use this for endpoints that require login.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


def migrate_session_data(session_id: str, user_id: str, db: Session) -> int:
    """
    Migrate itineraries from session to authenticated user.
    Returns the number of itineraries migrated.
    """
    from app.db.models import SavedItinerary

    # Find all itineraries with this session_id that don't have a user_id
    itineraries = db.query(SavedItinerary).filter(
        SavedItinerary.session_id == session_id,
        SavedItinerary.user_id == None
    ).all()

    # Update them to belong to the user
    count = 0
    for itinerary in itineraries:
        itinerary.user_id = user_id
        count += 1

    if count > 0:
        db.commit()

    return count
