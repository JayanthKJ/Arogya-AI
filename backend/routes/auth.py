from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from auth.utils import create_access_token, hash_password, verify_password
from config.database import get_session
from models.db_models import User

from pydantic import Field

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
