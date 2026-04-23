"""
DINA Service — F11 Cognitive Diagnostic Model
Deterministic Input, Noisy "And" gate for nano-skill mastery estimation.

P(correct | all required skills mastered) = 1 - slip
P(correct | missing any required skill) = guess
"""

from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger
from models.dina import DINAParameter, NanoSkill, QMatrix, StudentNanoSkillMastery

logger = get_logger("dina_service")


# ---------------------------------------------------------------------------
# Core DINA probability
# ---------------------------------------------------------------------------

def calculate_dina_probability(
    *,
    slip: float,
    guess: float,
    all_skills_mastered: bool,
) -> float:
    """Calculate P(correct) under the DINA model.

    P(X=1 | eta=1) = 1 - slip   (knows all required skills)
    P(X=1 | eta=0) = guess      (missing at least one skill)

    Args:
        slip: P(incorrect | all skills mastered). Typically 0.05-0.20.
        guess: P(correct | missing skills). Typically 0.10-0.25.
        all_skills_mastered: Whether student has all required skills.

    Returns:
        Probability of correct response (0.0 to 1.0).
    """
    if all_skills_mastered:
        return 1.0 - slip
    return guess


def calculate_dina_probability_continuous(
    *,
    slip: float,
    guess: float,
    skill_masteries: list[float],
) -> float:
    """Continuous DINA: uses mastery probabilities instead of binary.

    eta = product of all skill masteries (conjunctive model).
    P(correct) = (1-slip)^eta * guess^(1-eta)
    """
    if not skill_masteries:
        return guess

    # eta = product of mastery probabilities (all skills needed)
    eta = 1.0
    for m in skill_masteries:
        eta *= max(0.0, min(1.0, m))

    # Continuous interpolation
    return ((1.0 - slip) ** eta) * (guess ** (1.0 - eta))


# ---------------------------------------------------------------------------
# Mastery estimation (posterior update)
# ---------------------------------------------------------------------------

def update_mastery_posterior(
    *,
    prior_mastery: float,
    slip: float,
    guess: float,
    is_correct: bool,
) -> float:
    """Bayesian update of a single skill mastery given one observation.

    Uses Bayes' rule:
        P(mastered | correct) = P(correct | mastered) * P(mastered) / P(correct)
        P(mastered | incorrect) = P(incorrect | mastered) * P(mastered) / P(incorrect)
    """
    p_correct_mastered = 1.0 - slip
    p_correct_not_mastered = guess

    if is_correct:
        likelihood_mastered = p_correct_mastered
        likelihood_not = p_correct_not_mastered
    else:
        likelihood_mastered = slip
        likelihood_not = 1.0 - guess

    numerator = likelihood_mastered * prior_mastery
    denominator = numerator + likelihood_not * (1.0 - prior_mastery)

    if denominator < 1e-10:
        return prior_mastery

    return numerator / denominator


# ---------------------------------------------------------------------------
# EM calibration (slip/guess estimation)
# ---------------------------------------------------------------------------

def em_step(
    *,
    responses: list[dict],
    skill_masteries: dict[str, dict[str, float]],
    q_matrix: dict[str, list[str]],
    current_slip: dict[str, float],
    current_guess: dict[str, float],
) -> tuple[dict[str, float], dict[str, float]]:
    """One EM iteration for slip/guess parameter estimation.

    Args:
        responses: [{student_id, question_id, is_correct}]
        skill_masteries: {student_id: {skill_id: mastery}}
        q_matrix: {question_id: [required_skill_ids]}
        current_slip: {question_id: slip}
        current_guess: {question_id: guess}

    Returns:
        (new_slip, new_guess) dicts.
    """
    new_slip: dict[str, float] = {}
    new_guess: dict[str, float] = {}

    # Group responses by question
    question_responses: dict[str, list[dict]] = {}
    for r in responses:
        qid = r["question_id"]
        if qid not in question_responses:
            question_responses[qid] = []
        question_responses[qid].append(r)

    for qid, resps in question_responses.items():
        required_skills = q_matrix.get(qid, [])
        if not required_skills:
            new_slip[qid] = current_slip.get(qid, 0.1)
            new_guess[qid] = current_guess.get(qid, 0.2)
            continue

        # E-step: compute expected eta for each student
        slip_num = 0.0
        slip_den = 0.0
        guess_num = 0.0
        guess_den = 0.0

        for r in resps:
            sid = r["student_id"]
            student_skills = skill_masteries.get(sid, {})

            # Compute eta (probability all required skills are mastered)
            eta = 1.0
            for skill_id in required_skills:
                eta *= student_skills.get(skill_id, 0.5)

            is_correct = r["is_correct"]

            # Accumulate for M-step
            if is_correct:
                slip_num += eta * current_slip.get(qid, 0.1)
                # P(eta=1|correct) contribution to slip denominator
                slip_den += eta
            else:
                slip_num += eta * (1.0 - current_slip.get(qid, 0.1))
                slip_den += eta

            if is_correct:
                guess_num += (1.0 - eta) * current_guess.get(qid, 0.2)
                guess_den += (1.0 - eta)
            else:
                guess_den += (1.0 - eta)

        # M-step: update parameters
        new_slip[qid] = (slip_num / max(slip_den, 1e-10))
        new_guess[qid] = (guess_num / max(guess_den, 1e-10))

        # Clamp to valid ranges
        new_slip[qid] = max(0.01, min(0.40, new_slip[qid]))
        new_guess[qid] = max(0.01, min(0.40, new_guess[qid]))

    return new_slip, new_guess


