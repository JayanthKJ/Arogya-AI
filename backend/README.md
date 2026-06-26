# Arogya AI — Backend

Production-grade Python FastAPI backend for the Arogya AI health assistant.
It provides symptom extraction, context-aware prompting, safe AI responses, and a secure user authentication system.

## Tech Stack
- **FastAPI** (Web framework)
- **SQLModel & SQLAlchemy** (ORM and Database Models)
- **PostgreSQL** (Database, via psycopg2)
- **Google GenAI / OpenAI / Anthropic** (LLM Integrations)
- **PyJWT & Passlib (Bcrypt)** (For Authentication and Password Hashing)
- **Pytest** (For testing)

## Folder Structure

```
backend/
├── main.py                     # App factory, middleware, router registration
├── requirements.txt
├── .env.example                # Copy to .env and fill in values
│
├── config/
│   ├── settings.py             # Pydantic BaseSettings config
│   └── database.py             # Database engine and session initialization
│
├── models/
│   ├── db_models.py            # SQLModel database tables (User, ChatHistory, etc.)
│   └── schemas.py              # Pydantic validation schemas (Request/Response DTOs)
│
├── routes/
│   ├── chat.py                 # Chat endpoints
│   └── auth.py                 # Auth endpoints (Login, Register, Password Reset)
│
├── services/
│   ├── ai_service.py           # Orchestrates the AI pipeline
│   ├── symptom_extractor.py    # Rule-based NLP: symptoms, duration, body parts
│   ├── prompt_builder.py       # Builds prompts for the LLM
│   └── safety_filter.py        # Post-filter for AI responses
│
└── tests/
    └── test_backend.py         # Unit and integration tests (pytest)
```

## Authentication & Database

The backend includes a full authentication system using JWT tokens:
- `POST /auth/register`: Create a new user account
- `POST /auth/login`: Authenticate and receive a JWT token
- Password resets and email functionality are integrated (using Resend).

Ensure you have configured `DATABASE_URL` and `SECRET_KEY` in your environment along with your LLM configuration (e.g. `GEMINI_API_KEY`).

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, GEMINI_API_KEY, etc.

# 4. Run the development server
uvicorn main:app --reload --port 8000

# 5. Open the interactive API docs
# http://localhost:8000/docs  (only visible when DEBUG=true)
```
