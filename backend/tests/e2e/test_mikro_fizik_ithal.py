"""Mikro Orijinal TYT Fizik 2025 ithalinin koruma testleri.

Canli DB istemez; veri setini, konu agacini, ithal script'ini ve
migration'i dosyadan okur -- CI'da da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU   -- 5 sik, dolu cevap, benzersiz hash/id, NFC.
2. SERIT KAPILARI        -- test ici numara surekliligi, serit sayisi,
                            seridin testin son sayfasinda olmasi.
3. KONU AGACI            -- her kodun agacta olmasi, onek kurali,
                            OSYM/KARMA testlerin BOLUM dugumune baglanmasi.
4. SOZLESME              -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK             -- ortme isaretleniyor, cozum uydurulmuyor,
                            ithal PASIF, mukerrer aday silinmiyor.
6. GORSEL KIRPIMI        -- kutu/gorsel yolu tutarliligi, kart siniri.
7. MIGRATION ZINCIRI     -- 0032 kimligi, ASCII, agacla birebir.
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

from scripts.kitap import mikro_fizik_ithal as mf  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
VERI_YOLU = CIKTI / "mikro_fizik_tyt_sorular.json"
AGAC_YOLU = CIKTI / "mikro_fizik_tyt_konu_agaci.json"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_SORU = 1326
BEKLENEN_TEST = 186
BEKLENEN_SERIT = 186
BEKLENEN_KUTU = 1247
BEKLENEN_KUTUSUZ = 79
BEKLENEN_SEKIL = 1022
BEKLENEN_GORSEL_BORCU = 66
BEKLENEN_ORTME = 16
BEKLENEN_DIZGI_KUSURU = 16
BEKLENEN_MUKERRER = 34
BEKLENEN_BOLUM_DUZEYI = 522
BEKLENEN_OSYM = 476
BEKLENEN_KARMA_BANT = 46
BEKLENEN_BOLUM = 11
BEKLENEN_KONU = 49
ILK_SAYFA, SON_SAYFA = 7, 398
# Sayfa karti 728x968; kirpim kutulari bu kartin icinde kalmali.
KART_GENISLIK, KART_YUKSEKLIK = 728, 968


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


def _test_kimligi(r: dict) -> tuple:
    """Test numarasi bolum icinde tekrar eder; kimlik (bolum, test_no)."""
    return (r["bolum_no"], r["test_no"])


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


def test_dosya_sayfasi_basili_sayfayla_ayni(veri) -> None:
    """Serit kirpimi basili numarayi da tasidi; ikisi ayrilirsa hizalama bozuk."""
    for r in veri:
        assert r["sayfa"] == r["basili_sayfa"], r["id"]


# --- 2. SERIT KAPILARI ------------------------------------------------


def test_test_sayisi(veri) -> None:
    assert len({_test_kimligi(r) for r in veri}) == BEKLENEN_TEST


def test_serit_sayfasi_sayisi(veri) -> None:
    """Her testin bir serit sayfasi var; serit sayisi test sayisiyla ayni."""
    assert len({r["serit_sayfa"] for r in veri}) == BEKLENEN_SERIT
    assert BEKLENEN_SERIT == BEKLENEN_TEST


def test_test_ici_numara_surekliligi(veri) -> None:
    """Her testte soru numaralari 1..N kesintisiz olmali."""
    gruplar: dict[tuple, list[dict]] = {}
    for r in veri:
        gruplar.setdefault(_test_kimligi(r), []).append(r)
    assert len(gruplar) == BEKLENEN_TEST
    for ti, rs in gruplar.items():
        nos = sorted(r["soru_no"] for r in rs)
        assert nos == list(range(1, len(nos) + 1)), (ti, nos[:20])


def test_okunan_soru_sayisi_seritle_ayni(veri) -> None:
    """Serit girdi sayisi ile okunan soru sayisi her testte birebir olmali."""
    gruplar: dict[tuple, list[dict]] = {}
    for r in veri:
        gruplar.setdefault(_test_kimligi(r), []).append(r)
    for ti, rs in gruplar.items():
        assert len(rs) == rs[0]["test_soru_sayisi"], ti


def test_serit_testin_son_sayfasinda(veri) -> None:
    """Bu kitapta her test 2 sayfa; serit IKINCI sayfanin altinda."""
    for r in veri:
        assert r["serit_sayfa"] == r["test_bas_sayfa"] + 1, r["id"]
        assert r["test_bas_sayfa"] <= r["sayfa"] <= r["serit_sayfa"], r["id"]


def test_tek_cevap_kaynagi(veri) -> None:
    """Bu kitabin tek basili anahtari sayfa alti seridi; baskasi yok."""
    assert {r["cevap_kaynagi"] for r in veri} == {"sayfa_alti_cevap_seridi"}
    assert all(r["anahtar_cift_okuma"] for r in veri)


def test_harf_dagilimi_tek_harfe_cokmemis(veri) -> None:
    dag = Counter(r["correct_answer"] for r in veri)
    assert sum(dag.values()) == BEKLENEN_SORU
    assert set(dag) == set("ABCDE")
    for h, n in dag.items():
        assert 0.10 <= n / BEKLENEN_SORU <= 0.35, (h, n)


# --- 3. KONU AGACI ----------------------------------------------------


def test_agac_onbir_bolum_ve_kirkdokuz_konu(agac) -> None:
    assert sum(1 for a in agac if a["seviye"] == 2) == BEKLENEN_BOLUM
    assert sum(1 for a in agac if a["seviye"] == 3) == BEKLENEN_KONU


def test_bolum_numaralari_kesintisiz(agac) -> None:
    siralar = sorted(a["sira"] for a in agac if a["seviye"] == 2)
    assert siralar == list(range(1, BEKLENEN_BOLUM + 1))


def test_bolumler_fiz_kokune_bagli(agac) -> None:
    for a in agac:
        if a["seviye"] == 2:
            assert a["ust"] == mf.FIZ_KOK_KODU, a["kod"]


def test_her_konu_kodu_agacta_var(veri, agac) -> None:
    kodlar = {a["kod"] for a in agac}
    eksik = {r["konu_kodu"] for r in veri} - kodlar
    assert not eksik, sorted(eksik)


def test_agacta_bos_dugum_yok(veri, agac) -> None:
    """Uydurulmus dugum kalmasin: her dugume en az bir soru bagli."""
    kullanilan = {r["konu_kodu"] for r in veri}
    bos = {a["kod"] for a in agac} - kullanilan
    assert not bos, sorted(bos)


def test_konu_kodu_oneki(veri) -> None:
    for r in veri:
        assert r["konu_kodu"].startswith(mf.KOD_ONEKI), r["id"]


def test_osym_tarzi_testler_bolum_dugumune_bagli(veri) -> None:
    """OSYM TARZI testler bir KONU degil, bolumun tamamini tarar."""
    osym = [r for r in veri if r["test_turu"] == "osym_tarzi"]
    assert len(osym) == BEKLENEN_OSYM
    for r in osym:
        assert r["konu_eslesme_duzeyi"] == "bolum", r["id"]


def test_karma_bantli_kazanim_testleri_bolum_duzeyinde(veri) -> None:
    """Baslik bandi "KARMA TEST" ise band bir konu adi vermiyor demektir."""
    karma = re.compile(r"karma test( - \d+)?$")
    kt = [
        r
        for r in veri
        if r["test_turu"] == "kazanim"
        and karma.fullmatch(_ascii_kucuk(r["test_basligi"]))
    ]
    assert len(kt) == BEKLENEN_KARMA_BANT
    for r in kt:
        assert r["konu_eslesme_duzeyi"] == "bolum", r["id"]
    # Baska hicbir kazanim satiri bolum duzeyine dusurulmemis olmali.
    kazanim_bolum = [
        r
        for r in veri
        if r["test_turu"] == "kazanim" and r["konu_eslesme_duzeyi"] == "bolum"
    ]
    assert len(kazanim_bolum) == BEKLENEN_KARMA_BANT


def test_eslesme_duzeyi_konu_adiyla_tutarli(veri) -> None:
    """Bolum duzeyi = band konu adi VERMEDI demek; ikisi birlikte hareket eder."""
    for r in veri:
        bolumde = r["konu_eslesme_duzeyi"] == "bolum"
        assert bolumde == (r["konu"] is None), r["id"]
        if bolumde:
            assert r["konu_kodu"] == r["bolum_kodu"], r["id"]
        else:
            assert r["konu_kodu"].startswith(r["bolum_kodu"] + "-"), r["id"]
            assert r["konu_kodu"] != r["bolum_kodu"], r["id"]


def test_bolum_duzeyi_capa(veri) -> None:
    n = sum(1 for r in veri if r["konu_eslesme_duzeyi"] == "bolum")
    assert n == BEKLENEN_BOLUM_DUZEYI


def test_bolum_duzeyi_bayraga_tasiniyor(veri) -> None:
    """MUTASYON KARSILIGI: _bayraklar bu isareti dusurerse test duser."""
    bolumlu = next(r for r in veri if r["konu_eslesme_duzeyi"] == "bolum")
    konulu = next(r for r in veri if r["konu_eslesme_duzeyi"] == "konu")
    sec_b = {h: bolumlu[h.lower()] for h in "ABCDE"}
    sec_k = {h: konulu[h.lower()] for h in "ABCDE"}
    assert "konu_bolum_duzeyinde" in mf._bayraklar(bolumlu, sec_b)
    assert "konu_bolum_duzeyinde" not in mf._bayraklar(konulu, sec_k)


def test_agac_adlari_ascii(agac) -> None:
    for a in agac:
        assert a["ad_ascii"].isascii(), a["kod"]


def test_agac_ust_dugumleri_tanimli(agac) -> None:
    kodlar = {a["kod"] for a in agac} | {mf.FIZ_KOK_KODU}
    for a in agac:
        assert a["ust"] in kodlar, a["kod"]


# --- 4. SOZLESME ------------------------------------------------------


def test_kaynak_adi_sozlesmeye_uygun() -> None:
    kaynak_adi_dogrula(mf.KAYNAK_ADI, kayitli_olmali=True)
    assert mf.KAYNAK_ADI in KAYNAK_KAYITLARI
    assert mf.KAYNAK_ADI.isascii()
    assert "  " not in mf.KAYNAK_ADI


def test_kaynak_adi_baska_kayitla_cakismiyor() -> None:
    digerleri = [a for a in KAYNAK_KAYITLARI if a != mf.KAYNAK_ADI]
    assert cakisan_kaynak(mf.KAYNAK_ADI, digerleri) is None


def test_ithal_araci_kaydi_script_yoluyla_ayni() -> None:
    assert KAYNAK_KAYITLARI[mf.KAYNAK_ADI]["ithal_araci"] == mf.ITHAL_ARACI


def test_onek_ayri_kitaplarla_cakismiyor() -> None:
    assert mf.ONEK == "MIKRO_FIZIK_TYT"
    digerleri = [k["onek"] for a, k in KAYNAK_KAYITLARI.items() if a != mf.KAYNAK_ADI]
    assert mf.ONEK not in digerleri


def test_sinav_turu_ve_ders_alani() -> None:
    assert mf.SINAV_TURU == "TYT"
    assert mf.DERS_ALANI == "FIZIK"
    assert "'TYT', 'FIZIK'" in mf._QM


# --- 5. DURUSTLUK -----------------------------------------------------


def test_ortme_sayisi_capa(veri) -> None:
    """Bu kitabin ikinci yakalamasi YOK; kurtarma kanali olmadan kalan ortme."""
    assert sum(1 for r in veri if r["okuyucu_simgesi_ortmesi"]) == BEKLENEN_ORTME


def test_ortme_bayraga_tasiniyor(veri) -> None:
    """MUTASYON KARSILIGI: _bayraklar bu isareti dusurerse test duser."""
    ortmeli = next(r for r in veri if r["okuyucu_simgesi_ortmesi"])
    temiz = next(r for r in veri if not r["okuyucu_simgesi_ortmesi"])
    sec_o = {h: ortmeli[h.lower()] for h in "ABCDE"}
    sec_t = {h: temiz[h.lower()] for h in "ABCDE"}
    assert "okuyucu_simgesi_ortmesi" in mf._bayraklar(ortmeli, sec_o)
    assert "okuyucu_simgesi_ortmesi" not in mf._bayraklar(temiz, sec_t)


def test_ortme_metadataya_yaziliyor(veri) -> None:
    ortmeli = next(r for r in veri if r["okuyucu_simgesi_ortmesi"])
    pm = mf.kayit_uret(ortmeli)["pipeline_metadata"]
    assert pm["okuyucu_simgesi_ortmesi"] is True
    assert pm["ortulen_metin"]
    assert "okuyucu_simgesi_ortmesi" in pm["bayraklar"]


def test_dizgi_kusuru_bayrakli(veri) -> None:
    kusurlu = [r for r in veri if r["kaynak_kusuru"]]
    assert len(kusurlu) == BEKLENEN_DIZGI_KUSURU
    pm = mf.kayit_uret(kusurlu[0])["pipeline_metadata"]
    assert "kaynak_dizgi_kusuru" in pm["bayraklar"]
    assert pm["kaynak_kusuru"]


def test_mukerrer_adaylari_silinmedi_isaretlendi(veri) -> None:
    """Baska yayinevinin kitabiyla ortusen sorular SILINMEZ, isaretlenir."""
    adaylar = [r for r in veri if r["mukerrer_aday"]]
    assert len(adaylar) == BEKLENEN_MUKERRER
    for r in adaylar:
        m = r["mukerrer_aday"]
        assert m["db_id"] and m["db_kitap"], r["id"]
        assert m["ortusme"] >= 0.75, r["id"]
    pm = mf.kayit_uret(adaylar[0])["pipeline_metadata"]
    assert "mukerrer_aday" in pm["bayraklar"]
    assert pm["mukerrer_aday"]["db_id"]


def test_mukerrer_adaylarinda_cevap_catismasi_yok(veri) -> None:
    """Yan bulgu capasi: 34 adayin 34'unde DB cevabi bizim seritle ayni."""
    adaylar = [r["mukerrer_aday"] for r in veri if r["mukerrer_aday"]]
    assert all(m["cevap_ayni"] for m in adaylar)
    assert all(m["db_cevap"] == m["bizim_cevap"] for m in adaylar)


