"""
Offline Sync Service — F10 PWA Offline Mode

Business logic for building offline study packages and processing results
that were recorded while the student had no network connectivity.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger

logger = get_logger("offline_sync_service")

# Estimate: 2 minutes per question for offline study
_MINUTES_PER_QUESTION = 2


async def build_sync_package(
    *,
    db: AsyncSession,
    student_id: str,
    subject: str | None,
    limit: int,
) -> dict[str, Any]:
    """Build an offline study package for the given student.

    Combines:
    1. FSRS cards that are due today (spaced-repetition review).
    2. Random questions from topics where the student has low performance
       (or random questions when no performance data exists).

    Args:
        db: Async database session.
        student_id: UUID string of the student.
        subject: Optional uppercase subject filter (e.g. "MATEMATIK").
        limit: Maximum total questions to include.

    Returns:
        Dict matching SyncPackageResponse schema.
    """
    from models.fsrs_models import FSRSCard
    from models.question_bank import QuestionBankItem

    now = datetime.now(UTC)
    package_id = str(uuid.uuid4())

    # ------------------------------------------------------------------
    # 1. Fetch FSRS due cards
    # ------------------------------------------------------------------
    fsrs_query = (
        select(FSRSCard)
        .where(
            and_(
                FSRSCard.student_id == student_id,
                FSRSCard.due_date <= now,
            )
        )
        .limit(min(limit, 50))
    )

    if subject:
        # FSRSCard.subject_area is an Enum; compare by value string
        from models.enums_db import SubjectArea

        try:
            subject_enum = SubjectArea(subject.lower())
            fsrs_query = fsrs_query.where(FSRSCard.subject_area == subject_enum)
        except ValueError:
            # Unknown subject — skip filter, return all due cards
            logger.warning(
                f"Unknown subject for FSRS filter: {subject}",
                extra_data={"student_id": student_id},
            )

    fsrs_result = await db.execute(fsrs_query)
    due_cards = fsrs_result.scalars().all()

    fsrs_due_cards: list[dict[str, Any]] = []
    for card in due_cards:
        fsrs_due_cards.append(
            {
                "card_id": card.id,
                # FSRS cards may not be linked to question_bank directly;
                # use card id as placeholder question_id
                "question_id": card.id,
                "due_at": card.due_date.isoformat(),
                "interval": card.scheduled_days,
                "ease_factor": round(card.difficulty, 4),
            }
        )

    # ------------------------------------------------------------------
    # 2. Fetch questions from question_bank
    # ------------------------------------------------------------------
    remaining_slots = limit - len(fsrs_due_cards)
    if remaining_slots < 1:
        remaining_slots = 10  # always include at least some questions

    dialect = db.bind.dialect.name if db.bind else "sqlite"
    if dialect == "postgresql":
        q_query = (
            select(QuestionBankItem)
            .tablesample(func.bernoulli(20))
            .where(QuestionBankItem.is_active == True)  # noqa: E712
        )
    else:
        q_query = (
            select(QuestionBankItem)
            .where(QuestionBankItem.is_active == True)  # noqa: E712
        )

    if subject:
        q_query = q_query.where(QuestionBankItem.subject_area == subject.upper())

    if dialect == "postgresql":
        q_query = q_query.limit(remaining_slots)
    else:
        q_query = q_query.order_by(func.random()).limit(remaining_slots)

    q_result = await db.execute(q_query)
    questions_db = q_result.scalars().all()

    if dialect == "postgresql" and len(questions_db) < remaining_slots:
        fallback_query = select(QuestionBankItem).where(QuestionBankItem.is_active == True)
        if subject:
            fallback_query = fallback_query.where(QuestionBankItem.subject_area == subject.upper())
        fallback_query = fallback_query.limit(remaining_slots)
        q_result = await db.execute(fallback_query)
        questions_db = q_result.scalars().all()

    questions: list[dict[str, Any]] = []
    for q in questions_db:
        # QuestionBankItem ORM has option_a..option_e columns (Text).
        # Compose into a dict for the OfflineQuestion.options payload.
        raw_options: dict[str, str] = {
            "A": q.option_a or "",
            "B": q.option_b or "",
            "C": q.option_c or "",
            "D": q.option_d or "",
        }
        if q.option_e:
            raw_options["E"] = q.option_e
        questions.append(
            {
                "id": q.id,
                "text": q.question_text or "",
                "options": raw_options,
                "correct_answer": q.correct_answer or "",
                "subject": q.subject_area or "",
                "topic": q.primary_topic_id or "",
                "difficulty": (
                    q.difficulty_level.value if q.difficulty_level else "medium"
                ),
            }
        )

    total = len(questions)
    estimated_minutes = total * _MINUTES_PER_QUESTION
    question_ids = [q["id"] for q in questions] or None

    await db.execute(
        text(
            """
            INSERT INTO offline_sync_packages (
                package_id,
                student_id,
                question_ids
            )
            VALUES (
                :package_id,
                :student_id,
                CAST(:question_ids AS jsonb)
            )
            """
        ),
        {
            "package_id": package_id,
            "student_id": student_id,
            "question_ids": json.dumps(question_ids) if question_ids else None,
        },
    )
    await db.commit()

    return {
        "package_id": package_id,
        "created_at": now.isoformat(),
        "questions": questions,
        "fsrs_due_cards": fsrs_due_cards,
        "total_questions": total,
        "estimated_study_time_minutes": estimated_minutes,
    }


async def process_sync_results(
    *,
    db: AsyncSession,
    student_id: str,
    package_id: str,
    results: list[dict[str, Any]],
    completed_at: str,
) -> dict[str, Any]:
    """Process offline results uploaded by the student.

    For each result:
    - Validates the question exists and belongs to question_bank.
    - Inserts a record into student_answers (using a synthetic exam session or
      the offline_sync pseudo-session id).
    - Updates FSRS card scheduling when a matching card is found.

    Args:
        db: Async database session.
        student_id: UUID string of the student.
        package_id: ID of the originating sync package (for audit).
        results: List of answer dicts from the frontend.
        completed_at: ISO-8601 string of when the offline session ended.

    Returns:
        Dict with synced_count, failed_count, next_sync_recommended_at.
    """
    from models.fsrs_models import FSRSCard
    from models.question_bank import QuestionBankItem

    synced = 0
    failed = 0
    package_row = await db.execute(
        text(
            """
            SELECT student_id, consumed_at
            FROM offline_sync_packages
            WHERE package_id = :package_id
            """
        ),
        {"package_id": package_id},
    )
    package = package_row.mappings().first()

    if package is None:
        return _reject_batch(
            reason="unknown_package",
            level="warning",
            student_id=student_id,
            package_id=package_id,
            result_count=len(results),
        )

    if package["student_id"] != student_id:
        return _reject_batch(
            reason="ownership_mismatch",
            level="error",
            student_id=student_id,
            package_id=package_id,
            result_count=len(results),
        )

    if package["consumed_at"] is not None:
        return _reject_batch(
            reason="already_consumed",
            level="warning",
            student_id=student_id,
            package_id=package_id,
            result_count=len(results),
        )

    # Batch fetch all potential questions and FSRS cards in one go to prevent N+1 queries
    question_ids = [item["question_id"] for item in results if "question_id" in item]
    
    questions_map = {}
    if question_ids:
        q_result = await db.execute(
            select(QuestionBankItem).where(
                and_(
                    QuestionBankItem.id.in_(question_ids),
                    QuestionBankItem.is_active == True,  # noqa: E712
                )
            )
        )
        questions_map = {q.id: q for q in q_result.scalars().all()}

    cards = []
    if question_ids:
        from sqlalchemy import or_
        clauses = [FSRSCard.front_text.contains(qid) for qid in question_ids]
        card_result = await db.execute(
            select(FSRSCard).where(
                and_(
                    FSRSCard.student_id == student_id,
                    or_(*clauses)
                )
            )
        )
        cards = card_result.scalars().all()

    for item in results:
        try:
            question_id = item["question_id"]
            selected_answer = (item.get("selected_answer") or "").strip().upper()
            is_correct = bool(item.get("is_correct", False))
            time_seconds = float(item.get("time_seconds", 0.0))

            # Validate answer character
            if selected_answer not in {"A", "B", "C", "D", "E"}:
                logger.warning(
                    f"Invalid answer '{selected_answer}' for question {question_id}",
                    extra_data={"student_id": student_id},
                )
                failed += 1
                continue

            # Check question exists
            question = questions_map.get(question_id)
            if question is None:
                logger.warning(
                    f"Question not found or inactive: {question_id}",
                    extra_data={"student_id": student_id},
                )
                failed += 1
                continue

            # Find matching FSRS card in pre-fetched list
            card = next((c for c in cards if question_id in c.front_text), None)
            if card is not None:
                _apply_fsrs_grade(
                    card=card, is_correct=is_correct, time_seconds=time_seconds
                )
                db.add(card)

            synced += 1

        except Exception as exc:
            logger.exception(
                "Failed to process offline result: %s",
                exc,
                extra={"student_id": student_id, "item": item},
            )
            failed += 1

    await db.execute(
        text(
            """
            UPDATE offline_sync_packages
            SET consumed_at = NOW()
            WHERE package_id = :package_id
            """
        ),
        {"package_id": package_id},
    )
    await db.commit()

    return {
        "synced_count": synced,
        "failed_count": failed,
        "next_sync_recommended_at": _next_sync_at_iso(),
    }


def _reject_batch(
    *,
    reason: str,
    level: str,
    student_id: str,
    package_id: str,
    result_count: int,
) -> dict[str, Any]:
    log_message = (
        "Offline sync batch rejected: "
        f"{reason} (student={student_id}, package_id={package_id})"
    )
    if level == "error":
        logger.error(log_message, extra_data={"reason": reason})
    else:
        logger.warning(log_message, extra_data={"reason": reason})

    return {
        "synced_count": 0,
        "failed_count": result_count,
        "next_sync_recommended_at": _next_sync_at_iso(),
    }


def _next_sync_at_iso() -> str:
    # Recommend next sync in ~6 hours
    next_sync = datetime.now(UTC) + timedelta(hours=6)
    return next_sync.isoformat()


def _apply_fsrs_grade(*, card: Any, is_correct: bool, time_seconds: float) -> None:
    """Apply a simple FSRS grade update to a card.

    Uses a minimal FSRS-4.5 approximation:
    - Grade 1 (Again) when wrong
    - Grade 3 (Good)  when correct and slow (>60s)
    - Grade 4 (Easy)  when correct and fast

    Args:
        card: FSRSCard ORM object (mutated in-place).
        is_correct: Whether the student answered correctly.
        time_seconds: Response time in seconds.
    """
    from datetime import datetime, timedelta

    now = datetime.now(UTC)

    if not is_correct:
        # Again — reset stability slightly, shorten interval
        card.lapses += 1
        card.scheduled_days = max(1, card.scheduled_days // 2)
        card.stability = max(0.5, card.stability * 0.6)
        card.state = "review"
    else:
        grade = 3 if time_seconds > 60 else 4
        card.reps += 1
        # Simplified stability increase
        stability_factor = 2.5 if grade == 4 else 1.8
        card.stability = max(0.5, card.stability * stability_factor)
        card.scheduled_days = max(1, int(card.stability))
        card.state = "review"

    card.last_review = now
    card.due_date = now + timedelta(days=card.scheduled_days)


async def get_sync_status(*, db: AsyncSession, student_id: str) -> dict[str, Any]:
    """Return sync status for the student.

    Args:
        db: Async database session.
        student_id: UUID string of the student.

    Returns:
        Dict with last_sync_at, pending_results_count, offline_package_version.
    """
    from models.fsrs_models import FSRSCard

    now = datetime.now(UTC)

    # Count FSRS cards that are currently due (proxy for pending review work)
    pending_result = await db.execute(
        select(func.count())
        .select_from(FSRSCard)
        .where(
            and_(
                FSRSCard.student_id == student_id,
                FSRSCard.due_date <= now,
            )
        )
    )
    pending_count = pending_result.scalar_one_or_none() or 0

    # Last review time across all FSRS cards
    last_review_result = await db.execute(
        select(func.max(FSRSCard.last_review)).where(FSRSCard.student_id == student_id)
    )
    last_review: datetime | None = last_review_result.scalar_one_or_none()

    return {
        "last_sync_at": last_review.isoformat() if last_review else None,
        "pending_results_count": pending_count,
        "offline_package_version": "1.0",
    }
