"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables or .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "DocQA AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, production

    # CORS - dynamically set based on environment
    ALLOWED_ORIGINS: list[str] = []

    # GCP Settings
    GCP_PROJECT_ID: str = ""
    GCP_STORAGE_BUCKET: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set default CORS origins if not provided
        if not self.ALLOWED_ORIGINS:
            if self.ENVIRONMENT == "production":
                self.ALLOWED_ORIGINS = ["*"]  # Cloud Run handles this
            else:
                self.ALLOWED_ORIGINS = [
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://localhost:5173",
                    "http://localhost:8001",
                ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://docqa:docqa_password@localhost:5432/docqa"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 100

    # Rate Limiting
    RATE_LIMIT_CHAT: int = 30  # requests per minute
    RATE_LIMIT_UPLOAD: int = 10  # uploads per hour

    # Vector Store
    FAISS_INDEX_DIR: str = "./faiss_indices"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
