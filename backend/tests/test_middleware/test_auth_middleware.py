"""
Tests for authentication middleware.
"""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import patch, MagicMock

from app.middleware.auth_middleware import get_current_user_id, get_optional_user_id, AuthMiddleware


@pytest.mark.asyncio
async def test_get_current_user_id_success():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    
    with patch("app.middleware.auth_middleware.verify_access_token") as mock_verify:
        mock_verify.return_value = {"sub": "user_123"}
        user_id = await get_current_user_id(creds)
        assert user_id == "user_123"


@pytest.mark.asyncio
async def test_get_current_user_id_missing():
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Authentication required"


@pytest.mark.asyncio
async def test_get_current_user_id_invalid():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")
    
    with patch("app.middleware.auth_middleware.verify_access_token") as mock_verify:
        mock_verify.return_value = None
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(creds)
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or expired token"


@pytest.mark.asyncio
async def test_get_optional_user_id():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    
    with patch("app.middleware.auth_middleware.verify_access_token") as mock_verify:
        mock_verify.return_value = {"sub": "user_123"}
        user_id = await get_optional_user_id(creds)
        assert user_id == "user_123"
        
        # Test no creds
        assert await get_optional_user_id(None) is None
        
        # Test invalid creds
        mock_verify.return_value = None
        assert await get_optional_user_id(creds) is None


@pytest.mark.asyncio
async def test_auth_middleware():
    async def mock_app(scope, receive, send):
        pass
        
    middleware = AuthMiddleware(mock_app)
    
    scope = {
        "type": "http",
        "headers": [(b"authorization", b"Bearer valid_token")],
        "state": {}
    }
    
    with patch("app.middleware.auth_middleware.verify_access_token") as mock_verify:
        mock_verify.return_value = {"sub": "user_123"}
        await middleware(scope, MagicMock(), MagicMock())
        
        assert scope["state"]["user_id"] == "user_123"
