"""
Tests for rate limiter middleware.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock

from app.middleware.rate_limiter import check_rate_limit, RateLimitMiddleware


@pytest.mark.asyncio
async def test_check_rate_limit_allowed(mock_redis):
    """Request within limit should be allowed."""
    # Override execute to return count = 1
    mock_redis.pipeline.return_value.execute.return_value = [0, 1, 1, True]

    with patch("app.middleware.rate_limiter.redis_client", mock_redis):
        result = await check_rate_limit("user1", "chat", 10, 60)

    assert result["allowed"] is True
    assert result["remaining"] == 9
    assert "reset" in result


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(mock_redis):
    """Request exceeding limit should raise 429."""
    mock_redis.pipeline.return_value.execute.return_value = [0, 1, 11, True]

    with patch("app.middleware.rate_limiter.redis_client", mock_redis):
        with pytest.raises(HTTPException) as exc:
            await check_rate_limit("user1", "chat", 10, 60)

    assert exc.value.status_code == 429
    assert exc.value.detail["error"] == "Rate limit exceeded"
    assert exc.value.detail["limit"] == 10


@pytest.mark.asyncio
async def test_rate_limit_middleware_pass():
    """Middleware should add rate limit headers on POST."""

    async def call_next(request):
        response = MagicMock()
        response.headers = {}
        return response

    middleware = RateLimitMiddleware(MagicMock())

    request = MagicMock()
    request.url.path = "/api/chat"
    request.method = "POST"
    request.state.user_id = "user1"

    with patch("app.middleware.rate_limiter.check_rate_limit") as mock_check:
        mock_check.return_value = {"allowed": True, "remaining": 5, "reset": 100}

        response = await middleware.dispatch(request, call_next)

    assert response.headers["X-RateLimit-Remaining"] == "5"
    assert response.headers["X-RateLimit-Reset"] == "100"
    mock_check.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_middleware_skip_get():
    """Middleware should skip rate limiting for GET requests."""

    async def call_next(request):
        return "response"

    middleware = RateLimitMiddleware(MagicMock())

    request = MagicMock()
    request.url.path = "/api/chat"
    request.method = "GET"
    request.state.user_id = "user1"

    with patch("app.middleware.rate_limiter.check_rate_limit") as mock_check:
        response = await middleware.dispatch(request, call_next)

    assert response == "response"
    mock_check.assert_not_called()
