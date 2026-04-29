from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field

from enum import Enum

class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"

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
    role: RoleEnum = Field(nullable=False)                          # "user" | "assistant"
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=_now, nullable=False)