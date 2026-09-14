#!/usr/bin/env python
"""345 TYT-AYT Geometri Soru Bankasi -- OCR ciktisini PASIF ithal eder.

NEDEN PASIF VE is_ai_generated=TRUE
-----------------------------------
0013/0015/0017/biyo345 ithalleriyle ayni gerekce: metin bir OCR/VLM
hattindan geldi. Kaynak zkitap goruntuleyici EKRAN GORUNTUSUDUR. Her satir
su sekilde yazilir:

    is_active = FALSE, is_public = FALSE,
    is_ai_generated = TRUE, review_status = 'PENDING'

Servis kapisi (`v_safe_for_beta`) `(is_ai_generated = false OR
review_status = 'APPROVED')` ister; iki alan da bu satirlari kapinin
DISINDA tutar. Ithal tek basina hicbir soruyu ogrenciye ulastirmaz;
aktiflestirme ayri karardir.

CEVAP KAYNAGI: YALNIZ KITABIN BASILI ANAHTARI
---------------------------------------------
Sorular tekrar cozulerek dogrulanmaz (urun karari). Uretim ve olcumler
veriseti/zkitap/cikti/GEO345_YONTEM.md'de: iki bagimsiz okuma + hakem turu
(sayfa duzeyinde 767/776, girdi duzeyinde 2735/2745), ardindan NUMARA
SUREKLILIGI denetimi 2743 girdinin 2742'sinde kusursuz. Tek kirilma
kitabin dizgi hatasi (c2 s285 sag). `explanation` bu yuzden NULL kalir.

KONU BAGLAMA: SAYFANIN KENDI BASLIK BANDINDAN
---------------------------------------------
0017 (Mikro Geometri) ile ayni ilke: agac kitabin ICINDEKILER sayfasindan
DEGIL, her sayfanin KENDI BASLIK BANDINDAN uretildi.

Olcum zinciri (detay GEO345_YONTEM.md F9):
  * Bant, y 90-200 / x 800-1340 penceresinde kirmizi maskeyle bulunur;
    baslik bandi murekkebi >=100 ve genisligi >=60 olan satir band(lar)idir.
  * Bandin sagindaki ZORLUK GOSTERGESININ dolu kirmizi ibresi ayni
    satirlarda durdugu icin maskeye giriyordu. Yatay bosluk histogrami
    (7743 bosluk) ayrimi net veriyor: metin ici en genis bosluk 14, sonraki
    deger 22. BOSLUK_ESIK=18 ile ilk (en soldaki) yeterince genis grup
    alinir; ibre grubu w<=17 oldugu icin elenir.
  * 626 sayfada bant bulundu; gri tonlu vektorler Pearson >= 0.80 ile
    baglanti-bileseni olarak kumelendi -> 74 kume. Her kumeden 3 uye
    montajlanip okundu; kume ici tutarsizlik YOK.
  * Okuma 17 farkli konu adi verdi ve bu 17 ad sayfa sirasinda tam 17 KOSU
    olusturdu: hicbir konu ikinci kez acilmiyor, hicbir konu baska bir
    blogun icinde gorunmuyor. Okuyucuya beklenen kosu sayisi SOYLENMEDI --
    bu yuzden denetimin serbestlik derecesi yok.
  * Bloklar arasindaki ara sayfalar ("ORIJINAL SORULAR", "TYT/AYT
    TARZINDA", "Klasiklesmis Sorular", "OSYM TADINDA") konu bandi
    tasimiyor; 37 sayfanin ust seridi tek tek okundu ve hepsinin bir
    ONCEKI bloga ait oldugu goruldu. ACILAR blogunun ilk sayfalari
    (c1/6-17) bandi SOLUK bastigi icin esigi gecmiyor; o 12 sayfa da tek
    tek okundu, 10'unda ACILAR bandi var. Gizli 18. konu yok.
  * Sonuc: 2743 sorunun 2743'u bir konu blogunun icinde.

AGACA BAGLAMA: 10 YAPRAK + 7 UNITE
----------------------------------
Mevcut GEO agaci 0020'den beri yayinevinden bagimsiz: 5 unite, 31 yaprak.
Kitabin 17 bandinin 10'u bir yapraga BIREBIR karsilik geliyor. Kalan 7'si
birden fazla yapragin BIRLESIMI ("DIKDORTGEN - KARE" = GEO-U2-DIKDORTGEN +
GEO-U2-KARE gibi); bunlar icin yeni yaprak UYDURULMADI -- var olan
yapraklarla ortusen sahte bir yaprak agacin anlamini bozardi. Bu 7 konu
UNITE dugumune baglanir ve `konu_eslesme_duzeyi='unite'` ile ISARETLENIR.
Bandin ham metni her soruda `pipeline_metadata.konu_bandi` olarak durur,
yani ileride daha ince bir tur bu satirlari --meta-guncelle ile
inceltebilir. Bu ithal HICBIR migration gerektirmez.

BILINEN SINIR: SINAV TURU OLCULMEDI
-----------------------------------
Kitap TYT ve AYT sorularini KARISIK basiyor; `exam_type` ise tek degerli
bir kolon (DB'de yalnizca 'TYT' ve 'AYT' var). Soru duzeyinde sinav turu
OLCULMEDI: "TYT TARZINDA"/"AYT TARZINDA" bantlari yalnizca birkac ara
sayfada var, kitabin govdesi ("KAZANIM ODAKLI SORULAR") hic isaret
tasimiyor. Kardes geometri kitabiyla (Mikro Orijinal) tutarli olsun diye
'AYT' yazilir ve durum
`pipeline_metadata.sinav_turu_kaynagi='olculmedi_kitap_TYT-AYT_karisik'`
ile isaretlenir. Satirlar zaten PASIF; duzeltme --meta-guncelle ile
geriye donuk yapilabilir.

GORSELLER
---------
question_image_url TAM SORU KIRPIMIDIR (metin + sekil birlikte); kirpim
kutusu pipeline_metadata.kirpim_kutusu'nda saklanir ve gorseller her
ortamda kaynaktan yeniden uretilebilir (scripts/kitap/geo345_kirp.py).
`gorsel_kaynagi='tam_soru_kirpimi'`.

BILINEN SINIR: OKUNAMAYAN PARCALAR
----------------------------------
11 soruda `[okunamadi]` isareti var (uydurma yerine durust isaretleme) ve
6 sorunun SIKLARI GORSEL. Bunlarin metin alanlari arama/hash icindir;
dogru gosterim kirpim gorselidir. Hepsi `bayraklar` ile isaretlenir.

BEDAVA CAPRAZ DOGRULAMA
-----------------------
2743 hash'in 35'i canli DB'de zaten var ve hepsi `Mikro Orijinal 2025 AYT
Geometri Soru Bankasi` etiketli -- iki kitap ayni resmi OSYM sorularini
basmis. `ayristir()` bu 35 satiri `yabanci` dondurur ve UZERINE YAZILMAZ.

Kurallar
--------
- id = uuid5(NAMESPACE_OID, soru_hash); soru_hash = pilot_500p formulu.
- Ayni id varsa satir ATLANIR (idempotent; tekrar kosum guvenli).
- primary_topic_id: yaprak ya da unite kodu; bulunamazsa GEO koku.
- question_image_url = /static/crops/GEO345/<id>.png

KULLANIM
--------
    python backend/scripts/kitap/geo345_ithal.py --dsn postgresql://... [--yaz]
    (--yaz verilmezse yalnizca plan basilir)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI, ayristir, yabanci_yaz
from services.turkish_readability_service import TurkishReadabilityService

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
VARSAYILAN_VERI = "veriseti/zkitap/cikti/geo345_sorular.json"
KAYNAK_ADI = "345 2025 TYT-AYT Geometri Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
GEO_KOK_KODU = "GEO"
SINAV_TURU = "AYT"
DERS_ALANI = "GEOMETRI"
SINIF_DUZEYI = 12
TELIF_NOTU = (
    "UcDortBes Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "OCR/VLM hatti: anahtar icin iki bagimsiz okuma + hakem turu + numara "
    "surekliligi denetimi (2743 girdide 1 kirilma, o da kitabin dizgi "
    "hatasi); konu bandi 74 kumede okundu ve 17 ad sayfa sirasinda 17 kosu "
    "verdi. Tek cevap kaynagi kitabin basili anahtaridir; soru cozulmedi. "
    "Detay: veriseti/zkitap/cikti/GEO345_YONTEM.md"
)

# Kitabin baslik bandi -> agac dugumu.
# 'yaprak': band bir L3 yapraga birebir karsilik geliyor.
# 'unite' : band birden cok yapragin birlesimi; sahte yaprak uydurulmadi.
KONU_HARITASI: dict[str, tuple[str, str]] = {
    "A\u00c7ILAR": ("GEO-U1", "unite"),
    "\u00d6ZEL \u00dc\u00c7GENLER": ("GEO-U1", "unite"),
    "\u00dc\u00c7GENDE YARDIMCI ELEMANLAR": ("GEO-U1", "unite"),
    "BENZERL\u0130K": ("GEO-U1-BENZERLIK", "yaprak"),
    "\u00dc\u00c7GENDE ALAN": ("GEO-U1-UCGENDE-ALAN", "yaprak"),
    "GENEL D\u00d6RTGENLER - YAMUK": ("GEO-U2", "unite"),
    "PARALELKENAR E\u015eKENAR D\u00d6RTGEN - DELTO\u0130D": ("GEO-U2", "unite"),
    "D\u0130KD\u00d6RTGEN - KARE": ("GEO-U2", "unite"),
    "\u00c7OKGENLER": ("GEO-U2-COKGENLER", "yaprak"),
    "\u00c7EMBERDE A\u00c7I": ("GEO-U3-CEMBERDE-ACI", "yaprak"),
    "\u00c7EMBERDE UZUNLUK": ("GEO-U3-CEMBERDE-UZUNLUK", "yaprak"),
    "DA\u0130REDE ALAN": ("GEO-U3-DAIREDE-ALAN", "yaprak"),
    "NOKTA ANAL\u0130T\u0130\u011e\u0130": ("GEO-U4-NOKTANIN-ANALITIGI", "yaprak"),
    "DO\u011eRU ANAL\u0130T\u0130\u011e\u0130": ("GEO-U4-DOGRUNUN-ANALITIGI", "yaprak"),
    "\u00c7EMBER ANAL\u0130T\u0130\u011e\u0130": (
        "GEO-U4-CEMBERIN-ANALITIGI",
        "yaprak",
    ),
    "D\u00d6N\u00dc\u015e\u00dcMLER": ("GEO-U4", "unite"),
    "KATI C\u0130S\u0130MLER": ("GEO-U5-KATI-CISIMLER", "yaprak"),
}

# Konu bloklari: (ilk sayfa, son sayfa, band metni). Sayfa numaralari DOSYA
# numarasidir (sayfa_XXXX.png), kitabin basili numarasi degil.
KONU_BLOKLARI: dict[str, list[tuple[int, int, str]]] = {
    "c1": [
        (6, 43, "A\u00c7ILAR"),
        (44, 93, "\u00d6ZEL \u00dc\u00c7GENLER"),
        (94, 141, "BENZERL\u0130K"),
        (142, 195, "\u00dc\u00c7GENDE YARDIMCI ELEMANLAR"),
        (196, 233, "\u00dc\u00c7GENDE ALAN"),
        (234, 287, "GENEL D\u00d6RTGENLER - YAMUK"),
        (288, 352, "PARALELKENAR E\u015eKENAR D\u00d6RTGEN - DELTO\u0130D"),
        (353, 414, "D\u0130KD\u00d6RTGEN - KARE"),
        (415, 440, "\u00c7OKGENLER"),
    ],
    "c2": [
        (5, 45, "\u00c7EMBERDE A\u00c7I"),
        (46, 97, "\u00c7EMBERDE UZUNLUK"),
        (98, 131, "DA\u0130REDE ALAN"),
        (132, 161, "NOKTA ANAL\u0130T\u0130\u011e\u0130"),
        (162, 213, "DO\u011eRU ANAL\u0130T\u0130\u011e\u0130"),
        (214, 247, "D\u00d6N\u00dc\u015e\u00dcMLER"),
        (248, 279, "\u00c7EMBER ANAL\u0130T\u0130\u011e\u0130"),
        (280, 336, "KATI C\u0130S\u0130MLER"),
    ],
}

# core/turkish_nlp_service._simple_root_suffix_split ile BIREBIR ayni liste.
# Turkce harfler \u kacisiyla yazilir (kaynak dosya ASCII kalsin diye);
# ASCII'ye duzlestirmek YANLIS olur -- gercek metinde "n\u0131n" gecer.
EKLER = (
    "lar",
    "ler",
    "dan",
    "den",
    "tan",
    "ten",
    "n\u0131n",
    "nin",
    "nun",
    "n\u00fcn",
    "nda",
    "nde",
    "n\u0131",
    "ni",
    "nu",
    "n\u00fc",
    "ya",
    "ye",
    "yla",
    "yle",
    "d\u0131r",
    "dir",
    "dur",
    "d\u00fcr",
    "t\u0131r",
    "tir",
    "tur",
    "t\u00fcr",
)
W_EK, W_TURETIM, W_BIRLESIK = 0.15, 0.20, 0.25

# DIKKAT -- KATASTROFIK GERI IZLEME ONARIMI (PR #266 ile ayni desen).
# Eski desen sondaki grubu ic ice nicelemisti ve eslesmeyen girdilerde
# ustel geri izleme uretiyordu. Yeni desen ic ice nicelemez.
SAYISAL_SIK = re.compile(
    "^[\\s\\d.,/+\\-x*^()\u2212\u221a\u00b7]+[a-zA-Z\u00b0%/\u00b2\u00b3\\s]{0,12}$"
)
NICELIK = re.compile(
    "ka\u00e7|b\u00fcy\u00fckl\u00fc\u011f\u00fc\\s+ne|de\u011feri\\s+ne|ka\u00e7t\u0131r",
    re.IGNORECASE,
)
OKUNAMADI = "[okunamadi]"


def _nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t or "").strip()


def soru_hash(metin: str, secenekler: dict[str, str]) -> str:
    """scripts/pipeline/pilot_500p.py::_hash_question ile birebir."""
    payload = "|".join(
        [_nfc(metin).lower()] + [_nfc(secenekler.get(h, "")) for h in "ABCDE"]
    )
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


def konu_bandi(cilt: str, sayfa: int) -> str | None:
    """Sayfanin ait oldugu konu blogunun band metni."""
    for bas, son, ad in KONU_BLOKLARI.get(cilt, []):
        if bas <= sayfa <= son:
            return ad
    return None


def _kelime_istatistik(metin: str) -> tuple[int, int, float]:
    kelimeler = metin.split()
    if not kelimeler:
        return 0, 0, 0.0
    return (
        len(kelimeler),
        len(set(kelimeler)),
        sum(len(k) for k in kelimeler) / len(kelimeler),
    )


def _ek_ayikla(kelime: str) -> list[str]:
    """core/turkish_nlp_service._simple_root_suffix_split'in ek toplama adimi.

    DIKKAT: kaynak dongu ilk eslesmede BREAK eder -- kelime basina EN FAZLA
    BIR ek ayiklanir. Bu davranis birebir korunur.
    """
    kalan = kelime.lower()
    for ek in sorted(EKLER, key=len, reverse=True):
        if kalan.endswith(ek) and len(kalan) > len(ek):
            return [ek]
    return []


def morfoloji_karmasikligi(metin: str) -> float:
    """Zemberek YOKKEN repo'nun dustugu heuristik yolun aynisi."""
    turkce = "\u00e7\u011f\u0131\u00f6\u015f\u00fc\u00c7\u011e\u0130\u00d6\u015e\u00dc"
    kelimeler = [
        "".join(c for c in k if c.isalnum() or c in turkce) for k in metin.split()
    ]
    kelimeler = [k for k in kelimeler if len(k) >= 2]
    if not kelimeler:
        return 0.3  # servisin bos-metin varsayilani
    en = 0.0
    for k in kelimeler:
        n = len(_ek_ayikla(k))
        en = max(en, min(1.0, n * W_EK + min(3, n) * W_TURETIM))
    return round(en, 4)


