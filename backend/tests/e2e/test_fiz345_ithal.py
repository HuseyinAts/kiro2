"""345 2025 AYT Fizik ithalinin koruma testleri.

Canli DB istemez; veri setini, konu agacini, ithal script'ini ve
migration'i dosyadan okur -- CI'da da koser.

BOLUMLER
1. VERI SETI BUTUNLUGU   -- 5 sik, dolu cevap, benzersiz hash/id, NFC.
2. CEVAP SATIRI KAPILARI -- sayfa ici numara surekliligi, test yapisi,
                            cevap kaynagi tekligi.
3. KONU AGACI            -- her kodun agacta olmasi, onek kurali,
                            bolum/konu duzeyi tutarliligi.
4. SOZLESME              -- kaynak adi ASCII, kayitli, cakismasiz.
5. DURUSTLUK             -- ortme isaretleniyor, cozum uydurulmuyor,
                            ithal PASIF, mukerrer aday silinmiyor.
6. GORSEL KIRPIMI        -- kutu/gorsel yolu tutarliligi, kart siniri,
                            cevap satirinin USTUNDE kalma sarti.
7. MIGRATION ZINCIRI     -- 0033 kimligi, ASCII, agacla birebir.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import fiz345_ithal as fz  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    cakisan_kaynak,
    kaynak_adi_dogrula,
)

CIKTI = KOK.parent / "veriseti" / "zkitap" / "cikti"
VERI_YOLU = CIKTI / "345_ayt_fizik_sorular.json"
AGAC_YOLU = CIKTI / "345_ayt_fizik_konu_agaci.json"

# Olculen capalar; sessizce degistirilemez.
BEKLENEN_SORU = 1308
BEKLENEN_TEST = 190
BEKLENEN_SAYFA = 380
BEKLENEN_KUTU = 1295
BEKLENEN_KUTUSUZ = 13
BEKLENEN_SEKIL = 1007
BEKLENEN_GORSEL_BORCU = 11
BEKLENEN_SIK_GORSEL = 19
BEKLENEN_ORTME = 16
BEKLENEN_DIZGI_KUSURU = 25
BEKLENEN_MUKERRER = 11
BEKLENEN_BOLUM_DUZEYI = 1037
BEKLENEN_BOLUM = 20
BEKLENEN_KONU = 40
ILK_SAYFA, SON_SAYFA = 6, 391
# Sayfa karti 748x980 (BU kitap icin olculdu).
KART_GENISLIK, KART_YUKSEKLIK = 748, 980
# Cevap satirinin ust siniri kart koordinatinda; kirpim bunu GECEMEZ.
CEVAP_SATIRI_UST = 892


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
    assert len({r["sayfa"] for r in veri}) == BEKLENEN_SAYFA


def test_dosya_sayfasi_basili_sayfayla_ayni(veri) -> None:
    for r in veri:
        assert r["sayfa"] == r["basili_sayfa"], r["id"]


# --- 2. CEVAP SATIRI KAPILARI -----------------------------------------


def test_tek_cevap_kaynagi(veri) -> None:
    """Bu kitabin tek basili anahtari sayfa alti satiri; baskasi yok."""
    assert {r["cevap_kaynagi"] for r in veri} == {"sayfa_alti_cevap_satiri"}
    assert all(r["anahtar_cift_okuma"] for r in veri)


def test_sayfa_ici_numara_surekliligi(veri) -> None:
    """Sol sutun bitince sag sutun kaldigi yerden devam etmeli."""
    sayfa = defaultdict(list)
    for r in veri:
        sayfa[r["sayfa"]].append(r)
    for s, rs in sayfa.items():
        sirali = sorted(
            rs, key=lambda r: (0 if r["sutun"] == "sol" else 1, r["soru_no"])
        )
        nos = [r["soru_no"] for r in sirali]
        assert nos == list(range(nos[0], nos[0] + len(nos))), (s, nos)


def test_test_sayisi_ve_yapisi(veri) -> None:
    """Her test 1'den baslar, iki sayfadir ve numaralari kesintisizdir."""
    testler = defaultdict(list)
    for r in veri:
        testler[r["test_no"]].append(r)
    assert len(testler) == BEKLENEN_TEST
    for tno, rs in testler.items():
        nos = sorted(r["soru_no"] for r in rs)
        assert nos == list(range(1, len(nos) + 1)), (tno, nos)
        sayfalar = {r["sayfa"] for r in rs}
        bas = {r["test_bas_sayfa"] for r in rs}
        son = {r["test_son_sayfa"] for r in rs}
        assert len(bas) == len(son) == 1, tno
        # assert icinde pop() yan etkidir (CodeQL py/side-effect-in-assert);
        # degerler once cikarilir.
        ilk_sayfa = next(iter(bas))
        son_sayfa = next(iter(son))
        assert min(sayfalar) >= ilk_sayfa, (tno, min(sayfalar), ilk_sayfa)
        assert max(sayfalar) <= son_sayfa, (tno, max(sayfalar), son_sayfa)


