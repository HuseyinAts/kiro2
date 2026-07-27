"""
Placement Assessment Service — F5 Neural Network Placement
16-question adaptive Bayesian assessment using IRT infrastructure.

Flow:
1. Start assessment → initialize prior (N(0,1))
2. Select next question → Maximum Fisher Information
3. Student answers → Update posterior (EAP)
4. Repeat until 16 questions or SE < 0.35
5. Return knowledge state map (per-subject mastery)

Uses existing:
- algorithms/irt_model.py: FourParameterIRTModel, IRTItem, IRTResponse
- question_bank: 77K+ calibrated questions with IRT params
"""

import math
import uuid
from datetime import UTC, datetime
from typing import Any

import numpy as np
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from algorithms.irt_model import FourParameterIRTModel, IRTItem, IRTResponse
from core.structured_logger import get_logger

logger = get_logger("placement_assessment")

# Assessment configuration
MAX_QUESTIONS = 16
SE_CONVERGENCE = 0.35  # Stop early if SE drops below this
THETA_GRID = np.linspace(-4.0, 4.0, 81)  # EAP quadrature grid
PRIOR_MEAN = 0.0
PRIOR_SD = 1.0

# Subject-to-topic mapping for knowledge state
SUBJECT_AREAS = [
    "MATEMATIK",
    "FIZIK",
    "KIMYA",
    "BIYOLOJI",
    "TURKCE",
    "TARIH",
    "COGRAFYA",
    "GEOMETRI",
]


def _normal_pdf(x: float, mu: float, sigma: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))


