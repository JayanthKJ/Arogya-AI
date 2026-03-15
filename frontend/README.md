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
