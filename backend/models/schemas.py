"""
models/schemas.py
-----------------
All Pydantic models (request bodies, response shapes, internal DTOs).
Keeping schemas in one place makes validation and OpenAPI docs consistent.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── Inbound ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """
    Body of POST /chat.
    `message` is the raw text the user typed in the frontend.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's health-related question or description of symptoms.",
        examples=["I have fever and headache for 3 days"],
    )

    @field_validator("message")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message must not be empty or only whitespace.")
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
    user_prompt: str


class LLMRawResponse(BaseModel):
    """
    Raw text returned by the LLM before safety filtering.
    """

    raw_text: str
    model_used: str


# ── Outbound ──────────────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    """
    Shape of the JSON response returned to the frontend.
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
    """
    Consistent error envelope for all HTTP error responses.
    """

    detail: str
    code: str = "INTERNAL_ERROR"
