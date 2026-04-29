from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from auth.dependencies import get_current_user
from config.database import get_session
from models.db_models import ChatMessage, User
from models.schemas import ChatRequest, ChatResponse, ErrorResponse
from services.ai_service import AIService
from config.settings import get_settings, Settings

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

# ── Module-level singleton — do NOT instantiate per-request ───────────
_ai_service = AIService()

# ── Dependency: shared AIService instance ────────────────────────────────────
# FastAPI calls this once per request; the instance itself is lightweight
# because the heavy SDK clients are created lazily inside _call_llm().

def get_ai_service() -> AIService:
    return _ai_service


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "LLM unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Send a message to Arogya AI",
    description=(
        "Accepts a user message and session_id. Retrieves conversation history "
        "for the session, builds a context-aware prompt, calls the LLM, applies "
        "a safety filter, persists the reply, and returns the response."
    ),
)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_session),
    ai_service: AIService = Depends(get_ai_service),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Main chat endpoint.
    v2 request body:
        { "message": "I still have that headache", "session_id": "abc123" }

    Response body (UNCHANGED from v1):
        {
          "reply": "...",
          "extracted": { "symptoms": [...], "duration": "..." },
          "safe": true
        }
    """
    logger.info(
        "POST /chat | user=%s | session=%s | msg_len=%d",
        current_user.id,
        request.session_id,
        len(request.message),
    )

    try:
        # ── v3 change: pass session_id and user_id alongside the message ──────
        result = await ai_service.process(
            user_message=request.message,
            session_id=request.session_id,
            db=db,
            user_id=current_user.id,
        )
        return result


    except ValueError as exc:
        # Client-side issue (bad input, invalid state)
        logger.warning("Bad request: %s", exc)
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except RuntimeError as exc:
        # External/system dependency failure (LLM, SDK, etc.)
        logger.error("Service failure (LLM/SDK): %s", exc)
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again shortly.",
        )

    except Exception as exc:
        # Unexpected server-side error
        logger.exception("Unexpected server error in /chat: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        )

# ---------------------------------------------------------------------------
# GET /chat/health  (public — no auth required)
# ---------------------------------------------------------------------------

@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
    }


# ---------------------------------------------------------------------------
# GET /chat/history/{session_id}  (protected — user-isolated)
# ---------------------------------------------------------------------------

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Returns conversation history scoped to BOTH the session_id and the
    authenticated user's id, preventing cross-user data leakage.
    """
    logger.info(
        "GET /chat/history | user=%s | session=%s",
        current_user.id,
        session_id,
    )
    messages = db.exec(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
    ).all()

    messages = list(reversed(messages))

    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
