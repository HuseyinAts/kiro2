"""DB tablo pariteliği — canlı kod yolu olan tablolar gerçekten var mı?

Neden bu test var (27 Tem 2026):
`alembic/versions/c555a10f4b93_sync_db_changes.py` bir `--autogenerate` çıktısıdır
ve `upgrade()` gövdesinde 145 adet `DROP TABLE IF EXISTS ... CASCADE` taşır.
`env.py` target_metadata'sı yalnızca `models.database.Base` olduğu için, başka
model modüllerindeki (ve raw-SQL ile yaratılmış) tablolar autogenerate'e "fazlalık"
göründü ve düşürüldü. `alembic_version` head'de kaldığı için şema kaybı SESSİZ oldu:
son 72 saatte `student_question_flags` 160, `teacher_classroom_students` 84,
`billing_subscriptions` 17 kez `UndefinedTableError` fırlattı.

Bu test o sınıfı ("alembic head diyor ki uygulandı, ama tablo yok") yakalar.
Kapsam bilinçli olarak DAR: ORM'de tanımlı her tablo değil, yalnızca canlı bir
kullanıcı yolundan sorgulanan tablolar. env.py:65 zaten "108 tablo henüz DB'de
oluşturulmamış (gelecek özellikler için model var)" diyor — onları istemek gürültü
üretir, sinyal değil.

NOT (kapsam sınırı): golden-flows.yml şu an bu dosyayı çağırmıyor (satır 220
`tests/e2e/test_golden_flows.py` ile dosya-kapsamlı). Workflow'un geçersiz YAML'ı
düzeltilirken (`-m golden_flow` tüm tests/e2e üzerinde) bu dosya da kapıya girecek.
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = pytest.mark.golden_flow

# tablo -> onu canlı olarak sorgulayan kod yolu (bu tablo yoksa o yol 500 verir)
CRITICAL_TABLES: dict[str, str] = {
    "billing_subscriptions": "GET /api/v1/billing/me (billing_api.py:62)",
    "student_question_flags": "POST /api/v1/questions/{id}/flag + curator köprüsü",
    "teacher_classroom_students": "GET /api/v1/teacher/students, /classes sayımı",
    "teacher_exam_configs": "GET /api/v1/teacher/exams",
    "teacher_assignments": "GET /api/v1/teacher/assignments",
    "teacher_contents": "GET /api/v1/teacher/contents",
}


@pytest_asyncio.fixture
async def db_conn():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)

    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await engine.connect()
    except Exception as exc:  # DB ayakta değil — kapıyı fail-close etme
        await engine.dispose()
        pytest.skip(f"DB erişilemiyor: {type(exc).__name__}")
    try:
        yield conn
    finally:
        await conn.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_critical_tables_exist(db_conn):
    """Canlı kod yolu olan her tablo DB'de mevcut olmalı."""
    missing: list[str] = []
    for table, kod_yolu in CRITICAL_TABLES.items():
        result = await db_conn.execute(
            text("SELECT to_regclass(:qualified)"), {"qualified": f"public.{table}"}
        )
        if result.scalar() is None:
            missing.append(f"{table} -> {kod_yolu}")

    assert not missing, (
        "Şu tablolar DB'de YOK ama canlı kod onları sorguluyor (500 üretir):\n  "
        + "\n  ".join(missing)
        + "\n\nalembic_version head'de olması tablonun var olduğunu KANITLAMAZ — "
        "c555a10f4b93 upgrade() gövdesinde 145 DROP TABLE taşıyor."
    )
