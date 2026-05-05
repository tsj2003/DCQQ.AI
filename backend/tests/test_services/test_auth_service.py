"""
Tests for auth service — Google OAuth and JWT.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.auth_service import (
    create_access_token,
    verify_access_token,
    get_google_auth_url,
    exchange_google_code,
    get_or_create_user,
    get_user_by_id,
)
from app.models.user import User


class TestCreateAccessToken:
    def test_creates_valid_token(self):
        user_id = str(uuid.uuid4())
        token, expires_in = create_access_token(user_id, "test@test.com")
        assert token is not None
        assert isinstance(token, str)
        assert expires_in > 0

    def test_token_contains_user_id(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@test.com")
        payload = verify_access_token(token)
        assert payload["sub"] == user_id

    def test_token_contains_email(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@test.com")
        payload = verify_access_token(token)
        assert payload["email"] == "test@test.com"


class TestVerifyAccessToken:
    def test_verifies_valid_token(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@test.com")
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

    def test_rejects_invalid_token(self):
        payload = verify_access_token("invalid.token.here")
        assert payload is None

    def test_rejects_tampered_token(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@test.com")
        tampered = token[:-10] + "tampered!!"
        payload = verify_access_token(tampered)
        assert payload is None


class TestGetGoogleAuthUrl:
    def test_returns_google_url(self):
        with patch("app.services.auth_service.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
            mock_settings.GOOGLE_REDIRECT_URI = "http://localhost/callback"

            url = get_google_auth_url()
            assert "accounts.google.com" in url
            assert "test-client-id" in url
            assert "http://localhost/callback" in url


class TestExchangeGoogleCode:
    @pytest.mark.asyncio
    async def test_exchanges_code_for_user_info(self):
        mock_token_response = MagicMock()
        mock_token_response.raise_for_status = MagicMock()
        mock_token_response.json.return_value = {"access_token": "fake_token"}

        mock_user_response = MagicMock()
        mock_user_response.raise_for_status = MagicMock()
        mock_user_response.json.return_value = {
            "email": "test@test.com",
            "name": "Test User",
            "picture": "http://example.com/avatar.png",
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_token_response)
        mock_client.get = AsyncMock(return_value=mock_user_response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch("app.services.auth_service.settings") as mock_settings:
                mock_settings.GOOGLE_CLIENT_ID = "test-client-id"
                mock_settings.GOOGLE_CLIENT_SECRET = "test-secret"
                mock_settings.GOOGLE_REDIRECT_URI = "http://localhost/callback"

                result = await exchange_google_code("fake_code")

        assert result["email"] == "test@test.com"
        assert result["name"] == "Test User"


class TestGetOrCreateUser:
    @pytest.mark.asyncio
    async def test_creates_new_user(self):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        google_user = {
            "email": "new@test.com",
            "name": "New User",
            "picture": "http://example.com/avatar.png",
        }

        _user = await get_or_create_user(mock_db, google_user)

        assert mock_db.add.called
        assert mock_db.flush.called

    @pytest.mark.asyncio
    async def test_returns_existing_user(self):
        existing_user = User(
            id=uuid.uuid4(),
            email="existing@test.com",
            name="Existing User",
        )

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        google_user = {
            "email": "existing@test.com",
            "name": "Updated Name",
        }

        user = await get_or_create_user(mock_db, google_user)

        assert user.email == "existing@test.com"
        assert not mock_db.add.called


class TestGetUserById:
    @pytest.mark.asyncio
    async def test_returns_user_by_id(self):
        user_id = str(uuid.uuid4())
        existing_user = User(id=uuid.UUID(user_id), email="test@test.com")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute.return_value = mock_result

        user = await get_user_by_id(mock_db, user_id)

        assert user is not None
        assert str(user.id) == user_id

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_id(self):
        mock_db = AsyncMock()

        user = await get_user_by_id(mock_db, "invalid-uuid")

        assert user is None

    @pytest.mark.asyncio
    async def test_returns_none_if_not_found(self):
        user_id = str(uuid.uuid4())

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user = await get_user_by_id(mock_db, user_id)

        assert user is None
