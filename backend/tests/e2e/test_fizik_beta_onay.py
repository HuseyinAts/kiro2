"""0039 (345 AYT Fizik + Mikro TYT Fizik beta onayi) korumalari -- canli DB istemez.

NE KORUR
1. KIMLIK     -- revizyon adi/zinciri, 32 karakter siniri, ASCII.
2. KAPSAM     -- yalniz iki hedef kaynak; UPDATE'ler id listesiyle sinirli.
3. DISLAMA    -- servis edilemez satirlar hedefin DISINDA:
                 (a) sik_bos / gorsel_yok_sekilli /
                     gosterilemez_gorsel_sik_kirpimsiz bayraklari
                 (b) ogrenciye GORUNEN alti alandan birinde `[??]`
                 Ikincisi bu migration'a ozgudur: ortme bayragi iki kitapta
                 FARKLI seyi isaretliyor (FIZ345'te basili soru numarasini,
                 MIKRO'da govdeyi), bu yuzden dislama bayraga degil olcume
                 baglandi.
4. DURUSTLUK  -- human_verified yazmaz, is_ai_generated'a dokunmaz.
5. GERI ALMA  -- eklenen anahtarlar downgrade listesinde; gunluk uc onceki
                 degeri saklar.
6. SINYALLER  -- her kitabin sinyalleri KENDINE ait (kopyalanmamis).
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
MIG_YOLU = KOK / "alembic" / "versions" / "0039_fizik_beta_onay.py"

FIZ345 = "345 2025 AYT Fizik Soru Bankasi"
MIKRO = "Mikro Orijinal TYT Fizik Soru Bankasi 2025"

GORUNEN_ALANLAR = (
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
)


@pytest.fixture(scope="module")
def mig():
    spec = importlib.util.spec_from_file_location("mig0039", MIG_YOLU)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def metin() -> str:
    return MIG_YOLU.read_text("utf-8")


@pytest.fixture(scope="module")
def kod() -> str:
    """Modul docstring'i cikarilmis kaynak (docstring 'human_verified
    YAZILMIYOR' gibi cumleler icerir; ham metinde aramak yanlis pozitif verir).
    """
    agac = ast.parse(MIG_YOLU.read_text("utf-8"))
    govde = agac.body[1:] if ast.get_docstring(agac) else agac.body
    return "\n".join(ast.unparse(d) for d in govde)


# ----------------------------------------------------------------- 1. kimlik


def test_kimlik_ve_zincir(mig) -> None:
    assert mig.revision == "0039_fizik_beta_onay"
    assert mig.down_revision == "0038_fizik_gorsel_url"
    assert len(mig.revision) <= 32


def test_ascii(metin: str) -> None:
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"ASCII disi karakter: {disarida}"


# ----------------------------------------------------------------- 2. kapsam


def test_yalniz_iki_hedef_kaynak(mig) -> None:
    assert {k for k, _ in mig.KAYNAKLAR} == {FIZ345, MIKRO}


def test_hedef_sorgusu_source_book_ile_sinirli(mig) -> None:
    assert "source_book = :kaynak" in mig._HEDEF_SQL


def test_guncellemeler_id_listesiyle_sinirli(kod: str) -> None:
    """Kosulsuz bir UPDATE question_bank BUTUN bankayi aktiflestirirdi."""
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


# ---------------------------------------------------------------- 3. dislama


def test_servis_disi_bayraklar_sql_ile_ayni(mig) -> None:
    """Sabit liste ile SQL metni ayni uc bayragi tasimali.

    SQL duz yazildigi icin (S608'den kacinmak uzere) ikisi elle esitlenir;
    bu test kaymayi yakalar.
    """
    assert set(mig.SERVIS_DISI_BAYRAKLAR) == {
        "sik_bos",
        "gorsel_yok_sekilli",
        "gosterilemez_gorsel_sik_kirpimsiz",
    }
    for bayrak in mig.SERVIS_DISI_BAYRAKLAR:
        assert f"? '{bayrak}'" in mig._HEDEF_SQL, f"SQL'de {bayrak} dislanmiyor"


def test_gorunen_alti_alanda_ortme_isareti_dislanir(mig) -> None:
    """ASIL YENILIK: dislama bayraga degil OLCUME bagli."""
    sql = mig._HEDEF_SQL
    for alan in GORUNEN_ALANLAR:
        assert f"qc.{alan} NOT LIKE :isaret" in sql, f"{alan} denetlenmiyor"
    assert mig.ORTME_ISARETI == "%[??]%"


def test_ortme_bayragi_tek_basina_dislamiyor(mig) -> None:
    """FIZ345'te ortme basili NUMARAYI vuruyor; o satirlar servis edilebilir.

    Bayrak adi SQL'de gecmemeli -- gecerse 16 saglam satir bosuna dusardi.
    """
    assert "okuyucu_simgesi_ortmesi" not in mig._HEDEF_SQL


def test_mukerrer_aday_dislanmiyor(mig) -> None:
    """Mukerrer adaylari GORUNUR birakildi, dislanmadi (karar geri alinabilir)."""
    assert "mukerrer_aday" not in mig._HEDEF_SQL


# -------------------------------------------------------------- 4. durustluk


def test_human_verified_yazmaz(kod: str) -> None:
    assert "human_verified" not in kod
    assert "auto_judged_high" in kod


def test_is_ai_generated_alanina_dokunmaz(kod: str) -> None:
    assert not re.search(r"SET[^;]*is_ai_generated", kod)


def test_toplu_onay_isaretlenir(kod: str) -> None:
    assert "'onay_turu', 'toplu_beta_sahibi'" in kod
    assert "'bireysel_denetim_yapildi', false" in kod


# -------------------------------------------------------------- 5. geri alma


def test_eklenen_anahtarlar_downgrade_listesinde(mig) -> None:
    assert set(mig.EK_ANAHTARLAR) == {
        "consensus_2signal_run",
        "konsensus_sinyalleri",
        "onay_turu",
        "bireysel_denetim_yapildi",
    }


def test_eklenen_her_anahtar_gercekten_siliniyor(mig, kod: str) -> None:
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


# -------------------------------------------------------------- 6. sinyaller


def test_her_kitabin_sinyalleri_kendine_ait(mig) -> None:
    sinyaller = dict(mig.KAYNAKLAR)
    a, b = set(sinyaller[FIZ345]), set(sinyaller[MIKRO])
    assert a and b
    assert not (a & b), f"iki kitapta ortak sinyal: {a & b}"


def test_sinyaller_kitaba_ozgu_terim_tasiyor(mig) -> None:
    sinyaller = dict(mig.KAYNAKLAR)
    assert any("cevap_satiri" in s for s in sinyaller[FIZ345])
    assert any("serit" in s for s in sinyaller[MIKRO])


def test_uyum_sinyali_kapinin_bekledigi_anahtar(kod: str) -> None:
    assert "'consensus_2signal_run', true" in kod


def test_onceki_beta_migrationlariyla_kaynak_cakismasi_yok() -> None:
    """0037 geometriyi acti, 0039 fizigi; ayni satiri iki kez acmasinlar."""
    yol = KOK / "alembic" / "versions" / "0037_geo_beta_onay.py"
    spec = importlib.util.spec_from_file_location("mig0037", yol)
    assert spec and spec.loader
    m37 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m37)
    spec2 = importlib.util.spec_from_file_location("mig0039b", MIG_YOLU)
    assert spec2 and spec2.loader
    m39 = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(m39)
    ortak = {k for k, _ in m37.KAYNAKLAR} & {k for k, _ in m39.KAYNAKLAR}
    assert not ortak, f"iki migration ayni kaynagi aciyor: {ortak}"
