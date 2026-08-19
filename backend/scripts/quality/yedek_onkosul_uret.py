#!/usr/bin/env python
"""`pg_dump -t` yedeğinin ÖNKOŞUL dosyasını üretir (enum + uzantı tipleri).

NEDEN VAR (19 Ağu 2026, A2b)
----------------------------
`pg_dump -t <tablo>` bir tabloyu dökerken o tablonun bağlı olduğu **kullanıcı
tiplerini ve uzantı tiplerini TAŞIMAZ**. Boş bir hedefe geri yüklerken:

    pg_restore: hata: ERROR: type "public.questiondifficultylevel" does not exist
    -> question_statistics TABLOSU HIC OLUSMADI -> 36.967 satir HIC YUKLENMEDI

5 tablodan 4'ü yüklendi, biri tamamen kayboldu ve `pg_restore` yalnızca
`EXIT=1` dedi. Yani "dump içinde 147.880 satır var" ölçümü dump'ın
**içeriğini** kanıtlıyordu, **geri yüklenebilirliğini** değil.

İkinci katman ancak ilki kapatılınca göründü (`public.vector`), o yüzden
bağımlılıklar tek tek keşfedilmiyor — `pg_catalog`'dan **sistemik** çıkarılıyor
(`L-s202-katmanli-hata-sistemik-tara`).

DDL ELLE YAZILMAZ, ÜRETİLİR (`L-s202-ddl-orm-den-render`): enum etiketleri
elle kopyalanırsa bir harf hatası tipi sessizce farklı yapar.

KULLANIM
--------
    python backend/scripts/quality/yedek_onkosul_uret.py > backups/<ad>.prereq.sql

    # geri yukleme:
    psql -d <HEDEF> -v ON_ERROR_STOP=1 -f backups/<ad>.prereq.sql
    pg_restore -d <HEDEF> --no-owner --no-privileges backups/<ad>.dump

Bekçi: `backend/tests/db/test_yedek_onkosul_kapsami.py`
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

# Yedegin aldigi tablolar. Bekci bu kumenin dump ile AYNI oldugunu assert eder;
# ayrisirsa uretec eksik tip uretir ve kimse fark etmez (yanlis-sifir).
YEDEK_TABLOLARI = (
    "question_bank",
    "question_content",
    "question_metadata",
    "question_statistics",
    "topic_hierarchy",
)

_SORGU_UZANTI = text("""
    SELECT DISTINCT e.extname
      FROM pg_attribute a
      JOIN pg_class c ON c.oid = a.attrelid
                     AND c.relnamespace = 'public'::regnamespace
      JOIN pg_type t ON t.oid = a.atttypid
      JOIN pg_depend d ON d.objid = t.oid AND d.deptype = 'e'
      JOIN pg_extension e ON e.oid = d.refobjid
     WHERE c.relname = ANY(:tablolar)
       AND a.attnum > 0 AND NOT a.attisdropped
""")

# enumsortorder SART: PG'de enum SIRASI anlamlidir (ORDER BY, <, >).
_SORGU_ENUM = text("""
    SELECT t.typname, e.enumlabel
      FROM pg_attribute a
      JOIN pg_class c ON c.oid = a.attrelid
                     AND c.relnamespace = 'public'::regnamespace
      JOIN pg_type t ON t.oid = a.atttypid AND t.typtype = 'e'
      JOIN pg_enum e ON e.enumtypid = t.oid
     WHERE c.relname = ANY(:tablolar)
       AND a.attnum > 0 AND NOT a.attisdropped
     ORDER BY t.typname, e.enumsortorder
""")


async def gerekli_tipler(session) -> dict:
    """Canlı şemadan, yedek tablolarının yerleşik-OLMAYAN tip bağımlılıkları."""
    tablolar = list(YEDEK_TABLOLARI)
    uzantilar = set(
        (await session.execute(_SORGU_UZANTI, {"tablolar": tablolar})).scalars().all()
    )
    enumlar: dict[str, list[str]] = {}
    for ad, etiket in (
        await session.execute(_SORGU_ENUM, {"tablolar": tablolar})
    ).all():
        enumlar.setdefault(ad, []).append(etiket)
    return {"uzantilar": uzantilar, "enumlar": enumlar}


def onkosul_sql(gerekli: dict) -> str:
    """Önkoşul SQL'ini üret. Uzantılar ÖNCE (enum onlara bağlı olabilir)."""
    satirlar = [
        "-- URETILDI: backend/scripts/quality/yedek_onkosul_uret.py (elle yazilmadi)",
        "-- Kullanim: psql -d <HEDEF> -v ON_ERROR_STOP=1 -f <bu dosya>, SONRA pg_restore",
    ]
    for uzanti in sorted(gerekli["uzantilar"]):
        satirlar.append(f"CREATE EXTENSION IF NOT EXISTS {uzanti};")
    for ad, etiketler in sorted(gerekli["enumlar"].items()):
        # Etiket SIRASI korunur -- sorgu enumsortorder ile geliyor.
        degerler = ", ".join(f"'{e}'" for e in etiketler)
        satirlar.append(f"CREATE TYPE public.{ad} AS ENUM ({degerler});")
    return "\n".join(satirlar) + "\n"


def eksik_tipler(sql_metni: str, gerekli: dict) -> set[str]:
    """Verilen önkoşul SQL'inin KARŞILAMADIĞI bağımlılıklar.

    Bekçinin çekirdeği ve bilerek SAF: DB'siz mutasyonla çivilenebilsin.
    Boş küme = önkoşul tam.
    """
    eksik: set[str] = set()
    for uzanti in gerekli["uzantilar"]:
        if f"EXTENSION IF NOT EXISTS {uzanti};" not in sql_metni:
            eksik.add(f"uzanti:{uzanti}")
    for ad in gerekli["enumlar"]:
        if f"CREATE TYPE public.{ad} AS ENUM" not in sql_metni:
            eksik.add(f"enum:{ad}")
    return eksik


async def _uret() -> str:
    dsn = os.environ.get("KVKK_VERIFY_DSN") or os.environ.get("DATABASE_URL_SYNC")
    if not dsn or "sqlite" in dsn.lower():
        raise SystemExit(
            "HATA: gercek postgres DSN yok. KVKK_VERIFY_DSN ver.\n"
            "(sqlite REDDEDILIR -- yanlis semadan onkosul uretmek sessiz felakettir)"
        )
    for onek in ("postgresql+psycopg2://", "postgresql://"):
        if dsn.startswith(onek):
            dsn = dsn.replace(onek, "postgresql+asyncpg://", 1)
            break

    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            gerekli = await gerekli_tipler(conn)
    finally:
        await engine.dispose()

    if not gerekli["uzantilar"] and not gerekli["enumlar"]:
        # Yanlis-SIFIR bir BULGU degil, alet arizasi adayidir.
        raise SystemExit(
            "HATA: hicbir tip bagimliligi bulunamadi — sorgu ya da baglanti bozuk. "
            "Bos bir onkosul dosyasi yazmak, kirik yedegi 'tam' gosterirdi."
        )
    return onkosul_sql(gerekli)


if __name__ == "__main__":
    sys.stdout.write(asyncio.run(_uret()))
