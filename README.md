# Arogya AI — Chat Interface

A clean, modular React + TailwindCSS chat interface built for elderly users.
Large fonts (18px+), high contrast, simple layout, and full accessibility support.

## Folder Structure

```
arogya-ai/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.example
└── src/
    ├── main.jsx               # Entry point
    ├── App.jsx                # Root layout, wires all pieces
    ├── index.css              # Tailwind directives + global resets
    │
    ├── components/
    │   ├── Header.jsx         # Top bar: branding, status, action buttons
    │   ├── Sidebar.jsx        # Left nav: branding, history, disclaimer
    │   ├── ChatWindow.jsx     # Scrollable message list + welcome banner
    │   ├── MessageBubble.jsx  # Single chat message (user or AI)
    │   └── ChatInput.jsx      # Auto-grow textarea + send button
    │
    ├── hooks/
    │   └── useChat.js         # messages[], isLoading, error, send(), clearError()
    │
    ├── services/
    │   └── api.js             # sendMessage() — real API or mock fallback
    │
    └── constants/
        └── index.js           # QUICK_CHIPS, CHAT_HISTORY, APP_NAME
```

## Component Responsibilities

| Component       | Single Responsibility                                    |
|-----------------|----------------------------------------------------------|
| `App.jsx`       | Compose layout, wire hook → components                   |
| `Sidebar`       | Show branding, history list, disclaimer                  |
| `Header`        | Show identity, status dot, language & emergency buttons  |
| `ChatWindow`    | Render message list, typing indicator, error toast       |
| `MessageBubble` | Render ONE message bubble (user or AI)                   |
| `ChatInput`     | Capture user input, trigger send, show loading state     |

## Hook: useChat

```js
const { messages, isLoading, error, send, clearError } = useChat();
```

| Value        | Type              | Description                         |
|--------------|-------------------|-------------------------------------|
| `messages`   | `Message[]`       | All messages in the conversation    |
| `isLoading`  | `boolean`         | True while waiting for AI response  |
| `error`      | `string \| null`  | Error message if API call failed    |
| `send(text)` | `(string) => void`| Sends a user message                |
| `clearError` | `() => void`      | Dismisses the error toast           |

## Service: api.js

```js
import { sendMessage } from "./services/api";
const reply = await sendMessage(messageHistory); // returns string
```

- Set `VITE_API_URL` in `.env.local` to point at your backend.
- Leave it blank to use rotating mock responses (great for development).
- Your backend endpoint should accept `POST /api/chat` with body:
  `{ messages: [{ role: "user"|"assistant", content: string }] }`
  and return `{ reply: string }`.

## Quick Start

```bash
npm install
cp .env.example .env.local   # optionally set VITE_API_URL
npm run dev
```

## Accessibility Features

- All fonts 18px or larger
- Color contrast ≥ 4.5:1 (WCAG AA)
- `aria-label`, `role="log"`, `aria-live` on message area
- Keyboard navigable (Enter to send, Tab through buttons)
- Focus ring on all interactive elements
- Mobile-responsive with slide-in sidebar drawer

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
