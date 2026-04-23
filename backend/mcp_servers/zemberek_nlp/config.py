"""
Zemberek NLP MCP Server Configuration
Environment-based configuration with Pydantic

Supports both JPype (direct Java bridge) and HTTP backend modes.
"""


from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class ZemberekConfig(BaseSettings):
    """Configuration for Zemberek NLP MCP Server"""

    # JPype Bridge Configuration
    use_jpype: bool = Field(
        default=True,
        description="Use JPype bridge (True) or HTTP backend (False)",
    )
    java_home: str | None = Field(
        default=None,
        description="JAVA_HOME path (uses env var if None)",
    )
    zemberek_jar_path: str | None = Field(
        default=None,
        description="Path to Zemberek JAR file (auto-detected if None)",
    )
    jpype_jvm_options: list[str] = Field(
        default_factory=lambda: ["-Xmx512m"],
        description="Additional JVM options",
    )

    # HTTP Backend Service (fallback)
    zemberek_host: str = Field(
        default="localhost", description="Zemberek HTTP backend host"
    )
    zemberek_port: int = Field(
        default=8081, description="Zemberek HTTP backend port"
    )

    # Redis Cache
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str | None = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")

    # Cache Configuration
    cache_namespace: str = Field(
        default="zemberek", description="Redis cache key namespace"
    )
    cache_enabled: bool = Field(default=True, description="Enable Redis caching")

    # Performance
    http_timeout: float = Field(
        default=10.0, description="HTTP request timeout in seconds"
    )
    max_connections: int = Field(
        default=100, description="Max HTTP connection pool size"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_latency: bool = Field(default=True, description="Log request latencies")

    model_config = ConfigDict(
        env_prefix="ZEMBEREK_",
        env_file=".env",
        extra="ignore"
    )

    @property
    def zemberek_url(self) -> str:
        """Get full Zemberek HTTP backend URL"""
        return f"http://{self.zemberek_host}:{self.zemberek_port}"

    @property
    def redis_url(self) -> str:
        """Get full Redis URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Cache TTL settings per tool (in seconds)
CACHE_TTL: dict[str, int] = {
    "morphology": 3600,  # 1 hour - stable results
    "lemmatization": 3600,  # 1 hour - stable results
    "spell_check": 1800,  # 30 min - may need dictionary updates
    "tokenization": 3600,  # 1 hour - stable results
    "ner": 1800,  # 30 min - context-dependent
    "segmentation": 3600,  # 1 hour - stable results
    "normalization": 1800,  # 30 min - dictionary updates
}


def get_ttl(tool_name: str) -> int:
    """Get TTL for a specific tool"""
    return CACHE_TTL.get(tool_name, 3600)


# Global config instance
_config: ZemberekConfig | None = None


def get_config() -> ZemberekConfig:
    """Get or create global config instance"""
    global _config
    if _config is None:
        _config = ZemberekConfig()
    return _config
