"""
KIRO2 Claude Agent Wrapper

Claude Agent SDK'yı KIRO2 platformuna uyarlayan wrapper sınıfı.
Domain-specific tool seçimi ve model stratejisi içerir.

Kullanım:
    agent = KIRO2Agent(domain="backend")
    result = await agent.execute("Analiz yap")

    # Özel config ile
    config = AgentConfig(model="opus", max_tokens=4096)
    agent = KIRO2Agent(domain="testing", config=config)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from backend.sdk.tool_definitions import get_domain_tools, ToolRegistry

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Kullanılabilir model tipleri."""

    OPUS = "claude-opus-4-5-20251101"
    SONNET = "claude-sonnet-4-20250514"
    HAIKU = "claude-haiku-4-20250514"


class AgentDomain(str, Enum):
    """Agent domain tipleri."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    TESTING = "testing"
    RESEARCH = "research"
    AI_ML = "ai_ml"
    DEVOPS = "devops"


@dataclass
class AgentConfig:
    """Agent yapılandırma sınıfı."""

    model: ModelType = ModelType.SONNET
    max_tokens: int = 8192
    temperature: float = 0.7
    timeout_ms: int = 120000
    max_retries: int = 3
    checkpoint_enabled: bool = True
    checkpoint_interval: int = 300000  # 5 dakika
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Agent çalıştırma sonucu."""

    success: bool
    output: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tokens_used: int = 0
    duration_ms: int = 0
    error: str | None = None


class KIRO2Agent:
    """
    KIRO2-specific agent wrapper.

    Claude Agent SDK'yı KIRO2 platformuna uyarlayan ana sınıf.
    Domain-specific tool seçimi ve model stratejisi uygular.

    Attributes:
        domain: Agent'ın çalışma alanı (backend, frontend, testing, vb.)
        config: Agent yapılandırması
        tools: Domain'e göre seçilmiş tool listesi

    Kalite Öncelikli Model Stratejisi:
        - Basit araştırma: Sonnet
        - Kod yazma: Sonnet
        - Kritik kararlar: Opus
        - Code review: Opus
        - Test yazma: Sonnet
    """

    def __init__(
        self,
        domain: str | AgentDomain,
        config: AgentConfig | None = None,
        custom_tools: list[str] | None = None,
    ) -> None:
        """
        KIRO2Agent başlat.

        Args:
            domain: Agent'ın çalışma alanı
            config: Opsiyonel yapılandırma
            custom_tools: Ek tool listesi (domain tool'larına eklenir)
        """
        self.domain = AgentDomain(domain) if isinstance(domain, str) else domain
        self.config = config or AgentConfig()

        # Domain tool'larını al
        domain_tools = get_domain_tools(self.domain.value)

        # Custom tool'ları ekle
        if custom_tools:
            domain_tools = list(set(domain_tools + custom_tools))

        self.tools = domain_tools
        self._callbacks: list[Callable] = []
        self._is_running = False

        logger.info(f"KIRO2Agent initialized: domain={self.domain}, tools={len(self.tools)}")

    def _get_model_for_task(self, task_type: str) -> ModelType:
        """
        Görev tipine göre optimal model seç.

        Kalite öncelikli strateji:
        - research, documentation → Sonnet
        - coding, refactoring → Sonnet
        - critical_decision, architecture → Opus
        - code_review, security → Opus
        - testing → Sonnet

        Args:
            task_type: Görev tipi

        Returns:
            Seçilen model
        """
        opus_tasks = {"critical_decision", "architecture", "code_review", "security"}

        if task_type in opus_tasks:
            return ModelType.OPUS

        return self.config.model

    async def execute(
        self,
        prompt: str,
        task_type: str = "general",
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Agent'ı çalıştır.

        Args:
            prompt: Çalıştırılacak prompt
            task_type: Görev tipi (model seçimi için)
            context: Ek context bilgisi

        Returns:
            AgentResult: Çalıştırma sonucu
        """
        import time

        start_time = time.time()
        self._is_running = True

        try:
            model = self._get_model_for_task(task_type)

            logger.info(f"Executing: model={model}, task_type={task_type}")

            # Agent SDK çağrısı simülasyonu
            # Gerçek implementasyonda anthropic-agent-sdk kullanılır
            result = await self._simulate_execution(prompt, model, context)

            duration_ms = int((time.time() - start_time) * 1000)

            return AgentResult(
                success=True,
                output=result["output"],
                tool_calls=result.get("tool_calls", []),
                tokens_used=result.get("tokens_used", 0),
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return AgentResult(
                success=False,
                output="",
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
            )
        finally:
            self._is_running = False

    async def _simulate_execution(
        self,
        prompt: str,
        model: ModelType,
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Agent çalıştırma simülasyonu.

        Not: Gerçek implementasyonda bu method anthropic-agent-sdk
        kullanarak gerçek API çağrısı yapar.

        Args:
            prompt: Prompt
            model: Kullanılacak model
            context: Context

        Returns:
            Simüle edilmiş sonuç
        """
        # Simülasyon - gerçek SDK entegrasyonunda değiştirilecek
        await asyncio.sleep(0.1)  # Simüle edilmiş gecikme

        return {
            "output": f"[Simulated] Executed with {model.value}",
            "tool_calls": [],
            "tokens_used": 100,
        }

    def add_callback(self, callback: Callable) -> None:
        """Callback ekle."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Callback kaldır."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    @property
    def is_running(self) -> bool:
        """Agent çalışıyor mu?"""
        return self._is_running

    def get_available_tools(self) -> list[str]:
        """Kullanılabilir tool listesi."""
        return self.tools.copy()

    def __repr__(self) -> str:
        return f"KIRO2Agent(domain={self.domain}, tools={len(self.tools)})"


# Domain-specific agent factory fonksiyonları
def create_backend_agent(config: AgentConfig | None = None) -> KIRO2Agent:
    """Backend domain agent'ı oluştur."""
    return KIRO2Agent(domain=AgentDomain.BACKEND, config=config)


def create_frontend_agent(config: AgentConfig | None = None) -> KIRO2Agent:
    """Frontend domain agent'ı oluştur."""
    return KIRO2Agent(domain=AgentDomain.FRONTEND, config=config)


def create_testing_agent(config: AgentConfig | None = None) -> KIRO2Agent:
    """Testing domain agent'ı oluştur."""
    return KIRO2Agent(domain=AgentDomain.TESTING, config=config)


def create_research_agent(config: AgentConfig | None = None) -> KIRO2Agent:
    """Research domain agent'ı oluştur."""
    config = config or AgentConfig()
    config.model = ModelType.SONNET  # Araştırma için Sonnet yeterli
    return KIRO2Agent(domain=AgentDomain.RESEARCH, config=config)


def create_code_review_agent(config: AgentConfig | None = None) -> KIRO2Agent:
    """Code review agent'ı oluştur (Opus kullanır)."""
    config = config or AgentConfig()
    config.model = ModelType.OPUS  # Code review için Opus
    return KIRO2Agent(
        domain=AgentDomain.BACKEND,
        config=config,
        custom_tools=["Read", "Grep", "Glob"],
    )
