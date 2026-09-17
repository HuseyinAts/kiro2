"""Bilgi Sarmal TYT Turkce ithalinin koruma testleri.

Canli DB istemez; veri setini, konu agacini, ithal script'ini ve iki
migration'i dosyadan okur -- CI'da da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU   -- 5 sik, dolu cevap, benzersiz hash/id.
2. ANAHTAR KAPILARI      -- test ici numara surekliligi, soru sayisi,
                            sayfa araliklarinin kitabi tam kaplamasi.
3. KONU AGACI            -- her kodun agacta olmasi, onek kurali,
                            karma testlerin BOLUM dugumune baglanmasi.
4. SOZLESME              -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK             -- okuyucu simgesi ortmesi isaretleniyor,
                            cozum uydurulmuyor, ithal PASIF.
6. MIGRATION ZINCIRI     -- 0029/0030 kimlikleri ve ASCII.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter
from itertools import pairwise
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import bilgi_sarmal_turkce_ithal as bs  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
    normalize_anahtar,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
VERI_YOLU = CIKTI / "bilgi_sarmal_turkce_sorular.json"
AGAC_YOLU = CIKTI / "bilgi_sarmal_turkce_konu_agaci.json"

BEKLENEN_SORU = 1468
BEKLENEN_TEST = 114
BEKLENEN_ORTME = 451
ILK_SAYFA, SON_SAYFA = 9, 331


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


# --- 2. ANAHTAR KAPILARI ----------------------------------------------


def test_test_sayisi(veri) -> None:
    assert len({r["test_index"] for r in veri}) == BEKLENEN_TEST


def test_test_ici_numara_surekliligi(veri) -> None:
    """Her testte soru numaralari 1..N kesintisiz olmali."""
    gruplar: dict[int, list[dict]] = {}
    for r in veri:
        gruplar.setdefault(r["test_index"], []).append(r)
    for ti, rs in gruplar.items():
        nos = sorted(r["soru_no"] for r in rs)
        assert nos == list(range(1, len(nos) + 1)), (ti, nos[:20])


def test_okunan_soru_sayisi_anahtarla_ayni(veri) -> None:
    gruplar: dict[int, list[dict]] = {}
    for r in veri:
        gruplar.setdefault(r["test_index"], []).append(r)
    for ti, rs in gruplar.items():
        assert len(rs) == rs[0]["test_soru_sayisi"], ti


def test_sayfa_araliklari_kitabi_tam_kapliyor(veri) -> None:
    """114 testin araligi 9-331'i boslksuz ve cakismasiz kaplamali."""
    araliklar = sorted({(r["test_bas_sayfa"], r["test_son_sayfa"]) for r in veri})
    assert len(araliklar) == BEKLENEN_TEST
    assert araliklar[0][0] == ILK_SAYFA
    assert araliklar[-1][1] == SON_SAYFA
    for onceki, sonraki in pairwise(araliklar):
        assert sonraki[0] == onceki[1] + 1, (onceki, sonraki)


def test_her_soru_kendi_testinin_sayfa_araliginda(veri) -> None:
    for r in veri:
        assert r["test_bas_sayfa"] <= r["sayfa"] <= r["test_son_sayfa"], r["id"]


def test_anahtar_sayfalari_kitabin_sonunda(veri) -> None:
    assert {r["anahtar_sayfa"] for r in veri} <= {332, 333, 334, 335, 336}


# --- 3. KONU AGACI ----------------------------------------------------


def test_agac_dokuz_bolum_ve_otuziki_konu(agac) -> None:
    assert sum(1 for a in agac if a["seviye"] == 2) == 9
    assert sum(1 for a in agac if a["seviye"] == 3) == 32


def test_bolum_numaralari_kesintisiz(agac) -> None:
    siralar = sorted(a["sira"] for a in agac if a["seviye"] == 2)
    assert siralar == list(range(1, 10))


def test_her_konu_kodu_agacta_var(veri, agac) -> None:
    kodlar = {a["kod"] for a in agac}
    eksik = {r["konu_kodu"] for r in veri} - kodlar
    assert not eksik, sorted(eksik)


def test_konu_kodu_oneki(veri) -> None:
    for r in veri:
        assert r["konu_kodu"].startswith(bs.KOD_ONEKI), r["id"]


def test_karma_testler_bolum_dugumune_bagli(veri) -> None:
    """Sarmal / OSYM / Simulasyon / Karma / Tarama bir KONU degildir."""
    karma = re.compile(r"sarmal test|osym|simulasyon|karma|tarama testi")
    for r in veri:
        if karma.search(_ascii_kucuk(r["test_konu"])):
            assert r["konu_eslesme_duzeyi"] == "bolum_karma_test", r["id"]
            assert r["konu_kodu"] == r["bolum_kodu"], r["id"]
        else:
            assert r["konu_eslesme_duzeyi"] == "konu", r["id"]


def test_agac_adlari_ascii(agac) -> None:
    for a in agac:
        assert a["ad_ascii"].isascii(), a["kod"]


# --- 4. SOZLESME ------------------------------------------------------


