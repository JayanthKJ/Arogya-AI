from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select, delete

from auth.utils import create_access_token, hash_password, verify_password
from config.database import get_session
from config.settings import get_settings
from models.db_models import User, PasswordResetToken
from services.email_service import send_password_reset_email


router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas (auth-specific, kept local to avoid polluting
# the global schemas module)
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupRequest,
    db: Session = Depends(get_session),
):
    existing = db.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Account created successfully.", "user_id": user.id}


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_session),
):
    user = db.exec(select(User).where(User.email == payload.email)).first()

    # Deliberate constant-time path: verify even on missing user to avoid
    # timing-based user enumeration attacks.
    password_ok = verify_password(payload.password, user.password_hash) if user else False

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token)

# ---------------------------------------------------------------------------
# POST /auth/forgot-password
# ---------------------------------------------------------------------------

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_session),
):
    user = db.exec(select(User).where(User.email == payload.email)).first()

    if user:
        # Delete any existing reset tokens for this user
        db.exec(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
        
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        
        settings = get_settings()
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        send_password_reset_email(email=user.email, reset_link=reset_link)
        
    # Always return the same response to prevent user enumeration
    return {"message": "If an account exists for this email, a reset link has been sent."}


# ---------------------------------------------------------------------------
# POST /auth/reset-password
# ---------------------------------------------------------------------------

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_session),
):
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    
    reset_token = db.exec(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token."
        )
        
    # Ensure timezone awareness for expires_at (SQLite may return naive datetimes)
    expires_at = reset_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if datetime.now(timezone.utc) > expires_at:
        db.delete(reset_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token."
        )
        
    user = db.exec(select(User).where(User.id == reset_token.user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token."
        )
        
    # Update the user's password
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    
    # Delete the used token
    db.delete(reset_token)
    db.commit()
    
    return {"message": "Password has been reset successfully."}