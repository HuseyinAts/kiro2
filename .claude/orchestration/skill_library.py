"""Skill Library - Procedural Memory (Katman 5).

Voyager pattern + Agent Skills Standard + security gates.

FM-5 mitigation: safety_permissions allowlist, quality gate zorunlu.

Depolama: .claude/orchestration/skill_library/skills.json
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .schemas import ALLOWED_PERMISSIONS, Skill, file_lock
except ImportError:
    from schemas import ALLOWED_PERMISSIONS, Skill, file_lock  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


class SkillLibrary:
    """Voyager pattern + Agent Skills Standard + security gates.

    FM-5 mitigation: safety_permissions allowlist, quality gate.
    """

    def __init__(self, base_path: str = ".claude") -> None:
        self.base_path = Path(base_path)
        self._storage_path = (
            self.base_path / "orchestration" / "skill_library" / "skills.json"
        )
        self._skills: dict[str, Skill] = {}
        self._load()

    def _load(self) -> None:
        """Load skills from JSON storage."""
        if not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("skills", []):
                skill = Skill.from_dict(item)
                if skill.id:
                    self._skills[skill.id] = skill
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Failed to load skill library: %s", e)

    def _save(self) -> None:
        """Persist skills to JSON storage with file locking."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(self._storage_path):
            data = {
                "skills": [s.to_dict() for s in self._skills.values()],
                "total_count": len(self._skills),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    def add_skill(self, skill: Skill) -> str:
        """Add skill after validation. safety_permissions required.

        Args:
            skill: Skill to add.

        Returns:
            Skill ID.

        Raises:
            ValueError: If permissions invalid or missing.
        """
        if not self._validate_permissions(skill):
            raise ValueError(
                f"Invalid safety_permissions: {skill.safety_permissions}. "
                f"Allowed: {sorted(ALLOWED_PERMISSIONS)}"
            )

        if not skill.safety_permissions:
            raise ValueError("safety_permissions required (FM-5)")

        if not skill.id:
            skill.id = str(uuid.uuid4())[:12]

        now = datetime.now(timezone.utc).isoformat()
        skill.created_at = skill.created_at or now
        skill.updated_at = now
        skill.confidence = "LOW"

        self._skills[skill.id] = skill
        self._save()
        logger.info("Skill added: %s (%s)", skill.name, skill.id)
        return skill.id

    def find_skills(
        self,
        task_description: str = "",
        tags: list[str] | None = None,
        top_k: int = 3,
    ) -> list[Skill]:
        """Find skills by tag match + text similarity.

        Args:
            task_description: Task description for text matching.
            tags: Tags to filter by.
            top_k: Maximum results.

        Returns:
            Matching skills sorted by relevance.
        """
        results: list[tuple[Skill, float]] = []
        search_tags = set(t.lower() for t in (tags or []))
        search_words = set(task_description.lower().split()) if task_description else set()

        for skill in self._skills.values():
            score = 0.0

            # Tag overlap
            if search_tags:
                skill_tags = set(t.lower() for t in skill.tags)
                if skill_tags & search_tags:
                    score += len(skill_tags & search_tags) / len(search_tags | skill_tags)

            # Text similarity
            if search_words:
                desc_words = set(skill.description.lower().split())
                name_words = set(skill.name.lower().split())
                all_words = desc_words | name_words
                if all_words:
                    score += 0.5 * len(search_words & all_words) / max(1, len(search_words))

            # Boost by success rate
            score += 0.2 * skill.success_rate

            if score > 0:
                results.append((skill, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in results[:top_k]]

    def promote_skill(self, skill_id: str, test_results: dict[str, Any]) -> bool:
        """Promote skill confidence after quality gate pass.

        Args:
            skill_id: Skill to promote.
            test_results: Must contain {"passed": True} at minimum.

        Returns:
            True if promoted.

        Raises:
            ValueError: If skill not found or tests didn't pass.
        """
        if skill_id not in self._skills:
            raise ValueError(f"Skill not found: {skill_id}")

        if not test_results.get("passed"):
            raise ValueError("Cannot promote: tests did not pass (FM-5)")

        skill = self._skills[skill_id]
        confidence_order = ["LOW", "MEDIUM", "HIGH", "VERIFIED"]
        current_idx = confidence_order.index(skill.confidence)

        if current_idx < len(confidence_order) - 1:
            skill.confidence = confidence_order[current_idx + 1]
            skill.evidence.append(f"test_run:{datetime.now(timezone.utc).isoformat()}")
            skill.version = self._bump_version(skill.version)
            skill.updated_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.info(
                "Skill promoted: %s → %s (%s)",
                skill.name,
                skill.confidence,
                skill.id,
            )
            return True

        return False

    def record_usage(self, skill_id: str, success: bool) -> None:
        """Track skill usage and update success_rate.

        Args:
            skill_id: Skill used.
            success: Whether usage was successful.
        """
        if skill_id not in self._skills:
            return

        skill = self._skills[skill_id]
        total = skill.usage_count
        skill.usage_count += 1

        # Running average
        if total == 0:
            skill.success_rate = 1.0 if success else 0.0
        else:
            skill.success_rate = (skill.success_rate * total + (1.0 if success else 0.0)) / (
                total + 1
            )

        skill.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()

    def _validate_permissions(self, skill: Skill) -> bool:
        """Check safety_permissions against allowlist (FM-5)."""
        return all(p in ALLOWED_PERMISSIONS for p in skill.safety_permissions)

    @staticmethod
    def _bump_version(version: str) -> str:
        """Bump patch version (semver)."""
        try:
            parts = version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except (ValueError, IndexError):
            return "1.0.1"

    def get_skill(self, skill_id: str) -> Skill | None:
        """Get skill by ID."""
        return self._skills.get(skill_id)

    def list_skills(self) -> list[Skill]:
        """List all skills."""
        return list(self._skills.values())
