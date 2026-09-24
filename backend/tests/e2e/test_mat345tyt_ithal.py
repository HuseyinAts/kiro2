"""345 2025 TYT Matematik ithalinin kapilari.

Canli DB istemez; veri setini, konu haritasini, kirpim kutularini, cevap
anahtarini, ortme olcumunu, mukerrer adaylarini ve ithal script'ini DOSYADAN
okur -- CI'da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 2063 kayit, 5 sik, dolu cevap, benzersiz id.
2. YAPISAL GARANTILER   -- 202 test, basili numara == test ici sira,
                           metin kanalina cevap sizmamis.
3. KONU BAGLANTISI      -- her kayit MAT-345T25 agacinda; migration ile ayni kodlar.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz; eski hat
                           yazimi 0043 ile duzeltiliyor.
5. DURUSTLUK            -- cozum yok, ithal PASIF, bayrak capalari, cikmis yil.
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

from scripts.kitap import mat345tyt_ithal as mi  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
    normalize_anahtar,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_matematik_"
YOLLAR = {
    "veri": CIKTI / f"{ON}metin.json",
    "harita": CIKTI / f"{ON}konu_haritasi.json",
    "kutular": CIKTI / f"{ON}kirpim_kutulari.json",
    "anahtar": CIKTI / f"{ON}cevap_anahtari.json",
    "ortme": CIKTI / f"{ON}ortme_olcumu.json",
    "mukerrer": CIKTI / f"{ON}mukerrer_adaylari.json",
}
ITHAL_YOLU = KOK / "scripts" / "kitap" / "mat345tyt_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0042_mat345tyt_konu_agaci.py"
AD_YOLU = KOK / "alembic" / "versions" / "0043_mat345tyt_kaynak_adi.py"
ARAC_YOLLARI = [
    ITHAL_YOLU,
    AGAC_YOLU,
    AD_YOLU,
    KOK / "scripts" / "kitap" / "mat345tyt_tarama.py",
    KOK / "scripts" / "kitap" / "mat345tyt_kutu.py",
    KOK / "scripts" / "kitap" / "mat345tyt_kirp.py",
    KOK / "scripts" / "kitap" / "mat345tyt_metin_harness.py",
]

BEKLENEN_SORU = 2063
BEKLENEN_TEST = 202
BEKLENEN_DUGUM = 30  # konu dugumu; bolum dugumleri soru tasimaz
BAYRAKLAR = {
    "kaynak_kusuru": 101,
    "cikmis_soru": 149,
    "okuyucu_diski_ortme": 167,
    "sik_tekrar": 24,
    "sikler_gorsel": 22,
    "mukerrer_aday": 27,
    "numara_ortulu": 1,
}
CEVAP_KANALI = {
    "iki_okuma+piksel": 1762,
    "iki_okuma(biri_tereddutlu)+goz": 44,
    "iki_okuma+piksel_supheli+goz": 16,
    "iki_okuma+goz(piksel_kapsam_disi)": 241,
}
SINAV = {"TYT": 81, "MSU": 61, "AYT": 7}
SAYFA_ILK, SAYFA_SON = 6, 416
KART_G, KART_Y = 742, 977


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def paket() -> dict[str, dict]:
    return {ad: _oku(y) for ad, y in YOLLAR.items()}


def _bagla(p: dict[str, dict]) -> list[dict]:
    return mi.satirlari_bagla(
        p["veri"],
        p["harita"],
        p["kutular"],
        p["anahtar"],
        ortme=p["ortme"],
        mukerrer=p["mukerrer"],
    )


@pytest.fixture(scope="module")
def kayitlar(paket: dict[str, dict]) -> list[dict]:
    k = [mi.kayit_uret(r) for r in _bagla(paket)]
    mi.sekil_ikizleri(k)
    return k


def _modul(ad: str, yol: Path) -> object:
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def agac() -> object:
    return _modul("agac0042", AGAC_YOLU)


@pytest.fixture(scope="module")
def ad_duzeltme() -> object:
    return _modul("ad0043", AD_YOLU)


# ------------------------------------------------- 1. veri seti butunlugu


def test_kayit_sayisi_ve_id(kayitlar: list[dict]) -> None:
    assert len(kayitlar) == BEKLENEN_SORU
    assert len({k["id"] for k in kayitlar}) == BEKLENEN_SORU
    assert len({k["soru_hash"] for k in kayitlar}) == BEKLENEN_SORU


def test_her_kayitta_bes_sik_ve_dolu_cevap(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        assert set(k["secenekler"]) == set("ABCDE"), k["id"]
        assert k["correct_answer"] in set("ABCDE"), k["id"]
        assert k["secenekler"][k["correct_answer"]].strip(), k["id"]
        assert k["question_text"].strip()


def test_sayfa_araligi_ve_basili_sayfa(kayitlar: list[dict]) -> None:
    s = [k["source_page"] for k in kayitlar]
    assert min(s) == SAYFA_ILK and max(s) == SAYFA_SON
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["basili_sayfa"] == pm["sayfa_dosya_no"] == k["source_page"]


# ------------------------------------------------- 2. yapisal garantiler


def test_yapisal_kapilar_temiz(paket: dict[str, dict]) -> None:
    assert (
        mi._yapisal_kapilar(
            paket["veri"], paket["harita"], paket["kutular"], paket["anahtar"]
        )
        == []
    )


def test_on_kontrol_temiz(kayitlar: list[dict]) -> None:
    assert mi._on_kontrol(kayitlar) == []


def test_test_ve_ici_sira(kayitlar: list[dict]) -> None:
    assert (
        len({k["pipeline_metadata"]["birim_kodu"] for k in kayitlar}) == BEKLENEN_TEST
    )
    ortulu = [k for k in kayitlar if k["pipeline_metadata"]["soru_no_basili"] is None]
    assert [k["pipeline_metadata"]["kaynak_gorseli"] for k in ortulu] == [
        "MAT345-T192_07.png"
    ]
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        if pm["soru_no_basili"] is not None:
            assert pm["soru_no_basili"] == pm["birim_ici_sira"], k["id"]


def test_cevap_kanali_dagilimi(kayitlar: list[dict]) -> None:
    assert (
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar))
        == CEVAP_KANALI
    )


# ------------------------------------------------- 3. konu baglantisi


def test_bir_test_tek_dugume_baglanir(kayitlar: list[dict]) -> None:
    dugum: dict[str, set[str]] = {}
    for k in kayitlar:
        dugum.setdefault(k["pipeline_metadata"]["birim_kodu"], set()).add(
            k["konu_kodu"]
        )
    assert all(len(v) == 1 for v in dugum.values())


def test_konu_kodlari_migration_ile_ayni(
    kayitlar: list[dict], agac: object, paket: dict
) -> None:
    bolum = set(agac.BOLUMLER)  # type: ignore[attr-defined]
    konu = set(agac.KONULAR)  # type: ignore[attr-defined]
    h = paket["harita"]
    assert {k for k, _ in bolum} == {b["kod"] for b in h["bolumler"]}
    assert all(ad == f"Bolum {k[-2:]}" for k, ad in bolum)
    assert {(u, k) for u, k, _ in konu} == {
        (f"MAT-345T25-B{x['bolum']:02d}", x["kod"]) for x in h["konular"]
    }
    for _, kod, ad in konu:
        assert ad.isascii() and ad.strip(), kod
    bagli = {k["konu_kodu"] for k in kayitlar}
    assert bagli == {k for _, k, _ in konu}
    assert len(bagli) == BEKLENEN_DUGUM


def test_migration_zinciri(agac: object, ad_duzeltme: object) -> None:
    assert agac.down_revision == "0041_acil25geo_agac"  # type: ignore[attr-defined]
    assert ad_duzeltme.down_revision == agac.revision  # type: ignore[attr-defined]
    for m in (agac, ad_duzeltme):
        assert len(m.revision) <= 32  # type: ignore[attr-defined]
    assert agac.KOD_ONEKI == mi.KOD_ONEKI  # type: ignore[attr-defined]


# ------------------------------------------------------------ 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(mi.KAYNAK_ADI, kayitli_olmali=True)
    assert cakisan_kaynak(mi.KAYNAK_ADI, list(KAYNAK_KAYITLARI)) is None
    kayit = KAYNAK_KAYITLARI[mi.KAYNAK_ADI]
    assert kayit["onek"] == mi.ONEK
    assert kayit["ithal_araci"] == mi.ITHAL_ARACI


def test_eski_hat_yazimi_ayni_kitap_0043_duzeltiyor(ad_duzeltme: object) -> None:
    """Eski hat yazimi ayni anahtara cozuluyor; 0043 onu yeni ada ceviriyor."""
    eski, yeni = ad_duzeltme.ESKI, ad_duzeltme.YENI  # type: ignore[attr-defined]
    assert yeni == mi.KAYNAK_ADI and eski != yeni
    assert normalize_anahtar(eski) == normalize_anahtar(yeni)
    assert normalize_anahtar(
        "345 2024 Tyt Matematik Soru Bankas\u0131"
    ) != normalize_anahtar(yeni)


@pytest.mark.parametrize("yol", ARAC_YOLLARI, ids=lambda p: p.name)
def test_arac_kaynak_dosyalari_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name


# ----------------------------------------------------------- 5. durustluk


def test_ithal_pasif_sozlesmesi() -> None:
    kolon, deger = mi._QB.split("VALUES")
    assert "is_active, is_public" in " ".join(kolon.split())
    assert "FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE" in deger
    assert "NULL, %(question_image_url)s" in mi._QC
    assert "'TYT', 'MATEMATIK'" in mi._QM and "'PENDING'" in mi._QM


def test_cozum_uydurulmuyor(kayitlar: list[dict]) -> None:
    assert all(k["explanation"] is None for k in kayitlar)
    assert "cozulmedi" in mi.URETIM_NOTU


def test_gorsel_ve_kutu_tutarli(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        x0, y0, x1, y1 = k["pipeline_metadata"]["kirpim_kutusu"]
        assert 0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y, k["id"]
        assert k["question_image_url"] == (
            f"/static/crops/{mi.CROP_ONEK}/{k['pipeline_metadata']['kaynak_gorseli']}"
        )


def test_olculen_bayrak_capalari(kayitlar: list[dict]) -> None:
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    assert dict(bayrak) == BAYRAKLAR


def test_cikmis_yil_yalniz_etiketli_soruda(kayitlar: list[dict]) -> None:
    cikmis = [k for k in kayitlar if k["osym_year"] is not None]
    assert len(cikmis) == BAYRAKLAR["cikmis_soru"]
    assert dict(Counter(k["pipeline_metadata"]["sinav"] for k in cikmis)) == SINAV
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert k["osym_format_compliant"] is (k["osym_year"] is not None)
        assert (pm["cikmis_etiketi"] is not None) == (k["osym_year"] is not None), k[
            "id"
        ]
        if k["osym_year"] is not None:
            assert (
                2018 <= k["osym_year"] <= 2025
                and str(k["osym_year"]) in pm["cikmis_etiketi"]
            )


@pytest.mark.parametrize(
    ("etiket", "beklenen"),
    [
        ("MS\u00dc - 2021", ("MSU", 2021)),
        ("TYT - 2023", ("TYT", 2023)),
        ("2019 - TYT", ("TYT", 2019)),
        (None, (None, None)),
        ("MSU", (None, None)),
        ("2020", (None, None)),
    ],
)
def test_etiket_ayristirma(etiket: str | None, beklenen: tuple) -> None:
    assert mi.etiket_ayristir(etiket) == beklenen


# ------------------------------------------------------------ 6. mutasyon


def _m_soru_sil(p: dict) -> None:
    del p["veri"]["sorular"][100]


def _m_kutu_sil(p: dict) -> None:
    del p["kutular"]["kutular"][100]


def _m_anahtar_sil(p: dict) -> None:
    del p["anahtar"]["cevaplar"][100]


def _m_cevap_sizdi(p: dict) -> None:
    p["veri"]["sorular"][0]["cevap"] = "D"


def _m_test_sil(p: dict) -> None:
    del p["harita"]["testler"][10]


def _m_konu_sil(p: dict) -> None:
    del p["harita"]["konular"][3]


def _m_ayni_kirpim_iki_kez(p: dict) -> None:
    p["veri"]["sorular"][1] = copy.deepcopy(p["veri"]["sorular"][0])


YAPISAL: list[tuple[str, Callable[[dict], None]]] = [
    ("metinden soru silindi", _m_soru_sil),
    ("kirpim kutusu silindi", _m_kutu_sil),
    ("anahtardan cevap silindi", _m_anahtar_sil),
    ("metin kanalina cevap sizdi", _m_cevap_sizdi),
    ("haritadan test silindi", _m_test_sil),
    ("haritadan konu silindi", _m_konu_sil),
    ("ayni kirpim iki kez okundu", _m_ayni_kirpim_iki_kez),
]


@pytest.mark.parametrize(("ad", "bozucu"), YAPISAL)
def test_yapisal_kapi_mutasyonu_yakaliyor(
    ad: str, bozucu: Callable, paket: dict
) -> None:
    p = copy.deepcopy(paket)
    bozucu(p)
    assert mi._yapisal_kapilar(p["veri"], p["harita"], p["kutular"], p["anahtar"]), ad


def _kayit_boz(paket: dict, bozucu: Callable[[list[dict]], None]) -> list[str]:
    satir = _bagla(copy.deepcopy(paket))
    bozucu(satir)
    k = [mi.kayit_uret(r) for r in satir]
    mi.sekil_ikizleri(k)
    return mi._on_kontrol(k)


def test_on_kontrol_bos_anahtar_sikki(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["sikler"]["C"] = ""
        s[0]["cevap"] = "C"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_yanlis_konu_kodu(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["konu_kodu"] = "MAT.SAY"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_kirpimsiz_satir(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["kirpim_kutusu"] = None

    assert _kayit_boz(paket, boz)


def test_on_kontrol_gecersiz_cevap(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["cevap"] = "F"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_numarasiz_satir_numara_capali_ise_durur(paket: dict) -> None:
    """Basili numara yalniz capasi SIMGE olan kutuda bos olabilir."""

    def boz(s: list[dict]) -> None:
        s[0]["basili_no"] = None

    assert _kayit_boz(paket, boz)


def test_on_kontrol_sekilsiz_cift_okuma_durur(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        for alan in ("govde", "sikler"):
            s[1][alan] = copy.deepcopy(s[0][alan])
        s[1]["sekil_var"] = False

    assert any("ayni hash" in h for h in _kayit_boz(paket, boz))


def test_on_kontrol_cikmis_yil_tutarsiz(paket: dict) -> None:
    k = [mi.kayit_uret(r) for r in _bagla(copy.deepcopy(paket))]
    k[0]["pipeline_metadata"]["cikmis_soru"] = True
    k[0]["osym_year"] = None
    assert any("cikmis" in h for h in mi._on_kontrol(k))


def test_basili_numara_kaymasi_baglamada_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["veri"]["sorular"][5]["basili_no"] += 1
    with pytest.raises(ValueError, match="basili"):
        _bagla(p)


def test_test_konusu_haritada_yoksa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["konu"] = "MAT-345T25-B99-01"
    with pytest.raises(ValueError, match="haritada yok"):
        _bagla(p)


def test_kutu_baska_soruyu_gosteriyorsa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["kutular"]["kutular"][0]["serit_sira"] += 1
    with pytest.raises(ValueError, match="ayni soruyu"):
        _bagla(p)


def test_kutu_test_sayfasi_disindaysa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["sayfalar"] = [999]
    with pytest.raises(ValueError, match="testin sayfalarinda"):
        _bagla(p)
