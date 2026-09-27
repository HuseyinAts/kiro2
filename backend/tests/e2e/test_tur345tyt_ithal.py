"""345 2025 TYT Turkce Soru Bankasi ithalinin kapilari.

Canli DB istemez; veri setini, unite haritasini, kirpim kutularini, cevap
anahtarini, ortme olcumunu, mukerrer adaylarini ve ithal script'ini
DOSYADAN okur (gozle listelenen numara ortmesi bu kitapta yok) -- CI'da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 2070 kayit, 5 sik, dolu cevap, benzersiz id.
2. YAPISAL GARANTILER   -- 207 test, basili numara == test ici sira (null
                           yalniz ortulu soruda), cevap sizmamis, 71 etiket.
3. KONU BAGLANTISI      -- konu testi konu, Karma testi unite dugumunde.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK            -- cozum yok, ithal PASIF, bayrak capalari, cikmis.
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

from scripts.kitap import tur345tyt_ithal as si  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_turkce_"
YOLLAR = {
    "veri": CIKTI / f"{ON}metin.json",
    "harita": CIKTI / f"{ON}konu_haritasi.json",
    "kutular": CIKTI / f"{ON}kirpim_kutulari.json",
    "anahtar": CIKTI / f"{ON}cevap_anahtari.json",
    "ortme": CIKTI / f"{ON}ortme_olcumu.json",
    "mukerrer": CIKTI / f"{ON}mukerrer_adaylari.json",
    "numara_goz": CIKTI / f"{ON}numara_goz.json",
    "ham": CIKTI / f"{ON}ham_okumalar.json",
}
ITHAL_YOLU = KOK / "scripts" / "kitap" / "tur345tyt_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0068_trt345_konu_agaci.py"
ARAC_YOLLARI = [
    ITHAL_YOLU,
    AGAC_YOLU,
    KOK / "scripts" / "kitap" / "tur345tyt_tarama.py",
    KOK / "scripts" / "kitap" / "tur345tyt_anahtar.py",
    KOK / "scripts" / "kitap" / "tur345tyt_harita.py",
    KOK / "scripts" / "kitap" / "tur345tyt_kutu.py",
    KOK / "scripts" / "kitap" / "tur345tyt_kirp.py",
    KOK / "scripts" / "kitap" / "tur345tyt_metin_harness.py",
    KOK / "scripts" / "kitap" / "tur345tyt_mukerrer.py",
]

BEKLENEN_SORU = 2070
BEKLENEN_TEST = 207
BEKLENEN_UNITE = 8
BEKLENEN_KONU = 27
BAYRAKLAR = {
    "mukerrer_aday": 28,
    "cikmis_soru": 71,
    "okuyucu_diski_ortme": 260,
    "kaynak_kusuru": 371,
    "db_hash_carpismasi": 4,
    "sik_tekrar": 4,
    "sikler_gorsel": 3,
    "diger_kaynak_cevap_farki": 4,
    "diger_kaynak_sik_sirasi_farkli": 3,
}
CEVAP_KANALI = {
    "iki_okuma+glif": 2064,
    "iki_okuma_farki+goz(5-6x)+glif": 3,
    "iki_okuma+glif_uyumsuz+goz_teyidi(5x)": 3,
}
SAYFA_ILK, SAYFA_SON = 6, 431  # basili = dosya
KART_G, KART_Y = 742, 979


def _oku(yol: Path) -> dict:
    return json.loads(yol.read_text("utf-8"))


@pytest.fixture(scope="module")
def paket() -> dict[str, dict]:
    p = {ad: _oku(y) for ad, y in YOLLAR.items() if y.exists()}
    assert "numara_goz" not in p  # bu kitapta gozle listelenen ortme yok
    p["numara_goz"] = {"dosyalar": []}
    return p


def _bagla(p: dict[str, dict]) -> list[dict]:
    return si.satirlari_bagla(
        p["veri"],
        p["harita"],
        p["kutular"],
        p["anahtar"],
        ortme=p["ortme"],
        mukerrer=p["mukerrer"],
        numara_goz=p["numara_goz"],
        goz_hucreleri=si.goz_hucreleri(p["ham"], p["harita"]),
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
    return _modul("agac0068i", AGAC_YOLU)


def _ad(k: dict) -> str:
    return k["pipeline_metadata"]["kaynak_gorseli"].removesuffix(".png")


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


def test_cevaplar_anahtarla_birebir(kayitlar: list[dict], paket: dict) -> None:
    anahtar = {
        f"{c['birim']}_{c['soru']:02d}": c["cevap"]
        for c in paket["anahtar"]["cevaplar"]
    }
    for k in kayitlar:
        assert k["correct_answer"] == anahtar[_ad(k)], _ad(k)


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


def test_test_ve_ici_sira(kayitlar: list[dict], paket: dict) -> None:
    assert (
        len({k["pipeline_metadata"]["birim_kodu"] for k in kayitlar}) == BEKLENEN_TEST
    )
    goz = set(paket["numara_goz"]["dosyalar"])
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        if pm["soru_no_basili"] is None:
            assert "numara_ortulu" in pm["bayraklar"]
            assert pm["soru_no_kaynagi"] == "test_ici_sira_numara_ortulu"
            assert (
                pm["kirpim_capa_kanali"] == "simge"
                or pm["okuyucu_diski_ortme"]
                or _ad(k) in goz
            ), _ad(k)
        else:
            assert pm["soru_no_basili"] == pm["birim_ici_sira"], k["id"]


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


def test_dugum_kodlari_migration_ile_ayni(kayitlar: list[dict], agac: object) -> None:
    unite = {kod for kod, _ in agac.UNITELER}  # type: ignore[attr-defined]
    konu = {kod: u for kod, _, u in agac.KONULAR}  # type: ignore[attr-defined]
    assert len(unite) == BEKLENEN_UNITE and len(konu) == BEKLENEN_KONU
    assert (agac.KOK,) == si.KOK_KODLARI  # type: ignore[attr-defined]
    assert {k["konu_kodu"] for k in kayitlar} <= unite | set(konu)
    assert set(konu) <= {k["konu_kodu"] for k in kayitlar}
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        if pm["test_turu"] == "KA":
            assert pm["konu_eslesme_duzeyi"] == "unite" and k["konu_kodu"] in unite
            assert pm["konu_adi"] is None
        else:
            assert pm["konu_eslesme_duzeyi"] == "konu" and k["konu_kodu"] in konu
            assert pm["konu_adi"]
    assert {k["subject_area"] for k in kayitlar} == {"TURKCE"}
    tur = Counter(k["pipeline_metadata"]["test_turu"] for k in kayitlar)
    assert set(tur) == {"KO", "OT", "OR", "KA"} and sum(tur.values()) == BEKLENEN_SORU


def test_ortak_parca_gorsel_boyu(kayitlar: list[dict], paket: dict) -> None:
    """Ortak parcali soruda gorsel = parca + 8 px + soru; digerlerinde kutu."""
    ortak = {
        f"{k['birim']}_{k['soru']:02d}": k["ortak_parca"]
        for k in paket["kutular"]["kutular"]
        if k.get("ortak_parca")
    }
    assert len(ortak) == 10 and si.ORTAK_ARALIK == 8
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        x0, y0, x1, y1 = pm["kirpim_kutusu"]
        o = ortak.get(_ad(k))
        if o is None:
            assert pm["gorsel_boyu"] == [x1 - x0, y1 - y0]
            assert pm["ortak_parca_ilk_soru"] is None
        else:
            p = o["kutu"]
            assert pm["gorsel_boyu"] == [x1 - x0, y1 - y0 + p[3] - p[1] + 8]
            assert pm["ortak_parca_ilk_soru"] == o["ilk_soru"]
            assert pm["ortak_parca_basligi"]
            assert pm["gorsel_kaynagi"] == "ortak_parca_ustte_8px+soru_kirpimi"


def test_yabanci_hash_paragraf_kitabi(kayitlar: list[dict], paket: dict) -> None:
    """4 soru Paragraf kitabinda ayni hash ile var: ayni id, ithal yazmaz."""
    carp = {c["dosya"]: c["db_id"] for c in paket["mukerrer"]["db_tam_hash_carpismasi"]}
    assert len(carp) == 4
    for k in kayitlar:
        if _ad(k) in carp:
            assert k["id"] == carp[_ad(k)]


# ------------------------------------------------------------ 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(si.KAYNAK_ADI, kayitli_olmali=True)
    assert cakisan_kaynak(si.KAYNAK_ADI, list(KAYNAK_KAYITLARI)) is None
    kayit = KAYNAK_KAYITLARI[si.KAYNAK_ADI]
    assert kayit["onek"] == si.ONEK == "TRT345"
    assert kayit["ithal_araci"] == si.ITHAL_ARACI


@pytest.mark.parametrize("yol", ARAC_YOLLARI, ids=lambda p: p.name)
def test_arac_kaynak_dosyalari_ascii(yol: Path) -> None:
    assert all(b < 128 for b in yol.read_bytes()), yol.name


# ----------------------------------------------------------- 5. durustluk


def test_ithal_pasif_sozlesmesi() -> None:
    kolon, deger = si._QB.split("VALUES")
    assert "is_active, is_public" in " ".join(kolon.split())
    assert "FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE" in deger
    assert "NULL, %(question_image_url)s" in si._QC
    assert "'TYT', %(subject_area)s" in si._QM and "'PENDING'" in si._QM


def test_cozum_uydurulmuyor(kayitlar: list[dict]) -> None:
    assert all(k["explanation"] is None for k in kayitlar)
    assert "cozulmedi" in si.URETIM_NOTU
    assert all(
        k["pipeline_metadata"]["cozum_dogrulamasi"] == "yapilmadi_urun_karari"
        for k in kayitlar
    )


def test_cikmis_sorular_etiketten(kayitlar: list[dict]) -> None:
    cikmis = [k for k in kayitlar if k["pipeline_metadata"]["cikmis_soru"]]
    assert len(cikmis) == 71
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        if pm["cikmis_soru"]:
            assert k["osym_format_compliant"] is True
            sinav, yil = si.etiket_ayristir(pm["cikmis_etiketi"])
            assert (
                (pm["sinav"], pm["sinav_yili"])
                == (sinav, yil)
                == (sinav, k["osym_year"])
            )
            assert pm["sinav"] in ("TYT", "MSU") and 2018 <= yil <= 2025
        else:
            assert k["osym_year"] is None and k["osym_format_compliant"] is False


def test_etiket_ayristir() -> None:
    assert si.etiket_ayristir("MS\xdc - 2022") == ("MSU", 2022)
    assert si.etiket_ayristir("TYT - 2024") == ("TYT", 2024)
    assert si.etiket_ayristir("TYT") == (None, None)
    assert si.etiket_ayristir(None) == (None, None)


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


def test_okunamaz_isaret_yok(kayitlar: list[dict]) -> None:
    assert not any(
        "okunamaz_isaret" in k["pipeline_metadata"]["bayraklar"] for k in kayitlar
    )


def test_mukerrer_bayraklari_olcumle_ayni(kayitlar: list[dict], paket: dict) -> None:
    muk = paket["mukerrer"]
    carpisan = {
        _ad(k) for k in kayitlar if k["pipeline_metadata"]["db_hash_carpismasi"]
    }
    assert carpisan == {c["dosya"] for c in muk["db_tam_hash_carpismasi"]}
    guclu = {a["dosya"] for a in muk["adaylar"] if a["guclu"]}
    assert {
        _ad(k) for k in kayitlar if k["pipeline_metadata"]["mukerrer_aday"]
    } == guclu
    fark = [k for k in kayitlar if k["pipeline_metadata"]["diger_kaynak_cevap_farki"]]
    guclu_fark = [c for c in muk["cevap_farki"] if c["guclu"]]
    assert {_ad(k) for k in fark} == {
        c["dosya"] for c in guclu_fark if c["db_dogrusu_bizde"] != c["bizim_cevap"]
    }
    sira = {
        _ad(k)
        for k in kayitlar
        if k["pipeline_metadata"]["diger_kaynak_sik_sirasi_farkli"]
    }
    assert sira == {
        c["dosya"] for c in guclu_fark if c["db_dogrusu_bizde"] == c["bizim_cevap"]
    }
    # bizim cevap basili anahtar; diger kaynagin cevabi yalniz bilgi
    for k in fark:
        assert (
            k["correct_answer"]
            != k["pipeline_metadata"]["diger_kaynak_cevap_farki"]["db_cevap"]
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


def _m_test_sil(p: dict) -> None:
    del p["harita"]["testler"][10]


def _m_unite_sil(p: dict) -> None:
    del p["harita"]["uniteler"][3]


def _m_ayni_kirpim_iki_kez(p: dict) -> None:
    p["veri"]["sorular"][1] = copy.deepcopy(p["veri"]["sorular"][0])


def _m_etiket_fazla(p: dict) -> None:
    p["veri"]["sorular"][7]["etiket"] = "TYT - 2023"


def _m_etiket_bicimsiz(p: dict) -> None:
    s = next(s for s in p["veri"]["sorular"] if s.get("etiket"))
    s["etiket"] = "ORIJINAL"


YAPISAL: list[tuple[str, Callable[[dict], None]]] = [
    ("metinden soru silindi", _m_soru_sil),
    ("kirpim kutusu silindi", _m_kutu_sil),
    ("anahtardan cevap silindi", _m_anahtar_sil),
    ("metin kanalina cevap sizdi", _m_cevap_sizdi),
    ("haritadan test silindi", _m_test_sil),
    ("haritadan unite silindi", _m_unite_sil),
    ("ayni kirpim iki kez okundu", _m_ayni_kirpim_iki_kez),
    ("fazladan cikmis etiketi", _m_etiket_fazla),
    ("ayrismayan etiket", _m_etiket_bicimsiz),
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
        s[0]["konu_kodu"] = "TAR.GENEL"

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
        i = next(i for i, x in enumerate(s) if not x.get("sekil_var"))
        j = next(j for j, x in enumerate(s) if j > i and not x.get("sekil_var"))
        for alan in ("govde", "sikler"):
            s[j][alan] = copy.deepcopy(s[i][alan])

    assert any("ayni hash" in h for h in _kayit_boz(paket, boz))


def test_on_kontrol_cikmis_yil_tutarsizligi(kayitlar: list[dict]) -> None:
    k = copy.deepcopy(kayitlar)
    x = next(x for x in k if x["pipeline_metadata"]["cikmis_soru"])
    x["osym_year"] = None
    assert any("cikmis" in h for h in si._on_kontrol(k))


def test_basili_numara_kaymasi_baglamada_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    s = next(s for s in p["veri"]["sorular"] if s["basili_no"] is not None)
    s["basili_no"] += 1
    with pytest.raises(ValueError, match="basili"):
        _bagla(p)


def test_ortulu_olmayan_null_numara_durur(paket: dict) -> None:
    """Numara capali (simgesiz) ve ortmesiz sutunda null numara kabul edilmez.

    Bu kitapta tum capalar simge; kapinin calistigi capa kanali numaraya
    cevrilmis ortmesiz bir kutuda gosterilir.
    """
    p = copy.deepcopy(paket)
    ortulen = {(o["birim"], o["soru"]) for o in p["ortme"]["ortme"]}
    k = next(
        k for k in p["kutular"]["kutular"] if (k["birim"], k["soru"]) not in ortulen
    )
    k["capa_kanali"] = "numara"
    ad = f"{k['birim']}_{k['soru']:02d}"
    next(s for s in p["veri"]["sorular"] if s["dosya"] == ad)["basili_no"] = None
    with pytest.raises(ValueError, match="basili None"):
        _bagla(p)


def test_test_unitesi_haritada_yoksa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["unite"] = "TUR-345T25-U99"
    with pytest.raises((ValueError, KeyError)):
        _bagla(p)


def test_kutu_baska_soruyu_gosteriyorsa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["kutular"]["kutular"][0]["sutun_sira"] += 1
    with pytest.raises(ValueError, match="ayni soruyu"):
        _bagla(p)


def test_kutu_test_sayfasi_disindaysa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["sayfalar"] = [999]
    with pytest.raises(ValueError, match="testin sayfalarinda"):
        _bagla(p)


def test_goz_hucreleri_iki_kanal(paket: dict) -> None:
    goz = si.goz_hucreleri(paket["ham"], paket["harita"])
    assert goz == {
        ("TRT345-T071", 4): "iki_okuma_farki+goz(5-6x)+glif",
        ("TRT345-T086", 7): "iki_okuma_farki+goz(5-6x)+glif",
        ("TRT345-T173", 4): "iki_okuma_farki+goz(5-6x)+glif",
        ("TRT345-T120", 3): "iki_okuma+glif_uyumsuz+goz_teyidi(5x)",
        ("TRT345-T143", 10): "iki_okuma+glif_uyumsuz+goz_teyidi(5x)",
        ("TRT345-T180", 8): "iki_okuma+glif_uyumsuz+goz_teyidi(5x)",
    }


def test_goz_hucresi_bilinmeyen_testte_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["ham"]["goz_kararlari"]["farklar"]["T999#1"] = "A"
    with pytest.raises(ValueError, match="haritada yok"):
        si.goz_hucreleri(p["ham"], p["harita"])


def test_konu_testi_yanlis_uniteye_baglanirsa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    t = next(t for t in p["harita"]["testler"] if t["duzey"] == "konu")
    t["dugum"] = "TUR-345T25-U02-K01" if "U01" in t["unite"] else "TUR-345T25-U01-K01"
    with pytest.raises(ValueError, match="unitesi"):
        _bagla(p)


def test_karma_disi_test_unite_dugumune_baglanirsa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    t = next(t for t in p["harita"]["testler"] if t["tur"] == "KO")
    t["duzey"], t["dugum"] = "unite", t["unite"]
    with pytest.raises(ValueError, match="tutarsiz"):
        _bagla(p)


def test_on_kontrol_taninmayan_ders(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["ders"] = "KIMYA"

    assert any("ders" in h for h in _kayit_boz(paket, boz))
