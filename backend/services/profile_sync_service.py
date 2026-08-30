"""
Student Profile Synchronization & Auto-Provisioning Service

Ensures that any student user account has matching entries in:
- student_profiles
- learning_path_student_profiles

Prevents 404/500 errors when students attempt to solve questions or access learning paths.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def ensure_student_profile(
    db: AsyncSession, user_id: str, grade_level: int = 11
) -> dict[str, str]:
    """
    On-the-fly helper ensuring student_profiles and learning_path_student_profiles exist for user_id.
    Returns status dictionary indicating created or existing profiles.
    """
    if not user_id:
        return {"status": "skipped", "reason": "empty_user_id"}

    # Check user role
    user_res = await db.execute(
        text("SELECT id, role FROM users WHERE id = :uid"), {"uid": user_id}
    )
    user_row = user_res.fetchone()
    if not user_row:
        return {"status": "error", "reason": "user_not_found"}

    # 1. Ensure student_profiles row
    await db.execute(
        text("""
            INSERT INTO student_profiles
                (id, user_id, grade_level, veli_onay, current_level, total_study_hours,
                 total_questions_solved, correct_answers, irt_ability, created_at, updated_at)
            VALUES
                (:id, :user_id, :grade_level, TRUE, 0.0, 0, 0, 0, 0.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING;
        """),
        {"id": user_id, "user_id": user_id, "grade_level": grade_level},
    )

    # 2. Ensure learning_path_student_profiles row
    #
    # `neuro_inclusive_mode` (boolean, NOT NULL, server_default YOK) EXPLICIT
    # verilmeli -- ORM'deki Python-tarafi `default=False` (bkz. S255,
    # models/learning_path_models.py) yalnizca ORM INSERT'lerini korur, bu
    # raw-SQL cagrisini KORUMAZ. Olculdu: bu deger olmadan her cagri
    # `NotNullViolationError` ile duser (bkz.
    # tests/integration/test_db_profile_sync.py::test_ensure_student_profile_on_demand).
    await db.execute(
        text("""
            INSERT INTO learning_path_student_profiles
                (student_id, user_id, name, grade, exam_target, learning_style, knowledge_level, neuro_inclusive_mode, interests, goals, available_time, metadata_json, created_at, updated_at)
            VALUES
                (:student_id, :user_id, 'Student', :grade, 'TYT', 'visual', 'beginner', FALSE, '[]', '[]', 60, '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (student_id) DO NOTHING;
        """),
        {"student_id": user_id, "user_id": user_id, "grade": str(grade_level)},
    )

    await db.commit()
    logger.info(f"Student profile ensured for user_id={user_id}")
    return {"status": "ok", "user_id": user_id}
