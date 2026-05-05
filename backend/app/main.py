"""
DocQA AI — Main FastAPI Application

An AI-powered document and multimedia Q&A web application.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, close_db
from app.redis_client import close_redis
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.api import auth, upload, chat, summary, media

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    await init_db()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.FAISS_INDEX_DIR).mkdir(parents=True, exist_ok=True)
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    # Shutdown
    await close_db()
    await close_redis()
    print(f"👋 {settings.APP_NAME} stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered document and multimedia Q&A application",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Register API routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(summary.router)
app.include_router(media.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
