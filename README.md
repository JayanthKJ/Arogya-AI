# Arogya AI

Arogya AI is a compassionate health guidance assistant designed with a clean, highly accessible interface for elderly users. 

This repository is split into two primary sub-projects: a **React + TailwindCSS Frontend** and a **FastAPI + SQLModel Backend**.

## Project Architecture

### 1. Frontend (`/frontend`)
The user interface is built with **React** and bundled using **Vite**.
- Focuses on accessibility (large fonts, high contrast, WCAG AA compliance).
- Includes an authentication flow (Login, Registration, Password Resets) using `react-router-dom`.
- Features an intuitive chat interface optimized for seamless interactions.
- [View Frontend README](./frontend/README.md)

### 2. Backend (`/backend`)
The backend is a robust API powered by **FastAPI**.
- Manages secure user authentication via **JWT** and password hashing.
- Uses **SQLModel / SQLAlchemy** connecting to a **PostgreSQL** database to store users and chat history.
- Integrates with multiple LLM providers (Google GenAI, OpenAI, Anthropic, or Mock for dev) to extract symptoms, build medical context prompts, and apply safety filtering.
- [View Backend README](./backend/README.md)

## Quick Start

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Populate the required values like DATABASE_URL, SECRET_KEY, and GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```
