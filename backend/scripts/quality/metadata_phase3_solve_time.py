#!/usr/bin/env python3
"""
Phase 3: estimated_solve_time_seconds + osym_section + ocr_confidence_avg.

Base times (YKS empirical norms):
  TYT: 73 sec/q average (165 min / 135 q × 60)
  AYT: 135 sec/q (180 min / 80 q × 60)

Subject modifiers:
  Matematik/Geometri: +20%
  Türkçe/Edebiyat:   +30% (paragraph reading)
  Fizik/Kimya/Bio:   +15%
  Tarih/Coğrafya/Sosyal: -10%

Difficulty modifier (irt_b):
  b ≤ -2 (very easy):  ×0.6
  -2 < b ≤ -0.5:       ×0.8
  -0.5 < b ≤ 0.5:      ×1.0
  0.5 < b ≤ 2:         ×1.3
  b > 2:               ×1.6

Bloom level:
  1-2 (bilgi/kavrama): ×0.9
  3 (uygulama):        ×1.0
  4 (analiz):          ×1.2
  5-6 (sentez/değer):  ×1.4

Bounded: 20-300 seconds.

osym_section: derived from exam_type + subject_area
ocr_confidence_avg: from pipeline_metadata.extraction_confidence if available
"""

import json
import os
import sys

import psycopg2
from psycopg2.extras import execute_values

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DSN = os.environ.get("DATABASE_URL") or (__import__("sys").exit("ERROR: DATABASE_URL env required (no hardcoded fallback)"))

BASE_TIMES = {"TYT": 73, "AYT": 135, "YDT": 90}
SUBJECT_MOD = {
    "MATEMATIK": 1.20,
    "GEOMETRI": 1.20,
    "TURKCE": 1.30,
    "EDEBIYAT": 1.30,
    "FIZIK": 1.15,
    "KIMYA": 1.15,
    "BIYOLOJI": 1.15,
    "TARIH": 0.90,
    "COGRAFYA": 0.90,
    "SOSYAL": 0.90,
    "FELSEFE": 1.10,
    "DIN": 0.85,
    "GENEL": 1.00,
}


def difficulty_mod(b):
    if b is None:
        return 1.0
    if b <= -2:
        return 0.6
    if b <= -0.5:
        return 0.8
    if b <= 0.5:
        return 1.0
    if b <= 2:
        return 1.3
    return 1.6


def bloom_mod(level):
    if level is None:
        return 1.0
    if level <= 2:
        return 0.9
    if level == 3:
        return 1.0
    if level == 4:
        return 1.2
    return 1.4


def osym_section(exam_type, subject):
    e = (exam_type or "").upper()
    s = (subject or "").upper()
    if e == "TYT":
        if s in ("MATEMATIK", "GEOMETRI"):
            return "tyt_matematik"
        if s in ("TURKCE", "EDEBIYAT"):
            return "tyt_turkce"
        if s in ("FIZIK", "KIMYA", "BIYOLOJI", "FEN"):
            return "tyt_fen"
        if s in ("TARIH", "COGRAFYA", "FELSEFE", "DIN", "SOSYAL"):
            return "tyt_sosyal"
        return "tyt_diger"
    if e == "AYT":
        if s in ("MATEMATIK", "GEOMETRI"):
            return "ayt_say"  # sayısal
        if s in ("FIZIK", "KIMYA", "BIYOLOJI"):
            return "ayt_say"
        if s in ("EDEBIYAT", "TURKCE"):
            return "ayt_ea"  # eşit ağırlık
        if s in ("TARIH", "COGRAFYA"):
            return "ayt_ea"
        if s in ("SOSYAL", "FELSEFE", "DIN"):
            return "ayt_soz"  # sözel
        return "ayt_diger"
    return None


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("""
        SELECT id::text, exam_type, subject_area, irt_difficulty, bloom_level,
               pipeline_metadata::text
        FROM question_bank
        WHERE is_active=true
    """)
    rows = cur.fetchall()
    print(f"[scan] {len(rows):,} rows\n")

    updates = []
    for r in rows:
        qid, exam, subj, b, bloom, pm_str = r
        base = BASE_TIMES.get((exam or "").upper(), 90)
        smod = SUBJECT_MOD.get((subj or "").upper(), 1.0)
        dmod = difficulty_mod(float(b) if b is not None else None)
        bmod = bloom_mod(bloom)
        time_sec = base * smod * dmod * bmod
        time_sec = max(20, min(300, int(round(time_sec))))

        section = osym_section(exam, subj)

        ocr_conf = None
        if pm_str:
            try:
                pm = json.loads(pm_str)
                ec = pm.get("extraction_confidence")
                if ec is not None:
                    ocr_conf = round(float(ec), 4)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        updates.append((qid, time_sec, section, ocr_conf))

    print(f"[compute done] {len(updates):,}\n[apply chunked]...")
    CHUNK = 5000
    for i in range(0, len(updates), CHUNK):
        batch = updates[i : i + CHUNK]
        cur.execute("""
            CREATE TEMP TABLE _b3 (
                qid VARCHAR PRIMARY KEY,
                t INTEGER, sec VARCHAR, ocr NUMERIC
            ) ON COMMIT DROP
        """)
        execute_values(cur, "INSERT INTO _b3 VALUES %s", batch, page_size=5000)
        cur.execute("""
            UPDATE question_bank q
            SET estimated_solve_time_seconds = b.t,
                osym_section = b.sec,
                ocr_confidence_avg = b.ocr
            FROM _b3 b WHERE q.id::text = b.qid
        """)
        conn.commit()
        print(
            f"  chunk {i // CHUNK + 1}/{(len(updates) + CHUNK - 1) // CHUNK} ({cur.rowcount} updated)",
            flush=True,
        )
    print("[done]")
    conn.close()


if __name__ == "__main__":
    main()