def test_cozum_uydurulmuyor(veri) -> None:
    """Kitabin soru sayfalarinda cozum yok; explanation NULL kalir."""
    for r in veri[:50]:
        assert mf.kayit_uret(r)["explanation"] is None


def test_cevap_kaynagi_metadataya_tasiniyor(veri) -> None:
    pm = mf.kayit_uret(veri[0])["pipeline_metadata"]
    assert pm["cevap_kaynagi"] == "sayfa_alti_cevap_seridi"
    assert pm["anahtar_cift_okuma"] is True
    assert pm["anahtar_dogrulamasi"] == mf.ANAHTAR_DOGRULAMASI
    assert pm["cozum_dogrulamasi"] == "yapilmadi_urun_karari"
    # Kitap OSYM formatinda oldugunu iddia etmiyor; biz de etmiyoruz.
    assert mf.kayit_uret(veri[0])["osym_format_compliant"] is False


def test_cikmis_soru_iddiasi_yok(veri) -> None:
    """Bu kitap cikmis soru yili basmiyor; uydurulmamali."""
    for r in veri[:50]:
        assert mf.kayit_uret(r)["osym_year"] is None


def test_ithal_pasif_sozlesmesi() -> None:
    assert "FALSE, FALSE" in mf._QB
    assert "'PENDING'" in mf._QB
    assert "TRUE, 'PENDING'" in mf._QB  # is_ai_generated TRUE


