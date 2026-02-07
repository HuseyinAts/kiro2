"""
A/B Testing Framework Service - CLAUDE.md Self-Improvement

Bu servis, kural değişikliklerini A/B testi ile doğrular:
- Traffic splitting (%50-%50)
- Statistical significance testing (p < 0.05)
- Multi-metric evaluation
- Winner selection
- Automatic production deployment

Spec: claude-md-self-improvement REQ-4
- REQ-4.1: Traffic %50-%50 split
- REQ-4.2: Minimum 1000 sample
- REQ-4.3: p-value < 0.05
- REQ-4.4: Multi-metric evaluation
- REQ-4.5: Winning variant production'a alınır
- REQ-4.6: Confidence interval ve effect size

Author: KIRO2 Team
Date: 2026-01-17
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging
import hashlib
from uuid import uuid4

# Statistical computing
try:
    import numpy as np
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    np = None  # type: ignore
    stats = None  # type: ignore

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Models
from backend.models.claude_md_improvement_models import (
    RuleEffectiveness,
    AuditLog,
)

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """A/B test status."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Variant(str, Enum):
    """Test variant."""
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class ABTestResult:
    """Result of an A/B test."""
    test_id: str
    status: TestStatus
    winner: Optional[Variant]
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    control_metrics: Dict[str, float]
    treatment_metrics: Dict[str, float]
    sample_sizes: Dict[str, int]
    is_significant: bool
    recommendation: str


@dataclass
class ABTest:
    """A/B test configuration."""
    id: str
    rule_id: str
    control_text: str
    treatment_text: str
    status: TestStatus = TestStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    min_samples: int = 1000
    max_duration_days: int = 14
    traffic_split: float = 0.5  # Treatment gets this fraction
    metrics: List[str] = field(default_factory=lambda: ["success_rate", "avg_rating"])
    control_samples: int = 0
    treatment_samples: int = 0
    control_successes: int = 0
    treatment_successes: int = 0
    control_ratings: List[float] = field(default_factory=list)
    treatment_ratings: List[float] = field(default_factory=list)


