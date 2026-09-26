"""345 2025 Start Matematik ithalinin kapilari.

Canli DB istemez; veri setini, unite haritasini, kirpim kutularini, cevap
anahtarini, ortme olcumunu, mukerrer adaylarini ve ithal script'ini DOSYADAN
okur -- CI'da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 371 kayit, 5 sik, dolu cevap, benzersiz id.
2. YAPISAL GARANTILER   -- 45 test, basili numara == test ici sira,
                           metin kanalina cevap sizmamis, etiket yok.
3. KONU BAGLANTISI      -- her kayit MAT-345S25 unitesinde; migration ile ayni.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz; eski hat
                           ayni adi tasir ama 0058 ile pasif ve id'si ayri.
5. DURUSTLUK            -- cozum yok, ithal PASIF, bayrak capalari.
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

from scripts.kitap import stm345_ithal as si  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_start_matematik_"
YOLLAR = {
    "veri": CIKTI / f"{ON}metin.json",
    "harita": CIKTI / f"{ON}konu_haritasi.json",
    "kutular": CIKTI / f"{ON}kirpim_kutulari.json",
    "anahtar": CIKTI / f"{ON}cevap_anahtari.json",
    "ortme": CIKTI / f"{ON}ortme_olcumu.json",
    "mukerrer": CIKTI / f"{ON}mukerrer_adaylari.json",
}
ITHAL_YOLU = KOK / "scripts" / "kitap" / "stm345_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0057_stm345_konu_agaci.py"
PASIF_YOLU = KOK / "alembic" / "versions" / "0058_stm345_eski_hat_pasif.py"
ARAC_YOLLARI = [
    ITHAL_YOLU,
    AGAC_YOLU,
    PASIF_YOLU,
    KOK / "scripts" / "kitap" / "stm345_tarama.py",
    KOK / "scripts" / "kitap" / "stm345_anahtar.py",
    KOK / "scripts" / "kitap" / "stm345_harita.py",
    KOK / "scripts" / "kitap" / "stm345_kutu.py",
    KOK / "scripts" / "kitap" / "stm345_kirp.py",
    KOK / "scripts" / "kitap" / "stm345_metin_harness.py",
    KOK / "scripts" / "kitap" / "stm345_mukerrer.py",
]

BEKLENEN_SORU = 371
BEKLENEN_TEST = 45
BEKLENEN_UNITE = 16
BAYRAKLAR = {
    "kaynak_kusuru": 23,
    "okunamaz_isaret": 6,
    "okuyucu_diski_ortme": 6,
    "sik_tekrar": 3,
    "sikler_gorsel": 3,
}
CEVAP_KANALI = {
    "iki_okuma+piksel": 347,
    "iki_okuma+piksel+tereddut(numara_surekliligi)": 11,
    "iki_okuma+goz(10x)": 12,
    "iki_okuma+goz(10x)+tereddut(numara_surekliligi)": 1,
}
OKUNAMAZ = {"T005_05", "T011_07", "T012_02", "T035_08", "T036_02", "T038_04"}
SAYFA_ILK, SAYFA_SON = 10, 319  # basili; dosya 11..320
KART_G, KART_Y = 742, 977


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def paket() -> dict[str, dict]:
    return {ad: _oku(y) for ad, y in YOLLAR.items()}


def _bagla(p: dict[str, dict]) -> list[dict]:
    return si.satirlari_bagla(
        p["veri"],
        p["harita"],
        p["kutular"],
        p["anahtar"],
        ortme=p["ortme"],
        mukerrer=p["mukerrer"],
    )


@pytest.fixture(scope="module")
def kayitlar(paket: dict[str, dict]) -> list[dict]:
    k = [si.kayit_uret(r) for r in _bagla(paket)]
    si.sekil_ikizleri(k)
    return k


def _modul(ad: str, yol: Path) -> object:
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def agac() -> object:
    return _modul("agac0057i", AGAC_YOLU)


@pytest.fixture(scope="module")
def pasif() -> object:
    return _modul("pasif0058i", PASIF_YOLU)


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
        assert pm["basili_sayfa"] == pm["sayfa_dosya_no"] - 1 == k["source_page"]


def test_cevaplar_anahtarla_birebir(kayitlar: list[dict], paket: dict) -> None:
    anahtar = {
        f"{c['birim']}_{c['soru']:02d}": c["cevap"]
        for c in paket["anahtar"]["cevaplar"]
    }
    for k in kayitlar:
        ad = k["pipeline_metadata"]["kaynak_gorseli"].removesuffix(".png")
        assert k["correct_answer"] == anahtar[ad], ad


# ------------------------------------------------- 2. yapisal garantiler


def test_yapisal_kapilar_temiz(paket: dict[str, dict]) -> None:
    assert (
        si._yapisal_kapilar(
            paket["veri"], paket["harita"], paket["kutular"], paket["anahtar"]
        )
        == []
    )


def test_on_kontrol_temiz(kayitlar: list[dict]) -> None:
    assert si._on_kontrol(kayitlar) == []


def test_test_ve_ici_sira(kayitlar: list[dict]) -> None:
    assert (
        len({k["pipeline_metadata"]["birim_kodu"] for k in kayitlar}) == BEKLENEN_TEST
    )
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["soru_no_basili"] == pm["birim_ici_sira"], k["id"]
        assert pm["kirpim_capa_kanali"] == "numara"


def test_cevap_kanali_dagilimi(kayitlar: list[dict]) -> None:
    assert (
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar))
        == CEVAP_KANALI
    )


# ------------------------------------------------- 3. konu baglantisi


def test_bir_test_tek_uniteye_baglanir(kayitlar: list[dict]) -> None:
    dugum: dict[str, set[str]] = {}
    for k in kayitlar:
        dugum.setdefault(k["pipeline_metadata"]["birim_kodu"], set()).add(
            k["konu_kodu"]
        )
    assert all(len(v) == 1 for v in dugum.values())


def test_unite_kodlari_migration_ile_ayni(kayitlar: list[dict], agac: object) -> None:
    uniteler = {kod for kod, _ in agac.UNITELER}  # type: ignore[attr-defined]
    assert {k["konu_kodu"] for k in kayitlar} == uniteler
    assert len(uniteler) == BEKLENEN_UNITE
    assert agac.KOD_ONEKI == si.KOD_ONEKI  # type: ignore[attr-defined]
    assert all(
        k["pipeline_metadata"]["konu_eslesme_duzeyi"] == "unite" for k in kayitlar
    )


# ------------------------------------------------------------ 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(si.KAYNAK_ADI, kayitli_olmali=True)
    assert cakisan_kaynak(si.KAYNAK_ADI, list(KAYNAK_KAYITLARI)) is None
    kayit = KAYNAK_KAYITLARI[si.KAYNAK_ADI]
    assert kayit["onek"] == si.ONEK == "STM345"
    assert kayit["ithal_araci"] == si.ITHAL_ARACI


def test_eski_hat_ayri_kimlik_ve_pasif(kayitlar: list[dict], pasif: object) -> None:
    """Eski hat ayni kaynak adini tasir; id'leri ithalle kesismez, 0058 kapatir."""
    assert pasif.KAYNAK == si.KAYNAK_ADI  # type: ignore[attr-defined]
    eski = set(pasif.ESKI_HAT_PASIF)  # type: ignore[attr-defined]
    assert not eski & {k["id"] for k in kayitlar}


