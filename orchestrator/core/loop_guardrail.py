"""Loop Guardrail - Sonsuz döngü koruması.

Orchestrator'ın sonsuz döngüye girmesini önler:
- Max iteration limiti
- Timeout kontrolü
- Tekrarlayan state tespiti (error fingerprint)
- No-progress detection
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .state import RunState, TaskStatus


class GuardrailAction(Enum):
    """Guardrail kararları."""

    CONTINUE = "continue"
    WARN = "warn"
    HALT = "halt"


class ViolationType(Enum):
    """İhlal türleri."""

    MAX_ITERATIONS = "max_iterations"
    TIMEOUT = "timeout"
    REPEATED_ERROR = "repeated_error"
    NO_PROGRESS = "no_progress"
    RESOURCE_LIMIT = "resource_limit"


@dataclass
class GuardrailConfig:
    """Guardrail konfigürasyonu."""

    max_iterations: int = 10
    timeout_seconds: float = 600.0
    max_repeated_errors: int = 3
    no_progress_threshold: int = 3
    warn_at_iteration: int = 7
    max_total_tokens: int = 500_000


@dataclass
class GuardrailResult:
    """Guardrail kontrol sonucu."""

    action: GuardrailAction
    violation: ViolationType | None = None
    message: str = ""
    iteration: int = 0
    elapsed_seconds: float = 0.0


@dataclass
class LoopGuardrail:
    """Orchestrator döngü koruması.

    Her iterasyonda check() çağrılır. RunState'deki error
    fingerprint'leri ve iterasyon sayısını izler.

    Example:
        >>> guardrail = LoopGuardrail()
        >>> result = guardrail.check(state)
        >>> if result.action == GuardrailAction.HALT:
        ...     # Döngüyü durdur
    """

    config: GuardrailConfig = field(default_factory=GuardrailConfig)
    _start_time: float = field(default_factory=time.monotonic, init=False)
    _state_hashes: list[str] = field(default_factory=list, init=False)
    _error_counts: dict[str, int] = field(default_factory=dict, init=False)

    def reset(self) -> None:
        """Guardrail state'ini sıfırla. Yeni task başlangıcında çağır."""
        self._start_time = time.monotonic()
        self._state_hashes.clear()
        self._error_counts.clear()

    def check(self, state: RunState) -> GuardrailResult:
        """State'i kontrol et ve aksiyon belirle.

        Args:
            state: Mevcut RunState.

        Returns:
            GuardrailResult with action (CONTINUE/WARN/HALT).
        """
        elapsed = time.monotonic() - self._start_time
        iteration = state.current_iteration

        # 1. Max iteration kontrolü
        if iteration >= self.config.max_iterations:
            return GuardrailResult(
                action=GuardrailAction.HALT,
                violation=ViolationType.MAX_ITERATIONS,
                message=f"Max iteration ({self.config.max_iterations}) aşıldı",
                iteration=iteration,
                elapsed_seconds=elapsed,
            )

        # 2. Timeout kontrolü
        if elapsed >= self.config.timeout_seconds:
            return GuardrailResult(
                action=GuardrailAction.HALT,
                violation=ViolationType.TIMEOUT,
                message=f"Timeout ({self.config.timeout_seconds}s) aşıldı",
                iteration=iteration,
                elapsed_seconds=elapsed,
            )

        # 3. Tekrarlayan error kontrolü
        repeated = self._check_repeated_errors(state)
        if repeated is not None:
            return repeated

        # 4. No-progress kontrolü
        no_progress = self._check_no_progress(state)
        if no_progress is not None:
            return no_progress

        # 5. Warning kontrolü
        if iteration >= self.config.warn_at_iteration:
            return GuardrailResult(
                action=GuardrailAction.WARN,
                message=f"İterasyon {iteration}/{self.config.max_iterations} - limite yaklaşılıyor",
                iteration=iteration,
                elapsed_seconds=elapsed,
            )

        return GuardrailResult(
            action=GuardrailAction.CONTINUE,
            iteration=iteration,
            elapsed_seconds=elapsed,
        )

    def _check_repeated_errors(self, state: RunState) -> GuardrailResult | None:
        """Aynı hatanın tekrarlanıp tekrarlanmadığını kontrol et."""
        if not state.errors:
            return None

        last_error = state.errors[-1]
        fingerprint = _error_fingerprint(last_error)

        self._error_counts[fingerprint] = self._error_counts.get(fingerprint, 0) + 1

        if self._error_counts[fingerprint] >= self.config.max_repeated_errors:
            return GuardrailResult(
                action=GuardrailAction.HALT,
                violation=ViolationType.REPEATED_ERROR,
                message=f"Aynı hata {self._error_counts[fingerprint]} kez tekrarlandı: {last_error[:100]}",
                iteration=state.current_iteration,
                elapsed_seconds=time.monotonic() - self._start_time,
            )
        return None

    def _check_no_progress(self, state: RunState) -> GuardrailResult | None:
        """State değişip değişmediğini kontrol et."""
        current_hash = _state_hash(state)
        self._state_hashes.append(current_hash)

        if len(self._state_hashes) < self.config.no_progress_threshold + 1:
            return None

        recent = self._state_hashes[-self.config.no_progress_threshold :]
        if len(set(recent)) == 1:
            return GuardrailResult(
                action=GuardrailAction.HALT,
                violation=ViolationType.NO_PROGRESS,
                message=f"Son {self.config.no_progress_threshold} iterasyonda ilerleme yok",
                iteration=state.current_iteration,
                elapsed_seconds=time.monotonic() - self._start_time,
            )
        return None


def _error_fingerprint(error: str) -> str:
    """Hata mesajından fingerprint oluştur."""
    normalized = error.strip().lower()[:200]
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def _state_hash(state: RunState) -> str:
    """State'in hash'ini oluştur (ilerleme tespiti için)."""
    status_val = state.status.value if hasattr(state.status, "value") else str(state.status)
    key_fields = f"{status_val}:{state.current_iteration}:{len(state.errors)}"
    return hashlib.md5(key_fields.encode()).hexdigest()[:12]
