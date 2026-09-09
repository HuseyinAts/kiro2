#!/usr/bin/env python
"""kitapcik_cikar.py ciktisini (JSON) question_bank'a PASIF olarak ithal eder.

NEDEN PASIF (9 Eyl 2026)
------------------------
Kitapcigin ilk sayfasi: "Bu testlerin her hakki saklidir. ... Merkezimizin
yazili izni olmadan ... kullanilmasi yasaktir." Ithal edilen her satir
`is_active=false`, `is_public=false`, `review_status='pending'`; sinav
motoru ve kapi (`mv_safe_for_beta`) pasif soruyu servis etmez.
Aktiflestirme ayri ve bilincli bir adim (`--aktiflestir`, hukuki onaydan
sonra); bu script onu varsayilan olarak YAPMAZ.

Kurallar
--------
- id = uuid5(NAMESPACE_OID, soru_hash); soru_hash = pilot_500p formulu
  (md5(lower(nfc(question_text))|A|B|C|D|E)) -- uq_qb_soru_hash_active ile uyumlu.
- Ayni id varsa satir ATLANIR (idempotent; tekrar kosum guvenli).
- Gorsel/formul/alti cizili bayrakli sorularda question_image_url =
  /static/crops/<onek>/<dosya> (kitapcik_cikar --kirp ciktisi); metin de
  saklanir (arama/embedding icin).
- primary_topic_id = dersin kok konusu (konu atamasi ayri is; 0009 sozlesmesi
  geregi ders koku ile subject_area uyusur).
- Blueprint sapmasi (JSON ozeti != beklenen) ya da anahtarsiz soru varsa
  ithal HIC BASLAMAZ.

KULLANIM
--------
    python backend/scripts/osym/kitapcik_ithal.py data/osym/tyt_2025.json --dsn postgresql://... [--yaz]
    (--yaz verilmezse yalnizca plan basilir)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import unicodedata
import uuid
from pathlib import Path
from typing import Any

import psycopg

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)

DERS_KOKU = {
    "TURKCE": "TUR",
    "TARIH": "TAR",
    "COGRAFYA": "COG",
    "FELSEFE": "SOS",
    "DIN": "SOS",
    "SOSYAL": "SOS",
    "MATEMATIK": "MAT",
    "GEOMETRI": "GEO",
    "FIZIK": "FIZ",
    "KIMYA": "KIM",
    "BIYOLOJI": "BIO",
    "EDEBIYAT": "EDB",
    "FEN": "FEN",
}
TELIF_NOTU = (
    "OSYM: 'Bu testlerin her hakki saklidir; yazili izin olmadan kullanilmasi yasaktir.' "
    "Aktiflestirme hukuki onay bekler."
)


def _nfc(t: str) -> str:
    return unicodedata.normalize("NFC", t).strip()


def soru_hash(q: dict[str, Any]) -> str:
    """scripts/pipeline/pilot_500p.py::_hash_question ile birebir."""
    o = q["options"]
    payload = "|".join(
        [
            _nfc(q["question_text"]).lower(),
            _nfc(o["A"]),
            _nfc(o["B"]),
            _nfc(o["C"]),
            _nfc(o["D"]),
            _nfc(o.get("E") or ""),
        ]
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


def kayit_uret(
    q: dict[str, Any], meta: dict[str, Any], kaynak_adi: str, onek: str
) -> dict[str, Any]:
    h = soru_hash(q)
    n, u, ort = _kelime_istatistik(q["question_text"])
    gorsel = q.get("gorsel_dosya")
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_OID, h)),
        "soru_hash": h,
        "kok": DERS_KOKU[q["subject_area"]],
        "question_text": q["question_text"],
        "options": q["options"],
        "correct_answer": q["correct_answer"],
        "question_image_url": f"/static/crops/{onek}/{gorsel}" if gorsel else None,
        "exam_type": meta["sinav"],
        "subject_area": q["subject_area"],
        "osym_year": meta["yil"],
        "source_book": kaynak_adi,
        "source_page": q["sayfa"],
        "word_count": n,
        "unique_word_count": u,
        "average_word_length": ort,
        "pipeline_metadata": {
            "kaynak": "osym_kitapcik",
            "dosya": meta["dosya"],
            "test": q["test"],
            "soru_no": q["no"],
            "bayraklar": q["bayraklar"],
            "telif": TELIF_NOTU,
            "ithal_araci": "scripts/osym/kitapcik_ithal.py",
        },
    }


_QB = """
INSERT INTO question_bank (id, soru_hash, primary_topic_id, is_active, is_public, created_by,
    reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor)