def test_metin_tavani_kayitli(veri) -> None:
    pm = mf.kayit_uret(veri[0])["pipeline_metadata"]
    assert pm["metin_tavani"] == "kaynak_1920x1080_sayfa_karti_728x968"


def test_on_kontrol_taninmayan_cevap_kaynagini_reddeder(veri) -> None:
    """MUTASYON KARSILIGI: kaynak adi bozulursa ithal durmali."""
    k = mf.kayit_uret(veri[0])
    k["pipeline_metadata"]["cevap_kaynagi"] = "tahmin"
    hata = mf._on_kontrol([k])
    assert any("cevap kaynagi" in h for h in hata), hata


def test_on_kontrol_yanlis_konu_kodunu_reddeder(veri) -> None:
    k = mf.kayit_uret(veri[0])
    k["konu_kodu"] = "TUR-BS1"
    hata = mf._on_kontrol([k])
    assert any("konu kodu" in h for h in hata), hata


# --- 6. GORSEL KIRPIMI ------------------------------------------------


def test_kutu_sayilari_capa(veri) -> None:
    kutulu = sum(1 for r in veri if r["kirpim_kutusu"])
    assert kutulu == BEKLENEN_KUTU
    assert len(veri) - kutulu == BEKLENEN_KUTUSUZ


