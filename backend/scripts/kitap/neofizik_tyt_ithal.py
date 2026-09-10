#!/usr/bin/env python
"""Neofizik TYT Fizik Soru Bankasi -- OCR ciktisini question_bank'a PASIF ithal eder.

NEDEN PASIF VE is_ai_generated=TRUE
-----------------------------------
0013/0014'teki AYT ithaliyla ayni gerekce: metin bir OCR/VLM hattindan geldi
(kitabin PDF'inde metin katmani YOK; 256 sayfanin tamami 1920x1080 raster).
Her satir su sekilde yazilir:

    is_active = FALSE, is_public = FALSE,
    is_ai_generated = TRUE, review_status = 'PENDING'

Servis kapisi (`v_safe_for_beta`) `(is_ai_generated = false OR review_status =
'APPROVED')` ister; iki alan da bu satirlari kapinin DISINDA tutar. Ithal tek
basina hicbir soruyu ogrenciye ulastirmaz; aktiflestirme ayri karardir.

CEVAP KAYNAGI: YALNIZ KITABIN BASILI ANAHTARI
---------------------------------------------
Sorular tekrar cozulerek dogrulanmaz (urun karari). Basili anahtar tek
kaynaktir ve segmentasyona karsi bagimsiz yer gercegi olarak da kullanildi:
109 test blogunun 109'unda anahtardaki cevap sayisi o bloktaki soru sayisiyla
birebir esit. `explanation` bu yuzden NULL birakilir -- cozum uretilmedi,
uretilmis gibi gosterilmez.

DOLDURULAN TURETIK ALANLAR (hepsi HESAPLANIR, sabit degil)
----------------------------------------------------------
- readability_score : Atesman okunabilirlik indeksi; repo'nun kendi
  services/turkish_readability_service.py'sinden hesaplanir (sabit 50.0 degil).
- morphology_complexity : repo'nun kendi Turkce morfoloji hattinin ZEMBEREKSIZ
  yolu (core/turkish_nlp_service._simple_root_suffix_split +
  algorithms/irt_morfoloji_service._calculate_word_complexity agirliklari).
  OLCULDU: bu yol kelime basina EN FAZLA BIR ek soyar, bu yuzden soru duzeyinde
  deger 0.0 ile 0.35 arasinda IKI degere cokuyor ve 891 fizik sorusunun
  tamaminda 0.35 cikiyor -- yani bu alan Zemberek olmadan BILGI TASIMIYOR.
  Uydurmak yerine oldugu gibi yazilir ve metadata'da
  `morfoloji_kaynagi='heuristik_zemberek_yok_sabit'` ile ACIKCA isaretlenir.
  Gercek deger icin Zemberek gerekir; makinede jar var ama jpype Java 9+
  istiyor, kurulu Java 8. Zemberek acildiginda `--meta-guncelle` 891 satiri
  yeniden hesaplar (satirlar silinmez).
- word_count / unique_word_count / average_word_length : metinden sayilir.
- bloom_level : DAR ve tanimli bir kural; yalnizca "sayisal sonuc isteyen +
  besi de sayisal sik" deseninde 3/application, aksi halde ev varsayilani
  2/comprehension. Kaynak metadata'da `bloom_kaynagi` ile isaretlenir.
- osym_year / osym_format_compliant : YALNIZCA metninde basili sinav-yil
  etiketi olan cikmis sorularda doldurulur (91 soru: TYT 2018-2024,
  MSU 2019-2024). Yayinevinin kendi yazdigi sorulara OSYM damgasi vurulmaz.

VERI NEREDEN GELIYOR
--------------------
`veriseti/zkitap/cikti/neofizik_tyt_sorular.json` (git disinda; .gitignore
`veriseti/`). Uretim yontemi ve olcumleri ayni klasordeki TYT_YONTEM.md'de:
iki bagimsiz okuma (891/891 soru), normalizasyon sonrasi 870/870 birebir uyum,
kalan 21 soru hakem turunda gorselle cozuldu.

Kurallar
--------
- id = uuid5(NAMESPACE_OID, soru_hash); soru_hash = pilot_500p formulu
  (md5(lower(nfc(question_text))|A|B|C|D|E)) -- uq_qb_soru_hash_active uyumlu.
- Ayni id varsa satir ATLANIR (idempotent; tekrar kosum guvenli).
- primary_topic_id: 0015 migration'inin kurdugu FIZ alt agaci
  (FIZ-NEOT-U<n>-<KONU>); bulunamazsa FIZ koku.
- question_image_url = /static/crops/NEOFIZIK_TYT/<id>.png

KULLANIM
--------
    python backend/scripts/kitap/neofizik_tyt_ithal.py --dsn postgresql://... [--yaz]
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

from services.turkish_readability_service import TurkishReadabilityService

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
VARSAYILAN_VERI = "veriseti/zkitap/cikti/neofizik_tyt_sorular.json"
KAYNAK_ADI = "Neofizik TYT Fizik Soru Bankasi"
ONEK = "NEOFIZIK_TYT"
FIZ_KOK_KODU = "FIZ"
SINAV_TURU = "TYT"
SINIF_DUZEYI = 12  # mevcut TYT satirlarinin cogunlugu (4482/5503) -- ev sozlesmesi
TELIF_NOTU = (
    "Neofizik Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "OCR/VLM hatti: iki bagimsiz okuma + uyusmazlikta hakem turu + kitabin "
    "basili cevap anahtari (tek cevap kaynagi; soru tekrar cozulmedi). "
    "Detay: veriseti/zkitap/cikti/TYT_YONTEM.md"
)

# core/turkish_nlp_service._simple_root_suffix_split ile BIREBIR ayni liste.
# Turkce harfler \u kacisiyla yazilir (kaynak dosya ASCII kalsin diye); ASCII'ye
# duzlestirmek YANLIS olur -- "basinclarin" ile "basinclarin" ayni ek degildir,
# gercek metinde "n\u0131n" gecer. Ilk surumde duzlestirilmisti ve olcum
# morfoloji=0.0 verdi; hata boyle yakalandi.
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
# algorithms/irt_morfoloji_service.complexity_weights ile ayni agirliklar
W_EK, W_TURETIM, W_BIRLESIK = 0.15, 0.20, 0.25

# Not: Turkce karakterler \u kacisiyla yazilir -- kaynak dosya ASCII kalir.
SAYISAL_SIK = re.compile(
    "^[\\s\\d.,/+\\-x*^()]+(?:[a-zA-Z\u00b0%/\u00b2\u00b3]{0,6}\\s*)*$"
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


def konu_kodu(unite_no: int, konu: str) -> str:
    """0015 migration'inin urettigi kodla birebir ayni olmali.

    topic_hierarchy.code varchar(50) -- kesme siniri buradan geliyor.
    """
    sade = unicodedata.normalize("NFKD", _ascii_tr(konu).upper())
    sade = "".join(c for c in sade if not unicodedata.combining(c))
    slug = "".join(ch if ch.isalnum() else "-" for ch in sade).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return f"FIZ-NEOT-U{unite_no}-{slug}"[:50].rstrip("-")


def _ascii_tr(s: str) -> str:
    esle = {
        "\u0131": "i",
        "\u0130": "I",
        "\u015f": "s",
        "\u015e": "S",
        "\u011f": "g",
        "\u011e": "G",
        "\u00fc": "u",
        "\u00dc": "U",
        "\u00f6": "o",
        "\u00d6": "O",
        "\u00e7": "c",
        "\u00c7": "C",
    }
    return "".join(esle.get(c, c) for c in s)


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
    BIR ek ayiklanir. Bu davranis birebir korunur; cok ekli bir ayiklama
    yazmak uretimdeki degerden farkli sayi uretirdi.
    """
    kalan = kelime.lower()
    for ek in sorted(EKLER, key=len, reverse=True):
        if kalan.endswith(ek) and len(kalan) > len(ek):
            return [ek]
    return []


