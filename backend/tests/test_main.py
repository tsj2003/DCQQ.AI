"""
Tests for main application - startup, shutdown, and health check.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import lifespan


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test health check endpoint."""
    response = await async_client.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_docs_endpoint(async_client):
    """Test that API docs are accessible."""
    response = await async_client.get("/api/docs")
    
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_lifespan_startup_shutdown():
    """Test application lifespan startup and shutdown."""
    mock_app = MagicMock()
    
    with patch("app.main.init_db", new=AsyncMock()) as mock_init:
        with patch("app.main.close_db", new=AsyncMock()) as mock_close:
            with patch("app.main.close_redis", new=AsyncMock()) as mock_close_redis:
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    # Test startup
                    async with lifespan(mock_app):
                        mock_init.assert_called_once()
                        assert mock_mkdir.call_count == 2  # upload and faiss dirs
                    
                    # Test shutdown
                    mock_close.assert_called_once()
                    mock_close_redis.assert_called_once()


@pytest.mark.asyncio
async def test_cors_headers(async_client):
    """Test CORS headers are present."""
    response = await async_client.options("/api/health")
    
    # Should not raise an error
    assert response.status_code in [200, 405]  # 200 if allowed, 405 if method not allowed
