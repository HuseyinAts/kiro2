"""
Mastery Confidence Service — F13

IRT-based confidence intervals and mastery confidence levels.
Reads student response history and computes ability estimates with
95% confidence intervals using the test information function.
"""

from __future__ import annotations

import math
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger

logger = get_logger("mastery_confidence_service")

# ---------------------------------------------------------------------------
# IRT helpers
# ---------------------------------------------------------------------------

# Prior: N(0, 1) — standard normal
_PRIOR_MEAN = 0.0
_PRIOR_VAR = 1.0

# Default difficulty when unknown
_DEFAULT_DIFFICULTY = 0.0


def _irt_probability(theta: float, difficulty: float) -> float:
    """1PL IRT probability of correct response."""
    exponent = theta - difficulty
    # Clamp to prevent overflow
    exponent = max(-10.0, min(10.0, exponent))
    return 1.0 / (1.0 + math.exp(-exponent))


def _mle_ability(
    responses: list[dict[str, Any]],
) -> tuple[float, float, float]:
    """Maximum Likelihood Estimation of ability (theta).

    Uses Newton-Raphson with Bayesian prior for stability.

    Returns:
        (theta, ci_low, ci_high) — ability estimate and 95% CI bounds.
    """
    if not responses:
        # No data — return prior with wide CI
        return _PRIOR_MEAN, _PRIOR_MEAN - 1.96, _PRIOR_MEAN + 1.96

    theta = _PRIOR_MEAN
    max_iter = 25

    for _ in range(max_iter):
        info = 1.0 / _PRIOR_VAR  # Prior information
        score = -(theta - _PRIOR_MEAN) / _PRIOR_VAR  # Prior score

        for r in responses:
            diff = r.get("difficulty", _DEFAULT_DIFFICULTY)
            p = _irt_probability(theta, diff)
            is_correct = 1.0 if r["is_correct"] else 0.0

            score += is_correct - p
            info += p * (1.0 - p)

        if info <= 0:
            break

        delta = score / info
        theta += delta

        if abs(delta) < 1e-5:
            break

    # Clamp theta to [-4, 4]
    theta = max(-4.0, min(4.0, theta))

    # Standard error from Fisher information
    se = 1.0 / math.sqrt(max(info, 0.01))

    ci_low = max(-4.0, theta - 1.96 * se)
    ci_high = min(4.0, theta + 1.96 * se)

    return theta, ci_low, ci_high


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_subject_confidence(
    *,
    db: AsyncSession,
    student_id: str,
    subject: str,
) -> dict[str, Any]:
    """Compute IRT ability estimate and 95% CI for a subject.

    Args:
        db: Async database session.
        student_id: Student identifier.
        subject: Subject code (e.g. 'matematik').

    Returns:
        {ability, ci_low, ci_high, response_count}
    """
    responses = await _fetch_responses(db, student_id, subject)
    theta, ci_low, ci_high = _mle_ability(responses)

    return {
        "ability": theta,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "response_count": len(responses),
    }


async def get_topics_confidence(
    *,
    db: AsyncSession,
    student_id: str,
    subject: str,
) -> list[dict[str, Any]]:
    """Compute per-topic mastery and confidence for a subject.

    Groups student responses by topic, computes ability per topic,
    and derives mastery (sigmoid of theta) and CI for each.

    Args:
        db: Async database session.
        student_id: Student identifier.
        subject: Subject code.

    Returns:
        [{topic_id, name, mastery, ci_low, ci_high, response_count}]
    """
    responses = await _fetch_responses(db, student_id, subject, group_by_topic=True)

    # Group by topic
    topic_map: dict[str, list[dict]] = {}
    topic_names: dict[str, str] = {}
    for r in responses:
        tid = r.get("topic_id", "unknown")
        topic_map.setdefault(tid, []).append(r)
        if "topic_name" in r:
            topic_names[tid] = r["topic_name"]

    results = []
    for tid, topic_responses in topic_map.items():
        theta, ci_low, ci_high = _mle_ability(topic_responses)
        # Convert theta to [0, 1] mastery via sigmoid
        mastery = _irt_probability(theta, 0.0)

        results.append(
            {
                "topic_id": tid,
                "name": topic_names.get(tid, tid),
                "mastery": mastery,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "response_count": len(topic_responses),
            }
        )

    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _fetch_responses(
    db: AsyncSession,
    student_id: str,
    subject: str,
    *,
    group_by_topic: bool = False,
) -> list[dict[str, Any]]:
    """Fetch student response history from student_answers + question_bank.

    Returns list of {is_correct, difficulty, topic_id?, topic_name?}.
    """
    try:
        # Read graded answers from student_answers (the table save-answer writes
        # to). The old query targeted a phantom `exam_responses` table (no model,
        # never created) and silently returned empty for every student. The real
        # answers live in student_answers; student_id is reached via exam_sessions.
        from sqlalchemy import text

        query = text("""
            SELECT
                sa.is_correct,
                qb.difficulty_level,
                qb.primary_topic_id,
                qb.subject_area
            FROM student_answers sa
            JOIN exam_sessions es ON sa.exam_session_id = es.id
            JOIN question_bank qb ON sa.question_id = CAST(qb.id AS TEXT)
            WHERE es.student_id = :student_id
              AND qb.subject_area = :subject
              AND sa.is_correct IS NOT NULL
            ORDER BY sa.answered_at DESC
            LIMIT 500
        """)

        result = await db.execute(
            query,
            {"student_id": student_id, "subject": subject.upper()},
        )
        rows = result.fetchall()

        responses = []
        for row in rows:
            difficulty = _DEFAULT_DIFFICULTY
            if row[1] is not None:
                # Try to parse difficulty_level as float
                try:
                    difficulty = float(row[1])
                except (ValueError, TypeError):
                    # Map categorical difficulty to numeric
                    diff_map = {
                        "COK_KOLAY": -2.0,
                        "KOLAY": -1.0,
                        "ORTA": 0.0,
                        "ZOR": 1.0,
                        "COK_ZOR": 2.0,
                    }
                    difficulty = diff_map.get(str(row[1]).upper(), 0.0)

            entry: dict[str, Any] = {
                "is_correct": bool(row[0]),
                "difficulty": difficulty,
            }
            if group_by_topic:
                entry["topic_id"] = str(row[2]) if row[2] else "general"
                entry["topic_name"] = str(row[2]) if row[2] else subject.capitalize()

            responses.append(entry)

        return responses

    except Exception as exc:
        logger.warning(
            "Response fetch failed, returning empty",
            extra_data={
                "student_id": student_id,
                "subject": subject,
                "error": str(exc),
            },
        )
        return []
