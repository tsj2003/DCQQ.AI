"""
Redis-based sliding window rate limiter middleware.
"""

import time

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.redis_client import redis_client

settings = get_settings()

# Rate limit configurations: {path_prefix: (limit, window_seconds)}
RATE_LIMITS = {
    "/api/chat": (settings.RATE_LIMIT_CHAT, 60),  # 30 req/min
    "/api/documents/upload": (settings.RATE_LIMIT_UPLOAD, 3600),  # 10/hour
}


async def check_rate_limit(user_id: str, action: str, limit: int, window: int) -> dict:
    """Check if request is within rate limit using sliding window.

    Args:
        user_id: User identifier.
        action: Action identifier (e.g., 'chat', 'upload').
        limit: Maximum requests allowed in window.
        window: Time window in seconds.

    Returns:
        Dict with 'allowed', 'remaining', 'reset' keys.

    Raises:
        HTTPException: If rate limit exceeded.
    """
    key = f"rate:{action}:{user_id}"
    now = time.time()

    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)
    results = await pipe.execute()

    count = results[2]
    remaining = max(0, limit - count)

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": limit,
                "window_seconds": window,
                "retry_after": window,
            },
        )

    return {
        "allowed": True,
        "remaining": remaining,
        "reset": int(now + window),
    }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that applies rate limiting based on request path."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for non-API routes
        path = request.url.path

        # Find matching rate limit rule
        matched_rule = None
        for prefix, (limit, window) in RATE_LIMITS.items():
            if path.startswith(prefix):
                matched_rule = (prefix, limit, window)
                break

        if matched_rule and request.method in ("POST", "PUT", "PATCH"):
            # Extract user ID from JWT (already set by auth middleware)
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                prefix, limit, window = matched_rule
                action = prefix.replace("/api/", "").replace("/", "_")
                rate_info = await check_rate_limit(user_id, action, limit, window)

                response = await call_next(request)
                response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
                return response

        return await call_next(request)
