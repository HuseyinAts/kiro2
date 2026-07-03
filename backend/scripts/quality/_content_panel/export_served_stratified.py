"""KIRO2 İçerik Kalitesi Uzman Paneli — servis edilen havuz stratified export.

Kaynak: v_safe_for_beta (CANLI servis havuzu). Branş başına <=40 soru, TAM METİN.
Secret güvenliği: DATABASE_URL backend/.env'den dotenv ile yüklenir, ASLA print edilmez.
"""

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND_ENV = Path(r"C:/Users/husey/kiro2/backend/.env")
OUT = Path(
    r"C:/Users/husey/kiro2/backend/scripts/quality/_content_panel/served_stratified_sample.csv"
)
PER_BRANCH = 40

load_dotenv(BACKEND_ENV)
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    sys.exit("ERROR: DATABASE_URL yok (backend/.env yüklenemedi)")
db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
# Gerçek instance: native PG18 localhost:5434 / kiro2. Parola/kullanıcı korunur, print YOK.
url = make_url(db_url).set(host="localhost", port=5434, database="kiro2")
engine = create_engine(url)

DIST_SQL = text(
    "SELECT q.subject_area, count(*) AS toplam "
    "FROM question_bank q WHERE q.id IN (SELECT id FROM v_safe_for_beta) "
    "GROUP BY q.subject_area ORDER BY toplam DESC"
)

SAMPLE_SQL = text(
    """
    WITH served AS (
      SELECT q.id, q.subject_area, q.exam_type, q.grade_level, q.question_text,
             q.option_a, q.option_b, q.option_c, q.option_d, q.option_e,
             upper(trim(q.correct_answer)) AS key,
             CASE WHEN q.question_image_url IS NOT NULL AND length(q.question_image_url) > 0
                  THEN 'VAR' ELSE '' END AS gorsel,
             q.source_book, q.source_page,
             row_number() OVER (PARTITION BY q.subject_area ORDER BY md5(q.id::text)) AS rn
      FROM question_bank q
      WHERE q.id IN (SELECT id FROM v_safe_for_beta)
    )
    SELECT id::text AS id, subject_area, exam_type, grade_level, question_text,
           option_a, option_b, option_c, option_d, option_e, key, gorsel,
           source_book, source_page
    FROM served WHERE rn <= :per ORDER BY subject_area, rn
    """
)

with engine.connect() as conn:
    print("=== v_safe_for_beta branş dağılımı (evren) ===")
    total = 0
    for row in conn.execute(DIST_SQL):
        print(f"  {row.subject_area:<14} {row.toplam}")
        total += row.toplam
    print(f"  {'TOPLAM':<14} {total}")

    rows = conn.execute(SAMPLE_SQL, {"per": PER_BRANCH}).fetchall()
    cols = [
        "id",
        "subject_area",
        "exam_type",
        "grade_level",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "option_e",
        "key",
        "gorsel",
        "source_book",
        "source_page",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(cols)
        for r in rows:
            w.writerow([r._mapping[c] for c in cols])

print(f"\n=== Export tamamlandı: {OUT.name} — {len(rows)} satır ===")
# Branş başına örneklem sayısı
from collections import Counter

c = Counter(r.subject_area for r in rows)
for k in sorted(c):
    print(f"  örneklem {k:<14} {c[k]}")
