"""
Comprehensive tests for core/config.py
Tests configuration loading, validation, and defaults
"""
import os
import pytest
from unittest.mock import patch


class TestSettingsDefaults:
    """Test default settings values"""

    def test_app_name_default(self):
        """Test default app name"""
        from core.config import Settings

        settings = Settings()
        assert settings.app_name == "Türkiye Üniversite Sınavları Hazırlık Platformu"

    def test_app_version_default(self):
        """Test default app version"""
        from core.config import Settings

        settings = Settings()
        assert settings.app_version == "1.0.0"

    def test_debug_default_false(self):
        """Test debug defaults to False"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.debug is False

    def test_environment_default(self):
        """Test default environment is development"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.environment == "development"

    def test_host_default(self):
        """Test default host"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.host == "0.0.0.0"

    def test_port_default(self):
        """Test default port"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.port == 8000

    def test_database_url_default(self):
        """Test default database URL"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.database_url == "sqlite+aiosqlite:///./turkiye_sinav.db"

    def test_redis_url_default(self):
        """Test default Redis URL"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.redis_url == "redis://localhost:6379/0"

    def test_elasticsearch_url_default(self):
        """Test default Elasticsearch URL"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.elasticsearch_url == "http://localhost:9200"


class TestSettingsEnvironmentVariables:
    """Test settings from environment variables"""

    def test_debug_from_env_true(self):
        """Test debug set to true from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"DEBUG": "true"}):
            settings = Settings()
            assert settings.debug is True

    def test_debug_from_env_false(self):
        """Test debug set to false from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"DEBUG": "false"}):
            settings = Settings()
            assert settings.debug is False

    def test_environment_from_env(self):
        """Test environment from env variable"""
        from core.config import Settings

        # FIX: Production environment requires strong, random keys (no weak keywords)
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",
                "DATABASE_URL": "postgresql+asyncpg://produser:StrongP@ss123!Prod@prodhost:5432/proddb",
                "SECRET_KEY": "xF4XmfFRyJpbHC0DwzdT2rozSyRlkjyXcD4NWwWhaf4U2aWD9JHeeYCZ1DhSi3K2",
                "JWT_SECRET_KEY": "ZcXF6-2MU-cuMZQzMX4xL0MxPcbIsB4Yj37HylQNNaMM5d8xB_PgBvp8MILttUaL",
                "ALLOWED_ORIGINS": "https://example.com,https://app.example.com",
                "YOUTUBE_API_KEY": "AIzaSyDxVqW8kF9_pL2mN3oP4qR5sT6uV7wX8yZ0",
                "DEBUG": "false",
            },
        ):
            settings = Settings()
            assert settings.environment == "production"

    def test_port_from_env(self):
        """Test port from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"PORT": "9000"}):
            settings = Settings()
            assert settings.port == 9000

    def test_database_url_from_env(self):
        """Test database URL from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/testdb"}):
            settings = Settings()
            assert settings.database_url == "postgresql://localhost/testdb"

    def test_secret_key_from_env(self):
        """Test secret key from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"SECRET_KEY": "my-secret-key"}):
            settings = Settings()
            assert settings.secret_key == "my-secret-key"

    def test_access_token_expire_from_env(self):
        """Test token expiration from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "60"}):
            settings = Settings()
            assert settings.access_token_expire_minutes == 60

    def test_rate_limit_from_env(self):
        """Test rate limit from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"RATE_LIMIT_PER_MINUTE": "200"}):
            settings = Settings()
            assert settings.rate_limit_per_minute == 200


class TestSettingsValidation:
    """Test settings validation"""

    def test_valid_postgresql_url(self):
        """Test valid PostgreSQL URL passes validation"""
        from core.config import Settings

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/db"}):
            settings = Settings()
            assert settings.database_url == "postgresql://localhost/db"

    def test_valid_postgresql_asyncpg_url(self):
        """Test valid PostgreSQL+asyncpg URL passes validation"""
        from core.config import Settings

        with patch.dict(
            os.environ, {"DATABASE_URL": "postgresql+asyncpg://localhost/db"}
        ):
            settings = Settings()
            assert settings.database_url == "postgresql+asyncpg://localhost/db"

    def test_valid_sqlite_url(self):
        """Test valid SQLite URL passes validation"""
        from core.config import Settings

        with patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///./test.db"}):
            settings = Settings()
            assert settings.database_url == "sqlite+aiosqlite:///./test.db"

    def test_invalid_database_url(self):
        """Test invalid database URL raises ValueError"""
        from core.config import Settings

        with patch.dict(os.environ, {"DATABASE_URL": "mysql://localhost/db"}):
            with pytest.raises(
                ValueError,
                match="Veritabanı URL PostgreSQL veya SQLite formatında olmalı",
            ):
                Settings()

    def test_valid_redis_url(self):
        """Test valid Redis URL passes validation"""
        from core.config import Settings

        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379/0"}):
            settings = Settings()
            assert settings.redis_url == "redis://localhost:6379/0"

    def test_invalid_redis_url(self):
        """Test invalid Redis URL raises ValueError"""
        from core.config import Settings

        with patch.dict(os.environ, {"REDIS_URL": "http://localhost:6379"}):
            with pytest.raises(ValueError, match="Redis URL redis:// ile başlamalı"):
                Settings()


