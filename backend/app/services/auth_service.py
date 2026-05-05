"""
Authentication service — JWT generation/verification + Google OAuth.
"""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User

settings = get_settings()

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


def create_access_token(user_id: str, email: str) -> tuple[str, int]:
    """Create a JWT access token.

    Returns:
        Tuple of (token_string, expires_in_seconds)
    """
    expires_delta = timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def verify_access_token(token: str) -> dict | None:
    """Verify and decode a JWT access token.

    Returns:
        Decoded payload dict, or None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def get_google_auth_url() -> str:
    """Generate the Google OAuth authorization URL."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


async def exchange_google_code(code: str) -> dict:
    """Exchange Google authorization code for tokens and user info."""
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        token_response = await client.post(GOOGLE_TOKEN_URL, data=token_data)
        token_response.raise_for_status()
        tokens = token_response.json()

        # Get user info
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        user_response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
        user_response.raise_for_status()
        return user_response.json()


async def get_or_create_user(db: AsyncSession, google_user: dict) -> User:
    """Get existing user or create new one from Google OAuth data."""
    email = google_user["email"]

    # Try to find existing user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            name=google_user.get("name"),
            avatar_url=google_user.get("picture"),
            provider="google",
        )
        db.add(user)
        await db.flush()

    return user


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Get user by their UUID."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None

    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()
