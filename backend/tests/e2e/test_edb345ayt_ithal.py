"""345 2025 AYT Turk Edebiyati ithalinin kapilari.

Canli DB istemez; veri setini, konu haritasini, kirpim kutularini, cevap
anahtarini, ortme olcumunu, mukerrer adaylarini ve ithal script'ini DOSYADAN
okur -- CI'da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 1384 kayit, 5 sik, dolu cevap, benzersiz id.
2. YAPISAL GARANTILER   -- 148 test, basili numara == test ici sira,
                           metin kanalina cevap sizmamis.
3. KONU BAGLANTISI      -- her kayit EDB-345A25 agacinda (konu ya da unite);
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

from scripts.kitap import edb345ayt_ithal as mi  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_ayt_edebiyat_"
YOLLAR = {
    "veri": CIKTI / f"{ON}metin.json",
    "harita": CIKTI / f"{ON}konu_haritasi.json",
    "kutular": CIKTI / f"{ON}kirpim_kutulari.json",
    "anahtar": CIKTI / f"{ON}cevap_anahtari.json",
    "ortme": CIKTI / f"{ON}ortme_olcumu.json",
    "mukerrer": CIKTI / f"{ON}mukerrer_adaylari.json",
}
ITHAL_YOLU = KOK / "scripts" / "kitap" / "edb345ayt_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0053_edb345ayt_konu_agaci.py"
ARAC_YOLLARI = [
    ITHAL_YOLU,
    AGAC_YOLU,
    KOK / "scripts" / "kitap" / "edb345ayt_tarama.py",
    KOK / "scripts" / "kitap" / "edb345ayt_kutu.py",
    KOK / "scripts" / "kitap" / "edb345ayt_kirp.py",
    KOK / "scripts" / "kitap" / "edb345ayt_metin_harness.py",
]

BEKLENEN_SORU = 1384
BEKLENEN_TEST = 148
# 46 konu (Kazanim Odakli + OSYM Tadinda) + 10 unite (Karma / Orijinal / Genel Bakis)
BEKLENEN_DUGUM = 56
DUZEY = {"konu": 1026, "unite": 358}
KONU_TURLERI = ("kazanim_odakli", "osym_tadinda")
BAYRAKLAR = {
    "kaynak_kusuru": 59,
    "cikmis_soru": 61,
    "okuyucu_diski_ortme": 94,
    "sik_tekrar": 2,
    "sikler_gorsel": 1,
    "mukerrer_aday": 6,
    "ortak_metin_govdede": 23,
}
CEVAP_KANALI = {
    "iki_okuma+piksel": 1325,
    "iki_okuma(biri_tereddutlu)+piksel+goz": 58,
    "iki_okuma(uyusmaz)+piksel+goz": 1,
}
# 2010-2017 cikmislari kitapta 'OSYM - yil' etiketiyle basili.
SINAV = {"AYT": 51, "OSYM": 10}
SAYFA_ILK, SAYFA_SON = 6, 320
BEKLENEN_ORTAK = 11
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
    assert mi.sekil_ikizleri(k) == 0
    return k


def _modul(ad: str, yol: Path) -> object:
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def agac() -> object:
    return _modul("agac0053", AGAC_YOLU)


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
    unite = set(agac.UNITELER)  # type: ignore[attr-defined]
    konu = set(agac.KONULAR)  # type: ignore[attr-defined]
    h = paket["harita"]
    assert {k for k, _ in unite} == {u["kod"] for u in h["uniteler"]}
    assert {(u, k) for u, k, _ in konu} == {
        (f"EDB-345A25-U{x['unite']:02d}", x["kod"]) for x in h["konular"]
    }
    # adlar haritadaki Turkce adla birebir (kaynak dosyada kacis dizisiyle)
    ad = {x["kod"]: x["ad"] for x in h["uniteler"] + h["konular"]}
    for kod, a in [*unite, *((k, a) for _, k, a in konu)]:
        assert a == ad[kod], kod
    bagli = {k["konu_kodu"] for k in kayitlar}
    assert bagli == {k for _, k, _ in konu} | {k for k, _ in unite}
    assert len(bagli) == BEKLENEN_DUGUM


def test_eslesme_duzeyi_test_turuyle(kayitlar: list[dict]) -> None:
    """Kazanim Odakli / OSYM Tadinda -> konu; Karma / Orijinal / Genel Bakis -> unite."""
    say: Counter[str] = Counter()
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        beklenen = "konu" if pm["test_turu"] in KONU_TURLERI else "unite"
        assert pm["konu_eslesme_duzeyi"] == beklenen, k["id"]
        assert k["konu_kodu"].count("-") == (3 if beklenen == "konu" else 2), k["id"]
        say[beklenen] += 1
    assert dict(say) == DUZEY


def test_migration_zinciri(agac: object) -> None:
    assert agac.down_revision == "0052_kim345ayt_eski_etiket"  # type: ignore[attr-defined]
    assert len(agac.revision) <= 32  # type: ignore[attr-defined]
    assert agac.KOD_ONEKI == mi.KOD_ONEKI  # type: ignore[attr-defined]


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
    assert "'AYT', 'EDEBIYAT'" in mi._QM and "'PENDING'" in mi._QM


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
                2010 <= k["osym_year"] <= 2025
                and str(k["osym_year"]) in pm["cikmis_etiketi"]
            )


@pytest.mark.parametrize(
    ("etiket", "beklenen"),
    [
        ("MS\u00dc - 2021", ("MSU", 2021)),
        ("TYT - 2023", ("TYT", 2023)),
        ("2019 - TYT", ("TYT", 2019)),
        ("AYT - 2020", ("AYT", 2020)),
        ("AYT - 2018", ("AYT", 2018)),
        ("LYS-1 - 2014", ("LYS", 2014)),
        ("LYS - 1 - 2013", ("LYS", 2013)),
        ("LYS1 - 2012", ("LYS", 2012)),
        ("\u00d6SYM - 2015", ("OSYM", 2015)),
        ("OSYM - 2010", ("OSYM", 2010)),
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


def test_on_kontrol_eslesme_duzeyi_tutarsiz(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        assert s[0]["konu_eslesme_duzeyi"] == "konu"
        s[0]["konu_eslesme_duzeyi"] = "unite"

    assert any("eslesme duzeyi" in h for h in _kayit_boz(paket, boz))


def test_on_kontrol_bos_anahtar_sikki(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["sikler"]["C"] = ""
        s[0]["cevap"] = "C"

    assert _kayit_boz(paket, boz)


def test_on_kontrol_yanlis_konu_kodu(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["konu_kodu"] = "EDB-OSYM-GENEL"

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


def test_test_konusu_haritada_yoksa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["konu"] = "EDB-345A25-U99-01"
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
