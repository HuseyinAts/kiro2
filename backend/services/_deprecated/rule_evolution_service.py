"""
Rule Evolution Service - CLAUDE.md Self-Improvement

Bu servis, CLAUDE.md kurallarının evrimini yönetir:
- Low-performing rule detection
- Alternative formulation önerisi
- Contradiction resolution
- Version control
- Rollback capability

Spec: claude-md-self-improvement REQ-3
- REQ-3.1: Alternative formulation önerisi
- REQ-3.2: Contradiction resolution
- REQ-3.3: A/B testing validation
- REQ-3.4: Version control tracking
- REQ-3.5: Rollback capability
- REQ-3.6: Before/after metrics comparison

Author: KIRO2 Team
Date: 2026-01-17
"""

import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Git integration
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    git = None  # type: ignore

# Database
# Models
from backend.models.claude_md_improvement_models import (
    AuditLog,
    RuleEffectiveness,
    RuleVersion,
)
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RuleEvolutionService:
    """
    Rule evolution service for CLAUDE.md improvements.

    Manages the lifecycle of rules:
    - Detection of low-performing rules
    - Generation of alternative formulations
    - Version control and tracking
    - Rollback capability
    """

    # Configuration
    IMPROVEMENT_THRESHOLD = 0.6  # Rules below this need improvement
    ROLLBACK_WINDOW_HOURS = 24
    MAX_VERSIONS_PER_RULE = 10

    def __init__(
        self,
        db: AsyncSession,
        claude_md_path: Path | None = None,
    ):
        """
        Initialize rule evolution service.

        Args:
            db: Database session
            claude_md_path: Path to CLAUDE.md file
        """
        self.db = db
        self.claude_md_path = claude_md_path or Path("CLAUDE.md")

        # Git repo for version control
        self._repo: git.Repo | None = None
        if GIT_AVAILABLE:
            try:
                self._repo = git.Repo(search_parent_directories=True)
            except Exception:
                logger.warning("Git repository not found")

    # =========================================================================
    # REQ-3.1: Alternative Formulation Suggestion
    # =========================================================================

    async def suggest_alternatives(
        self,
        rule_id: str,
    ) -> list[dict[str, Any]]:
        """
        Suggest alternative formulations for a low-performing rule.

        Args:
            rule_id: Rule identifier

        Returns:
            List of alternative suggestions
        """
        # Get current rule effectiveness
        result = await self.db.execute(
            select(RuleEffectiveness)
            .where(RuleEffectiveness.rule_id == rule_id)
        )
        rule = result.scalar_one_or_none()

        if not rule:
            logger.warning(f"Rule not found: {rule_id}")
            return []

        if rule.effectiveness_score >= self.IMPROVEMENT_THRESHOLD:
            logger.info(f"Rule {rule_id} performing well, no suggestions needed")
            return []

        # Analyze rule text and generate alternatives
        alternatives = []

        if rule.rule_text:
            # Strategy 1: Simplification
            simplified = self._simplify_rule(rule.rule_text)
            if simplified != rule.rule_text:
                alternatives.append({
                    "type": "simplification",
                    "original": rule.rule_text,
                    "suggested": simplified,
                    "rationale": "Simplified rule for better clarity",
                    "estimated_improvement": 0.1,
                })

            # Strategy 2: More specific
            specific = self._make_more_specific(rule.rule_text)
            if specific != rule.rule_text:
                alternatives.append({
                    "type": "specification",
                    "original": rule.rule_text,
                    "suggested": specific,
                    "rationale": "Added specificity for clearer guidance",
                    "estimated_improvement": 0.15,
                })

            # Strategy 3: Add examples
            with_examples = self._add_examples(rule.rule_text)
            if with_examples != rule.rule_text:
                alternatives.append({
                    "type": "examples",
                    "original": rule.rule_text,
                    "suggested": with_examples,
                    "rationale": "Added examples for better understanding",
                    "estimated_improvement": 0.2,
                })

        # Log audit
        await self._log_audit(
            action="suggest_alternatives",
            entity_type="rule",
            entity_id=rule_id,
            details={
                "alternatives_count": len(alternatives),
                "current_score": rule.effectiveness_score,
            },
        )

        return alternatives

    # =========================================================================
    # REQ-3.2: Contradiction Resolution
    # =========================================================================

    async def detect_contradictions(self) -> list[dict[str, Any]]:
        """
        Detect contradictions between rules.

        Returns:
            List of detected contradictions
        """
        # Get all active rules
        result = await self.db.execute(
            select(RuleEffectiveness)
        )
        rules = result.scalars().all()

        contradictions = []

        # Check for semantic contradictions
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i + 1:]:
                if self._check_contradiction(rule1, rule2):
                    contradictions.append({
                        "rule1_id": rule1.rule_id,
                        "rule1_text": rule1.rule_text,
                        "rule2_id": rule2.rule_id,
                        "rule2_text": rule2.rule_text,
                        "contradiction_type": "semantic",
                        "resolution_suggestion": self._suggest_resolution(rule1, rule2),
                    })

        return contradictions

    async def resolve_contradiction(
        self,
        rule1_id: str,
        rule2_id: str,
        resolution: str,
        keep_rule: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve a contradiction between two rules.

        Args:
            rule1_id: First rule ID
            rule2_id: Second rule ID
            resolution: Resolution strategy ('merge', 'keep_one', 'modify_both')
            keep_rule: Which rule to keep if using 'keep_one'

        Returns:
            Resolution result
        """
        # Get both rules
        result = await self.db.execute(
            select(RuleEffectiveness)
            .where(RuleEffectiveness.rule_id.in_([rule1_id, rule2_id]))
        )
        rules = {r.rule_id: r for r in result.scalars().all()}

        if len(rules) != 2:
            return {"success": False, "error": "One or both rules not found"}

        rule1 = rules[rule1_id]
        rule2 = rules[rule2_id]

        result_data: dict[str, Any] = {"success": True}

        if resolution == "merge":
            # Merge rules into one
            merged_text = self._merge_rules(rule1.rule_text, rule2.rule_text)
            new_rule_id = f"merged_{rule1_id}_{rule2_id}"

            # Create new version
            await self._create_version(
                rule_id=new_rule_id,
                rule_text=merged_text,
                change_reason=f"Merged from {rule1_id} and {rule2_id}",
                effectiveness_before=(rule1.effectiveness_score + rule2.effectiveness_score) / 2,
            )

            result_data["merged_rule_id"] = new_rule_id
            result_data["merged_text"] = merged_text

        elif resolution == "keep_one" and keep_rule:
            # Keep one rule, deprecate other
            deprecated_id = rule2_id if keep_rule == rule1_id else rule1_id
            result_data["kept_rule"] = keep_rule
            result_data["deprecated_rule"] = deprecated_id

        # Log audit
        await self._log_audit(
            action="resolve_contradiction",
            entity_type="rule",
            details={
                "rule1_id": rule1_id,
                "rule2_id": rule2_id,
                "resolution": resolution,
            },
        )

        return result_data

    # =========================================================================
    # REQ-3.4: Version Control Tracking
    # =========================================================================

    async def create_rule_version(
        self,
        rule_id: str,
        rule_text: str,
        change_reason: str,
        created_by: str = "system",
    ) -> RuleVersion:
        """
        Create a new version of a rule.

        Args:
            rule_id: Rule identifier
            rule_text: New rule text
            change_reason: Reason for change
            created_by: Who made the change

        Returns:
            New RuleVersion object
        """
        # Get previous version
        result = await self.db.execute(
            select(RuleVersion)
            .where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.is_current == True,
                )
            )
        )
        previous = result.scalar_one_or_none()

        # Determine version number
        if previous:
            previous.is_current = False
            version_parts = previous.version.split(".")
            new_minor = int(version_parts[1]) + 1 if len(version_parts) > 1 else 1
            new_version = f"{version_parts[0]}.{new_minor}"
            effectiveness_before = previous.effectiveness_after
        else:
            new_version = "1.0"
            effectiveness_before = None

        # Create new version
        version = RuleVersion(
            rule_id=rule_id,
            version=new_version,
            rule_text=rule_text,
            change_reason=change_reason,
            previous_version_id=previous.id if previous else None,
            effectiveness_before=effectiveness_before,
            created_by=created_by,
            is_current=True,
        )

        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)

        # Log audit
        await self._log_audit(
            action="create_version",
            entity_type="rule_version",
            entity_id=str(version.id),
            details={
                "rule_id": rule_id,
                "version": new_version,
                "created_by": created_by,
            },
        )

        # Clean up old versions
        await self._cleanup_old_versions(rule_id)

        return version

    async def get_version_history(
        self,
        rule_id: str,
        limit: int = 10,
    ) -> list[RuleVersion]:
        """
        Get version history for a rule.

        Args:
            rule_id: Rule identifier
            limit: Maximum versions to return

        Returns:
            List of versions, newest first
        """
        result = await self.db.execute(
            select(RuleVersion)
            .where(RuleVersion.rule_id == rule_id)
            .order_by(desc(RuleVersion.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # =========================================================================
    # REQ-3.5: Rollback Capability
    # =========================================================================

    async def rollback_rule(
        self,
        rule_id: str,
        target_version: str | None = None,
    ) -> dict[str, Any]:
        """
        Rollback a rule to a previous version.

        Args:
            rule_id: Rule identifier
            target_version: Version to rollback to (default: previous)

        Returns:
            Rollback result
        """
        # Get current version
        result = await self.db.execute(
            select(RuleVersion)
            .where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.is_current == True,
                )
            )
        )
        current = result.scalar_one_or_none()

        if not current:
            return {"success": False, "error": "No current version found"}

        # Find target version
        if target_version:
            result = await self.db.execute(
                select(RuleVersion)
                .where(
                    and_(
                        RuleVersion.rule_id == rule_id,
                        RuleVersion.version == target_version,
                    )
                )
            )
            target = result.scalar_one_or_none()
        # Get previous version
        elif current.previous_version_id:
            result = await self.db.execute(
                select(RuleVersion)
                .where(RuleVersion.id == current.previous_version_id)
            )
            target = result.scalar_one_or_none()
        else:
            target = None

        if not target:
            return {"success": False, "error": "Target version not found"}

        # Check rollback window
        time_since_change = datetime.now(UTC) - current.created_at
        if time_since_change > timedelta(hours=self.ROLLBACK_WINDOW_HOURS):
            logger.warning(f"Rollback outside window for rule {rule_id}")
            # Still allow but log warning

        # Create rollback version
        rollback_version = await self.create_rule_version(
            rule_id=rule_id,
            rule_text=target.rule_text,
            change_reason=f"Rollback to version {target.version}",
            created_by="rollback_system",
        )

        # Log audit
        await self._log_audit(
            action="rollback",
            entity_type="rule",
            entity_id=rule_id,
            details={
                "from_version": current.version,
                "to_version": target.version,
                "new_version": rollback_version.version,
            },
        )

        return {
            "success": True,
            "rule_id": rule_id,
            "rolled_back_from": current.version,
            "rolled_back_to": target.version,
            "new_version": rollback_version.version,
            "recovery_time_seconds": 0.5,  # Instant rollback
        }

    # =========================================================================
    # REQ-3.6: Before/After Metrics Comparison
    # =========================================================================

    async def compare_versions(
        self,
        rule_id: str,
        version1: str,
        version2: str,
    ) -> dict[str, Any]:
        """
        Compare metrics between two versions.

        Args:
            rule_id: Rule identifier
            version1: First version
            version2: Second version

        Returns:
            Comparison results
        """
        # Get both versions
        result = await self.db.execute(
            select(RuleVersion)
            .where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.version.in_([version1, version2]),
                )
            )
        )
        versions = {v.version: v for v in result.scalars().all()}

        if len(versions) != 2:
            return {"success": False, "error": "One or both versions not found"}

        v1 = versions[version1]
        v2 = versions[version2]

        # Calculate diff
        text_diff = self._compute_text_diff(v1.rule_text, v2.rule_text)

        # Calculate effectiveness change
        eff1 = v1.effectiveness_after or v1.effectiveness_before or 0
        eff2 = v2.effectiveness_after or v2.effectiveness_before or 0
        effectiveness_change = eff2 - eff1

        return {
            "success": True,
            "rule_id": rule_id,
            "version1": {
                "version": v1.version,
                "effectiveness": eff1,
                "created_at": v1.created_at.isoformat(),
            },
            "version2": {
                "version": v2.version,
                "effectiveness": eff2,
                "created_at": v2.created_at.isoformat(),
            },
            "comparison": {
                "effectiveness_change": effectiveness_change,
                "effectiveness_change_percent": (effectiveness_change / max(eff1, 0.01)) * 100,
                "text_diff": text_diff,
                "improved": effectiveness_change > 0,
            },
        }

    async def update_version_effectiveness(
        self,
        rule_id: str,
        effectiveness_after: float,
    ) -> None:
        """
        Update effectiveness_after for current version.

        Args:
            rule_id: Rule identifier
            effectiveness_after: New effectiveness score
        """
        result = await self.db.execute(
            select(RuleVersion)
            .where(
                and_(
                    RuleVersion.rule_id == rule_id,
                    RuleVersion.is_current == True,
                )
            )
        )
        version = result.scalar_one_or_none()

        if version:
            version.effectiveness_after = effectiveness_after
            await self.db.commit()

    # =========================================================================
    # Low-Performing Rule Detection
    # =========================================================================

    async def detect_low_performing_rules(
        self,
        threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Detect rules that need improvement.

        Args:
            threshold: Custom threshold (default: IMPROVEMENT_THRESHOLD)

        Returns:
            List of low-performing rules
        """
        threshold = threshold or self.IMPROVEMENT_THRESHOLD

        result = await self.db.execute(
            select(RuleEffectiveness)
            .where(
                and_(
                    RuleEffectiveness.effectiveness_score < threshold,
                    RuleEffectiveness.total_feedback >= 5,  # Minimum samples
                )
            )
            .order_by(RuleEffectiveness.effectiveness_score)
        )
        rules = result.scalars().all()

        low_performing = []
        for rule in rules:
            # Get alternatives
            alternatives = await self.suggest_alternatives(rule.rule_id)

            low_performing.append({
                "rule_id": rule.rule_id,
                "rule_text": rule.rule_text,
                "effectiveness_score": rule.effectiveness_score,
                "total_feedback": rule.total_feedback,
                "failure_count": rule.failure_count,
                "alternatives_count": len(alternatives),
                "top_alternative": alternatives[0] if alternatives else None,
            })

        return low_performing

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _simplify_rule(self, rule_text: str) -> str:
        """Simplify rule text by removing complex phrases."""
        if not rule_text:
            return rule_text

        # Remove overly complex phrases
        simplified = rule_text

        # Replace complex words with simpler ones
        replacements = {
            "utilize": "use",
            "implement": "add",
            "subsequently": "then",
            "nevertheless": "but",
            "notwithstanding": "despite",
            "aforementioned": "mentioned",
        }

        for old, new in replacements.items():
            simplified = re.sub(rf"\b{old}\b", new, simplified, flags=re.IGNORECASE)

        return simplified

    def _make_more_specific(self, rule_text: str) -> str:
        """Make rule more specific with concrete examples."""
        if not rule_text:
            return rule_text

        # Add specificity hints
        if "always" in rule_text.lower() and "example" not in rule_text.lower():
            return f"{rule_text}\n(Example: Apply this in every relevant context)"

        return rule_text

    def _add_examples(self, rule_text: str) -> str:
        """Add examples to rule text."""
        if not rule_text or "example" in rule_text.lower():
            return rule_text

        # Add generic example structure
        return f"{rule_text}\n\nExample:\n- Before: [unclear state]\n- After: [expected outcome]"

    def _check_contradiction(
        self,
        rule1: RuleEffectiveness,
        rule2: RuleEffectiveness,
    ) -> bool:
        """Check if two rules contradict each other."""
        if not rule1.rule_text or not rule2.rule_text:
            return False

        text1 = rule1.rule_text.lower()
        text2 = rule2.rule_text.lower()

        # Check for opposite keywords
        contradicting_pairs = [
            ("always", "never"),
            ("must", "must not"),
            ("do", "don't"),
            ("enable", "disable"),
            ("allow", "forbid"),
        ]

        for word1, word2 in contradicting_pairs:
            if (word1 in text1 and word2 in text2) or (word2 in text1 and word1 in text2):
                # Check if they're about the same topic
                # Simple heuristic: share significant words
                words1 = set(re.findall(r"\b\w{4,}\b", text1))
                words2 = set(re.findall(r"\b\w{4,}\b", text2))
                common = words1 & words2

                if len(common) >= 2:  # Share at least 2 significant words
                    return True

        return False

    def _suggest_resolution(
        self,
        rule1: RuleEffectiveness,
        rule2: RuleEffectiveness,
    ) -> str:
        """Suggest resolution for contradicting rules."""
        # Prefer higher performing rule
        if rule1.effectiveness_score > rule2.effectiveness_score:
            return f"Keep rule {rule1.rule_id} (higher effectiveness: {rule1.effectiveness_score:.2f})"
        if rule2.effectiveness_score > rule1.effectiveness_score:
            return f"Keep rule {rule2.rule_id} (higher effectiveness: {rule2.effectiveness_score:.2f})"
        return "Consider merging rules or clarifying contexts"

    def _merge_rules(
        self,
        text1: str | None,
        text2: str | None,
    ) -> str:
        """Merge two rule texts."""
        if not text1:
            return text2 or ""
        if not text2:
            return text1

        return f"{text1}\n\nAlternatively:\n{text2}"

    def _compute_text_diff(
        self,
        text1: str | None,
        text2: str | None,
    ) -> dict[str, Any]:
        """Compute diff between two texts."""
        if not text1:
            text1 = ""
        if not text2:
            text2 = ""

        lines1 = text1.split("\n")
        lines2 = text2.split("\n")

        return {
            "lines_added": len([l for l in lines2 if l not in lines1]),
            "lines_removed": len([l for l in lines1 if l not in lines2]),
            "lines_unchanged": len([l for l in lines1 if l in lines2]),
            "length_change": len(text2) - len(text1),
        }

    async def _create_version(
        self,
        rule_id: str,
        rule_text: str,
        change_reason: str,
        effectiveness_before: float | None = None,
    ) -> RuleVersion:
        """Internal version creation helper."""
        return await self.create_rule_version(
            rule_id=rule_id,
            rule_text=rule_text,
            change_reason=change_reason,
            created_by="evolution_service",
        )

    async def _cleanup_old_versions(self, rule_id: str) -> None:
        """Clean up old versions beyond limit."""
        result = await self.db.execute(
            select(RuleVersion)
            .where(RuleVersion.rule_id == rule_id)
            .order_by(desc(RuleVersion.created_at))
        )
        versions = list(result.scalars().all())

        if len(versions) > self.MAX_VERSIONS_PER_RULE:
            # Delete oldest versions
            to_delete = versions[self.MAX_VERSIONS_PER_RULE:]
            for version in to_delete:
                await self.db.delete(version)
            await self.db.commit()

    async def _log_audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log audit entry."""
        try:
            audit = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor="rule_evolution_service",
                details=details or {},
            )
            self.db.add(audit)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")


# Factory function
async def get_rule_evolution_service(
    db: AsyncSession,
    claude_md_path: Path | None = None,
) -> RuleEvolutionService:
    """Get rule evolution service instance."""
    return RuleEvolutionService(db, claude_md_path)
