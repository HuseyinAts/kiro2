"""#485 Task 2 — `question_bank.is_active` varsayilan degeri.

ÖLÇÜLEN KUSUR (18 Agu 2026, S229):
`models/question_bank.py` `is_active`'i `default=False, server_default="true"`
ile taniml(iyordu). SQLAlchemy'nin Python-side `default`'u INSERT'e kolonu
DAHIL EDER, dolayisiyla `server_default` HIC atesLenmez -> `is_active` set
edilmeden olusturulan her soru DB'ye **False** olarak yaziliyordu (yani
ogrenciye gorunmez + `uq_qb_soru_hash_active` mukerrer indeksi -- ki
`WHERE is_active = true` kismi indekstir -- o satirlar icin sessizce olu).

IKINCI OLCUM: `server_default="true"` canli DB'nin DDL'inde HIC YOKTU
(`information_schema.column_default IS NULL`). Yani "server_default eziliyor"
degil, **DDL'e hic girmemis fantom bir beyandi**; kolonu atlayan ham INSERT
`NotNullViolationError` veriyordu. Bu yuzden fix iki parcali:
  1. ORM `default=True`
  2. alembic `ALTER COLUMN is_active SET DEFAULT true` (DDL'i gercek yap)

Testler GERCEK Postgres'e kosar (mock DB bu kusur sinifini yapisal olarak
goremez -- S228 dersi) ve yazdiklarini ROLLBACK eder.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

os.environ.setdefault("TESTING", "true")

# `live_db` fixture'i tests/integration/conftest.py'de — DSN kaynak koda
# GOMULMEZ (parola git'e girmesin), ortam degiskeni veya backend/.env'den cozulur.
pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# 1) ORM katmani — sinif duzeyi beyan
# ---------------------------------------------------------------------------


async def test_orm_default_is_true_not_false() -> None:
    """ORM kolon varsayilani True olmali.

    `default=False` iken bu assert duser. Mutasyon: `default=True` -> `False`
    yapmak testi kirmali.
    """
    from models.question_bank import QuestionBankItem

    col = QuestionBankItem.__table__.c.is_active
    assert col.default is not None, "is_active'in Python-side default'u YOK"
    assert col.default.arg is True, (
        f"is_active Python-side default {col.default.arg!r} — True olmali. "
        "False ise is_active verilmeden olusturulan sorular GORUNMEZ olur."
    )


# ---------------------------------------------------------------------------
# 2) Davranis katmani — gercek INSERT ne yaziyor?
# ---------------------------------------------------------------------------


async def test_orm_insert_without_is_active_lands_true(live_db: AsyncSession) -> None:
    """is_active VERILMEDEN olusturulan soru DB'ye True olarak inmeli.

    Kusurun asil olculdugu yer burasi: sinif duzeyi beyan dogru olsa bile
    INSERT'in ne yazdigi ayri bir olcumdur.
    """
    from models.question_bank import QuestionBankItem

    topic_id = (
        await live_db.execute(text("SELECT id FROM topic_hierarchy LIMIT 1"))
    ).scalar()
    if topic_id is None:
        pytest.skip("topic_hierarchy bos — FK saglanamiyor")

    item = QuestionBankItem(soru_hash="t485_orm_" + "0" * 23, primary_topic_id=topic_id)
    live_db.add(item)
    await live_db.flush()

    # ORM cache'ini atlayarak DB'den ham oku
    db_value = (
        await live_db.execute(
            text("SELECT is_active FROM question_bank WHERE id = :i"), {"i": item.id}
        )
    ).scalar()

    assert db_value is True, (
        f"is_active DB'ye {db_value!r} olarak indi — True olmali. "
        "False ise yeni soru ogrenciye gorunmez ve mukerrer indeksi olu kalir."
    )


# ---------------------------------------------------------------------------
# 3) DDL katmani — migration gercekten uygulandi mi?
# ---------------------------------------------------------------------------


async def test_ddl_server_default_exists(live_db: AsyncSession) -> None:
    """DB'de gercek bir kolon varsayilani olmali (ORM'siz INSERT icin).

    ORM beyani `server_default="true"` yeterli DEGIL — o yalnizca
    `create_all`/migration DDL'i uretirken kullanilir. Canli DB'de gercekten
    var mi, `information_schema` ile olculur (Migration Kurallari: raw SQL
    migration -> information_schema dogrulamasi ZORUNLU).
    """
    default = (
        await live_db.execute(
            text("""SELECT column_default FROM information_schema.columns
                    WHERE table_name = 'question_bank'
                      AND column_name = 'is_active'""")
        )
    ).scalar()

    assert default is not None, (
        "question_bank.is_active DDL varsayilani YOK. ORM'de "
        'server_default="true" yaziyor ama DDL\'e girmemis (fantom beyan) — '
        "ORM'i atlayan INSERT NotNullViolation alir."
    )
    assert (
        "true" in str(default).lower()
    ), f"DDL varsayilani {default!r} — 'true' beklenirdi"


async def test_raw_insert_omitting_is_active_succeeds(live_db: AsyncSession) -> None:
    """ORM'i ATLAYAN ham INSERT de calismali (server_default devreye girer).

    Bu test DDL varsayilanini davranis uzerinden olcer: kolonu hic yazmayan
    bir INSERT NotNullViolation ALMAMALI ve satir True olmali.
    """
    topic_id = (
        await live_db.execute(text("SELECT id FROM topic_hierarchy LIMIT 1"))
    ).scalar()
    if topic_id is None:
        pytest.skip("topic_hierarchy bos — FK saglanamiyor")

    await live_db.execute(
        text("""INSERT INTO question_bank
                    (id, soru_hash, primary_topic_id, is_public,
                     is_ai_generated, is_anchor, review_status)
                VALUES ('t485-raw-1', :h, :t, false, false, false, 'approved')"""),
        {"h": "t485_raw_" + "0" * 23, "t": topic_id},
    )
    value = (
        await live_db.execute(
            text("SELECT is_active FROM question_bank WHERE id = 't485-raw-1'")
        )
    ).scalar()

    assert value is True, f"ham INSERT sonrasi is_active = {value!r}, True olmali"
