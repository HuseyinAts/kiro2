"""0023_345_beta_onay migration'inin koruma testleri.

Bu dosya ALTI sinif seyi dogrular. Hicbiri canli DB istemez; hepsi
migration modulunun kendisini okur -- yani CI'da da kosar.

1. ZINCIR: revizyon kimligi, onceki revizyon, ad uzunlugu (32 siniri).
2. HEDEF FILTRESI: kapinin KENDI kosullari olan iki bayrak (`sik_bos`,
   `gorsel_yok_sekilli`) hedef sorgusunda DISARIDA. MUTASYON KARSILIGI
   var: filtreyi kaldiran bir surum testi dusurur.
3. GERI ALINABILIRLIK DRIFTI: `_META_EKLE` hangi anahtarlari yaziyorsa
   `EK_ANAHTARLAR` tam olarak onlari icerir. Biri eklenip digeri
   unutulursa downgrade eksik kalirdi; bu test onu yakalar.
4. DURUSTLUK: `human_verified` yazilmaz, `is_ai_generated` alanina
   dokunulmaz. Kapiyi acmanin kolay ama yanlis yolu bunlardi.
5. SOZLESME: uc kaynak adi da `KAYNAK_KAYITLARI` kaydinda birebir var --
   bir harf yanlissa migration sessizce HICBIR SEY yapmazdi.
6. SINYAL DURUSTLUGU: her kitabin sinyal listesi kendine ozgudur, bos
   degildir ve hicbiri `cift_bagimsiz_okuma` (metnin iki kez okunmasi)
   IDDIA ETMEZ -- bu uc kitabin hicbirinde o kanal yok.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI  # noqa: E402

GOC_YOLU = KOK / "alembic" / "versions" / "0023_345_beta_onay.py"


def _modul():
    """Migration'i alembic'i calistirmadan modul olarak yukler."""
    spec = importlib.util.spec_from_file_location("goc_0023", GOC_YOLU)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def goc():
    return _modul()


@pytest.fixture(scope="module")
def kaynak_metni() -> str:
    return GOC_YOLU.read_text(encoding="utf-8")


# --- 1. ZINCIR ---------------------------------------------------------


def test_revizyon_zinciri(goc) -> None:
    assert goc.revision == "0023_345_beta_onay"
    assert goc.down_revision == "0022_biyo345tyt_konu_agaci"


def test_revizyon_adi_32_karakterden_kisa(goc) -> None:
    # 0016 bu sinira takilmisti; ders tekrarlanmasin.
    assert len(goc.revision) <= 32
    assert len(goc.GUNLUK) <= 63  # postgres identifier siniri


def test_dosya_ascii() -> None:
    ham = GOC_YOLU.read_bytes()
    kusurlu = [i for i, b in enumerate(ham) if b > 127]
    assert not kusurlu, f"ASCII disi bayt: {kusurlu[:5]}"


# --- 2. HEDEF FILTRESI (mutasyon karsiligi) ----------------------------


def test_hedef_sorgusu_iki_bayragi_da_disliyor(goc) -> None:
    sql = goc._HEDEF_SQL
    assert "'sik_bos'" in sql
    assert "'gorsel_yok_sekilli'" in sql
    assert sql.count("NOT (") >= 1


def _bayrak_gecer_mi(sql: str, bayraklar: set[str]) -> bool:
    """Hedef sorgusunun bayrak mantigini Python'da taklit eder.

    SQL'i calistirmadan filtrenin ANLAMINI sinar: sorguda hangi bayrak
    adlari 'NOT ... ?' kalibiyla geciyorsa o bayragi tasiyan satir elenir.
    """
    elenen = set(re.findall(r"\? '([a-z_]+)'\)", sql))
    return not (bayraklar & elenen)


def test_bayrakli_satirlar_elenir(goc) -> None:
    sql = goc._HEDEF_SQL
    assert _bayrak_gecer_mi(sql, set()) is True
    assert _bayrak_gecer_mi(sql, {"sik_bos"}) is False
    assert _bayrak_gecer_mi(sql, {"gorsel_yok_sekilli"}) is False
    assert _bayrak_gecer_mi(sql, {"konu_komsudan"}) is True


def test_mutasyon_filtresiz_surum_testi_dusurur() -> None:
    """Filtreyi kaldiran bir surum bu testi GECEMEZ (mutasyon karsiligi)."""
    bozuk = """
    SELECT qb.id FROM question_bank qb
      JOIN question_metadata qm ON qm.id = qb.id
     WHERE qm.source_book = :kaynak
    """
    assert _bayrak_gecer_mi(bozuk, {"sik_bos"}) is True
    assert _bayrak_gecer_mi(bozuk, {"gorsel_yok_sekilli"}) is True


# --- 3. GERI ALINABILIRLIK DRIFTI --------------------------------------


def test_ek_anahtarlar_meta_ekle_ile_ortusuyor(goc) -> None:
    metin = str(goc._META_EKLE)
    yazilan = set(re.findall(r"'([a-z_0-9]+)',\s*(?:true|false|CAST|')", metin))
    yazilan |= set(re.findall(r"'(konsensus_sinyalleri)'", metin))
    beklenen = set(goc.EK_ANAHTARLAR)
    eksik = yazilan - beklenen - {"toplu_beta_sahibi"}
    assert not eksik, f"downgrade'in silmedigi anahtar: {eksik}"
    assert beklenen <= yazilan | {"konsensus_sinyalleri"}


def test_downgrade_gunlugu_dusuruyor(kaynak_metni: str) -> None:
    alt = kaynak_metni.split("def downgrade")[1]
    assert "op.drop_table(GUNLUK)" in alt
    assert "onceki_is_active" in alt
    assert "onceki_quality_review_status" in alt


# --- 4. DURUSTLUK ------------------------------------------------------


def test_human_verified_yazilmaz(kaynak_metni: str) -> None:
    kod = kaynak_metni.split('"""', 2)[2]  # docstring'i disla
    assert "human_verified" not in kod
    assert "auto_judged_high" in kod


