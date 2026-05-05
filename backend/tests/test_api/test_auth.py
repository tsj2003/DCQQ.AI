"""
Tests for auth API endpoints.
"""

import uuid

import pytest
from unittest.mock import patch, MagicMock

from app.main import app
from tests.conftest import override_db


@pytest.mark.asyncio
async def test_get_google_auth_url(async_client):
    """Google auth endpoint should redirect to Google OAuth."""
    response = await async_client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code == 307
    assert "accounts.google.com" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_auth_callback_success(async_client):
    """Google callback should exchange code and return JWT."""
    with patch("app.api.auth.exchange_google_code") as mock_exchange:
        with patch("app.api.auth.get_or_create_user") as mock_get_or_create:
            with patch("app.api.auth.create_access_token") as mock_create_token:
                mock_exchange.return_value = {
                    "email": "test@test.com",
                    "name": "Test User",
                    "picture": "http://example.com/avatar.png",
                }

                mock_user = MagicMock()
                mock_user.id = uuid.uuid4()
                mock_user.email = "test@test.com"
                mock_get_or_create.return_value = mock_user

                mock_create_token.return_value = ("fake_token", 3600)

                response = await async_client.get(
                    "/api/auth/google/callback?code=fake_code"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["access_token"] == "fake_token"
                assert data["expires_in"] == 3600


@pytest.mark.asyncio
async def test_get_me_success(async_client, override_auth):
    """Authenticated user can retrieve their profile."""
    with patch("app.api.auth.get_user_by_id") as mock_get_user:
        mock_user = MagicMock()
        mock_user.id = uuid.UUID(override_auth)
        mock_user.email = "test@test.com"
        mock_user.name = "Test User"
        mock_user.avatar_url = "http://example.com/avatar.png"
        mock_user.provider = "google"
        mock_user.created_at = "2024-01-01T00:00:00Z"
        mock_get_user.return_value = mock_user

        response = await async_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@test.com"
        assert data["name"] == "Test User"


@pytest.mark.asyncio
async def test_guest_login(async_client, mock_db_session):
    """Guest login should create a guest user and return token."""
    override_db(mock_db_session)
    
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "guest@docqa.ai"
    
    with patch("app.api.auth.get_or_create_user") as mock_get_or_create:
        mock_get_or_create.return_value = mock_user
        
        response = await async_client.post("/api/auth/guest")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_refresh_token(async_client, override_auth, mock_db_session):
    """Refresh token should return new token."""
    override_db(mock_db_session)
    
    mock_user = MagicMock()
    mock_user.id = uuid.UUID(override_auth)
    mock_user.email = "test@test.com"
    
    with patch("app.api.auth.get_user_by_id") as mock_get_user:
        mock_get_user.return_value = mock_user
        
        response = await async_client.post("/api/auth/refresh")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_refresh_token_user_not_found(async_client, override_auth, mock_db_session):
    """Refresh token for non-existent user should 404."""
    override_db(mock_db_session)
    
    with patch("app.api.auth.get_user_by_id") as mock_get_user:
        mock_get_user.return_value = None
        
        response = await async_client.post("/api/auth/refresh")
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_auth_callback_oauth_failure(async_client, mock_db_session):
    """OAuth callback failure should return 400."""
    override_db(mock_db_session)
    
    with patch("app.api.auth.exchange_google_code") as mock_exchange:
        mock_exchange.side_effect = Exception("OAuth error")
        
        response = await async_client.get("/api/auth/google/callback?code=invalid")
        
        assert response.status_code == 400
        assert "OAuth failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_user_not_found(async_client, override_auth, mock_db_session):
    """Get current user when user doesn't exist should 404."""
    override_db(mock_db_session)
    
    with patch("app.api.auth.get_user_by_id") as mock_get_user:
        mock_get_user.return_value = None
        
        response = await async_client.get("/api/auth/me")
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
