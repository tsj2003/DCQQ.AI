"""
JWT authentication middleware.
"""

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_service import verify_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Extract and verify user ID from JWT token.

    Returns:
        User ID string from the JWT payload.

    Raises:
        HTTPException: If token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    return user_id


async def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """Optionally extract user ID — returns None if no token provided."""
    if credentials is None:
        return None

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        return None

    return payload.get("sub")


class AuthMiddleware:
    """Middleware that sets user_id on request state for rate limiting."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            from starlette.requests import Request
            request = Request(scope, receive)

            # Try to extract user from Authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = verify_access_token(token)
                if payload:
                    scope.setdefault("state", {})
                    scope["state"]["user_id"] = payload.get("sub")

        await self.app(scope, receive, send)
