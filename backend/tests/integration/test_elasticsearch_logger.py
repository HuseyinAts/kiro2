"""
Elasticsearch Logger Test Modülü
Elasticsearch tabanlı log yönetimi sistemi testleri
"""

import pytest
from datetime import UTC, datetime
from unittest.mock import MagicMock

from core.elasticsearch_logger import (
    ElasticsearchLogger,
    ElasticsearchLoggingMiddleware,
    LogCategory,
    LogEntry,
    LogLevel,
    get_elasticsearch_logger,
)


class TestLogEntry:
    """LogEntry model testleri"""

    def test_log_entry_creation(self):
        """Log entry oluşturma testi"""
        timestamp = datetime.now(UTC)
        entry = LogEntry(
            timestamp=timestamp,
            level=LogLevel.INFO,
            category=LogCategory.API,
            message="Test log mesajı",
            user_id="user_123",
            request_id="req_456",
            source="test_source",
            metadata={"key": "value"}
        )

        assert entry.timestamp == timestamp
        assert entry.level == LogLevel.INFO
        assert entry.category == LogCategory.API
        assert entry.message == "Test log mesajı"
        assert entry.user_id == "user_123"
        assert entry.request_id == "req_456"
        assert entry.source == "test_source"
        assert entry.metadata == {"key": "value"}

    def test_log_entry_metadata_default(self):
        """Log entry metadata varsayılan değer testi"""
        entry = LogEntry(
            message="Debug mesajı",
        )

        assert entry.metadata == {}
        assert isinstance(entry.metadata, dict)
        assert entry.level == LogLevel.INFO
        assert entry.category == LogCategory.GENERAL


class TestElasticsearchLogger:
    """ElasticsearchLogger testleri"""

    @pytest.fixture
    def logger(self):
        """Test için logger fixture"""
        return ElasticsearchLogger(
            index_prefix="test-logs",
            enabled=True
        )

    def test_logger_initialization(self, logger):
        """Logger başlatma testi"""
        assert logger.index_prefix == "test-logs"
        assert logger.enabled is True
        assert logger._entries == []

    @pytest.mark.asyncio
    async def test_log_methods(self, logger):
        """Log metodları testi"""
        # Info log
        await logger.info("Info mesajı", category=LogCategory.API, key="value")
        entries = await logger.get_entries()
        assert len(entries) == 1
        assert entries[0].level == LogLevel.INFO
        assert entries[0].category == LogCategory.API
        assert entries[0].message == "Info mesajı"
        assert entries[0].metadata == {"key": "value"}

        # Error log
        await logger.error("Error mesajı", category=LogCategory.DATABASE, error_code=500)
        entries = await logger.get_entries()
        assert len(entries) == 2
        assert entries[1].level == LogLevel.ERROR
        assert entries[1].category == LogCategory.DATABASE
        assert entries[1].message == "Error mesajı"
        assert entries[1].metadata == {"error_code": 500}

        # Warning log
        await logger.warning("Warning mesajı", category=LogCategory.SECURITY)
        entries = await logger.get_entries()
        assert len(entries) == 3
        assert entries[2].level == LogLevel.WARNING
        assert entries[2].category == LogCategory.SECURITY

    @pytest.mark.asyncio
    async def test_disabled_logger(self):
        """Disabled logger testi"""
        logger = ElasticsearchLogger(enabled=False)
        await logger.info("Info")
        entries = await logger.get_entries()
        assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_clear_entries(self, logger):
        """Clear entries testi"""
        await logger.info("Test")
        entries = await logger.get_entries()
        assert len(entries) == 1
        
        await logger.clear()
        entries = await logger.get_entries()
        assert len(entries) == 0


class TestElasticsearchLoggingMiddleware:
    """ElasticsearchLoggingMiddleware testleri"""

    @pytest.mark.asyncio
    async def test_middleware_call(self):
        """Middleware request testi"""
        app = MagicMock()
        # Mock as an async function
        async def mock_app(scope, receive, send):
            app(scope, receive, send)

        logger = ElasticsearchLogger()
        middleware = ElasticsearchLoggingMiddleware(mock_app, logger)
        
        scope = {"type": "http"}
        receive = MagicMock()
        send = MagicMock()
        
        await middleware(scope, receive, send)
        app.assert_called_once_with(scope, receive, send)


class TestSingletonLogger:
    """Singleton logger testleri"""

    def test_get_elasticsearch_logger_singleton(self):
        """Singleton pattern testi"""
        logger1 = get_elasticsearch_logger()
        logger2 = get_elasticsearch_logger()

        assert logger1 is logger2
        assert isinstance(logger1, ElasticsearchLogger)

class TestLogLevelsAndCategories:
    """Log seviyeleri ve kategorileri testleri"""

    def test_log_levels(self):
        """Log seviyeleri enum testi"""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"

    def test_log_categories(self):
        """Log kategorileri enum testi"""
        assert LogCategory.API.value == "api"
        assert LogCategory.DATABASE.value == "database"
        assert LogCategory.SECURITY.value == "security"
        assert LogCategory.PERFORMANCE.value == "performance"
        assert LogCategory.GENERAL.value == "general"
        assert LogCategory.AUTH.value == "auth"
        assert LogCategory.SYSTEM.value == "system"
        assert LogCategory.JOBS.value == "jobs"
