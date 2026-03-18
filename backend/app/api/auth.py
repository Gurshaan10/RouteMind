"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.db.session import get_db
from app.db.models import User
from app.core.auth import create_access_token, get_current_user, migrate_session_data
import uuid
from typing import Optional

router = APIRouter()


class GoogleAuthRequest(BaseModel):
    """Request model for Google OAuth authentication."""
    google_id: str
    email: EmailStr
    name: str
    avatar_url: str | None = None


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    name: str | None
    avatar_url: str | None
    created_at: str


@router.post("/google", response_model=AuthResponse)
def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate or create user with Google OAuth credentials.
    Called by NextAuth after successful Google login.
    """
    # Check if user exists
    user = db.query(User).filter(User.google_id == request.google_id).first()
    
    if not user:
        # Check if email already exists (user might have signed up with different method)
        user = db.query(User).filter(User.email == request.email).first()
        
        if user:
            # Link Google account to existing user
            user.google_id = request.google_id
            user.name = request.name
            user.avatar_url = request.avatar_url
        else:
            # Create new user
            user = User(
                id=str(uuid.uuid4()),
                email=request.email,
                name=request.name,
                avatar_url=request.avatar_url,
                google_id=request.google_id
            )
            db.add(user)
    else:
        # Update existing user info (name/avatar might have changed)
        user.name = request.name
        user.avatar_url = request.avatar_url
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token(user.id, user.email)
    
    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url
        }
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat()
    )


@router.post("/migrate-session")
def migrate_session(
    user: User = Depends(get_current_user),
    x_session_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Migrate itineraries from anonymous session to authenticated user.
    Called automatically when user signs in.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if not x_session_id:
        return {"migrated_count": 0, "message": "No session ID provided"}

    # Migrate session data
    count = migrate_session_data(x_session_id, user.id, db)

    return {
        "migrated_count": count,
        "message": f"Successfully migrated {count} itineraries to your account"
    }
