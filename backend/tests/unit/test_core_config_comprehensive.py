"""
Comprehensive Unit Tests for core/config.py
Testing configuration loading, validation, and security checks
"""
import pytest
import os
from unittest.mock import patch


class TestSettingsInitialization:
    """Test Settings class initialization and default values"""

    @pytest.mark.skip(reason=".env file overrides environment variables in test")
    def test_default_values(self):
        """Test default configuration values"""
        with patch.dict(os.environ, {'DEBUG': 'false', 'ENVIRONMENT': 'development'}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.app_name == "Türkiye Üniversite Sınavları Hazırlık Platformu"
            assert settings.app_version == "1.0.0"
            assert settings.debug is False
            assert settings.environment == "development"
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000

    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        with patch.dict(os.environ, {
            'DEBUG': 'true',
            'ENVIRONMENT': 'testing',
            'HOST': '127.0.0.1',
            'PORT': '9000'
        }, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.debug is True
            assert settings.environment == "testing"
            assert settings.host == "127.0.0.1"
            assert settings.port == 9000

    def test_database_defaults(self):
        """Test database configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert "sqlite+aiosqlite" in settings.database_url
            assert settings.database_echo is False
            assert settings.db_pool_size == 50
            assert settings.db_max_overflow == 100

    def test_redis_defaults(self):
        """Test Redis configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.redis_url == "redis://localhost:6379/0"
            assert settings.redis_password is None

    def test_security_defaults(self):
        """Test security configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.secret_key == "your-secret-key-change-in-production"
            assert settings.algorithm == "HS256"
            assert settings.access_token_expire_minutes == 30

    def test_jwt_defaults(self):
        """Test JWT configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.jwt_secret_key == settings.secret_key  # Fallback
            assert settings.jwt_algorithm == "HS256"
            assert settings.jwt_access_token_expire_minutes == 15
            assert settings.jwt_refresh_token_expire_days == 7

    def test_cors_defaults(self):
        """Test CORS configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert "http://localhost:3000" in settings.allowed_origins
            assert "http://localhost:5173" in settings.allowed_origins

    def test_monitoring_defaults(self):
        """Test monitoring configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.enable_monitoring is True
            assert settings.metrics_port == 8001

    def test_rate_limiting_defaults(self):
        """Test rate limiting configuration defaults"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.rate_limit_per_minute == 100

    def test_external_api_keys(self):
        """Test external API key configuration"""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key',
            'YOUTUBE_API_KEY': 'test-youtube-key'
        }, clear=True):
            from core.config import Settings
            settings = Settings()

            assert settings.openai_api_key == 'test-openai-key'
            assert settings.youtube_api_key == 'test-youtube-key'


class TestSettingsValidation:
    """Test Settings validation logic"""

    def test_valid_postgresql_url(self):
        """Test that valid PostgreSQL URLs pass validation"""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql+asyncpg://user:pass@localhost/dbname'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert "postgresql" in settings.database_url

    def test_valid_sqlite_url(self):
        """Test that valid SQLite URLs pass validation"""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'sqlite+aiosqlite:///./test.db'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert "sqlite" in settings.database_url

    def test_invalid_database_url_raises_error(self):
        """Test that invalid database URLs raise ValueError"""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'mysql://localhost/db'
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="PostgreSQL veya SQLite"):
                Settings()

    def test_valid_redis_url(self):
        """Test that valid Redis URLs pass validation"""
        with patch.dict(os.environ, {
            'REDIS_URL': 'redis://localhost:6379/1'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert settings.redis_url.startswith("redis://")

    def test_invalid_redis_url_raises_error(self):
        """Test that invalid Redis URLs raise ValueError"""
        with patch.dict(os.environ, {
            'REDIS_URL': 'http://localhost:6379'
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="redis://"):
                Settings()


class TestProductionValidation:
    """Test production environment validation"""

    def test_production_requires_strong_jwt_secret(self):
        """Test that production requires strong JWT secret key"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'JWT_SECRET_KEY': 'short'
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="at least 32 characters"):
                Settings()

    def test_production_rejects_default_secret_key(self):
        """Test that production rejects default secret keys"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECRET_KEY': 'your-secret-key-change-in-production',
            'JWT_SECRET_KEY': 'a' * 40  # Valid length
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="default value"):
                Settings()

    def test_production_rejects_sqlite(self):
        """Test that production rejects SQLite database"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'sqlite+aiosqlite:///./prod.db',
            'SECRET_KEY': 'a' * 40,
            'JWT_SECRET_KEY': 'b' * 40
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="SQLite is not allowed in production"):
                Settings()

    def test_production_rejects_weak_database_password(self):
        """Test that production rejects weak database passwords"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql+asyncpg://user:password@localhost/db',
            'SECRET_KEY': 'a' * 40,
            'JWT_SECRET_KEY': 'b' * 40
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="Weak database password"):
                Settings()

    def test_production_rejects_debug_mode(self):
        """Test that production rejects debug mode"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'true',
            'DATABASE_URL': 'postgresql+asyncpg://user:strongpass123@localhost/db',
            'SECRET_KEY': 'a' * 40,
            'JWT_SECRET_KEY': 'b' * 40
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="DEBUG mode"):
                Settings()

    def test_production_rejects_wildcard_cors(self):
        """Test that production rejects wildcard CORS"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'ALLOWED_ORIGINS': '*',
            'DATABASE_URL': 'postgresql+asyncpg://user:strongpass123@localhost/db',
            'SECRET_KEY': 'a' * 40,
            'JWT_SECRET_KEY': 'b' * 40
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="Wildcard CORS"):
                Settings()

    def test_production_rejects_localhost_cors(self):
        """Test that production rejects localhost in CORS"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'ALLOWED_ORIGINS': 'http://localhost:3000,https://example.com',
            'DATABASE_URL': 'postgresql+asyncpg://user:strongpass123@localhost/db',
            'SECRET_KEY': 'a' * 40,
            'JWT_SECRET_KEY': 'b' * 40
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="localhost in CORS"):
                Settings()

    def test_production_valid_configuration(self):
        """Test that valid production configuration passes"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'DATABASE_URL': 'postgresql+asyncpg://user:VeryStr0ng!Pass@localhost/db',
            'SECRET_KEY': 'a' * 40,
            'JWT_SECRET_KEY': 'b' * 40,
            'ALLOWED_ORIGINS': 'https://example.com,https://www.example.com'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert settings.environment == "production"


class TestDevelopmentConfiguration:
    """Test development environment configuration"""

    def test_development_allows_sqlite(self):
        """Test that development allows SQLite"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DATABASE_URL': 'sqlite+aiosqlite:///./dev.db'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert "sqlite" in settings.database_url

    def test_development_allows_debug_mode(self):
        """Test that development allows debug mode"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert settings.debug is True

    def test_development_allows_default_secrets(self):
        """Test that development allows default secret keys"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'development'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            # Should not raise error
            assert settings.secret_key == "your-secret-key-change-in-production"


