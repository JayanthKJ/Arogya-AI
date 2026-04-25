"""
routes/chat.py  (v2 — passes session_id into AIService.process)
Defines the /chat router with a single POST endpoint.
---------------------------------------------------------------
CHANGE LOG (v2):
  - chat() handler: reads session_id from ChatRequest and passes it
    to ai_service.process(message, session_id)
  - Everything else (error handling, response shape, health endpoint)
    is UNCHANGED from v1, which is as follows:
    Route handler responsibilities (only):
    - Validate the incoming request  (Pydantic handles this automatically)
    - Delegate to AIService
    - Return a typed response
    - Handle known exceptions with appropriate HTTP status codes

Business logic lives in services/, not here.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from config.settings import Settings, get_settings
from models.schemas  import ChatRequest, ChatResponse, ErrorResponse
from services        import AIService

from config.database import get_session
from sqlmodel import Session, select
from models.db_models import ChatMessage

logger = logging.getLogger(__name__)

# One router instance, mounted in main.py with prefix="/chat"
router = APIRouter(tags=["Chat"])


# ── Dependency: shared AIService instance ────────────────────────────────────
# FastAPI calls this once per request; the instance itself is lightweight
# because the heavy SDK clients are created lazily inside _call_llm().

# After — one AIService for the server's lifetime
_ai_service = AIService()     # ← constructed once at startup

def get_ai_service() -> AIService:
    return _ai_service        # ← same instance returned every time


# ── POST /chat ────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
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
    request:    ChatRequest = ...,
    ai_service: AIService   = Depends(get_ai_service),
    settings:   Settings    = Depends(get_settings),
    db:         Session     = Depends(get_session),   # added to allow db interaction
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
        "POST /chat | session=%s | message_length=%d",
        request.session_id, len(request.message),
    )

    try:
        # ── v2 change: pass session_id alongside the message ──────
        result = await ai_service.process(
            user_message=request.message,
            session_id=request.session_id,
            db=db,  # added db connection
        )
        return ChatResponse(**result)

    except ValueError as exc:
        # Raised for bad configuration (e.g. unknown LLM_PROVIDER)
        logger.error("Configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    except RuntimeError as exc:
        # Raised when an SDK is missing or the LLM API returns a hard failure
        logger.exception("LLM call failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable. Please try again shortly.",
        )

    except Exception as exc:
        # Catch-all — never expose raw tracebacks to the client
        logger.exception("Unexpected error in POST /chat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again.",
        )


# ── GET /chat/health — UNCHANGED ──────────────────────────────────────────────
# Lightweight liveness check that load-balancers / k8s can poll.

@router.get(
    "/health",
    summary="Chat service health check",
    include_in_schema=False
)
async def chat_health(settings: Settings = Depends(get_settings)):
    return {
        "status":   "ok",
        "provider": settings.LLM_PROVIDER,
    }

# ──────────────────────────────────────────────
# GET /chat/history/{session_id}   ← NEW
# ──────────────────────────────────────────────
@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    db: Session = Depends(get_session),
):
    """
    Returns the full conversation history for a session.
    Response shape: [{"role": "user"|"assistant", "content": "..."}]
    """
    messages = db.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    ).all()

    return [{"role": m.role, "content": m.content} for m in messages]