class TestSettingsCORS:
    """Test CORS configuration"""

    def test_allowed_origins_default(self):
        """Test default allowed origins"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "http://localhost:3000" in settings.allowed_origins
            assert "http://localhost:5173" in settings.allowed_origins

    def test_allowed_origins_from_env(self):
        """Test allowed origins from environment"""
        from core.config import Settings

        with patch.dict(
            os.environ, {"ALLOWED_ORIGINS": "http://example.com,http://test.com"}
        ):
            settings = Settings()
            assert "http://example.com" in settings.allowed_origins
            assert "http://test.com" in settings.allowed_origins
            assert len(settings.allowed_origins) == 2

    def test_allowed_origins_with_spaces(self):
        """Test allowed origins with spaces are trimmed"""
        from core.config import Settings

        with patch.dict(
            os.environ, {"ALLOWED_ORIGINS": " http://example.com , http://test.com "}
        ):
            settings = Settings()
            assert "http://example.com" in settings.allowed_origins
            assert "http://test.com" in settings.allowed_origins


class TestSettingsTurkishSupport:
    """Test Turkish language support settings"""

    def test_encoding_utf8(self):
        """Test encoding is UTF-8"""
        from core.config import Settings

        settings = Settings()
        assert settings.encoding == "utf-8"

    def test_locale_turkish(self):
        """Test locale is Turkish"""
        from core.config import Settings

        settings = Settings()
        assert settings.locale == "tr_TR.UTF-8"


class TestSettingsMonitoring:
    """Test monitoring configuration"""

    def test_enable_monitoring_default(self):
        """Test monitoring enabled by default"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.enable_monitoring is True

    def test_enable_monitoring_false(self):
        """Test monitoring can be disabled"""
        from core.config import Settings

        with patch.dict(os.environ, {"ENABLE_MONITORING": "false"}):
            settings = Settings()
            assert settings.enable_monitoring is False

    def test_metrics_port_default(self):
        """Test default metrics port"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.metrics_port == 8001

    def test_metrics_port_from_env(self):
        """Test metrics port from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"METRICS_PORT": "9090"}):
            settings = Settings()
            assert settings.metrics_port == 9090


class TestGetSettings:
    """Test get_settings singleton function"""

    def test_get_settings_returns_settings(self):
        """Test get_settings returns Settings instance"""
        from core.config import get_settings, Settings

        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        """Test get_settings returns same instance (singleton)"""
        from core.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestSettingsSecurity:
    """Test security-related settings"""

    def test_secret_key_default(self):
        """Test default secret key"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.secret_key == "your-secret-key-change-in-production"

    def test_algorithm_hs256(self):
        """Test algorithm is HS256"""
        from core.config import Settings

        settings = Settings()
        assert settings.algorithm == "HS256"

    def test_access_token_expire_default(self):
        """Test default token expiration"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.access_token_expire_minutes == 30


class TestSettingsExternalAPIs:
    """Test external API configuration"""

    def test_openai_api_key_none_by_default(self):
        """Test OpenAI API key is None by default"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.openai_api_key is None

    def test_openai_api_key_from_env(self):
        """Test OpenAI API key from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            settings = Settings()
            assert settings.openai_api_key == "sk-test123"

    def test_youtube_api_key_none_by_default(self):
        """Test YouTube API key is None by default"""
        from core.config import Settings

        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.youtube_api_key is None

    def test_youtube_api_key_from_env(self):
        """Test YouTube API key from environment"""
        from core.config import Settings

        with patch.dict(os.environ, {"YOUTUBE_API_KEY": "yt-key123"}):
            settings = Settings()
            assert settings.youtube_api_key == "yt-key123"