def test_her_test_tek_bolumde(veri) -> None:
    """Icindekilerden gelen bolum sinirlari test sinirlariyla catismamali."""
    testler = defaultdict(set)
    for r in veri:
        testler[r["test_no"]].add(r["bolum_no"])
    tasan = [t for t, b in testler.items() if len(b) != 1]
    assert not tasan, tasan


def test_harf_dagilimi_tek_harfe_cokmemis(veri) -> None:
    dag = Counter(r["correct_answer"] for r in veri)
    assert sum(dag.values()) == BEKLENEN_SORU
    assert set(dag) == set("ABCDE")
    for h, n in dag.items():
        assert 0.10 <= n / BEKLENEN_SORU <= 0.35, (h, n)


def test_test_turu_dort_degerden_biri(veri) -> None:
    assert {r["test_turu"] for r in veri} == {
        "kazanim",
        "osym_tadinda",
        "gunluk_hayat",
        "orijinal",
    }


# --- 3. KONU AGACI ----------------------------------------------------


def test_agac_yirmi_bolum_ve_kirk_konu(agac) -> None:
    assert sum(1 for a in agac if a["seviye"] == 2) == BEKLENEN_BOLUM
    assert sum(1 for a in agac if a["seviye"] == 3) == BEKLENEN_KONU


def test_bolum_numaralari_kesintisiz(agac) -> None:
    siralar = sorted(a["sira"] for a in agac if a["seviye"] == 2)
    assert siralar == list(range(1, BEKLENEN_BOLUM + 1))


def test_bolumler_fiz_kokune_bagli(agac) -> None:
    for a in agac:
        if a["seviye"] == 2:
            assert a["ust"] == fz.FIZ_KOK_KODU, a["kod"]


def test_her_konu_kodu_agacta_var(veri, agac) -> None:
    kodlar = {a["kod"] for a in agac}
    eksik = {r["konu_kodu"] for r in veri} - kodlar
    assert not eksik, sorted(eksik)


def test_agacta_bos_dugum_yok(veri, agac) -> None:
    kullanilan = {r["konu_kodu"] for r in veri}
    bos = {a["kod"] for a in agac} - kullanilan
    assert not bos, sorted(bos)


def test_konu_kodu_oneki(veri) -> None:
    for r in veri:
        assert r["konu_kodu"].startswith(fz.KOD_ONEKI), r["id"]


def test_eslesme_duzeyi_konu_adiyla_tutarli(veri) -> None:
    """Bolum duzeyi = bant konu adi VERMEDI demek; ikisi birlikte hareket eder."""
    for r in veri:
        bolumde = r["konu_eslesme_duzeyi"] == "bolum"
        assert bolumde == (r["konu"] is None), r["id"]
        if bolumde:
            assert r["konu_kodu"] == r["bolum_kodu"], r["id"]
        else:
            assert r["konu_kodu"].startswith(r["bolum_kodu"] + "-"), r["id"]


def test_bolum_duzeyi_capa(veri) -> None:
    n = sum(1 for r in veri if r["konu_eslesme_duzeyi"] == "bolum")
    assert n == BEKLENEN_BOLUM_DUZEYI


def test_bolum_duzeyi_bayraga_tasiniyor(veri) -> None:
    """MUTASYON KARSILIGI: _bayraklar bu isareti dusurerse test duser."""
    bolumlu = next(r for r in veri if r["konu_eslesme_duzeyi"] == "bolum")
    konulu = next(r for r in veri if r["konu_eslesme_duzeyi"] == "konu")
    sec_b = {h: bolumlu[h.lower()] for h in "ABCDE"}
    sec_k = {h: konulu[h.lower()] for h in "ABCDE"}
    assert "konu_bolum_duzeyinde" in fz._bayraklar(bolumlu, sec_b)
    assert "konu_bolum_duzeyinde" not in fz._bayraklar(konulu, sec_k)


def test_agac_adlari_ascii(agac) -> None:
    for a in agac:
        assert a["ad_ascii"].isascii(), a["kod"]


def test_agac_ust_dugumleri_tanimli(agac) -> None:
    kodlar = {a["kod"] for a in agac} | {fz.FIZ_KOK_KODU}
    for a in agac:
        assert a["ust"] in kodlar, a["kod"]


