#!/usr/bin/env python
"""Aktif Ogrenme TYT Dilbilgisi Soru Bankasi 2025 -- PASIF ithal.

NEDEN PASIF VE is_ai_generated=TRUE
-----------------------------------
0013/0015/0017/0021/0022/geo345 ile ayni gerekce: metin bir okuma
hattindan geldi, kaynak zkitap goruntuleyici EKRAN GORUNTUSUDUR. Her satir:

    is_active = FALSE, is_public = FALSE,
    is_ai_generated = TRUE, review_status = 'PENDING'

Servis kapisi (`v_safe_for_beta`) `(is_ai_generated = false OR
review_status = 'APPROVED')` ister; iki alan da bu satirlari kapinin
DISINDA tutar. Ithal tek basina hicbir soruyu ogrenciye ulastirmaz;
aktiflestirme AYRI karardir.

VERI NEREDEN GELIYOR
--------------------
`veriseti/zkitap/cikti/aktif_dilbilgisi_sorular.json` (537 soru).
Uretim yontemi ve tum olcumler: `veriseti/zkitap/cikti/DILBILGISI_YONTEM.md`.

CEVAP KAYNAGI: KITABIN BASILI CEVAP SERIDI
------------------------------------------
Sorular tekrar cozulerek dogrulanmaz (urun karari). 553 cevabin 553'u
sayfa altindaki basili cevap seridinden okundu. Iki BAGIMSIZ okuma
(farkli kirpim geometrisi ve olcek) arasinda FARK = 0; her testin soru
numaralari 1..N kesintisiz (44 test, 0 kusur). `explanation` bu yuzden NULL.

KONU BAGLAMA: SAYFANIN KENDI BASLIK BANDINDAN, UNITE DUZEYI
-----------------------------------------------------------
0017/0021/0022 ilkesi. 44 testin ilk sayfasindaki turuncu bant okundu;
17 ad cikti ve bu 17 ad sayfa sirasinda tam 17 KOSU olusturuyor.
0025_dilbilgisi_konu_agaci bu 17'yi TUR-D1..TUR-D16 + TUR-OSYM-GENEL
olarak kurar. Kitapta unite alti konu etiketi YOKTUR; "Konu Testi N" /
"OSYM Sorulari" konu degil TEST TURUDUR ve soru duzeyinde
`pipeline_metadata.test_turu` olarak tasinir. Var olmayan bir L3 katmani
uydurulmadi; `konu_eslesme_duzeyi='unite'` ile ISARETLENIR.

BU KITAPTA SORU GORSELI YOK -- VE GEREKMIYOR
--------------------------------------------
Dilbilgisi kitabi; 90 soru sayfasinin hicbirinde sekil/grafik soru
gorulmedi (90 sayfanin 90'i goruntu olarak okundu). `sekil_var` veri
setinde 537/537 FALSE, dolayisiyla `gorsel_yok_sekilli` bayragi HIC
uretilmez ve `question_image_url` NULL yazilir.

MEVCUT 17 SATIR ATLANIR
-----------------------
DB'de bu kitaptan 17 satir zaten var (eski gemini hatti,
kiro2_batch_v4.14e). Urun karari: DOKUNULMAZ, yeni ithal onlari ATLAR.
15'i bu kanalda (Konu Testi/OSYM) ve veri setinden ONCEDEN cikarildi
(`aktif_dilbilgisi_dislanan.json`); 2'si Kavrama/Uygulama sayfasinda,
yani bu ithalin kapsaminda degil.

OLCUM NOTU (kayda geciyor, duzeltilmedi): eslesen 15 satirin 13'unde
cevap basili seritle ayni, 2'sinde FARKLI -- s107 q6 (eski C, serit E)
ve s33 q4 (eski A, serit B). Her iki serit 5x buyutmede ucuncu kez
okundu. Eski satirlarin cevabi yanlis; duzeltmek bu PR'in konusu degil.

ADLANDIRMA
----------
0026_dilbilgisi_kaynak_adi mevcut 17 satirin `source_book` yazimini ASCII
sozlesmesine cevirir (U+0131 -> i). Bu script kanonik ASCII adi
KAYNAK_KAYITLARI'ndan okur; iki yazim yan yana kalirsa her koruma delinir.

Kurallar
--------
- id = uuid5(NAMESPACE_OID, soru_hash); soru_hash = pilot_500p formulu
  (scripts/kitap/metin_olcum.py, tek kaynak).
- Ayni id varsa satir ATLANIR (idempotent; tekrar kosum guvenli).
- primary_topic_id: 0025'in kurdugu TUR-D<n> / TUR-OSYM-GENEL; eksikse
  ithal DURUR -- kok dugume sessizce dusurmek YOK.

KULLANIM
--------
    python backend/scripts/kitap/dilbilgisi_ithal.py --dsn postgresql://... [--yaz]
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
    kelime_istatistik,
    morfoloji_karmasikligi,
    okunabilirlik,
    sik_bayraklari,
    soru_hash,
)

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
VARSAYILAN_VERI = "veriseti/zkitap/cikti/aktif_dilbilgisi_sorular.json"
KAYNAK_ADI = "Aktif Ogrenme Tyt Dilbilgisi Soru Bankasi 2025"
ONEK = KAYNAK_KAYITLARI[KAYNAK_ADI]["onek"]
TUR_KOK_KODU = "TUR"
# 0025 kodlari: TUR-D1..TUR-D16 ve TUR-OSYM-GENEL. Desen TUR kokunu,
# TUR.ANL/TUR.DIL/TUR.PAR/TUR.YAZ (nokta ayracli) ve TYT-TR-* dugumlerini
# KAPSAMAZ.
KOD_ONEKI = "TUR-D"
OSYM_KODU = "TUR-OSYM-GENEL"
SINAV_TURU = "TYT"
DERS_ALANI = "TURKCE"
# Olculdu (16 Eyl 2026): exam_type='TYT' satirlarinin 6396'si grade_level=12,
# 1021'i 11. Bu kitabin kendi 17 eski satirinin 16'si da 12.
SINIF_DUZEYI = 12
TELIF_NOTU = (
    "Aktif Ogrenme Yayinlari. Ticari soru bankasi; icerik hak sahibinin izni "
    "olmadan servis edilemez. Ithal PASIF, aktiflestirme ayri karar."
)
URETIM_NOTU = (
    "Goruntuden okuma hatti: sayfa siniflandirmasi iki bagimsiz kanalla "
    "(bant renk imzasi / cevap seridi varligi) sifir uyusmazlikla 90 soru "
    "sayfasi; cevap anahtari CIFT OKUMA (farkli geometri+olcek) fark=0; "
    "test ici numara surekliligi 44 testte 0 kusur; soru segmentasyonu "
    "imlec sayisi = anahtar soru sayisi, 90/90 sayfa 0 kusur; yapisal "
    "dogrulayici K1-K11 553 soruda 1 bulgu (o da kitabin kendi dizgi "
    "kusuru, ilgili soru ithal disi). Cevaplar kitabin basili cevap "
    "seridinden okundu; soru cozulmedi. Konu, sayfanin kendi baslik "
    "bandindan. Detay: veriseti/zkitap/cikti/DILBILGISI_YONTEM.md"
)
ANAHTAR_DOGRULAMASI = (
    "anahtar_seridi_cift_okuma_fark_0__numara_surekliligi_44_test_0_kusur"
)


def _bayraklar(r: dict[str, Any], sec: dict[str, str]) -> list[str]:
    """Ortak sik bayraklari + bu kitaba ozgu isaretler.

    `gorsel_yok_sekilli` BU KITAPTA URETILMEZ: sekilli soru yok (bkz. modul
    basligi). Bayragi "her ihtimale karsi" eklemek olcum disi bir iddia
    olurdu; bunun yerine sekil_var gercekten TRUE gelirse ISARETLENIR ve
    testte bu satirin hic olmadigi kilitlenir.
    """
    # Acik anotasyon: kok pyproject.toml `warn_return_any = true` diyor ve
    # pre-commit mypy'si metin_olcum'u ayri bir kok altinda cozdugu icin
    # donus tipini Any goruyordu.
    b: list[str] = sik_bayraklari(sec)
    if r.get("sekil_var"):
        b.append("gorsel_yok_sekilli")
    if not r.get("sayfada_bant_var"):
        b.append("konu_komsudan")
    if r.get("kaynak_kusuru"):
        b.append("kaynak_dizgi_kusuru")
    return b


def kayit_uret(r: dict[str, Any]) -> dict[str, Any]:
    sec = {h: r[h.lower()] for h in "ABCDE"}
    h = soru_hash(r["question_text"], sec)
    n, u, ort = kelime_istatistik(r["question_text"])
    bloom, bloom_ad, bloom_kaynak = bloom_belirle(r["question_text"], sec)
    cikmis = bool(r.get("cikmis"))
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "konu_kodu": r["konu_kodu"],
        "question_text": r["question_text"],
        "secenekler": sec,
        "correct_answer": r["correct_answer"],
        # Bu kitapta soru kirpimi yok ve sekilli soru da yok -- bkz. baslik.
        "question_image_url": None,
        # Bu kitapta dosya numarasi ile basili sayfa numarasi AYNI
        # (s118 sayfa rozeti "118" ile dogrulandi).
        "source_page": int(r["sayfa"]),
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "readability_score": okunabilirlik(r["question_text"], sec),
        "morphology_complexity": morfoloji_karmasikligi(r["question_text"]),
        "bloom_level": bloom,
        "bloom_category": bloom_ad,
        # Kitap "(OSYM'den)" diyor ama YIL yazmiyor; yil uydurulmaz.
        "osym_year": None,
        "osym_format_compliant": cikmis,
        "pipeline_metadata": {
            "kaynak": ONEK.lower(),
            "konu_kodu": r["konu_kodu"],
            "konu_bandi": r.get("konu_bandi"),
            "konu_eslesme_duzeyi": "unite",
            "konu_kaynagi": "sayfa_baslik_bandi",
            "sayfa_dosya_no": int(r["sayfa"]),
            "basili_sayfa": r.get("basili_sayfa"),
            "sutun": r.get("sutun"),
            "pozisyon": r.get("pozisyon"),
            "soru_no": r.get("soru_no"),
            "test_turu": r.get("test_turu"),
            "test_no": r.get("test_no"),
            "basili_test_rozeti": r.get("basili_test_rozeti"),
            "bayraklar": _bayraklar(r, sec),
            "cevap_kaynagi": r.get("cevap_kaynagi") or "cevap_seridi",
            "anahtar_dogrulamasi": ANAHTAR_DOGRULAMASI,
            "cikmis_soru": cikmis,
            "sinav_yili": None,
            "sekil_var": bool(r.get("sekil_var")),
            "gorsel_kaynagi": "yok_sekilli_soru_bulunmadi",
            "sutun_gorseli": None,
            "numaralanmis_sozcukler": r.get("numaralar"),
            "alti_cizili": r.get("alti_cizili"),
            "kaynak_kusuru": r.get("kaynak_kusuru"),
            "metin_kaynagi": "sayfa_granulerliginde_gorsel_okuma",
            "bloom_kaynagi": bloom_kaynak,
            "morfoloji_kaynagi": "heuristik_zemberek_yok_sabit",
            "okunabilirlik_kaynagi": "atesman_turkish_readability_service",
            "cozum_dogrulamasi": "yapilmadi_urun_karari",
            "telif": TELIF_NOTU,
            "uretim": URETIM_NOTU,
            "ithal_araci": "scripts/kitap/dilbilgisi_ithal.py",
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
VALUES (%(id)s, %(bloom_level)s, %(bloom_category)s, 'TYT', 'TURKCE', %(grade_level)s,
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
        kod = k["konu_kodu"] or ""
        if not (kod.startswith(KOD_ONEKI) or kod == OSYM_KODU):
            hata.append(
                f"{k['id']}: konu kodu {kod!r} {KOD_ONEKI}* ya da {OSYM_KODU} degil"
            )
        if k["id"] in gorulen:
            hata.append(f"{k['id']}: veri setinde ayni hash iki kez")
        gorulen.add(k["id"])
    return hata


def _konu_id_ata(
    conn: psycopg.Connection, kayitlar: list[dict[str, Any]]
) -> str | None:
    """Her kayda konu_id yazar; basarisizsa DURDURMA gerekcesini dondurur.

    Kok dugume sessizce dusurmek YOK: 0025 kosmamissa ithal hic baslamaz.
    """
    kok = conn.execute(
        "SELECT id FROM topic_hierarchy WHERE code = %s AND parent_id IS NULL",
        (TUR_KOK_KODU,),
    ).fetchone()
    if not kok:
        return f"{TUR_KOK_KODU} kok konusu yok"
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
            "0025_dilbilgisi_konu_agaci kosmadi mi? Kok dugume dusurup "
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
        print(f"  {adet:5d}  {kod:16s}  {band}")
    print(
        "test turu         :",
        dict(Counter(k["pipeline_metadata"]["test_turu"] for k in kayitlar)),
    )
    bayrak: Counter[str] = Counter()
    for k in kayitlar:
        bayrak.update(k["pipeline_metadata"]["bayraklar"])
    print("bayraklar         :", dict(bayrak) or "(yok)")
    print("cikmis (OSYM)     :", sum(1 for k in kayitlar if k["osym_format_compliant"]))
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
        "on kontrol: 5 sik + dolu anahtar + dolu metin + TUR-D/TUR-OSYM konu "
        "kodu + benzersiz hash -- TEMIZ"
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

        satir = conn.execute(
            """SELECT count(*),
                      count(*) FILTER (WHERE b.is_active),
                      count(*) FILTER (WHERE EXISTS (
                          SELECT 1 FROM v_safe_for_beta v WHERE v.id = b.id))
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s AND m.pipeline_metadata->>'ithal_araci' = %s""",
            (KAYNAK_ADI, "scripts/kitap/dilbilgisi_ithal.py"),
        ).fetchone()
        if satir is None:  # pragma: no cover -- count(*) her zaman satir dondurur
            raise RuntimeError("dogrulama sorgusu satir dondurmedi")
        n, aktif, kapida = satir
        print(f"YAZILDI: {len(yeni)} yeni satir")
        print(
            f"DB'de bu ithalin satirlari: toplam {n}, is_active {aktif}, "
            f"kapidan gecen {kapida}"
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
