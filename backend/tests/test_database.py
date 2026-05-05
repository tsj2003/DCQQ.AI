"""
Tests for database module.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.database import init_db, close_db, get_db


@pytest.mark.asyncio
async def test_init_db():
    """Test database initialization."""
    with patch("app.database.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_conn.run_sync = AsyncMock()
        mock_engine.begin = MagicMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=False)
        
        await init_db()
        
        # Should not raise any errors


@pytest.mark.asyncio
async def test_init_db_error():
    """Test database initialization error handling."""
    with patch("app.database.engine") as mock_engine:
        mock_engine.begin = MagicMock(side_effect=Exception("DB Error"))
        
        # Should not raise - errors are caught and printed
        await init_db()


@pytest.mark.asyncio
async def test_close_db():
    """Test database shutdown."""
    with patch("app.database.engine") as mock_engine:
        mock_engine.dispose = AsyncMock()
        
        await close_db()
        
        mock_engine.dispose.assert_called_once()


@pytest.mark.asyncio
async def test_get_db():
    """Test database session dependency."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    
    with patch("app.database.async_session") as mock_session_maker:
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)
        
        async for session in get_db():
            assert session is mock_session


