from sqlmodel import SQLModel, Field
from typing import Literal
from datetime import datetime, timezone
import uuid

from enum import Enum

class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"

class ChatMessage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    session_id: str = Field(index=True)

    role: RoleEnum
    content: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))