def calibrate_parameters(
    *,
    responses: list[dict],
    skill_masteries: dict[str, dict[str, float]],
    q_matrix: dict[str, list[str]],
    max_iterations: int = 20,
    convergence_threshold: float = 0.001,
) -> tuple[dict[str, float], dict[str, float]]:
    """Run EM algorithm until convergence.

    Returns:
        (slip_params, guess_params) dicts keyed by question_id.
    """
    # Initialize
    question_ids = set(r["question_id"] for r in responses)
    slip = dict.fromkeys(question_ids, 0.1)
    guess = dict.fromkeys(question_ids, 0.2)

    for iteration in range(max_iterations):
        new_slip, new_guess = em_step(
            responses=responses,
            skill_masteries=skill_masteries,
            q_matrix=q_matrix,
            current_slip=slip,
            current_guess=guess,
        )

        # Check convergence
        max_change = 0.0
        for qid in question_ids:
            max_change = max(
                max_change,
                abs(new_slip.get(qid, 0.1) - slip.get(qid, 0.1)),
                abs(new_guess.get(qid, 0.2) - guess.get(qid, 0.2)),
            )

        slip = new_slip
        guess = new_guess

        if max_change < convergence_threshold:
            logger.info(
                f"DINA EM converged after {iteration + 1} iterations",
                extra_data={"max_change": max_change},
            )
            break

    return slip, guess


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------

async def estimate_student_mastery(
    *,
    db: AsyncSession,
    student_id: str,
    question_id: str,
    is_correct: bool,
) -> list[dict]:
    """Update nano-skill mastery for a student based on one response.

    Returns updated mastery states for affected skills.
    """
    # Get Q-matrix entries for this question
    q_result = await db.execute(
        select(QMatrix).where(
            QMatrix.question_id == question_id,
            QMatrix.is_required == True,  # noqa: E712
        )
    )
    q_entries = q_result.scalars().all()

    if not q_entries:
        return []

    # Get DINA parameters
    param_result = await db.execute(
        select(DINAParameter).where(DINAParameter.question_id == question_id)
    )
    params = param_result.scalar_one_or_none()
    slip = params.slip if params else 0.1
    guess = params.guess if params else 0.2

    updated = []
    for q_entry in q_entries:
        # Get or create mastery record
        mastery_result = await db.execute(
            select(StudentNanoSkillMastery).where(
                StudentNanoSkillMastery.student_id == student_id,
                StudentNanoSkillMastery.nano_skill_id == q_entry.nano_skill_id,
            )
        )
        mastery = mastery_result.scalar_one_or_none()

        if not mastery:
            mastery = StudentNanoSkillMastery(
                student_id=student_id,
                nano_skill_id=q_entry.nano_skill_id,
                mastery=0.5,
            )
            db.add(mastery)
            await db.flush()

        # Bayesian update
        new_mastery = update_mastery_posterior(
            prior_mastery=mastery.mastery,
            slip=slip,
            guess=guess,
            is_correct=is_correct,
        )
        mastery.mastery = new_mastery
        mastery.response_count += 1
        mastery.confidence = 1.0 - (1.0 / math.sqrt(mastery.response_count + 1))

        await db.flush()

        updated.append({
            "nano_skill_id": q_entry.nano_skill_id,
            "mastery": round(new_mastery, 4),
            "confidence": round(mastery.confidence, 4),
            "response_count": mastery.response_count,
        })

    return updated


async def get_student_skill_profile(
    *,
    db: AsyncSession,
    student_id: str,
    subject: str | None = None,
) -> list[dict]:
    """Get all nano-skill mastery states for a student."""
    query = (
        select(StudentNanoSkillMastery, NanoSkill)
        .join(NanoSkill, StudentNanoSkillMastery.nano_skill_id == NanoSkill.id)
        .where(StudentNanoSkillMastery.student_id == student_id)
    )

    if subject:
        query = query.where(NanoSkill.subject == subject.upper())

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "nano_skill_id": mastery.nano_skill_id,
            "skill_name": skill.name,
            "subject": skill.subject,
            "mastery": round(mastery.mastery, 4),
            "confidence": round(mastery.confidence, 4),
            "response_count": mastery.response_count,
            "knowledge_point_id": skill.knowledge_point_id,
        }
        for mastery, skill in rows
    ]
