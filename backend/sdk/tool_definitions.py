"""
KIRO2 Tool Definitions

Claude Code tool tanımları ve domain-specific registry.
Her domain için önceden tanımlanmış tool setleri içerir.

Kullanım:
    from backend.sdk.tool_definitions import get_domain_tools, register_tool

    # Domain tool'larını al
    tools = get_domain_tools("backend")

    # Özel tool kaydet
    @register_tool("my-tool", domains=["backend"])
    def my_tool(arg: str) -> str:
        return f"Result: {arg}"
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T", bound=Callable)


# Domain-specific tool setleri
BACKEND_TOOLS = [
    "Read",
    "Edit",
    "Write",
    "Bash",
    "Grep",
    "Glob",
    "Task",
]

FRONTEND_TOOLS = [
    "Read",
    "Edit",
    "Write",
    "Bash",
    "Glob",
]

TESTING_TOOLS = [
    "Read",
    "Bash",
    "Grep",
    "Glob",
]

RESEARCH_TOOLS = [
    "Read",
    "Grep",
    "Glob",
    "WebSearch",
    "WebFetch",
]

AI_ML_TOOLS = [
    "Read",
    "Edit",
    "Write",
    "Bash",
    "Grep",
    "Glob",
    "Task",
    "mcp__chromadb-mcp__search_questions",
    "mcp__chromadb-mcp__embed_content",
]

DEVOPS_TOOLS = [
    "Read",
    "Bash",
    "Glob",
    "Grep",
]

# Domain → Tools mapping
DOMAIN_TOOLS: dict[str, list[str]] = {
    "backend": BACKEND_TOOLS,
    "frontend": FRONTEND_TOOLS,
    "testing": TESTING_TOOLS,
    "research": RESEARCH_TOOLS,
    "ai_ml": AI_ML_TOOLS,
    "devops": DEVOPS_TOOLS,
}


@dataclass
class ToolDefinition:
    """Tool tanımı."""

    name: str
    description: str
    handler: Callable | None = None
    domains: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)


class ToolRegistry:
    """
    Tool registry sınıfı.

    Özel tool'ların kaydedilmesi ve yönetilmesi için kullanılır.
    """

    _instance: ToolRegistry | None = None
    _tools: dict[str, ToolDefinition] = {}

    def __new__(cls) -> ToolRegistry:
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(
        self,
        name: str,
        description: str = "",
        domains: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        required_permissions: list[str] | None = None,
    ) -> Callable[[T], T]:
        """
        Tool kaydetme decorator'ı.

        Args:
            name: Tool adı
            description: Tool açıklaması
            domains: Tool'un kullanılabileceği domain'ler
            parameters: Tool parametreleri
            required_permissions: Gerekli izinler

        Returns:
            Decorator fonksiyonu
        """
        def decorator(func: T) -> T:
            tool_def = ToolDefinition(
                name=name,
                description=description or func.__doc__ or "",
                handler=func,
                domains=domains or [],
                parameters=parameters or {},
                required_permissions=required_permissions or [],
            )
            self._tools[name] = tool_def

            # Domain tool listelerine ekle
            for domain in tool_def.domains:
                if domain in DOMAIN_TOOLS:
                    if name not in DOMAIN_TOOLS[domain]:
                        DOMAIN_TOOLS[domain].append(name)

            logger.info(f"Registered tool: {name}")
            return func

        return decorator

    def get(self, name: str) -> ToolDefinition | None:
        """Tool tanımı al."""
        return self._tools.get(name)

    def list_tools(self, domain: str | None = None) -> list[str]:
        """
        Tool listesi.

        Args:
            domain: Opsiyonel domain filtresi

        Returns:
            Tool isimleri listesi
        """
        if domain:
            return [
                name for name, tool in self._tools.items()
                if domain in tool.domains or not tool.domains
            ]
        return list(self._tools.keys())

    def clear(self) -> None:
        """Registry temizle (test için)."""
        self._tools.clear()


# Global registry instance
_registry = ToolRegistry()


def register_tool(
    name: str,
    domains: list[str] | None = None,
    description: str = "",
    parameters: dict[str, Any] | None = None,
) -> Callable[[T], T]:
    """
    Tool kaydetme fonksiyonu.

    Kullanım:
        @register_tool("my-tool", domains=["backend"])
        def my_tool(arg: str) -> str:
            return f"Result: {arg}"

    Args:
        name: Tool adı
        domains: Kullanılabilir domain'ler
        description: Açıklama
        parameters: Parametre tanımları

    Returns:
        Decorator
    """
    return _registry.register(
        name=name,
        description=description,
        domains=domains,
        parameters=parameters,
    )


def get_domain_tools(domain: str) -> list[str]:
    """
    Domain'e göre tool listesi al.

    Args:
        domain: Domain adı (backend, frontend, testing, vb.)

    Returns:
        Tool isimleri listesi
    """
    base_tools = DOMAIN_TOOLS.get(domain, []).copy()

    # Registry'den domain-specific tool'ları ekle
    for name, tool in _registry._tools.items():
        if domain in tool.domains and name not in base_tools:
            base_tools.append(name)

    return base_tools


def get_tool_definition(name: str) -> ToolDefinition | None:
    """Tool tanımı al."""
    return _registry.get(name)


# KIRO2-specific tool tanımları
@register_tool(
    name="irt-calculator",
    domains=["ai_ml", "backend"],
    description="IRT 3PL model hesaplamaları yapar",
    parameters={
        "difficulty": {"type": "float", "range": [-4.0, 4.0]},
        "discrimination": {"type": "float", "range": [0.2, 4.0]},
        "guessing": {"type": "float", "range": [0.0, 0.35]},
        "ability": {"type": "float", "range": [-4.0, 4.0]},
    },
)
def irt_calculator(
    difficulty: float,
    discrimination: float,
    guessing: float,
    ability: float,
) -> float:
    """
    IRT 3PL model ile başarı olasılığı hesapla.

    P(θ) = c + (1-c) / (1 + exp(-a(θ-b)))

    Args:
        difficulty: Zorluk parametresi (b)
        discrimination: Ayırt edicilik parametresi (a)
        guessing: Şans parametresi (c)
        ability: Öğrenci yeteneği (θ)

    Returns:
        Başarı olasılığı [0, 1]
    """
    import math

    # Parametre validasyonu
    if not -4.0 <= difficulty <= 4.0:
        raise ValueError(f"difficulty must be in [-4.0, 4.0], got {difficulty}")
    if not 0.2 <= discrimination <= 4.0:
        raise ValueError(f"discrimination must be in [0.2, 4.0], got {discrimination}")
    if not 0.0 <= guessing <= 0.35:
        raise ValueError(f"guessing must be in [0.0, 0.35], got {guessing}")

    # 3PL formülü
    exponent = -discrimination * (ability - difficulty)
    probability = guessing + (1 - guessing) / (1 + math.exp(exponent))

    return probability


@register_tool(
    name="zpd-analyzer",
    domains=["ai_ml", "backend"],
    description="ZPD (Zone of Proximal Development) analizi yapar",
    parameters={
        "success_probability": {"type": "float", "range": [0.0, 1.0]},
    },
)
def zpd_analyzer(success_probability: float) -> dict[str, Any]:
    """
    ZPD analizi yap.

    Optimal ZPD bölgesi: %15-85 başarı olasılığı

    Args:
        success_probability: Hesaplanan başarı olasılığı

    Returns:
        ZPD analiz sonucu
    """
    ZPD_MIN = 0.15
    ZPD_MAX = 0.85

    in_zpd = ZPD_MIN <= success_probability <= ZPD_MAX

    if success_probability < ZPD_MIN:
        recommendation = "Soru çok zor, daha kolay soru öner"
        zone = "frustration"
    elif success_probability > ZPD_MAX:
        recommendation = "Soru çok kolay, daha zor soru öner"
        zone = "comfort"
    else:
        recommendation = "Soru optimal zorlukta"
        zone = "zpd"

    return {
        "success_probability": success_probability,
        "in_zpd": in_zpd,
        "zone": zone,
        "zpd_range": {"min": ZPD_MIN, "max": ZPD_MAX},
        "recommendation": recommendation,
    }


@register_tool(
    name="turkish-text-validator",
    domains=["ai_ml", "backend"],
    description="Türkçe metin validasyonu yapar",
)
def turkish_text_validator(text: str) -> dict[str, Any]:
    """
    Türkçe metin validasyonu.

    Kontroller:
    - UTF-8 encoding
    - Türkçe karakter kullanımı
    - I/ı dönüşüm tutarlılığı

    Args:
        text: Kontrol edilecek metin

    Returns:
        Validasyon sonucu
    """
    turkish_chars = set("çÇğĞıİöÖşŞüÜ")
    text_chars = set(text)

    has_turkish = bool(turkish_chars & text_chars)

    # I/ı kontrolü
    has_wrong_i = "I" in text and "İ" not in text and any(c in text for c in "ıi")

    issues = []
    if has_wrong_i:
        issues.append("I/ı dönüşüm hatası olabilir")

    return {
        "valid": len(issues) == 0,
        "has_turkish_chars": has_turkish,
        "issues": issues,
        "char_count": len(text),
    }