def okunabilirlik(metin: str, secenekler: dict[str, str]) -> float:
    """Atesman indeksi (repo'nun kendi servisi), 0-100'e kirpilir."""
    tam = metin + "\n" + "\n".join(secenekler.values())
    ol = TurkishReadabilityService.analyze_text(tam)
    return round(max(0.0, min(100.0, float(ol["atesman_index"]))), 2)


def bloom_belirle(metin: str, secenekler: dict[str, str]) -> tuple[int, str, str]:
    """Dar kural: sayisal sonuc istenen + besi de sayisal sik -> uygulama."""
    sayisal = sum(
        1 for s in secenekler.values() if s.strip() and SAYISAL_SIK.match(s.strip())
    )
    if sayisal == 5 and NICELIK.search(metin):
        return 3, "application", "kural:sayisal_sonuc"
    return 2, "comprehension", "varsayilan:ev_sozlesmesi"


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Veri setinin kendi isaretleri + okunamayan parca tespiti."""
    b: list[str] = []
    if r.get("sik_bos") or any(not (sec[h] or "").strip() for h in "ABCDE"):
        b.append("sik_bos")
    if (
        r.get("sik_tekrar")
        or len({(sec[h] or "").strip().lower() for h in "ABCDE"}) < 5
    ):
        b.append("sik_tekrar")
    if r.get("okuma_supheli"):
        b.append("okuma_supheli")
    if OKUNAMADI in (r.get("question_text") or "") or any(
        OKUNAMADI in (sec[h] or "") for h in "ABCDE"
    ):
        b.append("okunamadi")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r[h.lower()] for h in "ABCDE"}
    h = soru_hash(r["question_text"], sec)
    n, u, ort = _kelime_istatistik(r["question_text"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["question_text"], sec)
    band = konu_bandi(r["cilt"], int(r["sayfa"]))
    kod, duzey = KONU_HARITASI.get(band or "", (GEO_KOK_KODU, "kok"))
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": kod,
        "question_text": r["question_text"],
        "secenekler": sec,
        "correct_answer": r["correct_answer"],
        "question_image_url": f"/static/crops/{ONEK}/{r['id']}.png",
        # DIKKAT: source_page DOSYA numarasidir, kitabin BASILI sayfa
        # numarasi degil.
        "source_page": int(r["sayfa"]),
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["question_text"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["question_text"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        # Bu kitapta OSYM cikmis-soru kanali YOK: kitabin bastigi OSYM
        # sorulari zaten Mikro Orijinal ithalinde duruyor ve `ayristir()`
        # onlari yabanci sayip dokunmuyor.
        "osym_year": None,
        "osym_format_compliant": False,
        "pipeline_metadata": {
            "kaynak": "345_2025_tyt_ayt_geometri_soru_bankasi",
            "konu_bandi": band,
            "konu_kodu": kod,
            "konu_eslesme_duzeyi": duzey,
            "konu_kaynagi": "sayfa_baslik_bandi",
            "cilt": r["cilt"],
            "sayfa_dosya_no": int(r["sayfa"]),
            "sutun": r["sutun"],
            "soru_no": r["soru_no"],
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": "kitabin_basili_anahtari",
            "cevap_eslemesi": "konumsal_sutun_sirasi",
            "anahtar_dogrulamasi": "numara_surekliligi_2743_girdi_1_dizgi_hatasi",
            "sinav_turu_kaynagi": "olculmedi_kitap_TYT-AYT_karisik",
            "sekil_var": bool(r.get("sekil_var")),
            "sekil_aciklama": r.get("sekil_aciklama") or None,
            "gorsel_kaynagi": "tam_soru_kirpimi",
            "kirpim_kutusu": r["kutu"],
            "metin_kaynagi": "sutun_granulerliginde_tek_okuma",
            "bloom_kaynagi": bloom_kaynak,
            "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
            "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
            "cozum_dogrulamasi": "yapilmadi_urun_karari",
            "telif": TELIF_NOTU,
            "uretim": URETIM_NOTU,
            "ithal_araci": "scripts/kitap/geo345_ithal.py",
        },
    }


_QB = """
INSERT INTO question_bank (id, soru_hash, primary_topic_id, is_active, is_public, created_by,
    reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor)