def test_kutular_sayfa_kartinin_icinde(veri) -> None:
    """Kutu kart koordinatinda; disari tasarsa kirpim PDF'te patlar."""
    for r in veri:
        k = r["kirpim_kutusu"]
        if not k:
            continue
        x0, y0, x1, y1 = k
        assert 0 <= x0 < x1 <= KART_GENISLIK, r["id"]
        assert 0 <= y0 < y1 <= KART_YUKSEKLIK, r["id"]


def test_gorsel_yolu_kutuyla_tutarli(veri) -> None:
    for r in veri[:200] + veri[-200:]:
        k = mf.kayit_uret(r)
        assert bool(k["question_image_url"]) == bool(r["kirpim_kutusu"]), r["id"]
        if k["question_image_url"]:
            assert k["question_image_url"].endswith(f"{k['id']}.png")
            assert mf.CROP_ONEK in k["question_image_url"]


def test_on_kontrol_kutu_gorsel_tutarsizligini_reddeder(veri) -> None:
    """MUTASYON KARSILIGI: kutu silinip yol kalirsa ithal durmali."""
    k = mf.kayit_uret(next(r for r in veri if r["kirpim_kutusu"]))
    k["pipeline_metadata"]["kirpim_kutusu"] = None
    hata = mf._on_kontrol([k])
    assert any("kutu ve gorsel" in h for h in hata), hata


