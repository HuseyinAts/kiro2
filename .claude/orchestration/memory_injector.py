"""Memory Injector - Pre-task hafiza enjeksiyonu.

WM-State / WM-Scratch ayrimi ile agent'lara context saglar.
ACT-R activation skorlamasi, BDI state separation, token limit enforcement.

Akademik temel:
- ACT-R (Anderson): 4-faktorlu activation scoring
- BDI (Bratman): Belief/Desire/Intention ayrim
- Reflexion (Shinn et al.): Evidence-based reflection formatting

FM-2 mitigation: WM-State read-only, agent degistiremez.
FM-6 mitigation: Max 10 lesson, <2000 token, confidence >= MEDIUM.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .schemas import (
        CONFIDENCE_SCORES,
        MAX_LESSONS,
        MAX_TOKEN_BUDGET,
        MIN_CONFIDENCE,
        InjectedContext,
        Lesson,
        SemanticInsight,
        SkillPointer,
        file_lock,
    )
except ImportError:
    from schemas import (  # type: ignore[no-redef]
        CONFIDENCE_SCORES,
        MAX_LESSONS,
        MAX_TOKEN_BUDGET,
        MIN_CONFIDENCE,
        InjectedContext,
        Lesson,
        SemanticInsight,
        SkillPointer,
        file_lock,
    )

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ACT-R Activation Scoring
# ---------------------------------------------------------------------------


def _score_activation(
    item: Lesson | SemanticInsight,
    task_type: str,
    task_tags: list[str],
) -> float:
    """ACT-R 4-factor activation score.

    activation = 0.25*recency + 0.20*frequency + 0.35*relevance + 0.20*success_confidence

    Args:
        item: Lesson or SemanticInsight.
        task_type: Current task type for relevance matching.
        task_tags: Current task tags for relevance matching.

    Returns:
        Activation score (0-1).
    """
    now = datetime.now(timezone.utc)

    # Recency: exp(-0.1 * days_since_last_access)
    last_access_str = getattr(item, "last_accessed", "") or getattr(
        item, "last_verified", ""
    )
    if last_access_str:
        try:
            last_dt = datetime.fromisoformat(last_access_str.replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            days = max(0, (now - last_dt).total_seconds() / 86400)
        except (ValueError, TypeError):
            days = 30.0
    else:
        days = 30.0
    recency = math.exp(-0.1 * days)

    # Frequency: min(access_count / 20, 1.0)
    access_count = getattr(item, "access_count", 0) or getattr(
        item, "usage_count", 0
    )
    if not access_count:
        access_count = 0
    frequency = min(access_count / 20, 1.0)

    # Relevance: tag overlap + task_type match (0-1)
    item_tags = getattr(item, "scope", []) or getattr(item, "tags", []) or []
    item_task_type = getattr(item, "task_type", "")
    tag_overlap = 0.0
    if task_tags and item_tags:
        tag_set = set(t.lower() for t in task_tags)
        item_set = set(t.lower() for t in item_tags)
        if tag_set or item_set:
            tag_overlap = len(tag_set & item_set) / max(1, len(tag_set | item_set))
    type_match = 1.0 if item_task_type and item_task_type == task_type else 0.0
    relevance = 0.6 * tag_overlap + 0.4 * type_match

    # Success confidence
    confidence_str = getattr(item, "confidence", "LOW")
    success_conf = CONFIDENCE_SCORES.get(confidence_str, 0.2)

    activation = 0.25 * recency + 0.20 * frequency + 0.35 * relevance + 0.20 * success_conf
    return round(activation, 4)


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


def _estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token)."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# MemoryInjector
# ---------------------------------------------------------------------------


class MemoryInjector:
    """Pre-task hafiza enjeksiyonu. WM-State / WM-Scratch ayrimi.

    FM-2 mitigation: WM-State read-only, agent degistiremez.
    FM-6 mitigation: Max 10 lesson, <2000 token, confidence >= MEDIUM.
    """

    def __init__(
        self,
        base_path: str = ".claude",
        db_url: str | None = None,
    ) -> None:
        self.base_path = Path(base_path)
        self.db_url = db_url or "postgresql+asyncpg://localhost:5434/kiro2"
        self._skill_library_path = (
            self.base_path / "orchestration" / "skill_library" / "skills.json"
        )
        self._collective_memory_dir = self.base_path / "orchestration" / "collective_memory"

    def get_context(
        self,
        agent_id: str,
        task_description: str,
        task_type: str = "",
        task_tags: list[str] | None = None,
        desires: list[str] | None = None,
        intentions: list[str] | None = None,
    ) -> InjectedContext:
        """Build WM-State context for injection.

        Args:
            agent_id: Target agent identifier.
            task_description: Current task description.
            task_type: Task type for filtering.
            task_tags: Tags for relevance matching.
            desires: BDI desires (task goals + success criteria).
            intentions: BDI intentions (selected strategy + plan).

        Returns:
            InjectedContext ready for markdown formatting.
        """
        tags = task_tags or []

        # Query all memory layers
        episodic_lessons = self._query_episodic(agent_id, task_type)
        semantic_insights = self._query_semantic(task_type)
        skills = self._query_skills(task_type, tags)

        # Score and sort by activation
        scored_lessons = [
            (lesson, _score_activation(lesson, task_type, tags))
            for lesson in episodic_lessons
        ]
        scored_lessons.sort(key=lambda x: x[1], reverse=True)

        scored_insights = [
            (insight, _score_activation(insight, task_type, tags))
            for insight in semantic_insights
        ]
        scored_insights.sort(key=lambda x: x[1], reverse=True)

        # Separate positive lessons and anti-patterns
        positive = []
        anti_patterns = []
        for lesson, score in scored_lessons:
            if lesson.outcome == "failure":
                anti_patterns.append(lesson)
            else:
                positive.append(lesson)

        # Separate facts and heuristics
        facts = [i for i, _ in scored_insights if i.insight_type == "fact"]
        heuristics = [i for i, _ in scored_insights if i.insight_type == "heuristic"]

        # Build beliefs (BDI - P7)
        beliefs: list[str] = []
        for fact in facts[:3]:
            beliefs.append(f"[FACT] {fact.statement}")
        for lesson in positive[:3]:
            beliefs.append(f"[LESSON] {lesson.hypothesis} → {lesson.fix}")
        for ap in anti_patterns[:2]:
            beliefs.append(f"[ANTI-PATTERN] {ap.hypothesis}")

        # Apply token budget (FM-6)
        ctx = InjectedContext(
            beliefs=beliefs,
            desires=desires or [task_description],
            intentions=intentions or [],
            lessons=positive[:MAX_LESSONS],
            anti_patterns=anti_patterns[:3],
            skills=skills[:3],
            facts=facts[:5],
        )

        # Trim to token budget (all categories, not just lessons)
        md = self.format_as_markdown(ctx)
        ctx.token_count = _estimate_tokens(md)

        # Progressive trimming: lessons → anti_patterns → facts → skills → beliefs
        trim_order = [
            ("lessons", 1),
            ("anti_patterns", 1),
            ("facts", 1),
            ("skills", 1),
            ("beliefs", 2),
        ]
        while ctx.token_count > MAX_TOKEN_BUDGET:
            trimmed = False
            for attr, min_len in trim_order:
                lst = getattr(ctx, attr)
                if len(lst) > min_len:
                    lst.pop()
                    trimmed = True
                    break
            if not trimmed:
                break
            md = self.format_as_markdown(ctx)
            ctx.token_count = _estimate_tokens(md)

        # Update access counts for used lessons
        self._update_access_counts(ctx.lessons + ctx.anti_patterns)

        return ctx

    def _update_access_counts(self, used_lessons: list[Lesson]) -> None:
        """Update access_count and last_accessed for used lessons in cache."""
        if not used_lessons:
            return
        cache_file = self.base_path / "orchestration" / "lesson_cache.json"
        if not cache_file.exists():
            return
        try:
            with file_lock(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                used_ids = {l.id for l in used_lessons}
                now = datetime.now(timezone.utc).isoformat()
                modified = False
                for item in data.get("lessons", []):
                    if item.get("id") in used_ids:
                        item["access_count"] = item.get("access_count", 0) + 1
                        item["last_accessed"] = now
                        modified = True
                if modified:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to update access counts: %s", e)

    def _query_episodic(self, agent_id: str, task_type: str) -> list[Lesson]:
        """Query episodic memory from JSON fallback.

        Reads lessons from coordination results or a local cache file.
        For full DB integration, this calls MemoryStore async methods.
        """
        lessons: list[Lesson] = []

        # Try loading from local lesson cache
        cache_file = self.base_path / "orchestration" / "lesson_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("lessons", []):
                    confidence = item.get("confidence", "LOW")
                    if CONFIDENCE_SCORES.get(confidence, 0) < CONFIDENCE_SCORES[MIN_CONFIDENCE]:
                        continue
                    if item.get("agent_id") and item["agent_id"] != agent_id:
                        continue
                    if item.get("safety_review") in ("fail", "quarantine"):
                        continue
                    lessons.append(Lesson(**{
                        k: v for k, v in item.items()
                        if k in Lesson.__dataclass_fields__
                    }))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("Failed to load lesson cache: %s", e)

        return lessons

    def _query_semantic(self, task_type: str) -> list[SemanticInsight]:
        """Query semantic memory from sharded JSON (Katman 4).

        Reads from collective_memory/{domain}/{task_type}.json
        Falls back to collective_memory/general/general.json
        """
        insights: list[SemanticInsight] = []

        # Try task-type specific shard
        paths_to_try = []
        if task_type:
            paths_to_try.append(
                self._collective_memory_dir / "general" / f"{task_type}.json"
            )
        paths_to_try.append(self._collective_memory_dir / "general" / "general.json")

        # Also try legacy single-file
        legacy = self.base_path / "orchestration" / "collective_memory.json"
        if legacy.exists():
            paths_to_try.append(legacy)

        for path in paths_to_try:
            if not path.exists():
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("insights", []):
                    confidence = item.get("confidence", "LOW")
                    if CONFIDENCE_SCORES.get(confidence, 0) < CONFIDENCE_SCORES[MIN_CONFIDENCE]:
                        continue
                    insights.append(SemanticInsight(
                        key=item.get("key", item.get("insight_id", "")),
                        statement=item.get("statement", item.get("content", "")),
                        derived_from=item.get("derived_from", []),
                        conflict_keys=item.get("conflict_keys", []),
                        supersedes=item.get("supersedes", []),
                        last_verified=item.get("last_verified", item.get("updated_at", "")),
                        confidence=confidence,
                        domain=item.get("domain", "general"),
                        task_type=item.get("task_type", ""),
                        source_agent_id=item.get("source_agent_id", ""),
                        insight_type=item.get("insight_type", "heuristic"),
                        created_by=item.get("created_by", ""),
                        created_at=item.get("created_at", ""),
                    ))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("Failed to load semantic memory from %s: %s", path, e)

        return insights

    def _query_skills(
        self, task_type: str, tags: list[str]
    ) -> list[SkillPointer]:
        """Query skill library (Katman 5)."""
        skills: list[SkillPointer] = []

        if not self._skill_library_path.exists():
            return skills

        try:
            with open(self._skill_library_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("skills", []):
                confidence = item.get("confidence", "LOW")
                if CONFIDENCE_SCORES.get(confidence, 0) < CONFIDENCE_SCORES[MIN_CONFIDENCE]:
                    continue
                skill_tags = item.get("tags", [])
                # Tag match filter
                if tags:
                    overlap = set(t.lower() for t in tags) & set(
                        t.lower() for t in skill_tags
                    )
                    if not overlap:
                        continue
                skills.append(SkillPointer(
                    id=item.get("id", ""),
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    tags=skill_tags,
                    confidence=confidence,
                    success_rate=item.get("success_rate", 0.0),
                ))
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("Failed to load skill library: %s", e)

        return skills

    def _format_reflexion(self, failures: list[Lesson]) -> str:
        """Evidence-based reflection: Signal→Hypothesis→Fix→Result→Generalization."""
        if not failures:
            return ""

        lines = ["### Anti-Pattern'ler (Kacin!)"]
        for lesson in failures[:3]:
            signals = ", ".join(lesson.signals) if lesson.signals else "unknown"
            lines.append(f"- **Signal:** {signals}")
            if lesson.hypothesis:
                lines.append(f"  **Hypothesis:** {lesson.hypothesis}")
            if lesson.fix:
                lines.append(f"  **Fix:** {lesson.fix}")
            if lesson.result:
                lines.append(f"  **Result:** {lesson.result}")
            symptoms = lesson.applicability.get("symptoms", [])
            if symptoms:
                lines.append(f"  **When:** {', '.join(symptoms)}")
            lines.append("")

        return "\n".join(lines)

    def format_as_markdown(self, context: InjectedContext) -> str:
        """Format WM-State as markdown for injection.

        Injection categories:
        - Fact (dogrulanmis): codebase gerceleri
        - Lesson (sartli oneri): applicability kosullari ile
        - Anti-pattern (kacin): ayri koleksiyonda
        - Skill pointer (modul referansi): sablon/komut degil

        Token limit: <2000.
        """
        sections: list[str] = []

        # BDI Header (P7)
        sections.append("## WM-State (Read-Only)")
        sections.append("")

        # Beliefs
        if context.beliefs:
            sections.append("### Beliefs (Bilgi)")
            for belief in context.beliefs:
                sections.append(f"- {belief}")
            sections.append("")

        # Desires
        if context.desires:
            sections.append("### Desires (Hedef)")
            for desire in context.desires:
                sections.append(f"- {desire}")
            sections.append("")

        # Intentions
        if context.intentions:
            sections.append("### Intentions (Strateji)")
            for intention in context.intentions:
                sections.append(f"- {intention}")
            sections.append("")

        # Facts
        if context.facts:
            sections.append("### Facts (Dogrulanmis)")
            for fact in context.facts:
                conf_label = f"[{fact.confidence}]"
                sections.append(f"- {conf_label} {fact.statement}")
            sections.append("")

        # Lessons
        if context.lessons:
            sections.append("### Lessons (Sartli Oneri)")
            for lesson in context.lessons:
                symptoms = lesson.applicability.get("symptoms", [])
                cond = f" (when: {', '.join(symptoms)})" if symptoms else ""
                sections.append(
                    f"- [{lesson.confidence}] {lesson.hypothesis} → {lesson.fix}{cond}"
                )
            sections.append("")

        # Anti-patterns
        if context.anti_patterns:
            sections.append(self._format_reflexion(context.anti_patterns))

        # Skills
        if context.skills:
            sections.append("### Skills (Modul Referansi)")
            for skill in context.skills:
                sections.append(
                    f"- **{skill.name}**: {skill.description} "
                    f"(success: {skill.success_rate:.0%})"
                )
            sections.append("")

        return "\n".join(sections)


# ---------------------------------------------------------------------------
# CLI entry point (for hooks)
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for SessionStart hook.

    Reads agent_id from .claude/coordination/state.json,
    generates WM-State context, writes to stdout for injection.
    """
    import sys

    base_path = Path(".claude")
    state_file = base_path / "coordination" / "state.json"

    agent_id = "unknown"
    task_description = ""
    task_type = ""

    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            agent_id = state.get("current_agent_id", "unknown")
            task_description = state.get("current_task", "")
            task_type = state.get("task_type", "")
        except (json.JSONDecodeError, KeyError):
            pass

    injector = MemoryInjector(base_path=str(base_path))
    ctx = injector.get_context(
        agent_id=agent_id,
        task_description=task_description,
        task_type=task_type,
    )

    if ctx.lessons or ctx.anti_patterns or ctx.facts or ctx.skills:
        md = injector.format_as_markdown(ctx)
        print(md)
        logger.info(
            "Injected %d lessons, %d anti-patterns, %d facts, %d skills (%d tokens)",
            len(ctx.lessons),
            len(ctx.anti_patterns),
            len(ctx.facts),
            len(ctx.skills),
            ctx.token_count,
        )
    else:
        logger.info("No relevant context found for agent=%s", agent_id)


if __name__ == "__main__":
    main()
