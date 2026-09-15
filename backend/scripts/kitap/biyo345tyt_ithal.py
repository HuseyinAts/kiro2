#!/usr/bin/env python
"""345 2025 TYT Biyoloji Soru Bankasi -- OCR ciktisini PASIF ithal eder.

NEDEN PASIF VE is_ai_generated=TRUE
-----------------------------------
0013/0015/0017/0021/geo345 ile ayni gerekce: metin bir OCR/VLM hattindan
geldi. Kaynak zkitap goruntuleyici EKRAN GORUNTUSUDUR. Her satir soyle
yazilir:

    is_active = FALSE, is_public = FALSE,
    is_ai_generated = TRUE, review_status = 'PENDING'

Servis kapisi (`v_safe_for_beta`) `(is_ai_generated = false OR
review_status = 'APPROVED')` ister; iki alan da bu satirlari kapinin
DISINDA tutar. Ithal tek basina hicbir soruyu ogrenciye ulastirmaz;
aktiflestirme ayri karardir.

VERI NEREDEN GELIYOR
--------------------
`veriseti/zkitap/cikti/biyo345tyt_sorular.json` -- OCR klasorunden
`scripts/kitap/biyo345tyt_derle.py` ile derlenir (git disinda kalan
ocr_json/ klasorunu bu arac okur, ithal araci okumaz).

CEVAP KAYNAGI: KITABIN BASILI CEVAP SERIDI
------------------------------------------
Sorular tekrar cozulerek dogrulanmaz (urun karari). 1024 cevabin 1024'u
sayfa altindaki cevap seridinden okundu (`cevap_kaynagi` alaninda kayitli)
ve dogrulayici K1-K11 hic kusur bulmadi. `explanation` bu yuzden NULL.

KONU BAGLAMA: SAYFANIN KENDI BASLIK BANDINDAN, UNITE DUZEYI
-----------------------------------------------------------
0017/geo345 ilkesi. Olcum (ocr_json/, 15 Eyl 2026): 219 soru sayfasinin
112'sinde bant var; kanonlastirilinca 14 ad kaliyor ve bu 14 ad sayfa
sirasinda tam 14 KOSU olusturuyor -- hicbir konu ikinci kez acilmiyor.
Bantsiz 107 sayfa bloklarin arasinda kaliyor ("OSYM Tadinda / Orijinal /
Karma Sorular" bolumleri); bir ONCEKI bloga ait olduklari 11 ornek sayfada
soru metni okunarak dogrulandi (11/11).

0022 migration'i bu 14 konuyu BIO-T1..BIO-T14 olarak kurar. Kitapta unite
alti konu etiketi YOKTUR; sayfa ustundeki "Kazanim Odakli / Karma / OSYM
Tadinda / Orijinal Sorular / OSYM Kosesi" konu degil TEST TURUDUR ve soru
duzeyinde `pipeline_metadata.test_turu` olarak tasinir. Var olmayan bir L3
katmani uydurulmadi; `konu_eslesme_duzeyi='unite'` ile ISARETLENIR.

DIKKAT: BIO-U1..U16 (0021) AYT uniteleridir ve bu kitapla TEK BIR ORTUSME
YOKTUR; bu yuzden ayri bir TYT seti kuruldu, var olan bir uniteye
baglanmadi.

BILINEN SINIR: SORU GORSELI YOK
-------------------------------
Bu kitabin gorsel hatti sayfa ve SUTUN kirpimi uretti, SORU KUTUSU
uretmedi. Veri setinde kirpim kutusu yok, bu yuzden `question_image_url`
NULL yazilir (semada zaten 2303 satir boyle). Sekil iceren 334 soru
`bayraklar` icinde `gorsel_yok_sekilli` ile ISARETLENIR -- bu sorular
metin olarak eksiktir ve AKTIFLESTIRMEDEN ONCE kutu tespit turu
gerektirir. Sutun kirpiminin dosya adi her satirda
`pipeline_metadata.sutun_gorseli` olarak durur.

CIKMIS SORULAR
--------------
84 soru `is_real_exam_question` ve `exam_year` tasiyor; `osym_year` ve
`osym_format_compliant` YALNIZ bu sorularda doldurulur -- yayinevinin
kendi yazdigi sorulara OSYM damgasi vurulmaz.

Kurallar
--------
- id = uuid5(NAMESPACE_OID, soru_hash); soru_hash = pilot_500p formulu.
- Ayni id varsa satir ATLANIR (idempotent; tekrar kosum guvenli).
- primary_topic_id: 0022'nin kurdugu BIO-T<n>; eksikse ithal DURUR.

KULLANIM
--------
    python backend/scripts/kitap/biyo345tyt_ithal.py --dsn postgresql://... [--yaz]
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
VARSAYILAN_VERI = "veriseti/zkitap/cikti/biyo345tyt_sorular.json"
KAYNAK_ADI = "345 2025 TYT Biyoloji Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
BIO_KOK_KODU = "BIO"
# 0022 kodlari: BIO-T1 ... BIO-T14. Desen BIO kokunu, BIO-OSYM-GENEL'i ve
# 0021'in BIO-U* AYT unitelerini KAPSAMAZ.
KOD_ONEKI = "BIO-T"
SINAV_TURU = "TYT"
DERS_ALANI = "BIYOLOJI"
SINIF_DUZEYI = 12  # mevcut TYT satirlarinin ev sozlesmesi (olculdu: 5373/6394)
TELIF_NOTU = (
    "UcDortBes Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "OCR/VLM hatti: sayfa + sutun kirpimi, sayfa basina JSON cikarim, "
    "dogrulayici K1-K11 (sayim, sutun dagilimi, beyan durustlugu, cevap "
    "gecerliligi, bos sik, kisaltma izi, NFC, sayfa ici numara sirasi, "
    "sayfa ici ve sayfalar arasi tekrar, sayfalar arasi numara surekliligi) "
    "-- 1024 soruda 0 kusur. Cevaplar kitabin basili cevap seridinden "
    "okundu; soru cozulmedi. Konu, sayfanin kendi baslik bandindan. "
    "Detay: veriseti/zkitap/cikti/BIYO345TYT_YONTEM.md"
)

# core/turkish_nlp_service._simple_root_suffix_split ile BIREBIR ayni liste.
# Turkce harfler \u kacisiyla yazilir (kaynak dosya ASCII kalsin diye);
# ASCII'ye duzlestirmek YANLIS olur -- gercek metinde "nin" gecer.
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

# DIKKAT -- KATASTROFIK GERI IZLEME ONARIMI (PR #266/#269 ile ayni desen).
# Eski desen sondaki grubu ic ice nicelemisti ve eslesmeyen girdilerde
# ustel geri izleme uretiyordu. Yeni desen ic ice nicelemez.
SAYISAL_SIK = re.compile(
    "^[\\s\\d.,/+\\-x*^()\u2212\u221a\u00b7]+[a-zA-Z\u00b0%/\u00b2\u00b3\\s]{0,12}$"
)
NICELIK = re.compile(
    "ka\u00e7|b\u00fcy\u00fckl\u00fc\u011f\u00fc\\s+ne|de\u011feri\\s+ne|ka\u00e7t\u0131r",
    re.IGNORECASE,
)


def _nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t or "").strip()


def soru_hash(metin: str, secenekler: dict[str, str]) -> str:
    """scripts/pipeline/pilot_500p.py::_hash_question ile birebir."""
    payload = "|".join(
        [_nfc(metin).lower()] + [_nfc(secenekler.get(h, "")) for h in "ABCDE"]
    )
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()


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
    """Veri setinin isaretleri + bu kitaba ozgu gorsel eksigi."""
    b: list[str] = []
    if any(not (sec[h] or "").strip() for h in "ABCDE"):
        b.append("sik_bos")
    # DIKKAT: kiyas HARF BUYUKLUGUNE DUYARLI. geo345/biyo345'te bu karsilastirma
    # .lower() ile yapiliyor; biyolojide bu YANLIS POZITIF uretiyor cunku
    # genetik sorularinda siklar yalnizca harf buyukluguyle ayrilir (alel
    # gosterimi: 'A' baskin, 'a' cekinik). Olculdu: lower() ile 9 soru "sik
    # tekrar" sayiliyor, duyarli kiyasla 0 -- dokuzunun da siklari gercekte
    # farkli (orn. s0174 sag #5: aBCD / ABDd / ABCD / aBcd / ABcd).
    if len({(sec[h] or "").strip() for h in "ABCDE"}) < 5:
        b.append("sik_tekrar")
    # Bu kitapta soru gorseli YOK; sekil iceren sorular metin olarak
    # eksiktir ve aktiflestirmeden once kutu tespiti gerektirir.
    if r.get("sekil_var"):
        b.append("gorsel_yok_sekilli")
    if not r.get("sayfada_bant_var"):
        b.append("konu_komsudan")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r[h.lower()] for h in "ABCDE"}
    h = soru_hash(r["question_text"], sec)
    n, u, ort = _kelime_istatistik(r["question_text"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["question_text"], sec)
    cikmis = bool(r.get("cikmis")) and bool(r.get("sinav_yili"))
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "question_text": r["question_text"],
        "secenekler": sec,
        "correct_answer": r["correct_answer"],
        # Bu kitapta soru kirpimi YOK -- bkz. modul basligi.
        "question_image_url": None,
        # DIKKAT: source_page DOSYA numarasidir; kitabin BASILI sayfa
        # numarasi pipeline_metadata.basili_sayfa'da ayrica durur (bu
        # kitapta ikisi 0196 sonrasi AYRISIYOR, kaynak veri kusuru).
        "source_page": int(r["sayfa"]),
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["question_text"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["question_text"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": int(r["sinav_yili"]) if cikmis else None,
        "osym_format_compliant": cikmis,
        "pipeline_metadata": {
            "kaynak": "345_2025_tyt_biyoloji_soru_bankasi",
            "konu_kodu": r["konu_kodu"],
            "konu_bandi": r.get("konu_bandi"),
            "konu_eslesme_duzeyi": "unite",
            "konu_kaynagi": (
                "sayfa_baslik_bandi"
                if r.get("sayfada_bant_var")
                else "blok_icinde_komsu_sayfadan"
            ),
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": r.get("basili_sayfa"),
            "sutun": r.get("sutun"),
            "pozisyon": r.get("pozisyon"),
            "soru_no": r.get("soru_no"),
            "test_turu": r.get("test_turu"),
            "test_no": r.get("test_no"),
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": r.get("cevap_kaynagi") or "cevap_seridi",
            "anahtar_dogrulamasi": "dogrulayici_K1_K11_1024_soruda_0_kusur",
            "cikmis_soru": bool(r.get("cikmis")),
            "sinav_yili": r.get("sinav_yili"),
            "sekil_var": bool(r.get("sekil_var")),
            "gorsel_kaynagi": "yok_soru_kirpimi_uretilmedi",
            "sutun_gorseli": r.get("sutun_gorseli"),
            "zorluk_tahmini": r.get("zorluk_tahmini"),
            "cikarim_guveni": r.get("cikarim_guveni"),
            "metin_kaynagi": "sayfa_granulerliginde_tek_okuma",
            "bloom_kaynagi": bloom_kaynak,
            "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
            "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
            "cozum_dogrulamasi": "yapilmadi_urun_karari",
            "telif": TELIF_NOTU,
            "uretim": URETIM_NOTU,
            "ithal_araci": "scripts/kitap/biyo345tyt_ithal.py",
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
    NULL, NULL, NULL)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'TYT', 'BIYOLOJI', %(grade_level)s,
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
    gorulen: set[str] = set()
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
        if not (k["konu_kodu"] or "").startswith(KOD_ONEKI):
            hata.append(f"{k['id']}: konu kodu {k['konu_kodu']!r} {KOD_ONEKI}* degil")
        if k["id"] in gorulen:
            hata.append(f"{k['id']}: veri setinde ayni hash iki kez")
        gorulen.add(k["id"])
    return hata


def _konu_id_ata(
    conn: psycopg.Connection, kayitlar: list[dict[str, Any]]
) -> str | None:
    """Her kayda konu_id yazar; basarisizsa DURDURMA gerekcesini dondurur.

    Kok dugume sessizce dusurmek YOK: 0022 kosmamissa ithal hic baslamaz.
    """
    kok = conn.execute(
        "SELECT id FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
        (BIO_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{BIO_KOK_KODU} kok konusu yok"
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
            f"{len(eksik)} konu kodu agacta yok: {sorted(eksik)}. "
            "0022_biyo345tyt_konu_agaci kosmadi mi? Kok dugume dusurup "
            "sessizce yanlis baglamaktansa duruyorum."
        )
    for k in kayitlar:
        k["konu_id"] = konular[k["konu_kodu"]]
    return None


def _meta_yenile(conn: psycopg.Connection, eski: list[dict], yaz: bool) -> None:
    """Zaten yazilmis satirlarin turetik alanlarini tazeler."""
    if not yaz:
        print(f"(--meta-guncelle plani: {len(eski)} satirin metadata'si yenilenecek)")
        return
    with conn.transaction():
        for k in eski:
            conn.execute(
                "UPDATE question_metadata SET pipeline_metadata = %(pm)s::json, "
                "readability_score = %(oku)s, morphology_complexity = %(morf)s, "
                "bloom_level = %(bl)s, bloom_category = %(bk)s, osym_year = %(yil)s, "
                "osym_format_compliant = %(resmi)s WHERE id = %(id)s",
                {
                    "id": k["id"],
                    "pm": json.dumps(k["pipeline_metadata"], ensure_ascii=False),
                    "oku": k["readability_score"],
                    "morf": k["morphology_complexity"],
                    "bl": k["bloom_level"],
                    "bk": k["bloom_category"],
                    "yil": k["osym_year"],
                    "resmi": k["osym_format_compliant"],
                },
            )
            conn.execute(
                "UPDATE question_bank SET primary_topic_id = %(kid)s WHERE id = %(id)s",
                {"id": k["id"], "kid": k["konu_id"]},
            )
    print(f"META GUNCELLENDI: {len(eski)} satir")


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    morf = [k["morphology_complexity"] for k in kayitlar]
    print("konu dagilimi:")
    sayac = Counter(k["konu_kodu"] for k in kayitlar)
    for kod, adet in sorted(sayac.items(), key=lambda kv: -kv[1]):
        band = next(
            k["pipeline_metadata"]["konu_bandi"]
            for k in kayitlar
            if k["konu_kodu"] == kod
        )
        print(f"  {adet:5d}  {kod:9s}  {band}")
    print(
        "test turu         :",
        dict(Counter(k["pipeline_metadata"]["test_turu"] for k in kayitlar)),
    )
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak))
    print("cikmis (yil dolu) :", sum(1 for k in kayitlar if k["osym_year"]))
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


def ithal(veri_yolu: Path, dsn: str, yaz: bool, meta_guncelle: bool = False) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    print(f"veri setinde {len(veri)} soru")
    if not veri:
        print("DURDU: ithal edilecek satir yok")
        return 2

    kayitlar = [kayit_uret(r) for r in veri]
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return 2
    print(
        "on kontrol: 5 sik + dolu anahtar + dolu metin + BIO-T konu kodu + "
        "benzersiz hash -- TEMIZ"
    )

    with psycopg.connect(dsn) as conn:
        gerekce = _konu_id_ata(conn, kayitlar)
        if gerekce:
            print(f"DURDU: {gerekce}")
            return 2

        # DIKKAT: soru_hash metin+5 sik uzerinden hesaplandigi icin ayni soru
        # baska bir kaynakta da varsa ID AYNI olur. Var olan satirlar kaynak
        # kitaba gore ayrilir; --meta-guncelle YALNIZ bu kitabin satirlarina
        # dokunur.
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
        help="var olan satirlarin turetik alanlarini yeniden yaz",
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    return ithal(Path(args.veri), args.dsn, args.yaz, args.meta_guncelle)


if __name__ == "__main__":
    raise SystemExit(main())