@pytest.mark.parametrize("yol", ARAC_YOLLARI, ids=lambda p: p.name)
def test_arac_kaynak_dosyalari_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name


# ----------------------------------------------------------- 5. durustluk


def test_ithal_pasif_sozlesmesi() -> None:
    kolon, deger = si._QB.split("VALUES")
    assert "is_active, is_public" in " ".join(kolon.split())
    assert "FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE" in deger
    assert "NULL, %(question_image_url)s" in si._QC
    assert "'TYT', 'MATEMATIK'" in si._QM and "'PENDING'" in si._QM


def test_cozum_uydurulmuyor(kayitlar: list[dict]) -> None:
    assert all(k["explanation"] is None for k in kayitlar)
    assert "cozulmedi" in si.URETIM_NOTU
    assert all(
        k["pipeline_metadata"]["cozum_dogrulamasi"] == "yapilmadi_urun_karari"
        for k in kayitlar
    )


def test_cikmis_soru_yok(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        assert k["osym_year"] is None and k["osym_format_compliant"] is False
        assert k["pipeline_metadata"]["cikmis_soru"] is False


def test_gorsel_ve_kutu_tutarli(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        x0, y0, x1, y1 = k["pipeline_metadata"]["kirpim_kutusu"]
        assert 0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y, k["id"]
        assert k["question_image_url"] == (
            f"/static/crops/{si.CROP_ONEK}/{k['pipeline_metadata']['kaynak_gorseli']}"
        )


def test_olculen_bayrak_capalari(kayitlar: list[dict]) -> None:
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    assert dict(bayrak) == BAYRAKLAR


def test_okunamaz_isaret_bayragi_listeyle_ayni(kayitlar: list[dict]) -> None:
    isaretli = {
        k["pipeline_metadata"]["birim_kodu"].removeprefix("STM345-")
        + f"_{k['pipeline_metadata']['birim_ici_sira']:02d}"
        for k in kayitlar
        if "okunamaz_isaret" in k["pipeline_metadata"]["bayraklar"]
    }
    assert isaretli == OKUNAMAZ


def test_mukerrer_bayragi_yok(kayitlar: list[dict]) -> None:
    assert all(k["pipeline_metadata"]["mukerrer_aday"] is None for k in kayitlar)


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


def _m_unite_sil(p: dict) -> None:
    del p["harita"]["uniteler"][3]


def _m_ayni_kirpim_iki_kez(p: dict) -> None:
    p["veri"]["sorular"][1] = copy.deepcopy(p["veri"]["sorular"][0])


def _m_etiket(p: dict) -> None:
    p["veri"]["sorular"][7]["etiket"] = "TYT - 2023"


YAPISAL: list[tuple[str, Callable[[dict], None]]] = [
    ("metinden soru silindi", _m_soru_sil),
    ("kirpim kutusu silindi", _m_kutu_sil),
    ("anahtardan cevap silindi", _m_anahtar_sil),
    ("metin kanalina cevap sizdi", _m_cevap_sizdi),
    ("haritadan test silindi", _m_test_sil),
    ("haritadan unite silindi", _m_unite_sil),
    ("ayni kirpim iki kez okundu", _m_ayni_kirpim_iki_kez),
    ("beklenmeyen cikmis etiketi", _m_etiket),
]


@pytest.mark.parametrize(("ad", "bozucu"), YAPISAL)
def test_yapisal_kapi_mutasyonu_yakaliyor(
    ad: str, bozucu: Callable, paket: dict
) -> None:
    p = copy.deepcopy(paket)
    bozucu(p)
    assert si._yapisal_kapilar(p["veri"], p["harita"], p["kutular"], p["anahtar"]), ad


def _kayit_boz(paket: dict, bozucu: Callable[[list[dict]], None]) -> list[str]:
    satir = _bagla(copy.deepcopy(paket))
    bozucu(satir)
    k = [si.kayit_uret(r) for r in satir]
    si.sekil_ikizleri(k)
    return si._on_kontrol(k)


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


def test_on_kontrol_tanimsiz_kanal(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["cevap_kanali"] = "tahmin"

    assert any("kanali" in h for h in _kayit_boz(paket, boz))


def test_on_kontrol_sekilsiz_cift_okuma_durur(paket: dict) -> None:
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


def test_test_unitesi_haritada_yoksa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["unite"] = "MAT-345S25-U99"
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
