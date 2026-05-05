"""
Pytest configuration and shared fixtures.
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.database import Base, get_db
from app.middleware.auth_middleware import get_current_user_id, get_optional_user_id
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def async_client():
    """Provide an async HTTP client wired to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    # Always clean up overrides after each test
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """Generic mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def override_auth():
    """Override auth dependency to always return a fixed user id."""
    user_id = "00000000-0000-0000-0000-000000000000"

    async def _override():
        return user_id

    app.dependency_overrides[get_current_user_id] = _override
    yield user_id
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def override_optional_auth():
    """Override optional auth dependency."""
    user_id = "00000000-0000-0000-0000-000000000000"

    async def _override():
        return user_id

    app.dependency_overrides[get_optional_user_id] = _override
    yield user_id
    app.dependency_overrides.pop(get_optional_user_id, None)


def override_db(mock_session):
    """Create a db dependency override that yields the mock session."""
    async def _override():
        yield mock_session

    app.dependency_overrides[get_db] = _override


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Provide test settings."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///test.db",
        REDIS_URL="redis://localhost:6379/1",
        JWT_SECRET_KEY="test-secret-key",
        OPENAI_API_KEY="sk-test-key",
        UPLOAD_DIR="./test_uploads",
        FAISS_INDEX_DIR="./test_faiss",
    )


@pytest.fixture
def mock_user_id():
    """Provide a test user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_document_id():
    """Provide a test document ID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_redis():
    """Mock Redis client with properly awaitable pipeline."""
    redis = MagicMock()
    # pipeline() in redis.asyncio is a sync call that returns a Pipeline object
    mock_pipe = MagicMock()
    mock_pipe.zremrangebyscore = MagicMock(return_value=mock_pipe)
    mock_pipe.zadd = MagicMock(return_value=mock_pipe)
    mock_pipe.zcard = MagicMock(return_value=mock_pipe)
    mock_pipe.expire = MagicMock(return_value=mock_pipe)
    mock_pipe.execute = AsyncMock(return_value=[0, 1, 1, True])
    redis.pipeline = MagicMock(return_value=mock_pipe)
    return redis


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("app.services.embedding.AsyncOpenAI") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_pdf_pages():
    """Sample PDF page data."""
    return [
        {"page": 1, "text": "This is page one content about machine learning and AI."},
        {"page": 2, "text": "This is page two content about deep learning neural networks."},
        {"page": 3, "text": "This is page three about natural language processing and transformers."},
    ]


@pytest.fixture
def sample_transcript():
    """Sample transcription data."""
    return {
        "segments": [
            {"id": 0, "start": 0.0, "end": 5.0, "text": "Welcome to the presentation."},
            {"id": 1, "start": 5.0, "end": 12.0, "text": "Today we will discuss machine learning."},
            {"id": 2, "start": 12.0, "end": 20.0, "text": "Neural networks are a key technology."},
        ],
        "full_text": "Welcome to the presentation. Today we will discuss machine learning. Neural networks are a key technology.",
    }


@pytest.fixture
def sample_chunks():
    """Sample text chunks with metadata."""
    return [
        {
            "text": "Machine learning is a subset of AI.",
            "metadata": {"page": 1, "chunk_index": 0, "source_type": "pdf"},
        },
        {
            "text": "Deep learning uses neural networks.",
            "metadata": {"page": 2, "chunk_index": 1, "source_type": "pdf"},
        },
    ]
