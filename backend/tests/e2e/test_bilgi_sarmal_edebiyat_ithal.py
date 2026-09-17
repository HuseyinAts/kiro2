"""Bilgi Sarmal AYT Edebiyat ithalinin koruma testleri.

Canli DB istemez; veri setini, konu agacini, ithal script'ini ve
migration'i dosyadan okur -- CI'da da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU   -- 5 sik, dolu cevap, benzersiz hash/id, NFC.
2. ANAHTAR KAPILARI      -- test ici numara surekliligi, soru sayisi,
                            anahtar sayfalari, iki cevap kaynagi.
3. KONU AGACI            -- her kodun agacta olmasi, onek kurali,
                            karma testlerin BOLUM dugumune baglanmasi.
4. SOZLESME              -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK             -- ortme isaretleniyor, cozum uydurulmuyor,
                            ithal PASIF, sekil borcu bayrakli.
6. MIGRATION ZINCIRI     -- 0031 kimligi, ASCII, agacla birebir.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import bilgi_sarmal_edebiyat_ithal as bs  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
VERI_YOLU = CIKTI / "bilgi_sarmal_edebiyat_sorular.json"
AGAC_YOLU = CIKTI / "bilgi_sarmal_edebiyat_konu_agaci.json"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_SORU = 1597
BEKLENEN_TEST = 130
BEKLENEN_ANAHTAR_CEVAP = 1572
BEKLENEN_SORDUK = 25
BEKLENEN_ORTME = 2
BEKLENEN_SEKIL = 64
BEKLENEN_DIZGI_KUSURU = 8
BEKLENEN_BOLUM = 5
BEKLENEN_KONU = 53
ILK_SAYFA, SON_SAYFA = 11, 407
ANAHTAR_SAYFALARI = {409, 410, 411, 412, 413, 414, 415, 416}


def _ascii_kucuk(s: str) -> str:
    """Turkce harfleri ASCII'ye katlayip kucultur (yalniz karsilastirma icin).

    Kaynak dosya ASCII kalsin diye desenler de ASCII yazilir.
    """
    esle = {
        chr(0x0131): "i",
        chr(0x0130): "i",
        chr(0x015F): "s",
        chr(0x015E): "s",
        chr(0x011F): "g",
        chr(0x011E): "g",
        chr(0x00FC): "u",
        chr(0x00DC): "u",
        chr(0x00F6): "o",
        chr(0x00D6): "o",
        chr(0x00E7): "c",
        chr(0x00C7): "c",
        chr(0x00EE): "i",
        chr(0x00C2): "a",
        chr(0x00E2): "a",
    }
    return "".join(esle.get(c, c) for c in s).lower()


@pytest.fixture(scope="module")
def veri() -> list[dict]:
    ham: list[dict] = json.loads(VERI_YOLU.read_text(encoding="utf-8"))
    return ham


@pytest.fixture(scope="module")
def agac() -> list[dict]:
    ham: list[dict] = json.loads(AGAC_YOLU.read_text(encoding="utf-8"))
    return ham


# --- 1. VERI SETI BUTUNLUGU -------------------------------------------


def test_veri_seti_boyutu(veri) -> None:
    assert len(veri) == BEKLENEN_SORU


def test_her_soruda_bes_dolu_sik(veri) -> None:
    kusur = [
        r["id"] for r in veri if any(not (r.get(h) or "").strip() for h in "abcde")
    ]
    assert not kusur, kusur[:5]


def test_cevaplar_gecerli_ve_sikka_karsilik_geliyor(veri) -> None:
    for r in veri:
        assert r["correct_answer"] in ("A", "B", "C", "D", "E"), r["id"]
        assert (r[r["correct_answer"].lower()] or "").strip(), r["id"]


def test_hash_ve_id_benzersiz(veri) -> None:
    assert len({r["soru_hash"] for r in veri}) == len(veri)
    assert len({r["id"] for r in veri}) == len(veri)


def test_metin_nfc_ve_temiz(veri) -> None:
    for r in veri:
        s = r["question_text"]
        assert s == unicodedata.normalize("NFC", s), r["id"]
        assert not re.search(r"\\u[0-9a-fA-F]{4}", s), r["id"]


def test_sayfa_araligi(veri) -> None:
    assert min(r["sayfa"] for r in veri) >= ILK_SAYFA
    assert max(r["sayfa"] for r in veri) <= SON_SAYFA


# --- 2. ANAHTAR KAPILARI ----------------------------------------------


def test_test_sayisi(veri) -> None:
    assert len({r["test_index"] for r in veri if r["test_index"]}) == BEKLENEN_TEST


def test_test_ici_numara_surekliligi(veri) -> None:
    """Her testte soru numaralari 1..N kesintisiz olmali."""
    gruplar: dict[int, list[dict]] = {}
    for r in veri:
        if r["kaynak_bolumu"] != "test":
            continue
        gruplar.setdefault(r["test_index"], []).append(r)
    assert len(gruplar) == BEKLENEN_TEST
    for ti, rs in gruplar.items():
        nos = sorted(r["soru_no"] for r in rs)
        assert nos == list(range(1, len(nos) + 1)), (ti, nos[:20])


def test_okunan_soru_sayisi_anahtarla_ayni(veri) -> None:
    """SORDUK tekrari dusuldukten sonra her test kendi sayisini tutmali."""
    gruplar: dict[int, list[dict]] = {}
    for r in veri:
        if r["kaynak_bolumu"] != "test":
            continue
        gruplar.setdefault(r["test_index"], []).append(r)
    for ti, rs in gruplar.items():
        assert len(rs) == rs[0]["test_soru_sayisi"], ti


def test_her_test_sorusu_kendi_testinin_sayfa_araliginda(veri) -> None:
    for r in veri:
        if r["kaynak_bolumu"] != "test":
            continue
        assert r["test_bas_sayfa"] <= r["sayfa"] <= r["test_son_sayfa"], r["id"]


def test_anahtar_sayfalari_kitabin_sonunda(veri) -> None:
    kullanilan = {r["anahtar_sayfa"] for r in veri if r["anahtar_sayfa"]}
    assert kullanilan == ANAHTAR_SAYFALARI


def test_iki_cevap_kaynagi_ve_sayilari(veri) -> None:
    """Kitabin IKI basili cevap kaynagi var; ikisi de kayitli."""
    sayac = Counter(r["cevap_kaynagi"] for r in veri)
    assert set(sayac) == {
        "kitap_sonu_anahtari",
        "sayfa_ici_kirmizi_sik",
        "kitap_sonu_anahtari__sayfa_ici_kirmizi_sik_teyitli",
    }
    assert sayac["sayfa_ici_kirmizi_sik"] == BEKLENEN_SORDUK
    # Kitap sonu anahtarindan cevap alan satirlar: 1572 test sorusu
    # (3'u ayrica kirmizi sikla TEYITLI oldugu icin ayri anahtarda sayilir).
    anahtarli = (
        sayac["kitap_sonu_anahtari"]
        + sayac["kitap_sonu_anahtari__sayfa_ici_kirmizi_sik_teyitli"]
    )
    assert anahtarli == BEKLENEN_ANAHTAR_CEVAP
    assert anahtarli + BEKLENEN_SORDUK == BEKLENEN_SORU


def test_sorduk_tekrari_iki_kaynakla_teyitli(veri) -> None:
    """Kitap 3 soruyu iki yerde basmis; iki bagimsiz kaynak ayni harfi verdi."""
    tekrar = [r for r in veri if r.get("sorduk_tekrari")]
    assert len(tekrar) == 3
    for r in tekrar:
        assert r["cevap_kaynagi"].endswith("kirmizi_sik_teyitli"), r["id"]
        assert r["sorduk_sayfa"] in (258, 346, 406), r["id"]


def test_harf_dagilimi_tek_harfe_cokmemis(veri) -> None:
    dag = Counter(r["correct_answer"] for r in veri)
    assert sum(dag.values()) == BEKLENEN_SORU
    assert set(dag) == set("ABCDE")
    for h, n in dag.items():
        assert 0.10 <= n / BEKLENEN_SORU <= 0.35, (h, n)


# --- 3. KONU AGACI ----------------------------------------------------


def test_agac_bes_bolum_ve_elliuc_konu(agac) -> None:
    assert sum(1 for a in agac if a["seviye"] == 2) == BEKLENEN_BOLUM
    assert sum(1 for a in agac if a["seviye"] == 3) == BEKLENEN_KONU


def test_bolum_numaralari_kesintisiz(agac) -> None:
    siralar = sorted(a["sira"] for a in agac if a["seviye"] == 2)
    assert siralar == list(range(1, BEKLENEN_BOLUM + 1))


def test_bolumler_edb_kokune_bagli(agac) -> None:
    for a in agac:
        if a["seviye"] == 2:
            assert a["ust"] == bs.EDB_KOK_KODU, a["kod"]


def test_her_konu_kodu_agacta_var(veri, agac) -> None:
    kodlar = {a["kod"] for a in agac}
    eksik = {r["konu_kodu"] for r in veri} - kodlar
    assert not eksik, sorted(eksik)


def test_konu_kodu_oneki(veri) -> None:
    for r in veri:
        assert r["konu_kodu"].startswith(bs.KOD_ONEKI), r["id"]


def test_karma_testler_bolum_dugumune_bagli(veri) -> None:
    """SARMAL TEST / OSYM TIPI / Roman Karma bir KONU degildir."""
    karma = re.compile(r"sarmal test|osym|karma|sorduk")
    for r in veri:
        if karma.search(_ascii_kucuk(r["test_konu"])):
            assert r["konu_eslesme_duzeyi"] == "bolum", r["id"]
            assert r["konu_kodu"] == r["bolum_kodu"], r["id"]
        else:
            assert r["konu_eslesme_duzeyi"] == "konu", r["id"]


def test_agac_adlari_ascii(agac) -> None:
    for a in agac:
        assert a["ad_ascii"].isascii(), a["kod"]


def test_agac_ust_dugumleri_tanimli(agac) -> None:
    kodlar = {a["kod"] for a in agac} | {bs.EDB_KOK_KODU}
    for a in agac:
        assert a["ust"] in kodlar, a["kod"]


# --- 4. SOZLESME ------------------------------------------------------


def test_kaynak_adi_sozlesmeye_uygun() -> None:
    kaynak_adi_dogrula(bs.KAYNAK_ADI, kayitli_olmali=True)
    assert bs.KAYNAK_ADI in KAYNAK_KAYITLARI
    assert bs.KAYNAK_ADI.isascii()
    assert "  " not in bs.KAYNAK_ADI


def test_kaynak_adi_baska_kayitla_cakismiyor() -> None:
    digerleri = [a for a in KAYNAK_KAYITLARI if a != bs.KAYNAK_ADI]
    assert cakisan_kaynak(bs.KAYNAK_ADI, digerleri) is None


def test_kardes_kitaptan_ayri_kaynak() -> None:
    """TYT Turkce ile AYT Edebiyat AYNI KITAP DEGIL; onekleri de ayri."""
    assert bs.ONEK == "BS_AYT_EDEBIYAT"
    assert KAYNAK_KAYITLARI["Bilgi Sarmal Tyt Turkce Soru Bankasi"]["onek"] != bs.ONEK


def test_ithal_araci_kaydi_script_yoluyla_ayni() -> None:
    assert KAYNAK_KAYITLARI[bs.KAYNAK_ADI]["ithal_araci"] == bs.ITHAL_ARACI


def test_sinav_turu_ve_ders_alani() -> None:
    assert bs.SINAV_TURU == "AYT"
    assert bs.DERS_ALANI == "EDEBIYAT"
    assert "'AYT', 'EDEBIYAT'" in bs._QM


# --- 5. DURUSTLUK -----------------------------------------------------


def test_ortme_sayisi_capa(veri) -> None:
    """Ikinci yakalamadan kurtarma sonrasi kalan ortme; capa olarak yazilir."""
    assert sum(1 for r in veri if r["okuyucu_simgesi_ortmesi"]) == BEKLENEN_ORTME


def test_ortme_bayraga_tasiniyor(veri) -> None:
    """MUTASYON KARSILIGI: _bayraklar bu isareti dusurerse test duser."""
    ortmeli = next(r for r in veri if r["okuyucu_simgesi_ortmesi"])
    temiz = next(r for r in veri if not r["okuyucu_simgesi_ortmesi"])
    sec_o = {h: ortmeli[h.lower()] for h in "ABCDE"}
    sec_t = {h: temiz[h.lower()] for h in "ABCDE"}
    assert "okuyucu_simgesi_ortmesi" in bs._bayraklar(ortmeli, sec_o)
    assert "okuyucu_simgesi_ortmesi" not in bs._bayraklar(temiz, sec_t)


def test_ortme_metadataya_yaziliyor(veri) -> None:
    ortmeli = next(r for r in veri if r["okuyucu_simgesi_ortmesi"])
    pm = bs.kayit_uret(ortmeli)["pipeline_metadata"]
    assert pm["okuyucu_simgesi_ortmesi"] is True
    assert pm["ortulen_metin"]
    assert "okuyucu_simgesi_ortmesi" in pm["bayraklar"]
    assert "ikinci_yakalama" in pm["ortme_kurtarma_kanali"]


def test_sekil_borcu_bayrakli(veri) -> None:
    """Sekil/tablo var ama kirpim yok: ogrenciye sekilsiz gosterilemez."""
    sekilli = [r for r in veri if r["sekil_var"]]
    assert len(sekilli) == BEKLENEN_SEKIL
    pm = bs.kayit_uret(sekilli[0])["pipeline_metadata"]
    assert "gorsel_yok_sekilli" in pm["bayraklar"]
    assert pm["gorsel_kaynagi"] == "yok_soru_kirpimi_uretilmedi"


def test_dizgi_kusuru_bayrakli(veri) -> None:
    kusurlu = [r for r in veri if r["kaynak_kusuru"]]
    assert len(kusurlu) == BEKLENEN_DIZGI_KUSURU
    pm = bs.kayit_uret(kusurlu[0])["pipeline_metadata"]
    assert "kaynak_dizgi_kusuru" in pm["bayraklar"]
    assert pm["kaynak_kusuru"]


def test_cikmis_sorular_yil_tasiyor(veri) -> None:
    cikmis = [r for r in veri if r.get("kaynak_bolumu") == "sorduk_sordular"]
    assert cikmis
    yilli = [r for r in cikmis if r.get("sinav_yili")]
    assert yilli
    pm = bs.kayit_uret(yilli[0])["pipeline_metadata"]
    assert pm["cikmis_soru"] is True
    assert pm["sinav_yili"] == yilli[0]["sinav_yili"]
    assert bs.kayit_uret(yilli[0])["osym_year"] == yilli[0]["sinav_yili"]


def test_cozum_uydurulmuyor(veri) -> None:
    """Kitabin soru sayfalarinda cozum yok; explanation NULL kalir."""
    for r in veri[:50]:
        assert bs.kayit_uret(r)["explanation"] is None


def test_cevap_kaynagi_metadataya_tasiniyor(veri) -> None:
    testli = next(r for r in veri if r["cevap_kaynagi"] == "kitap_sonu_anahtari")
    kirmizi = next(r for r in veri if r["cevap_kaynagi"] == "sayfa_ici_kirmizi_sik")
    pm1 = bs.kayit_uret(testli)["pipeline_metadata"]
    pm2 = bs.kayit_uret(kirmizi)["pipeline_metadata"]
    assert pm1["cevap_kaynagi"] == "kitap_sonu_anahtari"
    assert pm1["anahtar_dogrulamasi"] == bs.ANAHTAR_DOGRULAMASI
    assert pm2["cevap_kaynagi"] == "sayfa_ici_kirmizi_sik"
    assert pm2["anahtar_dogrulamasi"] == bs.KIRMIZI_DOGRULAMASI
    assert pm1["cozum_dogrulamasi"] == "yapilmadi_urun_karari"


def test_ithal_pasif_sozlesmesi() -> None:
    assert "FALSE, FALSE" in bs._QB
    assert "'PENDING'" in bs._QB
    assert "TRUE, 'PENDING'" in bs._QB  # is_ai_generated TRUE


def test_metin_tavani_kayitli(veri) -> None:
    pm = bs.kayit_uret(veri[0])["pipeline_metadata"]
    assert pm["metin_tavani"] == "kaynak_1920x1080_sayfa_karti_728x968"


def test_teyit_duzeltmesi_kayitli(veri) -> None:
    """Teyit orneklemindeki tek icerik duzeltmesi izlenebilir olmali."""
    duzeltilmis = [r for r in veri if r.get("teyit_duzeltmesi")]
    assert len(duzeltilmis) == 1
    r = duzeltilmis[0]
    assert r["sayfa"] == 380 and r["soru_no"] == 22
    assert "evlilik" in r["question_text"]
    assert bs.kayit_uret(r)["pipeline_metadata"]["teyit_duzeltmesi"]


def test_on_kontrol_taninmayan_cevap_kaynagini_reddeder(veri) -> None:
    """MUTASYON KARSILIGI: kaynak adi bozulursa ithal durmali."""
    k = bs.kayit_uret(veri[0])
    k["pipeline_metadata"]["cevap_kaynagi"] = "tahmin"
    hata = bs._on_kontrol([k])
    assert any("cevap kaynagi" in h for h in hata), hata


def test_on_kontrol_yanlis_konu_kodunu_reddeder(veri) -> None:
    k = bs.kayit_uret(veri[0])
    k["konu_kodu"] = "TUR-BS1"
    hata = bs._on_kontrol([k])
    assert any("konu kodu" in h for h in hata), hata


# --- 6. MIGRATION ZINCIRI ---------------------------------------------


def _goc(ad: str):
    yol = KOK / "alembic" / "versions" / ad
    spec = importlib.util.spec_from_file_location(f"_g_{ad}", yol)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, yol


def test_0031_zinciri_ve_ascii() -> None:
    mod, yol = _goc("0031_bilgi_sarmal_edebiyat_agaci.py")
    assert mod.revision == "0031_bs_edebiyat_agac"
    assert mod.down_revision == "0030_bs_kaynak_adi"
    assert len(mod.revision) <= 32
    assert not [b for b in yol.read_bytes() if b > 127]
    assert len(mod.BOLUMLER) == BEKLENEN_BOLUM
    assert len(mod.KONULAR) == BEKLENEN_KONU
    assert mod.EDB_KOK_KODU == bs.EDB_KOK_KODU
    assert mod.KOD_ONEKI == bs.KOD_ONEKI


def test_0031_agacla_birebir(agac) -> None:
    mod, _ = _goc("0031_bilgi_sarmal_edebiyat_agaci.py")
    dosya = {a["kod"] for a in agac}
    goc_kod = {k for _, k, _ in mod.BOLUMLER} | {k for _, _, k, _ in mod.KONULAR}
    assert dosya == goc_kod
    adlar = {a["kod"]: a["ad_ascii"] for a in agac}
    for _sira, kod, ad in mod.BOLUMLER:
        assert adlar[kod] == ad, kod
    for _ust, _sira, kod, ad in mod.KONULAR:
        assert adlar[kod] == ad, kod


def test_0031_edebiyat_alanina_yaziyor() -> None:
    _, yol = _goc("0031_bilgi_sarmal_edebiyat_agaci.py")
    kod = yol.read_text(encoding="utf-8").split('"""', 2)[2]
    assert "'EDEBIYAT'" in kod
    assert "'TURKCE'" not in kod


def test_0031_gunlugu_ve_geri_alinabilirlik() -> None:
    mod, yol = _goc("0031_bilgi_sarmal_edebiyat_agaci.py")
    assert mod.GUNLUK == "bs_edebiyat_konu_gunlugu_0031"
    kod = yol.read_text(encoding="utf-8").split('"""', 2)[2]
    # downgrade soru tasiyan dugume dokunmamali
    assert "primary_topic_id = ANY" in kod
    assert "NOT EXISTS" in kod
