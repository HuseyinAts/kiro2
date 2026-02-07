"""
KIRO2 Orchestrator - Konfigürasyon

Bu modül, tüm yapılandırma ayarlarını merkezi olarak yönetir.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from enum import Enum


class Environment(Enum):
    """Çalışma ortamı"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class LLMConfig:
    """LLM Provider Konfigürasyonu"""
    # API Keys (environment variables'dan okunur)
    anthropic_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    openai_api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    
    # Model defaults
    default_claude_model: str = "claude-sonnet-4-20250514"
    default_openai_model: str = "gpt-4o"
    
    # Limits
    max_tokens: int = 8192
    temperature: float = 0.1
    timeout_seconds: int = 120
    max_retries: int = 3
    
    # Cost control
    cost_limit_per_run: float = 10.0  # USD
    cost_limit_daily: float = 100.0  # USD


@dataclass
class RedisConfig:
    """Redis Konfigürasyonu (State Management)"""
    host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    password: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    
    # Connection pool
    max_connections: int = 10
    socket_timeout: float = 5.0
    
    # Key prefixes
    state_prefix: str = "kiro2:state:"
    lock_prefix: str = "kiro2:lock:"
    
    @property
    def url(self) -> str:
        """Redis connection URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class PostgresConfig:
    """PostgreSQL Konfigürasyonu (Persistent Memory)"""
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5434")))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "kiro2"))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "kiro2"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", ""))
    
    # Connection pool
    min_connections: int = 2
    max_connections: int = 10
    
    @property
    def url(self) -> str:
        """PostgreSQL connection URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_url(self) -> str:
        """AsyncPG connection URL"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class OrchestrationConfig:
    """Orchestration Konfigürasyonu"""
    # Iteration limits
    max_iterations: int = 10
    max_fix_attempts: int = 3
    
    # Diff limits
    max_files_per_iteration: int = 5
    max_lines_per_iteration: int = 200
    max_total_lines: int = 500
    
    # No-progress detection
    identical_error_threshold: int = 4
    
    # Timeouts
    step_timeout_seconds: int = 300
    total_timeout_seconds: int = 1800  # 30 minutes
    
    # Quality gates
    lint_enabled: bool = True
    typecheck_enabled: bool = True
    test_enabled: bool = True
    security_enabled: bool = True
    
    # Quality thresholds
    min_test_coverage: float = 0.80
    max_lint_errors: int = 0
    max_type_errors: int = 0


@dataclass
class ToolConfig:
    """Tool Execution Konfigürasyonu"""
    # Sandbox settings
    enable_sandbox: bool = True
    allow_network: bool = False
    allow_subprocess: bool = True
    
    # File operations
    backup_before_edit: bool = True
    max_file_size_bytes: int = 1_000_000  # 1MB
    
    # Command execution
    command_timeout_seconds: int = 30
    max_output_lines: int = 1000
    
    # Paths
    allowed_paths: list = field(default_factory=lambda: [
        "src/",
        "tests/",
        "docs/",
        "scripts/",
    ])
    
    blocked_paths: list = field(default_factory=lambda: [
        ".git/",
        ".env",
        "secrets/",
        "node_modules/",
        "__pycache__/",
        ".venv/",
    ])


@dataclass
class LangSmithConfig:
    """LangSmith Tracing Konfigürasyonu"""
    enabled: bool = field(
        default_factory=lambda: os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    )
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("LANGSMITH_API_KEY")
    )
    project: str = field(
        default_factory=lambda: os.getenv("LANGSMITH_PROJECT", "kiro2-orchestrator")
    )
    endpoint: str = "https://api.smith.langchain.com"


@dataclass
class Config:
    """Ana Konfigürasyon"""
    # Environment
    env: Environment = field(
        default_factory=lambda: Environment(os.getenv("KIRO2_ENV", "development"))
    )
    
    # Project paths
    project_root: Path = field(
        default_factory=lambda: Path(os.getenv("KIRO2_PROJECT_ROOT", "."))
    )
    
    # Sub-configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    orchestration: OrchestrationConfig = field(default_factory=OrchestrationConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    langsmith: LangSmithConfig = field(default_factory=LangSmithConfig)
    
    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    log_format: str = "json"  # "json" or "text"
    
    def is_production(self) -> bool:
        """Production ortamında mı?"""
        return self.env == Environment.PRODUCTION
    
    def validate(self) -> list[str]:
        """Konfigürasyonu doğrula, hataları döndür"""
        errors = []
        
        # API key kontrolü
        if not self.llm.anthropic_api_key and not self.llm.openai_api_key:
            errors.append("En az bir LLM API key gerekli (ANTHROPIC_API_KEY veya OPENAI_API_KEY)")
        
        # Production için ek kontroller
        if self.is_production():
            if not self.redis.password:
                errors.append("Production'da Redis password gerekli")
            if not self.postgres.password:
                errors.append("Production'da PostgreSQL password gerekli")
            if not self.langsmith.enabled:
                errors.append("Production'da LangSmith tracing önerilir")
        
        return errors


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Global config instance'ı al"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reset_config() -> None:
    """Config'i sıfırla (test için)"""
    global _config
    _config = None


# Environment variables template
ENV_TEMPLATE = """
# KIRO2 Orchestrator Environment Variables
# Copy this to .env and fill in the values

# Environment
KIRO2_ENV=development  # development, staging, production

# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Redis (State Management)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# PostgreSQL (Persistent Memory)
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_DB=kiro2
POSTGRES_USER=kiro2
POSTGRES_PASSWORD=

# LangSmith (Tracing)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=kiro2-orchestrator

# Logging
LOG_LEVEL=INFO
"""
