"""Senkron (psycopg v3) Postgres motoru -- DB dogrulama testleri icin tek tanim.

NEDEN VAR (olcum: CI run 34055271678, 6 Eyl 2026)
-------------------------------------------------
Bes test dosyasi birbirinin kopyasi bir `_engine()` tasiyordu:

    raw = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    create_engine(make_url(raw).set(host="127.0.0.1", port=5434, database="kiro2"))

Bu iki ayri kusuru birden uretiyordu ve ikisi de YALNIZ CI'da goruluyordu
(yerelde veritabani adi gercekten `kiro2`, psycopg2 de kurulu):

  1. `database="kiro2"` sabiti .env'den gelen adi EZIYOR. CI'da veritabani
     `kiro2_test` -> `InvalidCatalogNameError: database "kiro2" does not
     exist`. Olculen etki: 13 test (bu bes dosya) + ayni sinifin baska
     dosyalardaki ornekleri.
  2. `postgresql://` SQLAlchemy 2.x'te VARSAYILAN surucu olarak psycopg2
     arar. Depoda calisan surucu psycopg v3 (`requirements.txt`:
     `psycopg[binary]>=3.1.0`); psycopg2 YALNIZ `requirements-test.txt`te
     ve CI o dosyayi hic kurmuyor (`ci.yml` sadece requirements.txt +
     elle sayilan birkac paket kuruyor) -> `ModuleNotFoundError: No module
     named 'psycopg2'`.

KURAL (tests/e2e/pg_dsn.py ile ayni): gercek-DB testi, gercek DB yoksa SKIP
olmali -- sahte bir motorla ya da var olmayan bir veritabani adiyla
BASARISIZ olmamali. Basarisizlik "kod bozuk" demektir; ortam eksikligi degil.

Host/port bilincli olarak sabit kaliyor: hem yerelde hem CI'da Postgres
5434'te. Degisen tek sey veritabani adi ve surucu -- ikisi de artik DSN'den
ve kurulu paketten geliyor.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url

SKIP_SEBEBI = (
    "Gercek postgres DATABASE_URL yok (backend/.env ya da ortam degiskeni). "
    "conftest.py DATABASE_URL'i sqlite'a ezdigi icin .env override=True ile "
    "yeniden okunuyor."
)


def sync_pg_url(host: str = "127.0.0.1", port: int = 5434):
    """psycopg v3 surucusune sabitlenmis SQLAlchemy URL; yoksa pytest.skip."""
    from dotenv import load_dotenv

    env_yolu = Path(__file__).resolve().parents[1] / ".env"
    # override=True: conftest TESTING modunda DATABASE_URL'i sqlite'a set
    # ediyor; bu DB-dogrulama testleri gercek postgres hedefler.
    load_dotenv(env_yolu, override=True)

    raw = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not raw.startswith("postgresql"):
        pytest.skip(SKIP_SEBEBI)

    return make_url(raw).set(host=host, port=port, drivername="postgresql+psycopg")


def sync_pg_engine(host: str = "127.0.0.1", port: int = 5434) -> Engine:
    """Baglanabilir bir senkron Engine dondur; DB yoksa pytest.skip."""
    return create_engine(sync_pg_url(host=host, port=port))


def async_pg_dsn(host: str = "127.0.0.1", port: int = 5434) -> str:
    """asyncpg surucusune sabitlenmis DSN METNI; DB yoksa pytest.skip.

    NEDEN `render_as_string(hide_password=False)` (ve `str(url)` DEGIL):
    SQLAlchemy'de `URL.__str__()` = `render_as_string(hide_password=True)`,
    yani sifreyi `***` ile MASKELER ve o maske DSN'e literal sifre olarak
    gider -> `asyncpg.InvalidPasswordError`. Ayni tuzak bu depoda daha once
    olculdu: tests/unit/test_org_members.py (SS10.52).

    NEDEN SABIT DSN DEGIL: cagiran dosyalar
    `postgresql+asyncpg://<kullanici>:<parola>@localhost:5434/kiro2` gibi
    SABIT bir metin tasiyordu. Bu (a) parolayi git'e sokuyor -- S229'da
    ayni sinif `detect-secrets` tarafindan HAKLI olarak bloklanmisti -- ve
    (b) veritabani adini yerele civiliyordu; CI'da ad `kiro2_test` oldugu
    icin 29 test `InvalidCatalogNameError` ile dusuyordu.
    """
    return (
        sync_pg_url(host=host, port=port)
        .set(drivername="postgresql+asyncpg")
        .render_as_string(hide_password=False)
    )
