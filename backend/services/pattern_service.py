"""
Pattern Detection Service - CLAUDE.md Self-Improvement

Bu servis, feedback verilerinden pattern tespiti yapar:
- Error pattern clustering
- Success pattern identification
- Anti-pattern detection
- Statistical significance testing

Spec: claude-md-self-improvement REQ-2
- REQ-2.1: Error pattern clustering
- REQ-2.2: Success pattern identification
- REQ-2.3: Anti-pattern detection
- REQ-2.4: Statistical significance >= 0.95
- REQ-2.5: Visualization (heatmap, graph)
- REQ-2.6: Actionable recommendations

Author: KIRO2 Team
Date: 2026-01-17
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import logging

# Scientific computing
try:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from scipy import stats
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    np = None  # type: ignore
    KMeans = None  # type: ignore

# Database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

# Models
from backend.models.claude_md_improvement_models import (
    FeedbackRecord,
    PatternDetection,
    RuleEffectiveness,
    AuditLog,
)
from backend.hooks.claude_md_improvement.models import PatternInfo

logger = logging.getLogger(__name__)


class PatternDetectionService:
    """
    Pattern detection service for CLAUDE.md feedback analysis.

    Implements REQ-2: Pattern Detection with:
    - K-means clustering for error patterns
    - Statistical significance testing (>= 0.95)
    - Anti-pattern detection
    """

    # Configuration
    MIN_SAMPLES_FOR_CLUSTERING = 10
    CONFIDENCE_THRESHOLD = 0.95
    MAX_CLUSTERS = 5

    def __init__(self, db: AsyncSession):
        """Initialize pattern detection service."""
        self.db = db

        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available. Pattern detection limited.")

    # =========================================================================
    # REQ-2.1: Error Pattern Clustering
    # =========================================================================

    async def detect_error_patterns(
        self,
        window_days: int = 30,
        min_occurrences: int = 3,
    ) -> List[PatternInfo]:
        """
        Detect error patterns using clustering.

        Args:
            window_days: Analysis window in days
            min_occurrences: Minimum occurrences to form a pattern

        Returns:
            List of detected error patterns
        """
        # Get failed feedback records
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        result = await self.db.execute(
            select(FeedbackRecord)
            .where(
                and_(
                    FeedbackRecord.outcome == "failure",
                    FeedbackRecord.created_at >= cutoff,
                )
            )
            .order_by(FeedbackRecord.created_at.desc())
        )
        records = result.scalars().all()

        if len(records) < self.MIN_SAMPLES_FOR_CLUSTERING:
            logger.info(f"Not enough samples for clustering: {len(records)}")
            return []

        # Extract features for clustering
        features = self._extract_features(records)

        if not SKLEARN_AVAILABLE or features is None:
            # Fallback: simple grouping by rule_id
            return await self._simple_error_grouping(records, min_occurrences)

        # K-means clustering
        patterns = self._cluster_patterns(features, records, "error")

        # Filter by minimum occurrences and confidence
        filtered = [
            p for p in patterns
            if p.occurrence_count >= min_occurrences
            and p.confidence >= self.CONFIDENCE_THRESHOLD
        ]

        # Save to database
        for pattern in filtered:
            await self._save_pattern(pattern)

        return filtered

    # =========================================================================
    # REQ-2.2: Success Pattern Identification
    # =========================================================================

    async def detect_success_patterns(
        self,
        window_days: int = 30,
        min_occurrences: int = 5,
    ) -> List[PatternInfo]:
        """
        Identify success patterns (high-performing rule combinations).

        Args:
            window_days: Analysis window in days
            min_occurrences: Minimum occurrences to form a pattern

        Returns:
            List of success patterns
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        # Get successful feedback with high ratings
        result = await self.db.execute(
            select(FeedbackRecord)
            .where(
                and_(
                    FeedbackRecord.outcome == "success",
                    FeedbackRecord.created_at >= cutoff,
                )
            )
        )
        records = result.scalars().all()

        if len(records) < self.MIN_SAMPLES_FOR_CLUSTERING:
            return []

        # Group by rule combinations
        rule_combinations: Dict[str, List[FeedbackRecord]] = defaultdict(list)

        for record in records:
            # Use rule_id or extract from context
            key = record.rule_id or "unknown"
            rule_combinations[key].append(record)

        patterns = []
        for rule_key, rule_records in rule_combinations.items():
            if len(rule_records) >= min_occurrences:
                # Calculate confidence using binomial test
                success_rate = len(rule_records) / max(len(records), 1)
                confidence = self._calculate_confidence(
                    successes=len(rule_records),
                    total=len(records),
                )

                if confidence >= self.CONFIDENCE_THRESHOLD:
                    pattern = PatternInfo(
                        pattern_type="success",
                        description=f"High-performing rule: {rule_key}",
                        occurrence_count=len(rule_records),
                        confidence=confidence,
                        related_rules=[rule_key] if rule_key != "unknown" else [],
                        recommendation=f"Consider using rule {rule_key} pattern more frequently",
                    )
                    patterns.append(pattern)
                    await self._save_pattern(pattern)

        return patterns

    # =========================================================================
    # REQ-2.3: Anti-Pattern Detection
    # =========================================================================

    async def detect_anti_patterns(
        self,
        window_days: int = 30,
    ) -> List[PatternInfo]:
        """
        Detect anti-patterns (problematic rule sequences).

        Anti-patterns include:
        - Rules with consistently high failure rates
        - Rules with high retry counts
        - Rules frequently requiring edits

        Returns:
            List of detected anti-patterns
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        # Get rule effectiveness data
        result = await self.db.execute(
            select(RuleEffectiveness)
            .where(RuleEffectiveness.last_updated >= cutoff)
        )
        rules = result.scalars().all()

        anti_patterns = []

        for rule in rules:
            # Check for anti-pattern indicators
            if rule.total_feedback < 5:
                continue  # Not enough data

            failure_rate = rule.failure_count / rule.total_feedback

            # Anti-pattern: High failure rate (> 50%)
            if failure_rate > 0.5:
                confidence = self._calculate_confidence(
                    successes=rule.failure_count,
                    total=rule.total_feedback,
                )

                if confidence >= self.CONFIDENCE_THRESHOLD:
                    pattern = PatternInfo(
                        pattern_type="anti",
                        description=f"High failure rate for rule: {rule.rule_id}",
                        occurrence_count=rule.failure_count,
                        confidence=confidence,
                        related_rules=[rule.rule_id],
                        recommendation=f"Review and improve rule {rule.rule_id}. "
                                      f"Failure rate: {failure_rate:.1%}",
                    )
                    anti_patterns.append(pattern)
                    await self._save_pattern(pattern)

        # Check for retry-heavy rules (implicit feedback)
        result = await self.db.execute(
            select(
                FeedbackRecord.rule_id,
                func.avg(FeedbackRecord.retry_count).label("avg_retry"),
                func.count().label("count"),
            )
            .where(
                and_(
                    FeedbackRecord.created_at >= cutoff,
                    FeedbackRecord.rule_id.isnot(None),
                )
            )
            .group_by(FeedbackRecord.rule_id)
            .having(func.count() >= 5)
        )
        retry_stats = result.all()

        for stat in retry_stats:
            if stat.avg_retry and stat.avg_retry > 2.0:  # Average > 2 retries
                pattern = PatternInfo(
                    pattern_type="anti",
                    description=f"High retry count for rule: {stat.rule_id}",
                    occurrence_count=stat.count,
                    confidence=0.95,  # Confidence from sample size
                    related_rules=[stat.rule_id] if stat.rule_id else [],
                    recommendation=f"Rule {stat.rule_id} requires average {stat.avg_retry:.1f} retries. "
                                  "Consider simplifying or clarifying.",
                )
                anti_patterns.append(pattern)
                await self._save_pattern(pattern)

        return anti_patterns

    # =========================================================================
    # REQ-2.4: Statistical Significance Testing
    # =========================================================================

    def _calculate_confidence(
        self,
        successes: int,
        total: int,
        expected_rate: float = 0.5,
    ) -> float:
        """
        Calculate statistical confidence using binomial test.

        Args:
            successes: Number of successes
            total: Total trials
            expected_rate: Expected success rate (null hypothesis)

        Returns:
            Confidence level (1 - p-value)
        """
        if total == 0:
            return 0.0

        if SKLEARN_AVAILABLE:
            try:
                # Binomial test
                result = stats.binomtest(
                    successes,
                    total,
                    expected_rate,
                    alternative="two-sided",
                )
                p_value = result.pvalue
                return 1.0 - p_value
            except Exception as e:
                logger.warning(f"Binomial test failed: {e}")

        # Fallback: simple confidence based on sample size
        # Using rule of thumb: n >= 30 for ~95% confidence
        if total >= 30:
            return 0.95
        elif total >= 10:
            return 0.80 + (total - 10) * 0.0075  # 0.80 to 0.95
        else:
            return 0.50 + total * 0.03  # 0.50 to 0.80

    async def test_pattern_significance(
        self,
        pattern: PatternInfo,
        alpha: float = 0.05,
    ) -> Tuple[bool, float]:
        """
        Test if a pattern is statistically significant.

        Args:
            pattern: Pattern to test
            alpha: Significance level (default 0.05 for 95% confidence)

        Returns:
            Tuple of (is_significant, p_value)
        """
        # Already calculated confidence in pattern
        is_significant = pattern.confidence >= (1 - alpha)
        p_value = 1 - pattern.confidence

        return is_significant, p_value

    # =========================================================================
    # REQ-2.5: Visualization Data
    # =========================================================================

    async def generate_heatmap_data(
        self,
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate data for pattern heatmap visualization.

        Returns:
            Dictionary with heatmap data structure
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)

        # Get rule x outcome matrix
        result = await self.db.execute(
            select(
                FeedbackRecord.rule_id,
                FeedbackRecord.outcome,
                func.count().label("count"),
            )
            .where(
                and_(
                    FeedbackRecord.created_at >= cutoff,
                    FeedbackRecord.rule_id.isnot(None),
                )
            )
            .group_by(FeedbackRecord.rule_id, FeedbackRecord.outcome)
        )
        data = result.all()

        # Build heatmap structure
        rules = set()
        outcomes = ["success", "failure", "partial", "timeout"]
        matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        for row in data:
            rules.add(row.rule_id)
            matrix[row.rule_id][row.outcome] = row.count

        return {
            "type": "heatmap",
            "rules": list(rules),
            "outcomes": outcomes,
            "matrix": {
                rule: [matrix[rule][outcome] for outcome in outcomes]
                for rule in rules
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def generate_graph_data(
        self,
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Generate data for pattern relationship graph.

        Returns:
            Dictionary with graph nodes and edges
        """
        # Get active patterns
        result = await self.db.execute(
            select(PatternDetection)
            .where(PatternDetection.active == True)
        )
        patterns = result.scalars().all()

        nodes = []
        edges = []

        for pattern in patterns:
            # Add pattern node
            node_id = str(pattern.id)
            nodes.append({
                "id": node_id,
                "label": pattern.description[:50],
                "type": pattern.pattern_type,
                "confidence": pattern.confidence,
                "size": pattern.occurrence_count,
            })

            # Add edges to related rules
            related = pattern.related_rules or []
            for rule_id in related:
                edges.append({
                    "source": node_id,
                    "target": rule_id,
                    "weight": pattern.confidence,
                })

        return {
            "type": "graph",
            "nodes": nodes,
            "edges": edges,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # =========================================================================
    # REQ-2.6: Actionable Recommendations
    # =========================================================================

    async def get_recommendations(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get actionable recommendations based on detected patterns.

        Returns:
            List of recommendations with priority
        """
        # Get active patterns sorted by confidence and occurrence
        result = await self.db.execute(
            select(PatternDetection)
            .where(PatternDetection.active == True)
            .order_by(
                PatternDetection.confidence.desc(),
                PatternDetection.occurrence_count.desc(),
            )
            .limit(limit)
        )
        patterns = result.scalars().all()

        recommendations = []

        for pattern in patterns:
            priority = self._calculate_priority(pattern)

            recommendations.append({
                "pattern_id": str(pattern.id),
                "pattern_type": pattern.pattern_type,
                "description": pattern.description,
                "recommendation": pattern.recommendation,
                "confidence": pattern.confidence,
                "priority": priority,
                "related_rules": pattern.related_rules,
                "action_required": pattern.pattern_type == "anti",
            })

        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)

        return recommendations

    # =========================================================================
    # Comprehensive Analysis
    # =========================================================================

    async def run_full_analysis(
        self,
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Run comprehensive pattern analysis.

        Returns:
            Complete analysis results
        """
        logger.info(f"Running full pattern analysis (window: {window_days} days)")

        # Detect all pattern types
        error_patterns = await self.detect_error_patterns(window_days)
        success_patterns = await self.detect_success_patterns(window_days)
        anti_patterns = await self.detect_anti_patterns(window_days)

        # Generate visualizations
        heatmap_data = await self.generate_heatmap_data(window_days)
        graph_data = await self.generate_graph_data(window_days)

        # Get recommendations
        recommendations = await self.get_recommendations()

        # Log audit
        await self._log_audit(
            action="full_analysis",
            entity_type="pattern",
            details={
                "window_days": window_days,
                "error_patterns_count": len(error_patterns),
                "success_patterns_count": len(success_patterns),
                "anti_patterns_count": len(anti_patterns),
            },
        )

        return {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "window_days": window_days,
            "patterns": {
                "error": [p.model_dump() for p in error_patterns],
                "success": [p.model_dump() for p in success_patterns],
                "anti": [p.model_dump() for p in anti_patterns],
            },
            "total_patterns": len(error_patterns) + len(success_patterns) + len(anti_patterns),
            "visualizations": {
                "heatmap": heatmap_data,
                "graph": graph_data,
            },
            "recommendations": recommendations,
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_features(
        self,
        records: List[FeedbackRecord],
    ) -> Optional[np.ndarray]:
        """Extract numerical features for clustering."""
        if not SKLEARN_AVAILABLE:
            return None

        features = []
        for record in records:
            features.append([
                record.retry_count or 0,
                record.edit_frequency or 0,
                record.execution_time or 0,
                1 if record.test_passed else 0,
                1 if record.lint_passed else 0,
                1 if record.type_check_passed else 0,
            ])

        return np.array(features)

    def _cluster_patterns(
        self,
        features: np.ndarray,
        records: List[FeedbackRecord],
        pattern_type: str,
    ) -> List[PatternInfo]:
        """Cluster features using K-means."""
        if not SKLEARN_AVAILABLE:
            return []

        # Normalize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Determine optimal number of clusters (max 5)
        n_clusters = min(self.MAX_CLUSTERS, len(records) // 3)
        n_clusters = max(2, n_clusters)  # At least 2 clusters

        # K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(features_scaled)

        # Group records by cluster
        clusters: Dict[int, List[FeedbackRecord]] = defaultdict(list)
        for idx, record in enumerate(records):
            clusters[labels[idx]].append(record)

        # Create patterns from clusters
        patterns = []
        for cluster_id, cluster_records in clusters.items():
            # Get related rules
            related_rules = list(set(
                r.rule_id for r in cluster_records
                if r.rule_id
            ))

            # Calculate cluster confidence
            confidence = self._calculate_confidence(
                successes=len(cluster_records),
                total=len(records),
            )

            pattern = PatternInfo(
                pattern_type=pattern_type,
                description=f"{pattern_type.capitalize()} cluster {cluster_id + 1}: "
                           f"{len(cluster_records)} occurrences",
                occurrence_count=len(cluster_records),
                confidence=confidence,
                related_rules=related_rules,
                recommendation=self._generate_cluster_recommendation(
                    cluster_records, pattern_type
                ),
            )
            patterns.append(pattern)

        return patterns

    async def _simple_error_grouping(
        self,
        records: List[FeedbackRecord],
        min_occurrences: int,
    ) -> List[PatternInfo]:
        """Simple grouping fallback when sklearn is not available."""
        groups: Dict[str, List[FeedbackRecord]] = defaultdict(list)

        for record in records:
            key = record.rule_id or "unknown"
            groups[key].append(record)

        patterns = []
        for key, group_records in groups.items():
            if len(group_records) >= min_occurrences:
                pattern = PatternInfo(
                    pattern_type="error",
                    description=f"Error pattern for rule: {key}",
                    occurrence_count=len(group_records),
                    confidence=self._calculate_confidence(
                        len(group_records), len(records)
                    ),
                    related_rules=[key] if key != "unknown" else [],
                    recommendation=f"Investigate failures in rule {key}",
                )
                patterns.append(pattern)

        return patterns

    def _generate_cluster_recommendation(
        self,
        records: List[FeedbackRecord],
        pattern_type: str,
    ) -> str:
        """Generate recommendation based on cluster characteristics."""
        if not records:
            return "No recommendation available"

        # Analyze cluster characteristics
        avg_retry = sum(r.retry_count or 0 for r in records) / len(records)
        avg_exec_time = sum(r.execution_time or 0 for r in records) / len(records)
        test_fail_rate = sum(1 for r in records if r.test_passed == False) / len(records)

        recommendations = []

        if avg_retry > 2:
            recommendations.append(f"High retry rate ({avg_retry:.1f}). Consider simplifying rules.")

        if avg_exec_time > 10:
            recommendations.append(f"Slow execution ({avg_exec_time:.1f}s). Optimize for performance.")

        if test_fail_rate > 0.5:
            recommendations.append(f"High test failure rate ({test_fail_rate:.1%}). Review test coverage.")

        return " ".join(recommendations) if recommendations else "Monitor this pattern for changes."

    def _calculate_priority(self, pattern: PatternDetection) -> int:
        """Calculate priority score (1-5) for a pattern."""
        # Base priority on pattern type
        if pattern.pattern_type == "anti":
            base = 4
        elif pattern.pattern_type == "error":
            base = 3
        else:
            base = 2

        # Adjust by confidence
        if pattern.confidence >= 0.99:
            base += 1

        # Adjust by occurrence count
        if pattern.occurrence_count >= 20:
            base += 1

        return min(5, max(1, base))

    async def _save_pattern(self, pattern: PatternInfo) -> None:
        """Save pattern to database."""
        try:
            # Check for existing similar pattern
            result = await self.db.execute(
                select(PatternDetection)
                .where(
                    and_(
                        PatternDetection.pattern_type == pattern.pattern_type,
                        PatternDetection.description == pattern.description,
                        PatternDetection.active == True,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing pattern
                existing.occurrence_count = pattern.occurrence_count
                existing.confidence = pattern.confidence
                existing.last_seen = datetime.now(timezone.utc)
                existing.related_rules = pattern.related_rules
                existing.recommendation = pattern.recommendation
            else:
                # Create new pattern
                db_pattern = PatternDetection(
                    pattern_type=pattern.pattern_type,
                    description=pattern.description,
                    occurrence_count=pattern.occurrence_count,
                    confidence=pattern.confidence,
                    related_rules=pattern.related_rules,
                    recommendation=pattern.recommendation,
                )
                self.db.add(db_pattern)

            await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to save pattern: {e}")
            await self.db.rollback()

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
                actor="pattern_service",
                details=details or {},
            )
            self.db.add(audit)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")


# Factory function
async def get_pattern_service(db: AsyncSession) -> PatternDetectionService:
    """Get pattern detection service instance."""
    return PatternDetectionService(db)