# --- 4. SOZLESME ------------------------------------------------------


def test_kaynak_adi_sozlesmeye_uygun() -> None:
    kaynak_adi_dogrula(fz.KAYNAK_ADI, kayitli_olmali=True)
    assert fz.KAYNAK_ADI in KAYNAK_KAYITLARI
    assert fz.KAYNAK_ADI.isascii()
    assert "  " not in fz.KAYNAK_ADI


def test_kaynak_adi_baska_kayitla_cakismiyor() -> None:
    digerleri = [a for a in KAYNAK_KAYITLARI if a != fz.KAYNAK_ADI]
    assert cakisan_kaynak(fz.KAYNAK_ADI, digerleri) is None


def test_ithal_araci_kaydi_script_yoluyla_ayni() -> None:
    assert KAYNAK_KAYITLARI[fz.KAYNAK_ADI]["ithal_araci"] == fz.ITHAL_ARACI


def test_onek_baska_kitapla_cakismiyor() -> None:
    assert fz.ONEK == "FIZ345"
    digerleri = [k["onek"] for a, k in KAYNAK_KAYITLARI.items() if a != fz.KAYNAK_ADI]
    assert fz.ONEK not in digerleri


def test_sinav_turu_ve_ders_alani() -> None:
    assert fz.SINAV_TURU == "AYT"
    assert fz.DERS_ALANI == "FIZIK"
    assert "'AYT', 'FIZIK'" in fz._QM


def test_kardes_fizik_kitabindan_ayri() -> None:
    """Mikro TYT Fizik ile bu kitap AYNI DEGIL; onek ve agac oneki ayri."""
    assert fz.KOD_ONEKI == "FIZ-345"
    assert KAYNAK_KAYITLARI["Mikro Orijinal TYT Fizik Soru Bankasi 2025"]["onek"] != (
        fz.ONEK
    )


# --- 5. DURUSTLUK -----------------------------------------------------


def test_ortme_sayisi_capa(veri) -> None:
    assert sum(1 for r in veri if r["okuyucu_simgesi_ortmesi"]) == BEKLENEN_ORTME


def test_ortme_bayraga_tasiniyor(veri) -> None:
    """MUTASYON KARSILIGI: _bayraklar bu isareti dusurerse test duser."""
    ortmeli = next(r for r in veri if r["okuyucu_simgesi_ortmesi"])
    temiz = next(r for r in veri if not r["okuyucu_simgesi_ortmesi"])
    sec_o = {h: ortmeli[h.lower()] for h in "ABCDE"}
    sec_t = {h: temiz[h.lower()] for h in "ABCDE"}
    assert "okuyucu_simgesi_ortmesi" in fz._bayraklar(ortmeli, sec_o)
    assert "okuyucu_simgesi_ortmesi" not in fz._bayraklar(temiz, sec_t)


def test_ortme_metadataya_yaziliyor(veri) -> None:
    ortmeli = next(r for r in veri if r["okuyucu_simgesi_ortmesi"])
    pm = fz.kayit_uret(ortmeli)["pipeline_metadata"]
    assert pm["okuyucu_simgesi_ortmesi"] is True
    assert "okuyucu_simgesi_ortmesi" in pm["bayraklar"]


def test_dizgi_kusuru_bayrakli(veri) -> None:
    kusurlu = [r for r in veri if r["kaynak_kusuru"]]
    assert len(kusurlu) == BEKLENEN_DIZGI_KUSURU
    pm = fz.kayit_uret(kusurlu[0])["pipeline_metadata"]
    assert "kaynak_dizgi_kusuru" in pm["bayraklar"]
    assert pm["kaynak_kusuru"]


def test_mukerrer_adaylari_silinmedi_isaretlendi(veri) -> None:
    adaylar = [r for r in veri if r["mukerrer_aday"]]
    assert len(adaylar) == BEKLENEN_MUKERRER
    for r in adaylar:
        m = r["mukerrer_aday"]
        assert m["db_id"] and m["db_kitap"], r["id"]
        assert m["ortusme"] >= 0.75, r["id"]
    pm = fz.kayit_uret(adaylar[0])["pipeline_metadata"]
    assert "mukerrer_aday" in pm["bayraklar"]
    assert pm["mukerrer_aday"]["db_id"]


