"""
Tests for authentication service.
"""

import uuid


from app.services.auth_service import (
    create_access_token,
    verify_access_token,
    get_google_auth_url,
)


class TestCreateAccessToken:
    def test_creates_valid_token(self):
        user_id = str(uuid.uuid4())
        token, expires_in = create_access_token(user_id, "test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0
        assert expires_in > 0

    def test_token_contains_user_id(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@example.com")
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

    def test_token_contains_email(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@example.com")
        payload = verify_access_token(token)
        assert payload["email"] == "test@example.com"


class TestVerifyAccessToken:
    def test_verifies_valid_token(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@example.com")
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

    def test_rejects_invalid_token(self):
        payload = verify_access_token("invalid-token")
        assert payload is None

    def test_rejects_tampered_token(self):
        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id, "test@example.com")
        tampered = token[:-5] + "XXXXX"
        payload = verify_access_token(tampered)
        assert payload is None


class TestGetGoogleAuthUrl:
    def test_returns_google_url(self):
        url = get_google_auth_url()
        assert "accounts.google.com" in url
        assert "response_type=code" in url
