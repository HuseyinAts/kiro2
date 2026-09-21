"""C1CELL 2024 Geometri ithalinin koruma testleri.

Canli DB istemez; veri setini, konu haritasini, kirpim kutularini, cevap
anahtarini ve ithal script'ini DOSYADAN okur -- CI'da da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 1770 soru, 5 sik, dolu cevap, benzersiz hash.
2. YAPISAL GARANTILER   -- 163 birim, ortulu 0, basili numara == birim ici
                           sira, metin/anahtar caprazi.
3. KONU BAGLANTISI      -- her kayit GEO-C1C24 agacinda bir dugume baglanir;
                           bir birim asla iki konuya bolunmez.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK            -- cozum uydurulmuyor, ithal PASIF, kirpim/gorsel
                           tutarli, kutular kartin icinde.
6. MUTASYON             -- kapilarin GERCEKTEN kapi oldugu: veri bilerek
                           bozulur, her bozulmanin yakalandigi olculur.
                           (Bir kapi hic ates etmiyorsa kapi degildir.)
"""

from __future__ import annotations

import copy
import itertools
import json
import sys
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import c1cell_geo_ithal as cg  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
VERI_YOLU = CIKTI / "c1cell_2024_geometri_metin.json"
HARITA_YOLU = CIKTI / "c1cell_2024_geometri_konu_haritasi.json"
KUTU_YOLU = CIKTI / "c1cell_2024_geometri_kirpim_kutulari.json"
ANAHTAR_YOLU = CIKTI / "c1cell_2024_geometri_cevap_anahtari.json"
ITHAL_YOLU = KOK / "scripts" / "kitap" / "c1cell_geo_ithal.py"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_SORU = 1770
BEKLENEN_KUTU = 1770
BEKLENEN_ORTULU = 0
BEKLENEN_BIRIM = 163
BEKLENEN_SEKIL = 1519
BEKLENEN_SIK_GORSEL = 1
BEKLENEN_SIK_TEKRAR = 3
BEKLENEN_BOLUM = 5
BEKLENEN_KONU = 21
ILK_SAYFA, SON_SAYFA = 8, 411


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def veri() -> dict:
    return _oku(VERI_YOLU)


@pytest.fixture(scope="module")
def harita() -> dict:
    return _oku(HARITA_YOLU)


@pytest.fixture(scope="module")
def kutular() -> dict:
    return _oku(KUTU_YOLU)


@pytest.fixture(scope="module")
def anahtar() -> dict:
    return _oku(ANAHTAR_YOLU)


@pytest.fixture(scope="module")
def paket(veri: dict, harita: dict, kutular: dict, anahtar: dict) -> tuple[dict, ...]:
    """Dort girdi tek demette -- mutasyon testinin imzasini kisa tutar."""
    return (veri, harita, kutular, anahtar)


@pytest.fixture(scope="module")
def satirlar(veri: dict, harita: dict, kutular: dict) -> list[dict]:
    return cg.satirlari_bagla(veri, harita, kutular)


@pytest.fixture(scope="module")
def kayitlar(satirlar: list[dict]) -> list[dict]:
    return [cg.kayit_uret(r) for r in satirlar]


# ------------------------------------------------------- 1. veri seti


def test_soru_sayisi(satirlar: list[dict]) -> None:
    assert len(satirlar) == BEKLENEN_SORU


def test_on_kontrol_temiz(kayitlar: list[dict]) -> None:
    hata = cg._on_kontrol(kayitlar)
    assert not hata, hata[:5]


def test_hash_benzersiz(kayitlar: list[dict]) -> None:
    sayac = Counter(k["soru_hash"] for k in kayitlar)
    ikiz = [h for h, n in sayac.items() if n > 1]
    assert not ikiz, f"{len(ikiz)} tekrarlanan hash"
    assert len({k["id"] for k in kayitlar}) == len(kayitlar)


def test_sayfa_araligi(kayitlar: list[dict]) -> None:
    sayfalar = [k["source_page"] for k in kayitlar]
    assert min(sayfalar) == ILK_SAYFA
    assert max(sayfalar) == SON_SAYFA


