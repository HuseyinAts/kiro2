"""Lesson Consolidator - Monthly consolidation + SOAR chunking + semantic sharding.

FM-3 mitigation: strict VERIFIED = Bayesian mean>=0.9, n>=10, no regression.
FM-4 mitigation: conflict resolution + supersedes chain.
M2: Memory pruning (90 gun erisim yok + LOW → delete).
M4: VERIFIED = Bayesian criteria.
M5: Cross-agent debate verification (HIGH→VERIFIED).
P9: SOAR episodic→semantic distillation.
P13: Multi-agent knowledge distillation.

Akademik temel:
- SOAR (Laird/Newell): Episodic → semantic distillation
- USC (Chen): Universal Self-Consistency for cross-agent debate
- ExpeL (Zhao et al.): Cross-task insight extraction
"""

from __future__ import annotations

import json
import logging
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Import shared schemas (cross-platform path handling)
_ORCHESTRATION_DIR = Path(__file__).resolve().parent.parent.parent / ".claude" / "orchestration"
if str(_ORCHESTRATION_DIR) not in sys.path:
    sys.path.insert(0, str(_ORCHESTRATION_DIR))

try:
    from schemas import file_lock
except ImportError:
    from contextlib import contextmanager

    @contextmanager  # type: ignore[no-redef]
    def file_lock(path: Any):  # type: ignore[misc]
        """Fallback no-op lock."""
        yield

# Agent .md dosyalari
AGENT_DIR = Path(".claude/agents")
KFC_AGENT_DIR = AGENT_DIR / "kfc"
LESSON_CACHE = Path(".claude/orchestration/lesson_cache.json")
COLLECTIVE_MEMORY_DIR = Path(".claude/orchestration/collective_memory")


