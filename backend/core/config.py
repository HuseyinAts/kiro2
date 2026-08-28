"""
Uygulama konfigürasyon ayarları
Türkçe karakter desteği ve environment değişkenleri
"""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_current_dir = Path(__file__).parent.parent
_root_dir = _current_dir.parent
_env_file = (
    _root_dir / ".env" if (_root_dir / ".env").exists() else _current_dir / ".env"
)
load_dotenv(_env_file)


class EmbeddingModelType(str, Enum):
    """Desteklenen embedding model tipleri."""

    BERTURK = "berturk"
    MULTILINGUAL = "multilingual"


class EmbeddingConfig:
    """
    Embedding model konfigürasyonu.

    Spec REQ-1: İkisi de desteklenecek - config ile seçilebilir.
    - berturk: Türkçe odaklı BERTurk modeli (mevcut)
    - multilingual: Çok dilli Sentence-Transformers modeli (spec talep)
    """

    MODEL_OPTIONS: dict[str, str] = {
        EmbeddingModelType.BERTURK: "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr",
        EmbeddingModelType.MULTILINGUAL: "paraphrase-multilingual-mpnet-base-v2",
    }
    DEFAULT_MODEL: str = os.getenv("EMBEDDING_MODEL", EmbeddingModelType.BERTURK)
    MODEL_DIMENSIONS: dict[str, int] = {
        EmbeddingModelType.BERTURK: 768,
        EmbeddingModelType.MULTILINGUAL: 768,
    }
    BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    CACHE_TTL_SECONDS: int = int(os.getenv("EMBEDDING_CACHE_TTL", "86400"))

    @classmethod
    def get_model_name(cls) -> str:
        """Aktif embedding model adını döndür."""
        model_type = cls.DEFAULT_MODEL
        return cls.MODEL_OPTIONS.get(
            model_type, cls.MODEL_OPTIONS[EmbeddingModelType.BERTURK]
        )

    @classmethod
    def get_model_dimension(cls) -> int:
        """Aktif model dimension'ını döndür."""
        model_type = cls.DEFAULT_MODEL
        return cls.MODEL_DIMENSIONS.get(model_type, 768)


