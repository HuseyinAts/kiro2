"""
LearningPathFacade — optional PostgreSQL persistence.

Loads/saves domain `LearningPath` and `StudentProfile` via
`database.learning_path_repository.LearningPathRepository`.
Full round-trip uses `agent_metadata.facade_domain_path` JSON (from `LearningPath.to_dict()`).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from core.database import get_db_session_context
from database.learning_path_repository import LearningPathRepository

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _domain_path_to_row(
    path: Any, subject: str, extra_metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Map domain LearningPath + subject to `learning_paths` insert dict."""
    now = datetime.now(UTC).replace(tzinfo=None)
    created = path.created_at
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "")).replace(tzinfo=None)
    elif isinstance(created, datetime):
        created = created.replace(tzinfo=None)
    else:
        created = now

    phases_payload = [p.to_dict() for p in path.phases]
    resources_payload = [r.to_dict() for r in path.resources]
    meta: dict[str, Any] = {
        "facade_domain_path": path.to_dict(),
        **(extra_metadata or {}),
        **(path.metadata or {}),
    }

    total_topics = int(
        path.metadata.get("total_topics")
        or sum(len(p.resources) for p in path.phases)
        or len(path.resources)
        or 0
    )

    return {
        "path_id": path.path_id,
        "student_id": path.student_id,
        "subject": subject,
        "difficulty_level": (path.metadata or {}).get("difficulty_level", "intermediate"),
        "duration_weeks": int((path.metadata or {}).get("duration_weeks", 12)),
        "target_date": (path.metadata or {}).get("target_date"),
        "modules": (path.metadata or {}).get("modules", []),
        "phases": phases_payload,
        "resources": resources_payload,
        "ai_generated": True,
        "reasoning": path.reasoning or "",
        "agent_metadata": meta,
        "total_modules": max(1, len(path.phases)),
        "completed_modules": int((path.metadata or {}).get("completed_modules", 0)),
        "total_topics": total_topics,
        "completed_topics": int((path.metadata or {}).get("completed_topics", 0)),
        "overall_progress": float((path.metadata or {}).get("overall_progress", 0.0)),
        "total_time": int((path.metadata or {}).get("total_time", 0)),
        "created_at": created,
        "updated_at": now,
    }


async def _ensure_lp_student_profile(
    session: Any, student_id: str, domain_profile: Any | None
) -> None:
    """Ensure `learning_path_student_profiles` row exists (FK for learning_paths)."""
    repo = LearningPathRepository()
    existing = await repo.get_student_profile(session, student_id)
    if existing:
        return
    if domain_profile is not None:
        goals = [domain_profile.learning_goal] if domain_profile.learning_goal else []
        data = {
            "student_id": student_id,
            "name": domain_profile.name or "Öğrenci",
            "grade": domain_profile.grade or "12",
            "exam_target": domain_profile.exam_target or "YKS",
            "learning_style": domain_profile.learning_style.value,
            "knowledge_level": domain_profile.knowledge_level.value,
            "interests": list(domain_profile.interests or []),
            "goals": goals or ["YKS"],
            "available_time": int(domain_profile.available_time or 240),
            "metadata_json": {
                "learning_goal": domain_profile.learning_goal,
                **(domain_profile.metadata or {}),
            },
        }
    else:
        data = {
            "student_id": student_id,
            "name": "Öğrenci",
            "grade": "12",
            "exam_target": "YKS",
            "learning_style": "mixed",
            "knowledge_level": "intermediate",
            "interests": [],
            "goals": ["YKS"],
            "available_time": 240,
            "metadata_json": {},
        }
    try:
        await repo.create_student_profile(session, data)
    except (ValueError, Exception) as e:
        # Duplicate or schema drift — do not break path save
        logger.warning("learning_path_student_profiles create skipped: %s", e)


async def load_student_path_from_db(
    student_id: str,
) -> Any | None:
    from agents.learning_path.models import LearningPath

    try:
        async with get_db_session_context() as session:
            repo = LearningPathRepository()
            rows = await repo.get_student_learning_paths(
                session, student_id, subject=None
            )
            if not rows:
                return None
            row = rows[0]
            meta: dict = row.agent_metadata or {}
            raw = meta.get("facade_domain_path")
            if raw:
                return LearningPath.from_dict(raw)
    except Exception as e:
        logger.warning("load_student_path_from_db: %s", e)
    return None


async def load_student_profile_from_db(student_id: str) -> Any | None:
    from agents.learning_path.models import (
        KnowledgeLevel,
        LearningStyle,
        StudentProfile,
    )

    try:
        async with get_db_session_context() as session:
            repo = LearningPathRepository()
            row = await repo.get_student_profile(session, student_id)
            if not row:
                return None

            def _ls(s: str) -> Any:
                try:
                    return LearningStyle(s)
                except ValueError:
                    return LearningStyle.MIXED

            def _kl(s: str) -> Any:
                try:
                    return KnowledgeLevel(s)
                except ValueError:
                    return KnowledgeLevel.INTERMEDIATE

            md: dict = row.metadata_json or {}
            return StudentProfile(
                student_id=row.student_id,
                name=row.name or "",
                grade=row.grade or "12",
                exam_target=row.exam_target or "YKS-TYT",
                learning_goal=md.get("learning_goal", "") or "",
                learning_style=_ls(row.learning_style or "mixed"),
                knowledge_level=_kl(row.knowledge_level or "intermediate"),
                interests=list(row.interests or []),
                available_time=int(row.available_time or 240),
                metadata=md,
            )
    except Exception as e:
        logger.warning("load_student_profile_from_db: %s", e)
    return None


async def persist_student_path(
    path: Any,
    subject: str,
    domain_profile: Any | None = None,
) -> None:
    """Write domain LearningPath to `learning_paths` (best-effort)."""
    try:
        from agents.learning_path.models import LearningPath

        if not isinstance(path, LearningPath):
            return
        row = _domain_path_to_row(path, subject)
        async with get_db_session_context() as session:
            await _ensure_lp_student_profile(session, path.student_id, domain_profile)
            repo = LearningPathRepository()
            await repo.create_learning_path(session, row)
    except Exception as e:
        logger.warning("persist_student_path: %s", e)