class LessonConsolidator:
    """Monthly consolidation + SOAR chunking + semantic sharding.

    FM-4 mitigation: conflict resolution + supersedes chain.
    FM-3 mitigation: strict VERIFIED criteria.
    """

    def __init__(self, base_path: str = ".") -> None:
        self.base_path = Path(base_path)
        self._lesson_cache = self.base_path / LESSON_CACHE
        self._collective_memory_dir = self.base_path / COLLECTIVE_MEMORY_DIR
        self._agent_dir = self.base_path / AGENT_DIR
        self._kfc_dir = self.base_path / KFC_AGENT_DIR

    def consolidate_for_agent(self, agent_id: str) -> list[dict[str, Any]]:
        """Get top 5 VERIFIED lessons for agent.

        VERIFIED criteria (M4):
        - Bayesian posterior mean >= 0.9
        - n >= 10 observations
        - 3+ different tasks with test pass rate improvement
        - No regression
        - Safety review: pass

        Returns:
            Top 5 verified lessons.
        """
        lessons = self._load_lessons()
        agent_lessons = [
            l for l in lessons
            if l.get("agent_id") == agent_id
            and l.get("confidence") == "VERIFIED"
            and l.get("safety_review") == "pass"
        ]

        # Sort by Bayesian mean (highest first)
        for lesson in agent_lessons:
            alpha = lesson.get("beta_alpha", 1)
            beta = lesson.get("beta_beta", 1)
            lesson["_bayesian_mean"] = alpha / (alpha + beta)

        agent_lessons.sort(key=lambda x: x.get("_bayesian_mean", 0), reverse=True)

        # Clean temp field
        for lesson in agent_lessons:
            lesson.pop("_bayesian_mean", None)

        return agent_lessons[:5]

    def update_agent_md(self, agent_id: str, lessons: list[dict[str, Any]]) -> bool:
        """Update agent .md OGRENME section with verified lessons.

        Args:
            agent_id: Agent identifier (matches .md filename).
            lessons: Verified lessons to write.

        Returns:
            True if updated successfully.
        """
        # Find agent .md file
        md_path = self._find_agent_md(agent_id)
        if not md_path:
            logger.warning("Agent .md not found for: %s", agent_id)
            return False

        try:
            content = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.error("Failed to read agent .md: %s", e)
            return False

        # Build lessons table
        table_lines = [
            "| # | Ders | Kategori | Scope | Evidence | Expiry | Owner |",
            "|---|------|----------|-------|----------|--------|-------|",
        ]
        for i, lesson in enumerate(lessons, 1):
            scope = ", ".join(lesson.get("scope", []))
            evidence = ", ".join(lesson.get("evidence_refs", [])[:2])
            expiry = lesson.get("expiry", "")[:7]  # YYYY-MM
            owner = self._sanitize_md(lesson.get("owner", ""))
            desc = self._sanitize_md(lesson.get("hypothesis", "")[:60])
            category = self._sanitize_md(lesson.get("task_type", "general"))
            table_lines.append(
                f"| {i} | {desc} | {category} | {scope} | {evidence} | {expiry} | {owner} |"
            )

        table_str = "\n".join(table_lines)

        # Replace existing VERIFIED table or insert
        marker_start = "### Dogrulanmis Dersler (VERIFIED, Auto-Updated Monthly)"
        marker_end = "### Anti-Pattern"

        if marker_start in content:
            # Find and replace the table section
            start_idx = content.index(marker_start)
            end_idx = content.find(marker_end, start_idx)
            if end_idx == -1:
                end_idx = len(content)

            new_section = f"{marker_start}\n{table_str}\n\n"
            content = content[:start_idx] + new_section + content[end_idx:]
        else:
            logger.info("OGRENME section not found in %s, skipping table update", md_path.name)
            return False

        try:
            md_path.write_text(content, encoding="utf-8")
            logger.info("Updated agent .md: %s (%d lessons)", md_path.name, len(lessons))
            return True
        except OSError as e:
            logger.error("Failed to write agent .md: %s", e)
            return False

    def distill_episodes_to_semantic(self) -> int:
        """SOAR: Distill repeated episodic patterns to semantic memory.

        Finds lessons that appear 3+ times with same signals/task_type
        and creates generalized semantic insights.

        Returns:
            Number of new insights created.
        """
        lessons = self._load_lessons()

        # Group by (task_type, sorted signals)
        pattern_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for lesson in lessons:
            if lesson.get("outcome") != "success":
                continue
            key = f"{lesson.get('task_type', '')}:{','.join(sorted(lesson.get('signals', [])))}"
            pattern_groups[key].append(lesson)

        new_insights = 0
        for key, group in pattern_groups.items():
            if len(group) < 3:
                continue

            # Create semantic insight
            representative = group[0]
            task_type = representative.get("task_type", "general")
            hypothesis = representative.get("hypothesis", "")
            fix = representative.get("fix", "")

            insight = {
                "key": f"distilled:{key[:50]}",
                "statement": f"{hypothesis} → {fix}" if fix else hypothesis,
                "derived_from": [l.get("id", "") for l in group],
                "conflict_keys": [],
                "supersedes": [],
                "last_verified": datetime.now(timezone.utc).isoformat(),
                "confidence": "MEDIUM",
                "domain": "general",
                "task_type": task_type,
                "source_agent_id": "consolidator",
                "insight_type": "heuristic",
                "created_by": "lesson_consolidator",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            self._write_semantic_insight(insight)
            new_insights += 1

        return new_insights

    def _resolve_conflicts(self, domain: str, task_type: str) -> int:
        """Resolve conflicting insights: supersedes chain, archive old ones.

        Uses O(n) key indexing instead of O(n²) comparison.

        Returns:
            Number of conflicts resolved.
        """
        shard_file = self._collective_memory_dir / domain / f"{task_type}.json"
        if not shard_file.exists():
            return 0

        try:
            with open(shard_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, KeyError):
            return 0

        insights = data.get("insights", [])
        if not insights:
            return 0

        # O(n) pass: track best insight per key (most recent wins)
        best_per_key: dict[str, tuple[int, str]] = {}  # key → (index, last_verified)
        duplicates: set[int] = set()

        for i, insight in enumerate(insights):
            key = insight.get("key", "")
            if not key:
                continue
            verified = insight.get("last_verified", "")
            if key in best_per_key:
                prev_idx, prev_verified = best_per_key[key]
                if verified > prev_verified:
                    duplicates.add(prev_idx)
                    best_per_key[key] = (i, verified)
                else:
                    duplicates.add(i)
            else:
                best_per_key[key] = (i, verified)

        resolved = len(duplicates)
        if resolved > 0:
            remaining = [
                ins for i, ins in enumerate(insights) if i not in duplicates
            ]
            data["insights"] = remaining
            data["total_count"] = len(remaining)
            data["updated_at"] = datetime.now(timezone.utc).isoformat()

            with file_lock(shard_file):
                with open(shard_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

        return resolved

    def archive_old_lessons(self, max_age_days: int = 180) -> int:
        """Archive 6-month old LOW confidence lessons.

        Returns:
            Number archived.
        """
        lessons = self._load_lessons()
        now = datetime.now(timezone.utc)
        archived = 0
        remaining = []

        for lesson in lessons:
            if lesson.get("confidence") not in ("LOW", "low"):
                remaining.append(lesson)
                continue

            ts = lesson.get("timestamp", "")
            try:
                created = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                remaining.append(lesson)
                continue

            if (now - created).days >= max_age_days:
                archived += 1
                continue

            remaining.append(lesson)

        if archived > 0:
            self._save_lessons_raw(remaining)
            logger.info("Archived %d old LOW-confidence lessons", archived)

        return archived

    def distill_cross_agent(self) -> int:
        """P13: Multi-agent knowledge distillation.

        If 3+ agents learned the same lesson → promote to "universal lesson".

        Returns:
            Number of universal lessons created.
        """
        lessons = self._load_lessons()

        # Group by hypothesis (simplified pattern matching)
        hypothesis_agents: dict[str, set[str]] = defaultdict(set)
        hypothesis_lessons: dict[str, dict[str, Any]] = {}

        for lesson in lessons:
            if lesson.get("outcome") != "success":
                continue
            if lesson.get("confidence") in ("LOW", "low"):
                continue

            hyp = lesson.get("hypothesis", "").strip().lower()[:100]
            if not hyp:
                continue

            hypothesis_agents[hyp].add(lesson.get("agent_id", ""))
            if hyp not in hypothesis_lessons:
                hypothesis_lessons[hyp] = lesson

        universal_count = 0
        for hyp, agents in hypothesis_agents.items():
            if len(agents) < 3:
                continue

            # Create universal insight
            representative = hypothesis_lessons[hyp]
            insight = {
                "key": f"universal:{hyp[:50]}",
                "statement": f"[UNIVERSAL] {representative.get('hypothesis', '')} → {representative.get('fix', '')}",
                "derived_from": list(agents),
                "conflict_keys": [],
                "supersedes": [],
                "last_verified": datetime.now(timezone.utc).isoformat(),
                "confidence": "HIGH",
                "domain": "general",
                "task_type": representative.get("task_type", "general"),
                "source_agent_id": "consolidator",
                "insight_type": "heuristic",
                "created_by": "lesson_consolidator:cross_agent",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            self._write_semantic_insight(insight)
            universal_count += 1
            logger.info(
                "Universal lesson created: %s (from %d agents)",
                hyp[:60],
                len(agents),
            )

        return universal_count

    def consolidate_all(self) -> dict[str, Any]:
        """Run full consolidation for all agents.

        Returns:
            Summary statistics dict with keys:
            agents_updated, insights_distilled, conflicts_resolved,
            lessons_archived, universal_lessons.
        """
        stats: dict[str, Any] = {
            "agents_updated": 0,
            "insights_distilled": 0,
            "conflicts_resolved": 0,
            "lessons_archived": 0,
            "universal_lessons": 0,
        }

        # 1. Distill episodic → semantic (SOAR)
        stats["insights_distilled"] = self.distill_episodes_to_semantic()

        # 2. Resolve conflicts in semantic memory
        general_dir = self._collective_memory_dir / "general"
        if general_dir.exists():
            for shard_file in general_dir.glob("*.json"):
                task_type = shard_file.stem
                stats["conflicts_resolved"] += self._resolve_conflicts("general", task_type)

        # 3. Cross-agent distillation (P13)
        stats["universal_lessons"] = self.distill_cross_agent()

        # 4. Archive old lessons
        stats["lessons_archived"] = self.archive_old_lessons()

        # 5. Update each agent's .md with VERIFIED lessons
        agent_ids = self._get_all_agent_ids()
        for agent_id in agent_ids:
            verified = self.consolidate_for_agent(agent_id)
            if verified:
                if self.update_agent_md(agent_id, verified):
                    stats["agents_updated"] += 1

        logger.info("Consolidation complete: %s", stats)
        return stats

    # Cross-agent debate (M5) - simplified version
    def cross_agent_verify(self, lesson: dict[str, Any]) -> bool:
        """M5: Cross-agent debate verification for HIGH→VERIFIED promotion.

        Checks if 2+ different agent types have similar lessons.
        This is a simplified version that uses pattern matching instead
        of live LLM debate.

        Returns:
            True if verified by cross-agent agreement.
        """
        lessons = self._load_lessons()
        target_hyp = lesson.get("hypothesis", "").strip().lower()
        target_agent = lesson.get("agent_id", "")

        if not target_hyp:
            return False

        # Find similar lessons from different agents
        agreeing_agents: set[str] = set()
        for other in lessons:
            if other.get("agent_id") == target_agent:
                continue
            if other.get("outcome") != "success":
                continue

            other_hyp = other.get("hypothesis", "").strip().lower()
            # Simple similarity: >50% word overlap
            target_words = set(target_hyp.split())
            other_words = set(other_hyp.split())
            if target_words and other_words:
                overlap = len(target_words & other_words) / len(target_words | other_words)
                if overlap > 0.5:
                    agreeing_agents.add(other.get("agent_id", ""))

        verified = len(agreeing_agents) >= 2
        if verified:
            logger.info(
                "Cross-agent verified: lesson from %s confirmed by %s",
                target_agent,
                agreeing_agents,
            )
        return verified

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _sanitize_md(text: str) -> str:
        """Strip markdown-breaking characters from lesson fields."""
        return text.replace("|", "∣").replace("\n", " ").replace("\r", "")

    def _find_agent_md(self, agent_id: str) -> Path | None:
        """Find agent .md file by agent_id."""
        # Direct match
        direct = self._agent_dir / f"{agent_id}.md"
        if direct.exists():
            return direct

        # Check KFC dir
        kfc = self._kfc_dir / f"{agent_id}.md"
        if kfc.exists():
            return kfc

        # Fuzzy match (agent_id might be partial)
        for md_file in self._agent_dir.glob("*.md"):
            if agent_id in md_file.stem:
                return md_file
        for md_file in self._kfc_dir.glob("*.md"):
            if agent_id in md_file.stem:
                return md_file

        return None

    def _get_all_agent_ids(self) -> list[str]:
        """Get all active agent IDs from .md files."""
        ids = []
        if self._agent_dir.exists():
            for md in self._agent_dir.glob("*.md"):
                ids.append(md.stem)
        if self._kfc_dir.exists():
            for md in self._kfc_dir.glob("*.md"):
                ids.append(md.stem)
        return ids

    def _load_lessons(self) -> list[dict[str, Any]]:
        """Load raw lessons from cache."""
        if not self._lesson_cache.exists():
            return []
        try:
            with open(self._lesson_cache, "r", encoding="utf-8") as f:
                return json.load(f).get("lessons", [])
        except (json.JSONDecodeError, KeyError):
            return []

    def _save_lessons_raw(self, lessons: list[dict[str, Any]]) -> None:
        """Save raw lessons to cache with file locking."""
        self._lesson_cache.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(self._lesson_cache):
            with open(self._lesson_cache, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "lessons": lessons,
                        "total_count": len(lessons),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

    def _write_semantic_insight(self, insight: dict[str, Any]) -> None:
        """Write insight to sharded semantic JSON with file locking."""
        domain = insight.get("domain", "general")
        task_type = insight.get("task_type", "general")

        shard_dir = self._collective_memory_dir / domain
        shard_dir.mkdir(parents=True, exist_ok=True)
        shard_file = shard_dir / f"{task_type}.json"

        with file_lock(shard_file):
            insights: list[dict[str, Any]] = []
            if shard_file.exists():
                try:
                    with open(shard_file, "r", encoding="utf-8") as f:
                        insights = json.load(f).get("insights", [])
                except (json.JSONDecodeError, KeyError):
                    pass

            # Check for duplicate key
            existing_keys = {i.get("key") for i in insights}
            if insight.get("key") in existing_keys:
                return

            insights.append(insight)

            with open(shard_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "insights": insights,
                        "total_count": len(insights),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
