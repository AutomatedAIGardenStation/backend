import pytest
from unittest.mock import AsyncMock, patch
from app.core.session import get_db
import sqlalchemy.ext.asyncio

@pytest.mark.asyncio
async def test_get_db_yields_session():
    # We mock AsyncSessionLocal so it doesn't try to connect to an actual DB in unit test
    with patch('app.core.session.AsyncSessionLocal') as mock_session_local:
        # Mock the session instance that is yielded
        mock_session = AsyncMock(spec=sqlalchemy.ext.asyncio.AsyncSession)
        # Configure the async context manager on mock_session_local return value
        mock_session_local.return_value.__aenter__.return_value = mock_session

        # Test the dependency generator
        gen = get_db()
        session = await gen.__anext__()

        assert session is mock_session

        # Finish the generator loop
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

        # Verify that the context manager entered and exited correctly
        mock_session_local.return_value.__aenter__.assert_called_once()
        mock_session_local.return_value.__aexit__.assert_called_once()