def test_her_soruda_bes_dolu_sik(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        sec = k["secenekler"]
        assert sorted(sec) == list("ABCDE")
        assert all(sec[h].strip() for h in "ABCDE"), k["id"]


# ------------------------------------------------------- 2. yapisal garantiler


def test_yapisal_kapilar_temiz(veri: dict, anahtar: dict, kutular: dict) -> None:
    hata = cg._yapisal_kapilar(veri, anahtar, kutular)
    assert not hata, hata[:5]


def test_birim_sayisi(kayitlar: list[dict]) -> None:
    birimler = {k["pipeline_metadata"]["birim_no"] for k in kayitlar}
    assert len(birimler) == BEKLENEN_BIRIM


def test_ortulu_soru_yok(kutular: dict) -> None:
    """C1CELL'in ACIL'den ayrildigi nokta: hicbir soru disarida kalmadi."""
    assert len(kutular["kutular"]) == BEKLENEN_KUTU
    assert sum(1 for b in kutular["kutular"] if b.get("ortulu")) == BEKLENEN_ORTULU
    assert kutular.get("ortulu") == BEKLENEN_ORTULU


def test_her_soruda_kirpim_var(kayitlar: list[dict]) -> None:
    eksik = [k["id"] for k in kayitlar if not k["question_image_url"]]
    assert not eksik, f"{len(eksik)} soru kirpimsiz"


def test_basili_numara_birim_ici_siraya_esit(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["soru_no_basili"] == pm["birim_ici_sira"], pm["kaynak_gorseli"]


def test_metin_ve_anahtar_celismiyor(veri: dict, anahtar: dict) -> None:
    """Iki BAGIMSIZ hat (12 ajanli metin, uc kanalli anahtar) ayni seyi diyor."""
    assert len(anahtar["anahtar"]) == BEKLENEN_SORU
    assert not cg._anahtar_caprazi(veri, anahtar)


def test_her_birimin_cevaplari_kesintisiz(anahtar: dict) -> None:
    """Birim ici numaralar 1..N; bir cevap atlanirsa burada gorunur."""
    birim: dict[int, list[int]] = {}
    for a in anahtar["anahtar"]:
        birim.setdefault(int(a["birim"]), []).append(int(a["soru_no"]))
    assert len(birim) == BEKLENEN_BIRIM
    for b, nolar in birim.items():
        assert sorted(nolar) == list(range(1, len(nolar) + 1)), b


# ------------------------------------------------------- 3. konu baglantisi


def test_her_kayit_gereken_onekte(kayitlar: list[dict]) -> None:
    assert all(k["konu_kodu"].startswith(cg.KOD_ONEKI) for k in kayitlar)


def test_konu_kodlari_haritada_tanimli(kayitlar: list[dict], harita: dict) -> None:
    tanimli = {b["kod"] for b in harita["bolumler"]} | {
        k["kod"] for k in harita["konular"]
    }
    kullanilan = {k["konu_kodu"] for k in kayitlar}
    assert kullanilan <= tanimli
    # Kok dugume dusen kayit YOK.
    assert cg.GEO_KOK_KODU not in kullanilan


def test_haritanin_her_konusu_kullaniliyor(kayitlar: list[dict], harita: dict) -> None:
    """Bos konu dugumu = ya harita yanlis ya atama; ikisi de sessiz kalmasin."""
    assert len(harita["bolumler"]) == BEKLENEN_BOLUM
    assert len(harita["konular"]) == BEKLENEN_KONU
    kullanilan = {k["konu_kodu"] for k in kayitlar}
    bos = {k["kod"] for k in harita["konular"]} - kullanilan
    assert not bos, f"soru almayan konu: {sorted(bos)}"


def test_bir_birim_tek_konuya_baglanir(satirlar: list[dict]) -> None:
    birim_konu: dict[int, set[str]] = {}
    for s in satirlar:
        birim_konu.setdefault(int(s["birim"]), set()).add(s["konu_kodu"])
    bolunmus = {b: k for b, k in birim_konu.items() if len(k) != 1}
    assert not bolunmus, f"iki konuya bolunen birim: {bolunmus}"


def test_konu_sayfa_araliklari_cakismiyor(harita: dict) -> None:
    araliklar = sorted(
        (k["bas_sayfa"], k["son_sayfa"], k["kod"]) for k in harita["konular"]
    )
    for (_b1, s1, k1), (b2, _s2, k2) in itertools.pairwise(araliklar):
        assert s1 < b2, f"{k1} ve {k2} sayfa araliklari cakisiyor"


def test_bolum_kodu_konu_kodunun_oneki(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert k["konu_kodu"].startswith(pm["bolum_kodu"])
        assert pm["bolum_kodu"].count("-") == 2


# ------------------------------------------------------- 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(cg.KAYNAK_ADI, kayitli_olmali=True)
    assert cg.KAYNAK_ADI in KAYNAK_KAYITLARI
    assert KAYNAK_KAYITLARI[cg.KAYNAK_ADI]["ithal_araci"] == cg.ITHAL_ARACI


def test_kaynak_adi_baska_bir_yazimla_cakismiyor() -> None:
    digerleri = [a for a in KAYNAK_KAYITLARI if a != cg.KAYNAK_ADI]
    assert cakisan_kaynak(cg.KAYNAK_ADI, digerleri) is None


def test_ithal_araci_yolu_gercek() -> None:
    # ITHAL_ARACI backend/ koku icinde goreli yazilir (KAYNAK_KAYITLARI deseni).
    assert (KOK / cg.ITHAL_ARACI).exists()


# ------------------------------------------------------- 5. durustluk


def test_cozum_uydurulmuyor(kayitlar: list[dict]) -> None:
    assert all(k["explanation"] is None for k in kayitlar)
    assert all(
        k["pipeline_metadata"]["cozum_dogrulamasi"] == "yapilmadi_urun_karari"
        for k in kayitlar
    )


def test_ithal_pasif_yaziyor() -> None:
    metin = ITHAL_YOLU.read_text("utf-8")
    # question_bank INSERT'i FALSE, FALSE yaziyor (is_active, is_public).
    assert "now(), now(), TRUE, 'PENDING', FALSE" in metin
    assert "%(konu_id)s, FALSE, FALSE" in metin
    assert "'PENDING')" in metin  # question_metadata.pedagogical_status


def test_cevap_kaynagi_tek(kayitlar: list[dict]) -> None:
    kaynaklar = {k["pipeline_metadata"]["cevap_kaynagi"] for k in kayitlar}
    assert kaynaklar == {cg.CEVAP_KAYNAGI}


def test_kirpim_ve_gorsel_tutarli(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        kutu = k["pipeline_metadata"]["kirpim_kutusu"]
        assert bool(kutu) == bool(k["question_image_url"])
        assert k["question_image_url"].endswith(
            k["pipeline_metadata"]["kaynak_gorseli"]
        )


def test_kirpim_kutulari_kart_icinde(kayitlar: list[dict]) -> None:
    genislik = cg.KART[2] - cg.KART[0]
    yukseklik = cg.KART[3] - cg.KART[1]
    for k in kayitlar:
        x0, y0, x1, y1 = k["pipeline_metadata"]["kirpim_kutusu"]
        ad = k["pipeline_metadata"]["kaynak_gorseli"]
        assert 0 <= x0 < x1 <= genislik, ad
        assert 0 <= y0 < y1 <= yukseklik, ad


def test_bayrak_sayilari(kayitlar: list[dict]) -> None:
    b: Counter[str] = Counter()
    for k in kayitlar:
        b.update(k["pipeline_metadata"]["bayraklar"])
    assert b["sikler_gorsel"] == BEKLENEN_SIK_GORSEL
    assert b["sik_tekrar"] == BEKLENEN_SIK_TEKRAR
    # Kirpimsiz soru yok; dolayisiyla gosterilemez satir da yok.
    assert b["gorsel_yok_sekilli"] == 0
    assert b["gosterilemez_gorsel_sik_kirpimsiz"] == 0
    assert b["anahtar_sikki_okunamadi"] == 0


def test_sekilli_soru_sayisi(kayitlar: list[dict]) -> None:
    n = sum(1 for k in kayitlar if k["pipeline_metadata"]["sekil_var"])
    assert n == BEKLENEN_SEKIL


def test_gorsel_sikli_soru_isaretli(kayitlar: list[dict]) -> None:
    """Siklari sekil olan tek soru: metin uydurulmadi, bayrakli ve kirpimli."""
    gorsel = [k for k in kayitlar if k["pipeline_metadata"]["sikler_gorsel"]]
    assert len(gorsel) == BEKLENEN_SIK_GORSEL
    for k in gorsel:
        assert "sikler_gorsel" in k["pipeline_metadata"]["bayraklar"]
        assert k["question_image_url"], "gorsel sikli soru kirpimsiz olamaz"


def test_ithal_ascii() -> None:
    metin = ITHAL_YOLU.read_text("utf-8")
    disarida = sorted({c for c in metin if ord(c) > 127})
    assert not disarida, f"ASCII disi karakter: {disarida}"


# ------------------------------------------------------- 6. mutasyon


def _bozuk_yakalandi_mi(
    paket: tuple[dict, ...],
    boz: Callable[[dict, dict, dict, dict], None],
) -> bool:
    """Veriyi bozar ve HERHANGI bir kapinin ates edip etmedigini dondurur."""
    v, h, k, a = (copy.deepcopy(x) for x in paket)
    boz(v, h, k, a)
    try:
        if cg._yapisal_kapilar(v, a, k):
            return True
        kayitlar = [cg.kayit_uret(r) for r in cg.satirlari_bagla(v, h, k)]
        return bool(cg._on_kontrol(kayitlar))
    except (ValueError, KeyError):
        # satirlari_bagla / birim_konu_haritasi da birer kapidir.
        return True


BOZMALAR: list[tuple[str, Callable[[dict, dict, dict, dict], None]]] = [
    ("soru silindi", lambda v, h, k, a: v["sorular"].pop(5)),
    ("kutu silindi", lambda v, h, k, a: k["kutular"].pop(2)),
    ("kutu ortulu isaretlendi", lambda v, h, k, a: k["kutular"][2].update(ortulu=True)),
    (
        "metin cevabi degisti",
        lambda v, h, k, a: v["sorular"][7].update(
            cevap="A" if v["sorular"][7]["cevap"] != "A" else "B"
        ),
    ),
    (
        "anahtar cevabi degisti",
        lambda v, h, k, a: a["anahtar"][3].update(
            cevap="A" if a["anahtar"][3]["cevap"] != "A" else "B"
        ),
    ),
    (
        "basili numara kaydi",
        lambda v, h, k, a: v["sorular"][9].update(soru_no_basili=99),
    ),
    ("birim iki konuya yayildi", lambda v, h, k, a: v["sorular"][0].update(sayfa=200)),
    (
        "sayfa harita disina cikti",
        lambda v, h, k, a: v["sorular"][0].update(sayfa=9999),
    ),
    ("govde bosaldi", lambda v, h, k, a: v["sorular"][11].update(govde="   ")),
    ("sik anahtari eksildi", lambda v, h, k, a: v["sorular"][12]["sikler"].pop("D")),
    (
        "anahtar sikki bosaldi",
        lambda v, h, k, a: v["sorular"][13]["sikler"].update(
            {v["sorular"][13]["cevap"]: ""}
        ),
    ),
    (
        "ayni soru iki kez",
        lambda v, h, k, a: v["sorular"].__setitem__(
            20, copy.deepcopy(v["sorular"][19])
        ),
    ),
    (
        "konu kodu oneki bozuldu",
        lambda v, h, k, a: h["konular"][0].update(kod="XXX-01"),
    ),
]


@pytest.mark.parametrize(("ad", "boz"), BOZMALAR, ids=[b[0] for b in BOZMALAR])
def test_mutasyon_kapiya_takiliyor(
    ad: str,
    boz: Callable[[dict, dict, dict, dict], None],
    paket: tuple[dict, ...],
) -> None:
    """Her bozulma en az bir kapiyi tetiklemeli.

    Bu testler kapilarin GERCEKTEN kapi oldugunu olcer. Bir bozulma
    sessizce gecerse kapi yoktur; "kontrol ediyorum" demek ile kontrol
    etmek arasindaki fark budur.
    """
    assert _bozuk_yakalandi_mi(paket, boz), f"{ad}: hicbir kapi ates etmedi"
