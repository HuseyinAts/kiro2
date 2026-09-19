"""ACIL 2023-2024 Geometri ithalinin koruma testleri.

Canli DB istemez; veri setini, konu haritasini, kirpim kutularini ve ithal
script'ini DOSYADAN okur -- CI'da da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU -- 5 sik, dolu cevap, benzersiz hash, gorsel adi.
2. ORTME SOZLESMESI    -- 151 ortulu soru ithale GIRMEZ.
3. KONU BAGLANTISI     -- her kayit GEO-ACL24 agacinda bir dugume baglanir.
4. SOZLESME            -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK           -- cozum uydurulmuyor, ithal PASIF, okunamayan
                          alanlar bayrakla gorunur, kirpim/gorsel tutarli.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import acil_geo_ithal as ag  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
VERI_YOLU = CIKTI / "acil_2324_geometri_metin.json"
HARITA_YOLU = CIKTI / "acil_2324_geometri_konu_haritasi.json"
KUTU_YOLU = CIKTI / "acil_2324_geometri_kirpim_kutulari.json"
ITHAL_YOLU = KOK / "scripts" / "kitap" / "acil_geo_ithal.py"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_SORU = 1730
BEKLENEN_KUTU = 1881
BEKLENEN_ORTULU = 151
BEKLENEN_TEST = 138
BEKLENEN_SEKIL = 1513
BEKLENEN_SIK_GORSEL = 17
BEKLENEN_DIZGI_KUSURU = 36
BEKLENEN_OKUNAMAYAN = 4
BEKLENEN_ANAHTAR_OKUNAMADI = 1
ILK_SAYFA, SON_SAYFA = 5, 446


@pytest.fixture(scope="module")
def satirlar() -> list[dict]:
    return ag.satirlari_bagla(
        json.loads(VERI_YOLU.read_text("utf-8")),
        json.loads(HARITA_YOLU.read_text("utf-8")),
        json.loads(KUTU_YOLU.read_text("utf-8")),
    )


@pytest.fixture(scope="module")
def kayitlar(satirlar: list[dict]) -> list[dict]:
    return [ag.kayit_uret(r) for r in satirlar]


# ------------------------------------------------------- 1. veri seti


def test_soru_sayisi(satirlar: list[dict]) -> None:
    assert len(satirlar) == BEKLENEN_SORU


def test_ortulu_kutular_ithale_girmiyor() -> None:
    kutular = json.loads(KUTU_YOLU.read_text("utf-8"))
    ortulu = [b for b in kutular["kutular"] if b.get("ortulu")]
    assert len(kutular["kutular"]) == BEKLENEN_KUTU
    assert len(ortulu) == BEKLENEN_ORTULU
    veri = json.loads(VERI_YOLU.read_text("utf-8"))
    adlar = {s["gorsel"] for s in veri["sorular"]}
    ortulu_ad = {f"s{b['sayfa']:04d}_{b['sutun']}_{b['sira']}.png" for b in ortulu}
    assert not (adlar & ortulu_ad)
    assert len(adlar) + len(ortulu_ad) == BEKLENEN_KUTU


def test_on_kontrol_temiz(kayitlar: list[dict]) -> None:
    hata = ag._on_kontrol(kayitlar)
    assert not hata, hata[:5]


def test_hash_benzersiz(kayitlar: list[dict]) -> None:
    sayac = Counter(k["soru_hash"] for k in kayitlar)
    ikiz = [h for h, n in sayac.items() if n > 1]
    assert not ikiz, f"{len(ikiz)} tekrarlanan hash"
    assert len({k["id"] for k in kayitlar}) == len(kayitlar)


def test_sayfa_araligi(kayitlar: list[dict]) -> None:
    sayfalar = [k["source_page"] for k in kayitlar]
    assert min(sayfalar) >= ILK_SAYFA
    assert max(sayfalar) <= SON_SAYFA


def test_test_sayisi(satirlar: list[dict]) -> None:
    assert len({s["test"] for s in satirlar}) == BEKLENEN_TEST


# ------------------------------------------------------- 2. konu baglantisi


def test_her_kayit_gereken_onekte(kayitlar: list[dict]) -> None:
    assert all(k["konu_kodu"].startswith(ag.KOD_ONEKI) for k in kayitlar)


def test_konu_kodlari_haritada_tanimli(kayitlar: list[dict]) -> None:
    harita = json.loads(HARITA_YOLU.read_text("utf-8"))
    tanimli = (
        {b["kod"] for b in harita["bolumler"]}
        | {k["kod"] for k in harita["konular"]}
        | {a["kod"] for a in harita["alt_konular"]}
    )
    kullanilan = {k["konu_kodu"] for k in kayitlar}
    assert kullanilan <= tanimli
    # Kok dugume dusen kayit YOK.
    assert ag.GEO_KOK_KODU not in kullanilan


def test_bolum_kodu_konu_kodunun_oneki(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert k["konu_kodu"].startswith(pm["bolum_kodu"])
        assert pm["bolum_kodu"].count("-") == 2


# ------------------------------------------------------- 3. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(ag.KAYNAK_ADI, kayitli_olmali=True)
    assert ag.KAYNAK_ADI in KAYNAK_KAYITLARI
    assert KAYNAK_KAYITLARI[ag.KAYNAK_ADI]["ithal_araci"] == ag.ITHAL_ARACI


def test_kaynak_adi_baska_bir_yazimla_cakismiyor() -> None:
    digerleri = [a for a in KAYNAK_KAYITLARI if a != ag.KAYNAK_ADI]
    assert cakisan_kaynak(ag.KAYNAK_ADI, digerleri) is None


def test_ithal_araci_yolu_gercek() -> None:
    # ITHAL_ARACI backend/ koku icinde goreli yazilir (KAYNAK_KAYITLARI deseni).
    assert (KOK / ag.ITHAL_ARACI).exists()


# ------------------------------------------------------- 4. durustluk


def test_cozum_uydurulmuyor(kayitlar: list[dict]) -> None:
    assert all(k["explanation"] is None for k in kayitlar)
    assert all(
        k["pipeline_metadata"]["cozum_dogrulamasi"] == "yapilmadi_urun_karari"
        for k in kayitlar
    )


def test_ithal_pasif_yaziyor() -> None:
    metin = ITHAL_YOLU.read_text("utf-8")
    assert "is_active" in metin
    # question_bank INSERT'i FALSE, FALSE yaziyor (is_active, is_public).
    assert "now(), now(), TRUE, 'PENDING', FALSE" in metin
    assert "%(konu_id)s, FALSE, FALSE" in metin


def test_cevap_kaynagi_tek(kayitlar: list[dict]) -> None:
    kaynaklar = {k["pipeline_metadata"]["cevap_kaynagi"] for k in kayitlar}
    assert kaynaklar == {ag.CEVAP_KAYNAGI}


def test_kirpim_ve_gorsel_tutarli(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        kutu = k["pipeline_metadata"]["kirpim_kutusu"]
        assert bool(kutu) == bool(k["question_image_url"])
        if kutu:
            assert k["question_image_url"].endswith(
                k["pipeline_metadata"]["kaynak_gorseli"]
            )


def test_kirpim_kutulari_kart_icinde(kayitlar: list[dict]) -> None:
    genislik = ag.KART[2] - ag.KART[0]
    yukseklik = ag.KART[3] - ag.KART[1]
    for k in kayitlar:
        kutu = k["pipeline_metadata"]["kirpim_kutusu"]
        if not kutu:
            continue
        x0, y0, x1, y1 = kutu
        assert 0 <= x0 < x1 <= genislik, k["pipeline_metadata"]["kaynak_gorseli"]
        assert 0 <= y0 < y1 <= yukseklik, k["pipeline_metadata"]["kaynak_gorseli"]


def test_bayrak_sayilari(kayitlar: list[dict]) -> None:
    b: Counter[str] = Counter()
    for k in kayitlar:
        b.update(k["pipeline_metadata"]["bayraklar"])
    assert b["sikler_gorsel"] == BEKLENEN_SIK_GORSEL
    assert b["kaynak_dizgi_kusuru"] == BEKLENEN_DIZGI_KUSURU
    assert b["okunamayan_parca"] == BEKLENEN_OKUNAMAYAN
    assert b["anahtar_sikki_okunamadi"] == BEKLENEN_ANAHTAR_OKUNAMADI
    # Kirpimi olmayan soru yok; dolayisiyla gosterilemez satir da yok.
    assert b["gorsel_yok_sekilli"] == 0
    assert b["gosterilemez_gorsel_sik_kirpimsiz"] == 0


def test_sekilli_soru_sayisi(kayitlar: list[dict]) -> None:
    n = sum(1 for k in kayitlar if k["pipeline_metadata"]["sekil_var"])
    assert n == BEKLENEN_SEKIL


def test_bos_anahtar_sikki_yalniz_belgelenmis_olabilir(kayitlar: list[dict]) -> None:
    """Bos anahtar sikki AFFEDILIR ama yalniz belgeli + kirpimli ise."""
    for k in kayitlar:
        sec = k["secenekler"]
        if (sec.get(k["correct_answer"]) or "").strip():
            continue
        pm = k["pipeline_metadata"]
        assert pm["okunamayan"], k["pipeline_metadata"]["kaynak_gorseli"]
        assert k["question_image_url"], k["pipeline_metadata"]["kaynak_gorseli"]
        assert "anahtar_sikki_okunamadi" in pm["bayraklar"]


def test_ithal_ascii() -> None:
    metin = ITHAL_YOLU.read_text("utf-8")
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"ASCII disi karakter: {disarida}"