class Settings:
    """Uygulama ayarları."""

    def __init__(self) -> None:
        """Initialize application settings from environment."""
        self.app_name: str = "Türkiye Üniversite Sınavları Hazırlık Platformu"
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            self.log_level = "INFO"
        self.log_format = os.getenv(
            "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.log_json = os.getenv("LOG_JSON", "false").lower() == "true"
        self.slow_query_threshold_ms = int(os.getenv("SLOW_QUERY_THRESHOLD_MS", "500"))
        self.slow_api_threshold_ms = int(os.getenv("SLOW_API_THRESHOLD_MS", "1000"))
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable is required.\nCreate a .env file with:\n  DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"
            )
        self.database_echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.database_test_url = os.getenv(
            "DATABASE_TEST_URL", "sqlite+aiosqlite:///./test_turkiye_sinav.db"
        )
        self.db_pool_size = int(os.getenv("DB_POOL_SIZE", "15"))
        self.db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "15"))
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_host_env = os.getenv("REDIS_HOST")
        if _redis_host_env:
            self.redis_host = _redis_host_env
        else:
            import re as _re

            _m = _re.match("redis://(?:[^@]+@)?([^:/]+)", self.redis_url)
            self.redis_host = _m.group(1) if _m else "localhost"
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        self.elasticsearch_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.elasticsearch_user = os.getenv("ELASTICSEARCH_USER", "elastic")
        self.elasticsearch_password = os.getenv(
            "ELASTICSEARCH_PASSWORD", "Kiro2Elastic2026!"
        )
        self.elasticsearch_index = os.getenv(
            "ELASTICSEARCH_INDEX", "turkiye_sinav_platform"
        )
        self.secret_key = os.getenv(
            "SECRET_KEY", "your-secret-key-change-in-production"
        )
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret_key:
            self.jwt_secret_key = self.secret_key
            if self.environment == "production":
                raise ValueError(
                    "CRITICAL SECURITY ERROR: JWT_SECRET_KEY environment variable is required in production!"
                )
        if self.environment == "production":
            if len(self.jwt_secret_key) < 64:
                raise ValueError("CRITICAL: JWT_SECRET_KEY must be at least 64 chars!")
            unique_chars = len(set(self.jwt_secret_key))
            if unique_chars < 32:
                raise ValueError(
                    f"CRITICAL: JWT key low entropy ({unique_chars}/32 chars)!"
                )
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
        )
        self.jwt_refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
        )
        origins_str = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://localhost:5173",
        )
        self.allowed_origins = [origin.strip() for origin in origins_str.split(",")]
        self.encoding = "utf-8"
        self.locale = "tr_TR.UTF-8"
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1")
        self.llm_model = os.getenv("LLM_MODEL", "minimax-m2.5")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.qwen_api_key = os.getenv("QWEN_API_KEY")
        self.qwen_api_base = os.getenv("QWEN_API_BASE", "http://localhost:8001")
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.enable_monitoring = (
            os.getenv("ENABLE_MONITORING", "true").lower() == "true"
        )
        self.metrics_port = int(os.getenv("METRICS_PORT", "8001"))
        self.feature_flags = {
            "new_exam_ui": os.getenv("FF_NEW_EXAM_UI", "false").lower() == "true",
            "bionic_reading": os.getenv("FF_BIONIC_READING", "true").lower() == "true",
            "dark_mode": os.getenv("FF_DARK_MODE", "true").lower() == "true",
            "ai_tutor": os.getenv("FF_AI_TUTOR", "false").lower() == "true",
            "ai_question_generation": os.getenv("FF_AI_QUESTION_GEN", "false").lower()
            == "true",
            "gemini_integration": os.getenv("FF_GEMINI", "true").lower() == "true",
            "irt_adaptive": os.getenv("FF_IRT_ADAPTIVE", "true").lower() == "true",
            "fsrs_spaced_repetition": os.getenv("FF_FSRS", "true").lower() == "true",
            "zpd_optimization": os.getenv("FF_ZPD", "true").lower() == "true",
            "turkish_nlp": os.getenv("FF_TURKISH_NLP", "true").lower() == "true",
            "zemberek_integration": os.getenv("FF_ZEMBEREK", "true").lower() == "true",
            "premium_analytics": os.getenv("FF_PREMIUM_ANALYTICS", "false").lower()
            == "true",
            "video_solutions": os.getenv("FF_VIDEO_SOLUTIONS", "false").lower()
            == "true",
            "beta_multi_agent": os.getenv("FF_BETA_MULTI_AGENT", "false").lower()
            == "true",
            "beta_voice_input": os.getenv("FF_BETA_VOICE", "false").lower() == "true",
        }
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
        if self.environment == "production":
            if self.jwt_secret_key == "your-secret-key-change-in-production":
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Production JWT secret key is using default value! Set JWT_SECRET_KEY environment variable to a strong random key."
                )
            if len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: JWT secret key must be at least 32 characters long!"
                )
        if (
            self.environment == "production"
            and self.secret_key == "your-secret-key-change-in-production"
        ):
            raise ValueError(
                "CRITICAL SECURITY ERROR: Production SECRET_KEY is using default value!"
            )
        if self.environment == "production":
            self._validate_production_environment()

    def _validate_production_environment(self):
        """
        SECURITY FIX: Comprehensive production environment validation
        Prevents common deployment mistakes
        """
        errors = []
        if "sqlite" in self.database_url.lower():
            errors.append("SQLite is not allowed in production (use PostgreSQL)")
        if "postgresql" in self.database_url:
            weak_passwords = ["postgres", "password", "admin", "root"]
            for weak_pwd in weak_passwords:
                if f":{weak_pwd}@" in self.database_url:
                    errors.append(
                        f"Weak database password detected: '{weak_pwd}' - use strong random password"
                    )
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
        if self.youtube_api_key:
            if len(self.youtube_api_key) < 20:
                errors.append("YOUTUBE_API_KEY appears invalid (too short)")
            if (
                "test" in self.youtube_api_key.lower()
                or "example" in self.youtube_api_key.lower()
            ):
                errors.append("YOUTUBE_API_KEY appears to be a placeholder")
        if self.debug:
            errors.append(
                "DEBUG mode is enabled in production - this is a security risk!"
            )
        if "*" in self.allowed_origins:
            errors.append("Wildcard CORS (*) is not allowed in production")
        if any("localhost" in origin for origin in self.allowed_origins):
            errors.append("localhost in CORS origins - remove for production")
        if errors:
            error_msg = "\n".join(f"  - {err}" for err in errors)
            raise ValueError(
                f'\n{"=" * 70}\nCRITICAL PRODUCTION VALIDATION ERRORS:\n{error_msg}\n{"=" * 70}\nFix these issues before deploying to production!\nSee .env.example for secure configuration template.'
            )

    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            feature_name: The name of the feature flag

        Returns:
            True if the feature is enabled, False otherwise
        """
        return self.feature_flags.get(feature_name, False)


@lru_cache
def get_settings() -> Settings:
    """Singleton pattern ile ayarları getir"""
    return Settings()


settings = get_settings()
