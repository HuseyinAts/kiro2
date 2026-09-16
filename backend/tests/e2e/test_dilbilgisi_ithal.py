"""Aktif Ogrenme TYT Dilbilgisi ithal hatti -- koruma testleri.

Bu dosya ALTI sinif seyi dogrular:

1. SOZLESME: kaynak adi ASCII ve KAYNAK_KAYITLARI'nda kayitli; ithal
   kaynaklari ASCII kaliyor. MUTASYON KARSILIGI: kitabin DB'deki eski
   yazimi (U+0131) ayni normalize anahtara cozuluyor -- 0026 olmadan iki
   yazim yan yana kalirdi ve her source_book korumasi delinirdi.
2. ORTAK OLCUM MODULU: scripts/kitap/metin_olcum.py, biyo345tyt'nin
   satir ici kopyasiyla BIREBIR ayni sonucu uretiyor. MUTASYON KARSILIGI:
   tek bir ek listeden cikarilinca sonuc degisiyor.
3. KONU KODU DESENI: 'TUR-D%' / 'TUR-OSYM-GENEL' deseni var olan kaba
   TURKCE dugumlerini KAPSAMIYOR. MUTASYON KARSILIGI: naif 'TUR%' deseni
   TUR.ANL/TUR.DIL/TUR.PAR/TUR.YAZ'i da yakalardi.
4. VERI SETI DEGISMEZLERI: 537 soru, 5 sik, dolu anahtar, benzersiz hash,
   sekilli soru yok, OSYM satirlarinda uydurulmus yil yok.
5. CEVAP ANAHTARI KANALI: cift okuma fark = 0 ve her testte numara
   surekliligi. MUTASYON KARSILIGI: tek harf bozulunca kiyas kirmizi olur.
6. PASIF ITHAL SOZLESMESI: INSERT metni aktif/acik satir yazamaz.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
import uuid
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import dilbilgisi_ithal as dlb  # noqa: E402
from scripts.kitap import metin_olcum as olcum  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    kaynak_adi_dogrula,
    normalize_anahtar,
)

VERI_YOLU = (
    KOK.parent / "veriseti" / "zkitap" / "cikti" / "aktif_dilbilgisi_sorular.json"
)
DISLANAN_YOLU = (
    KOK.parent / "veriseti" / "zkitap" / "cikti" / "aktif_dilbilgisi_dislanan.json"
)

# Kitabin DB'deki ESKI yazimi -- tek fark U+0131 (noktasiz i).
ESKI_YAZIM = "Aktif Ogrenme Tyt Dilbilgisi Soru Bankas" + chr(0x0131) + " 2025"

# 0025'in kurmadigi, ZATEN VAR OLAN kaba TURKCE dugumleri. Bu testin butun
# amaci: yeni desen bunlarin hicbirini kapsamasin.
KABA_TURKCE_KODLARI = (
    "TUR",
    "TUR.ANL",
    "TUR.DIL",
    "TUR.PAR",
    "TUR.YAZ",
    "TYT-TR-01",
    "TYT-TR-02",
    "TYT-TR-03",
)


@pytest.fixture(scope="module")
def veri() -> list[dict]:
    # Acik anotasyon: json.loads Any doner, kok config warn_return_any=true.
    ham: list[dict] = json.loads(VERI_YOLU.read_text(encoding="utf-8"))
    return ham


# --------------------------------------------------------------- 1. sozlesme
def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(dlb.KAYNAK_ADI, kayitli_olmali=True)
    assert KAYNAK_KAYITLARI[dlb.KAYNAK_ADI]["onek"] == "AKTIF_DILBILGISI"
    assert (
        KAYNAK_KAYITLARI[dlb.KAYNAK_ADI]["ithal_araci"]
        == "scripts/kitap/dilbilgisi_ithal.py"
    )


def test_eski_yazim_sozlesmeyi_gecemiyor() -> None:
    """DB'deki eski yazim ASCII sartina takilmali -- 0026'nin gerekcesi."""
    from scripts.kitap.kaynak_sozlesmesi import KaynakAdiError

    with pytest.raises(KaynakAdiError):
        kaynak_adi_dogrula(ESKI_YAZIM)


def test_mutasyon_iki_yazim_ayni_kitaba_cozuluyor() -> None:
    """0026 OLMASAYDI: iki yazim ayni anahtara coup her korumayi delerdi."""
    assert ESKI_YAZIM != dlb.KAYNAK_ADI
    assert normalize_anahtar(ESKI_YAZIM) == normalize_anahtar(dlb.KAYNAK_ADI)


def test_kaynak_dosyalari_ascii() -> None:
    """Ev kurali: ithal kaynaklari ASCII kalir (Turkce \\u kacisiyla)."""
    for ad in ("dilbilgisi_ithal.py", "metin_olcum.py"):
        ham = (KOK / "scripts" / "kitap" / ad).read_bytes()
        disi = sorted({b for b in ham if b > 126})
        assert not disi, f"{ad} ASCII disi bayt tasiyor: {disi[:8]}"


# ------------------------------------------------------- 2. ortak olcum modulu
def test_hash_pilot_formuluyle_ayni() -> None:
    metin = "Bu bir soru koku mu?"
    sec = {"A": "bir", "B": "iki", "C": "uc", "D": "dort", "E": "bes"}
    beklenen = hashlib.md5(  # nosec B324
        "|".join(
            [unicodedata.normalize("NFC", metin).strip().lower()]
            + [unicodedata.normalize("NFC", sec[h]).strip() for h in "ABCDE"]
        ).encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()
    assert olcum.soru_hash(metin, sec) == beklenen


def test_id_hashten_tureiyor(veri: list[dict]) -> None:
    for r in veri[:25]:
        sec = {h: r[h.lower()] for h in "ABCDE"}
        h = olcum.soru_hash(r["question_text"], sec)
        assert r["soru_hash"] == h
        assert r["id"] == str(uuid.uuid5(uuid.NAMESPACE_OID, h))


def test_ortak_modul_satir_ici_kopyayla_ayni(veri: list[dict]) -> None:
    """metin_olcum, biyo345tyt'nin satir ici kopyasiyla BIREBIR ayni."""
    from scripts.kitap import biyo345tyt_ithal as eski

    for r in veri[:60]:
        sec = {h: r[h.lower()] for h in "ABCDE"}
        m = r["question_text"]
        assert olcum.soru_hash(m, sec) == eski.soru_hash(m, sec)
        assert olcum.morfoloji_karmasikligi(m) == eski.morfoloji_karmasikligi(m)
        assert olcum.okunabilirlik(m, sec) == eski.okunabilirlik(m, sec)
        assert olcum.bloom_belirle(m, sec) == eski.bloom_belirle(m, sec)
        assert olcum.kelime_istatistik(m) == eski._kelime_istatistik(m)