def morfoloji_karmasikligi(metin: str) -> float:
    """Zemberek YOKKEN repo'nun dustugu heuristik yolun aynisi.

    irt_morfoloji_service._calculate_word_complexity: en karmasik kelimenin
    skoru alinir (ek_sayisi*0.15 + min(3, ek_sayisi)*0.20 + birlesik*0.25),
    0-1'e kirpilir. Birlesiklik fallback yolunda daima False'tur.
    """
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
    # _ek_ayikla en fazla 1 ek dondurdugu icin en \in {0.0, 0.35}. Bu, kaynak
    # servisin davranisidir; burada duzeltilmez, isaretlenir (bkz docstring).
    return round(en, 4)


def okunabilirlik(metin: str, secenekler: dict[str, str]) -> float:
    """Atesman indeksi (repo'nun kendi servisi), 0-100'e kirpilir."""
    tam = metin + "\n" + "\n".join(secenekler.values())
    ol = TurkishReadabilityService.analyze_text(tam)
    return round(max(0.0, min(100.0, float(ol["atesman_index"]))), 2)


def bloom_belirle(metin: str, secenekler: dict[str, str]) -> tuple[int, str, str]:
    """Dar kural: sayisal sonuc istenen + besi de sayisal sik -> uygulama.

    Baska hicbir Bloom yukseltmesi yapilmaz; dogrulanmamis bir siniflandirici
    uydurmak yerine ev varsayilani (2/comprehension) korunur.
    """
    sayisal = sum(
        1 for s in secenekler.values() if s.strip() and SAYISAL_SIK.match(s.strip())
    )
    if sayisal == 5 and NICELIK.search(metin):
        return 3, "application", "kural:sayisal_sonuc"
    return 2, "comprehension", "varsayilan:ev_sozlesmesi"


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = r["secenekler"]
    h = soru_hash(r["soru_metni"], sec)
    n, u, ort = _kelime_istatistik(r["soru_metni"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["soru_metni"], sec)
    varliklar = [
        {
            "tur": v["tur"],
            "url": f"/static/crops/{ONEK}/{Path(v['dosya']).name}",
            "kutu": v["kutu"],
            "guven": v.get("guven"),
        }
        for v in r.get("gorsel_varliklar", [])
    ]
    resmi = bool(r.get("sinav_yili"))
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": konu_kodu(r["bolum_no"], r["konu"]),
        "question_text": r["soru_metni"],
        "secenekler": sec,
        "correct_answer": r["dogru_cevap"],
        "question_image_url": f"/static/crops/{ONEK}/{r['id']}.png",
        "source_page": r["sayfa"],
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["soru_metni"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["soru_metni"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": r.get("sinav_yili"),
        "osym_format_compliant": resmi,
        "pipeline_metadata": {
            "kaynak": "neofizik_tyt_soru_bankasi",
            "kayit_id": r["id"],
            "unite_no": r["bolum_no"],
            "unite_adi": r["bolum_adi"],
            "konu": r["konu"],
            "test_no": r["test_no"],
            "soru_no": r["soru_no"],
            "bayraklar": r["bayraklar"],
            "cevap_kaynagi": r["cevap_kaynagi"],
            "cikmis_soru": r["cikmis_soru"],
            "sinav_kaynagi": r.get("sinav_kaynagi"),
            "sinav_yili": r.get("sinav_yili"),
            "gorsel_varliklar": varliklar,
            "kirpim_kutusu": r.get("kirpim_kutusu"),
            "metin_kaynagi": r["metin_kaynagi"],
            "ikinci_okuma_uyumu": r.get("ikinci_okuma_uyumu"),
            "guven": r["guven"],
            "bloom_kaynagi": bloom_kaynak,
            "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
            "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
            "cozum_dogrulamasi": "yapilmadi_urun_karari",
            "telif": TELIF_NOTU,
            "uretim": URETIM_NOTU,
            "ithal_araci": "scripts/kitap/neofizik_tyt_ithal.py",
        },
    }


_QB = """
INSERT INTO question_bank (id, soru_hash, primary_topic_id, is_active, is_public, created_by,
    reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor)
VALUES (%(id)s, %(soru_hash)s, %(konu_id)s, FALSE, FALSE, NULL, NULL, now(), now(), TRUE, 'PENDING', FALSE)
"""
_QC = """
INSERT INTO question_content (id, question_text, option_a, option_b, option_c, option_d, option_e,
    correct_answer, explanation, question_image_url)
VALUES (%(id)s, %(question_text)s, %(a)s, %(b)s, %(c)s, %(d)s, %(e)s, %(correct_answer)s, NULL, %(question_image_url)s)
"""
_QM = """
INSERT INTO question_metadata (id, bloom_level, bloom_category, exam_type, subject_area, grade_level,
    osym_format_compliant, osym_year, source_book, source_page, pipeline_metadata, morphology_complexity,
    word_count, unique_word_count, average_word_length, readability_score, pedagogical_status)
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'TYT', 'FIZIK', %(grade_level)s,
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
                "UPDATE question_content SET question_image_url = %(u)s WHERE id = %(id)s",
                {"id": k["id"], "u": k["question_image_url"]},
            )
    print(f"META GUNCELLENDI: {len(eski)} satir")


def _ozet(kayitlar: list[dict[str, Any]]) -> None:
    oku = [k["readability_score"] for k in kayitlar]
    morf = [k["morphology_complexity"] for k in kayitlar]
    print(
        "konu dagilimi (ilk 6):",
        dict(Counter(k["pipeline_metadata"]["konu"] for k in kayitlar).most_common(6)),
    )
    print(
        "gorsel varligi olan:",
        sum(1 for k in kayitlar if k["pipeline_metadata"]["gorsel_varliklar"]),
    )
    print(
        "sik_bos bayrakli  :",
        sum(1 for k in kayitlar if "sik_bos" in k["pipeline_metadata"]["bayraklar"]),
    )
    print("cikmis (yil dolu) :", sum(1 for k in kayitlar if k["osym_year"]))
    print("bloom dagilimi    :", dict(Counter(k["bloom_category"] for k in kayitlar)))
    if oku:
        print(
            f"okunabilirlik     : ort {sum(oku)/len(oku):.1f}  min {min(oku)}  maks {max(oku)}"
        )
        print(
            f"morfoloji         : ort {sum(morf)/len(morf):.3f}  min {min(morf)}  maks {max(morf)}"
        )


def ithal(veri_yolu: Path, dsn: str, yaz: bool, meta_guncelle: bool = False) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    hazir = [r for r in veri if r["inceleme_durumu"] == "ONAYA_HAZIR"]
    print(f"veri setinde {len(veri)} soru; ONAYA_HAZIR {len(hazir)}")
    if not hazir:
        print("DURDU: ithal edilecek ONAYA_HAZIR satir yok")
        return 2

    kayitlar = [kayit_uret(r) for r in hazir]
    hata = _on_kontrol(kayitlar)
    if hata:
        print(f"DURDU: on kontrol {len(hata)} sorun buldu; ilk 10:")
        for h in hata[:10]:
            print("   ", h)
        return 2
    print("on kontrol: 5 sik + dolu anahtar + dolu metin + benzersiz hash -- TEMIZ")

    with psycopg.connect(dsn) as conn:
        kok = conn.execute(
            "SELECT id FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
            (FIZ_KOK_KODU,),
        ).fetchone()
        if not kok:
            print(f"DURDU: {FIZ_KOK_KODU} kok konusu yok")
            return 2
        konular: dict[str, str] = dict(
            conn.execute(
                "SELECT code, id FROM topic_hierarchy WHERE code LIKE 'FIZ-NEOT-%'"
            ).fetchall()
        )
        eksik_konu = {k["konu_kodu"] for k in kayitlar} - set(konular)
        if eksik_konu:
            print(
                f"UYARI: {len(eksik_konu)} konu kodu yok (0015 migration kosmadi mi?); "
                f"bunlar FIZ koku ile yazilacak. Ornek: {sorted(eksik_konu)[:3]}"
            )
        for k in kayitlar:
            k["konu_id"] = konular.get(k["konu_kodu"], kok[0])

        var = {
            r[0]
            for r in conn.execute(
                "SELECT id FROM question_bank WHERE id = ANY(%s)",
                ([k["id"] for k in kayitlar],),
            ).fetchall()
        }
        yeni = [k for k in kayitlar if k["id"] not in var]
        print(f"zaten var: {len(var)}, yazilacak: {len(yeni)}")

        if meta_guncelle and var:
            _meta_yenile(conn, [k for k in kayitlar if k["id"] in var], yaz)
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
                        "question_image_url": k["question_image_url"],
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
                "HATA: pasif ithal sozlesmesi bozuldu (aktif ya da kapidan gecen satir var)"
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
