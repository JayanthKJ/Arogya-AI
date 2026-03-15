"""
main.py
-------
FastAPI application factory and entry point.

Responsibilities:
  - Create and configure the FastAPI app instance
  - Register middleware (CORS, logging)
  - Mount all routers
  - Expose a root health-check endpoint
  - Configure structured logging

Run locally:
    uvicorn main:app --reload --port 8000

Production:
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import get_settings
from routes import chat_router

# ── Logging setup ─────────────────────────────────────────────────────────────
# Configure before anything else so all subsequent loggers inherit the format.

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown hooks) ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code before `yield` runs on startup; code after runs on shutdown.
    Add DB connection pools, warm-up caches, etc. here.
    """
    logger.info(
        "Starting %s v%s | provider=%s | debug=%s",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.LLM_PROVIDER,
        settings.DEBUG,
    )
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Backend API for Arogya AI — a compassionate health guidance assistant. "
            "Provides symptom extraction, context-aware prompting, and safe AI responses."
        ),
        docs_url="/docs" if settings.DEBUG else None,   # hide Swagger in production
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # ── Request timing middleware ──────────────────────────────────
    @app.middleware("http")
    async def log_request_time(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s → %d  (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # ── Global exception handler ───────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred.", "code": "INTERNAL_ERROR"},
        )

    # ── Routers ───────────────────────────────────────────────────
    app.include_router(chat_router, prefix="/chat")

    # ── Root health check ──────────────────────────────────────────
    @app.get("/", tags=["Health"], summary="Root health check")
    async def root():
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status":  "running",
        }

    @app.get("/health", tags=["Health"], summary="Detailed health check")
    async def health():
        return {
            "service":  settings.APP_NAME,
            "version":  settings.APP_VERSION,
            "status":   "healthy",
            "provider": settings.LLM_PROVIDER,
            "debug":    settings.DEBUG,
        }

    return app


# ── Singleton app instance ────────────────────────────────────────────────────
app = create_app()
