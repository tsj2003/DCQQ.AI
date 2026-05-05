"""
Tests for redis client module.
"""

import pytest
from unittest.mock import patch, AsyncMock

from app.redis_client import close_redis


@pytest.mark.asyncio
async def test_close_redis():
    """Test redis connection close."""
    with patch("app.redis_client.redis_client") as mock_redis:
        mock_redis.close = AsyncMock()
        
        await close_redis()
        
        mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_close_redis_error():
    """Test redis close error handling."""
    with patch("app.redis_client.redis_client.close", side_effect=Exception("Connection error")):
        # The function doesn't catch errors, so this should raise
        with pytest.raises(Exception, match="Connection error"):
            await close_redis()