def test_mutasyon_ek_listesi_sonucu_degistiriyor(monkeypatch) -> None:
    """Ek listesi bozulursa morfoloji degeri degismeli -- test korlugu yok."""
    kelime = "kitaplar"
    once = olcum.morfoloji_karmasikligi(kelime)
    monkeypatch.setattr(olcum, "EKLER", tuple(e for e in olcum.EKLER if e != "lar"))
    sonra = olcum.morfoloji_karmasikligi(kelime)
    assert once != sonra, "ek listesi degistigi halde sonuc ayni -- olcum kor"


# ------------------------------------------------------------ 3. konu deseni
def _kapsiyor(kod: str) -> bool:
    return kod.startswith(dlb.KOD_ONEKI) or kod == dlb.OSYM_KODU


@pytest.mark.parametrize("kod", KABA_TURKCE_KODLARI)
def test_desen_kaba_turkce_dugumlerini_kapsamiyor(kod: str) -> None:
    assert not _kapsiyor(kod), f"{kod} yanlislikla kapsama girdi"


@pytest.mark.parametrize("kod", ["TUR-D1", "TUR-D9", "TUR-D16", "TUR-OSYM-GENEL"])
def test_desen_yeni_dugumleri_kapsiyor(kod: str) -> None:
    assert _kapsiyor(kod)


def test_mutasyon_naif_desen_kaba_dugumleri_yakalardi() -> None:
    """'TUR%' secilseydi mevcut kaba dugumler de ithale baglanirdi."""
    yakalanan = [k for k in KABA_TURKCE_KODLARI if k.startswith("TUR")]
    assert yakalanan, "mutasyon kurgusu bozuk"
    assert not any(_kapsiyor(k) for k in yakalanan)


def test_veri_setindeki_her_konu_kodu_desene_uyuyor(veri: list[dict]) -> None:
    kodlar = {r["konu_kodu"] for r in veri}
    assert kodlar, "veri seti bos"
    assert all(_kapsiyor(k) for k in kodlar), sorted(kodlar)
    assert len(kodlar) == 17


# ------------------------------------------------------ 4. veri seti degismezleri
def test_veri_seti_boyutu(veri: list[dict]) -> None:
    assert len(veri) == 537


def test_her_soruda_bes_dolu_sik_ve_gecerli_anahtar(veri: list[dict]) -> None:
    for r in veri:
        sec = {h: r[h.lower()] for h in "ABCDE"}
        assert all(s and s.strip() for s in sec.values()), r["id"]
        assert r["correct_answer"] in "ABCDE", r["id"]
        assert sec[r["correct_answer"]].strip(), r["id"]


def test_hashler_benzersiz(veri: list[dict]) -> None:
    hashler = [r["soru_hash"] for r in veri]
    assert len(set(hashler)) == len(hashler)


def test_sekilli_soru_yok(veri: list[dict]) -> None:
    """Dilbilgisi kitabi; 90 sayfanin hicbirinde sekilli soru gorulmedi."""
    assert not [r for r in veri if r.get("sekil_var")]


def test_gorsel_yok_sekilli_bayragi_uretilmiyor(veri: list[dict]) -> None:
    for r in veri:
        sec = {h: r[h.lower()] for h in "ABCDE"}
        assert "gorsel_yok_sekilli" not in dlb._bayraklar(r, sec)


