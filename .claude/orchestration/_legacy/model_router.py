"""
Model Router - Gorev Bazli Akilli Model Secimi

Gorev tipine, karmasikliga, maliyete ve performansa gore
en uygun LLM modelini otomatik secer.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from .agent_genome import AgentModel, ModelProvider, CapabilityType


class TaskComplexity(Enum):
    """Gorev karmasiklik seviyesi"""
    TRIVIAL = "trivial"         # Basit, tek adimli
    SIMPLE = "simple"           # Kolay, az adimli
    MODERATE = "moderate"       # Orta, birden fazla adim
    COMPLEX = "complex"         # Karmasik, cok adimli
    EXPERT = "expert"           # Uzman, derin analiz gerektiren


class TaskType(Enum):
    """Gorev tipi"""
    # Kod Yazma
    CODE_GENERATION = "code_generation"
    CODE_COMPLETION = "code_completion"
    CODE_REFACTORING = "code_refactoring"

    # Kod Analizi
    CODE_REVIEW = "code_review"
    BUG_DETECTION = "bug_detection"
    SECURITY_AUDIT = "security_audit"

    # Test
    TEST_GENERATION = "test_generation"
    TEST_DEBUGGING = "test_debugging"

    # Planlama ve Tasarim
    ARCHITECTURE_DESIGN = "architecture_design"
    TASK_PLANNING = "task_planning"
    ALGORITHM_DESIGN = "algorithm_design"

    # Dokumantasyon
    DOCUMENTATION = "documentation"
    CODE_EXPLANATION = "code_explanation"

    # NLP ve Icerik
    TURKISH_NLP = "turkish_nlp"
    CONTENT_GENERATION = "content_generation"
    QUESTION_ANALYSIS = "question_analysis"

    # Debugging
    ERROR_ANALYSIS = "error_analysis"
    PERFORMANCE_DEBUGGING = "performance_debugging"

    # Genel
    CHAT = "chat"
    GENERAL = "general"


@dataclass
class RoutingDecision:
    """Model yonlendirme karari"""
    selected_model: AgentModel
    fallback_model: Optional[AgentModel]
    reasoning: str
    estimated_cost: float
    confidence: float  # 0.0 - 1.0
    constraints_applied: list[str] = field(default_factory=list)


@dataclass
class RoutingConstraints:
    """Yonlendirme kisitlamalari"""
    max_cost_per_request: float = 1.0  # USD
    preferred_providers: list[ModelProvider] = field(default_factory=list)
    excluded_providers: list[ModelProvider] = field(default_factory=list)
    min_context_window: int = 0
    prefer_speed: bool = False
    prefer_quality: bool = False
    require_reasoning: bool = False
    allow_local_models: bool = True


@dataclass
class UsageStats:
    """Model kullanim istatistikleri"""
    model: AgentModel
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0


class ModelRouter:
    """
    Akilli Model Yonlendirici

    Gorevler:
    1. Gorev tipine gore model sec
    2. Maliyet optimizasyonu
    3. Performans dengeleme
    4. Provider failover
    5. Kullanim takibi
    """

    # Gorev tipi -> Onerilen modeller (oncelik sirasina gore)
    # Guncelleme: Ocak 2026 - KIRO2 Orkestrasyon Stratejisi Uyumlu
    # Kaynak: KIRO2 Claude Code vs Codex Orkestrasyon Stratejisi Belgesi
    TASK_MODEL_MAPPING = {
        # ============================================
        # KOD YAZMA - Codex oncelikli (basit), Claude karmasik icin
        # ============================================
        TaskType.CODE_GENERATION: [
            AgentModel.GPT5_2_CODEX,       # Basit/orta kod: Codex hizli ve ucuz
            AgentModel.CLAUDE_SONNET_4_5,  # Karmasik kod: Claude kaliteli
            AgentModel.DEEPSEEK_CODER_V2,  # Yerel alternatif
        ],
        TaskType.CODE_COMPLETION: [
            AgentModel.GPT5_NANO,          # Boilerplate: En hizli, en ucuz
            AgentModel.CLAUDE_HAIKU_4_5,   # Alternatif hizli
            AgentModel.GEMINI_3_FLASH,     # Anlik tamamlama
        ],
        # KARMASIK REFACTORING -> Claude Code (Belge: cross-cutting)
        TaskType.CODE_REFACTORING: [
            AgentModel.CLAUDE_OPUS_4_5,    # Karmasik refactoring: Claude ustun
            AgentModel.CLAUDE_SONNET_4_5,  # Orta seviye refactoring
            AgentModel.GPT5_2_CODEX,       # Basit refactoring
        ],

        # ============================================
        # KOD ANALIZI - Claude Code oncelikli (Belge: guvenlik kritik)
        # ============================================
        TaskType.CODE_REVIEW: [
            AgentModel.CLAUDE_OPUS_4_5,    # En kapsamli kod inceleme
            AgentModel.O3,                 # Derin reasoning ile review
            AgentModel.GPT5,               # Flagship alternatif
        ],
        # DERIN DEBUGGING -> Claude Code (Belge: kok neden analizi)
        TaskType.BUG_DETECTION: [
            AgentModel.CLAUDE_OPUS_4_5,    # Derin bug analizi: Claude
            AgentModel.CLAUDE_SONNET_4_5,  # Orta seviye bug tespiti
            AgentModel.O4_MINI,            # Basit bug: Reasoning
        ],
        # GUVENLIK -> Claude Code (Belge: guvenlik kritik alan)
        TaskType.SECURITY_AUDIT: [
            AgentModel.CLAUDE_OPUS_4_5,    # Guvenlik: Claude zorunlu
            AgentModel.O3_PRO,             # Derin reasoning destegi
            AgentModel.GPT5,               # Kapsamli tarama
        ],

        # ============================================
        # TEST - Codex oncelikli (Belge: birim testleri Codex'e)
        # ============================================
        TaskType.TEST_GENERATION: [
            AgentModel.GPT5_2_CODEX,       # Test yazimi: Codex hizli
            AgentModel.CLAUDE_SONNET_4_5,  # Karmasik test senaryolari
            AgentModel.GEMINI_3_PRO,       # Buyuk test suite
        ],
        # KARMASIK DEBUG -> Claude (Belge: race condition, deadlock)
        TaskType.TEST_DEBUGGING: [
            AgentModel.CLAUDE_SONNET_4_5,  # Karmasik test debug: Claude
            AgentModel.O4_MINI,            # Reasoning destegi
            AgentModel.DEEPSEEK_CODER_V2,  # Yerel alternatif
        ],

        # ============================================
        # PLANLAMA VE TASARIM - Claude Code (Belge: mimari kararlar)
        # ============================================
        TaskType.ARCHITECTURE_DESIGN: [
            AgentModel.CLAUDE_OPUS_4_5,    # Mimari: Claude zorunlu
            AgentModel.O3_PRO,             # Derin reasoning destegi
            AgentModel.GPT5,               # Flagship alternatif
        ],
        TaskType.TASK_PLANNING: [
            AgentModel.CLAUDE_SONNET_4_5,  # Planlama: Claude planlar
            AgentModel.O4_MINI,            # Verimli reasoning
            AgentModel.GPT5_MINI,          # Hizli planlama
        ],
        # ALGORITMA -> Claude (Belge: algoritma tasarimi Claude'a)
        TaskType.ALGORITHM_DESIGN: [
            AgentModel.CLAUDE_OPUS_4_5,    # Algoritma: Claude zorunlu
            AgentModel.O3,                 # Derin reasoning
            AgentModel.DEEPSEEK_V3,        # Matematik guclu yerel
        ],

        # ============================================
        # DOKUMANTASYON - Codex oncelikli (Belge: boilerplate)
        # ============================================
        TaskType.DOCUMENTATION: [
            AgentModel.GPT5_2_CODEX,       # Dokumantasyon: Codex hizli
            AgentModel.GPT5_MINI,          # Alternatif ucuz
            AgentModel.CLAUDE_SONNET_4_5,  # Kaliteli dokuman
        ],
        TaskType.CODE_EXPLANATION: [
            AgentModel.GPT5_MINI,          # Aciklama: Codex hizli
            AgentModel.CLAUDE_SONNET_4_5,  # Derin aciklama
            AgentModel.GEMINI_3_FLASH,     # Anlik aciklama
        ],

        # ============================================
        # TURKCE NLP - Claude Code ZORUNLU (Belge: Turkce icerik)
        # ============================================
        TaskType.TURKISH_NLP: [
            AgentModel.CLAUDE_OPUS_4_5,    # Turkce: Claude ZORUNLU
            AgentModel.CLAUDE_SONNET_4_5,  # Alternatif Claude
            AgentModel.QWEN3_8B,           # Fine-tuned Turkce yerel
        ],
        # ICERIK URETIMI -> Claude (Belge: OSYM standartlari)
        TaskType.CONTENT_GENERATION: [
            AgentModel.CLAUDE_OPUS_4_5,    # YKS icerik: Claude ZORUNLU
            AgentModel.CLAUDE_SONNET_4_5,  # Hizli icerik
            AgentModel.QWEN3_8B,           # Turkce fine-tuned yerel
        ],
        # SORU ANALIZI -> Claude (Belge: soru analizi Claude'a)
        TaskType.QUESTION_ANALYSIS: [
            AgentModel.CLAUDE_OPUS_4_5,    # Soru analizi: Claude ZORUNLU
            AgentModel.QWEN3_8B,           # Turkce fine-tuned
            AgentModel.CLAUDE_SONNET_4_5,  # Alternatif
        ],

        # ============================================
        # DEBUGGING - Claude oncelikli (Belge: derin debugging)
        # ============================================
        TaskType.ERROR_ANALYSIS: [
            AgentModel.CLAUDE_OPUS_4_5,    # Hata analizi: Claude
            AgentModel.GEMINI_3_PRO,       # 1M+ context buyuk log
            AgentModel.GPT5,               # Flagship alternatif
        ],
        # PERFORMANS DEBUG -> Claude (Belge: bellek sizintisi, race)
        TaskType.PERFORMANCE_DEBUGGING: [
            AgentModel.CLAUDE_OPUS_4_5,    # Performans: Claude zorunlu
            AgentModel.O3,                 # Derin reasoning
            AgentModel.GPT5_2_CODEX,       # Kod odakli debug
        ],

        # ============================================
        # GENEL - Duruma gore (hibrit)
        # ============================================
        TaskType.CHAT: [
            AgentModel.CLAUDE_HAIKU_4_5,   # Chat: Hizli Claude
            AgentModel.GPT5_NANO,          # Ucuz alternatif
            AgentModel.GEMINI_3_FLASH,     # Anlik yanit
        ],
        TaskType.GENERAL: [
            AgentModel.CLAUDE_SONNET_4_5,  # Genel: Claude dengeli
            AgentModel.GPT5_MINI,          # Alternatif
            AgentModel.GEMINI_3_PRO,       # Buyuk context
        ],
    }

    # Karmasiklik -> Model tier eslestirmesi
    # Guncelleme: Ocak 2026 - flagship tier eklendi
    COMPLEXITY_TIER_MAPPING = {
        TaskComplexity.TRIVIAL: "budget",      # Haiku, Nano, Flash
        TaskComplexity.SIMPLE: "budget",       # Haiku, Nano, Flash
        TaskComplexity.MODERATE: "standard",   # Sonnet, Mini, Pro
        TaskComplexity.COMPLEX: "flagship",    # Opus, GPT-5, Gemini 3 Pro
        TaskComplexity.EXPERT: "reasoning",    # o3, o3-pro, o4-mini
    }

    def __init__(self, base_path: str = ".claude"):
        self.base_path = Path(base_path)
        self.stats_file = self.base_path / "orchestration" / "model_stats.json"

        self._usage_stats: dict[str, UsageStats] = {}
        self._default_constraints = RoutingConstraints()

    async def initialize(self) -> None:
        """Router'i baslat"""
        await self._load_stats()

    async def _load_stats(self) -> None:
        """Kullanim istatistiklerini yukle"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for model_name, stats in data.get("stats", {}).items():
                        self._usage_stats[model_name] = UsageStats(
                            model=AgentModel(model_name),
                            total_requests=stats.get("total_requests", 0),
                            total_tokens=stats.get("total_tokens", 0),
                            total_cost=stats.get("total_cost", 0.0),
                            avg_latency_ms=stats.get("avg_latency_ms", 0.0),
                            success_rate=stats.get("success_rate", 1.0),
                        )
            except Exception:
                pass

    async def _save_stats(self) -> None:
        """Kullanim istatistiklerini kaydet"""
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "stats": {
                model_name: {
                    "total_requests": stats.total_requests,
                    "total_tokens": stats.total_tokens,
                    "total_cost": stats.total_cost,
                    "avg_latency_ms": stats.avg_latency_ms,
                    "success_rate": stats.success_rate,
                }
                for model_name, stats in self._usage_stats.items()
            },
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    async def route(
        self,
        task_type: TaskType,
        complexity: TaskComplexity = TaskComplexity.MODERATE,
        constraints: Optional[RoutingConstraints] = None,
        context_size: int = 0,
        capability_required: Optional[CapabilityType] = None,
    ) -> RoutingDecision:
        """
        Gorev icin en uygun modeli sec

        Args:
            task_type: Gorev tipi
            complexity: Karmasiklik seviyesi
            constraints: Yonlendirme kisitlamalari
            context_size: Gerekli context boyutu (token)
            capability_required: Gerekli yetenek

        Returns:
            RoutingDecision
        """
        constraints = constraints or self._default_constraints
        applied_constraints = []

        # 1. Gorev tipine gore aday modeller
        candidates = self.TASK_MODEL_MAPPING.get(
            task_type,
            self.TASK_MODEL_MAPPING[TaskType.GENERAL]
        ).copy()

        # 2. Karmasiklik filtresi
        target_tier = self.COMPLEXITY_TIER_MAPPING[complexity]
        if constraints.require_reasoning:
            target_tier = "reasoning"
            applied_constraints.append("require_reasoning")

        # 3. Provider filtresi
        if constraints.preferred_providers:
            candidates = [
                m for m in candidates
                if m.provider in constraints.preferred_providers
            ] or candidates
            applied_constraints.append(f"preferred_providers: {[p.value for p in constraints.preferred_providers]}")

        if constraints.excluded_providers:
            candidates = [
                m for m in candidates
                if m.provider not in constraints.excluded_providers
            ]
            applied_constraints.append(f"excluded_providers: {[p.value for p in constraints.excluded_providers]}")

        # 4. Context window filtresi
        if context_size > 0:
            candidates = [
                m for m in candidates
                if m.context_window >= context_size
            ] or candidates
            if context_size > 100000:
                applied_constraints.append(f"min_context: {context_size}")

        # 5. Maliyet filtresi
        if constraints.max_cost_per_request < 1.0:
            # Tahmini maliyet hesapla (ortalama 2000 token)
            candidates = [
                m for m in candidates
                if self._estimate_cost(m, 2000, 2000) <= constraints.max_cost_per_request
            ] or candidates
            applied_constraints.append(f"max_cost: ${constraints.max_cost_per_request}")

        # 6. Local model filtresi
        if not constraints.allow_local_models:
            candidates = [
                m for m in candidates
                if m.provider != ModelProvider.LOCAL
            ]
            applied_constraints.append("no_local_models")

        # 7. Hiz vs Kalite tercihi
        if constraints.prefer_speed:
            # Budget modelleri one al
            candidates.sort(key=lambda m: (
                0 if m.tier == "budget" else 1,
                m.cost_per_1k_tokens["input"]
            ))
            applied_constraints.append("prefer_speed")
        elif constraints.prefer_quality:
            # Premium modelleri one al
            candidates.sort(key=lambda m: (
                0 if m.tier in ("premium", "reasoning") else 1,
                -m.cost_per_1k_tokens["input"]  # Pahali = kaliteli varsayimi
            ))
            applied_constraints.append("prefer_quality")

        # 8. Tier bazli filtreleme
        tier_filtered = [m for m in candidates if m.tier == target_tier]
        if not tier_filtered:
            # Bir ust tier'a bak
            tier_order = ["budget", "standard", "flagship", "premium", "reasoning"]
            target_idx = tier_order.index(target_tier) if target_tier in tier_order else 1
            for i in range(target_idx, len(tier_order)):
                tier_filtered = [m for m in candidates if m.tier == tier_order[i]]
                if tier_filtered:
                    break
        if tier_filtered:
            candidates = tier_filtered

        # 9. Final secim
        if not candidates:
            candidates = [AgentModel.CLAUDE_SONNET_4_5]  # Fallback - Ocak 2026

        selected = candidates[0]
        fallback = candidates[1] if len(candidates) > 1 else None

        # 10. Maliyet tahmini
        estimated_cost = self._estimate_cost(selected, 2000, 2000)

        # 11. Confidence hesapla
        confidence = self._calculate_confidence(
            selected, task_type, complexity, constraints
        )

        # 12. Reasoning olustur
        reasoning = self._generate_reasoning(
            selected, task_type, complexity, applied_constraints
        )

        return RoutingDecision(
            selected_model=selected,
            fallback_model=fallback,
            reasoning=reasoning,
            estimated_cost=estimated_cost,
            confidence=confidence,
            constraints_applied=applied_constraints,
        )

    def _estimate_cost(
        self,
        model: AgentModel,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Maliyet tahmini"""
        costs = model.cost_per_1k_tokens
        return (
            (input_tokens / 1000) * costs["input"] +
            (output_tokens / 1000) * costs["output"]
        )

    def _calculate_confidence(
        self,
        model: AgentModel,
        task_type: TaskType,
        complexity: TaskComplexity,
        constraints: RoutingConstraints
    ) -> float:
        """Secim guven skoru"""
        confidence = 0.8  # Base

        # Model-task uyumu
        preferred = self.TASK_MODEL_MAPPING.get(task_type, [])
        if model in preferred[:2]:
            confidence += 0.1
        elif model not in preferred:
            confidence -= 0.2

        # Tier uyumu
        target_tier = self.COMPLEXITY_TIER_MAPPING[complexity]
        if model.tier == target_tier:
            confidence += 0.1
        elif model.tier in ("premium", "reasoning") and target_tier in ("budget", "standard"):
            confidence += 0.05  # Overkill ama calisir

        # Constraint uyumu
        if constraints.prefer_speed and model.tier == "budget":
            confidence += 0.05
        if constraints.prefer_quality and model.tier in ("premium", "reasoning"):
            confidence += 0.05

        return min(1.0, max(0.0, confidence))

    def _generate_reasoning(
        self,
        model: AgentModel,
        task_type: TaskType,
        complexity: TaskComplexity,
        constraints: list[str]
    ) -> str:
        """Secim aciklamasi olustur - Ocak 2026 guncelleme"""
        parts = [
            f"Selected {model.value} for {task_type.value}",
            f"(complexity: {complexity.value}, tier: {model.tier})",
        ]

        if model.provider == ModelProvider.ANTHROPIC:
            if "opus" in model.value:
                parts.append("Claude Opus 4.5: En guclu Turkce ve kod analizi. 64K output.")
            elif "sonnet" in model.value:
                parts.append("Claude Sonnet 4.5: Dengeli performans ve maliyet.")
            else:
                parts.append("Claude Haiku 4.5: Ultra-hizli, dusuk maliyet.")
        elif model.provider == ModelProvider.OPENAI:
            if "o3" in model.value or "o4" in model.value:
                parts.append("o-serisi: Derin reasoning ve problem cozme.")
            elif "codex" in model.value:
                parts.append("GPT-5.2 Codex: Agentic coding icin optimize edildi.")
            elif "gpt-5" in model.value:
                parts.append("GPT-5: Flagship model, 256K context, multimodal.")
            else:
                parts.append("OpenAI: Hizli ve guvenilir performans.")
        elif model.provider == ModelProvider.GOOGLE:
            if "flash" in model.value:
                parts.append("Gemini Flash: Anlik yanit, dusuk maliyet.")
            else:
                parts.append("Gemini 3 Pro: 1M+ context, buyuk dosya analizi.")
        elif model.provider == ModelProvider.LOCAL:
            parts.append("Yerel model: Sifir maliyet, hizli yanit, veri gizliligi.")

        if constraints:
            parts.append(f"Constraints: {', '.join(constraints)}")

        return " ".join(parts)

    async def record_usage(
        self,
        model: AgentModel,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        success: bool
    ) -> None:
        """Model kullanimini kaydet"""
        model_key = model.value

        if model_key not in self._usage_stats:
            self._usage_stats[model_key] = UsageStats(model=model)

        stats = self._usage_stats[model_key]
        stats.total_requests += 1
        stats.total_tokens += input_tokens + output_tokens
        stats.total_cost += self._estimate_cost(model, input_tokens, output_tokens)

        # Rolling average latency
        stats.avg_latency_ms = (
            (stats.avg_latency_ms * (stats.total_requests - 1) + latency_ms) /
            stats.total_requests
        )

        # Success rate
        if not success:
            total_success = stats.success_rate * (stats.total_requests - 1)
            stats.success_rate = total_success / stats.total_requests
        else:
            total_success = stats.success_rate * (stats.total_requests - 1) + 1
            stats.success_rate = total_success / stats.total_requests

        await self._save_stats()

    async def get_provider_status(self) -> dict:
        """Provider durum raporu"""
        status = {}
        for provider in ModelProvider:
            provider_stats = [
                s for s in self._usage_stats.values()
                if s.model.provider == provider
            ]
            if provider_stats:
                status[provider.value] = {
                    "total_requests": sum(s.total_requests for s in provider_stats),
                    "total_cost": sum(s.total_cost for s in provider_stats),
                    "avg_success_rate": sum(s.success_rate for s in provider_stats) / len(provider_stats),
                }
            else:
                status[provider.value] = {
                    "total_requests": 0,
                    "total_cost": 0.0,
                    "avg_success_rate": 1.0,
                }
        return status

    async def get_cost_report(self) -> dict:
        """Maliyet raporu"""
        total_cost = sum(s.total_cost for s in self._usage_stats.values())
        by_provider = {}
        by_model = {}

        for model_key, stats in self._usage_stats.items():
            provider = stats.model.provider.value
            by_provider[provider] = by_provider.get(provider, 0) + stats.total_cost
            by_model[model_key] = stats.total_cost

        return {
            "total_cost_usd": total_cost,
            "by_provider": by_provider,
            "by_model": dict(sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:10]),
            "total_requests": sum(s.total_requests for s in self._usage_stats.values()),
            "total_tokens": sum(s.total_tokens for s in self._usage_stats.values()),
        }

    def get_recommended_model(
        self,
        capability: CapabilityType
    ) -> AgentModel:
        """
        Yetenek bazli model onerisi - KIRO2 Orkestrasyon Stratejisi Uyumlu

        Belge kurallari:
        - Turkce icerik ve guvenlik -> Claude Code
        - UI/UX ve boilerplate -> Codex
        - Karmasik isler -> Claude planlar, Codex uygular
        """
        capability_mapping = {
            # ============================================
            # CLAUDE CODE ZORUNLU ALANLAR
            # ============================================
            # Turkce NLP: Claude ZORUNLU (Belge: Turkce icerik)
            CapabilityType.NLP: AgentModel.CLAUDE_OPUS_4_5,
            # Analiz: Derin analiz Claude (Belge: karmasik analiz)
            CapabilityType.ANALYSIS: AgentModel.CLAUDE_OPUS_4_5,
            # Kod inceleme: Guvenlik kritik (Belge: guvenlik denetimi)
            CapabilityType.REVIEW: AgentModel.CLAUDE_OPUS_4_5,
            # Debugging: Derin debug Claude (Belge: kok neden analizi)
            CapabilityType.DEBUGGING: AgentModel.CLAUDE_OPUS_4_5,
            # Database: Sema tasarimi Claude (Belge: veritabani tasarimi)
            CapabilityType.DATABASE: AgentModel.CLAUDE_OPUS_4_5,
            # Icerik: YKS/OSYM standartlari (Belge: Turkce icerik)
            CapabilityType.CONTENT: AgentModel.CLAUDE_OPUS_4_5,

            # ============================================
            # CODEX ONCELIKLI ALANLAR
            # ============================================
            # Frontend: React bilesenleri (Belge: UI/UX Codex'e)
            CapabilityType.FRONTEND: AgentModel.GPT5_2_CODEX,
            # Backend: CRUD endpoint'leri (Belge: basit API Codex'e)
            CapabilityType.BACKEND: AgentModel.GPT5_2_CODEX,
            # Kod yazma: Boilerplate (Belge: standart pattern)
            CapabilityType.CODING: AgentModel.GPT5_2_CODEX,
            # Test: Birim testleri (Belge: test yazimi Codex'e)
            CapabilityType.TESTING: AgentModel.GPT5_2_CODEX,
            # DevOps: CI/CD (Belge: DevOps Codex'e)
            CapabilityType.DEVOPS: AgentModel.GPT5_2_CODEX,

            # ============================================
            # HIBRIT ALANLAR
            # ============================================
            # Koordinasyon: Planlama Claude, uygulama Codex
            CapabilityType.COORDINATION: AgentModel.CLAUDE_SONNET_4_5,
            # Ogrenme: Adaptif sistem Claude
            CapabilityType.LEARNING: AgentModel.CLAUDE_SONNET_4_5,
        }
        return capability_mapping.get(capability, AgentModel.CLAUDE_SONNET_4_5)

    def get_statistics(self) -> dict:
        """Router istatistikleri"""
        return {
            "total_models_used": len(self._usage_stats),
            "total_requests": sum(s.total_requests for s in self._usage_stats.values()),
            "total_cost": sum(s.total_cost for s in self._usage_stats.values()),
            "providers_active": len(set(s.model.provider for s in self._usage_stats.values())),
        }
