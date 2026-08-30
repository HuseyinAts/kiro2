"""OSYM referans sorgusu tablo-drift bekcisi.

NEDEN VAR
---------
`api/hybrid_question_generation.py` (Wave 2B few-shot havuzu) ve
`services/production_quality_monitor.py` (`_get_evaluator`) ham SQL ile
`FROM sorular` sorguluyordu. `sorular` tablosu YALNIZCA
`backend/migrations/013_create_sorular_table.sql` icinde tanimli; bu klasor
alembic'e HIC entegre degil, yani hicbir `alembic upgrade head` onu yaratmaz.
Tablo bu yuzden her ortamda yok.

Hata gorunur DEGILDI: iki cagri yeri de `except Exception -> logger.warning`
ile yutuyordu. Sonuc 500 degil, **sessiz kalite kaybi** — Wave 2B referanssiz
uretim yapiyor, kalite monitorunun evaluator'u hic kurulmuyor.

BU TEST NEYI CIVILER
--------------------
Testin kendi SQL kopyasi YOKTUR. Kaynak dosyalari okuyup icindeki SQL'de
gecen tablo adlarini cikarir ve her birinin canli DB'de var oldugunu dogrular.
Boylece test ile uretim SQL'i ayrisamaz: biri `sorular`'a geri donerse test
duser (mutasyonla dogrulandi).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

psycopg2 = pytest.importorskip("psycopg2")

pytestmark = [pytest.mark.integration]

DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

BACKEND = Path(__file__).resolve().parents[2]

# SQL'i ham metin olarak tasiyan cagri yerleri.
KAYNAKLAR = (
    "api/hybrid_question_generation.py",
    "services/production_quality_monitor.py",
)

# Buyuk harf ZORUNLU: Python'un `from x import y` satirlarini disarida birakir.
# `FROM (` / `JOIN (` alt-sorgulari eslesmez cunku ident `[a-z_]` ile baslamali.
TABLO_RE = re.compile(r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)\b")

# SQL'de tablo gibi gorunup tablo olmayan adlar (CTE, fonksiyon, alt-sorgu alias).
TABLO_OLMAYAN = frozenset({"unnest", "generate_series", "jsonb_array_elements"})


def _sqldeki_tablolar(goreli_yol: str) -> set[str]:
    metin = (BACKEND / goreli_yol).read_text(encoding="utf-8", errors="replace")
    return {t for t in TABLO_RE.findall(metin) if t not in TABLO_OLMAYAN}


@pytest.fixture(scope="module")
def baglanti():
    """Salt-okunur; yine de transaction acip sonunda ROLLBACK yapar."""
    try:
        conn = psycopg2.connect(DSN)
    except psycopg2.OperationalError as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


def _var_mi(baglanti, tablo: str) -> bool:
    """Tablo VEYA view VEYA matview olarak cozulebiliyor mu."""
    with baglanti.cursor() as imlec:
        imlec.execute("SELECT to_regclass(%s)", (f"public.{tablo}",))
        return imlec.fetchone()[0] is not None


def test_kaynaklar_sql_iceriyor() -> None:
    """Kontrol kolu: ayristirici gercekten tablo buluyor mu?

    Bu assert olmadan, regex bozulup 0 tablo dondurdugunde asagidaki testler
    'hicbir sey bulunamadi' diye SESSIZCE gecerdi — yani bekci olu olurdu.
    """
    for kaynak in KAYNAKLAR:
        tablolar = _sqldeki_tablolar(kaynak)
        assert tablolar, (
            f"{kaynak} icinde hic SQL tablo referansi bulunamadi — "
            "ayristirici bozulmus olabilir, bekci OLU demektir"
        )


@pytest.mark.parametrize("kaynak", KAYNAKLAR)
def test_sqldeki_her_tablo_canli_dbde_var(baglanti, kaynak: str) -> None:
    """Kaynak dosyanin SQL'inde gecen her tablo DB'de cozulebilmeli.

    Duserse: ya tablo silinmis ya da sorgu alembic disi bir tabloyu hedefliyor
    (`sorular` vakasi). Ikisi de sessiz bozulma uretir.
    """
    eksik = sorted(t for t in _sqldeki_tablolar(kaynak) if not _var_mi(baglanti, t))
    assert not eksik, (
        f"{kaynak} su tablolari sorguluyor ama canli DB'de YOKLAR: {eksik}. "
        "Sorgu sessizce yutuluyorsa kalite kaybi fark edilmez."
    )


def test_uretim_havuzu_kapisi_kullaniliyor(baglanti) -> None:
    """Soru metni ceken sorgular kalite kapisindan gecmeli.

    CLAUDE.md sert kurali: soru sorgularinda `is_active` + kalite-status
    filtresi ZORUNLU. Ham `question_content` taramasi OCR copunu LLM'e
    few-shot ornek olarak besler.
    """
    assert _var_mi(baglanti, "mv_safe_for_beta"), "kalite kapisi matview'i yok"

    for kaynak in KAYNAKLAR:
        tablolar = _sqldeki_tablolar(kaynak)
        if "question_content" not in tablolar:
            continue
        assert "mv_safe_for_beta" in tablolar, (
            f"{kaynak} `question_content`'ten metin cekiyor ama "
            "`mv_safe_for_beta` kapisini kullanmiyor"
        )
