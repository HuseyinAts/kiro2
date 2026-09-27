"""2019-2020 ACIL TYT Matematik Soru Bankasi ithalinin kapilari.

Canli DB istemez; veri setini, konu haritasini, kirpim kutularini, cevap
anahtarini, ortme olcumunu, mukerrer adaylarini ve ithal script'ini
DOSYADAN okur -- CI'da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU  -- 1203 kayit, 5 sik, dolu cevap, benzersiz id.
2. YAPISAL GARANTILER   -- 95 test, basili numara == test ici sira, cevap
                           sizmamis, etiket yok.
3. KONU BAGLANTISI      -- her test tek konu dugumune; bolum tutarli.
4. SOZLESME             -- kaynak adi ASCII, kayitli, cakismasiz.
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

from scripts.kitap import acil1920tyt_ithal as si  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
ON = "acil_1920_tyt_matematik_"
YOLLAR = {
    "veri": CIKTI / f"{ON}metin.json",
    "harita": CIKTI / f"{ON}konu_haritasi.json",
    "kutular": CIKTI / f"{ON}kirpim_kutulari.json",
    "anahtar": CIKTI / f"{ON}cevap_anahtari.json",
    "ortme": CIKTI / f"{ON}ortme_olcumu.json",
    "mukerrer": CIKTI / f"{ON}mukerrer_adaylari.json",
    "ham": CIKTI / f"{ON}ham_okumalar.json",
}
ITHAL_YOLU = KOK / "scripts" / "kitap" / "acil1920tyt_ithal.py"
AGAC_YOLU = KOK / "alembic" / "versions" / "0071_acl20t_konu_agaci.py"
ARAC_YOLLARI = [
    ITHAL_YOLU,
    AGAC_YOLU,
    KOK / "alembic" / "versions" / "0072_acl20t_eski_hat_pasif.py",
    KOK / "alembic" / "versions" / "0073_acl20t_beta_onay.py",
    *(
        KOK / "scripts" / "kitap" / f"acil1920tyt_{ad}.py"
        for ad in (
            "tarama",
            "anahtar",
            "harita",
            "kutu",
            "kirp",
            "metin_harness",
            "mukerrer",
        )
    ),
    KOK / "scripts" / "kitap" / "kaynak_sozlesmesi.py",
]

BEKLENEN_SORU = 1203
BEKLENEN_TEST = 95
BEKLENEN_BOLUM = 17
BEKLENEN_KONU = 32
BAYRAKLAR = {
    "kaynak_kusuru": 360,
    "okuyucu_diski_ortme": 234,
    "okunamaz_isaret": 192,
    "mukerrer_aday": 13,
    "sik_tekrar": 24,
    "sikler_gorsel": 28,
    "db_hash_carpismasi": 2,
}
CEVAP_KANALI = {"iki_okuma+glif": 1133, "iki_okuma+goz(5x)": 70}
KART_G, KART_Y = 742, 979


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
        goz_hucreleri=si.goz_hucreleri(p["ham"], p["harita"]),
    )


@pytest.fixture(scope="module")
def kayitlar(paket: dict[str, dict]) -> list[dict]:
    k = [si.kayit_uret(r) for r in _bagla(paket)]
    si.sekil_ikizleri(k)
    return k


@pytest.fixture(scope="module")
def agac() -> object:
    spec = importlib.util.spec_from_file_location("agac0071i", AGAC_YOLU)
    assert spec and spec.loader
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


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


def test_sayfa_ve_basili_sayfa(kayitlar: list[dict], paket: dict) -> None:
    test_sayfasi = {p for t in paket["harita"]["testler"] for p in t["sayfalar"]}
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["basili_sayfa"] == pm["sayfa_dosya_no"] == k["source_page"]
        assert k["source_page"] in test_sayfasi


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


def test_test_ve_ici_sira(kayitlar: list[dict]) -> None:
    assert (
        len({k["pipeline_metadata"]["birim_kodu"] for k in kayitlar}) == BEKLENEN_TEST
    )
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["soru_no_basili"] == pm["birim_ici_sira"], k["id"]
        assert pm["soru_no_kaynagi"] == "basili"
        assert pm["kirpim_capa_kanali"] == "kirmizi_basili_numara"


def test_cevap_kanali_dagilimi(kayitlar: list[dict]) -> None:
    assert (
        dict(Counter(k["pipeline_metadata"]["cevap_okuma_kanali"] for k in kayitlar))
        == CEVAP_KANALI
    )


def test_goz_kanali_glif_disi_testler(kayitlar: list[dict], paket: dict) -> None:
    disi = {f"ACL20T-T{t:03d}" for t in paket["ham"]["glif"]["kapsam_disi_test"]}
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert (pm["cevap_okuma_kanali"] == "iki_okuma+goz(5x)") == (
            pm["birim_kodu"] in disi
        )


# ------------------------------------------------- 3. konu baglantisi


def test_bir_test_tek_konuya_baglanir(kayitlar: list[dict]) -> None:
    dugum: dict[str, set[str]] = {}
    for k in kayitlar:
        dugum.setdefault(k["pipeline_metadata"]["birim_kodu"], set()).add(
            k["konu_kodu"]
        )
    assert all(len(v) == 1 for v in dugum.values())


def test_dugum_kodlari_migration_ile_ayni(kayitlar: list[dict], agac: object) -> None:
    bolum = {kod for kod, _ in agac.BOLUMLER}  # type: ignore[attr-defined]
    konu = {kod: b for kod, _, b in agac.KONULAR}  # type: ignore[attr-defined]
    assert len(bolum) == BEKLENEN_BOLUM and len(konu) == BEKLENEN_KONU
    assert (agac.KOK,) == si.KOK_KODLARI  # type: ignore[attr-defined]
    assert {k["konu_kodu"] for k in kayitlar} == set(konu)
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        assert pm["konu_eslesme_duzeyi"] == "konu" and pm["konu_adi"]
        assert konu[k["konu_kodu"]] == pm["bolum_kodu"] and pm["bolum_adi"]
    assert {k["subject_area"] for k in kayitlar} == {"MATEMATIK"}


def test_gorsel_boyu_kutudan(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        pm = k["pipeline_metadata"]
        x0, y0, x1, y1 = pm["kirpim_kutusu"]
        assert pm["gorsel_boyu"] == [x1 - x0, y1 - y0]
        assert 0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y, k["id"]
        assert k["question_image_url"] == (
            f"/static/crops/{si.CROP_ONEK}/{pm['kaynak_gorseli']}"
        )


def test_sekil_ikizi_yok(kayitlar: list[dict]) -> None:
    assert not any(
        "sekil_ikizi" in k["pipeline_metadata"]["bayraklar"] for k in kayitlar
    )


# ------------------------------------------------------------ 4. sozlesme


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(si.KAYNAK_ADI, kayitli_olmali=True)
    assert cakisan_kaynak(si.KAYNAK_ADI, list(KAYNAK_KAYITLARI)) is None
    kayit = KAYNAK_KAYITLARI[si.KAYNAK_ADI]
    assert kayit["onek"] == si.ONEK == "ACL20T"
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


def test_cikmis_soru_yok(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        assert not k["pipeline_metadata"]["cikmis_soru"]
        assert k["osym_year"] is None and k["osym_format_compliant"] is False


def test_olculen_bayrak_capalari(kayitlar: list[dict]) -> None:
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    assert dict(bayrak) == BAYRAKLAR


def test_okunamaz_isaret_metinle_ayni(kayitlar: list[dict]) -> None:
    for k in kayitlar:
        gorunen = k["question_text"] + "".join(k["secenekler"].values())
        assert ("[??]" in gorunen) == (
            "okunamaz_isaret" in k["pipeline_metadata"]["bayraklar"]
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
    assert not [
        k for k in kayitlar if k["pipeline_metadata"]["diger_kaynak_cevap_farki"]
    ]
    assert not [
        k for k in kayitlar if k["pipeline_metadata"]["diger_kaynak_sik_sirasi_farkli"]
    ]


def test_hash_carpismasi_id_farkli(kayitlar: list[dict], paket: dict) -> None:
    """Carpisan eski satirlarin id'si baska semada: bizim id uuid5(hash), ithal yazar."""
    carp = {c["dosya"]: c["db_id"] for c in paket["mukerrer"]["db_tam_hash_carpismasi"]}
    for k in kayitlar:
        if _ad(k) in carp:
            assert k["id"] != carp[_ad(k)]


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