class ABTestingService:
    """
    A/B Testing service for CLAUDE.md rule changes.

    Implements REQ-4: A/B Testing Framework with:
    - 50/50 traffic split
    - Minimum 1000 samples
    - p-value < 0.05 for significance
    - Multi-metric evaluation
    """

    # Configuration
    MIN_SAMPLES = 1000
    SIGNIFICANCE_LEVEL = 0.05
    MIN_EFFECT_SIZE = 0.05  # 5% minimum improvement

    def __init__(self, db: AsyncSession):
        """Initialize A/B testing service."""
        self.db = db
        self._active_tests: Dict[str, ABTest] = {}

        if not SCIPY_AVAILABLE:
            logger.warning("scipy not available. Statistical tests limited.")

    # =========================================================================
    # REQ-4.1: Traffic Split (50/50)
    # =========================================================================

    async def create_test(
        self,
        rule_id: str,
        control_text: str,
        treatment_text: str,
        min_samples: int = 1000,
        traffic_split: float = 0.5,
        metrics: Optional[List[str]] = None,
    ) -> ABTest:
        """
        Create a new A/B test.

        Args:
            rule_id: Rule being tested
            control_text: Current rule text (control)
            treatment_text: New rule text (treatment)
            min_samples: Minimum samples per variant (default: 1000)
            traffic_split: Fraction of traffic to treatment (default: 0.5)
            metrics: Metrics to evaluate

        Returns:
            Created ABTest
        """
        test = ABTest(
            id=str(uuid4()),
            rule_id=rule_id,
            control_text=control_text,
            treatment_text=treatment_text,
            min_samples=min_samples,
            traffic_split=traffic_split,
            metrics=metrics or ["success_rate", "avg_rating"],
        )

        self._active_tests[test.id] = test

        # Log audit
        await self._log_audit(
            action="create_test",
            entity_type="ab_test",
            entity_id=test.id,
            details={
                "rule_id": rule_id,
                "min_samples": min_samples,
                "traffic_split": traffic_split,
            },
        )

        logger.info(f"Created A/B test {test.id} for rule {rule_id}")
        return test

    async def start_test(self, test_id: str) -> ABTest:
        """
        Start an A/B test.

        Args:
            test_id: Test identifier

        Returns:
            Updated test
        """
        test = self._active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test not found: {test_id}")

        if test.status != TestStatus.DRAFT:
            raise ValueError(f"Test already started: {test.status}")

        test.status = TestStatus.RUNNING
        test.started_at = datetime.now(timezone.utc)

        await self._log_audit(
            action="start_test",
            entity_type="ab_test",
            entity_id=test_id,
        )

        return test

    def assign_variant(
        self,
        test_id: str,
        session_id: str,
    ) -> Variant:
        """
        Assign a variant to a session.

        Uses deterministic assignment based on session_id hash
        to ensure consistent variant for same session.

        Args:
            test_id: Test identifier
            session_id: Session identifier

        Returns:
            Assigned variant
        """
        test = self._active_tests.get(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return Variant.CONTROL  # Default to control

        # Deterministic assignment using hash
        hash_input = f"{test_id}:{session_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized = (hash_value % 1000) / 1000.0

        if normalized < test.traffic_split:
            return Variant.TREATMENT
        return Variant.CONTROL

    def get_rule_text(
        self,
        test_id: str,
        variant: Variant,
    ) -> str:
        """Get rule text for a variant."""
        test = self._active_tests.get(test_id)
        if not test:
            return ""

        if variant == Variant.TREATMENT:
            return test.treatment_text
        return test.control_text

    # =========================================================================
    # REQ-4.2: Minimum Sample Requirement
    # =========================================================================

    async def record_observation(
        self,
        test_id: str,
        variant: Variant,
        success: bool,
        rating: Optional[float] = None,
    ) -> None:
        """
        Record an observation for a test.

        Args:
            test_id: Test identifier
            variant: Which variant was used
            success: Whether task succeeded
            rating: Optional user rating (1-5)
        """
        test = self._active_tests.get(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return

        if variant == Variant.CONTROL:
            test.control_samples += 1
            if success:
                test.control_successes += 1
            if rating is not None:
                test.control_ratings.append(rating)
        else:
            test.treatment_samples += 1
            if success:
                test.treatment_successes += 1
            if rating is not None:
                test.treatment_ratings.append(rating)

        # Check if test is complete
        await self._check_test_completion(test)

    async def _check_test_completion(self, test: ABTest) -> None:
        """Check if test has reached minimum samples."""
        if test.control_samples >= test.min_samples and \
           test.treatment_samples >= test.min_samples:
            # Analyze and complete
            await self.analyze_test(test.id)

    # =========================================================================
    # REQ-4.3: Statistical Significance (p < 0.05)
    # =========================================================================

    async def analyze_test(
        self,
        test_id: str,
        force: bool = False,
    ) -> ABTestResult:
        """
        Analyze A/B test results.

        Args:
            test_id: Test identifier
            force: Force analysis even if min samples not reached

        Returns:
            Test result with statistical analysis
        """
        test = self._active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test not found: {test_id}")

        # Check minimum samples
        if not force and (test.control_samples < test.min_samples or
                         test.treatment_samples < test.min_samples):
            return ABTestResult(
                test_id=test_id,
                status=test.status,
                winner=None,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0),
                control_metrics=self._calculate_metrics(test, Variant.CONTROL),
                treatment_metrics=self._calculate_metrics(test, Variant.TREATMENT),
                sample_sizes={
                    "control": test.control_samples,
                    "treatment": test.treatment_samples,
                },
                is_significant=False,
                recommendation=f"Need more samples: control={test.control_samples}/{test.min_samples}, "
                              f"treatment={test.treatment_samples}/{test.min_samples}",
            )

        # Calculate success rates
        control_rate = test.control_successes / max(test.control_samples, 1)
        treatment_rate = test.treatment_successes / max(test.treatment_samples, 1)

        # Statistical test
        p_value, is_significant = self._chi_square_test(
            test.control_successes, test.control_samples,
            test.treatment_successes, test.treatment_samples,
        )

        # Effect size (Cohen's h for proportions)
        effect_size = self._calculate_effect_size(control_rate, treatment_rate)

        # Confidence interval for difference
        ci_low, ci_high = self._calculate_confidence_interval(
            control_rate, test.control_samples,
            treatment_rate, test.treatment_samples,
        )

        # Determine winner
        winner = None
        recommendation = ""

        if is_significant and effect_size >= self.MIN_EFFECT_SIZE:
            if treatment_rate > control_rate:
                winner = Variant.TREATMENT
                recommendation = (
                    f"Treatment wins! Success rate improved by "
                    f"{(treatment_rate - control_rate) * 100:.1f}% "
                    f"(p={p_value:.4f}, effect size={effect_size:.3f})"
                )
            else:
                winner = Variant.CONTROL
                recommendation = (
                    f"Control performs better. Keep current rule. "
                    f"(p={p_value:.4f})"
                )
        else:
            recommendation = (
                f"No significant difference detected "
                f"(p={p_value:.4f}, effect size={effect_size:.3f}). "
                f"Consider running test longer or accepting current rule."
            )

        # Update test status
        test.status = TestStatus.COMPLETED
        test.completed_at = datetime.now(timezone.utc)

        # Log audit
        await self._log_audit(
            action="analyze_test",
            entity_type="ab_test",
            entity_id=test_id,
            details={
                "p_value": p_value,
                "effect_size": effect_size,
                "winner": winner.value if winner else None,
                "is_significant": is_significant,
            },
        )

        return ABTestResult(
            test_id=test_id,
            status=test.status,
            winner=winner,
            p_value=p_value,
            effect_size=effect_size,
            confidence_interval=(ci_low, ci_high),
            control_metrics=self._calculate_metrics(test, Variant.CONTROL),
            treatment_metrics=self._calculate_metrics(test, Variant.TREATMENT),
            sample_sizes={
                "control": test.control_samples,
                "treatment": test.treatment_samples,
            },
            is_significant=is_significant,
            recommendation=recommendation,
        )

    def _chi_square_test(
        self,
        control_successes: int,
        control_total: int,
        treatment_successes: int,
        treatment_total: int,
    ) -> Tuple[float, bool]:
        """
        Perform chi-square test for independence.

        Returns:
            Tuple of (p_value, is_significant)
        """
        if SCIPY_AVAILABLE:
            # Create contingency table
            # [[control_success, control_fail], [treatment_success, treatment_fail]]
            table = [
                [control_successes, control_total - control_successes],
                [treatment_successes, treatment_total - treatment_successes],
            ]

            try:
                chi2, p_value, dof, expected = stats.chi2_contingency(table)
                return p_value, p_value < self.SIGNIFICANCE_LEVEL
            except Exception as e:
                logger.warning(f"Chi-square test failed: {e}")

        # Fallback: simple proportion test
        control_rate = control_successes / max(control_total, 1)
        treatment_rate = treatment_successes / max(treatment_total, 1)

        # Use normal approximation
        pooled_rate = (control_successes + treatment_successes) / \
                      max(control_total + treatment_total, 1)

        if pooled_rate == 0 or pooled_rate == 1:
            return 1.0, False

        se = (pooled_rate * (1 - pooled_rate) *
              (1 / control_total + 1 / treatment_total)) ** 0.5

        if se == 0:
            return 1.0, False

        z = abs(treatment_rate - control_rate) / se
        p_value = 2 * (1 - self._normal_cdf(z))

        return p_value, p_value < self.SIGNIFICANCE_LEVEL

    def _normal_cdf(self, x: float) -> float:
        """Standard normal CDF approximation."""
        # Approximation using error function
        import math
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    # =========================================================================
    # REQ-4.4: Multi-Metric Evaluation
    # =========================================================================

    def _calculate_metrics(
        self,
        test: ABTest,
        variant: Variant,
    ) -> Dict[str, float]:
        """Calculate all metrics for a variant."""
        if variant == Variant.CONTROL:
            samples = test.control_samples
            successes = test.control_successes
            ratings = test.control_ratings
        else:
            samples = test.treatment_samples
            successes = test.treatment_successes
            ratings = test.treatment_ratings

        metrics = {}

        # Success rate
        metrics["success_rate"] = successes / max(samples, 1)

        # Average rating
        if ratings:
            metrics["avg_rating"] = sum(ratings) / len(ratings)
            metrics["rating_count"] = len(ratings)
        else:
            metrics["avg_rating"] = 0.0
            metrics["rating_count"] = 0

        # Sample size
        metrics["sample_size"] = samples

        return metrics

    async def get_multi_metric_comparison(
        self,
        test_id: str,
    ) -> Dict[str, Any]:
        """
        Get detailed multi-metric comparison.

        Returns:
            Comparison across all metrics
        """
        test = self._active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test not found: {test_id}")

        control_metrics = self._calculate_metrics(test, Variant.CONTROL)
        treatment_metrics = self._calculate_metrics(test, Variant.TREATMENT)

        comparison = {}
        for metric in test.metrics:
            control_val = control_metrics.get(metric, 0)
            treatment_val = treatment_metrics.get(metric, 0)

            comparison[metric] = {
                "control": control_val,
                "treatment": treatment_val,
                "difference": treatment_val - control_val,
                "relative_change": (treatment_val - control_val) / max(control_val, 0.001),
                "treatment_wins": treatment_val > control_val,
            }

        return {
            "test_id": test_id,
            "metrics": comparison,
            "overall_winner": self._determine_overall_winner(comparison),
        }

    def _determine_overall_winner(
        self,
        comparison: Dict[str, Any],
    ) -> Optional[str]:
        """Determine overall winner based on all metrics."""
        treatment_wins = sum(
            1 for m in comparison.values()
            if m.get("treatment_wins", False)
        )
        total_metrics = len(comparison)

        if treatment_wins > total_metrics / 2:
            return "treatment"
        elif treatment_wins < total_metrics / 2:
            return "control"
        return None  # Tie

    # =========================================================================
    # REQ-4.5: Winner to Production
    # =========================================================================

    async def deploy_winner(
        self,
        test_id: str,
    ) -> Dict[str, Any]:
        """
        Deploy winning variant to production.

        Args:
            test_id: Test identifier

        Returns:
            Deployment result
        """
        test = self._active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test not found: {test_id}")

        # Analyze if not already done
        result = await self.analyze_test(test_id)

        if not result.winner:
            return {
                "success": False,
                "error": "No clear winner to deploy",
                "recommendation": result.recommendation,
            }

        # Get winning text
        winning_text = (
            test.treatment_text
            if result.winner == Variant.TREATMENT
            else test.control_text
        )

        # Deploy to rule effectiveness (update rule text)
        await self._update_rule_effectiveness(
            rule_id=test.rule_id,
            rule_text=winning_text,
            effectiveness_score=result.treatment_metrics["success_rate"]
            if result.winner == Variant.TREATMENT
            else result.control_metrics["success_rate"],
        )

        # Log audit
        await self._log_audit(
            action="deploy_winner",
            entity_type="ab_test",
            entity_id=test_id,
            details={
                "winner": result.winner.value,
                "rule_id": test.rule_id,
            },
        )

        return {
            "success": True,
            "winner": result.winner.value,
            "rule_id": test.rule_id,
            "deployed_text": winning_text[:200] + "..." if len(winning_text) > 200 else winning_text,
            "improvement": result.effect_size,
        }

    async def _update_rule_effectiveness(
        self,
        rule_id: str,
        rule_text: str,
        effectiveness_score: float,
    ) -> None:
        """Update rule effectiveness with winner."""
        result = await self.db.execute(
            select(RuleEffectiveness)
            .where(RuleEffectiveness.rule_id == rule_id)
        )
        rule = result.scalar_one_or_none()

        if rule:
            rule.rule_text = rule_text
            rule.effectiveness_score = effectiveness_score
            rule.last_updated = datetime.now(timezone.utc)
        else:
            rule = RuleEffectiveness(
                rule_id=rule_id,
                rule_text=rule_text,
                effectiveness_score=effectiveness_score,
            )
            self.db.add(rule)

        await self.db.commit()

    # =========================================================================
    # REQ-4.6: Confidence Interval and Effect Size
    # =========================================================================

    def _calculate_effect_size(
        self,
        control_rate: float,
        treatment_rate: float,
    ) -> float:
        """
        Calculate Cohen's h effect size for proportions.

        Cohen's h = 2 * (arcsin(sqrt(p2)) - arcsin(sqrt(p1)))
        """
        import math

        # Handle edge cases
        control_rate = max(0.001, min(0.999, control_rate))
        treatment_rate = max(0.001, min(0.999, treatment_rate))

        phi1 = 2 * math.asin(math.sqrt(control_rate))
        phi2 = 2 * math.asin(math.sqrt(treatment_rate))

        return abs(phi2 - phi1)

    def _calculate_confidence_interval(
        self,
        control_rate: float,
        control_n: int,
        treatment_rate: float,
        treatment_n: int,
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for difference in proportions.

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Point estimate
        diff = treatment_rate - control_rate

        # Standard error
        se = ((control_rate * (1 - control_rate) / max(control_n, 1)) +
              (treatment_rate * (1 - treatment_rate) / max(treatment_n, 1))) ** 0.5

        # Z-score for confidence level
        z = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%

        margin = z * se

        return (diff - margin, diff + margin)

    # =========================================================================
    # Test Management
    # =========================================================================

    async def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get test by ID."""
        return self._active_tests.get(test_id)

    async def list_tests(
        self,
        status: Optional[TestStatus] = None,
    ) -> List[ABTest]:
        """List all tests, optionally filtered by status."""
        tests = list(self._active_tests.values())

        if status:
            tests = [t for t in tests if t.status == status]

        return tests

    async def pause_test(self, test_id: str) -> ABTest:
        """Pause a running test."""
        test = self._active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test not found: {test_id}")

        if test.status != TestStatus.RUNNING:
            raise ValueError(f"Test not running: {test.status}")

        test.status = TestStatus.PAUSED

        await self._log_audit(
            action="pause_test",
            entity_type="ab_test",
            entity_id=test_id,
        )

        return test

    async def cancel_test(self, test_id: str) -> ABTest:
        """Cancel a test."""
        test = self._active_tests.get(test_id)
        if not test:
            raise ValueError(f"Test not found: {test_id}")

        test.status = TestStatus.CANCELLED
        test.completed_at = datetime.now(timezone.utc)

        await self._log_audit(
            action="cancel_test",
            entity_type="ab_test",
            entity_id=test_id,
        )

        return test

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log audit entry."""
        try:
            audit = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor="ab_testing_service",
                details=details or {},
            )
            self.db.add(audit)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")


# Factory function
async def get_ab_testing_service(db: AsyncSession) -> ABTestingService:
    """Get A/B testing service instance."""
    return ABTestingService(db)
