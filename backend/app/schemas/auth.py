"""
Pydantic schemas for authentication.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User profile response."""

    id: UUID
    email: str
    name: str | None
    avatar_url: str | None
    provider: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GoogleAuthCallback(BaseModel):
    """Google OAuth callback data."""

    code: str
    state: str | None = None
