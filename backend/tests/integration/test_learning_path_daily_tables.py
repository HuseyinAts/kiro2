"""learning_path gunluk plan tablolari bekcisi (cdea871deea9).

NEDEN VAR
---------
`daily_plans` / `yks_exam_goals` / `learning_progress_daily` bu ortamda hic
yoktu (041a9181271c'nin UYARI ciktisi). Canli kod bunlara bagimli:
`tasks/daily_plan_tasks.py` (gecelik Celery beat), `app/api/learning_path_daily.py`
(POST /learning-path/goal + gunluk plan varsayilan hedef), `api/pwa_sync_api.py`
(PWA offline-sync upsert). Tablo yoklugu -> her cagri 500 / gece boyu retry-fail.

Bu dosya iki seyi dogrular:
  1. Tablolar + kolonlar var mi (sema kontrolu).
  2. Uygulamanin GERCEK KULLANDIGI SQL (INSERT/UPSERT/SELECT, literal
     ON CONFLICT ifadeleri dahil) hatasiz calisiyor mu (rollback'li,
     uretim verisine dokunmadan).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

psycopg2 = pytest.importorskip("psycopg2")


def _bugun() -> date:
    """DTZ011: `date.today()` yerine tz-farkindali."""
    return datetime.now(UTC).date()


pytestmark = [pytest.mark.integration]

DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

TABLES = ("yks_exam_goals", "daily_plans", "learning_progress_daily")


@pytest.fixture(scope="module")
def baglanti():
    """Modul boyunca tek transaction, sonunda ROLLBACK — uretim verisine DOKUNMAZ."""
    try:
        conn = psycopg2.connect(DSN)
    except psycopg2.OperationalError as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture(scope="module")
def gercek_user_id(baglanti) -> str:
    """FK'nin gecerli olmasi icin `users` tablosundan gercek bir id al."""
    with baglanti.cursor() as imlec:
        imlec.execute("SELECT id FROM users LIMIT 1")
        row = imlec.fetchone()
    if not row:
        pytest.skip("`users` tablosu bos — FK testleri anlamsiz olur")
    return row[0]


def test_uc_tablo_da_var(baglanti) -> None:
    """Kapsam: cdea871deea9'un yarattigi 3 tablo mevcut mu."""
    with baglanti.cursor() as imlec:
        for t in TABLES:
            imlec.execute("SELECT to_regclass(%s)", (f"public.{t}",))
            assert (
                imlec.fetchone()[0] == t
            ), f"{t} hala yok — migration uygulanmamis olabilir"


def test_data_processing_agreements_organization_id_var(baglanti) -> None:
    with baglanti.cursor() as imlec:
        imlec.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='data_processing_agreements' "
            "AND column_name='organization_id'"
        )
        assert (
            imlec.fetchone() is not None
        ), "data_processing_agreements.organization_id hala yok"


def test_yks_exam_goals_upsert_calisir(baglanti, gercek_user_id: str) -> None:
    """app/api/learning_path_daily.py::save_student_goal ile BIREBIR ayni SQL."""
    with baglanti.cursor() as imlec:
        imlec.execute(
            """
            INSERT INTO yks_exam_goals
                (user_id, exam_type, exam_date, daily_minutes,
                 target_university, target_department, created_at, updated_at)
            VALUES (%(uid)s, %(exam_type)s, %(exam_date)s, %(daily_minutes)s,
                    %(target_univ)s, %(target_dept)s, NOW(), NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                exam_type = EXCLUDED.exam_type,
                exam_date = EXCLUDED.exam_date,
                daily_minutes = EXCLUDED.daily_minutes,
                target_university = EXCLUDED.target_university,
                target_department = EXCLUDED.target_department,
                updated_at = NOW()
            """,
            {
                "uid": gercek_user_id,
                "exam_type": "TYT",
                "exam_date": date(_bugun().year, 6, 7),
                "daily_minutes": 120,
                "target_univ": "ODTU",
                "target_dept": "Bilgisayar Muhendisligi",
            },
        )
        imlec.execute(
            "SELECT exam_type, exam_date, daily_minutes FROM yks_exam_goals "
            "WHERE user_id = %s",
            (gercek_user_id,),
        )
        row = imlec.fetchone()
    assert row == ("TYT", date(_bugun().year, 6, 7), 120)


