"""0037 (ACIL + C1CELL beta onayi) koruma testleri -- canli DB istemez.

NE KORUR
1. KIMLIK      -- revizyon adi/zinciri, 32 karakter siniri, ASCII.
2. KAPSAM      -- yalniz iki hedef kaynak; hedef SQL sik_bos'u disarida
                  birakir ve source_book ile sinirlidir; UPDATE'ler id
                  listesiyle sinirli (kosulsuz UPDATE butun bankayi acardi).
3. DURUSTLUK   -- human_verified yazmaz, is_ai_generated'a dokunmaz,
                  onay_turu toplu olarak isaretlenir.
4. GERI ALMA   -- eklenen her metadata anahtari downgrade listesinde;
                  gunluk tablosu uc onceki degeri de saklar.
5. SINYALLER   -- her kitabin sinyalleri KENDINE ait (kopyalanmamis).

NOT: aramalar modul DOCSTRING'I CIKARILMIS kaynak uzerinde yapilir.
Docstring bilerek "human_verified YAZILMIYOR" gibi cumleler icerir; ham
metinde arama yanlis pozitif uretir (ilk surumde tam bunu uretti).
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
MIG_YOLU = KOK / "alembic" / "versions" / "0037_geo_beta_onay.py"

ACIL = "ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi"
C1CELL = "C1CELL 2024 TYT-AYT Geometri Soru Bankasi"


@pytest.fixture(scope="module")
def mig():
    spec = importlib.util.spec_from_file_location("mig0037", MIG_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def metin() -> str:
    return MIG_YOLU.read_text("utf-8")


@pytest.fixture(scope="module")
def kod() -> str:
    """Modul docstring'i cikarilmis kaynak."""
    agac = ast.parse(MIG_YOLU.read_text("utf-8"))
    govde = agac.body[1:] if ast.get_docstring(agac) else agac.body
    return "\n".join(ast.unparse(d) for d in govde)


# ------------------------------------------------------------------ 1. kimlik


def test_kimlik_ve_zincir(mig) -> None:
    assert mig.revision == "0037_geo_beta_onay"
    assert mig.down_revision == "0036_geo_gorsel_url"
    assert len(mig.revision) <= 32


def test_ascii(metin: str) -> None:
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"ASCII disi karakter: {disarida}"


# ------------------------------------------------------------------ 2. kapsam


def test_yalniz_iki_hedef_kaynak(mig) -> None:
    assert {k for k, _ in mig.KAYNAKLAR} == {ACIL, C1CELL}


def test_hedef_sorgusu_source_book_ile_sinirli(mig) -> None:
    assert "source_book = :kaynak" in mig._HEDEF_SQL


def test_hedef_sorgusu_sik_bos_disarida_birakir(mig) -> None:
    """sik_bos kapinin KENDI kosulu; acilsa bile kapidan gecemez."""
    sql = " ".join(mig._HEDEF_SQL.split())
    assert "NOT ((qm.pipeline_metadata::jsonb -> 'bayraklar') ? 'sik_bos')" in sql


def test_guncellemeler_id_listesiyle_sinirli(kod: str) -> None:
    """question_bank / metadata / statistics UPDATE'leri id ile sinirli olmali.

    Kosulsuz bir UPDATE question_bank BUTUN soru bankasini aktiflestirirdi.
    topic_hierarchy haric tutulur: o sayac guncellemesidir, is_active'e gore
    yeniden hesaplar, satir secmez.
    """
    parcalar = [
        p
        for p in re.split(r"(?=UPDATE question_)", kod)
        if p.startswith("UPDATE question_")
    ]
    assert parcalar, "hic UPDATE bulunamadi -- test yanlis yere bakiyor"
    for parca in parcalar:
        assert (
            "id = ANY(:idler)" in parca or "WHERE id = :id" in parca
        ), f"id ile sinirli degil: {' '.join(parca.split())[:140]}"


# --------------------------------------------------------------- 3. durustluk


def test_human_verified_yazmaz(kod: str) -> None:
    """Hicbir insan bu sorulari tek tek dogrulamadi; oyle de yazilmamali."""
    assert "human_verified" not in kod
    assert "auto_judged_high" in kod


def test_is_ai_generated_alanina_dokunmaz(kod: str) -> None:
    assert not re.search(r"SET[^;]*is_ai_generated", kod)


def test_toplu_onay_isaretlenir(kod: str) -> None:
    assert "'onay_turu', 'toplu_beta_sahibi'" in kod
    assert "'bireysel_denetim_yapildi', false" in kod


# --------------------------------------------------------------- 4. geri alma


def test_eklenen_anahtarlar_downgrade_listesinde(mig) -> None:
    assert set(mig.EK_ANAHTARLAR) == {
        "consensus_2signal_run",
        "konsensus_sinyalleri",
        "onay_turu",
        "bireysel_denetim_yapildi",
    }


def test_eklenen_her_anahtar_gercekten_siliniyor(mig, kod: str) -> None:
    """jsonb_build_object'te eklenen her anahtar EK_ANAHTARLAR'da olmali."""
    eklenen = set(re.findall(r"'(\w+)',\s*(?:true|false|CAST|'toplu)", kod))
    eksik = eklenen - set(mig.EK_ANAHTARLAR)
    assert not eksik, f"eklenip downgrade'de silinmeyen anahtar: {eksik}"


def test_gunluk_uc_onceki_degeri_saklar(kod: str) -> None:
    for kolon in (
        "onceki_is_active",
        "onceki_review_status",
        "onceki_quality_review_status",
    ):
        assert kolon in kod, f"gunlukte {kolon} yok -- geri alinamaz"


def test_downgrade_gunluk_tablosunu_dusurur(kod: str) -> None:
    assert "op.drop_table(GUNLUK)" in kod


# --------------------------------------------------------------- 5. sinyaller


def test_her_kitabin_sinyalleri_kendine_ait(mig) -> None:
    """0023'un dersi: baska kitabin sinyal listesini kopyalamak yanlistir."""
    sinyaller = dict(mig.KAYNAKLAR)
    acil, c1 = set(sinyaller[ACIL]), set(sinyaller[C1CELL])
    assert acil and c1
    assert not (acil & c1), f"iki kitapta ortak sinyal: {acil & c1}"


def test_sinyaller_kitaba_ozgu_terim_tasiyor(mig) -> None:
    sinyaller = dict(mig.KAYNAKLAR)
    assert any("test_basina" in s for s in sinyaller[ACIL])
    assert any("birim" in s for s in sinyaller[C1CELL])


def test_uyum_sinyali_kapinin_bekledigi_anahtar(kod: str) -> None:
    """v_safe_for_beta'nin kabul ettigi alti anahtardan biri yazilmali."""
    assert "'consensus_2signal_run', true" in kod
