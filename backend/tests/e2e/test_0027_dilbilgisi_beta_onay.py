"""0027_dilbilgisi_beta migration'inin koruma testleri.

Bu dosya ALTI sinif seyi dogrular. Hicbiri canli DB istemez; hepsi
migration modulunun kendisini okur -- yani CI'da da kosar.

1. ZINCIR: revizyon kimligi, onceki revizyon, ad uzunlugu (32 siniri),
   ASCII temizligi.
2. HEDEF FILTRESI: UC bayrak (`sik_bos`, `gorsel_yok_sekilli`,
   `kaynak_dizgi_kusuru`) hedef sorgusunda DISARIDA; ayrica hedef
   `source_book` ile DEGIL `ithal_araci` ile daraltilir -- eski 17 satira
   dokunulmamasinin tek teminati budur. MUTASYON KARSILIGI var.
3. GERI ALINABILIRLIK DRIFTI: `_META_EKLE` hangi anahtarlari yaziyorsa
   `EK_ANAHTARLAR` tam olarak onlari icerir.
4. DURUSTLUK: `human_verified` yazilmaz, `is_ai_generated` ve `is_public`
   alanlarina dokunulmaz.
5. GRUP KAPSAMI: uc dogrulama grubu, ithal script'inin DB'ye yazdigi
   `anahtar_dogrulamasi` degerleriyle birebir ayni yazilir -- bir harf
   yanlissa migration o grup icin sessizce HICBIR SEY yapardi.
6. SINYAL DURUSTLUGU: Ornek grubu anahtar cift okumasi IDDIA ETMEZ
   (o kanalda cevap BIR KEZ okundu), listeler birbirinden farklidir ve
   hicbiri metnin iki kez okundugunu soylemez.
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

from scripts.kitap.dilbilgisi_ithal import (  # noqa: E402
    ANAHTAR_DOGRULAMASI,
    KAYNAK_ADI,
    SATIR_ICI_DOGRULAMASI,
)
from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI  # noqa: E402

GOC_YOLU = KOK / "alembic" / "versions" / "0027_dilbilgisi_beta_onay.py"


def _modul():
    """Migration'i alembic'i calistirmadan modul olarak yukler."""
    spec = importlib.util.spec_from_file_location("goc_0027", GOC_YOLU)
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
    assert goc.revision == "0027_dilbilgisi_beta"
    assert goc.down_revision == "0026_dilbilgisi_kaynak_adi"


def test_revizyon_adi_sinirlarin_icinde(goc) -> None:
    # 0016 bu sinira takilmisti; ders tekrarlanmasin.
    assert len(goc.revision) <= 32
    assert len(goc.GUNLUK) <= 63  # postgres identifier siniri


def test_dosya_ascii() -> None:
    ham = GOC_YOLU.read_bytes()
    kusurlu = [i for i, b in enumerate(ham) if b > 127]
    assert not kusurlu, f"ASCII disi bayt: {kusurlu[:5]}"


# --- 2. HEDEF FILTRESI (mutasyon karsiligi) ----------------------------


def _elenen_bayraklar(sql: str) -> set[str]:
    """Hedef sorgusundaki 'NOT ... ? <bayrak>' kaliplarini toplar."""
    return set(re.findall(r"\?\s*'([a-z_]+)'\)", sql))


def _bayrak_gecer_mi(sql: str, bayraklar: set[str]) -> bool:
    return not (bayraklar & _elenen_bayraklar(sql))


def test_hedef_sorgusu_uc_bayragi_da_disliyor(goc) -> None:
    elenen = _elenen_bayraklar(goc._HEDEF_SQL)
    assert {"sik_bos", "gorsel_yok_sekilli", "kaynak_dizgi_kusuru"} <= elenen


def test_bayrakli_satirlar_elenir(goc) -> None:
    sql = goc._HEDEF_SQL
    assert _bayrak_gecer_mi(sql, set()) is True
    assert _bayrak_gecer_mi(sql, {"sik_bos"}) is False
    assert _bayrak_gecer_mi(sql, {"gorsel_yok_sekilli"}) is False
    assert _bayrak_gecer_mi(sql, {"kaynak_dizgi_kusuru"}) is False
    assert _bayrak_gecer_mi(sql, {"konu_komsudan"}) is True


def test_mutasyon_filtresiz_surum_testi_dusurur() -> None:
    """Filtreyi kaldiran bir surum bu testi GECEMEZ (mutasyon karsiligi)."""
    bozuk = """
    SELECT qb.id FROM question_bank qb
      JOIN question_metadata qm ON qm.id = qb.id
     WHERE qm.source_book = :kaynak
    """
    assert _bayrak_gecer_mi(bozuk, {"kaynak_dizgi_kusuru"}) is True
    assert _bayrak_gecer_mi(bozuk, {"sik_bos"}) is True


def test_hedef_source_book_ile_degil_ithal_araci_ile_daraltilir(goc) -> None:
    """Eski 17 satira dokunulmamasinin TEK teminati budur.

    O satirlar ayni `source_book` degerini tasir ama `ithal_araci`
    TASIMAZ. Filtre source_book'a donerse 17 satir da acilirdi.
    """
    sql = goc._HEDEF_SQL
    assert "'ithal_araci'" in sql
    assert "source_book" not in sql
    assert goc.ITHAL_ARACI == "scripts/kitap/dilbilgisi_ithal.py"


def test_dizgi_kusurlu_satirlar_sayiliyor(kaynak_metni: str) -> None:
    """upgrade(), disarida kalan satir sayisini LOGLAR -- sessiz kalmaz."""
    ust = kaynak_metni.split("def upgrade")[1].split("def downgrade")[0]
    assert "kaynak_dizgi_kusuru" in ust
    assert "pasif kalan" in ust


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


def _kod(kaynak_metni: str) -> str:
    return kaynak_metni.split('"""', 2)[2]


