"""
CLAUDE.md Self-Improvement Feedback Collection Service.

Bu servis, agent performance feedback toplama ve analiz işlemlerini yönetir.

Spec: claude-md-self-improvement REQ-1 (Feedback Collection)
- REQ-1.1: Success/failure outcome kaydetme
- REQ-1.2: User rating (1-5) ve comment saklama
- REQ-1.3: Implicit feedback analizi (retry count, edit frequency)
- REQ-1.4: Per-rule effectiveness score hesaplama
- REQ-1.5: Improvement trigger (threshold < 0.6)
- REQ-1.6: 30-day rolling window

Boris Cherny Standards - Verification Feedback Loops
Daisy Stanton Standards - Exit Code 2 Mekanizması

Author: KIRO2 Team
Date: 2026-01-17
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from backend.hooks.claude_md_improvement.models import (
    ExitCodeResult,
    ImprovementTrigger,
    RuleEffectiveness,
)
from backend.models.claude_md_improvement_models import (
    AuditLog,
)
from backend.models.claude_md_improvement_models import (
    FeedbackRecord as FeedbackRecordDB,
)
from backend.models.claude_md_improvement_models import (
    ImprovementTrigger as ImprovementTriggerDB,
)
from backend.models.claude_md_improvement_models import (
    RuleEffectiveness as RuleEffectivenessDB,
)
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class FeedbackService:
    """
    Agent performance feedback toplama ve analiz servisi.

    Bu servis:
    - Task outcome kaydetme (success/failure)
    - User feedback kaydetme (rating 1-5, comment)
    - Implicit feedback izleme (retry count, edit frequency)
    - Per-rule effectiveness score hesaplama
    - 30-day rolling window ile analiz
    - İyileştirme trigger'ı oluşturma (threshold-based)

    Attributes:
        window_days: Değerlendirme penceresi (gün)
        improvement_threshold: İyileştirme tetikleme eşiği
        explicit_weight: Explicit feedback ağırlığı
        implicit_weight: Implicit feedback ağırlığı
    """

    def __init__(
        self,
        window_days: int = 30,
        improvement_threshold: float = 0.6,
        explicit_weight: float = 0.7,
        implicit_weight: float = 0.3,
    ):
        """
        FeedbackService başlat.

        Args:
            window_days: Değerlendirme penceresi (gün)
            improvement_threshold: İyileştirme tetikleme eşiği
            explicit_weight: Explicit feedback ağırlığı
            implicit_weight: Implicit feedback ağırlığı
        """
        self.window_days = window_days
        self.improvement_threshold = improvement_threshold
        self.explicit_weight = explicit_weight
        self.implicit_weight = implicit_weight

    async def record_outcome(
        self,
        session: AsyncSession,
        task_id: str,
        success: bool,
        rule_id: str | None = None,
        execution_time: float = 0.0,
        session_id: str | None = None,
        agent_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ExitCodeResult:
        """
        Task outcome kaydeder (REQ-1.1).

        Args:
            session: Database session
            task_id: Task ID
            success: Başarılı mı
            rule_id: İlgili CLAUDE.md rule ID
            execution_time: Çalışma süresi
            session_id: Claude Code session ID
            agent_type: Agent türü
            context: Ek bağlam

        Returns:
            ExitCodeResult
        """
        outcome = "success" if success else "failure"

        # Create feedback record
        record = FeedbackRecordDB(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type="automatic",
            outcome=outcome,
            execution_time=execution_time,
            session_id=session_id,
            agent_type=agent_type,
            context=context or {},
        )

        session.add(record)

        # Update rule effectiveness
        if rule_id:
            await self._update_effectiveness(session, rule_id, success)

        # Audit log
        await self._log_action(
            session,
            action="record_outcome",
            entity_type="feedback",
            entity_id=task_id,
            actor=agent_type or "system",
            details={"success": success, "rule_id": rule_id},
        )

        await session.commit()

        return ExitCodeResult.success(f"Outcome kaydedildi: {outcome}")

    async def record_user_feedback(
        self,
        session: AsyncSession,
        task_id: str,
        rating: int,
        comment: str | None = None,
        rule_id: str | None = None,
    ) -> ExitCodeResult:
        """
        Kullanıcı feedback'i kaydeder (REQ-1.2).

        Args:
            session: Database session
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

        # Rating'e göre outcome
        outcome = "success" if rating >= 4 else "failure"

        record = FeedbackRecordDB(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type="explicit",
            outcome=outcome,
            rating=rating,
            comment=comment,
        )

        session.add(record)

        # Update effectiveness with explicit score
        if rule_id:
            explicit_score = rating / 5.0
            await self._update_effectiveness(
                session, rule_id, rating >= 4, explicit_score=explicit_score
            )

        await self._log_action(
            session,
            action="record_user_feedback",
            entity_type="feedback",
            entity_id=task_id,
            actor="user",
            details={"rating": rating, "rule_id": rule_id},
        )

        await session.commit()

        return ExitCodeResult.success(f"User feedback kaydedildi: {rating}/5")

    async def record_implicit_feedback(
        self,
        session: AsyncSession,
        task_id: str,
        retry_count: int = 0,
        edit_frequency: int = 0,
        rule_id: str | None = None,
    ) -> ExitCodeResult:
        """
        Implicit feedback kaydeder (REQ-1.3).

        Args:
            session: Database session
            task_id: Task ID
            retry_count: Yeniden deneme sayısı
            edit_frequency: Düzenleme sıklığı
            rule_id: İlgili CLAUDE.md rule ID

        Returns:
            ExitCodeResult
        """
        # Yüksek retry/edit = düşük başarı
        success = retry_count <= 1 and edit_frequency <= 3
        outcome = "success" if success else "partial"

        record = FeedbackRecordDB(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type="implicit",
            outcome=outcome,
            retry_count=retry_count,
            edit_frequency=edit_frequency,
        )

        session.add(record)

        # Implicit score: düşük retry/edit = yüksek score
        implicit_score = 1.0 - min((retry_count + edit_frequency / 5) / 10, 1.0)

        if rule_id:
            await self._update_effectiveness(
                session, rule_id, success, implicit_score=implicit_score
            )

        await session.commit()

        return ExitCodeResult.success(
            f"Implicit feedback kaydedildi: retry={retry_count}, edits={edit_frequency}"
        )

    async def record_verification_result(
        self,
        session: AsyncSession,
        task_id: str,
        test_passed: bool,
        lint_passed: bool = True,
        type_check_passed: bool = True,
        rule_id: str | None = None,
    ) -> ExitCodeResult:
        """
        Boris Cherny verification sonuçlarını kaydeder.

        Args:
            session: Database session
            task_id: Task ID
            test_passed: Test geçti mi
            lint_passed: Lint geçti mi
            type_check_passed: Type check geçti mi
            rule_id: İlgili CLAUDE.md rule ID

        Returns:
            ExitCodeResult (Exit Code 2 if failed)
        """
        all_passed = test_passed and lint_passed and type_check_passed
        outcome = "success" if all_passed else "failure"

        record = FeedbackRecordDB(
            task_id=task_id,
            rule_id=rule_id,
            feedback_type="automatic",
            outcome=outcome,
            test_passed=test_passed,
            lint_passed=lint_passed,
            type_check_passed=type_check_passed,
        )

        session.add(record)

        if rule_id:
            await self._update_effectiveness(session, rule_id, all_passed)

        await session.commit()

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

    async def calculate_effectiveness(
        self, session: AsyncSession, rule_id: str
    ) -> RuleEffectiveness:
        """
        Belirli bir kuralın effectiveness skorunu hesaplar (REQ-1.4).

        Args:
            session: Database session
            rule_id: Kural ID

        Returns:
            RuleEffectiveness
        """
        cutoff = datetime.now(UTC) - timedelta(days=self.window_days)

        # Get feedback records
        query = select(FeedbackRecordDB).where(
            and_(
                FeedbackRecordDB.rule_id == rule_id,
                FeedbackRecordDB.created_at >= cutoff,
            )
        )
        result = await session.execute(query)
        records = result.scalars().all()

        if not records:
            return RuleEffectiveness(
                rule_id=rule_id,
                rule_text="",
                section="",
                effectiveness_score=0.5,  # Nötr
            )

        # Calculate metrics
        total = len(records)
        success_count = sum(1 for r in records if r.outcome == "success")
        failure_count = sum(1 for r in records if r.outcome == "failure")

        # Explicit score (average of ratings)
        explicit_records = [r for r in records if r.rating is not None]
        if explicit_records:
            explicit_score = sum(r.rating for r in explicit_records) / (
                len(explicit_records) * 5
            )
        else:
            explicit_score = 0.5

        # Implicit score (inverse of retry/edit)
        implicit_records = [
            r for r in records if r.feedback_type == "implicit"
        ]
        if implicit_records:
            avg_retry = sum(r.retry_count for r in implicit_records) / len(
                implicit_records
            )
            avg_edit = sum(r.edit_frequency for r in implicit_records) / len(
                implicit_records
            )
            implicit_score = 1.0 - min((avg_retry + avg_edit / 5) / 10, 1.0)
        else:
            implicit_score = 0.5

        # Weighted average
        weighted_score = (
            explicit_score * self.explicit_weight
            + implicit_score * self.implicit_weight
        )

        # Success rate
        success_rate = success_count / total if total > 0 else 0.5

        # Final effectiveness
        effectiveness_score = (weighted_score + success_rate) / 2

        # Confidence based on sample size
        confidence = min(total / 100, 1.0)

        return RuleEffectiveness(
            rule_id=rule_id,
            rule_text="",
            section="",
            total_feedback=total,
            success_count=success_count,
            failure_count=failure_count,
            effectiveness_score=effectiveness_score,
            confidence=confidence,
            explicit_score=explicit_score,
            implicit_score=implicit_score,
            window_days=self.window_days,
        )

    async def check_improvement_needed(
        self, session: AsyncSession, rule_id: str
    ) -> ImprovementTrigger | None:
        """
        Kuralın iyileştirme gerektirip gerektirmediğini kontrol eder (REQ-1.5).

        Args:
            session: Database session
            rule_id: Kural ID

        Returns:
            ImprovementTrigger if needed, else None
        """
        effectiveness = await self.calculate_effectiveness(session, rule_id)

        if effectiveness.effectiveness_score < self.improvement_threshold:
            trigger = ImprovementTrigger(
                rule_id=rule_id,
                trigger_reason=(
                    f"Effectiveness score ({effectiveness.effectiveness_score:.2f}) "
                    f"eşiğin ({self.improvement_threshold}) altında"
                ),
                current_score=effectiveness.effectiveness_score,
                threshold=self.improvement_threshold,
                suggested_actions=[
                    "Rule formülasyonunu gözden geçir",
                    "Alternatif ifade öner",
                    "A/B test başlat",
                ],
            )

            # Save to database
            trigger_db = ImprovementTriggerDB(
                rule_id=trigger.rule_id,
                trigger_reason=trigger.trigger_reason,
                current_score=trigger.current_score,
                threshold=trigger.threshold,
                improvement_target=trigger.improvement_target,
                suggested_actions=trigger.suggested_actions,
                priority=trigger.priority,
            )
            session.add(trigger_db)

            await self._log_action(
                session,
                action="create_improvement_trigger",
                entity_type="trigger",
                entity_id=rule_id,
                actor="system",
                details={
                    "current_score": effectiveness.effectiveness_score,
                    "threshold": self.improvement_threshold,
                },
            )

            await session.commit()

            return trigger

        return None

    async def get_feedback_summary(
        self, session: AsyncSession
    ) -> dict[str, Any]:
        """
        30-day rolling window feedback özeti getirir (REQ-1.6).

        Args:
            session: Database session

        Returns:
            Feedback özeti
        """
        cutoff = datetime.now(UTC) - timedelta(days=self.window_days)

        # Total count
        total_query = select(func.count(FeedbackRecordDB.id)).where(
            FeedbackRecordDB.created_at >= cutoff
        )
        total_result = await session.execute(total_query)
        total_feedback = total_result.scalar() or 0

        # Outcome distribution
        outcome_query = select(
            FeedbackRecordDB.outcome,
            func.count(FeedbackRecordDB.id),
        ).where(
            FeedbackRecordDB.created_at >= cutoff
        ).group_by(FeedbackRecordDB.outcome)

        outcome_result = await session.execute(outcome_query)
        outcome_distribution = dict(outcome_result.all())

        # Type distribution
        type_query = select(
            FeedbackRecordDB.feedback_type,
            func.count(FeedbackRecordDB.id),
        ).where(
            FeedbackRecordDB.created_at >= cutoff
        ).group_by(FeedbackRecordDB.feedback_type)

        type_result = await session.execute(type_query)
        type_distribution = dict(type_result.all())

        # Rules tracked
        rules_query = select(
            func.count(func.distinct(FeedbackRecordDB.rule_id))
        ).where(
            and_(
                FeedbackRecordDB.created_at >= cutoff,
                FeedbackRecordDB.rule_id.isnot(None),
            )
        )
        rules_result = await session.execute(rules_query)
        rules_tracked = rules_result.scalar() or 0

        # Pending triggers
        triggers_query = select(func.count(ImprovementTriggerDB.id)).where(
            ImprovementTriggerDB.processed == False  # noqa
        )
        triggers_result = await session.execute(triggers_query)
        pending_improvements = triggers_result.scalar() or 0

        return {
            "total_feedback": total_feedback,
            "window_days": self.window_days,
            "outcome_distribution": outcome_distribution,
            "type_distribution": type_distribution,
            "rules_tracked": rules_tracked,
            "pending_improvements": pending_improvements,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def _update_effectiveness(
        self,
        session: AsyncSession,
        rule_id: str,
        success: bool,
        explicit_score: float | None = None,
        implicit_score: float | None = None,
    ) -> None:
        """Rule effectiveness günceller."""
        query = select(RuleEffectivenessDB).where(
            RuleEffectivenessDB.rule_id == rule_id
        )
        result = await session.execute(query)
        effectiveness = result.scalar_one_or_none()

        if effectiveness is None:
            effectiveness = RuleEffectivenessDB(
                rule_id=rule_id,
                rule_text="",
                section="",
            )
            session.add(effectiveness)

        effectiveness.total_feedback += 1

        if success:
            effectiveness.success_count += 1
        else:
            effectiveness.failure_count += 1

        if explicit_score is not None:
            # Moving average
            effectiveness.explicit_score = (
                effectiveness.explicit_score * 0.9 + explicit_score * 0.1
            )

        if implicit_score is not None:
            effectiveness.implicit_score = (
                effectiveness.implicit_score * 0.9 + implicit_score * 0.1
            )

        # Recalculate effectiveness
        if effectiveness.total_feedback > 0:
            weighted = (
                effectiveness.explicit_score * self.explicit_weight
                + effectiveness.implicit_score * self.implicit_weight
            )
            success_rate = (
                effectiveness.success_count / effectiveness.total_feedback
            )
            effectiveness.effectiveness_score = (weighted + success_rate) / 2
            effectiveness.confidence = min(effectiveness.total_feedback / 100, 1.0)

        effectiveness.last_updated = datetime.now(UTC)

    async def _log_action(
        self,
        session: AsyncSession,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        actor: str | None = None,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Audit log oluşturur."""
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            reason=reason,
            details=details or {},
        )
        session.add(log)


# Singleton instance
_feedback_service: FeedbackService | None = None


def get_feedback_service() -> FeedbackService:
    """Singleton FeedbackService instance getir."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
