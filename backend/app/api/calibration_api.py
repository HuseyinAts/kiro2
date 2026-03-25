"""
GET /api/v1/calibration/status
IRT kalibrasyon durumunu döndürür.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db

router = APIRouter(prefix="/api/v1/calibration", tags=["IRT Kalibrasyon"])

STATUS_SQL = text("""
SELECT
    COUNT(*)                                                         AS total,
    COUNT(*) FILTER (WHERE is_calibrated = TRUE
        AND calibration_sample_size > 0
        AND calibration_quality_score > 0)                           AS genuinely_calibrated,
    COUNT(*) FILTER (WHERE is_calibrated = TRUE
        AND (calibration_sample_size = 0 OR calibration_quality_score = 0)) AS bootstrap_only,
    COUNT(*) FILTER (WHERE is_calibrated = FALSE)                    AS uncalibrated
FROM question_bank WHERE is_active = TRUE
""")

PENDING_SQL = text("""
SELECT COUNT(*) AS pending
FROM question_bank q
WHERE q.is_active = TRUE AND q.is_calibrated = FALSE
  AND (
    (SELECT COUNT(*) FROM kiro2_learning_events le
     WHERE le.question_id::text=q.id::text AND le.is_correct IS NOT NULL)
    +
    (SELECT COUNT(*) FROM student_answers sa
     WHERE sa.question_id::text=q.id::text AND sa.is_correct IS NOT NULL)
  ) >= 50
""")

LAST_RUN_SQL = text("""
SELECT MAX(calibration_date) AS last_run
FROM irt_calibration_history
WHERE standard_error > 0
""")

RESPONSE_STATS_SQL = text("""
SELECT
  (SELECT COUNT(*) FROM kiro2_learning_events
   WHERE event_type='cat_answer' AND is_correct IS NOT NULL)   AS cat_responses,
  (SELECT COUNT(*) FROM student_answers WHERE is_correct IS NOT NULL) AS exam_responses
""")


@router.get("/status", summary="IRT kalibrasyon durumu")
async def calibration_status(
    current_user: User         = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    r1 = (await db.execute(STATUS_SQL)).fetchone()
    r2 = (await db.execute(PENDING_SQL)).fetchone()
    r3 = (await db.execute(LAST_RUN_SQL)).fetchone()
    r4 = (await db.execute(RESPONSE_STATS_SQL)).fetchone()

    total          = r1.total          if r1 else 0
    genuine        = r1.genuinely_calibrated if r1 else 0
    bootstrap      = r1.bootstrap_only if r1 else 0
    uncalibrated   = r1.uncalibrated   if r1 else 0
    pending        = r2.pending        if r2 else 0
    last_run       = r3.last_run       if r3 else None
    cat_responses  = r4.cat_responses  if r4 else 0
    exam_responses = r4.exam_responses if r4 else 0

    # Kalibrasyon oranı
    genuine_pct = round(genuine / total * 100, 1) if total else 0

    return {
        "total_questions":        total,
        "genuinely_calibrated":   genuine,
        "genuinely_calibrated_pct": genuine_pct,
        "bootstrap_only":         bootstrap,
        "uncalibrated":           uncalibrated,
        "pending_calibration":    pending,   # ≥50 yanıt biriken, sıradaki
        "response_data": {
            "cat_responses":      cat_responses,
            "exam_responses":     exam_responses,
            "total_responses":    cat_responses + exam_responses,
            "responses_needed_for_first_3pl": max(0, 200 - (cat_responses + exam_responses)),
        },
        "last_genuine_calibration": str(last_run) if last_run else None,
        "pipeline_status": (
            "NO_DATA"       if (cat_responses + exam_responses) < 50   else
            "ACCUMULATING"  if (cat_responses + exam_responses) < 1000 else
            "READY"
        ),
        "recommendation": (
            "Öğrenci yanıtları birikiyor. Minimum 200 yanıt/soru için ~1000 öğrenci gerekli."
            if (cat_responses + exam_responses) < 200
            else f"{pending} soru kalibre edilmeye hazır. "
                 "python scripts/irt_calibration_runner.py çalıştır."
            if pending > 0
            else "Yeterli veri biriktikçe Celery task otomatik çalışacak."
        ),
    }
