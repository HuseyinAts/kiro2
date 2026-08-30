"""
Integration Test Suite for Database Table Synchronization & Student Profile Auto-Provisioning
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import inspect, text

from application.commands.auth import RegisterUserCommand, RegisterUserCommandHandler
from services.profile_sync_service import ensure_student_profile


@pytest.mark.asyncio
async def test_key_database_tables_exist(db_session):
    """Verify all critical tables exist in PostgreSQL / SQLite schema."""
    conn = await db_session.connection()
    present_tables = set(
        await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    )

    required_tables = [
        "users",
        "student_profiles",
        "learning_path_student_profiles",
        "video_solutions",
        "study_sessions",
        "fsrs_study_sessions",
        "question_bank",
        "exam_sessions",
        "student_answers",
    ]

    for tbl in required_tables:
        assert (
            tbl in present_tables
        ), f"Critical table '{tbl}' is missing from database schema!"


@pytest.mark.asyncio
async def test_student_registration_provisions_both_profiles(db_session):
    """Verify registering a student user provisions student_profiles and learning_path_student_profiles."""
    unique_email = f"sync_test_{uuid.uuid4().hex[:8]}@kiro2.com"
    cmd = RegisterUserCommand(
        email=unique_email,
        sifre="TestPass123!",
        ad_soyad="Sync Test Student",
        rol="ogrenci",
        birth_date=date(2005, 5, 15),
        sinif=11,
        db=db_session,
    )
    handler = RegisterUserCommandHandler()
    result = await handler.handle(cmd)

    assert result["success"] is True
    user_id = result["id"]

    # Check student_profiles
    res_sp = await db_session.execute(
        text("SELECT id FROM student_profiles WHERE user_id = :uid"), {"uid": user_id}
    )
    assert res_sp.fetchone() is not None, "student_profiles entry was not created!"

    # Check learning_path_student_profiles
    res_lp = await db_session.execute(
        text(
            "SELECT student_id FROM learning_path_student_profiles WHERE user_id = :uid"
        ),
        {"uid": user_id},
    )
    assert (
        res_lp.fetchone() is not None
    ), "learning_path_student_profiles entry was not created!"


@pytest.mark.asyncio
async def test_ensure_student_profile_on_demand(db_session):
    """Verify ensure_student_profile creates missing profile entries for an existing user."""
    test_user_id = f"usr_test_{uuid.uuid4().hex[:8]}"
    test_email = f"ondemand_{uuid.uuid4().hex[:8]}@kiro2.com"

    # Insert raw user without profile
    await db_session.execute(
        text("""
            INSERT INTO users (id, email, username, first_name, last_name, password_hash, role, is_active, is_verified, is_2fa_enabled, is_premium, is_parent, total_xp, level, elo_rating, created_at, updated_at)
            VALUES (:id, :email, :uname, 'Test', 'User', 'hash', 'STUDENT', TRUE, FALSE, FALSE, FALSE, FALSE, 0, 1, 1200, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """),
        {"id": test_user_id, "email": test_email, "uname": test_email.split("@")[0]},
    )
    await db_session.commit()

    # Call ensure_student_profile
    sync_res = await ensure_student_profile(db_session, test_user_id)
    assert sync_res["status"] == "ok"

    # Verify both tables populated
    sp_row = (
        await db_session.execute(
            text("SELECT id FROM student_profiles WHERE user_id = :uid"),
            {"uid": test_user_id},
        )
    ).fetchone()
    assert sp_row is not None

    lp_row = (
        await db_session.execute(
            text(
                "SELECT student_id FROM learning_path_student_profiles WHERE user_id = :uid"
            ),
            {"uid": test_user_id},
        )
    ).fetchone()
    assert lp_row is not None
