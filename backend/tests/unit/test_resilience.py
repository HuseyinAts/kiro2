import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from core.resilience import db_retry

@pytest.mark.asyncio
async def test_db_retry_success():
    """Test that a successful DB operation does not retry and returns the result."""
    mock_db = AsyncMock()
    
    class DummyService:
        def __init__(self):
            self.db = mock_db
            self.calls = 0
            
        @db_retry
        async def work(self):
            self.calls += 1
            return "ok"
            
    service = DummyService()
    result = await service.work()
    
    assert result == "ok"
    assert service.calls == 1
    mock_db.rollback.assert_not_called()

@pytest.mark.asyncio
async def test_db_retry_rollback_on_failure():
    """Test that an exception triggers rollback and retries up to max_attempts."""
    mock_db = AsyncMock()
    # Mock rollback to return a coroutine
    mock_db.rollback = AsyncMock()
    
    class DummyService:
        def __init__(self):
            self.db = mock_db
            self.calls = 0
            
        @db_retry(max_attempts=3, wait_seconds=0)
        async def work(self):
            self.calls += 1
            raise SQLAlchemyError("Mock DB Error")
            
    service = DummyService()
    
    with pytest.raises(SQLAlchemyError):
        await service.work()
        
    assert service.calls == 3
    assert mock_db.rollback.call_count == 3

@pytest.mark.asyncio
async def test_db_retry_no_retry_on_other_exceptions():
    """Test that non-SQLAlchemyError exceptions are raised immediately without retry."""
    mock_db = AsyncMock()
    
    class DummyService:
        def __init__(self):
            self.db = mock_db
            self.calls = 0
            
        @db_retry(max_attempts=3, wait_seconds=0)
        async def work(self):
            self.calls += 1
            raise ValueError("Generic Error")
            
    service = DummyService()
    
    with pytest.raises(ValueError):
        await service.work()
        
    assert service.calls == 1
    mock_db.rollback.assert_not_called()
