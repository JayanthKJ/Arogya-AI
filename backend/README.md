# Arogya AI — FastAPI Backend

Production-grade Python backend for the Arogya AI health assistant.

## Folder Structure

```
backend/
├── main.py                     # App factory, middleware, router registration
├── requirements.txt
├── .env.example                # Copy to .env and fill in your values
│
├── config/
│   └── settings.py             # Pydantic BaseSettings — all config from env
│
├── models/
│   └── schemas.py              # All Pydantic request/response/DTO models
│
├── routes/
│   └── chat.py                 # POST /chat  +  GET /chat/health
│
├── services/
│   ├── ai_service.py           # Orchestrates the full pipeline
│   ├── symptom_extractor.py    # Rule-based NLP: symptoms, duration, body parts
│   ├── prompt_builder.py       # Builds system + user prompts for the LLM
│   └── safety_filter.py        # Hard-block + soft-rewrite post-filter
│
└── tests/
    └── test_backend.py         # Unit + integration tests (pytest)
```

## Request/Response Flow

```
POST /chat  { "message": "I have fever for 3 days" }
     │
     ▼
[routes/chat.py]          — validates input, delegates to AIService
     │
     ▼
[SymptomExtractor]        — { symptoms: ["fever"], duration: "3 days" }
     │
     ▼
[PromptBuilder]           — system prompt + enriched user prompt
     │
     ▼
[AIService._call_llm()]   — OpenAI / Anthropic / Mock
     │
     ▼
[SafetyFilter]            — hard-block dangerous phrases, soft-rewrite hedges
     │
     ▼
{ "reply": "...", "extracted": {...}, "safe": true }
```

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set LLM_PROVIDER=mock for local dev (no API key needed)

# 4. Run the development server
uvicorn main:app --reload --port 8000

# 5. Open the interactive API docs
# http://localhost:8000/docs  (only visible when DEBUG=true)
```

## Environment Variables

| Variable             | Default                  | Description                              |
|----------------------|--------------------------|------------------------------------------|
| `LLM_PROVIDER`       | `mock`                   | `mock` \| `openai` \| `anthropic`        |
| `OPENAI_API_KEY`     | —                        | Required when `LLM_PROVIDER=openai`      |
| `OPENAI_MODEL`       | `gpt-4o-mini`            | OpenAI model name                        |
| `ANTHROPIC_API_KEY`  | —                        | Required when `LLM_PROVIDER=anthropic`   |
| `ANTHROPIC_MODEL`    | `claude-3-5-haiku-...`   | Anthropic model name                     |
| `LLM_MAX_TOKENS`     | `512`                    | Max tokens in LLM reply                  |
| `LLM_TEMPERATURE`    | `0.4`                    | LLM temperature (lower = safer)          |
| `CORS_ORIGINS`       | `http://localhost:3000`  | Comma-separated allowed frontend origins |
| `DEBUG`              | `false`                  | Enables `/docs` and verbose errors       |
| `LOG_LEVEL`          | `INFO`                   | `DEBUG` \| `INFO` \| `WARNING`           |

## Running Tests

```bash
pytest tests/ -v
```

Expected output: all 26 tests pass against the mock provider.

## Adding a New LLM Provider

1. Add credentials to `.env.example` and `config/settings.py`
2. Add an `elif provider == "yourprovider":` branch in `ai_service.py`
3. Install the provider's SDK in `requirements.txt`

No other files need to change.

## API Reference

### `POST /chat`

**Request**
```json
{ "message": "I have fever and headache for 3 days" }
```

**Response**
```json
{
  "reply": "Thank you for sharing...",
  "extracted": {
    "symptoms": ["fever", "headache"],
    "duration": "3 days",
    "body_parts": [],
    "severity_hints": []
  },
  "safe": true
}
```

### `GET /health`
Returns app name, version, and current LLM provider.