def test_daily_plans_upsert_calisir(baglanti, gercek_user_id: str) -> None:
    """tasks/daily_plan_tasks.py::_async_refresh ile BIREBIR ayni SQL."""
    with baglanti.cursor() as imlec:
        imlec.execute(
            """
            INSERT INTO daily_plans
                (user_id, plan_date, exam_date, days_remaining,
                 total_minutes, plan_json, weak_subject,
                 strong_subject, motivational_note, generated_at)
            VALUES
                (%(uid)s, %(plan_date)s, %(exam_date)s, %(days_rem)s,
                 %(total_min)s, %(plan_json)s, %(weak)s,
                 %(strong)s, %(note)s, NOW())
            ON CONFLICT (user_id, plan_date) DO UPDATE SET
                total_minutes     = EXCLUDED.total_minutes,
                plan_json         = EXCLUDED.plan_json,
                weak_subject      = EXCLUDED.weak_subject,
                strong_subject    = EXCLUDED.strong_subject,
                motivational_note = EXCLUDED.motivational_note,
                generated_at      = NOW()
            """,
            {
                "uid": gercek_user_id,
                "plan_date": _bugun(),
                "exam_date": date(_bugun().year, 6, 7),
                "days_rem": 100,
                "total_min": 120,
                "plan_json": '{"blocks": []}',
                "weak": "MATEMATIK",
                "strong": "TURKCE",
                "note": "Devam et!",
            },
        )
        imlec.execute(
            "SELECT total_minutes FROM daily_plans "
            "WHERE user_id = %s AND plan_date = %s",
            (gercek_user_id, _bugun()),
        )
        row = imlec.fetchone()
    assert row == (120,)


def test_learning_progress_daily_upsert_calisir(baglanti, gercek_user_id: str) -> None:
    """api/pwa_sync_api.py::sync_progress ile BIREBIR ayni SQL — literal
    ON CONFLICT ON CONSTRAINT adi Postgres'in oto-uretecegi adla eslesmeli.
    """
    with baglanti.cursor() as imlec:
        imlec.execute(
            """
            INSERT INTO learning_progress_daily
                (user_id, log_date, subject, minutes_spent, questions_done,
                 correct_count, activity_type)
            VALUES
                (%(user_id)s, %(log_date)s, %(subject)s, %(minutes_spent)s,
                 %(questions_done)s, %(correct_count)s, %(activity_type)s)
            ON CONFLICT ON CONSTRAINT
                learning_progress_daily_user_id_log_date_subject_activity_t_key
            DO UPDATE SET
                minutes_spent = EXCLUDED.minutes_spent,
                questions_done = EXCLUDED.questions_done,
                correct_count = EXCLUDED.correct_count
            """,
            {
                "user_id": gercek_user_id,
                "log_date": _bugun(),
                "subject": "MATEMATIK",
                "minutes_spent": 30,
                "questions_done": 10,
                "correct_count": 7,
                "activity_type": "practice",
            },
        )
        imlec.execute(
            "SELECT minutes_spent, questions_done, correct_count "
            "FROM learning_progress_daily "
            "WHERE user_id = %s AND log_date = %s "
            "AND subject = %s AND activity_type = %s",
            (gercek_user_id, _bugun(), "MATEMATIK", "practice"),
        )
        row = imlec.fetchone()
    assert row == (30, 10, 7)


def test_uc_tablo_fail_closed_data_processing_permissive(baglanti) -> None:
    """RLS kalibi: 3 yeni tablo fail-closed, data_processing_agreements permissive."""
    with baglanti.cursor() as imlec:
        for t in TABLES:
            imlec.execute(
                "SELECT qual FROM pg_policies "
                "WHERE tablename = %s AND policyname = 'tenant_isolation'",
                (t,),
            )
            qual = imlec.fetchone()[0]
            assert "IS NULL" not in qual, f"{t} beklenmedik sekilde permissive"

        imlec.execute(
            "SELECT qual FROM pg_policies "
            "WHERE tablename = 'data_processing_agreements' "
            "AND policyname = 'tenant_isolation'"
        )
        qual = imlec.fetchone()[0]
        assert (
            "IS NULL" in qual
        ), "data_processing_agreements beklenmedik sekilde fail-closed"
