"""Orijinal 2024 TYT-AYT Geometri ithalinin kapilari.

Canli DB istemez; veri setini, konu/birim haritasini, kirpim kutularini,
cevap anahtarini ve ithal script'ini DOSYADAN okur -- CI'da da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 2072 soru, 5 sik, dolu cevap, benzersiz hash.
2. YAPISAL GARANTILER   -- 231 birim, 2072 kutu, basili numara == birim ici
                           sira, metin kanalina cevap sizmamis.
3. KONU BAGLANTISI      -- her kayit GEO-ORJ24 agacinda bir dugume baglanir;
                           bir birim asla iki konuya bolunmez.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz; agac
                           migration'i ile ayni kodlar.
5. DURUSTLUK            -- cozum uydurulmuyor, ithal PASIF, kirpim/gorsel
                           tutarli, kutular kartin icinde.
6. MUTASYON             -- kapilarin GERCEKTEN kapi oldugu: veri bilerek
                           bozulur, her bozulmanin yakalandigi olculur.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import orijinal_geo_ithal as og  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
VERI_YOLU = CIKTI / "orijinal_2024_geometri_metin.json"
HARITA_YOLU = CIKTI / "orijinal_2024_geometri_konu_haritasi.json"
BIRIM_YOLU = CIKTI / "orijinal_2024_geometri_birim_haritasi.json"
KUTU_YOLU = CIKTI / "orijinal_2024_geometri_kirpim_kutulari.json"
ANAHTAR_YOLU = CIKTI / "orijinal_2024_geometri_cevap_anahtari.json"
ITHAL_YOLU = KOK / "scripts" / "kitap" / "orijinal_geo_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0040_orijinal_geo_konu_agaci.py"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_SORU = 2072
BEKLENEN_BIRIM = 231
BEKLENEN_SEKIL = 1784
BEKLENEN_SIK_GORSEL = 4
BEKLENEN_SIK_TEKRAR = 11
BEKLENEN_KUSUR = 101
BEKLENEN_BOLUM = 5
BEKLENEN_KONU = 35
GOZLE_CEVAP, MAKINE_CEVAP = 823, 1249
ILK_SAYFA, SON_SAYFA = 8, 432
KART_G, KART_Y = 734, 968


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def veri() -> dict:
    return _oku(VERI_YOLU)


@pytest.fixture(scope="module")
def harita() -> dict:
    return _oku(HARITA_YOLU)


@pytest.fixture(scope="module")
def birim() -> dict:
    return _oku(BIRIM_YOLU)


@pytest.fixture(scope="module")
def kutular() -> dict:
    return _oku(KUTU_YOLU)


@pytest.fixture(scope="module")
def anahtar() -> dict:
    return _oku(ANAHTAR_YOLU)


@pytest.fixture(scope="module")
def paket(
    veri: dict, harita: dict, birim: dict, kutular: dict, anahtar: dict
) -> tuple[dict, ...]:
    return (veri, harita, birim, kutular, anahtar)


@pytest.fixture(scope="module")
def kayitlar(paket: tuple[dict, ...]) -> list[dict]:
    v, h, b, k, a = paket
    return [og.kayit_uret(r) for r in og.satirlari_bagla(v, b, h, k, a)]


@pytest.fixture(scope="module")
def agac() -> object:
    spec = importlib.util.spec_from_file_location("agac0040", AGAC_YOLU)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# ------------------------------------------------- 1. veri seti butunlugu


def test_soru_sayisi_ve_kayit_sayisi(veri: dict, kayitlar: list[dict]) -> None:
    assert veri["soru_sayisi"] == len(veri["sorular"]) == BEKLENEN_SORU
    assert len(kayitlar) == BEKLENEN_SORU


def test_her_kayitta_bes_sik_ve_dolu_cevap(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        assert set(k["secenekler"]) == set("ABCDE"), k["id"]
        assert k["correct_answer"] in set("ABCDE"), k["id"]
        assert str(k["secenekler"][k["correct_answer"]]).strip(), k["id"]
        assert k["question_text"].strip()


def test_hashler_benzersiz(kayitlar: list[dict]) -> None:
    assert len({k["soru_hash"] for k in kayitlar}) == BEKLENEN_SORU
    assert len({k["id"] for k in kayitlar}) == BEKLENEN_SORU


def test_sayfa_araligi_kitabin_icinde(kayitlar: list[dict]) -> None:
    sayfalar = [k["source_page"] for k in kayitlar]
    assert min(sayfalar) == ILK_SAYFA
    assert max(sayfalar) == SON_SAYFA


# ------------------------------------------------- 2. yapisal garantiler


def test_yapisal_kapilar_temiz(paket: tuple[dict, ...]) -> None:
    v, _h, b, k, a = paket
    assert og._yapisal_kapilar(v, b, k, a) == []


def test_on_kontrol_temiz(kayitlar: list[dict]) -> None:
    assert og._on_kontrol(kayitlar) == []


def test_birim_sayisi_ve_ici_sira(kayitlar: list[dict]) -> None:
    birimler = Counter(k["pipeline_metadata"]["birim_kodu"] for k in kayitlar)
    assert len(birimler) == BEKLENEN_BIRIM
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["soru_no_basili"] == pm["birim_ici_sira"], k["id"]


def test_metin_kanali_cevap_tasimiyor(veri: dict) -> None:
    """Transkripsiyon anahtardan bagimsiz kanal; cevap ithalde birlesir."""
    yasak = {"cevap", "correct_answer", "answer"}
    assert not any(set(s) & yasak for s in veri["sorular"])


def test_cevap_kanali_dagilimi(kayitlar: list[dict]) -> None:
    sayim = Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar)
    assert sayim == {"gozle": GOZLE_CEVAP, "makine": MAKINE_CEVAP}


# ------------------------------------------------- 3. konu baglantisi


def test_her_kayit_bir_konuya_bagli(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        assert k["konu_kodu"].startswith(og.KOD_ONEKI), k["id"]
    assert len({k["konu_kodu"] for k in kayitlar}) == BEKLENEN_KONU


def test_bir_birim_iki_konuya_bolunmuyor(kayitlar: list[dict]) -> None:
    konu: dict[str, set[str]] = {}
    for k in kayitlar:
        konu.setdefault(k["pipeline_metadata"]["birim_kodu"], set()).add(k["konu_kodu"])
    bolunen = {b: sorted(v) for b, v in konu.items() if len(v) != 1}
    assert not bolunen, bolunen


def test_konu_kodlari_agac_migrationi_ile_ayni(
    kayitlar: list[dict], agac: object
) -> None:
    kodlar = {k["konu_kodu"] for k in kayitlar}
    agac_kodlari = {kod for _ust, kod, _ad in agac.KONULAR}  # type: ignore[attr-defined]
    assert kodlar <= agac_kodlari
    assert len(agac.BOLUMLER) == BEKLENEN_BOLUM  # type: ignore[attr-defined]
    assert len(agac.KONULAR) == BEKLENEN_KONU  # type: ignore[attr-defined]


def test_agac_kodlari_konu_haritasiyla_ayni(agac: object, harita: dict) -> None:
    """Migration adlari UYDURULMADI: haritadan uretildi."""
    harita_konu = {(k["ust"], k["kod"], k["ad"]) for k in harita["konular"]}
    assert set(agac.KONULAR) == harita_konu  # type: ignore[attr-defined]
    harita_bolum = {(b["kod"], b["ad"]) for b in harita["bolumler"]}
    assert set(agac.BOLUMLER) == harita_bolum  # type: ignore[attr-defined]


# ------------------------------------------------------------ 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(og.KAYNAK_ADI, kayitli_olmali=True)
    assert cakisan_kaynak(og.KAYNAK_ADI, list(KAYNAK_KAYITLARI)) is None
    kayit = KAYNAK_KAYITLARI[og.KAYNAK_ADI]
    assert kayit["onek"] == og.ONEK
    assert kayit["ithal_araci"] == og.ITHAL_ARACI


def test_ithal_araci_kaynak_dosyasi_ascii() -> None:
    for yol in (ITHAL_YOLU, AGAC_YOLU):
        metin = yol.read_text("utf-8")
        disarida = sorted({c for c in metin if ord(c) > 127})
        assert not disarida, f"{yol.name}: {disarida}"


# ----------------------------------------------------------- 5. durustluk


def test_ithal_pasif_sozlesmesi() -> None:
    """is_active FALSE, is_public FALSE, is_ai_generated TRUE, PENDING."""
    kolon = og._QB.split("VALUES")[0]
    deger = og._QB.split("VALUES")[1]
    assert "is_active, is_public" in " ".join(kolon.split())
    assert "FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE" in deger
    assert "NULL, %(question_image_url)s" in og._QC  # explanation NULL
    assert "'PENDING'" in og._QM  # pedagogical_status


def test_cozum_uydurulmuyor(kayitlar: list[dict]) -> None:
    assert all(k["explanation"] is None for k in kayitlar)
    assert "cozulmedi" in og.URETIM_NOTU


def test_gorsel_ve_kutu_tutarli(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        kutu = k["pipeline_metadata"]["kirpim_kutusu"]
        assert kutu, k["id"]
        assert k["question_image_url"].startswith(f"/static/crops/{og.CROP_ONEK}/")
        x0, y0, x1, y1 = kutu
        assert 0 <= x0 < x1 <= KART_G, k["id"]
        assert 0 <= y0 < y1 <= KART_Y, k["id"]


def test_olculen_bayrak_capalari(kayitlar: list[dict]) -> None:
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    assert bayrak["sikler_gorsel"] == BEKLENEN_SIK_GORSEL
    assert bayrak["sik_tekrar"] == BEKLENEN_SIK_TEKRAR
    assert bayrak["kaynak_kusuru"] == BEKLENEN_KUSUR
    assert bayrak["gorsel_yok_sekilli"] == 0
    sekilli = sum(1 for k in kayitlar if k["pipeline_metadata"]["sekil_var"])
    assert sekilli == BEKLENEN_SEKIL


def test_sinav_turu_olculmedigi_yazili(kayitlar: list[dict]) -> None:
    for k in kayitlar[:50]:
        assert k["pipeline_metadata"]["sinav_turu_kaynagi"].startswith("olculmedi")


# ------------------------------------------------------------ 6. mutasyon


def _m_soru_sil(p: tuple[dict, ...]) -> tuple[dict, ...]:
    v, h, b, k, a = p
    del v["sorular"][100]
    v["soru_sayisi"] = len(v["sorular"])
    return (v, h, b, k, a)


def _m_kutu_sil(p: tuple[dict, ...]) -> tuple[dict, ...]:
    v, h, b, k, a = p
    del k["kutular"][100]
    return (v, h, b, k, a)


def _m_anahtar_sil(p: tuple[dict, ...]) -> tuple[dict, ...]:
    v, h, b, k, a = p
    del a["cevaplar"][100]
    return (v, h, b, k, a)


def _m_cevap_sizdi(p: tuple[dict, ...]) -> tuple[dict, ...]:
    v, h, b, k, a = p
    v["sorular"][0]["cevap"] = "D"
    return (v, h, b, k, a)


def _m_birim_sil(p: tuple[dict, ...]) -> tuple[dict, ...]:
    v, h, b, k, a = p
    del b["birimler"][10]
    return (v, h, b, k, a)


YAPISAL_MUTASYONLAR: list[tuple[str, Callable]] = [
    ("metinden soru silindi", _m_soru_sil),
    ("kirpim kutusu silindi", _m_kutu_sil),
    ("anahtardan cevap silindi", _m_anahtar_sil),
    ("metin kanalina cevap sizdi", _m_cevap_sizdi),
    ("birim haritasindan birim silindi", _m_birim_sil),
]


@pytest.mark.parametrize(("ad", "bozucu"), YAPISAL_MUTASYONLAR)
def test_yapisal_kapi_mutasyonu_yakaliyor(
    ad: str, bozucu: Callable, paket: tuple[dict, ...]
) -> None:
    v, _h, b, k, a = bozucu(copy.deepcopy(paket))
    assert og._yapisal_kapilar(v, b, k, a), ad


def _kayit_bozup_kontrol(paket: tuple[dict, ...], bozucu: Callable) -> list[str]:
    v, h, b, k, a = copy.deepcopy(paket)
    satir = og.satirlari_bagla(v, b, h, k, a)
    bozucu(satir)
    return og._on_kontrol([og.kayit_uret(r) for r in satir])


def test_on_kontrol_bos_sik_yakaliyor(paket: tuple[dict, ...]) -> None:
    def boz(satir: list[dict]) -> None:
        satir[0]["sikler"]["C"] = ""
        satir[0]["cevap"] = "C"

    assert _kayit_bozup_kontrol(paket, boz)


def test_on_kontrol_yanlis_konu_kodu_yakaliyor(paket: tuple[dict, ...]) -> None:
    def boz(satir: list[dict]) -> None:
        satir[0]["konu_kodu"] = "GEO-U1-01"

    assert _kayit_bozup_kontrol(paket, boz)


def test_on_kontrol_kirpimsiz_satir_yakaliyor(paket: tuple[dict, ...]) -> None:
    def boz(satir: list[dict]) -> None:
        satir[0]["kirpim_kutusu"] = None

    assert _kayit_bozup_kontrol(paket, boz)


def test_on_kontrol_gecersiz_cevap_yakaliyor(paket: tuple[dict, ...]) -> None:
    def boz(satir: list[dict]) -> None:
        satir[0]["cevap"] = "F"

    assert _kayit_bozup_kontrol(paket, boz)


def test_birim_sirasi_bozulunca_duruyor(paket: tuple[dict, ...]) -> None:
    """Birim ici soru sayisi birim haritasiyla tutmazsa baglama DURMALI."""
    v, h, b, k, a = copy.deepcopy(paket)
    b["birimler"][0]["soru_sayisi"] += 1
    with pytest.raises(ValueError, match="birim ici"):
        og.satirlari_bagla(v, b, h, k, a)


def test_konu_araligi_celisince_duruyor(paket: tuple[dict, ...]) -> None:
    """Birim konusu ile sayfa araligi celisirse baglama DURMALI."""
    v, h, b, k, a = copy.deepcopy(paket)
    b["birimler"][0]["konu"] = "GEO-ORJ24-B05-05"
    with pytest.raises(ValueError, match="sayfa araligiyla"):
        og.satirlari_bagla(v, b, h, k, a)
