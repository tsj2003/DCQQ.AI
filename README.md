# DocQA AI — AI-Powered Document & Multimedia Q&A

[![CI/CD](https://github.com/yourusername/docqa-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/docqa-ai/actions)
[![Test Coverage](https://img.shields.io/badge/coverage-95%25+-brightgreen)](.)

> Upload PDFs, audio, and video files. Ask AI questions. Get answers with source references and playable timestamps.

## 🎥 Demo

[Watch walkthrough video on YouTube →](https://youtube.com/your-demo-video)

## ✨ Features

### Core
- 📄 **PDF Upload & Q&A** — Extract text, ask questions, get page-referenced answers
- 🎵 **Audio/Video Upload** — Transcribe with Whisper, ask questions with timestamp references  
- 💬 **AI Chatbot** — GPT-4o powered RAG pipeline with streaming responses
- 📝 **Summarization** — Auto-generated summaries for all uploaded content
- ▶️ **Play Button** — Jump to exact timestamps in audio/video from chat responses

### Bonus
- 🔍 **Vector Search** — FAISS semantic search for document retrieval
- ⚡ **Real-time Streaming** — Server-Sent Events for token-by-token chat responses
- 🔐 **Multi-user Auth** — Google OAuth 2.0 + JWT authentication
- 🚦 **Rate Limiting & Caching** — Redis-based sliding window rate limiter + response caching

## 🏗️ Architecture

```
┌────────────┐     ┌───────────────────────────────────┐
│   React    │────▶│         FastAPI Backend            │
│  Frontend  │ SSE │  ┌─────────┐  ┌──────────────┐   │
│  (Vite)    │◀────│  │ LangChain│  │ Whisper API  │   │
└────────────┘     │  │ + GPT-4o │  │ Transcription│   │
                   │  └────┬─────┘  └──────────────┘   │
                   │       │                            │
                   │  ┌────▼─────┐  ┌──────────────┐   │
                   │  │  FAISS   │  │  PostgreSQL   │   │
                   │  │ Vectors  │  │  Metadata     │   │
                   │  └──────────┘  └──────────────┘   │
                   │       ┌──────────────┐            │
                   │       │    Redis     │            │
                   │       │ Cache + Rate │            │
                   │       └──────────────┘            │
                   └───────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- Google OAuth credentials (for authentication)

### 1. Clone and configure
```bash
git clone https://github.com/yourusername/docqa-ai.git
cd docqa-ai
cp .env.example .env
# Edit .env with your API keys
```

### 2. Run with Docker Compose
```bash
docker compose up --build
```

### 3. Access the app
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

### Run locally (development)
```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 📡 API Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/auth/google` | Google OAuth login |
| GET | `/api/auth/google/callback` | OAuth callback |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/documents/upload` | Upload file |
| GET | `/api/documents` | List documents |
| GET | `/api/documents/{id}` | Get document |
| DELETE | `/api/documents/{id}` | Delete document |
| GET | `/api/documents/{id}/summary` | Get summary |
| POST | `/api/documents/{id}/summary` | Regenerate summary |
| POST | `/api/chat/sessions` | Create chat session |
| GET | `/api/chat/sessions` | List sessions |
| POST | `/api/chat/sessions/{id}/messages` | Send message (SSE) |
| GET | `/api/chat/sessions/{id}/messages` | Get chat history |
| GET | `/api/media/{id}` | Stream media file |
| GET | `/api/media/{id}/transcript` | Get transcript |

Full interactive docs at `/api/docs` (Swagger UI).

## 🧪 Testing

```bash
# Backend (95%+ coverage required)
cd backend
pytest --cov=app --cov-report=html --cov-fail-under=95 -v

# Frontend
cd frontend
npm run test -- --coverage
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| LLM | LangChain, OpenAI GPT-4o |
| Transcription | OpenAI Whisper API |
| Vector Store | FAISS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Frontend | React 18, TypeScript, Vite |
| Auth | Google OAuth 2.0, JWT |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions |

## 📄 License

MIT
# Deployment triggered
# CI/CD fix