VALUES (%(id)s, %(soru_hash)s, %(konu_id)s, FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE)
"""
_QC = """
INSERT INTO question_content (id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer, explanation, question_image_url, image_width, image_height)
VALUES (%(id)s, %(question_text)s, %(a)s, %(b)s, %(c)s, %(d)s, %(e)s, %(correct_answer)s, NULL,
    %(question_image_url)s, %(image_width)s, %(image_height)s)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'AYT', 'GEOMETRI', %(grade_level)s,
    %(osym_format_compliant)s, %(osym_year)s, %(source_book)s,
    %(source_page)s, %(pipeline_metadata)s::json, %(morphology_complexity)s, %(word_count)s,
    %(unique_word_count)s, %(average_word_length)s, %(readability_score)s, 'PENDING')
"""
_QS = """
INSERT INTO question_statistics (id, difficulty_level, irt_based_difficulty, student_success_rate,
    difficulty_update_count, irt_discrimination, irt_difficulty, irt_guessing, irt_upper_asymptote,
    is_calibrated, calibration_sample_size, calibration_quality_score, times_asked, times_correct,
    times_wrong, times_skipped, average_response_time, median_response_time, exposure_rate,
    quality_score, quality_review_status)
VALUES (%(id)s, 'MEDIUM', 'medium', 0.5, 0, 1.0, 0.0, 0.2, 1.0, FALSE, 0, 0.0, 0, 0, 0, 0, 0.0, 0.0, 0.0,
    100.0, 'pending')
