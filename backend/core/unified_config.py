"""
Unified Configuration Manager
Centralized configuration management with environment support, validation, and caching
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional

import yaml

try:
    from pydantic import ConfigDict, Field, field_validator
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings, ConfigDict, Field
        from pydantic import validator as field_validator
    except ImportError:
        # Fallback for tests - create a mock BaseSettings
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        Field = lambda default=None, **kwargs: default

        def field_validator(field_name, **kwargs):
            def decorator(func):
                return func

            return decorator

        ConfigDict = lambda **kwargs: None

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported environments"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ConfigSource(str, Enum):
    """Configuration sources in priority order"""

    ENVIRONMENT_VARS = "environment_vars"
    ENV_FILE = "env_file"
    YAML_FILE = "yaml_file"
    JSON_FILE = "json_file"
    DEFAULT_VALUES = "default_values"


@dataclass
class ConfigValidationRule:
    """Configuration validation rule"""

    field_name: str
    required: bool = True
    data_type: type = str
    validator_func: Optional[Callable] = None
    default_value: Any = None
    description: str = ""


class DatabaseConfig(BaseSettings):
    """Database configuration section"""

    url: str = Field(
        default="sqlite+aiosqlite:///./turkiye_sinav.db",
        description="Database connection URL",
    )
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=30, description="Max connection overflow")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")

    @field_validator("url")
    def validate_database_url(cls, v):
        valid_prefixes = (
            "postgresql://",
            "postgresql+asyncpg://",
            "sqlite+aiosqlite://",
            "mysql+aiomysql://",
        )
        if not v.startswith(valid_prefixes):
            raise ValueError(f"Database URL must start with one of: {valid_prefixes}")
        return v

    model_config = ConfigDict(env_prefix="DATABASE_")


class RedisConfig(BaseSettings):
    """Redis configuration section"""

    url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    password: str | None = Field(default=None, description="Redis password")
    max_connections: int = Field(default=50, description="Max Redis connections")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")

    @field_validator("url")
    def validate_redis_url(cls, v):
        if not v.startswith("redis://"):
            raise ValueError("Redis URL must start with redis://")
        return v

    model_config = ConfigDict(env_prefix="REDIS_")


class ElasticsearchConfig(BaseSettings):
    """Elasticsearch configuration section"""

    url: str = Field(default="http://localhost:9200", description="Elasticsearch URL")
    index: str = Field(
        default="turkiye_sinav_platform", description="Default index name"
    )
    username: str | None = Field(default=None, description="Elasticsearch username")
    password: str | None = Field(default=None, description="Elasticsearch password")
    timeout: int = Field(default=30, description="Request timeout in seconds")

    model_config = ConfigDict(env_prefix="ELASTICSEARCH_")


class SecurityConfig(BaseSettings):
    """Security configuration section"""

    secret_key: str = Field(
        default="your-secret-key-change-in-production", description="JWT secret key"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )
    password_min_length: int = Field(default=8, description="Minimum password length")

    @field_validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            logger.warning("Secret key should be at least 32 characters long")
        return v

    model_config = ConfigDict(env_prefix="SECURITY_")


class ExternalAPIConfig(BaseSettings):
    """External API configuration section"""

    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    youtube_api_key: str | None = Field(default=None, description="YouTube API key")
    huggingface_api_key: str | None = Field(
        default=None, description="HuggingFace API key"
    )
    google_api_key: str | None = Field(default=None, description="Google API key")

    # API endpoints
    huggingface_endpoint: str = Field(
        default="https://api-inference.huggingface.co",
        description="HuggingFace API endpoint",
    )
    custom_llm_endpoint: str | None = Field(
        default=None, description="Custom LLM endpoint URL"
    )

    # API limits and timeouts
    api_timeout: int = Field(default=30, description="API request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum API retry attempts")
    rate_limit_per_minute: int = Field(
        default=100, description="API rate limit per minute"
    )

    model_config = ConfigDict(env_prefix="API_")


class MonitoringConfig(BaseSettings):
    """Monitoring and logging configuration"""

    enable_monitoring: bool = Field(default=True, description="Enable monitoring")
    metrics_port: int = Field(default=8001, description="Metrics server port")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    enable_structured_logging: bool = Field(
        default=True, description="Enable structured JSON logging"
    )
    log_retention_days: int = Field(default=30, description="Log retention in days")

    @field_validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    model_config = ConfigDict(env_prefix="MONITORING_")


class ServerConfig(BaseSettings):
    """Server configuration section"""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    allowed_origins: str | list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins",
    )
    max_request_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum request size in bytes"  # 10MB
    )

    @field_validator("allowed_origins", mode="before")
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from .env file - supports JSON array or comma-separated string"""
        if isinstance(v, str):
            # Try to parse as JSON first
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fallback to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    model_config = ConfigDict(env_prefix="SERVER_")


