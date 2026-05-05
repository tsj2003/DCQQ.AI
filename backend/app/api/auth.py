"""
Authentication API endpoints — Google OAuth + JWT.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from app.schemas.auth import TokenResponse, UserResponse
from app.services.auth_service import (
    create_access_token,
    exchange_google_code,
    get_google_auth_url,
    get_or_create_user,
    get_user_by_id,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/google")
async def google_login():
    """Redirect user to Google OAuth consent screen."""
    auth_url = get_google_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback — exchange code for JWT.

    Args:
        code: Authorization code from Google.

    Returns:
        JWT access token.
    """
    try:
        google_user = await exchange_google_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {str(e)}")

    user = await get_or_create_user(db, google_user)
    token, expires_in = create_access_token(str(user.id), user.email)

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
    )


@router.post("/guest", response_model=TokenResponse)
async def guest_login(
    db: AsyncSession = Depends(get_db),
):
    """Bypass OAuth and log in as a guest user for testing/evaluation."""
    guest_data = {
        "email": "guest@docqa.ai",
        "name": "Guest Evaluator",
        "picture": "https://api.dicebear.com/7.x/avataaars/svg?seed=Guest",
    }
    user = await get_or_create_user(db, guest_data)
    token, expires_in = create_access_token(str(user.id), user.email)

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the current authenticated user's profile."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Refresh the JWT token."""
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    token, expires_in = create_access_token(str(user.id), user.email)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
    )
