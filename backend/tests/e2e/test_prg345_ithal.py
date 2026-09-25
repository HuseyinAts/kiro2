"""345 2025 Paragraf Sifir Risk ithalinin kapilari.

Canli DB istemez; veri setini, konu haritasini, kirpim kutularini, cevap
anahtarini, ortme olcumunu, mukerrer adaylarini ve ithal script'ini DOSYADAN
okur -- CI'da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 1012 kayit, 5 sik, dolu cevap, benzersiz id.
2. YAPISAL GARANTILER   -- 85 test, basili numara == test ici sira,
                           metin kanalina cevap sizmamis.
3. KONU BAGLANTISI      -- her kayit TUR-345P25 bolum dugumunde;
                           migration ile ayni kodlar.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK            -- cozum yok, ithal PASIF, bayrak capalari, cikmis yil,
                           ortak metin govdede.
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

from scripts.kitap import prg345_ithal as mi  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_paragraf_"
YOLLAR = {
    "veri": CIKTI / f"{ON}metin.json",
    "harita": CIKTI / f"{ON}konu_haritasi.json",
    "kutular": CIKTI / f"{ON}kirpim_kutulari.json",
    "anahtar": CIKTI / f"{ON}cevap_anahtari.json",
    "ortme": CIKTI / f"{ON}ortme_olcumu.json",
    "mukerrer": CIKTI / f"{ON}mukerrer_adaylari.json",
}
ITHAL_YOLU = KOK / "scripts" / "kitap" / "prg345_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0055_prg345_konu_agaci.py"
AD_YOLU = KOK / "alembic" / "versions" / "0054_prg345_kaynak_adi.py"
ARAC_YOLLARI = [
    ITHAL_YOLU,
    AGAC_YOLU,
    AD_YOLU,
    KOK / "scripts" / "kitap" / "prg345_tarama.py",
    KOK / "scripts" / "kitap" / "prg345_kutu.py",
    KOK / "scripts" / "kitap" / "prg345_kirp.py",
    KOK / "scripts" / "kitap" / "prg345_metin_harness.py",
]

BEKLENEN_SORU = 1012
BEKLENEN_TEST = 85
BEKLENEN_DUGUM = 7
BAYRAKLAR = {
    "okuyucu_diski_ortme": 250,
    "cikmis_soru": 84,
    "kaynak_kusuru": 143,
    "mukerrer_aday": 10,
    "eski_hat_ikizi": 8,
    "ortak_metin_govdede": 65,
    "kitap_ici_tekrar": 2,
    "numara_ortulu": 2,
    "bulanik_metin_tasarim": 8,
}
CEVAP_KANALI = {"iki_okuma": 978, "iki_okuma(biri_tereddutlu)+goz": 34}
SINAV = {"TYT": 37, "ALES": 18, "DGS": 10, "KPSS": 8, "MSU": 7, "AYT": 4}
SAYFA_ILK, SAYFA_SON = 4, 355
BEKLENEN_ORTAK = 30
KART_G, KART_Y = 742, 977
# Kitap ayni cikmis soruyu iki testte basmis (olculdu; prg345_ithal.kitap_ici_tekrarlar).
TEKRAR = {"PRG345-T022_20.png", "PRG345-T038_13.png"}


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
    assert mi.sekil_ikizleri(k) == 0
    assert mi.kitap_ici_tekrarlar(k) == 1
    return k


def _modul(ad: str, yol: Path) -> object:
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def agac() -> object:
    return _modul("agac0055", AGAC_YOLU)


# ------------------------------------------------- 1. veri seti butunlugu


def test_kayit_sayisi_ve_id(kayitlar: list[dict]) -> None:
    assert len(kayitlar) == BEKLENEN_SORU
    assert len({k["id"] for k in kayitlar}) == BEKLENEN_SORU
    # Tek ortak hash kitap ici tekrar ciftidir (iki test, iki kirpim).
    assert len({k["soru_hash"] for k in kayitlar}) == BEKLENEN_SORU - 1
    tekrar = [
        k for k in kayitlar if "kitap_ici_tekrar" in k["pipeline_metadata"]["bayraklar"]
    ]
    assert {k["pipeline_metadata"]["kaynak_gorseli"] for k in tekrar} == TEKRAR
    assert len({k["soru_hash"] for k in tekrar}) == 1


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
    assert len(ortulu) == BAYRAKLAR.get("numara_ortulu", 0)
    for k in ortulu:
        pm = k["pipeline_metadata"]
        assert (
            pm["kirpim_capa_kanali"] not in mi.NUMARA_KANALLARI
            or pm["kirpim_numara_disk_ortulu"]
        ), k["id"]
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
    bolum = list(agac.BOLUMLER)  # type: ignore[attr-defined]
    h = paket["harita"]
    assert [(b["kod"], b["ad"]) for b in h["bolumler"]] == bolum
    bagli = {k["konu_kodu"] for k in kayitlar}
    assert bagli == {k for k, _ in bolum}
    assert len(bagli) == BEKLENEN_DUGUM


def test_eslesme_duzeyi_bolum(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        assert k["pipeline_metadata"]["konu_eslesme_duzeyi"] == "bolum", k["id"]
        assert mi._duzey_kontrol(k) == [], k["id"]


def test_migration_zinciri(agac: object) -> None:
    ad = _modul("ad0054", AD_YOLU)
    assert ad.down_revision == "0053_edb345ayt_agac"  # type: ignore[attr-defined]
    assert agac.down_revision == ad.revision  # type: ignore[attr-defined]
    for m in (ad, agac):
        assert len(m.revision) <= 32  # type: ignore[attr-defined]
    assert agac.KOD_ONEKI == mi.KOD_ONEKI  # type: ignore[attr-defined]
    assert ad.YENI == mi.KAYNAK_ADI  # type: ignore[attr-defined]
    assert ad.ESKI != ad.YENI and ad.ESKI.rstrip(chr(0x0131)) + "i" == ad.YENI  # type: ignore[attr-defined]


# ------------------------------------------------------------ 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(mi.KAYNAK_ADI, kayitli_olmali=True)
    assert cakisan_kaynak(mi.KAYNAK_ADI, list(KAYNAK_KAYITLARI)) is None
    kayit = KAYNAK_KAYITLARI[mi.KAYNAK_ADI]
    assert kayit["onek"] == mi.ONEK
    assert kayit["ithal_araci"] == mi.ITHAL_ARACI


@pytest.mark.parametrize("yol", ARAC_YOLLARI, ids=lambda p: p.name)
def test_arac_kaynak_dosyalari_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name


# ----------------------------------------------------------- 5. durustluk


def test_ithal_pasif_sozlesmesi() -> None:
    kolon, deger = mi._QB.split("VALUES")
    assert "is_active, is_public" in " ".join(kolon.split())
    assert "FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE" in deger
    assert "NULL, %(question_image_url)s" in mi._QC
    assert "'TYT', 'TURKCE'" in mi._QM and "'PENDING'" in mi._QM


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
                2012 <= k["osym_year"] <= 2025
                and str(k["osym_year"]) in pm["cikmis_etiketi"]
            )


@pytest.mark.parametrize(
    ("etiket", "beklenen"),
    [
        ("2025 - MS\u00dc", ("MSU", 2025)),
        ("2021 - ALES", ("ALES", 2021)),
        ("2014 - DGS", ("DGS", 2014)),
        ("2019 - KPSS", ("KPSS", 2019)),
        ("2023 - TYT", ("TYT", 2023)),
        ("TYT - 2021", ("TYT", 2021)),
        ("2020 - AYT", ("AYT", 2020)),
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


def _m_bolum_sil(p: dict) -> None:
    del p["harita"]["bolumler"][3]


def _m_ayni_kirpim_iki_kez(p: dict) -> None:
    p["veri"]["sorular"][1] = copy.deepcopy(p["veri"]["sorular"][0])


YAPISAL: list[tuple[str, Callable[[dict], None]]] = [
    ("metinden soru silindi", _m_soru_sil),
    ("kirpim kutusu silindi", _m_kutu_sil),
    ("anahtardan cevap silindi", _m_anahtar_sil),
    ("metin kanalina cevap sizdi", _m_cevap_sizdi),
    ("haritadan test silindi", _m_test_sil),
    ("haritadan bolum silindi", _m_bolum_sil),
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
    mi.kitap_ici_tekrarlar(k)
    return mi._on_kontrol(k)


def test_on_kontrol_bolum_disi_konu_kodu(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["konu_kodu"] = "TUR-345P25-B09"

    assert any("bolum kodu degil" in h for h in _kayit_boz(paket, boz))


def test_on_kontrol_bos_anahtar_sikki(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["sikler"]["C"] = ""
        s[0]["cevap"] = "C"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_yanlis_konu_kodu(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["konu_kodu"] = "TUR-BS4"

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
    """Basili numara yalniz disk altinda (numara disi capa / numara_disk_ortulu) bos olabilir."""

    def boz(s: list[dict]) -> None:
        assert s[0]["capa_kanali"] == "numara" and not s[0]["numara_disk_ortulu"]
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


def test_test_bolumu_haritada_yoksa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["bolum"] = "TUR-345P25-B99"
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


# ------------------------------------------------------- 7. ortak metin


def test_ortak_metin_govdenin_basinda(kayitlar: list[dict], paket: dict) -> None:
    """Kapsamdaki her sorunun metni ortak parca + bos satir + kendi govdesi."""
    ortak = {o["ortak"]: o for o in paket["veri"]["ortak_metinler"]}
    assert len(ortak) == BEKLENEN_ORTAK
    govde = {s["dosya"]: s["govde"] for s in paket["veri"]["sorular"]}
    kapsanan = []
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        ad = pm["kaynak_gorseli"][:-4]
        if pm["ortak_metin"] is None:
            assert k["question_text"] == govde[ad], ad
            continue
        o = ortak[pm["ortak_metin"]]
        assert pm["ortak_metin_kapsami"] == o["kapsam"], ad
        assert o["kapsam"][0] <= pm["birim_ici_sira"] <= o["kapsam"][1], ad
        assert k["question_text"] == o["metin"] + mi.ORTAK_AYRAC + govde[ad], ad
        kapsanan.append(ad)
    assert len(kapsanan) == BAYRAKLAR["ortak_metin_govdede"]
    assert len(kapsanan) == sum(
        b - a + 1 for a, b in (o["kapsam"] for o in ortak.values())
    )


def test_ortak_kapsam_basi_kayarsa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["veri"]["ortak_metinler"][0]["kapsam"][0] += 1
    with pytest.raises(ValueError, match="kapsam basi"):
        _bagla(p)


def test_ortak_metin_eksikse_yapisal_kapi_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    del p["veri"]["ortak_metinler"][0]
    h = mi._yapisal_kapilar(p["veri"], p["harita"], p["kutular"], p["anahtar"])
    assert any("ortak metin" in x for x in h)


def test_kitap_ici_tekrar_ayni_testte_ayristirilmaz(paket: dict) -> None:
    """Ayni testte ayni hash gercek bir cift okumadir: tekrar sayilmaz, durur."""

    def boz(s: list[dict]) -> None:
        for alan in ("govde", "sikler"):
            s[2][alan] = copy.deepcopy(s[0][alan])

    assert any("ayni hash" in h for h in _kayit_boz(paket, boz))


def test_eski_hat_ikizleri_isaretli(kayitlar: list[dict], paket: dict) -> None:
    eski = {a["dosya"]: a for a in paket["mukerrer"]["eski_hat_satirlari"]}
    isaretli = {
        k["pipeline_metadata"]["kaynak_gorseli"][:-4]: k
        for k in kayitlar
        if "eski_hat_ikizi" in k["pipeline_metadata"]["bayraklar"]
    }
    assert set(isaretli) == set(eski)
    for ad, k in isaretli.items():
        assert k["pipeline_metadata"]["eski_hat_ikizi"]["db_id"] == eski[ad]["db_id"]
        assert eski[ad]["cevap_ayni"] is True
