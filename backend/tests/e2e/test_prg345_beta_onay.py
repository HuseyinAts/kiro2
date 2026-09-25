"""0056 (345 Paragraf: eski hat pasif + beta onayi) korumalari -- canli DB istemez.

NE KORUR
1. KIMLIK     -- revizyon adi/zinciri, 32 karakter siniri, ASCII.
2. KAPSAM     -- yalniz bu kitap + bu ithal araci; UPDATE'ler id ile sinirli.
3. DISLAMA    -- servis disi bayraklar ve gorunen alanda `[??]` disarida;
                 kitap ici tekrarin ikinci uyesi (hash kisiti) PASIF kalir.
4. ESKI HAT   -- tam 8 id, yalniz aktifse, yalniz is_active degisir;
                 acmadan ONCE kapanir.
5. DURUSTLUK  -- human_verified yazmaz, is_ai_generated / is_public'e
                 dokunmaz, toplu onay isaretlenir.
6. GERI ALMA  -- gunluk uc onceki deger + islem; downgrade once acilanlari
                 kapatir; eklenen anahtarlar silinir.
7. SINYALLER  -- bu kitaba ait; onceki beta migration'lariyla ortak yok.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
SURUMLER = KOK / "alembic" / "versions"
MIG_YOLU = SURUMLER / "0056_prg345_beta_onay.py"

GORUNEN_ALANLAR = (
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
)


def _yukle(yol: Path, ad: str):
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def mig():
    return _yukle(MIG_YOLU, "mig0056")


@pytest.fixture(scope="module")
def metin() -> str:
    return MIG_YOLU.read_text("utf-8")


@pytest.fixture(scope="module")
def kod() -> str:
    """Docstring'siz kaynak (docstring 'human_verified YAZILMAZ' icerir)."""
    agac = ast.parse(MIG_YOLU.read_text("utf-8"))
    govde = agac.body[1:] if ast.get_docstring(agac) else agac.body
    return "\n".join(ast.unparse(d) for d in govde)


# ----------------------------------------------------------------- 1. kimlik


def test_kimlik_ve_zincir(mig) -> None:
    assert mig.revision == "0056_prg345_beta_onay"
    assert mig.down_revision == "0055_prg345_agac"
    assert len(mig.revision) <= 32


def test_zincirin_basi_tek(mig) -> None:
    """0056'dan sonra gelen bir revizyon yoksa head tektir."""
    sonrakiler = [
        p.name
        for p in SURUMLER.glob("*.py")
        if f'down_revision: Union[str, None] = "{mig.revision}"' in p.read_text("utf-8")
    ]
    assert len(sonrakiler) <= 1


def test_ascii(metin: str) -> None:
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"ASCII disi karakter: {disarida}"


# ----------------------------------------------------------------- 2. kapsam


def test_kaynak_ve_arac(mig) -> None:
    assert mig.KAYNAK == "345 2025 Paragraf Sifir Risk Soru Bankasi"
    assert mig.ITHAL_ARACI == "scripts/kitap/prg345_ithal.py"


def test_hedef_kitap_ve_ithal_araciyla_sinirli(mig) -> None:
    sql = mig._HEDEF_SQL
    assert "qm.source_book = :kaynak" in sql
    assert "->> 'ithal_araci' = :arac" in sql


def test_guncellemeler_id_ile_sinirli(kod: str) -> None:
    parcalar = [
        p
        for p in re.split(r"(?=UPDATE question_)", kod)
        if p.startswith("UPDATE question_")
    ]
    assert len(parcalar) >= 5, "UPDATE'ler bulunamadi -- test yanlis yere bakiyor"
    for parca in parcalar:
        assert (
            "id = ANY(:idler)" in parca or "WHERE id = :id" in parca
        ), f"id ile sinirli degil: {' '.join(parca.split())[:140]}"


# ---------------------------------------------------------------- 3. dislama


def test_servis_disi_bayraklar_sql_ile_ayni(mig) -> None:
    assert set(mig.SERVIS_DISI_BAYRAKLAR) == {
        "sik_bos",
        "gorsel_yok_sekilli",
        "gosterilemez_gorsel_sik_kirpimsiz",
    }
    for bayrak in mig.SERVIS_DISI_BAYRAKLAR:
        assert f"? '{bayrak}'" in mig._HEDEF_SQL, f"SQL'de {bayrak} dislanmiyor"


def test_gorunen_alti_alanda_ortme_isareti_dislanir(mig) -> None:
    for alan in GORUNEN_ALANLAR:
        assert f"qc.{alan} NOT LIKE :isaret" in mig._HEDEF_SQL
    assert mig.ORTME_ISARETI == "%[??]%"


