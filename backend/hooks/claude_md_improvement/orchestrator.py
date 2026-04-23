"""
CLAUDE.md Self-Improvement Orchestrator.

Boris Cherny verification feedback loops ve Daisy Stanton
Exit Code mekanizması ile improvement sürecini koordine eder.

Data Flow:
    TaskCompletion → [Hook Trigger] → FeedbackCollector → PatternDetector → RuleEvolver
                          ↓                                                      ↓
                  verification-agent                                        ABTesting
                  test-runner (subagent)                                         ↓
                                                                           MetaLearning
                                                                                 ↓
                                                                           DocUpdater
                                                                                 ↓
                                                                       PerformanceMonitor
                                                                                 ↓
                                                           SafetyGuardrails → [Exit Code 2 if blocked]
                                                                                 ↓
                                                           [MCP: chromadb-mcp, zemberek-mcp]
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .feedback_hook import FeedbackHook
from .models import (
    ExitCodeResult,
    ImprovementTrigger,
    RuleEffectiveness,
)


class ImprovementOrchestrator:
    """
    CLAUDE.md Self-Improvement sürecini koordine eder.

    Bu orchestrator:
    - Feedback toplama ve analizi
    - Pattern detection tetikleme
    - Rule evolution koordinasyonu
    - Safety guardrails uygulama
    - Exit Code 2 mekanizması (Daisy Stanton)

    Attributes:
        feedback_hook: Feedback toplama hook'u
        claude_md_path: CLAUDE.md dosya yolu
        improvement_callbacks: İyileştirme callback'leri
    """

    def __init__(
        self,
        claude_md_path: Path | None = None,
        safety_enabled: bool = True,
        auto_improvement: bool = False,
    ):
        """
        ImprovementOrchestrator başlat.

        Args:
            claude_md_path: CLAUDE.md dosya yolu
            safety_enabled: Safety guardrails aktif mi
            auto_improvement: Otomatik iyileştirme aktif mi
        """
        self.claude_md_path = claude_md_path or Path("CLAUDE.md")
        self.safety_enabled = safety_enabled
        self.auto_improvement = auto_improvement

        # Core components
        self.feedback_hook = FeedbackHook()

        # Callbacks for extensibility
        self._improvement_callbacks: list[
            Callable[[ImprovementTrigger], Awaitable[None]]
        ] = []
        self._safety_callbacks: list[
            Callable[[dict[str, Any]], Awaitable[ExitCodeResult]]
        ] = []

        # State
        self._is_running = False
        self._last_analysis: datetime | None = None
        self._emergency_stop = False

    async def start(self) -> ExitCodeResult:
        """
        Orchestrator'ı başlat.

        Returns:
            ExitCodeResult
        """
        if self._emergency_stop:
            return ExitCodeResult.blocking_error(
                "Emergency stop aktif. Manuel restart gerekli."
            )

        self._is_running = True
        return ExitCodeResult.success("ImprovementOrchestrator başlatıldı")

    async def stop(self) -> ExitCodeResult:
        """
        Orchestrator'ı durdur.

        Returns:
            ExitCodeResult
        """
        self._is_running = False
        return ExitCodeResult.success("ImprovementOrchestrator durduruldu")

    async def emergency_stop(self, reason: str) -> ExitCodeResult:
        """
        Acil durum durdurması (REQ-8.6).

        Args:
            reason: Durdurma nedeni

        Returns:
            ExitCodeResult
        """
        self._emergency_stop = True
        self._is_running = False

        return ExitCodeResult.blocking_error(
            f"EMERGENCY STOP: {reason}. Manuel restart gerekli.",
            {"emergency_stop_at": datetime.now(UTC).isoformat(), "reason": reason},
        )

    async def record_task_completion(
        self,
        task_id: str,
        success: bool,
        rule_id: str | None = None,
        execution_time: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> ExitCodeResult:
        """
        Task tamamlanmasını kaydet ve analiz et.

        Args:
            task_id: Task ID
            success: Başarılı mı
            rule_id: İlgili CLAUDE.md rule ID
            execution_time: Çalışma süresi
            context: Ek bağlam

        Returns:
            ExitCodeResult
        """
        if not self._is_running:
            return ExitCodeResult.blocking_error(
                "Orchestrator çalışmıyor. start() çağırın."
            )

        # 1. Feedback kaydet
        result = await self.feedback_hook.record_outcome(
            task_id=task_id,
            success=success,
            rule_id=rule_id,
            execution_time=execution_time,
            context=context,
        )

        if result.exit_code != 0:
            return result

        # 2. Otomatik analiz (her 10 task'ta bir)
        if len(self.feedback_hook._feedback_store) % 10 == 0:
            await self._run_periodic_analysis()

        return result

    async def record_verification_result(
        self,
        task_id: str,
        test_passed: bool,
        lint_passed: bool = True,
        type_check_passed: bool = True,
        rule_id: str | None = None,
    ) -> ExitCodeResult:
        """
        Boris Cherny verification sonuçlarını kaydet.

        Args:
            task_id: Task ID
            test_passed: Test geçti mi
            lint_passed: Lint geçti mi
            type_check_passed: Type check geçti mi
            rule_id: İlgili CLAUDE.md rule ID

        Returns:
            ExitCodeResult (Exit Code 2 if failed)
        """
        if not self._is_running:
            return ExitCodeResult.blocking_error(
                "Orchestrator çalışmıyor. start() çağırın."
            )

        return await self.feedback_hook.record_test_result(
            task_id=task_id,
            test_passed=test_passed,
            lint_passed=lint_passed,
            type_check_passed=type_check_passed,
            rule_id=rule_id,
        )

    async def _run_periodic_analysis(self) -> None:
        """Periyodik analiz çalıştır."""
        self._last_analysis = datetime.now(UTC)

        # Feedback hook'u çalıştır
        await self.feedback_hook.run([])

        # İyileştirme trigger'larını işle
        pending_triggers = self.feedback_hook.get_pending_triggers()

        for trigger in pending_triggers:
            # Safety check
            if self.safety_enabled:
                safety_result = await self._check_safety(trigger)
                if safety_result.exit_code != 0:
                    continue  # Skip risky improvements

            # Callbacks çağır
            for callback in self._improvement_callbacks:
                try:
                    await callback(trigger)
                except Exception:
                    pass  # Log error in production

            # Auto-improvement aktifse uygula
            if self.auto_improvement:
                await self._apply_improvement(trigger)

            trigger.processed = True
            trigger.processed_at = datetime.now(UTC)

    async def _check_safety(self, trigger: ImprovementTrigger) -> ExitCodeResult:
        """
        Safety guardrails kontrol et (REQ-8).

        Args:
            trigger: İyileştirme trigger'ı

        Returns:
            ExitCodeResult
        """
        # Risky patterns kontrol
        risky_keywords = ["delete", "drop", "truncate", "remove all", "force"]

        for action in trigger.suggested_actions:
            action_lower = action.lower()
            if any(kw in action_lower for kw in risky_keywords):
                return ExitCodeResult.blocking_error(
                    f"Riskli aksiyon tespit edildi: {action}",
                    {"trigger_id": str(trigger.trigger_id), "action": action},
                )

        # Custom safety callbacks
        for callback in self._safety_callbacks:
            result = await callback(
                {
                    "trigger": trigger.model_dump(),
                    "rule_id": trigger.rule_id,
                    "actions": trigger.suggested_actions,
                }
            )
            if result.exit_code != 0:
                return result

        return ExitCodeResult.success("Safety check geçti")

    async def _apply_improvement(self, trigger: ImprovementTrigger) -> ExitCodeResult:
        """
        İyileştirmeyi uygula (auto-improvement mode).

        Args:
            trigger: İyileştirme trigger'ı

        Returns:
            ExitCodeResult
        """
        # TODO: Gerçek implementasyon Phase 3'te yapılacak
        # Şimdilik sadece log
        return ExitCodeResult.success(
            f"İyileştirme planlandı: {trigger.rule_id} (auto-apply devre dışı)"
        )

    def register_improvement_callback(
        self, callback: Callable[[ImprovementTrigger], Awaitable[None]]
    ) -> None:
        """İyileştirme callback'i kaydet."""
        self._improvement_callbacks.append(callback)

    def register_safety_callback(
        self, callback: Callable[[dict[str, Any]], Awaitable[ExitCodeResult]]
    ) -> None:
        """Safety callback'i kaydet."""
        self._safety_callbacks.append(callback)

    async def get_status(self) -> dict[str, Any]:
        """Orchestrator durumunu getir."""
        feedback_summary = await self.feedback_hook.get_feedback_summary()

        return {
            "is_running": self._is_running,
            "emergency_stop": self._emergency_stop,
            "safety_enabled": self.safety_enabled,
            "auto_improvement": self.auto_improvement,
            "last_analysis": (
                self._last_analysis.isoformat() if self._last_analysis else None
            ),
            "feedback_summary": feedback_summary,
            "improvement_callbacks_count": len(self._improvement_callbacks),
            "safety_callbacks_count": len(self._safety_callbacks),
        }

    async def get_rule_effectiveness(
        self, rule_id: str
    ) -> RuleEffectiveness | None:
        """Belirli bir kuralın effectiveness'ını getir."""
        return self.feedback_hook.get_effectiveness(rule_id)

    async def trigger_manual_analysis(self) -> dict[str, Any]:
        """Manuel analiz tetikle."""
        await self._run_periodic_analysis()

        return {
            "analyzed_at": datetime.now(UTC).isoformat(),
            "pending_improvements": [
                t.model_dump() for t in self.feedback_hook.get_pending_triggers()
            ],
            "average_effectiveness": await self.feedback_hook.calculate_aggregate_effectiveness(),
        }


# Singleton instance
_orchestrator_instance: ImprovementOrchestrator | None = None


def get_orchestrator() -> ImprovementOrchestrator:
    """Singleton orchestrator instance getir."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ImprovementOrchestrator()
    return _orchestrator_instance


async def init_orchestrator(
    claude_md_path: Path | None = None,
    safety_enabled: bool = True,
    auto_improvement: bool = False,
) -> ImprovementOrchestrator:
    """
    Orchestrator'ı başlat ve döndür.

    Args:
        claude_md_path: CLAUDE.md dosya yolu
        safety_enabled: Safety guardrails aktif mi
        auto_improvement: Otomatik iyileştirme aktif mi

    Returns:
        ImprovementOrchestrator instance
    """
    global _orchestrator_instance
    _orchestrator_instance = ImprovementOrchestrator(
        claude_md_path=claude_md_path,
        safety_enabled=safety_enabled,
        auto_improvement=auto_improvement,
    )
    await _orchestrator_instance.start()
    return _orchestrator_instance