def test_sekilli_ama_kutusuz_satirlar_bayrakli(veri) -> None:
    """Sekil var, kirpim yok: ogrenciye sekilsiz gosterilemez."""
    borclu = [r for r in veri if r["sekil_var"] and not r["kirpim_kutusu"]]
    assert len(borclu) == BEKLENEN_GORSEL_BORCU
    pm = mf.kayit_uret(borclu[0])["pipeline_metadata"]
    assert "gorsel_yok_sekilli" in pm["bayraklar"]
    assert pm["gorsel_kaynagi"] == "yok_kutu_uretilemedi"


def test_sekil_sayisi_capa(veri) -> None:
    assert sum(1 for r in veri if r["sekil_var"]) == BEKLENEN_SEKIL


def test_kutusuz_satirlarin_gerekcesi_yazili(veri) -> None:
    """Kutu uretilmediyse NEDEN uretilmedigi olculmus olmali."""
    for r in veri:
        if r["kirpim_kutusu"]:
            assert r["kirpim_gerekcesi"] is None, r["id"]
        else:
            assert r["kirpim_gerekcesi"], r["id"]
            assert "simge" in r["kirpim_gerekcesi"], r["id"]


def test_kirpim_koordinat_sistemi_kayitli(veri) -> None:
    pm = mf.kayit_uret(next(r for r in veri if r["kirpim_kutusu"]))["pipeline_metadata"]
    assert pm["kirpim_koordinat_sistemi"] == "sayfa_karti_596_46_1324_1014"
    assert pm["gorsel_kaynagi"] == "tam_soru_kirpimi"


# --- 7. MIGRATION ZINCIRI ---------------------------------------------


def _goc(ad: str):
    yol = KOK / "alembic" / "versions" / ad
    spec = importlib.util.spec_from_file_location(f"_g_{ad}", yol)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, yol


def test_0032_zinciri_ve_ascii() -> None:
    mod, yol = _goc("0032_mikro_fizik_konu_agaci.py")
    assert mod.revision == "0032_mikro_fizik_agac"
    assert mod.down_revision == "0031_bs_edebiyat_agac"
    assert len(mod.revision) <= 32
    assert not [b for b in yol.read_bytes() if b > 127]
    assert len(mod.BOLUMLER) == BEKLENEN_BOLUM
    assert len(mod.KONULAR) == BEKLENEN_KONU
    assert mod.FIZ_KOK_KODU == mf.FIZ_KOK_KODU
    assert mod.KOD_ONEKI == mf.KOD_ONEKI


def test_0032_agacla_birebir(agac) -> None:
    mod, _ = _goc("0032_mikro_fizik_konu_agaci.py")
    dosya = {a["kod"] for a in agac}
    goc_kod = {k for _, k, _ in mod.BOLUMLER} | {k for _, _, k, _ in mod.KONULAR}
    assert dosya == goc_kod
    adlar = {a["kod"]: a["ad_ascii"] for a in agac}
    for _sira, kod, ad in mod.BOLUMLER:
        assert adlar[kod] == ad, kod
    for _ust, _sira, kod, ad in mod.KONULAR:
        assert adlar[kod] == ad, kod


def test_0032_fizik_alanina_yaziyor() -> None:
    _, yol = _goc("0032_mikro_fizik_konu_agaci.py")
    kod = yol.read_text(encoding="utf-8").split('"""', 2)[2]
    assert "'FIZIK'" in kod
    assert "'EDEBIYAT'" not in kod
    assert "'TURKCE'" not in kod


def test_0032_gunlugu_ve_geri_alinabilirlik() -> None:
    mod, yol = _goc("0032_mikro_fizik_konu_agaci.py")
    assert mod.GUNLUK == "mikro_fizik_konu_gunlugu_0032"
    kod = yol.read_text(encoding="utf-8").split('"""', 2)[2]
    # downgrade soru tasiyan dugume dokunmamali
    assert "primary_topic_id = ANY" in kod
    assert "NOT EXISTS" in kod