VALUES (%(id)s, %(soru_hash)s, %(kok_id)s, FALSE, FALSE, NULL, NULL, now(), now(), FALSE, 'pending', FALSE)
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
VALUES (%(id)s, 2, 'comprehension', %(exam_type)s, %(subject_area)s, 12, TRUE, %(osym_year)s, %(source_book)s,
    %(source_page)s, %(pipeline_metadata)s::json, 0.5, %(word_count)s, %(unique_word_count)s,
    %(average_word_length)s, 50.0, 'PENDING')
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


def ithal(json_yolu: Path, dsn: str, kaynak_adi: str, onek: str, yaz: bool) -> int:
    veri = json.loads(json_yolu.read_text(encoding="utf-8"))
    meta, oz, sorular = veri["meta"], veri["ozet"], veri["sorular"]
    if oz["anahtari_olan"] != oz["toplam_soru"] or oz["bes_sikli"] != oz["toplam_soru"]:
        print(
            "DURDU: JSON ozeti tam degil (anahtar/sik eksigi) -- once kitapcik_cikar sapmasini coz"
        )
        return 2
    kayitlar = [kayit_uret(q, meta, kaynak_adi, onek) for q in sorular]
    print(
        f"{len(kayitlar)} soru; pasif ithal plani (kaynak={kaynak_adi}, yil={meta['yil']}, sinav={meta['sinav']})"
    )
    with psycopg.connect(dsn) as conn:
        kokler: dict[str, str] = dict(
            conn.execute(
                "SELECT code, id FROM topic_hierarchy WHERE parent_id IS NULL AND subject_area IS NULL AND is_active"
            ).fetchall()
        )
        eksik = {k["kok"] for k in kayitlar} - set(kokler)
        if eksik:
            print(f"DURDU: kok konu yok: {eksik}")
            return 2
        var = {
            r[0]
            for r in conn.execute(
                "SELECT id FROM question_bank WHERE id = ANY(%s)",
                ([k["id"] for k in kayitlar],),
            ).fetchall()
        }
        yeni = [k for k in kayitlar if k["id"] not in var]
        print(f"zaten var: {len(var)}, yazilacak: {len(yeni)}")
        from collections import Counter

        print("ders dagilimi:", dict(Counter(k["subject_area"] for k in yeni)))
        print("gorselli:", sum(1 for k in yeni if k["question_image_url"]))
        if not yaz:
            print("(--yaz verilmedi; hicbir sey yazilmadi)")
            return 0
        with conn.transaction():
            for k in yeni:
                o = k["options"]
                conn.execute(_QB, {**k, "kok_id": kokler[k["kok"]]})
                conn.execute(
                    _QC,
                    {
                        "id": k["id"],
                        "question_text": k["question_text"],
                        "a": o["A"],
                        "b": o["B"],
                        "c": o["C"],
                        "d": o["D"],
                        "e": o.get("E") or None,
                        "correct_answer": k["correct_answer"],
                        "question_image_url": k["question_image_url"],
                    },
                )
                conn.execute(
                    _QM,
                    {
                        **k,
                        "pipeline_metadata": json.dumps(
                            k["pipeline_metadata"], ensure_ascii=False
                        ),
                    },
                )
                conn.execute(_QS, {"id": k["id"]})
        n = conn.execute(
            "SELECT count(*) FROM question_bank b JOIN question_metadata m ON m.id=b.id WHERE m.source_book=%s AND b.is_active IS FALSE",
            (kaynak_adi,),
        ).fetchone()[0]
        print(f"YAZILDI: {len(yeni)} yeni satir; DB'de {kaynak_adi} pasif toplam {n}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("json")
    p.add_argument("--dsn", default=os.environ.get("KIRO2_DSN", VARSAYILAN_DSN))
    p.add_argument("--kaynak", help="source_book (varsayilan: OSYM <yil> <sinav>)")
    p.add_argument("--onek", help="crops alt dizini (varsayilan: OSYM_<yil>_<sinav>)")
    p.add_argument(
        "--yaz", action="store_true", help="gercekten yaz (varsayilan: plan)"
    )
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    meta = json.loads(Path(args.json).read_text(encoding="utf-8"))["meta"]
    kaynak = args.kaynak or f"OSYM {meta['yil']} {meta['sinav']}"
    onek = args.onek or f"OSYM_{meta['yil']}_{meta['sinav']}"
    return ithal(Path(args.json), args.dsn, kaynak, onek, args.yaz)


if __name__ == "__main__":
    raise SystemExit(main())
