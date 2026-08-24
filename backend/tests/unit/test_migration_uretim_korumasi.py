"""Bekci: goc testleri URETIM veritabanina karsi ASLA kosmamali.

Neden (S251, 24 Agu 2026): `tests/test_migrations.py` aylardir
`skipif(True, ...)` ile KOSULSUZ susturulmustu. Susturma kosullu hale
getirilince 16 testin 6'si canlandi -- ama ayni degisiklik bir tehlikeyi de
ACTI: `TestSchemaAfterMigration` ve `TestDowngradeSafety`,
`command.downgrade(..., "base")` cagirisini HEDEF VERITABANINDA calistirir ve
"mevcut tablo varsa atla" korumasi YOKTUR.

Onceki hal bu tehlikeyi sabit `True` ile ortuyordu. Yorum satiri yaptirim
degildir: bu depo 5 Agu 2026'da takipsiz bir TRUNCATE ile icerik kaybetti.
Bu yuzden koruma KODA gomuldu ve burada assert ediliyor.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
if (
    str(BACKEND) not in sys.path
):  # pragma: no cover  # ortam kurulumu: sys.path zaten doluysa kosmaz
    sys.path.insert(0, str(BACKEND))


def _modul():
    """test_migrations modulunu env okundugu ANDA yeniden yukler."""
    import tests.test_migrations as m

    return importlib.reload(m)


def test_uretim_dsn_i_reddedilir(monkeypatch):
    """`kiro2` (uretim) DSN'i verilirse kapi ACILMAMALI."""
    monkeypatch.setenv(
        "TEST_DATABASE_URL", "postgresql://postgres@localhost:5434/kiro2"
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)

    engel = _modul()._kosma_engeli()

    assert engel is not None, "uretim DSN'i ile kapi ACILDI -- downgrade(base) riski"
    assert "URETIM" in engel.upper()


def test_test_veritabani_dsn_i_kabul_edilir_veya_baglanti_sebebiyle_reddedilir(
    monkeypatch,
):
    """Kontrol kolu: reddin sebebi 'uretim' DEGIL baglanti olmali.

    Bu test dusmezse yukaridaki yesil anlamsizdir -- kapi her DSN'i
    reddediyor olabilir (yanlis-pozitif koruma).
    """
    monkeypatch.setenv(
        "TEST_DATABASE_URL", "postgresql://postgres@localhost:5434/kiro2_test_yok"
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)

    engel = _modul()._kosma_engeli()

    if engel is not None:
        assert (
            "URETIM" not in engel.upper()
        ), "uretim-disi DSN 'uretim korumasi' ile reddedildi -- koruma cok genis"


def test_postgres_olmayan_dsn_reddedilir(monkeypatch):
    monkeypatch.setenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    engel = _modul()._kosma_engeli()

    assert engel is not None
    assert "postgres" in engel.lower()


@pytest.mark.parametrize(
    ("dsn", "beklenen"),
    [
        ("postgresql://u:p@h:5434/kiro2", "kiro2"),
        ("postgresql+psycopg://u:p@h:5434/kiro2?sslmode=require", "kiro2"),
        ("postgresql://u:p@h:5434/kiro2_test", "kiro2_test"),
        ("postgresql://u@h/", ""),
    ],
)
def test_dsn_veritabani_adi_ayristirmasi(dsn, beklenen):
    """Ad ayristirmasi query-string ve surucu ekiyle bozulmamali."""
    assert _modul()._dsn_veritabani_adi(dsn) == beklenen