class TestGetSettingsSingleton:
    """Test get_settings() singleton function"""

    def test_get_settings_returns_settings(self):
        """Test that get_settings() returns Settings instance"""
        with patch.dict(os.environ, {}, clear=True):
            from core.config import get_settings, Settings
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        """Test that get_settings() uses lru_cache (singleton)"""
        with patch.dict(os.environ, {}, clear=True):
            # Clear cache first
            from core.config import get_settings
            get_settings.cache_clear()

            settings1 = get_settings()
            settings2 = get_settings()

            # Should return same instance
            assert settings1 is settings2


class TestJWTConfiguration:
    """Test JWT-specific configuration"""

    def test_jwt_secret_fallback_to_secret_key(self):
        """Test JWT secret falls back to SECRET_KEY if not set"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert settings.jwt_secret_key == settings.secret_key

    def test_jwt_secret_uses_env_var_when_set(self):
        """Test JWT secret uses JWT_SECRET_KEY when set"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'JWT_SECRET_KEY': 'different-jwt-key'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert settings.jwt_secret_key == 'different-jwt-key'
            assert settings.jwt_secret_key != settings.secret_key

    def test_production_requires_jwt_secret_key_env_var(self):
        """Test production requires JWT_SECRET_KEY to be set explicitly"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECRET_KEY': 'a' * 40
            # JWT_SECRET_KEY not set - should raise error
        }, clear=True):
            from core.config import Settings
            with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable is required"):
                Settings()


class TestCORSConfiguration:
    """Test CORS configuration parsing"""

    def test_cors_single_origin(self):
        """Test CORS with single origin"""
        with patch.dict(os.environ, {
            'ALLOWED_ORIGINS': 'https://example.com'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert len(settings.allowed_origins) == 1
            assert 'https://example.com' in settings.allowed_origins

    def test_cors_multiple_origins(self):
        """Test CORS with multiple origins"""
        with patch.dict(os.environ, {
            'ALLOWED_ORIGINS': 'https://example.com,https://app.example.com,https://admin.example.com'
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            assert len(settings.allowed_origins) == 3
            assert 'https://example.com' in settings.allowed_origins
            assert 'https://app.example.com' in settings.allowed_origins
            assert 'https://admin.example.com' in settings.allowed_origins

    def test_cors_strips_whitespace(self):
        """Test CORS origins have whitespace stripped"""
        with patch.dict(os.environ, {
            'ALLOWED_ORIGINS': 'https://example.com ,  https://app.example.com  '
        }, clear=True):
            from core.config import Settings
            settings = Settings()
            # All origins should have no leading/trailing whitespace
            for origin in settings.allowed_origins:
                assert origin == origin.strip()