def _m_konu_sil(p: dict) -> None:
    del p["harita"]["konular"][3]


def _m_ayni_kirpim_iki_kez(p: dict) -> None:
    p["veri"]["sorular"][1] = copy.deepcopy(p["veri"]["sorular"][0])


def _m_etiket_fazla(p: dict) -> None:
    p["veri"]["sorular"][7]["etiket"] = "TYT - 2019"


YAPISAL: list[tuple[str, Callable[[dict], None]]] = [
    ("metinden soru silindi", _m_soru_sil),
    ("kirpim kutusu silindi", _m_kutu_sil),
    ("anahtardan cevap silindi", _m_anahtar_sil),
    ("metin kanalina cevap sizdi", _m_cevap_sizdi),
    ("haritadan test silindi", _m_test_sil),
    ("haritadan bolum silindi", _m_bolum_sil),
    ("haritadan konu silindi", _m_konu_sil),
    ("ayni kirpim iki kez okundu", _m_ayni_kirpim_iki_kez),
    ("fazladan cikmis etiketi", _m_etiket_fazla),
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
        s[0]["konu_kodu"] = "MAT.GENEL"

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


def test_on_kontrol_taninmayan_ders(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        s[0]["ders"] = "KIMYA"

    assert any("ders" in h for h in _kayit_boz(paket, boz))


def test_on_kontrol_sekilsiz_cift_okuma_durur(paket: dict) -> None:
    def boz(s: list[dict]) -> None:
        i = next(i for i, x in enumerate(s) if not x.get("sekil_var"))
        j = next(j for j, x in enumerate(s) if j > i and not x.get("sekil_var"))
        for alan in ("govde", "sikler"):
            s[j][alan] = copy.deepcopy(s[i][alan])

    assert any("ayni hash" in h for h in _kayit_boz(paket, boz))


def test_basili_numara_kaymasi_baglamada_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["veri"]["sorular"][5]["basili_no"] += 1
    with pytest.raises(ValueError, match="basili"):
        _bagla(p)


def test_null_numara_durur(paket: dict) -> None:
    """Bu kitapta null numara yok; gelirse baglama durur."""
    p = copy.deepcopy(paket)
    p["veri"]["sorular"][5]["basili_no"] = None
    with pytest.raises(ValueError, match="basili None"):
        _bagla(p)


def test_test_bolumu_haritada_yoksa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["harita"]["testler"][0]["bolum"] = "MAT-ACL20T-B99"
    with pytest.raises(ValueError, match="bolum"):
        _bagla(p)


def test_konu_baska_bolumdeyse_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    t = next(t for t in p["harita"]["testler"] if t["bolum"] == "MAT-ACL20T-B02")
    t["konu"] = "MAT-ACL20T-B03-K01"
    with pytest.raises(ValueError, match="bolumu"):
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


def test_goz_hucreleri_glif_disi_testler(paket: dict) -> None:
    goz = si.goz_hucreleri(paket["ham"], paket["harita"])
    assert len(goz) == 70
    assert {b for b, _ in goz} == {f"ACL20T-T{t:03d}" for t in (20, 25, 31, 40, 67, 82)}


def test_goz_testi_haritada_yoksa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["ham"]["goz_c"]["testler"]["999"] = "A"
    with pytest.raises(ValueError, match="haritada yok"):
        si.goz_hucreleri(p["ham"], p["harita"])


def test_goz_testi_hucre_sayisi_farkliysa_durur(paket: dict) -> None:
    p = copy.deepcopy(paket)
    p["ham"]["goz_c"]["testler"]["20"] += "A"
    with pytest.raises(ValueError, match="soru sayisi"):
        si.goz_hucreleri(p["ham"], p["harita"])