def test_kitap_ici_tekrarin_ikinci_uyesi_disarida(mig) -> None:
    """uq_qb_soru_hash_active iki uyeyi ayni anda aktif tutamaz."""
    assert "qb.id <> :tekrar" in mig._HEDEF_SQL
    assert mig.KITAP_ICI_TEKRAR_PASIF == "4b52585c-f48e-5a69-bb06-9b4b9eb3ec91"


def test_bilgi_bayraklari_dislama_kosulu_degil(mig) -> None:
    """Olculup GORUNUR birakilan bayraklar hedefi daraltmamali."""
    for bayrak in (
        "kaynak_kusuru",
        "bulanik_metin_tasarim",
        "okuyucu_diski_ortme",
        "numara_ortulu",
        "mukerrer_aday",
        "cikmis_soru",
        "eski_hat_ikizi",
    ):
        assert bayrak not in mig._HEDEF_SQL, f"{bayrak} dislama kosuluna girmis"


# ---------------------------------------------------------------- 4. eski hat


def test_eski_hat_tam_sekiz_benzersiz_uuid(mig) -> None:
    ids = mig.ESKI_HAT_PASIF
    assert len(ids) == 8 and len(set(ids)) == 8
    for i in ids:
        assert re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", i
        )
    assert mig.KITAP_ICI_TEKRAR_PASIF not in ids


def test_eski_hat_yalniz_aktifse_ve_bu_kitapta(mig) -> None:
    sql = mig._ESKI_SQL
    assert "qb.id = ANY(:idler)" in sql
    assert "qm.source_book = :kaynak" in sql
    assert "qb.is_active IS TRUE" in sql


def test_eski_hat_yalniz_is_active_degisir(kod: str) -> None:
    """ast.unparse bitisik dizgileri birlestirir; UPDATE tek parca gorunur."""
    assert (
        "UPDATE question_bank SET is_active = FALSE, updated_at = now()"
        " WHERE id = ANY(:idler)" in kod
    )


def test_eski_hat_acmadan_once_kapanir(kod: str) -> None:
    yukselt = kod[kod.index("def upgrade") : kod.index("def downgrade")]
    assert yukselt.index("'eski_hat_pasif'") < yukselt.index("'beta_ac'")


# -------------------------------------------------------------- 5. durustluk


def test_human_verified_yazmaz(kod: str) -> None:
    assert "human_verified" not in kod
    assert "auto_judged_high" in kod


def test_is_ai_generated_ve_is_public_dokunulmaz(kod: str) -> None:
    assert not re.search(r"SET[^;]*is_ai_generated", kod)
    assert not re.search(r"SET[^;]*is_public", kod)


def test_toplu_onay_isaretlenir(kod: str) -> None:
    assert "'onay_turu', 'toplu_beta_sahibi'" in kod
    assert "'bireysel_denetim_yapildi', false" in kod


def test_uyum_sinyali_kapinin_bekledigi_anahtar(kod: str) -> None:
    assert "'consensus_2signal_run', true" in kod


# -------------------------------------------------------------- 6. geri alma


def test_eklenen_her_anahtar_downgrade_listesinde(mig, kod: str) -> None:
    eklenen = set(re.findall(r"'(\w+)',\s*(?:true|false|CAST|'toplu)", kod))
    assert eklenen, "eklenen anahtar bulunamadi -- test yanlis yere bakiyor"
    assert eklenen <= set(mig.EK_ANAHTARLAR)


def test_gunluk_onceki_degerleri_ve_islemi_saklar(kod: str) -> None:
    for kolon in (
        "islem",
        "onceki_is_active",
        "onceki_review_status",
        "onceki_quality_review_status",
    ):
        assert kolon in kod, f"gunlukte {kolon} yok -- geri alinamaz"


def test_downgrade_once_acilanlari_kapatir(kod: str) -> None:
    geri = kod[kod.index("def downgrade") :]
    assert "for sira in ('beta_ac', 'eski_hat_pasif')" in geri
    assert "op.drop_table(GUNLUK)" in geri


# -------------------------------------------------------------- 7. sinyaller


def test_sinyaller_bu_kitaba_ait(mig) -> None:
    s = set(mig.SINYALLER)
    assert len(s) == len(mig.SINYALLER) >= 3
    assert any("anahtar" in x for x in s)
    assert any("ikinci_okuma" in x for x in s)


def test_onceki_beta_migrationlariyla_ortak_sinyal_ve_kaynak_yok(mig) -> None:
    for ad in ("0037_geo_beta_onay.py", "0039_fizik_beta_onay.py"):
        eski = _yukle(SURUMLER / ad, "m_" + ad[:4])
        kaynaklar = {k for k, _ in eski.KAYNAKLAR}
        sinyaller = {s for _, ss in eski.KAYNAKLAR for s in ss}
        assert mig.KAYNAK not in kaynaklar
        assert not (set(mig.SINYALLER) & sinyaller)
