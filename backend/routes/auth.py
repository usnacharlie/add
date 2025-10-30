"""
Authentication API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib

from backend.config.database import get_db
from backend.models import User
from backend.schemas.user import UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def hash_pin(pin: str) -> str:
    """Hash a PIN using SHA256"""
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify a PIN against its hash"""
    return hash_pin(plain_pin) == hashed_pin


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user with email/phone and PIN
    """
    # Try to find user by email or phone
    user = db.query(User).filter(
        (User.email == credentials.identifier) |
        (User.phone == credentials.identifier)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    if not verify_pin(credentials.pin, user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Generate token (simple token for now, in production use JWT)
    token = f"user_{user.id}_{user.role}_{datetime.utcnow().timestamp()}"

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/verify-token")
def verify_token(token: str, db: Session = Depends(get_db)):
    """
    Verify a token and return user info
    """
    # Simple token parsing (user_id_role_timestamp)
    try:
        parts = token.split("_")
        if len(parts) >= 2 and parts[0] == "user":
            user_id = int(parts[1])
            user = db.query(User).filter(User.id == user_id).first()

            if user and user.is_active:
                return {"valid": True, "user": UserResponse.from_orm(user)}
    except:
        pass

    return {"valid": False}


@router.get("/me", response_model=UserResponse)
def get_current_user(token: str, db: Session = Depends(get_db)):
    """
    Get current user from token
    """
    try:
        parts = token.split("_")
        if len(parts) >= 2 and parts[0] == "user":
            user_id = int(parts[1])
            user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

            if user:
                return user
    except:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token"
    )