def test_is_ai_generated_alanina_dokunulmaz(kaynak_metni: str) -> None:
    kod = kaynak_metni.split('"""', 2)[2]
    assert not re.search(r"is_ai_generated\s*=\s*(TRUE|FALSE|true|false)", kod)


def test_toplu_onay_isaretleniyor(goc) -> None:
    metin = str(goc._META_EKLE)
    assert "'onay_turu', 'toplu_beta_sahibi'" in metin
    assert "'bireysel_denetim_yapildi', false" in metin


# --- 5. SOZLESME -------------------------------------------------------


def test_kaynak_adlari_sozlesmede_kayitli(goc) -> None:
    for kaynak, _ in goc.KAYNAKLAR:
        assert kaynak in KAYNAK_KAYITLARI, (
            f"{kaynak!r} KAYNAK_KAYITLARI'nda yok -- migration sessizce "
            "hicbir sey yapmaz"
        )


def test_uc_kitap_hedefleniyor(goc) -> None:
    adlar = [k for k, _ in goc.KAYNAKLAR]
    assert len(adlar) == 3
    assert len(set(adlar)) == 3
    assert all(a.startswith("345 2025 ") for a in adlar)


# --- 6. SINYAL DURUSTLUGU ----------------------------------------------


def test_her_kitabin_sinyalleri_var_ve_ozgun(goc) -> None:
    listeler = [s for _, s in goc.KAYNAKLAR]
    assert all(len(s) >= 2 for s in listeler)
    assert (
        len({tuple(s) for s in listeler}) == 3
    ), "iki kitap ayni sinyal listesini paylasiyor -- gerekce kopyalanmis"


def test_hicbir_kitap_metin_cift_okumasi_iddia_etmiyor(goc) -> None:
    # 0018'in `cift_bagimsiz_okuma` sinyali METNIN iki kez okunmasiydi;
    # bu uc kitabin hicbirinde o kanal YOK.
    for kaynak, sinyaller in goc.KAYNAKLAR:
        assert (
            "cift_bagimsiz_okuma" not in sinyaller
        ), f"{kaynak}: metin cift okumasi iddia ediliyor ama yok"


def test_anahtar_cift_okumasi_yalniz_iki_kitapta(goc) -> None:
    sahip = {k for k, s in goc.KAYNAKLAR if "anahtar_seridi_cift_okuma" in s}
    assert sahip == {
        "345 2025 TYT-AYT Geometri Soru Bankasi",
        "345 2025 AYT Biyoloji Soru Bankasi",
    }, "TYT biyolojide anahtar cift okumasi YOK; listeye girmemeli"


def test_tyt_biyoloji_dogrulayici_sinyaline_dayaniyor(goc) -> None:
    (sinyaller,) = (
        s for k, s in goc.KAYNAKLAR if k == "345 2025 TYT Biyoloji Soru Bankasi"
    )
    assert "dogrulayici_k1_k11_sifir_kusur" in sinyaller
    assert "manifest_soru_sayisi_ortusmesi" in sinyaller


def test_kapi_anahtari_yaziliyor(goc) -> None:
    # v_safe_for_beta'nin uyum sinyali kosulu bu anahtari arar.
    assert "consensus_2signal_run" in goc.EK_ANAHTARLAR
    assert "'consensus_2signal_run', true" in str(goc._META_EKLE)
