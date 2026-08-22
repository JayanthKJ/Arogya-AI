from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field

# from enum import Enum
#
# class RoleEnum(str, Enum):
#     user = "user"
#     assistant = "assistant"

# role: str = Field(default="user")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=_generate_uuid, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=_now, nullable=False)


# ---------------------------------------------------------------------------
# ChatMessage
# ---------------------------------------------------------------------------

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: str = Field(default_factory=_generate_uuid, primary_key=True)
    session_id: str = Field(index=True, nullable=False)
    user_id: str = Field(index=True, nullable=False)          # FK-style, no hard FK constraint
    role: str = Field(default="user", nullable=False)                          # "user" | "assistant"
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=_now, nullable=False)

# ---------------------------------------------------------------------------
# PasswordResetToken
# ---------------------------------------------------------------------------

class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: str = Field(default_factory=_generate_uuid, primary_key=True)
    user_id: str = Field(foreign_key = "users.id", index=True, nullable=False)
    token_hash: str = Field(nullable=False)
    expires_at: datetime = Field(nullable=False)
    created_at: datetime = Field(default_factory=_now, nullable=False)

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class UserSession(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=_generate_uuid, primary_key=True)
    user_id: str = Field(foreign_key = "users.id", index=True, nullable = False)
    created_at: datetime = Field(default_factory = _now, nullable = False)
    expires_at: datetime = Field(nullable = False)
    revoked_at: Optional[datetime] = Field(nullable = True)

# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

from datetime import date

class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"

    user_id: str = Field(foreign_key="users.id", primary_key=True, index=True, nullable=False)
    name: Optional[str] = Field(default=None)
    date_of_birth: Optional[date] = Field(default=None)
    language: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_now, nullable=False)
    updated_at: datetime = Field(default_factory=_now, nullable=False)