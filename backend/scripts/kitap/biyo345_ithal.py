#!/usr/bin/env python
"""345 2025 AYT Biyoloji Soru Bankasi -- OCR ciktisini PASIF ithal eder.

NEDEN PASIF VE is_ai_generated=TRUE
-----------------------------------
0013/0015/0017'deki ithallerle ayni gerekce: metin bir OCR/VLM hattindan
geldi. Kitabin kaynagi zkitap goruntuleyici EKRAN GORUNTUSUDUR; PDF yok,
metin katmani yok. Her satir su sekilde yazilir:

    is_active = FALSE, is_public = FALSE,
    is_ai_generated = TRUE, review_status = 'PENDING'

Servis kapisi (`v_safe_for_beta`) `(is_ai_generated = false OR review_status =
'APPROVED')` ister; iki alan da bu satirlari kapinin DISINDA tutar. Ithal tek
basina hicbir soruyu ogrenciye ulastirmaz; aktiflestirme ayri karardir.

CEVAP KAYNAGI: YALNIZ KITABIN BASILI ANAHTARI
---------------------------------------------
Sorular tekrar cozulerek dogrulanmaz (urun karari). Anahtar her soru
sayfasinin altinda tek satir halinde basili (y 1792-1803, tum kitapta sabit).
Iki bagimsiz okuma 307 sayfanin 294'unde birebir uyustu; 13 uyusmazligin
tamami B/E ve C/D karismasiydi ve 10x hakem kirpimiyla cozuldu (13/13 ikinci
okuma lehine). `explanation` bu yuzden NULL birakilir.

ANAHTARIN SIFIR SERBESTLIK DERECELI DOGRULAMASI
-----------------------------------------------
Okuyuculara beklenen girdi sayisi hic soylenmedi (capa bastirma). Birlestirme
sonrasi 1317 girdinin tamami NUMARA SUREKLILIGI denetiminden gecti: her girdi
bir oncekinden +1 ya da yeni testin basi olarak 1. SIFIR kirilma. Bu denetimin
serbestlik derecesi yok -- uydurulmus tek bir numara zinciri kirardi.

ESLEME KONUMSALDIR: seritteki i. girdi <-> sutundaki i. soru. Bu esleme
BAGIMSIZ dogrulandi: soru metinleri sutun granulerliginde ayri bir turda
okundu ve her sorunun BASILI NUMARASI kaydedildi; 600 sutunun 599'unda
numara dizisi anahtarla birebir ayni cikti. Tek sapma s0183 sag: sayfada
"67." basili, anahtar ve test sirasi "2" diyor (onceki sutun 1'de bitiyor).
YAYINEVI DIZGI HATASI; konumsal esleme etkilenmez, sapma
pipeline_metadata.anahtar_numara_sapmasi ile ISARETLENIR.

KONU BAGLAMA: UNITE DUZEYI
--------------------------
0021 migration'i kitabin 16 bolumunu BIO-U1..BIO-U16 olarak kurar. Soru ->
bolum eslemesi sayfa araligindan gelir (bolum ayrac sayfalari kitaptan
okundu). Kitapta UNITE ALTI konu etiketi YOKTUR; test basliklari
("3. TEST - KAZANIM ODAKLI SORULAR", "KARMA SORULAR 2", "OSYM TADINDA
SORULAR 1", "ORIJINAL SORULAR") konu degil TEST TURUDUR ve soru duzeyinde
pipeline_metadata.test_basligi olarak tasinir. Var olmayan bir L3 katmani
uydurulmadi; `konu_eslesme_duzeyi='unite'` ile ACIKCA isaretlenir.

GORSELLER
---------
question_image_url TAM SORU KIRPIMIDIR (metin + sekil birlikte); kirpim
kutusu pipeline_metadata.kirpim_kutusu'nda saklanir ve gorseller her ortamda
kaynaktan yeniden uretilebilir (scripts/kitap/biyo345_kirp.py).
Varlik duzeyinde (sekil sekil) ayristirma YAPILMADI;
`gorsel_kaynagi='tam_soru_kirpimi'` ile isaretlenir.

BILINEN SINIR: SIKLARI GORSEL OLAN SORULAR
------------------------------------------
Bazi sorularin siklari metin degil GRAFIK/TABLO/RESIMDIR. Bu sorularda
a..e alanlari okuyucunun TARIFIDIR, kitabin bastigi metin degil. Bir soruda
(s0362 sag #6) iki tarif ayni cikti ve `sik_tekrar` bayragiyla isaretlendi.
Bu sorularin dogru gosterimi KIRPIM GORSELIDIR; metin alanlari arama ve
hash icindir.

OSYM CIKMIS SORULARI
--------------------
Kitapta 71 "OSYM kosesi / CIKMIS SORU" kutusu var; kirmizi cerceveleri bagli
bilesen olarak olculdu ve yil-sinav etiketleri ayri bir turda okundu
(71/71 dolu; 2015 YGS bir tane, kalan 70'i AYT 2018-2025).
osym_year / osym_format_compliant YALNIZCA bu sorularda doldurulur --
yayinevinin kendi yazdigi sorulara OSYM damgasi vurulmaz.

BAGIMSIZ CAPRAZ DOGRULAMA (BEDAVA GELEN)
----------------------------------------
1317 hash'in 2'si canli DB'de ZATEN VARDI ve ikisi de `source_book =
'OSYM 2025 AYT'` etiketli. Ikisi de bu hattin OSYM-kutusu dedektorunun
bagimsiz olarak isaretledigi sorular. Yani hash formulu, metin cikarimi ve
OSYM tespiti UC AYRI KANALDAN birbirini dogruluyor.

VERI NEREDEN GELIYOR
--------------------
`veriseti/zkitap/cikti/biyo345_sorular.json` (git disinda; .gitignore
`veriseti/`). Uretim yontemi ve tum olcumler ayni klasordeki
BIYO345_YONTEM.md'de.

Kurallar
--------
- id = uuid5(NAMESPACE_OID, soru_hash); soru_hash = pilot_500p formulu
  (md5(lower(nfc(question_text))|A|B|C|D|E)) -- uq_qb_soru_hash_active uyumlu.
- Ayni id varsa satir ATLANIR (idempotent; tekrar kosum guvenli).
- primary_topic_id: 0021'in kurdugu BIO-U<n>; bulunamazsa BIO koku.
- question_image_url = /static/crops/BIYO345/<id>.png

KULLANIM
--------
    python backend/scripts/kitap/biyo345_ithal.py --dsn postgresql://... [--yaz]
    (--yaz verilmezse yalnizca plan basilir)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kaynak_sozlesmesi import KAYNAK_KAYITLARI, ayristir, yabanci_yaz
from scripts.kitap.metin_olcum import (
    bloom_belirle,
    morfoloji_karmasikligi,
    okunabilirlik,
    soru_hash,
)
from scripts.kitap.metin_olcum import (
    kelime_istatistik as _kelime_istatistik,
)

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
VARSAYILAN_VERI = "veriseti/zkitap/cikti/biyo345_sorular.json"
# Kanonik ad tek yerde durur (scripts/kitap/kaynak_sozlesmesi.py).
KAYNAK_ADI = "345 2025 AYT Biyoloji Soru Bankasi"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
BIO_KOK_KODU = "BIO"
# 0021 kodlari: BIO-U1 ... BIO-U16. LIKE deseni kokun kendisini ve
# BIO-OSYM-GENEL'i KAPSAMAZ.
KOD_ONEKI = "BIO-U"
SINAV_TURU = "AYT"
DERS_ALANI = "BIYOLOJI"
SINIF_DUZEYI = 12  # mevcut AYT satirlarinin ev sozlesmesi
TELIF_NOTU = (
    "UcDortBes Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "OCR/VLM hatti: anahtar icin iki bagimsiz okuma + uyusmazlikta hakem "
    "turu + numara surekliligi denetimi (1317 girdide 0 kirilma); metin "
    "sutun granulerliginde okundu ve numara dizisi 599/600 sutunda "
    "anahtarla birebir uyustu. Tek cevap kaynagi kitabin basili anahtaridir; "
    "soru tekrar cozulmedi. Detay: veriseti/zkitap/cikti/BIYO345_YONTEM.md"
)

# algorithms/irt_morfoloji_service.complexity_weights ile ayni agirliklar
W_EK, W_TURETIM, W_BIRLESIK = 0.15, 0.20, 0.25


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    b: list[str] = []
    if any(not (sec[h] or "").strip() for h in "ABCDE"):
        b.append("sik_bos")
    if len({(sec[h] or "").strip().lower() for h in "ABCDE"}) < 5:
        b.append("sik_tekrar")
    if r.get("basili_no") is not None:
        b.append("anahtar_numara_sapmasi")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r[h.lower()] for h in "ABCDE"}
    h = soru_hash(r["question_text"], sec)
    n, u, ort = _kelime_istatistik(r["question_text"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["question_text"], sec)
    resmi = bool(r.get("osym_yil"))
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": f"BIO-U{r['bolum_no']}",
        "question_text": r["question_text"],
        "secenekler": sec,
        "correct_answer": r["correct_answer"],
        "question_image_url": f"/static/crops/{ONEK}/{r['id']}.png",
        # DIKKAT: source_page DOSYA numarasidir, kitabin BASILI sayfa
        # numarasi degil (olculdu: sayfa_0020 -> basili 19). Kitap icine
        # referans verirken bu fark hatirlanmali.
        "source_page": int(r["sayfa"]),
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["question_text"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["question_text"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        "osym_year": r.get("osym_yil"),
        "osym_format_compliant": resmi,
        "pipeline_metadata": {
            "kaynak": "345_2025_ayt_biyoloji_soru_bankasi",
            "bolum_no": r["bolum_no"],
            "bolum_adi": r["bolum_adi"],
            "test_basligi": r.get("test_basligi") or None,
            "konu_eslesme_duzeyi": "unite",
            "sayfa_dosya_no": r["sayfa"],
            "sutun": r["sutun"],
            "soru_no": r["soru_no"],
            "basili_no": r.get("basili_no"),
            "anahtar_numara_sapmasi": r.get("basili_no") is not None,
            "bayraklar": _bayraklar(r, {h: r[h.lower()] for h in "ABCDE"}),
            "cevap_kaynagi": "kitabin_basili_anahtari",
            "cevap_eslemesi": "konumsal_sutun_sirasi",
            "anahtar_dogrulamasi": "numara_surekliligi_1317_girdi_0_kirilma",
            "cikmis_soru": bool(r.get("osym_cikmis")),
            "sinav_kaynagi": r.get("osym_sinav"),
            "sinav_yili": r.get("osym_yil"),
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
            "ithal_araci": "scripts/kitap/biyo345_ithal.py",
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
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'AYT', 'BIYOLOJI', %(grade_level)s,
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
        "bolum dagilimi:",
        dict(
            sorted(
                Counter(k["pipeline_metadata"]["bolum_no"] for k in kayitlar).items()
            )
        ),
    )
    print(
        "sekil iceren      :",
        sum(1 for k in kayitlar if k["pipeline_metadata"]["sekil_var"]),
    )
    print(
        "sik_bos bayrakli  :",
        sum(1 for k in kayitlar if "sik_bos" in k["pipeline_metadata"]["bayraklar"]),
    )
    print(
        "sik_tekrar bayrakli:",
        sum(1 for k in kayitlar if "sik_tekrar" in k["pipeline_metadata"]["bayraklar"]),
    )
    print("cikmis (yil dolu) :", sum(1 for k in kayitlar if k["osym_year"]))
    print(
        "anahtar no sapmasi:",
        sum(1 for k in kayitlar if k["pipeline_metadata"]["anahtar_numara_sapmasi"]),
    )
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
    veri_kutu = {k["id"]: r["kutu"] for k, r in zip(kayitlar, veri, strict=True)}
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
            (BIO_KOK_KODU,),
        ).fetchone()
        if not kok:
            print(f"DURDU: {BIO_KOK_KODU} kok konusu yok")
            return 2
        konular: dict[str, str] = dict(
            conn.execute(
                "SELECT code, id FROM topic_hierarchy WHERE code LIKE %s",
                (KOD_ONEKI + "%",),
            ).fetchall()
        )
        eksik_konu = {k["konu_kodu"] for k in kayitlar} - set(konular)
        if eksik_konu:
            print(
                f"UYARI: {len(eksik_konu)} unite kodu yok (0021 migration kosmadi mi?); "
                f"bunlar BIO koku ile yazilacak. Ornek: {sorted(eksik_konu)[:3]}"
            )
        for k in kayitlar:
            k["konu_id"] = konular.get(k["konu_kodu"], kok[0])

        # DIKKAT: soru_hash metin+5 sik uzerinden hesaplandigi icin ayni soru
        # baska bir kaynakta da varsa ID AYNI olur. Bu kitapta 2 soru boyle
        # (ikisi de "OSYM 2025 AYT" ithalinde zaten yazilmis cikmis sorular).
        # Var olan satirlar KAYNAK KITABA GORE ayrilir; --meta-guncelle YALNIZ
        # bu kitabin satirlarina dokunur.
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

        satir = conn.execute(
            """SELECT count(*),
                      count(*) FILTER (WHERE b.is_active),
                      count(*) FILTER (WHERE EXISTS (
                          SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id))
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s""",
            (KAYNAK_ADI,),
        ).fetchone()
        if satir is None:  # pragma: no cover  # count(*) hep satir dondurur
            raise RuntimeError("ozet sorgusu satir dondurmedi")
        n, aktif, kapida = satir
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
