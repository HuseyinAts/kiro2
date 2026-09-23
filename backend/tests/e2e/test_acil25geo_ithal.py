"""ACIL 2025 KURS TYT-AYT Geometri ithalinin kapilari.

Canli DB istemez; veri setini, konu/birim haritasini, kirpim kutularini,
cevap anahtarini, ortme olcumunu ve ithal script'ini DOSYADAN okur -- CI'da
koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 1948 kayit, 5 sik, dolu cevap, benzersiz id.
2. YAPISAL GARANTILER   -- 429 birim, basili numara == birim ici sira,
                           metin kanalina cevap sizmamis.
3. KONU BAGLANTISI      -- her kayit GEO-ACL25 agacinda; konu ogrenme alt
                           konuya, test konuya; migration ile ayni kodlar.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK            -- cozum yok, ithal PASIF, bayrak capalari, sekil ikizi.
6. MUTASYON             -- kapilar bilerek bozulan veride GERCEKTEN duruyor.
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

from scripts.kitap import acil25_geo_ithal as ag  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
YOLLAR = {
    "veri": CIKTI / "acil_2025_geometri_metin.json",
    "harita": CIKTI / "acil_2025_geometri_konu_haritasi.json",
    "birim": CIKTI / "acil_2025_geometri_birim_haritasi.json",
    "kutular": CIKTI / "acil_2025_geometri_kirpim_kutulari.json",
    "anahtar": CIKTI / "acil_2025_geometri_cevap_anahtari.json",
    "ortme": CIKTI / "acil_2025_geometri_ortme_olcumu.json",
}
ITHAL_YOLU = KOK / "scripts" / "kitap" / "acil25_geo_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0041_acil25_geo_konu_agaci.py"
ARAC_YOLLARI = [
    ITHAL_YOLU,
    AGAC_YOLU,
    KOK / "scripts" / "kitap" / "acil25_geo_kutu.py",
    KOK / "scripts" / "kitap" / "acil25_geo_kirp.py",
    KOK / "scripts" / "kitap" / "acil25_geo_metin_harness.py",
]

BEKLENEN_SORU = 1948
BEKLENEN_BIRIM = 429
BEKLENEN_DUGUM = 348  # 33 konu + 315 alt konu, hepsi en az bir soru tasiyor
BAYRAKLAR = {
    "sekil_ikizi": 2,
    "okuyucu_diski_ortme": 82,
    "kaynak_kusuru": 83,
    "sik_okunamadi": 4,
    "sik_tekrar": 15,
    "sikler_gorsel": 10,
}
CEVAP_KANALI = {"uc_okuma": 1915, "iki_okuma+piksel_BD": 31, "goz_zoom": 2}
BASILI_ILK, BASILI_SON = 3, 394
KART_G, KART_Y = 734, 968


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def paket() -> dict[str, dict]:
    return {ad: _oku(y) for ad, y in YOLLAR.items()}


def _bagla(p: dict[str, dict]) -> list[dict]:
    return ag.satirlari_bagla(
        p["veri"], p["birim"], p["harita"], p["kutular"], p["anahtar"], ortme=p["ortme"]
    )


@pytest.fixture(scope="module")
def kayitlar(paket: dict[str, dict]) -> list[dict]:
    k = [ag.kayit_uret(r) for r in _bagla(paket)]
    ag.sekil_ikizleri(k)
    return k


@pytest.fixture(scope="module")
def agac() -> object:
    spec = importlib.util.spec_from_file_location("agac0041", AGAC_YOLU)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


# ------------------------------------------------- 1. veri seti butunlugu


def test_kayit_sayisi(kayitlar: list[dict]) -> None:
    assert len(kayitlar) == BEKLENEN_SORU


def test_her_kayitta_bes_sik_ve_dolu_cevap(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        assert set(k["secenekler"]) == set("ABCDE"), k["id"]
        assert k["correct_answer"] in set("ABCDE"), k["id"]
        assert k["secenekler"][k["correct_answer"]] != ag.SIK_OKUNAMADI, k["id"]
        assert k["question_text"].strip()


def test_idler_benzersiz_hashler_yalniz_ikizde_tekrar(kayitlar: list[dict]) -> None:
    assert len({k["id"] for k in kayitlar}) == BEKLENEN_SORU
    tekrar = [h for h, n in Counter(k["soru_hash"] for k in kayitlar).items() if n > 1]
    assert len(tekrar) == 1


def test_basili_sayfa_araligi(kayitlar: list[dict]) -> None:
    s = [k["source_page"] for k in kayitlar]
    assert min(s) == BASILI_ILK and max(s) == BASILI_SON
    for k in kayitlar[:100]:
        pm = k["pipeline_metadata"]
        assert pm["basili_sayfa"] == pm["sayfa_dosya_no"] - ag.SAYFA_OFSETI


# ------------------------------------------------- 2. yapisal garantiler


def test_yapisal_kapilar_temiz(paket: dict[str, dict]) -> None:
    assert (
        ag._yapisal_kapilar(
            paket["veri"], paket["birim"], paket["kutular"], paket["anahtar"]
        )
        == []
    )


def test_on_kontrol_temiz(kayitlar: list[dict]) -> None:
    assert ag._on_kontrol(kayitlar) == []


def test_birim_ve_ici_sira(kayitlar: list[dict]) -> None:
    assert (
        len({k["pipeline_metadata"]["birim_kodu"] for k in kayitlar}) == BEKLENEN_BIRIM
    )
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["soru_no_basili"] == pm["birim_ici_sira"], k["id"]


def test_cevap_kanali_dagilimi(kayitlar: list[dict]) -> None:
    assert (
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar))
        == CEVAP_KANALI
    )


# ------------------------------------------------- 3. konu baglantisi


def test_konu_ogrenme_alt_konuya_test_konuya(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        if pm["birim_turu"] == "konu_ogrenme":
            assert pm["konu_eslesme_duzeyi"] == "alt_konu"
            assert k["konu_kodu"].startswith(pm["ana_konu_kodu"] + "-A"), k["id"]
        else:
            assert pm["konu_eslesme_duzeyi"] == "konu"
            assert k["konu_kodu"] == pm["ana_konu_kodu"], k["id"]


def test_bir_birim_tek_dugume_baglanir(kayitlar: list[dict]) -> None:
    dugum: dict[str, set[str]] = {}
    for k in kayitlar:
        dugum.setdefault(k["pipeline_metadata"]["birim_kodu"], set()).add(
            k["konu_kodu"]
        )
    assert all(len(v) == 1 for v in dugum.values())


def test_konu_kodlari_migration_ile_ayni(
    kayitlar: list[dict], agac: object, paket: dict
) -> None:
    konular = set(agac.KONULAR)  # type: ignore[attr-defined]
    altlar = set(agac.ALT_KONULAR)  # type: ignore[attr-defined]
    h = paket["harita"]
    assert konular == {(k["kod"], k["ad"]) for k in h["konular"]}
    assert altlar == {(a["ust"], a["kod"], a["ad"]) for a in h["alt_konular"]}
    agac_kodlari = {k for k, _ in konular} | {k for _, k, _ in altlar}
    bagli = {k["konu_kodu"] for k in kayitlar}
    assert bagli <= agac_kodlari
    assert len(bagli) == len(agac_kodlari) == BEKLENEN_DUGUM


def test_migration_zinciri(agac: object) -> None:
    assert agac.down_revision == "0040_orijinalgeo_agac"  # type: ignore[attr-defined]
    assert len(agac.revision) <= 32  # type: ignore[attr-defined]
    assert agac.KOD_ONEKI == ag.KOD_ONEKI  # type: ignore[attr-defined]


# ------------------------------------------------------------ 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(ag.KAYNAK_ADI, kayitli_olmali=True)
    assert cakisan_kaynak(ag.KAYNAK_ADI, list(KAYNAK_KAYITLARI)) is None
    kayit = KAYNAK_KAYITLARI[ag.KAYNAK_ADI]
    assert kayit["onek"] == ag.ONEK
    assert kayit["ithal_araci"] == ag.ITHAL_ARACI


def test_iki_acil_baskisi_ayri_kaynak() -> None:
    """2023-2024 ve 2025 KURS farkli kitaplar (farkli ISBN); adlar cakismamali."""
    assert "ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi" in KAYNAK_KAYITLARI
    assert (
        KAYNAK_KAYITLARI[ag.KAYNAK_ADI]["onek"]
        != KAYNAK_KAYITLARI["ACIL 2023-2024 TYT-AYT Geometri Soru Bankasi"]["onek"]
    )


@pytest.mark.parametrize("yol", ARAC_YOLLARI, ids=lambda p: p.name)
def test_arac_kaynak_dosyalari_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name


# ----------------------------------------------------------- 5. durustluk


def test_ithal_pasif_sozlesmesi() -> None:
    kolon, deger = ag._QB.split("VALUES")
    assert "is_active, is_public" in " ".join(kolon.split())
    assert "FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE" in deger
    assert "NULL, %(question_image_url)s" in ag._QC
    assert "'PENDING'" in ag._QM


def test_cozum_uydurulmuyor(kayitlar: list[dict]) -> None:
    assert all(k["explanation"] is None for k in kayitlar)
    assert "cozulmedi" in ag.URETIM_NOTU


def test_gorsel_ve_kutu_tutarli(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        x0, y0, x1, y1 = k["pipeline_metadata"]["kirpim_kutusu"]
        assert 0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y, k["id"]
        assert k["question_image_url"] == (
            f"/static/crops/{ag.CROP_ONEK}/{k['pipeline_metadata']['kaynak_gorseli']}"
        )


def test_olculen_bayrak_capalari(kayitlar: list[dict]) -> None:
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    assert dict(bayrak) == BAYRAKLAR


def test_sekil_ikizleri_birbirini_gosteriyor(kayitlar: list[dict]) -> None:
    ikiz = [k for k in kayitlar if "sekil_ikizi" in k["pipeline_metadata"]["bayraklar"]]
    assert len(ikiz) == 2
    a, b = (k["pipeline_metadata"] for k in ikiz)
    assert a["sekil_ikizi_ile"] == [b["kaynak_gorseli"]]
    assert b["sekil_ikizi_ile"] == [a["kaynak_gorseli"]]
    assert ikiz[0]["correct_answer"] != ikiz[1]["correct_answer"]


def test_sinav_turu_olculmedigi_yazili(kayitlar: list[dict]) -> None:
    assert all(
        k["pipeline_metadata"]["sinav_turu_kaynagi"].startswith("olculmedi")
        for k in kayitlar
    )


# ------------------------------------------------------------ 6. mutasyon


def _m_soru_sil(p: dict) -> None:
    del p["veri"]["sorular"][100]


def _m_kutu_sil(p: dict) -> None:
    del p["kutular"]["kutular"][100]


def _m_anahtar_sil(p: dict) -> None:
    del p["anahtar"]["cevaplar"][100]


def _m_cevap_sizdi(p: dict) -> None:
    p["veri"]["sorular"][0]["cevap"] = "D"


def _m_birim_sil(p: dict) -> None:
    del p["birim"]["birimler"][10]


def _m_ayni_kirpim_iki_kez(p: dict) -> None:
    p["veri"]["sorular"][1] = copy.deepcopy(p["veri"]["sorular"][0])


YAPISAL: list[tuple[str, Callable[[dict], None]]] = [
    ("metinden soru silindi", _m_soru_sil),
    ("kirpim kutusu silindi", _m_kutu_sil),
    ("anahtardan cevap silindi", _m_anahtar_sil),
    ("metin kanalina cevap sizdi", _m_cevap_sizdi),
    ("birim haritasindan birim silindi", _m_birim_sil),
    ("ayni kirpim iki kez okundu", _m_ayni_kirpim_iki_kez),
]


@pytest.mark.parametrize(("ad", "bozucu"), YAPISAL)
def test_yapisal_kapi_mutasyonu_yakaliyor(
    ad: str, bozucu: Callable, paket: dict
) -> None:
    p = copy.deepcopy(paket)
    bozucu(p)
    assert ag._yapisal_kapilar(p["veri"], p["birim"], p["kutular"], p["anahtar"]), ad


def _kayit_boz(paket: dict, bozucu: Callable[[list[dict]], None]) -> list[str]:
    satir = _bagla(copy.deepcopy(paket))
    bozucu(satir)
    k = [ag.kayit_uret(r) for r in satir]
    ag.sekil_ikizleri(k)
    return ag._on_kontrol(k)


def test_on_kontrol_bos_anahtar_sikki(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["sikler"]["C"] = ""
        s[0]["cevap"] = "C"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_yanlis_konu_kodu(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["konu_kodu"] = "GEO-ACL24-B01-01"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_kirpimsiz_satir(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["kirpim_kutusu"] = None

    assert _kayit_boz(paket, boz)


def test_on_kontrol_gecersiz_cevap(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["cevap"] = "F"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_sekilsiz_cift_okuma_durur(paket: dict) -> None:
    """Ayni metin iki kez ve biri sekilsiz: ikiz degil, cift okuma -- DURMALI."""

    def boz(s: list[dict]) -> None:
        for alan in ("govde", "sikler"):
            s[1][alan] = copy.deepcopy(s[0][alan])
        s[1]["sekil_var"] = False

    assert any("ayni hash" in h for h in _kayit_boz(paket, boz))


def test_basili_numara_kaymasi_baglamada_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["veri"]["sorular"][5]["basili_no"] += 1
    with pytest.raises(ValueError, match="basili"):
        _bagla(p)


def test_alt_konu_yanlis_konuya_bagliysa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    b = next(x for x in p["birim"]["birimler"] if x["alt_konu"])
    b["konu"] = "GEO-ACL25-K33" if b["konu"] != "GEO-ACL25-K33" else "GEO-ACL25-K01"
    with pytest.raises(ValueError, match="altinda degil"):
        _bagla(p)


def test_kutu_baska_soruyu_gosteriyorsa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["kutular"]["kutular"][0]["serit_sira"] += 1
    with pytest.raises(ValueError, match="ayni soruyu"):
        _bagla(p)
