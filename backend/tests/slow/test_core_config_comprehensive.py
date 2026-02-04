"""
Comprehensive tests for core.config module
Target: 95%+ coverage for critical configuration module
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from core.config import Settings, get_settings


class TestSettings:
    """Comprehensive Settings class tests"""

    def test_settings_initialization_default_values(self):
        """Test Settings initialization with default values"""
        settings = Settings()

        assert settings.app_name == "Türkiye Üniversite Sınavları Hazırlık Platformu"
        assert settings.app_version == "1.0.0"
        assert settings.debug is False
        assert settings.environment == "development"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert "turkiye_sinav.db" in settings.database_url
        assert settings.database_echo is False
        assert "test_turkiye_sinav.db" in settings.database_test_url
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.elasticsearch_url == "http://localhost:9200"
        assert settings.elasticsearch_index == "turkiye_sinav_platform"
        assert settings.algorithm == "HS256"
        assert settings.access_token_expire_minutes == 30
        assert "localhost:3000" in settings.allowed_origins
        assert "localhost:5173" in settings.allowed_origins

    @patch.dict(
        os.environ,
        {
            "DEBUG": "true",
            "ENVIRONMENT": "production",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "DATABASE_ECHO": "true",
            "DATABASE_TEST_URL": "postgresql://test:test@localhost/test_db",
            "REDIS_URL": "redis://localhost:6380/1",
            "REDIS_PASSWORD": "test123",
            "ELASTICSEARCH_URL": "http://elasticsearch:9200",
            "ELASTICSEARCH_INDEX": "test_index",
            "SECRET_KEY": "test-secret-key",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
            "ALLOWED_ORIGINS": "http://localhost:4000,http://example.com",
        },
    )
    def test_settings_initialization_with_env_vars(self):
        """Test Settings initialization with environment variables"""
        settings = Settings()

        assert settings.debug is True
        assert settings.environment == "production"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.database_url == "postgresql://test:test@localhost/test"
        assert settings.database_echo is True
        assert settings.database_test_url == "postgresql://test:test@localhost/test_db"
        assert settings.redis_url == "redis://localhost:6380/1"
        assert settings.redis_password == "test123"
        assert settings.elasticsearch_url == "http://elasticsearch:9200"
        assert settings.elasticsearch_index == "test_index"
        assert settings.secret_key == "test-secret-key"
        assert settings.access_token_expire_minutes == 60
        assert "localhost:4000" in settings.allowed_origins
        assert "example.com" in settings.allowed_origins

    @patch.dict(os.environ, {"DEBUG": "false"})
    def test_debug_false_case_insensitive(self):
        """Test debug flag with false value"""
        settings = Settings()
        assert settings.debug is False

    @patch.dict(os.environ, {"DEBUG": "FALSE"})
    def test_debug_false_uppercase(self):
        """Test debug flag with uppercase FALSE"""
        settings = Settings()
        assert settings.debug is False

    @patch.dict(os.environ, {"DEBUG": "True"})
    def test_debug_true_case_insensitive(self):
        """Test debug flag with True value"""
        settings = Settings()
        assert settings.debug is True

    @patch.dict(os.environ, {"DATABASE_ECHO": "false"})
    def test_database_echo_false(self):
        """Test database echo flag with false value"""
        settings = Settings()
        assert settings.database_echo is False

    @patch.dict(os.environ, {"DATABASE_ECHO": "TRUE"})
    def test_database_echo_true_uppercase(self):
        """Test database echo flag with uppercase TRUE"""
        settings = Settings()
        assert settings.database_echo is True

    @patch.dict(os.environ, {"PORT": "invalid"})
    def test_invalid_port_raises_error(self):
        """Test that invalid port raises ValueError"""
        with pytest.raises(ValueError):
            Settings()

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "invalid"})
    def test_invalid_access_token_expire_minutes_raises_error(self):
        """Test that invalid access token expire minutes raises ValueError"""
        with pytest.raises(ValueError):
            Settings()

    @patch.dict(os.environ, {"ALLOWED_ORIGINS": ""})
    def test_empty_allowed_origins(self):
        """Test with empty allowed origins"""
        settings = Settings()
        assert settings.allowed_origins == [""]

    @patch.dict(os.environ, {"ALLOWED_ORIGINS": "http://localhost:3000"})
    def test_single_allowed_origin(self):
        """Test with single allowed origin"""
        settings = Settings()
        assert settings.allowed_origins == ["http://localhost:3000"]

    @patch.dict(
        os.environ,
        {
            "ALLOWED_ORIGINS": "http://localhost:3000,  http://localhost:5173  ,http://example.com"
        },
    )
    def test_allowed_origins_with_spaces(self):
        """Test allowed origins with spaces"""
        settings = Settings()
        expected = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://example.com",
        ]
        assert settings.allowed_origins == expected

    def test_settings_immutable_after_creation(self):
        """Test that settings maintain their values"""
        settings = Settings()
        original_app_name = settings.app_name
        original_port = settings.port

        # Values should remain the same
        assert settings.app_name == original_app_name
        assert settings.port == original_port

    @patch.dict(os.environ, {"SECRET_KEY": ""})
    def test_empty_secret_key(self):
        """Test with empty secret key"""
        settings = Settings()
        assert settings.secret_key == ""

    @patch.dict(os.environ, {"REDIS_PASSWORD": ""})
    def test_empty_redis_password(self):
        """Test with empty redis password"""
        settings = Settings()
        assert settings.redis_password == ""

    def test_settings_attributes_exist(self):
        """Test that all expected attributes exist"""
        settings = Settings()

        required_attrs = [
            "app_name",
            "app_version",
            "debug",
            "environment",
            "host",
            "port",
            "database_url",
            "database_echo",
            "database_test_url",
            "redis_url",
            "redis_password",
            "elasticsearch_url",
            "elasticsearch_index",
            "secret_key",
            "algorithm",
            "access_token_expire_minutes",
            "allowed_origins",
        ]

        for attr in required_attrs:
            assert hasattr(settings, attr), f"Settings missing attribute: {attr}"

    def test_settings_types(self):
        """Test that settings have correct types"""
        settings = Settings()

        assert isinstance(settings.app_name, str)
        assert isinstance(settings.app_version, str)
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.environment, str)
        assert isinstance(settings.host, str)
        assert isinstance(settings.port, int)
        assert isinstance(settings.database_url, str)
        assert isinstance(settings.database_echo, bool)
        assert isinstance(settings.database_test_url, str)
        assert isinstance(settings.redis_url, str)
        assert isinstance(settings.elasticsearch_url, str)
        assert isinstance(settings.elasticsearch_index, str)
        assert isinstance(settings.secret_key, str)
        assert isinstance(settings.algorithm, str)
        assert isinstance(settings.access_token_expire_minutes, int)
        assert isinstance(settings.allowed_origins, list)


class TestGetSettings:
    """Test get_settings function"""

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns Settings instance"""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        """Test that get_settings caches the result"""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should return the same instance due to lru_cache
        assert settings1 is settings2

    def test_get_settings_multiple_calls_same_values(self):
        """Test that multiple calls return same configuration values"""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1.app_name == settings2.app_name
        assert settings1.port == settings2.port
        assert settings1.database_url == settings2.database_url