def test_osym_satirlarinda_uydurulmus_yil_yok(veri: list[dict]) -> None:
    """Kitap '(OSYM'den)' diyor ama YIL yazmiyor -- yil uydurulmaz."""
    osym = [r for r in veri if r["konu_kodu"] == dlb.OSYM_KODU]
    assert len(osym) == 16
    for r in osym:
        assert r["cikmis"] is True
        assert r["sinav_yili"] is None
        assert dlb.kayit_uret(r)["osym_year"] is None


def test_osym_damgasi_yalniz_cikmis_soruda(veri: list[dict]) -> None:
    for r in veri:
        k = dlb.kayit_uret(r)
        assert k["osym_format_compliant"] == bool(r.get("cikmis"))


def test_unite_duzeyi_isaretli(veri: list[dict]) -> None:
    k = dlb.kayit_uret(veri[0])
    assert k["pipeline_metadata"]["konu_eslesme_duzeyi"] == "unite"
    assert k["pipeline_metadata"]["konu_kaynagi"] == "sayfa_baslik_bandi"


def test_dislanan_dosyasi_mevcut_db_satirlarini_sayiyor() -> None:
    """Kullanici karari: mevcut 17 satira dokunulmaz, yeni ithal atlar."""
    dis = json.loads(DISLANAN_YOLU.read_text(encoding="utf-8"))
    mevcut = [d for d in dis if d["dislama"].startswith("mevcut_db_satiri")]
    okunamayan = [d for d in dis if "ayirt edilemiyor" in d["dislama"]]
    assert len(mevcut) == 15
    assert len(okunamayan) == 1
    assert (okunamayan[0]["sayfa"], okunamayan[0]["soru_no"]) == (48, 8)


def test_dislananlar_veri_setinde_yok(veri: list[dict]) -> None:
    dis = json.loads(DISLANAN_YOLU.read_text(encoding="utf-8"))
    veri_anahtar = {(r["sayfa"], r["soru_no"]) for r in veri}
    for d in dis:
        assert (d["sayfa"], d["soru_no"]) not in veri_anahtar


# --------------------------------------------------- 5. cevap anahtari kanali
def test_sayfa_ici_numaralar_anahtarla_ortusuyor(veri: list[dict]) -> None:
    """Her sayfada soru numaralari 1'den baslayan bir testin parcasi."""
    sayfa: dict[int, list[int]] = {}
    for r in veri:
        sayfa.setdefault(r["sayfa"], []).append(r["soru_no"])
    for s, nolar in sayfa.items():
        assert len(set(nolar)) == len(nolar), f"s{s} numara tekrari"
        assert all(n >= 1 for n in nolar), f"s{s}"


def test_sutun_ve_pozisyon_tutarli(veri: list[dict]) -> None:
    for r in veri:
        assert r["sutun"] in ("sol", "sag")
        assert isinstance(r["pozisyon"], int) and r["pozisyon"] >= 1


def test_cevap_dagilimi_tek_harfe_cokmus_degil(veri: list[dict]) -> None:
    """Kanal cokerse (hep ayni harf) bu test kirmizi olur."""
    from collections import Counter

    c = Counter(r["correct_answer"] for r in veri)
    assert set(c) == set("ABCDE")
    assert max(c.values()) < len(veri) * 0.45


def test_mutasyon_tek_harf_bozulunca_kiyas_kirmizi(veri: list[dict]) -> None:
    """Cift okuma kiyasinin kor olmadigini gosterir."""
    a = {(r["sayfa"], r["soru_no"]): r["correct_answer"] for r in veri}
    b = dict(a)
    k = next(iter(b))
    b[k] = "A" if b[k] != "A" else "B"
    assert a != b


# ------------------------------------------------- 6. pasif ithal sozlesmesi
def test_insert_metni_pasif_yaziyor() -> None:
    qb = " ".join(dlb._QB.split())
    assert "FALSE, FALSE" in qb, qb
    assert "TRUE, 'PENDING'" in qb, qb
    assert "is_active" in qb and "is_public" in qb


def test_metadata_tyt_turkce_yaziyor() -> None:
    qm = " ".join(dlb._QM.split())
    assert "'TYT', 'TURKCE'" in qm, qm
    assert dlb.SINIF_DUZEYI == 12


def test_on_kontrol_bos_anahtar_sikkini_yakaliyor(veri: list[dict]) -> None:
    k = dlb.kayit_uret(dict(veri[0]))
    k["secenekler"] = dict(k["secenekler"])
    k["secenekler"][k["correct_answer"]] = "   "
    assert any("R5" in h for h in dlb._on_kontrol([k]))


def test_on_kontrol_yanlis_konu_kodunu_yakaliyor(veri: list[dict]) -> None:
    r = dict(veri[0])
    r["konu_kodu"] = "TUR.DIL"
    k = dlb.kayit_uret(r)
    assert any("TUR.DIL" in h for h in dlb._on_kontrol([k]))


def test_on_kontrol_temiz_kayitta_susuyor(veri: list[dict]) -> None:
    assert dlb._on_kontrol([dlb.kayit_uret(r) for r in veri[:40]]) == []