"""


def _on_kontrol(kayitlar: list[dict[str, Any]]) -> list[str]:
    """Ithal oncesi ici bosluk denetimi -- bir tanesi bile varsa ithal baslamaz."""
    hata = []
    gorulen: dict[str, str] = {}
    for k in kayitlar:
        sec = k["secenekler"]
        if len(sec) != 5 or any(h not in sec for h in "ABCDE"):
            hata.append(f"{k['id']}: 5 sik degil ({sorted(sec)})")
        if not k["correct_answer"]:
            hata.append(f"{k['id']}: cevap anahtari yok")
        elif not (sec.get(k["correct_answer"]) or "").strip():
            hata.append(f"{k['id']}: anahtar {k['correct_answer']} sikki bos (R5)")
        if not k["question_text"].strip():
            hata.append(f"{k['id']}: soru metni bos")
        if k["pipeline_metadata"]["konu_bandi"] is None:
            hata.append(f"{k['id']}: sayfa hicbir konu blogunda degil")
        if k["id"] in gorulen:
            hata.append(f"{k['id']}: veri setinde ayni hash iki kez")
        gorulen[k["id"]] = k["soru_hash"]
    return hata


def _meta_yenile(conn: psycopg.Connection, eski: list[dict], yaz: bool) -> None:
    """Zaten yazilmis satirlarin turetik alanlarini ve gorsel referanslarini tazeler."""
    if not yaz:
        print(f"(--meta-guncelle plani: {len(eski)} satirin metadata'si yenilenecek)")
        return
    with conn.transaction():
        for k in eski:
            conn.execute(
                "UPDATE question_metadata SET pipeline_metadata = %(pm)s::json, "
                "readability_score = %(oku)s, morphology_complexity = %(morf)s, "
                "bloom_level = %(bl)s, bloom_category = %(bk)s WHERE id = %(id)s",
                {
                    "id": k["id"],
                    "pm": json.dumps(k["pipeline_metadata"], ensure_ascii=False),
                    "oku": k["readability_score"],
                    "morf": k["morphology_complexity"],
                    "bl": k["bloom_level"],
                    "bk": k["bloom_category"],
                },
            )
            conn.execute(
                "UPDATE question_bank SET primary_topic_id = %(kid)s WHERE id = %(id)s",
                {"id": k["id"], "kid": k["konu_id"]},
            )
            conn.execute(
                "UPDATE question_content SET question_image_url = %(u)s WHERE id = %(id)s",
                {"id": k["id"], "u": k["question_image_url"]},
            )
    print(f"META GUNCELLENDI: {len(eski)} satir")


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    morf = [k["morphology_complexity"] for k in kayitlar]
    band = Counter(k["pipeline_metadata"]["konu_bandi"] for k in kayitlar)
    print("konu dagilimi:")
    for ad, adet in band.most_common():
        kod, duzey = KONU_HARITASI.get(ad or "", (GEO_KOK_KODU, "kok"))
        print(f"  {adet:5d}  {kod:28s} ({duzey})  {ad}")
    print(
        "eslesme duzeyi    :",
        dict(Counter(k["pipeline_metadata"]["konu_eslesme_duzeyi"] for k in kayitlar)),
    )
    print(
        "cilt dagilimi     :",
        dict(Counter(k["pipeline_metadata"]["cilt"] for k in kayitlar)),
    )
    print(
        "sekil iceren      :",
        sum(1 for k in kayitlar if k["pipeline_metadata"]["sekil_var"]),
    )
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak))
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(
            f"okunabilirlik     : ort {sum(oku) / len(oku):.1f}  "
            f"min {min(oku)}  maks {max(oku)}"
        )
        print(
            f"morfoloji         : ort {sum(morf) / len(morf):.3f}  "
            f"min {min(morf)}  maks {max(morf)}"
        )


def _konu_id_ata(
    conn: psycopg.Connection, kayitlar: list[dict[str, Any]]
) -> str | None:
    """Her kayda konu_id yazar; basarisizsa DURDURMA gerekcesini dondurur.

    Kok dugume sessizce dusurmek YOK: agac eksikse ithal hic baslamaz.
    """
    kok = conn.execute(
        "SELECT id FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
        (GEO_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{GEO_KOK_KODU} kok konusu yok"
    kodlar = sorted({k["konu_kodu"] for k in kayitlar})
    konular: dict[str, str] = dict(
        conn.execute(
            "SELECT code, id FROM topic_hierarchy WHERE code = ANY(%s)",
            (kodlar,),
        ).fetchall()
    )
    eksik = set(kodlar) - set(konular)
    if eksik:
        return (
            f"{len(eksik)} konu kodu agacta yok: {sorted(eksik)}. Kok dugume "
            "dusurup sessizce yanlis baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def ithal(veri_yolu: Path, dsn: str, yaz: bool, meta_guncelle: bool = False) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    print(f"veri setinde {len(veri)} soru")
    if not veri:
        print("DURDU: ithal edilecek satir yok")
        return 2

    kayitlar = [kayit_uret(r) for r in veri]
    veri_kutu = {k["id"]: r["kutu"] for k, r in zip(kayitlar, veri, strict=True)}
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return 2
    print(
        "on kontrol: 5 sik + dolu anahtar + dolu metin + konu blogu + "
        "benzersiz hash -- TEMIZ"
    )

    with psycopg.connect(dsn) as conn:
        gerekce = _konu_id_ata(conn, kayitlar)
        if gerekce:
            print(f"DURDU: {gerekce}")
            return 2

        # DIKKAT: soru_hash metin+5 sik uzerinden hesaplandigi icin ayni soru
        # baska bir kaynakta da varsa ID AYNI olur. Bu kitapta 35 soru boyle
        # (hepsi Mikro Orijinal ithalinde duran resmi OSYM sorulari).
        yeni, bizim, yabanci = ayristir(conn, kayitlar, KAYNAK_ADI)
        print(f"zaten var: {len(kayitlar) - len(yeni)}, yazilacak: {len(yeni)}")
        yabanci_yaz(yabanci)

        if meta_guncelle and bizim:
            _meta_yenile(conn, bizim, yaz)
        _ozet(yeni or kayitlar)
        if not yaz:
            print("(--yaz verilmedi; hicbir sey yazilmadi)")
            return 0

        with conn.transaction():
            for k in yeni:
                s = k["secenekler"]
                kutu = veri_kutu[k["id"]]
                conn.execute(_QB, k)
                conn.execute(
                    _QC,
                    {
                        "id": k["id"],
                        "question_text": k["question_text"],
                        "a": s["A"],
                        "b": s["B"],
                        "c": s["C"],
                        "d": s["D"],
                        "e": s["E"],
                        "correct_answer": k["correct_answer"],
                        "question_image_url": k["question_image_url"],
                        "image_width": kutu[2] - kutu[0],
                        "image_height": kutu[3] - kutu[1],
                    },
                )
                conn.execute(
                    _QM,
                    {
                        **k,
                        "grade_level": SINIF_DUZEYI,
                        "source_book": KAYNAK_ADI,
                        "pipeline_metadata": json.dumps(
                            k["pipeline_metadata"], ensure_ascii=False
                        ),
                    },
                )
                conn.execute(_QS, {"id": k["id"]})

        n, aktif, kapida = conn.execute(
            """SELECT count(*),
                      count(*) FILTER (WHERE b.is_active),
                      count(*) FILTER (WHERE EXISTS (
                          SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id))
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s""",
            (KAYNAK_ADI,),
        ).fetchone()
        print(f"YAZILDI: {len(yeni)} yeni satir")
        print(
            f"DB'de {KAYNAK_ADI}: toplam {n}, is_active {aktif}, kapidan gecen {kapida}"
        )
        if aktif or kapida:
            print(
                "HATA: pasif ithal sozlesmesi bozuldu "
                "(aktif ya da kapidan gecen satir var)"
            )
            return 3
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--veri", default=VARSAYILAN_VERI)
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    p.add_argument(
        "--meta-guncelle",
        action="store_true",
        help="var olan satirlarin turetik alanlarini/gorsel URL'sini yeniden yaz",
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    return ithal(Path(args.veri), args.dsn, args.yaz, args.meta_guncelle)


if __name__ == "__main__":
    raise SystemExit(main())
