"""
routes/chat.py
--------------
Defines the /chat router with a single POST endpoint.

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

logger = logging.getLogger(__name__)

# One router instance, mounted in main.py with prefix="/chat"
router = APIRouter(tags=["Chat"])


# ── Dependency: shared AIService instance ────────────────────────────────────
# FastAPI calls this once per request; the instance itself is lightweight
# because the heavy SDK clients are created lazily inside _call_llm().

def get_ai_service() -> AIService:
    return AIService()


# ── POST /chat ────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Send a message to Arogya AI",
    description=(
        "Accepts a user's health-related message, extracts symptoms, "
        "builds a context-aware prompt, calls the configured LLM, "
        "applies a safety filter, and returns the AI's reply."
    ),
)
async def chat(
    request:    ChatRequest = ...,
    ai_service: AIService   = Depends(get_ai_service),
    settings:   Settings    = Depends(get_settings),
) -> ChatResponse:
    """
    Main chat endpoint.

    Request body:
        { "message": "I have fever and headache for 3 days" }

    Response body:
        {
          "reply": "...",
          "extracted": { "symptoms": [...], "duration": "..." },
          "safe": true
        }
    """
    logger.info("POST /chat — message length=%d", len(request.message))

    try:
        result = await ai_service.process(request.message)
        return ChatResponse(**result)

    except ValueError as exc:
        # Raised for bad configuration (e.g. unknown LLM_PROVIDER)
        logger.error("Configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
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


# ── GET /chat/health ──────────────────────────────────────────────────────────
# Lightweight liveness check that load-balancers / k8s can poll.

@router.get(
    "/health",
    summary="Chat service health check",
    include_in_schema=False,
)
async def chat_health(settings: Settings = Depends(get_settings)):
    return {
        "status":   "ok",
        "provider": settings.LLM_PROVIDER,
    }