def test_mukerrer_cevap_catismasi_kayitli(veri) -> None:
    """11 adayin 10'unda cevap ayni; catisan tek satir gizlenmiyor."""
    adaylar = [r["mukerrer_aday"] for r in veri if r["mukerrer_aday"]]
    ayni = sum(1 for m in adaylar if m["cevap_ayni"])
    assert ayni == len(adaylar) - 1
    catisan = [m for m in adaylar if not m["cevap_ayni"]]
    assert len(catisan) == 1
    assert catisan[0]["db_cevap"] != catisan[0]["bizim_cevap"]


def test_gorsel_sikli_sorular_isaretli(veri) -> None:
    """Siklari grafik olan sorular UYDURULMADI, isaretlendi."""
    gorsel = [r for r in veri if r["sikler_gorsel"]]
    assert len(gorsel) == BEKLENEN_SIK_GORSEL
    for r in gorsel:
        assert all((r[h] or "") == "(gorsel sik)" for h in "abcde"), r["id"]
    pm = fz.kayit_uret(gorsel[0])["pipeline_metadata"]
    assert "sikler_gorsel" in pm["bayraklar"]


def test_gosterilemez_satir_isaretli(veri) -> None:
    """Siklari gorsel AMA kirpimi da yok olan satir gorunur isaretlenir."""
    yok = [r for r in veri if r["sikler_gorsel"] and not r["kirpim_kutusu"]]
    assert len(yok) == 1
    pm = fz.kayit_uret(yok[0])["pipeline_metadata"]
    assert "gosterilemez_gorsel_sik_kirpimsiz" in pm["bayraklar"]


def test_cozum_uydurulmuyor(veri) -> None:
    for r in veri[:50]:
        assert fz.kayit_uret(r)["explanation"] is None


def test_cikmis_soru_yili_uydurulmuyor(veri) -> None:
    """Kitap yil basiyor ama yil alani sistematik cikarilmadi; NULL kalir."""
    for r in veri[:50]:
        assert fz.kayit_uret(r)["osym_year"] is None
        assert fz.kayit_uret(r)["osym_format_compliant"] is False


def test_cevap_kaynagi_metadataya_tasiniyor(veri) -> None:
    pm = fz.kayit_uret(veri[0])["pipeline_metadata"]
    assert pm["cevap_kaynagi"] == "sayfa_alti_cevap_satiri"
    assert pm["anahtar_cift_okuma"] is True
    assert pm["anahtar_dogrulamasi"] == fz.ANAHTAR_DOGRULAMASI
    assert pm["cozum_dogrulamasi"] == "yapilmadi_urun_karari"


def test_ithal_pasif_sozlesmesi() -> None:
    assert "FALSE, FALSE" in fz._QB
    assert "'PENDING'" in fz._QB
    assert "TRUE, 'PENDING'" in fz._QB  # is_ai_generated TRUE


def test_metin_tavani_kayitli(veri) -> None:
    pm = fz.kayit_uret(veri[0])["pipeline_metadata"]
    assert pm["metin_tavani"] == "kaynak_1920x1080_sayfa_karti_748x980"


def test_on_kontrol_taninmayan_cevap_kaynagini_reddeder(veri) -> None:
    """MUTASYON KARSILIGI: kaynak adi bozulursa ithal durmali."""
    k = fz.kayit_uret(veri[0])
    k["pipeline_metadata"]["cevap_kaynagi"] = "tahmin"
    hata = fz._on_kontrol([k])
    assert any("cevap kaynagi" in h for h in hata), hata


def test_on_kontrol_yanlis_konu_kodunu_reddeder(veri) -> None:
    k = fz.kayit_uret(veri[0])
    k["konu_kodu"] = "FIZ-MO1"
    hata = fz._on_kontrol([k])
    assert any("konu kodu" in h for h in hata), hata


# --- 6. GORSEL KIRPIMI ------------------------------------------------


def test_kutu_sayilari_capa(veri) -> None:
    kutulu = sum(1 for r in veri if r["kirpim_kutusu"])
    assert kutulu == BEKLENEN_KUTU
    assert len(veri) - kutulu == BEKLENEN_KUTUSUZ


def test_kutular_sayfa_kartinin_icinde(veri) -> None:
    for r in veri:
        k = r["kirpim_kutusu"]
        if not k:
            continue
        x0, y0, x1, y1 = k
        assert 0 <= x0 < x1 <= KART_GENISLIK, r["id"]
        assert 0 <= y0 < y1 <= KART_YUKSEKLIK, r["id"]


def test_kirpim_cevap_satirini_icermiyor(veri) -> None:
    """CEVAP SIZINTISI KAPISI: kirpimin alti cevap satirinin ustunde kalmali."""
    for r in veri:
        k = r["kirpim_kutusu"]
        if not k:
            continue
        assert k[3] <= CEVAP_SATIRI_UST, (r["id"], k[3])


