"""Curator verdict → student-flag auto-resolve regresyon testi.

Köprünün (flag→curator) ikinci yarısını korur: curator bir soruya verdict
verince o sorunun çözülmemiş öğrenci flag'leri otomatik kapanmalı:
  - reject / archive → flag.resolution = "confirmed" (öğrenci haklıydı)
  - verify           → flag.resolution = "rejected"  (yanlış alarm)

Strict-rollback fixture (KVKK deseni): KVKK_VERIFY_DSN (5434/kiro2 prod şeması),
join_transaction_mode="create_savepoint" → post_verdict'in commit()'i savepoint'e
yazar, dıştaki transaction test sonunda rollback → SIFIR kalıcı yazma.
"""

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.skipif(
    os.getenv("USE_POSTGRES_TESTS") != "true",
    reason="Curator verdict gerçek DB gerektirir (USE_POSTGRES_TESTS=true)",
)


@pytest_asyncio.fixture
async def db_session():
    """5434/kiro2'ye strict-rollback session (global broken db_session override)."""
    dsn = os.environ.get("KVKK_VERIFY_DSN")
    if not dsn:
        pytest.skip("KVKK_VERIFY_DSN ayarlı değil (5434 strict-rollback fixture)")
    if dsn.startswith("postgresql://"):
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif dsn.startswith("postgresql+psycopg2://"):
        dsn = dsn.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(dsn, poolclass=NullPool)
    conn = await engine.connect()
    trans = await conn.begin()
    maker = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        if trans.is_active:
            await trans.rollback()
        await conn.close()
        await engine.dispose()


class _Admin:
    """post_verdict yalnızca .id kullanır; audit_logs FK için gerçek user id verilir."""

    def __init__(self, uid: str):
        self.id = uid


async def _seed_flag(db: AsyncSession, qid: str, uid: str) -> str:
    flag_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO student_question_flags "
            "(id, user_id, question_id, flag_type, note, created_at) "
            "VALUES (:id, :uid, :qid, 'wrong_answer', 'regresyon testi', NOW())"
        ),
        {"id": flag_id, "uid": uid, "qid": qid},
    )
    await db.commit()
    return flag_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "verdict,expected_resolution",
    [("reject", "confirmed"), ("verify", "rejected")],
)
async def test_verdict_auto_resolves_student_flag(
    db_session: AsyncSession, verdict: str, expected_resolution: str
):
    """verdict → o sorunun çözülmemiş flag'i otomatik kapanır (doğru resolution ile)."""
    db = db_session

    # 1) Mevcut aktif soru + mevcut kullanıcı (FK'lar için)
    qid = (
        await db.execute(
            text("SELECT id FROM question_bank WHERE is_active = TRUE LIMIT 1")
        )
    ).scalar()
    uid = (await db.execute(text("SELECT id FROM users LIMIT 1"))).scalar()
    if not qid or not uid:
        pytest.skip("test için soru/kullanıcı bulunamadı")

    # 2) Çözülmemiş öğrenci flag'i oluştur
    flag_id = await _seed_flag(db, str(qid), str(uid))

    # 3) Verdict'i uygula (endpoint fonksiyonunu doğrudan çağır; request=None
    #    → _write_audit_log None'ı tolere eder)
    from api.curator import VerdictRequest, post_verdict

    resp = await post_verdict(
        body=VerdictRequest(question_id=str(qid), verdict=verdict),
        request=None,  # type: ignore[arg-type]
        admin=_Admin(str(uid)),
        db=db,
    )
    assert resp.new_status in ("rejected", "archived", "auto_judged_high")

    # 4) Flag otomatik kapandı mı + doğru resolution
    row = (
        await db.execute(
            text(
                "SELECT resolution, resolved_at, resolved_by "
                "FROM student_question_flags WHERE id = :id"
            ),
            {"id": flag_id},
        )
    ).first()
    assert row is not None
    assert row[0] == expected_resolution, (
        f"verdict={verdict} → flag.resolution beklenen '{expected_resolution}', "
        f"gelen '{row[0]}'"
    )
    assert row[1] is not None, "resolved_at set edilmeli"
    assert row[2] == str(uid), "resolved_by curator id olmalı"


@pytest.mark.asyncio
async def test_verdict_does_not_touch_other_questions_flags(db_session: AsyncSession):
    """Bir soruya verdict, BAŞKA sorunun flag'ini çözmemeli (WHERE question_id izolasyonu)."""
    db = db_session
    rows = (
        await db.execute(
            text("SELECT id FROM question_bank WHERE is_active = TRUE LIMIT 2")
        )
    ).all()
    uid = (await db.execute(text("SELECT id FROM users LIMIT 1"))).scalar()
    if len(rows) < 2 or not uid:
        pytest.skip("test için 2 soru + kullanıcı gerekli")
    q_verdict, q_other = str(rows[0][0]), str(rows[1][0])

    other_flag = await _seed_flag(db, q_other, str(uid))

    from api.curator import VerdictRequest, post_verdict

    await post_verdict(
        body=VerdictRequest(question_id=q_verdict, verdict="reject"),
        request=None,  # type: ignore[arg-type]
        admin=_Admin(str(uid)),
        db=db,
    )

    row = (
        await db.execute(
            text("SELECT resolved_at FROM student_question_flags WHERE id = :id"),
            {"id": other_flag},
        )
    ).first()
    assert row[0] is None, "başka sorunun flag'i dokunulmadan kalmalı"