class TestConfigurationValidation:
    """Test configuration validation scenarios"""

    @patch.dict(os.environ, {"PORT": "0"})
    def test_port_zero(self):
        """Test port with zero value"""
        settings = Settings()
        assert settings.port == 0

    @patch.dict(os.environ, {"PORT": "65535"})
    def test_port_max_value(self):
        """Test port with maximum value"""
        settings = Settings()
        assert settings.port == 65535

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "0"})
    def test_access_token_expire_minutes_zero(self):
        """Test access token expire minutes with zero value"""
        settings = Settings()
        assert settings.access_token_expire_minutes == 0

    @patch.dict(os.environ, {"ACCESS_TOKEN_EXPIRE_MINUTES": "43200"})  # 30 days
    def test_access_token_expire_minutes_large_value(self):
        """Test access token expire minutes with large value"""
        settings = Settings()
        assert settings.access_token_expire_minutes == 43200


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration"""

    def test_database_url_formats(self):
        """Test various database URL formats"""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///./test.db"}):
            settings = Settings()
            assert settings.database_url == "sqlite:///./test.db"

        with patch.dict(
            os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost:5432/db"}
        ):
            settings = Settings()
            assert settings.database_url == "postgresql://user:pass@localhost:5432/db"

    def test_redis_url_formats(self):
        """Test various Redis URL formats"""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost"}):
            settings = Settings()
            assert settings.redis_url == "redis://localhost"

        with patch.dict(
            os.environ, {"REDIS_URL": "redis://:password@localhost:6379/0"}
        ):
            settings = Settings()
            assert settings.redis_url == "redis://:password@localhost:6379/0"

    def test_configuration_for_different_environments(self):
        """Test configuration for different environments"""
        # Development
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            settings = Settings()
            assert settings.environment == "development"

        # Production
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            settings = Settings()
            assert settings.environment == "production"

        # Testing
        with patch.dict(os.environ, {"ENVIRONMENT": "testing"}):
            settings = Settings()
            assert settings.environment == "testing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