def test_gorsel_yolu_kutuyla_tutarli(veri) -> None:
    for r in veri[:200] + veri[-200:]:
        k = fz.kayit_uret(r)
        assert bool(k["question_image_url"]) == bool(r["kirpim_kutusu"]), r["id"]
        if k["question_image_url"]:
            assert k["question_image_url"].endswith(f"{k['id']}.png")
            assert fz.CROP_ONEK in k["question_image_url"]


def test_on_kontrol_kutu_gorsel_tutarsizligini_reddeder(veri) -> None:
    """MUTASYON KARSILIGI: kutu silinip yol kalirsa ithal durmali."""
    k = fz.kayit_uret(next(r for r in veri if r["kirpim_kutusu"]))
    k["pipeline_metadata"]["kirpim_kutusu"] = None
    hata = fz._on_kontrol([k])
    assert any("kutu ve gorsel" in h for h in hata), hata


def test_sekilli_ama_kutusuz_satirlar_bayrakli(veri) -> None:
    borclu = [r for r in veri if r["sekil_var"] and not r["kirpim_kutusu"]]
    assert len(borclu) == BEKLENEN_GORSEL_BORCU
    pm = fz.kayit_uret(borclu[0])["pipeline_metadata"]
    assert "gorsel_yok_sekilli" in pm["bayraklar"]
    assert pm["gorsel_kaynagi"] == "yok_kutu_uretilemedi"


def test_sekil_sayisi_capa(veri) -> None:
    assert sum(1 for r in veri if r["sekil_var"]) == BEKLENEN_SEKIL


def test_kutusuz_satirlarin_gerekcesi_yazili(veri) -> None:
    for r in veri:
        if r["kirpim_kutusu"]:
            assert r["kirpim_gerekcesi"] is None, r["id"]
        else:
            assert r["kirpim_gerekcesi"], r["id"]
            assert "simge" in r["kirpim_gerekcesi"], r["id"]


def test_kirpim_koordinat_sistemi_kayitli(veri) -> None:
    pm = fz.kayit_uret(next(r for r in veri if r["kirpim_kutusu"]))["pipeline_metadata"]
    assert pm["kirpim_koordinat_sistemi"] == "sayfa_karti_584_42_1332_1022"
    assert pm["gorsel_kaynagi"] == "tam_soru_kirpimi"


# --- 7. MIGRATION ZINCIRI ---------------------------------------------


def _goc(ad: str):
    yol = KOK / "alembic" / "versions" / ad
    spec = importlib.util.spec_from_file_location(f"_g_{ad}", yol)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, yol


def test_0033_zinciri_ve_ascii() -> None:
    mod, yol = _goc("0033_fiz345_konu_agaci.py")
    assert mod.revision == "0033_fiz345_agac"
    assert mod.down_revision == "0032_mikro_fizik_agac"
    assert len(mod.revision) <= 32
    assert not [b for b in yol.read_bytes() if b > 127]
    assert len(mod.BOLUMLER) == BEKLENEN_BOLUM
    assert len(mod.KONULAR) == BEKLENEN_KONU
    assert mod.FIZ_KOK_KODU == fz.FIZ_KOK_KODU
    assert mod.KOD_ONEKI == fz.KOD_ONEKI


def test_0033_agacla_birebir(agac) -> None:
    mod, _ = _goc("0033_fiz345_konu_agaci.py")
    dosya = {a["kod"] for a in agac}
    goc_kod = {k for _, k, _ in mod.BOLUMLER} | {k for _, _, k, _ in mod.KONULAR}
    assert dosya == goc_kod
    adlar = {a["kod"]: a["ad_ascii"] for a in agac}
    for _sira, kod, ad in mod.BOLUMLER:
        assert adlar[kod] == ad, kod
    for _ust, _sira, kod, ad in mod.KONULAR:
        assert adlar[kod] == ad, kod


def test_0033_fizik_alanina_yaziyor() -> None:
    _, yol = _goc("0033_fiz345_konu_agaci.py")
    kod = yol.read_text(encoding="utf-8").split('"""', 2)[2]
    assert "'FIZIK'" in kod
    assert "'EDEBIYAT'" not in kod
    assert "'TURKCE'" not in kod


def test_0033_gunlugu_ve_geri_alinabilirlik() -> None:
    mod, yol = _goc("0033_fiz345_konu_agaci.py")
    assert mod.GUNLUK == "fiz345_konu_gunlugu_0033"
    kod = yol.read_text(encoding="utf-8").split('"""', 2)[2]
    assert "primary_topic_id = ANY" in kod
    assert "NOT EXISTS" in kod
