"""
Test for Database Connection and Session Management
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_async_engine():
    """Mock async database engine"""
    engine = AsyncMock()
    engine.begin = AsyncMock()
    engine.dispose = AsyncMock()
    engine.pool.size.return_value = 10
    engine.pool.checkedout.return_value = 2
    return engine


@pytest.fixture
def mock_sync_engine():
    """Mock sync database engine"""
    engine = MagicMock()
    engine.dispose = MagicMock()
    return engine


@pytest.fixture
def mock_async_session():
    """Mock async session"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_sync_session():
    """Mock sync session"""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


class TestDatabaseConfiguration:
    """Test database configuration"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_database_url(self):
        """Test default database URL"""
        # Re-import to get fresh environment
        import importlib
        import backend.database.connection
        importlib.reload(backend.database.connection)
        
        from backend.database.connection import DATABASE_URL, SYNC_DATABASE_URL
        
        assert "postgresql+asyncpg://" in DATABASE_URL
        assert "teknofest" in DATABASE_URL
        assert "postgresql://" in SYNC_DATABASE_URL
        assert "asyncpg" not in SYNC_DATABASE_URL
    
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql+asyncpg://test:test@test:5432/test_db'})
    def test_custom_database_url(self):
        """Test custom database URL from environment"""
        import importlib
        import backend.database.connection
        importlib.reload(backend.database.connection)
        
        from backend.database.connection import DATABASE_URL, SYNC_DATABASE_URL
        
        assert DATABASE_URL == 'postgresql+asyncpg://test:test@test:5432/test_db'
        assert SYNC_DATABASE_URL == 'postgresql://test:test@test:5432/test_db'


class TestDatabaseManager:
    """Test DatabaseManager class"""
    
    @patch('backend.database.connection.async_engine')
    @patch('backend.database.connection.sync_engine')
    def test_database_manager_initialization(self, mock_sync_engine, mock_async_engine):
        """Test database manager initialization"""
        from backend.database.connection import DatabaseManager
        
        db_manager = DatabaseManager()
        
        assert db_manager.async_engine is not None
        assert db_manager.sync_engine is not None
        assert db_manager.async_session_factory is not None
        assert db_manager.sync_session_factory is not None
    
    @patch('backend.database.connection.async_engine')
    @patch('backend.database.connection.Base')
    @pytest.mark.asyncio
    async def test_create_tables(self, mock_base, mock_engine):
        """Test creating tables"""
        from backend.database.connection import DatabaseManager
        
        # Mock the async context manager
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager = DatabaseManager()
        db_manager.async_engine = mock_engine
        
        await db_manager.create_tables()
        
        mock_engine.begin.assert_called_once()
        mock_conn.run_sync.assert_called_once()
    
    @patch('backend.database.connection.async_engine')
    @patch('backend.database.connection.Base')
    @pytest.mark.asyncio
    async def test_drop_tables(self, mock_base, mock_engine):
        """Test dropping tables"""
        from backend.database.connection import DatabaseManager
        
        # Mock the async context manager
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager = DatabaseManager()
        db_manager.async_engine = mock_engine
        
        await db_manager.drop_tables()
        
        mock_engine.begin.assert_called_once()
        mock_conn.run_sync.assert_called_once()
    
    @patch('backend.database.connection.sync_engine')
    @patch('backend.database.connection.Base')
    def test_create_tables_sync(self, mock_base, mock_engine):
        """Test creating tables synchronously"""
        from backend.database.connection import DatabaseManager
        
        db_manager = DatabaseManager()
        db_manager.sync_engine = mock_engine
        
        db_manager.create_tables_sync()
        
        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('backend.database.connection.async_engine')
    @pytest.mark.asyncio
    async def test_check_connection_success(self, mock_engine):
        """Test successful connection check"""
        from backend.database.connection import DatabaseManager
        
        # Mock the async context manager
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        
        db_manager = DatabaseManager()
        db_manager.async_engine = mock_engine
        
        result = await db_manager.check_connection()
        
        assert result is True
        mock_engine.begin.assert_called_once()
        mock_conn.execute.assert_called_once()
    
    @patch('backend.database.connection.async_engine')
    @pytest.mark.asyncio
    async def test_check_connection_failure(self, mock_engine):
        """Test failed connection check"""
        from backend.database.connection import DatabaseManager
        
        # Mock the async context manager to raise exception
        mock_engine.begin.side_effect = Exception("Connection failed")
        
        db_manager = DatabaseManager()
        db_manager.async_engine = mock_engine
        
        result = await db_manager.check_connection()
        
        assert result is False
    
    @patch('backend.database.connection.async_engine')
    @pytest.mark.asyncio
    async def test_get_table_info_success(self, mock_engine):
        """Test getting table info successfully"""
        from backend.database.connection import DatabaseManager
        
        # Mock the async context manager and results
        mock_conn = AsyncMock()
        mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Mock table count result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5
        
        # Mock table names result
        mock_names_result = MagicMock()
        mock_names_result.fetchall.return_value = [('users',), ('posts',), ('comments',)]
        
        mock_conn.execute.side_effect = [mock_count_result, mock_names_result]
        
        db_manager = DatabaseManager()
        db_manager.async_engine = mock_engine
        
        result = await db_manager.get_table_info()
        
        assert result['table_count'] == 5
        assert result['table_names'] == ['users', 'posts', 'comments']
        assert result['status'] == 'connected'
    
    @patch('backend.database.connection.async_engine')
    @pytest.mark.asyncio
    async def test_get_table_info_failure(self, mock_engine):
        """Test getting table info with failure"""
        from backend.database.connection import DatabaseManager
        
        mock_engine.begin.side_effect = Exception("Database error")
        
        db_manager = DatabaseManager()
        db_manager.async_engine = mock_engine
        
        result = await db_manager.get_table_info()
        
        assert result['table_count'] == 0
        assert result['table_names'] == []
        assert result['status'] == 'error'
        assert 'error' in result


class TestSessionManagement:
    """Test session management functions"""
    
    @patch('backend.database.connection.AsyncSessionLocal')
    @pytest.mark.asyncio
    async def test_get_async_session_success(self, mock_session_factory, mock_async_session):
        """Test async session dependency injection success"""
        from backend.database.connection import get_async_session
        
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        async for session in get_async_session():
            assert session == mock_async_session
            break
        
        mock_async_session.close.assert_called_once()
    
    @patch('backend.database.connection.AsyncSessionLocal')
    @pytest.mark.asyncio
    async def test_get_async_session_error(self, mock_session_factory, mock_async_session):
        """Test async session dependency injection with error"""
        from backend.database.connection import get_async_session
        
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        try:
            async for session in get_async_session():
                # Simulate an error during session use
                raise Exception("Session error")
        except Exception:
            pass
        
        mock_async_session.rollback.assert_called_once()
        mock_async_session.close.assert_called_once()
    
    @patch('backend.database.connection.AsyncSessionLocal')
    @pytest.mark.asyncio
    async def test_get_async_session_context(self, mock_session_factory, mock_async_session):
        """Test async session context manager"""
        from backend.database.connection import get_async_session_context
        
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        async with get_async_session_context() as session:
            assert session == mock_async_session
        
        mock_async_session.commit.assert_called_once()
        mock_async_session.close.assert_called_once()
    
    @patch('backend.database.connection.AsyncSessionLocal')
    @pytest.mark.asyncio
    async def test_get_async_session_context_error(self, mock_session_factory, mock_async_session):
        """Test async session context manager with error"""
        from backend.database.connection import get_async_session_context
        
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        try:
            async with get_async_session_context() as session:
                raise Exception("Context error")
        except Exception:
            pass
        
        mock_async_session.rollback.assert_called_once()
        mock_async_session.close.assert_called_once()
    
    @patch('backend.database.connection.SessionLocal')
    def test_get_sync_session(self, mock_session_factory, mock_sync_session):
        """Test sync session creation"""
        from backend.database.connection import get_sync_session
        
        mock_session_factory.return_value = mock_sync_session
        
        session = get_sync_session()
        
        assert session == mock_sync_session
        mock_session_factory.assert_called_once()


class TestDatabaseInitialization:
    """Test database initialization functions"""
    
    @patch('backend.database.connection.db_manager')
    @pytest.mark.asyncio
    async def test_init_database_success(self, mock_db_manager):
        """Test successful database initialization"""
        from backend.database.connection import init_database
        
        mock_db_manager.check_connection = AsyncMock(return_value=True)
        mock_db_manager.create_tables = AsyncMock()
        mock_db_manager.get_table_info = AsyncMock(return_value={
            'table_count': 10,
            'table_names': ['users', 'posts']
        })
        
        await init_database()
        
        mock_db_manager.check_connection.assert_called_once()
        mock_db_manager.create_tables.assert_called_once()
        mock_db_manager.get_table_info.assert_called_once()
    
    @patch('backend.database.connection.db_manager')
    @pytest.mark.asyncio
    async def test_init_database_connection_failure(self, mock_db_manager):
        """Test database initialization with connection failure"""
        from backend.database.connection import init_database
        
        mock_db_manager.check_connection = AsyncMock(return_value=False)
        
        with pytest.raises(Exception, match="Database bağlantısı kurulamadı"):
            await init_database()
    
    @patch('backend.database.connection.async_engine')
    @patch('backend.database.connection.sync_engine')
    @pytest.mark.asyncio
    async def test_cleanup_database(self, mock_sync_engine, mock_async_engine):
        """Test database cleanup"""
        from backend.database.connection import cleanup_database
        
        mock_async_engine.dispose = AsyncMock()
        mock_sync_engine.dispose = MagicMock()
        
        await cleanup_database()
        
        mock_async_engine.dispose.assert_called_once()
        mock_sync_engine.dispose.assert_called_once()
    
    @patch('backend.database.connection.db_manager')
    @pytest.mark.asyncio
    async def test_database_health_check_healthy(self, mock_db_manager):
        """Test healthy database health check"""
        from backend.database.connection import database_health_check
        
        mock_db_manager.check_connection = AsyncMock(return_value=True)
        mock_db_manager.get_table_info = AsyncMock(return_value={
            'table_count': 15
        })
        
        # Mock the engine pool
        with patch('database.connection.async_engine') as mock_engine:
            mock_engine.pool.size.return_value = 20
            mock_engine.pool.checkedout.return_value = 3
            
            result = await database_health_check()
        
        assert result['status'] == 'healthy'
        assert result['connection'] is True
        assert result['tables'] == 15
        assert result['engine'] == 'PostgreSQL + AsyncPG'
        assert result['pool_size'] == 20
        assert result['checked_out'] == 3
    
    @patch('backend.database.connection.db_manager')
    @pytest.mark.asyncio
    async def test_database_health_check_unhealthy(self, mock_db_manager):
        """Test unhealthy database health check"""
        from backend.database.connection import database_health_check
        
        mock_db_manager.check_connection = AsyncMock(return_value=False)
        mock_db_manager.get_table_info = AsyncMock(return_value={
            'table_count': 0
        })
        
        result = await database_health_check()
        
        assert result['status'] == 'unhealthy'
        assert result['connection'] is False
    
    @patch('backend.database.connection.db_manager')
    @pytest.mark.asyncio
    async def test_database_health_check_exception(self, mock_db_manager):
        """Test database health check with exception"""
        from backend.database.connection import database_health_check
        
        mock_db_manager.check_connection = AsyncMock(side_effect=Exception("Connection error"))
        
        result = await database_health_check()
        
        assert result['status'] == 'unhealthy'
        assert result['connection'] is False
        assert 'error' in result


class TestEngineConfiguration:
    """Test engine configuration"""
    
    def test_async_engine_configuration(self):
        """Test async engine is properly configured"""
        from backend.database.connection import async_engine
        
        # Check that engine exists and has expected attributes
        assert async_engine is not None
        # These would be set by create_async_engine
        assert hasattr(async_engine, 'dispose')
        assert hasattr(async_engine, 'begin')
    
    def test_sync_engine_configuration(self):
        """Test sync engine is properly configured"""
        from backend.database.connection import sync_engine
        
        # Check that engine exists and has expected attributes
        assert sync_engine is not None
        assert hasattr(sync_engine, 'dispose')
    
    def test_session_factories_exist(self):
        """Test session factories are created"""
        from backend.database.connection import AsyncSessionLocal, SessionLocal
        
        assert AsyncSessionLocal is not None
        assert SessionLocal is not None


class TestGlobalInstances:
    """Test global instances"""
    
    def test_db_manager_global_instance(self):
        """Test global database manager instance"""
        from backend.database.connection import db_manager
        
        assert db_manager is not None
        assert hasattr(db_manager, 'async_engine')
        assert hasattr(db_manager, 'sync_engine')
        assert hasattr(db_manager, 'check_connection')
        assert hasattr(db_manager, 'create_tables')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])