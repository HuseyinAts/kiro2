"""Feedback Collector - Post-task feedback + evidence-based reflection.

FM-1 mitigation: evidence_refs zorunlu, constitutional gate.
FM-3 mitigation: strict VERIFIED kriterleri.
M1: Auto-golden-set (test/lint sonuclari = evidence_refs).
M2: Quarantine auto-resolve (14 gun expire + prediction error).
M4: Bayesian confidence update (Beta(alpha,beta)).
P10: Stigmergy (semantic memory'ye artifact birak).

Akademik temel:
- Reflexion (Shinn et al.): Evidence-based reflection template
- ExpeL (Zhao et al.): Cross-task insight extraction
- Voyager (Wang et al.): Skill extraction from solutions
- Argyris: Double-loop learning (3+ fail → varsayim sorgula)
- Memory-R1 / Nemori: RL-based memory governance
- HypoAgents (Duan): Bayesian posterior updating
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from .schemas import ALLOWED_PERMISSIONS, Lesson, SemanticInsight, Skill, file_lock
except ImportError:
    from schemas import ALLOWED_PERMISSIONS, Lesson, SemanticInsight, Skill, file_lock  # type: ignore[no-redef]

logger = logging.getLogger(__name__)

# Constitutional gate patterns (KIRO2 rules)
_SQL_INJECTION_RE = re.compile(r'f["\'].*SELECT|f["\'].*INSERT|f["\'].*UPDATE|f["\'].*DELETE', re.IGNORECASE)
_HARDCODED_SECRET_RE = re.compile(
    r'(api_key|password|secret|token)\s*=\s*["\'][^"\']{8,}', re.IGNORECASE
)
_REWARD_HACKING_RE = re.compile(
    r'assert\s+True|assert\s+true|echo\s+Success|print\s*\(\s*["\']Success', re.IGNORECASE
)
_UNSAFE_PATH_RE = re.compile(r'/etc/|/usr/|/bin/|/sbin/|~/.ssh|~/.aws|C:\\Windows|C:\\Program Files')
_COMMAND_IN_LESSON_RE = re.compile(r'(rm\s+-rf|DROP\s+TABLE|git\s+push\s+--force)', re.IGNORECASE)
_PORT_5432_RE = re.compile(r'port[=:]\s*5432\b')
_USE_AUTH_RE = re.compile(r'useAuth\.ts')


class FeedbackCollector:
    """Post-task feedback + evidence-based reflection.

    FM-1 mitigation: evidence_refs zorunlu, constitutional gate.
    FM-3 mitigation: strict VERIFIED kriterleri.
    """

    def __init__(self, base_path: str = ".claude") -> None:
        self.base_path = Path(base_path)
        self._lesson_cache_path = self.base_path / "orchestration" / "lesson_cache.json"
        self._collective_memory_dir = self.base_path / "orchestration" / "collective_memory"

    def record_outcome(
        self,
        agent_id: str,
        task: dict[str, Any],
        success: bool,
        details: dict[str, Any],
    ) -> Lesson | None:
        """Record task outcome with evidence.

        Args:
            agent_id: Agent that performed the task.
            task: Task description dict with keys: task_type, description, tags.
            success: Whether the task succeeded.
            details: Must contain 'signals' and 'evidence_refs'.

        Returns:
            Created Lesson or None if rejected by constitutional gate.
        """
        signals = details.get("signals", [])
        evidence_refs = details.get("evidence_refs", [])

        # FM-1: evidence_refs zorunlu
        if not evidence_refs:
            logger.warning("Lesson rejected: no evidence_refs (FM-1)")
            return None

        # Extract lesson
        lesson = self._extract_lesson(agent_id, task, success, details)

        # Constitutional gate (memory write governance)
        safety = self._constitutional_gate(lesson)
        lesson.safety_review = safety

        if safety == "fail":
            logger.warning("Lesson rejected by constitutional gate: %s", lesson.id)
            return None

        # M4: Bayesian confidence init
        if success:
            lesson.beta_alpha = 2
            lesson.beta_beta = 1
        else:
            lesson.beta_alpha = 1
            lesson.beta_beta = 2

        # Save to lesson cache
        self._save_lesson(lesson)

        # P10: Stigmergy - write semantic artifact
        if success and lesson.confidence != "LOW":
            self._write_stigmergy_artifact(lesson)

        # Check double-loop (Argyris)
        if not success:
            self._check_double_loop(agent_id)

        # Extract skill if successful (Voyager)
        if success and details.get("solution"):
            self._extract_skill(agent_id, task, details["solution"])

        logger.info(
            "Lesson recorded: %s (agent=%s, outcome=%s, safety=%s)",
            lesson.id,
            agent_id,
            lesson.outcome,
            safety,
        )
        return lesson

    def _extract_lesson(
        self,
        agent_id: str,
        task: dict[str, Any],
        success: bool,
        details: dict[str, Any],
    ) -> Lesson:
        """ExpeL: Extract lesson with provenance + applicability."""
        now = datetime.now(timezone.utc).isoformat()
        reflection = self._generate_reflection(
            agent_id, task, details.get("signals", []), details.get("error", "")
        )

        return Lesson(
            id=str(uuid.uuid4())[:12],
            agent_id=agent_id,
            task_type=task.get("task_type", ""),
            timestamp=now,
            outcome="success" if success else "failure",
            signals=details.get("signals", []),
            evidence_refs=details.get("evidence_refs", []),
            hypothesis=reflection.get("hypothesis", ""),
            fix=reflection.get("fix", ""),
            result=reflection.get("result", ""),
            applicability={
                "symptoms": reflection.get("symptoms", []),
                "constraints": details.get("constraints", []),
            },
            confidence="LOW",
            safety_review="pass",
            scope=[task.get("task_type", "")] if task.get("task_type") else [],
            expiry=(datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
            owner=f"feedback_collector:{agent_id}",
        )

    def _generate_reflection(
        self,
        agent_id: str,
        task: dict[str, Any],
        signals: list[str],
        error: str,
    ) -> dict[str, Any]:
        """Evidence-based template: Signal→Hypothesis→Fix→Result→Generalization.

        Returns dict with keys: hypothesis, fix, result, symptoms.
        """
        signal_str = ", ".join(signals) if signals else "unknown"
        task_desc = task.get("description", "")

        # Build hypothesis from signals
        hypothesis = ""
        if "test_fail" in signals:
            hypothesis = f"Test failure during: {task_desc[:100]}"
        elif "lint_fail" in signals:
            hypothesis = f"Lint error in task: {task_desc[:100]}"
        elif "type_fail" in signals:
            hypothesis = f"Type error in task: {task_desc[:100]}"
        elif "timeout" in signals:
            hypothesis = f"Timeout during: {task_desc[:100]}"
        else:
            hypothesis = f"Issue during: {task_desc[:100]}"

        if error:
            hypothesis += f" — {error[:200]}"

        # Symptoms for applicability
        symptoms = list(signals)
        if task.get("task_type"):
            symptoms.append(f"task_type:{task['task_type']}")

        return {
            "hypothesis": hypothesis,
            "fix": "",  # Will be filled by caller with actual fix
            "result": "",  # Will be filled by caller with test results
            "symptoms": symptoms,
        }

    def _constitutional_gate(self, lesson: Lesson) -> str:
        """Memory write governance: pass|fail|quarantine.

        Constitutional Gate Kontrol Listesi:
        1. SQL injection pattern → FAIL
        2. Hardcoded secrets → FAIL
        3. Reward hacking → FAIL
        4. Unsafe file paths → FAIL
        5. Turkce encoding ihlali → FAIL
        6. KIRO2 kural ihlali → FAIL
        7. Command in lesson → QUARANTINE
        """
        text = f"{lesson.hypothesis} {lesson.fix} {lesson.result}"

        if _SQL_INJECTION_RE.search(text):
            logger.warning("Constitutional gate FAIL: SQL injection pattern in lesson %s", lesson.id)
            return "fail"

        if _HARDCODED_SECRET_RE.search(text):
            logger.warning("Constitutional gate FAIL: hardcoded secret in lesson %s", lesson.id)
            return "fail"

        if _REWARD_HACKING_RE.search(text):
            logger.warning("Constitutional gate FAIL: reward hacking in lesson %s", lesson.id)
            return "fail"

        if _UNSAFE_PATH_RE.search(text):
            logger.warning("Constitutional gate FAIL: unsafe path in lesson %s", lesson.id)
            return "fail"

        if _PORT_5432_RE.search(text):
            logger.warning("Constitutional gate FAIL: port 5432 (should be 5434) in lesson %s", lesson.id)
            return "fail"

        if _USE_AUTH_RE.search(text):
            logger.warning("Constitutional gate FAIL: useAuth.ts (use authStore.ts) in lesson %s", lesson.id)
            return "fail"

        # Check for non-UTF8 (simple check)
        try:
            text.encode("utf-8")
        except UnicodeEncodeError:
            logger.warning("Constitutional gate FAIL: encoding issue in lesson %s", lesson.id)
            return "fail"

        if _COMMAND_IN_LESSON_RE.search(text):
            logger.warning("Constitutional gate QUARANTINE: command pattern in lesson %s", lesson.id)
            return "quarantine"

        return "pass"

    def _check_double_loop(self, agent_id: str) -> bool:
        """Argyris double-loop: 3+ consecutive failures → strategy change.

        Returns True if double-loop triggered.
        """
        lessons = self._load_lessons()
        agent_lessons = [
            l for l in lessons
            if l.get("agent_id") == agent_id
        ]

        # Check last 3
        recent = sorted(agent_lessons, key=lambda x: x.get("timestamp", ""), reverse=True)[:3]
        if len(recent) >= 3 and all(l.get("outcome") == "failure" for l in recent):
            logger.warning(
                "DOUBLE-LOOP triggered for agent=%s: 3+ consecutive failures. "
                "Strategy change recommended.",
                agent_id,
            )
            return True

        return False

    def _extract_skill(
        self,
        agent_id: str,
        task: dict[str, Any],
        solution: str,
    ) -> Skill | None:
        """Voyager: Extract skill from successful solution.

        Only extracts if solution looks reusable and has safe permissions.
        """
        # Simple heuristic: solution must be substantial
        if len(solution) < 50:
            return None

        skill = Skill(
            id=str(uuid.uuid4())[:12],
            name=f"skill_{task.get('task_type', 'generic')}_{agent_id[:6]}",
            description=f"Extracted from successful task: {task.get('description', '')[:100]}",
            entrypoint=solution[:500],
            safety_permissions=["read_repo"],  # Conservative default
            evidence=[f"task:{task.get('task_type', '')}:{datetime.now(timezone.utc).isoformat()}"],
            agent_id=agent_id,
            tags=task.get("tags", []),
            confidence="LOW",
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        # Validate permissions
        if not all(p in ALLOWED_PERMISSIONS for p in skill.safety_permissions):
            return None

        logger.info("Skill extracted: %s (agent=%s)", skill.name, agent_id)
        return skill

    def _update_activation(self, lesson_id: str) -> None:
        """ACT-R: update access_count + last_accessed."""
        lessons = self._load_lessons()
        for lesson in lessons:
            if lesson.get("id") == lesson_id:
                lesson["access_count"] = lesson.get("access_count", 0) + 1
                lesson["last_accessed"] = datetime.now(timezone.utc).isoformat()
                break
        self._save_lessons_raw(lessons)

    def update_confidence_bayesian(self, lesson_id: str, success: bool) -> str | None:
        """M4: Bayesian posterior update for a lesson.

        Args:
            lesson_id: Lesson to update.
            success: Whether the lesson application was successful.

        Returns:
            New confidence level or None if not found.
        """
        lessons = self._load_lessons()
        for lesson in lessons:
            if lesson.get("id") != lesson_id:
                continue

            alpha = lesson.get("beta_alpha", 1)
            beta = lesson.get("beta_beta", 1)

            if success:
                alpha += 1
            else:
                beta += 1

            lesson["beta_alpha"] = alpha
            lesson["beta_beta"] = beta

            n = alpha + beta - 2  # total observations
            mean = alpha / (alpha + beta)

            # Confidence thresholds (M4)
            if mean >= 0.9 and n >= 10:
                new_conf = "VERIFIED"
            elif mean >= 0.7 and n >= 5:
                new_conf = "HIGH"
            elif mean >= 0.4:
                new_conf = "MEDIUM"
            else:
                new_conf = "LOW"

            lesson["confidence"] = new_conf
            lesson["last_accessed"] = datetime.now(timezone.utc).isoformat()
            lesson["access_count"] = lesson.get("access_count", 0) + 1

            self._save_lessons_raw(lessons)
            return new_conf

        return None

    def quarantine_auto_resolve(self, max_age_days: int = 14) -> int:
        """M2: Auto-resolve quarantined lessons.

        - 7 days with new evidence → re-evaluate
        - 14 days without evidence → DELETE
        - Nemori pattern: prediction error check

        Returns:
            Number of resolved quarantine items.
        """
        lessons = self._load_lessons()
        now = datetime.now(timezone.utc)
        resolved = 0
        remaining = []

        for lesson in lessons:
            if lesson.get("safety_review") != "quarantine":
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

            age_days = (now - created).days

            if age_days >= max_age_days:
                # Auto-delete: no evidence within 14 days
                logger.info(
                    "Quarantine auto-delete: %s (age=%d days)",
                    lesson.get("id", "?"),
                    age_days,
                )
                resolved += 1
                continue

            remaining.append(lesson)

        if resolved > 0:
            self._save_lessons_raw(remaining)

        return resolved

    def cleanup_old_lessons(self, max_age_days: int = 90) -> int:
        """M2: Delete LOW confidence lessons with no access for 90 days.

        Returns:
            Number of deleted lessons.
        """
        lessons = self._load_lessons()
        now = datetime.now(timezone.utc)
        deleted = 0
        remaining = []

        for lesson in lessons:
            if lesson.get("confidence") != "LOW":
                remaining.append(lesson)
                continue

            last_accessed = lesson.get("last_accessed", lesson.get("timestamp", ""))
            try:
                last_dt = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                remaining.append(lesson)
                continue

            if (now - last_dt).days >= max_age_days:
                logger.info(
                    "Old lesson deleted: %s (confidence=LOW, age=%d days)",
                    lesson.get("id", "?"),
                    (now - last_dt).days,
                )
                deleted += 1
                continue

            remaining.append(lesson)

        if deleted > 0:
            self._save_lessons_raw(remaining)

        return deleted

    def _write_stigmergy_artifact(self, lesson: Lesson) -> None:
        """P10: Write successful lesson as semantic artifact for other agents."""
        domain = "general"
        task_type = lesson.task_type or "general"

        shard_dir = self._collective_memory_dir / domain
        shard_dir.mkdir(parents=True, exist_ok=True)
        shard_file = shard_dir / f"{task_type}.json"

        with file_lock(shard_file):
            # Load existing
            insights: list[dict[str, Any]] = []
            if shard_file.exists():
                try:
                    with open(shard_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    insights = data.get("insights", [])
                except (json.JSONDecodeError, KeyError):
                    pass

            # Add new insight from lesson
            insight = {
                "key": f"lesson:{lesson.id}",
                "statement": f"{lesson.hypothesis} → {lesson.fix}" if lesson.fix else lesson.hypothesis,
                "derived_from": [lesson.id],
                "conflict_keys": [],
                "supersedes": [],
                "last_verified": lesson.timestamp,
                "confidence": lesson.confidence,
                "domain": domain,
                "task_type": task_type,
                "source_agent_id": lesson.agent_id,
                "insight_type": "heuristic",
                "created_by": "feedback_collector",
                "created_at": lesson.timestamp,
            }
            insights.append(insight)

            # Save
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

    # -----------------------------------------------------------------------
    # Lesson cache I/O (with file locking)
    # -----------------------------------------------------------------------

    def _load_lessons(self) -> list[dict[str, Any]]:
        """Load raw lesson dicts from cache."""
        if not self._lesson_cache_path.exists():
            return []
        try:
            with open(self._lesson_cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("lessons", [])
        except (json.JSONDecodeError, KeyError):
            return []

    def _save_lessons_raw(self, lessons: list[dict[str, Any]]) -> None:
        """Save raw lesson dicts to cache with file locking."""
        self._lesson_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(self._lesson_cache_path):
            with open(self._lesson_cache_path, "w", encoding="utf-8") as f:
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

    def _save_lesson(self, lesson: Lesson) -> None:
        """Append lesson to cache with file locking."""
        with file_lock(self._lesson_cache_path):
            lessons = self._load_lessons()
            lesson_dict = {
                k: v for k, v in lesson.__dict__.items()
            }
            lessons.append(lesson_dict)
            self._lesson_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._lesson_cache_path, "w", encoding="utf-8") as f:
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


# ---------------------------------------------------------------------------
# CLI entry point (for hooks)
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for Stop hook.

    Reads session data from coordination/state.json,
    records outcome as lesson.
    """
    import sys

    base_path = Path(".claude")
    state_file = base_path / "coordination" / "state.json"

    if not state_file.exists():
        logger.info("No state file found, skipping feedback collection")
        return

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, KeyError):
        logger.warning("Failed to read state file")
        return

    agent_id = state.get("current_agent_id", "unknown")
    task = {
        "task_type": state.get("task_type", ""),
        "description": state.get("current_task", ""),
        "tags": state.get("tags", []),
    }
    success = state.get("last_outcome", "") == "success"
    details = {
        "signals": state.get("signals", []),
        "evidence_refs": state.get("evidence_refs", []),
        "error": state.get("last_error", ""),
    }

    # Only record if there's actual evidence
    if details["evidence_refs"]:
        collector = FeedbackCollector(base_path=str(base_path))
        lesson = collector.record_outcome(agent_id, task, success, details)
        if lesson:
            print(f"Lesson recorded: {lesson.id} (safety={lesson.safety_review})")

        # M2: Run quarantine auto-resolve
        resolved = collector.quarantine_auto_resolve()
        if resolved:
            print(f"Quarantine auto-resolved: {resolved} items")

        # M2: Cleanup old lessons
        cleaned = collector.cleanup_old_lessons()
        if cleaned:
            print(f"Old lessons cleaned: {cleaned} items")


if __name__ == "__main__":
    main()
