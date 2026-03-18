"""
models/schemas.py  (v2 — adds session_id to ChatRequest)
---------------------------------------------------------
v1:
All Pydantic models (request bodies, response shapes, internal DTOs).
Keeping schemas in one place makes validation and OpenAPI docs consistent.

CHANGE LOG (v2):
  - ChatRequest: added `session_id` field (required, non-empty string)

Everything else is unchanged from v1.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator
import uuid

# ── Inbound ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """
    Body of POST /chat.
    `message` is the raw text the user typed in the frontend.

    v2 adds `session_id` so the backend can look up and persist
    conversation history for this user/tab/session.
    The frontend should generate a stable UUID per conversation
    (e.g. crypto.randomUUID()) and pass it with every message.

    Fields:
      message    — raw text the user typed in the frontend.
      session_id — OPTIONAL. Groups messages into a conversation for memory.
                   Auto-generated as a fresh UUID when not provided, which
                   gives stateless / single-turn behaviour.
                   Send the same value across turns to enable conversation memory.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's health-related question or description of symptoms.",
        examples=["I have fever and headache for 3 days"],
    )

    # ── NEW in v2 ──────────────────────────────────────────────────
    # Optional — defaults to a fresh UUID so old frontends keep working.
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        min_length=1,
        max_length=128,
        description=(
            "Optional session identifier. When omitted, a new UUID is "
            "auto-generated (stateless / single-turn mode). Send the same "
            "value across turns to enable conversation memory."
        ),
        examples=["user-abc123", "550e8400-e29b-41d4-a716-446655440000"],
    )

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message must not be empty or only whitespace.")
        return stripped

    @field_validator("session_id")
    @classmethod
    def strip_session_id(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("session_id must not be empty or only whitespace.")
        return stripped


# ── Internal DTOs ─────────────────────────────────────────────────────────────

class ExtractedSymptoms(BaseModel):
    """
    Output of SymptomExtractor.
    Carries structured data into the PromptBuilder.
    """

    symptoms: list[str] = Field(
        default_factory=list,
        description="List of symptoms mentioned by the user.",
        examples=[["fever", "headache"]],
    )
    duration: Optional[str] = Field(
        default=None,
        description="Duration of symptoms, if mentioned.",
        examples=["3 days"],
    )
    body_parts: list[str] = Field(
        default_factory=list,
        description="Body parts mentioned (e.g. chest, stomach).",
    )
    severity_hints: list[str] = Field(
        default_factory=list,
        description="Severity words found (e.g. severe, mild, unbearable).",
    )


class BuiltPrompt(BaseModel):
    """
    Output of PromptBuilder.
    Holds the system and user messages that are sent to the LLM.
    """

    system_prompt: str
    user_prompt:   str


class LLMRawResponse(BaseModel):
    """
    Raw LLM text before safety filtering.
    Unchanged from v1.
    """

    raw_text:   str
    model_used: str


# ── Outbound ──────────────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    """
    Response returned to the frontend.
    Structure is UNCHANGED from v1 — no breaking changes.
    """

    reply: str = Field(
        ...,
        description="The AI-generated health guidance reply.",
    )
    extracted: ExtractedSymptoms = Field(
        ...,
        description="Structured data extracted from the user's message.",
    )
    safe: bool = Field(
        default=True,
        description="Whether the response passed the safety filter unchanged.",
    )


class ErrorResponse(BaseModel):
    """Consistent error envelope. Unchanged from v1."""

    detail: str
    code:   str = "INTERNAL_ERROR"
