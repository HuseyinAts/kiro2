"""
Productive Failure Service — F9
Pretest before instruction: student attempts questions on upcoming topic
BEFORE learning, then learns, then takes post-test to measure growth.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger
from models.question_bank import QuestionBankItem

logger = get_logger("productive_failure_service")

# Topic prefix to subject mapping (e.g., "MAT.GEO.1" -> "MAT" -> "MATEMATIK")
_TOPIC_PREFIX_MAP = {
    "MAT": "MATEMATIK",
    "FIZ": "FIZIK",
    "KIM": "KIMYA",
    "BIO": "BIYOLOJI",
    "TUR": "TURKCE",
    "TAR": "TARIH",
    "COG": "COGRAFYA",
    "GEO": "GEOMETRI",
    "EDE": "EDEBIYAT",
    "FEL": "FELSEFE",
}


async def get_pretest_questions(
    *,
    db: AsyncSession,
    topic_id: str,
    subject: Optional[str] = None,
    count: int = 3,
) -> list[dict]:
    """Select pretest questions for an upcoming topic.

    Picks medium-difficulty questions so the student gets a fair
    preview of what they'll learn, even if they fail.

    Args:
        db: Database session
        topic_id: Primary topic ID (e.g., "MAT.GEO.1")
        subject: Subject area (e.g., "MATEMATIK"). If None, uses topic_id prefix.
        count: Number of questions to return
    """
    # Extract subject from topic_id if not provided (e.g., "MAT.GEO.1" -> "MATEMATIK")
    if not subject and topic_id:
        # Try to extract subject from topic_id prefix (e.g., "MAT.GEO.1" -> "MAT")
        topic_prefix = topic_id.split(".")[0] if "." in topic_id else topic_id[:3]
        subject = _TOPIC_PREFIX_MAP.get(topic_prefix.upper(), "MATEMATIK")  # fallback

    subject_upper = subject.upper() if subject else "MATEMATIK"

    result = await db.execute(
        select(
            QuestionBankItem.id,
            QuestionBankItem.question_text,
            QuestionBankItem.option_a,
            QuestionBankItem.option_b,
            QuestionBankItem.option_c,
            QuestionBankItem.option_d,
            QuestionBankItem.option_e,
            QuestionBankItem.correct_answer,
            QuestionBankItem.difficulty_level,
        )
        .where(
            QuestionBankItem.is_active == True,  # noqa: E712
            QuestionBankItem.subject_area == subject_upper,
            QuestionBankItem.primary_topic_id == topic_id,
        )
        .order_by(func.random())
        .limit(count)
    )
    rows = result.all()

    return [
        {
            "question_id": str(r.id),
            "question_text": r.question_text,
            "options": {
                "A": r.option_a,
                "B": r.option_b,
                "C": r.option_c,
                "D": r.option_d,
                "E": r.option_e,
            },
            "correct_answer": r.correct_answer,
            "difficulty": r.difficulty_level,
        }
        for r in rows
    ]


def calculate_growth(
    *,
    pretest_results: list[dict],
    posttest_results: list[dict],
) -> dict:
    """Calculate learning growth from pretest to posttest.

    Args:
        pretest_results: [{question_id, is_correct, answer}]
        posttest_results: [{question_id, is_correct, answer}]

    Returns:
        Growth metrics including accuracy change and learning gain.
    """
    pre_correct = sum(1 for r in pretest_results if r.get("is_correct"))
    post_correct = sum(1 for r in posttest_results if r.get("is_correct"))
    pre_total = max(len(pretest_results), 1)
    post_total = max(len(posttest_results), 1)

    pre_accuracy = pre_correct / pre_total
    post_accuracy = post_correct / post_total

    # Normalized learning gain (Hake, 1998)
    # g = (post - pre) / (1 - pre)
    if pre_accuracy >= 1.0:
        normalized_gain = 0.0
    else:
        normalized_gain = (post_accuracy - pre_accuracy) / (1.0 - pre_accuracy)

    return {
        "pretest_accuracy": round(pre_accuracy, 3),
        "posttest_accuracy": round(post_accuracy, 3),
        "accuracy_change": round(post_accuracy - pre_accuracy, 3),
        "normalized_gain": round(max(0.0, normalized_gain), 3),
        "pretest_correct": pre_correct,
        "pretest_total": pre_total,
        "posttest_correct": post_correct,
        "posttest_total": post_total,
        "productive_failure_effective": post_accuracy > pre_accuracy,
    }


async def record_pretest_result(
    *,
    db: AsyncSession,
    student_id: str,
    topic_id: str,
    results: list[dict],
) -> dict:
    """Store pretest results for later comparison.

    Results are stored as JSON in the learning path progress.
    This is a lightweight approach — no new table needed.
    """
    from models.learning_path_models import LearningPathProgress

    # Find the progress record for this topic
    progress_result = await db.execute(
        select(LearningPathProgress).where(
            LearningPathProgress.student_id == student_id,
            LearningPathProgress.node_id == topic_id,
        )
    )
    progress = progress_result.scalar_one_or_none()

    if not progress:
        logger.warning(
            f"No progress record for student {student_id}, topic {topic_id}"
        )
        return {"stored": False, "reason": "no_progress_record"}

    # Store pretest data in the metadata/extra JSON field
    correct = sum(1 for r in results if r.get("is_correct"))
    total = len(results)

    # Use existing JSON column or add pretest data
    existing_meta = progress.metadata_ if hasattr(progress, "metadata_") else {}
    if not isinstance(existing_meta, dict):
        existing_meta = {}

    existing_meta["pretest"] = {
        "results": results,
        "correct": correct,
        "total": total,
        "accuracy": round(correct / max(total, 1), 3),
    }

    if hasattr(progress, "metadata_"):
        progress.metadata_ = existing_meta

    await db.flush()

    return {
        "stored": True,
        "pretest_accuracy": round(correct / max(total, 1), 3),
        "correct": correct,
        "total": total,
    }