class UnifiedConfig(BaseSettings):
    """
    Unified Configuration Manager
    Centralized configuration with environment support, validation, and caching
    """

    # Application metadata
    app_name: str = Field(
        default="Türkiye Üniversite Sınavları Hazırlık Platformu",
        description="Application name",
    )
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Current environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Turkish language support
    encoding: str = Field(default="utf-8", description="Character encoding")
    locale: str = Field(default="tr_TR.UTF-8", description="System locale")
    timezone: str = Field(default="Europe/Istanbul", description="Default timezone")

    # Configuration sections
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    elasticsearch: ElasticsearchConfig = Field(default_factory=ElasticsearchConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    external_apis: ExternalAPIConfig = Field(default_factory=ExternalAPIConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    # Feature flags
    enable_caching: bool = Field(default=True, description="Enable caching")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_swagger: bool = Field(
        default=True, description="Enable Swagger documentation"
    )
    enable_background_tasks: bool = Field(
        default=True, description="Enable background tasks"
    )

    # Custom application settings (can be extended by services)
    custom_settings: dict[str, Any] = Field(
        default_factory=dict, description="Custom application-specific settings"
    )

    @field_validator("environment", mode="before")
    def validate_environment(cls, v):
        if isinstance(v, str):
            try:
                return Environment(v.lower())
            except ValueError:
                logger.warning(f"Invalid environment '{v}', using development")
                return Environment.DEVELOPMENT
        return v

    @field_validator("debug", mode="before")
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    model_config = ConfigDict(
        # Load from .env file
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow case insensitive environment variables
        case_sensitive=False,
        # Support nested configuration
        env_nested_delimiter="__",
        # Allow extra fields to prevent validation errors
        extra="allow",
    )


class ConfigurationManager:
    """
    Enhanced Configuration Manager with multiple source support and caching
    """

    def __init__(
        self,
        config_dir: Path | None = None,
        env_file: str | None = None,
        enable_caching: bool = True,
    ):
        self.config_dir = config_dir or Path("config")
        self.env_file = env_file or ".env"
        self.enable_caching = enable_caching
        self._config_cache: dict[str, Any] = {}
        self._config_sources: list[ConfigSource] = []

        # Initialize configuration
        self._unified_config: UnifiedConfig | None = None
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from all sources"""
        try:
            # Load environment-specific configuration
            env = os.getenv("ENVIRONMENT", "development").lower()

            # Try to load from YAML file first
            config_file = self.config_dir / f"{env}.yaml"
            if config_file.exists():
                self._load_from_yaml(config_file)
                self._config_sources.append(ConfigSource.YAML_FILE)

            # Try to load from JSON file
            json_config_file = self.config_dir / f"{env}.json"
            if json_config_file.exists():
                self._load_from_json(json_config_file)
                self._config_sources.append(ConfigSource.JSON_FILE)

            # Load from .env file if exists
            env_path = Path(self.env_file)
            if env_path.exists():
                self._config_sources.append(ConfigSource.ENV_FILE)

            # Load main configuration using Pydantic
            self._unified_config = UnifiedConfig()
            self._config_sources.append(ConfigSource.ENVIRONMENT_VARS)

            logger.info(f"Configuration loaded from sources: {self._config_sources}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fallback to default configuration
            self._unified_config = UnifiedConfig()

    def _load_from_yaml(self, config_file: Path) -> None:
        """Load configuration from YAML file"""
        try:
            with open(config_file, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
                self._merge_config_data(yaml_data)
        except Exception as e:
            logger.error(f"Failed to load YAML config from {config_file}: {e}")

    def _load_from_json(self, config_file: Path) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_file, encoding="utf-8") as f:
                json_data = json.load(f)
                self._merge_config_data(json_data)
        except Exception as e:
            logger.error(f"Failed to load JSON config from {config_file}: {e}")

    def _merge_config_data(self, data: dict[str, Any]) -> None:
        """Merge configuration data into environment variables"""
        for key, value in data.items():
            if isinstance(value, dict):
                # Handle nested configuration
                for nested_key, nested_value in value.items():
                    env_key = f"{key.upper()}_{nested_key.upper()}"
                    if env_key not in os.environ:
                        os.environ[env_key] = str(nested_value)
            else:
                env_key = key.upper()
                if env_key not in os.environ:
                    os.environ[env_key] = str(value)

    @property
    def config(self) -> UnifiedConfig:
        """Get unified configuration"""
        if self._unified_config is None:
            self._load_configuration()
        return self._unified_config

    @lru_cache(maxsize=128)
    def get_section(self, section_name: str) -> Any:
        """Get a configuration section with caching"""
        return getattr(self.config, section_name, None)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting with dot notation support"""
        try:
            keys = key.split(".")
            value = self.config

            for k in keys:
                value = getattr(value, k)

            return value
        except (AttributeError, KeyError):
            return default

    def set_custom_setting(self, key: str, value: Any) -> None:
        """Set a custom setting"""
        self.config.custom_settings[key] = value

        # Clear cache if caching is enabled
        if self.enable_caching:
            self.get_section.cache_clear()

    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get a custom setting"""
        return self.config.custom_settings.get(key, default)

    def validate_configuration(self) -> list[str]:
        """Validate current configuration and return any issues"""
        issues = []

        try:
            # Validate database connection
            db_config = self.get_section("database")
            if not db_config.url:
                issues.append("Database URL is not configured")

            # Validate security settings in production
            if self.config.environment == Environment.PRODUCTION:
                if (
                    self.config.security.secret_key
                    == "your-secret-key-change-in-production"
                ):
                    issues.append("Default secret key is being used in production")

                if self.config.debug:
                    issues.append("Debug mode is enabled in production")

            # Validate external API keys if features are enabled
            api_config = self.get_section("external_apis")
            if not api_config.openai_api_key:
                issues.append("OpenAI API key is not configured")

            if not api_config.youtube_api_key:
                issues.append("YouTube API key is not configured")

        except Exception as e:
            issues.append(f"Configuration validation error: {e}")

        return issues

    def get_environment_info(self) -> dict[str, Any]:
        """Get environment information for debugging"""
        return {
            "environment": self.config.environment.value,
            "debug": self.config.debug,
            "config_sources": [source.value for source in self._config_sources],
            "config_dir": str(self.config_dir),
            "env_file": self.env_file,
            "validation_issues": self.validate_configuration(),
        }

    def reload_configuration(self) -> None:
        """Reload configuration from all sources"""
        self._config_cache.clear()
        if self.enable_caching:
            self.get_section.cache_clear()

        self._config_sources.clear()
        self._load_configuration()

        logger.info("Configuration reloaded")

    def export_configuration(self, include_secrets: bool = False) -> dict[str, Any]:
        """Export current configuration as dictionary"""
        config_dict = self.config.model_dump()

        if not include_secrets:
            # Remove sensitive information
            sensitive_fields = [
                "security.secret_key",
                "database.url",
                "redis.password",
                "external_apis.openai_api_key",
                "external_apis.youtube_api_key",
                "external_apis.huggingface_api_key",
                "elasticsearch.password",
            ]

            for field in sensitive_fields:
                keys = field.split(".")
                current = config_dict
                for key in keys[:-1]:
                    if key in current and isinstance(current[key], dict):
                        current = current[key]
                    else:
                        break
                else:
                    if keys[-1] in current:
                        current[keys[-1]] = "[REDACTED]"

        return config_dict


# Global configuration manager instance
_config_manager: ConfigurationManager | None = None


def get_config_manager(
    config_dir: Path | None = None, env_file: str | None = None, reload: bool = False
) -> ConfigurationManager:
    """Get global configuration manager instance"""
    global _config_manager

    if _config_manager is None or reload:
        _config_manager = ConfigurationManager(config_dir=config_dir, env_file=env_file)

    return _config_manager


@lru_cache
def get_unified_config() -> UnifiedConfig:
    """Get unified configuration with caching"""
    return get_config_manager().config


# Backwards compatibility aliases
def get_settings() -> UnifiedConfig:
    """Backwards compatibility alias"""
    return get_unified_config()


# Global configuration instance for easy access
config = get_unified_config()
settings = config  # Alias for backwards compatibility
