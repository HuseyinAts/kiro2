"""
Uygulama konfigürasyon ayarları
Türkçe karakter desteği ve environment değişkenleri
"""
import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file
# CRITICAL FIX: override=True ensures .env values override cached environment variables
load_dotenv(override=True)


class Settings:
    """Uygulama ayarları"""

    def __init__(self):
        # Uygulama temel ayarları
        self.app_name = "Türkiye Üniversite Sınavları Hazırlık Platformu"
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")

        # Sunucu ayarları
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))

        # Veritabanı ayarları
        self.database_url = os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./turkiye_sinav.db"
        )
        self.database_echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.database_test_url = os.getenv(
            "DATABASE_TEST_URL", "sqlite+aiosqlite:///./test_turkiye_sinav.db"
        )
        # Database pool settings (CRITICAL for performance)
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "50"))
        self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "100"))

        # Redis ayarları
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_password = os.getenv("REDIS_PASSWORD")

        # Elasticsearch ayarları
        self.elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.elasticsearch_index = os.getenv(
            "ELASTICSEARCH_INDEX", "turkiye_sinav_platform"
        )

        # Güvenlik ayarları
        self.secret_key = os.getenv(
            "SECRET_KEY", "your-secret-key-change-in-production"
        )
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )

        # JWT ayarları (SECURITY FIX: Missing JWT configuration)
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret_key:
            # Fallback to SECRET_KEY but warn
            self.jwt_secret_key = self.secret_key
            if self.environment == "production":
                raise ValueError(
                    "CRITICAL SECURITY ERROR: JWT_SECRET_KEY environment variable is required in production!"
                )
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
        )
        self.jwt_refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )

        # CORS ayarları
        origins_str = os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
        )
        self.allowed_origins = [origin.strip() for origin in origins_str.split(",")]

        # Türkçe karakter desteği
        self.encoding = "utf-8"
        self.locale = "tr_TR.UTF-8"

        # API rate limiting
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

        # External API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")

        # Monitoring ayarları
        self.enable_monitoring = (
            os.getenv("ENABLE_MONITORING", "true").lower() == "true"
        )
        self.metrics_port = int(os.getenv("METRICS_PORT", "8001"))

        # Validate URLs
        self._validate_settings()

    def _validate_settings(self):
        """Ayarları doğrula"""
        valid_db_prefixes = (
            "postgresql://",
            "postgresql+asyncpg://",
            "sqlite+aiosqlite://",
        )
        if not self.database_url.startswith(valid_db_prefixes):
            raise ValueError("Veritabanı URL PostgreSQL veya SQLite formatında olmalı")

        if not self.redis_url.startswith("redis://"):
            raise ValueError("Redis URL redis:// ile başlamalı")

        # SECURITY FIX: Validate JWT secret key
        if self.environment == "production":
            if self.jwt_secret_key == "your-secret-key-change-in-production":
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Production JWT secret key is using default value! "
                    "Set JWT_SECRET_KEY environment variable to a strong random key."
                )
            if len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: JWT secret key must be at least 32 characters long!"
                )

        # SECURITY FIX: Validate SECRET_KEY
        if (
            self.environment == "production"
            and self.secret_key == "your-secret-key-change-in-production"
        ):
            raise ValueError(
                "CRITICAL SECURITY ERROR: Production SECRET_KEY is using default value!"
            )

        # SECURITY FIX: Additional production validations
        if self.environment == "production":
            self._validate_production_environment()

    def _validate_production_environment(self):
        """
        SECURITY FIX: Comprehensive production environment validation
        Prevents common deployment mistakes
        """
        errors = []

        # 1. Database validation
        if "sqlite" in self.database_url.lower():
            errors.append("SQLite is not allowed in production (use PostgreSQL)")

        if "postgresql" in self.database_url:
            # Check for default/weak passwords in connection string
            weak_passwords = ["postgres", "password", "admin", "root"]
            for weak_pwd in weak_passwords:
                if f":{weak_pwd}@" in self.database_url:
                    errors.append(
                        f"Weak database password detected: '{weak_pwd}' - use strong random password"
                    )

        # 2. Secret key validation
        weak_secrets = [
            "your-secret-key-change-in-production",
            "kiro2-docker-secret-key-change-in-production",
            "secret",
            "dev",
            "test",
        ]
        if any(weak in self.secret_key.lower() for weak in weak_secrets):
            errors.append(
                "Weak SECRET_KEY detected - use strong random key (64+ characters)"
            )

        if len(self.secret_key) < 32:
            errors.append("SECRET_KEY too short - must be at least 32 characters")

        # 3. JWT secret validation
        if self.jwt_secret_key == self.secret_key:
            errors.append("JWT_SECRET_KEY should be different from SECRET_KEY")

        weak_jwt_secrets = [
            "kiro2-docker-jwt-secret-change-in-production",
            "jwt",
            "token",
        ]
        if any(weak in self.jwt_secret_key.lower() for weak in weak_jwt_secrets):
            errors.append(
                "Weak JWT_SECRET_KEY detected - use strong random key (64+ characters)"
            )

        # 4. API key validation
        if self.youtube_api_key:
            if len(self.youtube_api_key) < 20:
                errors.append("YOUTUBE_API_KEY appears invalid (too short)")
            if (
                "test" in self.youtube_api_key.lower()
                or "example" in self.youtube_api_key.lower()
            ):
                errors.append("YOUTUBE_API_KEY appears to be a placeholder")

        # 5. Debug mode check
        if self.debug:
            errors.append(
                "DEBUG mode is enabled in production - this is a security risk!"
            )

        # 6. CORS validation
        if "*" in self.allowed_origins:
            errors.append("Wildcard CORS (*) is not allowed in production")

        if any("localhost" in origin for origin in self.allowed_origins):
            errors.append("localhost in CORS origins - remove for production")

        # Raise if any errors found
        if errors:
            error_msg = "\n".join(f"  - {err}" for err in errors)
            raise ValueError(
                f"\n{'='*70}\n"
                f"CRITICAL PRODUCTION VALIDATION ERRORS:\n"
                f"{error_msg}\n"
                f"{'='*70}\n"
                f"Fix these issues before deploying to production!\n"
                f"See .env.example for secure configuration template."
            )


@lru_cache
def get_settings() -> Settings:
    """Singleton pattern ile ayarları getir"""
    return Settings()


# Global ayarlar instance
settings = get_settings()
