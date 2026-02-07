"""Regression Tracker - Test ve metrik regresyon takibi.

Test sonuçlarını ve metrikleri tarihsel olarak izler:
- Test result history
- Metrik karşılaştırma (coverage, duration, error rate)
- Regresyon tespiti ve uyarı
- Trend analizi
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class RegressionType(Enum):
    """Regresyon türleri."""

    COVERAGE_DROP = "coverage_drop"
    NEW_FAILURES = "new_failures"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_INCREASE = "error_rate_increase"
    DURATION_INCREASE = "duration_increase"


class Severity(Enum):
    """Regresyon şiddeti."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricSnapshot:
    """Belirli bir andaki metrik durumu."""

    timestamp: str = ""
    test_total: int = 0
    test_passed: int = 0
    test_failed: int = 0
    test_skipped: int = 0
    coverage_percent: float = 0.0
    duration_seconds: float = 0.0
    error_rate: float = 0.0
    run_id: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def pass_rate(self) -> float:
        """Test geçme oranı."""
        if self.test_total == 0:
            return 0.0
        return self.test_passed / self.test_total

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        return {
            "timestamp": self.timestamp,
            "test_total": self.test_total,
            "test_passed": self.test_passed,
            "test_failed": self.test_failed,
            "test_skipped": self.test_skipped,
            "coverage_percent": round(self.coverage_percent, 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "error_rate": round(self.error_rate, 4),
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetricSnapshot:
        """Dict'ten oluştur."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class RegressionAlert:
    """Regresyon uyarısı."""

    regression_type: RegressionType
    severity: Severity
    message: str
    current_value: float
    previous_value: float
    threshold: float
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict."""
        return {
            "type": self.regression_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "current": self.current_value,
            "previous": self.previous_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
        }


@dataclass
class RegressionConfig:
    """Regresyon tespiti eşikleri."""

    coverage_drop_threshold: float = 2.0  # %2 düşüş
    failure_increase_threshold: int = 1  # 1 yeni failure
    duration_increase_percent: float = 50.0  # %50 artış
    error_rate_increase_threshold: float = 0.05  # %5 artış
    max_history_size: int = 100


@dataclass
class RegressionTracker:
    """Regresyon takip sistemi.

    MetricSnapshot'ları kaydeder ve karşılaştırarak
    regresyon tespiti yapar.

    Example:
        >>> tracker = RegressionTracker(storage_path=Path(".claude/metrics"))
        >>> tracker.record(snapshot)
        >>> alerts = tracker.check_regressions()
    """

    storage_path: Path = field(default_factory=lambda: Path(".claude/metrics"))
    config: RegressionConfig = field(default_factory=RegressionConfig)
    _history: list[MetricSnapshot] = field(default_factory=list, init=False)
    _loaded: bool = field(default=False, init=False)

    def _ensure_loaded(self) -> None:
        """Lazy load history from disk."""
        if self._loaded:
            return
        self._loaded = True
        history_file = self.storage_path / "history.json"
        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                self._history = [MetricSnapshot.from_dict(d) for d in data]
            except (json.JSONDecodeError, KeyError):
                self._history = []

    def _save(self) -> None:
        """Save history to disk."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        history_file = self.storage_path / "history.json"
        data = [s.to_dict() for s in self._history[-self.config.max_history_size :]]
        history_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record(self, snapshot: MetricSnapshot) -> list[RegressionAlert]:
        """Yeni snapshot kaydet ve regresyon kontrolü yap.

        Args:
            snapshot: Mevcut metrik durumu.

        Returns:
            Tespit edilen regresyon uyarıları listesi.
        """
        self._ensure_loaded()
        self._history.append(snapshot)
        alerts = self.check_regressions()
        self._save()
        return alerts

    def check_regressions(self) -> list[RegressionAlert]:
        """Son snapshot'ı bir öncekiyle karşılaştır.

        Returns:
            Tespit edilen regresyon uyarıları.
        """
        self._ensure_loaded()
        if len(self._history) < 2:
            return []

        current = self._history[-1]
        previous = self._history[-2]
        alerts: list[RegressionAlert] = []

        # Coverage düşüşü
        if previous.coverage_percent > 0:
            drop = previous.coverage_percent - current.coverage_percent
            if drop >= self.config.coverage_drop_threshold:
                alerts.append(RegressionAlert(
                    regression_type=RegressionType.COVERAGE_DROP,
                    severity=Severity.ERROR if drop >= 5.0 else Severity.WARNING,
                    message=f"Coverage {previous.coverage_percent:.1f}% → {current.coverage_percent:.1f}% ({drop:.1f}% düşüş)",
                    current_value=current.coverage_percent,
                    previous_value=previous.coverage_percent,
                    threshold=self.config.coverage_drop_threshold,
                ))

        # Yeni test failure'ları
        new_failures = current.test_failed - previous.test_failed
        if new_failures >= self.config.failure_increase_threshold:
            alerts.append(RegressionAlert(
                regression_type=RegressionType.NEW_FAILURES,
                severity=Severity.ERROR,
                message=f"{new_failures} yeni test failure ({previous.test_failed} → {current.test_failed})",
                current_value=float(current.test_failed),
                previous_value=float(previous.test_failed),
                threshold=float(self.config.failure_increase_threshold),
            ))

        # Süre artışı
        if previous.duration_seconds > 0:
            increase_pct = ((current.duration_seconds - previous.duration_seconds) / previous.duration_seconds) * 100
            if increase_pct >= self.config.duration_increase_percent:
                alerts.append(RegressionAlert(
                    regression_type=RegressionType.DURATION_INCREASE,
                    severity=Severity.WARNING,
                    message=f"Test süresi {previous.duration_seconds:.1f}s → {current.duration_seconds:.1f}s ({increase_pct:.0f}% artış)",
                    current_value=current.duration_seconds,
                    previous_value=previous.duration_seconds,
                    threshold=self.config.duration_increase_percent,
                ))

        # Error rate artışı
        rate_increase = current.error_rate - previous.error_rate
        if rate_increase >= self.config.error_rate_increase_threshold:
            alerts.append(RegressionAlert(
                regression_type=RegressionType.ERROR_RATE_INCREASE,
                severity=Severity.CRITICAL if rate_increase >= 0.1 else Severity.WARNING,
                message=f"Error rate {previous.error_rate:.2%} → {current.error_rate:.2%}",
                current_value=current.error_rate,
                previous_value=previous.error_rate,
                threshold=self.config.error_rate_increase_threshold,
            ))

        return alerts

    @property
    def latest(self) -> MetricSnapshot | None:
        """En son snapshot."""
        self._ensure_loaded()
        return self._history[-1] if self._history else None

    @property
    def history_size(self) -> int:
        """Kayıtlı snapshot sayısı."""
        self._ensure_loaded()
        return len(self._history)
