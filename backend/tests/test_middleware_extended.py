"""
Extended tests for middleware.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.middleware.rate_limiter import RateLimitMiddleware


@pytest.mark.asyncio
async def test_rate_limit_middleware_skips_without_user_id():
    """Test that rate limit middleware skips if no user_id in state."""

    async def call_next(request):
        response = MagicMock()
        response.headers = {}
        return response

    middleware = RateLimitMiddleware(MagicMock())

    request = MagicMock()
    request.url.path = "/api/chat"
    request.method = "POST"
    request.state.user_id = None  # No user ID

    with patch("app.middleware.rate_limiter.check_rate_limit") as mock_check:
        _response = await middleware.dispatch(request, call_next)

    # Should not call check_rate_limit when user_id is None
    mock_check.assert_not_called()
