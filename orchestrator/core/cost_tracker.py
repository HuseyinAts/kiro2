"""Cost Tracker - LLM maliyet izleme.

Model bazlı token ve maliyet takibi:
- Token kullanımı (input/output)
- Model bazlı maliyet hesaplama
- Budget alerting (daily/monthly)
- Aggregation (daily/weekly/monthly)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class ModelTier(Enum):
    """Model kademeleri."""

    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"
    CODEX = "codex"


# Fiyatlandırma ($ per 1M token) - Şubat 2026
MODEL_PRICING: dict[ModelTier, dict[str, float]] = {
    ModelTier.OPUS: {"input": 15.0, "output": 75.0},
    ModelTier.SONNET: {"input": 3.0, "output": 15.0},
    ModelTier.HAIKU: {"input": 0.25, "output": 1.25},
    ModelTier.CODEX: {"input": 0.5, "output": 2.0},
}


@dataclass
class UsageRecord:
    """Tek bir API çağrısının kullanım kaydı."""

    timestamp: str = ""
    model: str = ""
    model_tier: str = "sonnet"
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: float = 0.0
    task_id: str = ""
    agent_name: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.cost_usd == 0.0:
            self.cost_usd = self._calculate_cost()

    def _calculate_cost(self) -> float:
        """Maliyeti hesapla."""
        try:
            tier = ModelTier(self.model_tier)
        except ValueError:
            tier = ModelTier.SONNET
        pricing = MODEL_PRICING.get(tier, MODEL_PRICING[ModelTier.SONNET])
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "model_tier": self.model_tier,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cost_usd": self.cost_usd,
            "task_id": self.task_id,
            "agent_name": self.agent_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UsageRecord:
        """Dict'ten oluştur."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class BudgetConfig:
    """Budget limitleri."""

    daily_limit_usd: float = 50.0
    weekly_limit_usd: float = 250.0
    monthly_limit_usd: float = 800.0
    alert_threshold: float = 0.8  # %80'inde uyar


@dataclass
class BudgetAlert:
    """Budget uyarısı."""

    period: str  # "daily" | "weekly" | "monthly"
    current_spend: float
    limit: float
    percent_used: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        return {
            "period": self.period,
            "current_spend": round(self.current_spend, 4),
            "limit": self.limit,
            "percent_used": round(self.percent_used, 2),
            "message": self.message,
        }


@dataclass
class CostSummary:
    """Maliyet özeti."""

    period: str
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    by_model: dict[str, float] = field(default_factory=dict)
    by_agent: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        return {
            "period": self.period,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_requests": self.total_requests,
            "by_model": {k: round(v, 4) for k, v in self.by_model.items()},
            "by_agent": {k: round(v, 4) for k, v in self.by_agent.items()},
        }


@dataclass
class CostTracker:
    """LLM maliyet takip sistemi.

    Her API çağrısını kaydeder, budget kontrolü yapar
    ve maliyet özetleri üretir.

    Example:
        >>> tracker = CostTracker(storage_path=Path(".claude/costs"))
        >>> alerts = tracker.record(UsageRecord(
        ...     model="claude-opus-4-5", model_tier="opus",
        ...     input_tokens=5000, output_tokens=2000
        ... ))
    """

    storage_path: Path = field(default_factory=lambda: Path(".claude/costs"))
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    _records: list[UsageRecord] = field(default_factory=list, init=False)
    _loaded: bool = field(default=False, init=False)

    def _ensure_loaded(self) -> None:
        """Lazy load records."""
        if self._loaded:
            return
        self._loaded = True
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_file = self.storage_path / f"{today}.json"
        if daily_file.exists():
            try:
                data = json.loads(daily_file.read_text(encoding="utf-8"))
                self._records = [UsageRecord.from_dict(d) for d in data]
            except (json.JSONDecodeError, KeyError):
                self._records = []

    def _save(self) -> None:
        """Save to daily file."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_file = self.storage_path / f"{today}.json"
        data = [r.to_dict() for r in self._records]
        daily_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record(self, usage: UsageRecord) -> list[BudgetAlert]:
        """Kullanım kaydı ekle ve budget kontrolü yap.

        Args:
            usage: API çağrısı kullanım kaydı.

        Returns:
            Budget uyarıları (varsa).
        """
        self._ensure_loaded()
        self._records.append(usage)
        self._save()
        return self.check_budget()

    def _load_period_spend(self, days: int) -> float:
        """Son N günün toplam harcamasını hesapla."""
        total = 0.0
        today = datetime.now(timezone.utc).date()
        for i in range(days):
            day = today - timedelta(days=i)
            day_file = self.storage_path / f"{day.isoformat()}.json"
            if day == today:
                # Bugünün verileri bellekte
                total += sum(r.cost_usd for r in self._records)
            elif day_file.exists():
                try:
                    data = json.loads(day_file.read_text(encoding="utf-8"))
                    total += sum(r.get("cost_usd", 0.0) for r in data)
                except (json.JSONDecodeError, KeyError):
                    pass
        return total

    def _check_period(
        self, period: str, spend: float, limit: float,
    ) -> BudgetAlert | None:
        """Tek bir period için budget kontrolü."""
        if limit <= 0:
            return None
        pct = (spend / limit) * 100
        if pct >= 100:
            return BudgetAlert(
                period=period,
                current_spend=spend,
                limit=limit,
                percent_used=pct,
                message=f"{period.capitalize()} limit AŞILDI: ${spend:.2f} / ${limit:.2f}",
            )
        if pct >= self.budget.alert_threshold * 100:
            return BudgetAlert(
                period=period,
                current_spend=spend,
                limit=limit,
                percent_used=pct,
                message=f"{period.capitalize()} limite yaklaşılıyor: ${spend:.2f} / ${limit:.2f} ({pct:.0f}%)",
            )
        return None

    def check_budget(self) -> list[BudgetAlert]:
        """Mevcut harcamayı budget limitleriyle karşılaştır.

        Daily, weekly ve monthly limitleri kontrol eder.

        Returns:
            Aşılmış veya yaklaşılmış limitler için uyarılar.
        """
        self._ensure_loaded()
        alerts: list[BudgetAlert] = []

        # Daily
        daily_spend = sum(r.cost_usd for r in self._records)
        alert = self._check_period("daily", daily_spend, self.budget.daily_limit_usd)
        if alert:
            alerts.append(alert)

        # Weekly (son 7 gün)
        weekly_spend = self._load_period_spend(7)
        alert = self._check_period("weekly", weekly_spend, self.budget.weekly_limit_usd)
        if alert:
            alerts.append(alert)

        # Monthly (son 30 gün)
        monthly_spend = self._load_period_spend(30)
        alert = self._check_period("monthly", monthly_spend, self.budget.monthly_limit_usd)
        if alert:
            alerts.append(alert)

        return alerts

    def daily_summary(self) -> CostSummary:
        """Günlük maliyet özeti."""
        self._ensure_loaded()
        summary = CostSummary(period="daily")

        for r in self._records:
            summary.total_cost_usd += r.cost_usd
            summary.total_input_tokens += r.input_tokens
            summary.total_output_tokens += r.output_tokens
            summary.total_requests += 1

            tier = r.model_tier
            summary.by_model[tier] = summary.by_model.get(tier, 0.0) + r.cost_usd

            if r.agent_name:
                summary.by_agent[r.agent_name] = summary.by_agent.get(r.agent_name, 0.0) + r.cost_usd

        return summary