def test_kaynak_adi_sozlesmeye_uygun() -> None:
    kaynak_adi_dogrula(bs.KAYNAK_ADI, kayitli_olmali=True)
    assert bs.KAYNAK_ADI in KAYNAK_KAYITLARI
    assert bs.KAYNAK_ADI.isascii()
    assert "  " not in bs.KAYNAK_ADI


def test_kaynak_adi_baska_kayitla_cakismiyor() -> None:
    digerleri = [a for a in KAYNAK_KAYITLARI if a != bs.KAYNAK_ADI]
    assert cakisan_kaynak(bs.KAYNAK_ADI, digerleri) is None


def test_eski_yazim_ayni_anahtara_cozuluyor() -> None:
    """0030 bir AD DUZELTMESIDIR: iki yazim ayni kitabi gosterir."""
    eski = "Bilgi Sarmal  Tyt T" + chr(0x00FC) + "rkce Soru Bankas" + chr(0x0131)
    assert normalize_anahtar(eski) == normalize_anahtar(bs.KAYNAK_ADI)


def test_ithal_araci_kaydi_script_yoluyla_ayni() -> None:
    assert KAYNAK_KAYITLARI[bs.KAYNAK_ADI]["ithal_araci"] == bs.ITHAL_ARACI


# --- 5. DURUSTLUK -----------------------------------------------------


def test_okuyucu_simgesi_ortmesi_sayisi(veri) -> None:
    """Olculen deger capa olarak yazilir; sessizce degistirilemez."""
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
    k = bs.kayit_uret(ortmeli)
    pm = k["pipeline_metadata"]
    assert pm["okuyucu_simgesi_ortmesi"] is True
    assert pm["ortulen_bolge"] >= 1
    assert "okuyucu_simgesi_ortmesi" in pm["bayraklar"]


def test_cozum_uydurulmuyor(veri) -> None:
    """Kitabin soru sayfalarinda cozum yok; explanation NULL kalir."""
    for r in veri[:50]:
        assert bs.kayit_uret(r)["explanation"] is None


def test_cevap_kaynagi_kitabin_anahtari(veri) -> None:
    pm = bs.kayit_uret(veri[0])["pipeline_metadata"]
    assert pm["cevap_kaynagi"] == "kitap_sonu_cevap_anahtari"
    assert pm["anahtar_cift_okuma"] is True
    assert pm["cozum_dogrulamasi"] == "yapilmadi_urun_karari"


def test_ithal_pasif_sozlesmesi() -> None:
    assert "FALSE, FALSE" in bs._QB
    assert "'PENDING'" in bs._QB
    assert "TRUE, 'PENDING'" in bs._QB  # is_ai_generated TRUE


def test_metin_tavani_kayitli(veri) -> None:
    pm = bs.kayit_uret(veri[0])["pipeline_metadata"]
    assert pm["metin_tavani"].startswith("kaynak_1920x1080")


def test_harf_dagilimi_anahtarla_ayni(veri) -> None:
    dag = Counter(r["correct_answer"] for r in veri)
    assert sum(dag.values()) == BEKLENEN_SORU
    assert set(dag) == set("ABCDE")
    # Hicbir harf %15'in altinda ya da %35'in ustunde degil -- tek bir
    # harfe cokmus bir okuma buradan belli olur.
    for h, n in dag.items():
        assert 0.15 <= n / BEKLENEN_SORU <= 0.35, (h, n)


# --- 6. MIGRATION ZINCIRI ---------------------------------------------


def _goc(ad: str):
    yol = KOK / "alembic" / "versions" / ad
    spec = importlib.util.spec_from_file_location(f"_g_{ad}", yol)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, yol


def test_0029_zinciri_ve_ascii() -> None:
    mod, yol = _goc("0029_bilgi_sarmal_konu_agaci.py")
    assert mod.revision == "0029_bilgi_sarmal_agac"
    assert mod.down_revision == "0028_dilbilgisi_cevap"
    assert len(mod.revision) <= 32
    assert not [b for b in yol.read_bytes() if b > 127]
    assert len(mod.BOLUMLER) == 9
    assert len(mod.KONULAR) == 32


def test_0030_zinciri_ve_ascii() -> None:
    mod, yol = _goc("0030_bilgi_sarmal_kaynak_adi.py")
    assert mod.revision == "0030_bs_kaynak_adi"
    assert mod.down_revision == "0029_bilgi_sarmal_agac"
    assert len(mod.revision) <= 32
    assert not [b for b in yol.read_bytes() if b > 127]
    assert mod.YENI == bs.KAYNAK_ADI


def test_0030_yalniz_source_book_kolonuna_dokunuyor() -> None:
    _, yol = _goc("0030_bilgi_sarmal_kaynak_adi.py")
    kod = yol.read_text(encoding="utf-8").split('"""', 2)[2]
    guncelleme = re.findall(r"UPDATE (\w+) SET (\w+)", kod)
    assert set(guncelleme) == {("question_metadata", "source_book")}, guncelleme


def test_agac_kodlari_migrationla_ayni(agac) -> None:
    mod, _ = _goc("0029_bilgi_sarmal_konu_agaci.py")
    dosya = {a["kod"] for a in agac}
    goc_kod = {k for _, k, _ in mod.BOLUMLER} | {k for _, _, k, _ in mod.KONULAR}
    assert dosya == goc_kod
