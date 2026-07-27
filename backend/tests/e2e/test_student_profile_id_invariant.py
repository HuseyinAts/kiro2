"""student_profiles.id == users.id değişmezi (invariant).

Kod tabanının TAMAMI bu değişmeze dayanıyor: `exam_sessions.student_id` FK'sı
`student_profiles.id`'ye bakar, ama sınav oluşturma yolu (sinav.py ->
osym_exam_engine.py) oraya `current_user.id` yazar. 21 okuma noktası ve
`beta_create_profiles.py:79`'daki "CONVENTION: student_profiles.id MUST EQUAL
users.id" notu aynı varsayımı paylaşıyor.

Değişmezi ihlal eden tek yer kayıt endpoint'iydi: `api/auth.py:631` profile'a
`str(uuid4())` ile bağımsız bir kimlik veriyordu. Sonuç: /auth/kayit ile kaydolan
her öğrenci `/osym-exam/beta-practice` çağırdığında ForeignKeyViolation -> HTTP 500
(27 Tem 2026 ölçümü: 74 profilin 60'ında id <> user_id).

Bu bug 17 May 2026'da zaten bulunmuş ama kaynakta değil, 11 kullanıcı için bir yama
script'iyle "çözülmüştü" (.claude/rules/testing.md Ders #14 ihlali: 2+ kez görülen
sorun ROOT CAUSE'dan çözülmeli). Bu test o yamanın yerine geçen kalıcı bekçidir:
auth.py bir daha bağımsız kimlik üretmeye başlarsa, ilk kayıttan sonra kırmızıya
döner.
"""

import os

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

pytestmark = pytest.mark.golden_flow


def _resolve_dsn() -> str | None:
    dsn = (
        os.environ.get("KVKK_VERIFY_DSN")
        or os.environ.get("DATABASE_URL_SYNC")
        or os.environ.get("DATABASE_URL")
    )
    if not dsn:
        return None
    for prefix in ("postgresql+psycopg2://", "postgresql://"):
        if dsn.startswith(prefix):
            return dsn.replace(prefix, "postgresql+asyncpg://", 1)
    return dsn


@pytest_asyncio.fixture
async def db_conn():
    dsn = _resolve_dsn()
    if not dsn:
        pytest.skip("KVKK_VERIFY_DSN / DATABASE_URL ayarlı değil")

    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await engine.connect()
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"DB erişilemiyor: {type(exc).__name__}")
    try:
        yield conn
    finally:
        await conn.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_student_profile_id_equals_user_id(db_conn):
    """Hiçbir öğrenci profilinde id, user_id'den farklı olmamalı."""
    result = await db_conn.execute(
        text(
            """
            SELECT id::text, user_id::text
            FROM student_profiles
            WHERE id::text <> user_id::text
            ORDER BY id
            LIMIT 5
            """
        )
    )
    ihlaller = result.fetchall()

    toplam = (
        await db_conn.execute(
            text(
                "SELECT count(*) FROM student_profiles WHERE id::text <> user_id::text"
            )
        )
    ).scalar()

    assert not ihlaller, (
        f"{toplam} profilde student_profiles.id <> user_id. "
        "Bu profillerin sahipleri /osym-exam/beta-practice çağırınca "
        "ForeignKeyViolation -> HTTP 500 alır "
        "(exam_sessions.student_id -> student_profiles.id).\n"
        f"İlk {len(ihlaller)} örnek (id, user_id): {ihlaller}"
    )
