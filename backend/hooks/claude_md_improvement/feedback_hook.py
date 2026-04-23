"""
CLAUDE.md Self-Improvement Feedback Hook.

Boris Cherny verification feedback loops prensibi ile
agent performance feedback toplama.

Exit Codes (Daisy Stanton):
- 0: Success
- 2: Blocking error (Claude'a geri beslenir)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..base import BaseHook
from ..models import HookConfig, QualityCheckResult
from .models import (
    ExitCodeResult,
    FeedbackRecord,
    FeedbackType,
    ImprovementTrigger,
    OutcomeType,
    RuleEffectiveness,
)


class FeedbackHook(BaseHook):
    """
    CLAUDE.md Self-Improvement için feedback toplama hook'u.

    Bu hook:
    - Task outcome'larını kaydeder (success/failure)
    - User feedback'i toplar (rating 1-5, comment)
    - Implicit feedback'i izler (retry count, edit frequency)
    - Per-rule effectiveness score hesaplar
    - 30-day rolling window kullanır
    - İyileştirme tetikleyicisi çalıştırır (threshold-based)

    Attributes:
        name: Hook adı
        feedback_store: Feedback kayıtları (memory)
        effectiveness_cache: Rule effectiveness cache
        improvement_threshold: İyileştirme eşiği
    """

    name: str = "claude_md_feedback"

    def __init__(
        self,
        config: HookConfig | None = None,
        storage_path: Path | None = None,
        improvement_threshold: float = 0.6,
    ):
        """
        FeedbackHook başlat.

        Args:
            config: Hook konfigürasyonu
            storage_path: Feedback depolama yolu
            improvement_threshold: İyileştirme tetikleme eşiği
        """
        super().__init__(config)
        self.storage_path = storage_path or Path("backend/data/feedback")
        self.improvement_threshold = improvement_threshold

        # In-memory stores (production'da Redis/PostgreSQL kullanılacak)
        self._feedback_store: list[FeedbackRecord] = []
        self._effectiveness_cache: dict[str, RuleEffectiveness] = {}
        self._triggers: list[ImprovementTrigger] = []

        # Rolling window
        self.window_days = 30

    async def run(self, files: list[str]) -> QualityCheckResult:
        """
        Feedback hook'u çalıştır.

        Args:
            files: Kontrol edilecek dosyalar (kullanılmıyor)

        Returns:
            QualityCheckResult
        """
        self._start_timer()

        try:
            # Mevcut feedback'leri analiz et
            rules_needing_improvement = await self._analyze_effectiveness()

            # İyileştirme gerekiyorsa trigger oluştur
            if rules_needing_improvement:
                for rule_id, score in rules_needing_improvement.items():
                    await self._create_improvement_trigger(rule_id, score)

            execution_time = self._stop_timer()

            return self._create_success_result(
                files_checked=0,
                execution_time=execution_time,
                warnings=[
                    f"{len(rules_needing_improvement)} kural iyileştirme gerektiriyor"
                ]
                if rules_needing_improvement
                else [],
            )

        except Exception as e:
            execution_time = self._stop_timer()
            return self._create_error_result(
                errors=[f"Feedback analizi başarısız: {e!s}"],
                files_checked=0,
                execution_time=execution_time,
            )

    async def record_outcome(
        self,
        task_id: str,
        success: bool,
        rule_id: str | None = None,
        execution_time: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> ExitCodeResult:
        """
        Task outcome'u kaydet.

        Args:
            task_id: Task ID
            success: Başarılı mı
            rule_id: İlgili CLAUDE.md rule ID
            execution_time: Çalışma süresi
            context: Ek bağlam

        Returns:
            ExitCodeResult
        """
        outcome = OutcomeType.SUCCESS if success else OutcomeType.FAILURE

        record = FeedbackRecord(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type=FeedbackType.AUTOMATIC,
            outcome=outcome,
            execution_time=execution_time,
            context=context or {},
        )

        self._feedback_store.append(record)

        # Rule effectiveness güncelle
        if rule_id:
            await self._update_rule_effectiveness(rule_id, success)

        return ExitCodeResult.success(f"Outcome kaydedildi: {outcome.value}")

    async def record_user_feedback(
        self,
        task_id: str,
        rating: int,
        comment: str | None = None,
        rule_id: str | None = None,
    ) -> ExitCodeResult:
        """
        Kullanıcı feedback'i kaydet.

        Args:
            task_id: Task ID
            rating: Puan (1-5)
            comment: Yorum
            rule_id: İlgili CLAUDE.md rule ID

        Returns:
            ExitCodeResult
        """
        if not 1 <= rating <= 5:
            return ExitCodeResult.blocking_error(
                f"Geçersiz rating: {rating}. 1-5 arası olmalı.",
                {"provided_rating": rating},
            )

        # Rating'e göre outcome belirle
        outcome = OutcomeType.SUCCESS if rating >= 4 else OutcomeType.FAILURE

        record = FeedbackRecord(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type=FeedbackType.EXPLICIT,
            outcome=outcome,
            rating=rating,
            comment=comment,
        )

        self._feedback_store.append(record)

        # Rule effectiveness güncelle
        if rule_id:
            await self._update_rule_effectiveness(
                rule_id, rating >= 4, explicit_score=rating / 5.0
            )

        return ExitCodeResult.success(f"User feedback kaydedildi: {rating}/5")

    async def record_implicit_feedback(
        self,
        task_id: str,
        retry_count: int = 0,
        edit_frequency: int = 0,
        rule_id: str | None = None,
    ) -> ExitCodeResult:
        """
        Implicit feedback kaydet.

        Args:
            task_id: Task ID
            retry_count: Yeniden deneme sayısı
            edit_frequency: Düzenleme sıklığı
            rule_id: İlgili CLAUDE.md rule ID

        Returns:
            ExitCodeResult
        """
        # Implicit feedback'ten outcome çıkar
        # Yüksek retry/edit = düşük başarı
        success = retry_count <= 1 and edit_frequency <= 3
        outcome = OutcomeType.SUCCESS if success else OutcomeType.PARTIAL

        record = FeedbackRecord(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type=FeedbackType.IMPLICIT,
            outcome=outcome,
            retry_count=retry_count,
            edit_frequency=edit_frequency,
        )

        self._feedback_store.append(record)

        # Implicit score hesapla (düşük retry/edit = yüksek score)
        implicit_score = 1.0 - min((retry_count + edit_frequency / 5) / 10, 1.0)

        if rule_id:
            await self._update_rule_effectiveness(
                rule_id, success, implicit_score=implicit_score
            )

        return ExitCodeResult.success(
            f"Implicit feedback kaydedildi: retry={retry_count}, edits={edit_frequency}"
        )

    async def record_test_result(
        self,
        task_id: str,
        test_passed: bool,
        lint_passed: bool = True,
        type_check_passed: bool = True,
        rule_id: str | None = None,
    ) -> ExitCodeResult:
        """
        Test sonuçlarını kaydet (Boris Cherny verification loop).

        Args:
            task_id: Task ID
            test_passed: Test geçti mi
            lint_passed: Lint geçti mi
            type_check_passed: Type check geçti mi
            rule_id: İlgili CLAUDE.md rule ID

        Returns:
            ExitCodeResult
        """
        # Tüm kontroller geçmeli
        all_passed = test_passed and lint_passed and type_check_passed
        outcome = OutcomeType.SUCCESS if all_passed else OutcomeType.FAILURE

        record = FeedbackRecord(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type=FeedbackType.AUTOMATIC,
            outcome=outcome,
            test_passed=test_passed,
            lint_passed=lint_passed,
            type_check_passed=type_check_passed,
        )

        self._feedback_store.append(record)

        if rule_id:
            await self._update_rule_effectiveness(rule_id, all_passed)

        # Exit Code 2 if any check failed (Daisy Stanton)
        if not all_passed:
            failed_checks = []
            if not test_passed:
                failed_checks.append("tests")
            if not lint_passed:
                failed_checks.append("lint")
            if not type_check_passed:
                failed_checks.append("type_check")

            return ExitCodeResult.blocking_error(
                f"Verification başarısız: {', '.join(failed_checks)}",
                {
                    "test_passed": test_passed,
                    "lint_passed": lint_passed,
                    "type_check_passed": type_check_passed,
                },
            )

        return ExitCodeResult.success("Tüm verification kontrolleri geçti")

    async def _update_rule_effectiveness(
        self,
        rule_id: str,
        success: bool,
        explicit_score: float | None = None,
        implicit_score: float | None = None,
    ) -> None:
        """Rule effectiveness güncelle."""
        if rule_id not in self._effectiveness_cache:
            self._effectiveness_cache[rule_id] = RuleEffectiveness(
                rule_id=rule_id,
                rule_text="",  # CLAUDE.md'den yüklenecek
                section="",
            )

        effectiveness = self._effectiveness_cache[rule_id]
        effectiveness.total_feedback += 1

        if success:
            effectiveness.success_count += 1
        else:
            effectiveness.failure_count += 1

        if explicit_score is not None:
            # Hareketli ortalama
            effectiveness.explicit_score = (
                effectiveness.explicit_score * 0.9 + explicit_score * 0.1
            )

        if implicit_score is not None:
            effectiveness.implicit_score = (
                effectiveness.implicit_score * 0.9 + implicit_score * 0.1
            )

        effectiveness.calculate_effectiveness()
        effectiveness.last_updated = datetime.now(UTC)

    async def _analyze_effectiveness(self) -> dict[str, float]:
        """
        Tüm kuralların effectiveness'ını analiz et.

        Returns:
            İyileştirme gerektiren kural ID'leri ve skorları
        """
        rules_needing_improvement: dict[str, float] = {}

        for rule_id, effectiveness in self._effectiveness_cache.items():
            # 30-day window kontrolü
            cutoff = datetime.now(UTC) - timedelta(days=self.window_days)
            if effectiveness.last_updated < cutoff:
                continue

            if effectiveness.needs_improvement:
                rules_needing_improvement[rule_id] = effectiveness.effectiveness_score

        return rules_needing_improvement

    async def _create_improvement_trigger(
        self, rule_id: str, current_score: float
    ) -> ImprovementTrigger:
        """İyileştirme trigger'ı oluştur."""
        trigger = ImprovementTrigger(
            rule_id=rule_id,
            trigger_reason=f"Effectiveness score ({current_score:.2f}) eşiğin ({self.improvement_threshold}) altında",
            current_score=current_score,
            threshold=self.improvement_threshold,
            suggested_actions=[
                "Rule formülasyonunu gözden geçir",
                "Alternatif ifade öner",
                "A/B test başlat",
            ],
        )

        self._triggers.append(trigger)
        return trigger

    def get_effectiveness(self, rule_id: str) -> RuleEffectiveness | None:
        """Belirli bir kuralın effectiveness'ını getir."""
        return self._effectiveness_cache.get(rule_id)

    def get_pending_triggers(self) -> list[ImprovementTrigger]:
        """İşlenmemiş trigger'ları getir."""
        return [t for t in self._triggers if not t.processed]

    async def calculate_aggregate_effectiveness(self) -> float:
        """Tüm kuralların ortalama effectiveness'ını hesapla."""
        if not self._effectiveness_cache:
            return 0.5

        total = sum(e.effectiveness_score for e in self._effectiveness_cache.values())
        return total / len(self._effectiveness_cache)

    async def get_feedback_summary(self) -> dict[str, Any]:
        """Feedback özeti getir."""
        # 30-day window
        cutoff = datetime.now(UTC) - timedelta(days=self.window_days)
        recent_feedback = [
            f for f in self._feedback_store if f.created_at >= cutoff
        ]

        # Outcome dağılımı
        outcome_counts: dict[str, int] = defaultdict(int)
        for f in recent_feedback:
            outcome_counts[f.outcome.value] += 1

        # Feedback type dağılımı
        type_counts: dict[str, int] = defaultdict(int)
        for f in recent_feedback:
            type_counts[f.feedback_type.value] += 1

        return {
            "total_feedback": len(recent_feedback),
            "window_days": self.window_days,
            "outcome_distribution": dict(outcome_counts),
            "type_distribution": dict(type_counts),
            "average_effectiveness": await self.calculate_aggregate_effectiveness(),
            "rules_tracked": len(self._effectiveness_cache),
            "pending_improvements": len(self.get_pending_triggers()),
        }