def test_human_verified_yazilmaz(kaynak_metni: str) -> None:
    kod = _kod(kaynak_metni)
    assert "human_verified" not in kod
    assert "auto_judged_high" in kod


def test_is_ai_generated_alanina_dokunulmaz(kaynak_metni: str) -> None:
    kod = _kod(kaynak_metni)
    assert not re.search(r"is_ai_generated\s*=\s*(TRUE|FALSE|true|false)", kod)


def test_is_public_alanina_dokunulmaz(kaynak_metni: str) -> None:
    """Bu depoda hicbir kitap ithali herkese acik degildir."""
    assert "is_public" not in _kod(kaynak_metni)


def test_toplu_onay_isaretleniyor(goc) -> None:
    metin = str(goc._META_EKLE)
    assert "'onay_turu', 'toplu_beta_sahibi'" in metin
    assert "'bireysel_denetim_yapildi', false" in metin


# --- 5. GRUP KAPSAMI ---------------------------------------------------


def test_kaynak_adi_sozlesmede_kayitli() -> None:
    assert KAYNAK_ADI in KAYNAK_KAYITLARI


# FAZ 1 (Konu Testi + OSYM) satirlari PR #283 surumuyle yazildi; o surumde
# sabit "__numara_surekliligi_44_test_0_kusur" ile bitiyordu. PR #284 sabiti
# genel hale getirdi, ama DB'deki ESKI satirlar eski degeri tasimaya devam
# ediyor. Migration uc degeri de bilmek ZORUNDA; bu yuzden tarihsel deger
# burada da capa olarak yazilir.
FAZ1_DEGERI = "anahtar_seridi_cift_okuma_fark_0__numara_surekliligi_44_test_0_kusur"


def test_gruplar_ithal_scriptinin_yazdigi_degerlerle_ayni(goc) -> None:
    """Migration'in grup anahtarlari, DB'de gercekten bulunan degerler.

    Bir harf sapsa migration o grup icin HICBIR SEY yapmaz ve bunu fark
    etmek zor olurdu -- kosum sessizce daha az satir acardi.
    """
    gruplar = {g for g, _ in goc.GRUPLAR}
    assert gruplar == {FAZ1_DEGERI, ANAHTAR_DOGRULAMASI, SATIR_ICI_DOGRULAMASI}


def test_faz1_degeri_faz2_degerinin_uzantisi() -> None:
    """Tarihsel degerin kok kismi bugunku sabitle ayni olmali."""
    kok = ANAHTAR_DOGRULAMASI.split("__")[0]
    assert FAZ1_DEGERI.startswith(kok + "__")
    assert FAZ1_DEGERI != ANAHTAR_DOGRULAMASI


def test_uc_grup_var_ve_tekil(goc) -> None:
    gruplar = [g for g, _ in goc.GRUPLAR]
    assert len(gruplar) == 3
    assert len(set(gruplar)) == 3


# --- 6. SINYAL DURUSTLUGU ----------------------------------------------


def test_her_grubun_sinyalleri_var_ve_ozgun(goc) -> None:
    listeler = [s for _, s in goc.GRUPLAR]
    assert all(len(s) >= 2 for s in listeler)
    assert (
        len({tuple(s) for s in listeler}) == 3
    ), "iki grup ayni sinyal listesini paylasiyor -- gerekce kopyalanmis"


def test_ornek_grubu_anahtar_cift_okumasi_iddia_etmiyor(goc) -> None:
    """Kavrama "Ornek" satirlarinda cevap BIR KEZ okundu.

    Bu testin dusmesi, DB'ye yapilmamis bir dogrulamanin yazildigi
    anlamina gelir -- kampanyanin en onemli durustluk kapisi.
    """
    (sinyaller,) = (s for g, s in goc.GRUPLAR if g == SATIR_ICI_DOGRULAMASI)
    assert not any("cift_okuma" in s for s in sinyaller)
    assert "satir_ici_cevap_ve_cozum_zorunlulugu_k12_kapisi" in sinyaller


def test_cevap_seridi_gruplari_cift_okumayi_iddia_ediyor(goc) -> None:
    for grup, sinyaller in goc.GRUPLAR:
        if grup == SATIR_ICI_DOGRULAMASI:
            continue
        assert any(
            s.startswith("anahtar_seridi_cift_okuma") for s in sinyaller
        ), f"{grup}: serit cift okundu ama sinyal listesinde yok"


def test_hicbir_grup_metin_cift_okumasi_iddia_etmiyor(goc) -> None:
    # Metin TEK okundu (sayfa granulerliginde); 0018'in
    # `cift_bagimsiz_okuma` sinyali bu kitapta YOK.
    for grup, sinyaller in goc.GRUPLAR:
        assert (
            "cift_bagimsiz_okuma" not in sinyaller
        ), f"{grup}: metin cift okumasi iddia ediliyor ama yok"


def test_kapi_anahtari_yaziliyor(goc) -> None:
    # v_safe_for_beta'nin uyum sinyali kosulu bu anahtari arar.
    assert "consensus_2signal_run" in goc.EK_ANAHTARLAR
    assert "'consensus_2signal_run', true" in str(goc._META_EKLE)
