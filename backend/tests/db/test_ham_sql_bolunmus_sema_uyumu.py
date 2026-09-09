"""photo_ask_service ve wave2b_quality_routes ham SQL'i gercek semada calisiyor mu.

tests/fast/test_ham_sql_bolunmus_kolon.py'nin DB'li kardesi: modul seviyesine
cikarilmis sorgu metinlerini gercek Postgres'e karsi kosturur. Satir sayisi
onemsiz (yerelde 0 embedding var, benzerlik sorgusu bos doner) -- kanit,
sorgunun UndefinedColumn atmadan donmesi. DB yoksa skip.

Mutasyon: eski tek-tablo sorgular geri konunca UndefinedColumnError (2/2 FAILED).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = [pytest.mark.db_invariant, pytest.mark.asyncio]


@pytest_asyncio.fixture
async def oturum():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)
    motor = create_async_engine(dsn, poolclass=NullPool)
    yapici = async_sessionmaker(motor, class_=AsyncSession, expire_on_commit=False)
    async with yapici() as s:
        yield s
    await motor.dispose()


async def test_wave2b_osym_referans_sorgusu(oturum: AsyncSession) -> None:
    from api.wave2b_quality_routes import OSYM_REFERANS_SQL

    satirlar = (await oturum.execute(text(OSYM_REFERANS_SQL), {"limit": 3})).fetchall()
    assert len(satirlar) <= 3
    for r in satirlar:
        assert r[0] and len(r[0]) > 50  # question_text
        assert r[3] is not None  # correct_answer


async def test_photo_ask_benzerlik_sorgusu(oturum: AsyncSession) -> None:
    from services.photo_ask_service import (
        KONU_FILTRESI,
        TEMEL_FILTRELER,
        benzer_soru_sql,
    )

    boyut = (
        await oturum.execute(
            text(
                "SELECT atttypmod FROM pg_attribute WHERE attrelid = "
                "'question_statistics'::regclass AND attname = 'embedding'"
            )
        )
    ).scalar_one()
    # Birim vektor (sifir vektorun kosinus uzakligi NaN olur, sorguyu olcmez)
    birim = "[" + ",".join(["1", *(["0"] * (int(boyut) - 1))]) + "]"
    where = " AND ".join([*TEMEL_FILTRELER, KONU_FILTRESI])
    satirlar = (
        await oturum.execute(
            text(benzer_soru_sql(where)),
            {"emb": birim, "min_sim": 0.0, "top_k": 3, "subject_area": "MATEMATIK"},
        )
    ).fetchall()
    assert len(satirlar) <= 3
    for r in satirlar:
        assert r.subject_area == "MATEMATIK"
        assert 0.0 <= float(r.similarity) <= 1.0
