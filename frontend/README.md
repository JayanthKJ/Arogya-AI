# Arogya AI — Frontend

A clean, modular React + TailwindCSS interface built for elderly users.
Features large fonts (18px+), high contrast, simple layout, and full accessibility support.

## Tech Stack
- **React 18** (Vite for fast bundling)
- **Tailwind CSS** (for styling and responsiveness)
- **React Router DOM** (for navigation and protected routes)
- **Lucide React** (for icons)

## Folder Structure

```
arogya-ai/frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env.example
└── src/
    ├── main.jsx               # Entry point
    ├── App.jsx                # Root layout, routes configuration
    ├── index.css              # Tailwind directives + global resets
    │
    ├── components/
    │   ├── Header.jsx         # Top bar: branding, status, action buttons
    │   ├── Sidebar.jsx        # Left nav: branding, history, disclaimer
    │   ├── ChatWindow.jsx     # Scrollable message list + welcome banner
    │   ├── MessageBubble.jsx  # Single chat message (user or AI)
    │   ├── ChatInput.jsx      # Auto-grow textarea + send button
    │   └── Auth.jsx           # Reusable auth component
    │
    ├── pages/
    │   ├── LoginPage.jsx
    │   ├── ChatPage.jsx
    │   ├── ForgotPasswordPage.jsx
    │   ├── ResetPasswordPage.jsx
    │   └── NotFoundPage.jsx
    │
    ├── routes/
    │   └── ProtectedRoute.jsx # Route wrapper requiring authentication
    │
    ├── hooks/
    │   └── useChat.js         # Chat state management hook
    │
    ├── services/
    │   └── api.js             # API integration (mock fallback & backend sync)
    │
    └── constants/
        └── index.js           # Shared constants (e.g., QUICK_CHIPS, APP_NAME)
```

## Features

- **Authentication System:** Includes Login, Password Reset, and secure Protected Routes to ensure user privacy.
- **Chat Interface:** An intuitive, auto-scrolling chat window with a dynamic chat input block.
- **Accessibility:** 
  - All fonts 18px or larger
  - Color contrast ≥ 4.5:1 (WCAG AA)
  - `aria-label`, `role="log"`, `aria-live` on message area
  - Keyboard navigable and focus rings on all interactive elements
- **Mobile-Responsive:** Adaptive layouts with a slide-in sidebar drawer for smaller screens.

## Quick Start

```bash
npm install
cp .env.example .env.local   # Configure VITE_API_URL here
npm run dev
```