class PlacementAssessment:
    """State for an in-progress placement assessment."""

    def __init__(self, student_id: str, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.student_id = student_id
        self.model = FourParameterIRTModel()

        # Bayesian state
        self.theta_estimate = PRIOR_MEAN
        self.theta_se = PRIOR_SD
        self.prior_mean = PRIOR_MEAN
        self.prior_sd = PRIOR_SD

        # Tracking
        self.responses: list[IRTResponse] = []
        self.answered_item_ids: list[str] = []
        self.items_pool: list[IRTItem] = []
        self.started_at = datetime.now(UTC)

    @property
    def question_count(self) -> int:
        return len(self.responses)

    @property
    def is_complete(self) -> bool:
        if self.question_count >= MAX_QUESTIONS:
            return True
        if self.question_count >= 8 and self.theta_se < SE_CONVERGENCE:
            return True  # Early convergence (min 8 questions)
        return False

    def update_posterior_eap(self) -> tuple[float, float]:
        """Update ability estimate using Expected A Posteriori (EAP).

        EAP is more stable than MLE with few responses because it
        incorporates a prior distribution.
        """
        if not self.responses:
            return self.prior_mean, self.prior_sd

        # Compute posterior on grid
        log_posterior = np.zeros_like(THETA_GRID)

        # Prior contribution
        for i, theta in enumerate(THETA_GRID):
            log_posterior[i] = math.log(
                max(_normal_pdf(theta, self.prior_mean, self.prior_sd), 1e-300)
            )

        # Likelihood contribution from each response
        for resp in self.responses:
            item = self.model.items.get(resp.item_id)
            if not item:
                continue
            for i, theta in enumerate(THETA_GRID):
                p = self.model.probability(theta, item)
                if resp.response == 1:
                    log_posterior[i] += math.log(max(p, 1e-300))
                else:
                    log_posterior[i] += math.log(max(1.0 - p, 1e-300))

        # Normalize (log-sum-exp trick)
        max_log = np.max(log_posterior)
        posterior = np.exp(log_posterior - max_log)
        total = np.sum(posterior)
        if total < 1e-300:
            return self.theta_estimate, self.theta_se

        posterior /= total

        # EAP estimate = E[theta | data]
        theta_hat = float(np.sum(THETA_GRID * posterior))
        # SE = sqrt(Var[theta | data])
        variance = float(np.sum((THETA_GRID - theta_hat) ** 2 * posterior))
        se = math.sqrt(max(variance, 1e-10))

        self.theta_estimate = np.clip(theta_hat, -4.0, 4.0)
        self.theta_se = se
        return self.theta_estimate, self.theta_se

    def select_next_item(self) -> IRTItem | None:
        """Select the most informative unanswered item."""
        return self.model.select_next_item_cat(
            current_theta=self.theta_estimate,
            available_items=self.items_pool,
            answered_items=self.answered_item_ids,
        )

    def record_response(self, item_id: str, correct: bool) -> tuple[float, float]:
        """Record a response and update the ability estimate.

        Returns (theta_estimate, theta_se).
        """
        resp = IRTResponse(
            student_id=self.student_id,
            item_id=item_id,
            response=1 if correct else 0,
            response_time=0.0,
        )
        self.responses.append(resp)
        self.answered_item_ids.append(item_id)
        self.model.add_response(resp)
        return self.update_posterior_eap()

    def get_confidence_interval(self) -> tuple[float, float]:
        """95% confidence interval for ability estimate."""
        return (
            self.theta_estimate - 1.96 * self.theta_se,
            self.theta_estimate + 1.96 * self.theta_se,
        )

    def get_confidence_level(self) -> str:
        """Human-readable confidence classification."""
        ci_width = 2 * 1.96 * self.theta_se
        if ci_width < 1.0:
            return "high"
        if ci_width < 2.0:
            return "medium"
        return "low"


# ---------------------------------------------------------------------------
# DB operations
# ---------------------------------------------------------------------------


async def load_assessment_items(
    *,
    db: AsyncSession,
    subjects: list[str] | None = None,
    max_per_subject: int = 50,
) -> list[IRTItem]:
    """Load IRT-calibrated questions from question_bank for the assessment pool.

    Selects questions with IRT parameters, balanced across subjects.
    """
    from models.question_bank import QuestionBankItem

    limit_val = max_per_subject * len(subjects or SUBJECT_AREAS)
    # NOT: select(...).tablesample() SQLAlchemy 2.0'da YOK — postgresql dalı
    # AttributeError ile patlıyordu. func.random() her iki dialect'te de çalışır,
    # dolayısıyla dialect ayrımına ve "az geldiyse tekrar sor" fallback'ine gerek
    # kalmadı (bkz offline_sync_service.py:112).
    query = select(QuestionBankItem).where(
        QuestionBankItem.is_active == True,  # noqa: E712
        QuestionBankItem.difficulty_level.isnot(None),
        # student-facing seçim TEK doğruluk kaynağı: v_safe_for_beta.
        # is_active-only sorgu 94K unverified/pending soruyu sızdırıyordu.
        QuestionBankItem.id.in_(text("SELECT id FROM v_safe_for_beta")),
    )

    if subjects:
        query = query.where(
            QuestionBankItem.subject_area.in_([s.upper() for s in subjects])
        )

    query = query.order_by(func.random()).limit(limit_val)

    result = await db.execute(query)
    rows = result.scalars().all()

    items = []
    for q in rows:
        # Map difficulty_level string to IRT difficulty float
        difficulty_map = {
            "COK_KOLAY": -2.0,
            "KOLAY": -1.0,
            "ORTA": 0.0,
            "ZOR": 1.0,
            "COK_ZOR": 2.0,
        }
        # GF40 fix: ``difficulty_level`` is a ``QuestionDifficultyLevel`` enum
        # on the ORM (via SQLAlchemy ``Enum``), not a plain str. Coerce to the
        # underlying value — or fall back to the raw attribute — before string
        # ops. ``str(enum)`` yields ``"QuestionDifficultyLevel.KOLAY"`` which is
        # useless, so reach for ``.value`` first.
        raw_diff = getattr(q, "difficulty_level", None)
        if raw_diff is None:
            diff_str = "ORTA"
        else:
            diff_str = str(getattr(raw_diff, "value", raw_diff))
        difficulty = difficulty_map.get(diff_str.upper().replace(" ", "_"), 0.0)

        try:
            item = IRTItem(
                item_id=str(q.id),
                discrimination=1.0,  # Default — will be calibrated over time
                difficulty=difficulty,
                guessing=0.2,  # 5-choice MCQ: 1/5 = 0.2
                upper_asymptote=0.98,
                subject=getattr(q, "subject_area", ""),
                topic=getattr(q, "primary_topic_id", "") or "",
                _validate=False,  # Skip strict validation for loaded items
            )
            items.append(item)
        except Exception:
            continue

    return items


async def start_assessment(
    *,
    db: AsyncSession,
    student_id: str,
    subjects: list[str] | None = None,
) -> dict[str, Any]:
    """Start a new placement assessment session.

    Returns session info and the first question.
    """
    assessment = PlacementAssessment(student_id=student_id)

    # Load item pool
    items = await load_assessment_items(db=db, subjects=subjects)
    if not items:
        return {"error": "Yeterli soru bulunamadı"}

    assessment.items_pool = items
    for item in items:
        assessment.model.add_item(item)

    # Select first question
    first_item = assessment.select_next_item()
    if not first_item:
        return {"error": "Soru seçilemedi"}

    return {
        "session_id": assessment.session_id,
        "total_questions": MAX_QUESTIONS,
        "current_question": 1,
        "question_id": first_item.item_id,
        "subject": first_item.subject,
        "difficulty": first_item.difficulty,
        "theta_estimate": assessment.theta_estimate,
        "theta_se": assessment.theta_se,
        "confidence_level": assessment.get_confidence_level(),
        "_assessment": assessment,  # Internal state (not serialized to client)
    }


def get_knowledge_state(assessment: PlacementAssessment) -> dict[str, Any]:
    """Convert final ability estimate to per-subject mastery percentages.

    Maps theta to a 0-100 mastery scale per subject based on
    which questions were answered correctly in each area.
    """
    subject_stats: dict[str, dict[str, int]] = {}

    for resp in assessment.responses:
        item = assessment.model.items.get(resp.item_id)
        if not item:
            continue
        subj = item.subject or "DIGER"
        if subj not in subject_stats:
            subject_stats[subj] = {"correct": 0, "total": 0}
        subject_stats[subj]["total"] += 1
        if resp.response == 1:
            subject_stats[subj]["correct"] += 1

    # Convert to mastery percentages
    knowledge_map = {}
    for subj, stats in subject_stats.items():
        if stats["total"] > 0:
            raw_pct = stats["correct"] / stats["total"] * 100
            # Adjust for guessing: mastery = (raw - chance) / (1 - chance)
            # For 5-choice MCQ, chance = 20%
            adjusted = max(0, (raw_pct - 20) / 80 * 100)
            knowledge_map[subj] = {
                "mastery_pct": round(adjusted, 1),
                "raw_accuracy": round(raw_pct, 1),
                "questions_answered": stats["total"],
                "correct": stats["correct"],
            }

    # Overall
    total_correct = sum(s["correct"] for s in subject_stats.values())
    total_answered = sum(s["total"] for s in subject_stats.values())

    ci = assessment.get_confidence_interval()

    return {
        "overall": {
            "theta": round(assessment.theta_estimate, 3),
            "se": round(assessment.theta_se, 3),
            "confidence_interval_95": [round(ci[0], 3), round(ci[1], 3)],
            "confidence_level": assessment.get_confidence_level(),
            "total_questions": total_answered,
            "total_correct": total_correct,
            "accuracy_pct": round(total_correct / max(total_answered, 1) * 100, 1),
            "yks_predicted_net": round(300 + assessment.theta_estimate * 66.67, 1),
        },
        "subjects": knowledge_map,
    }
