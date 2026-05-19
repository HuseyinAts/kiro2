#!/usr/bin/env python3
"""
v17 — answers_v9.db cross-reference audit.

veriseti/zkitap/answers_v9.db has 7,035 question_answer_pairs from an
earlier extraction (2026-02-14). Cross-check against question_bank:
  - Find DB rows with (book, page) match
  - Compare DB.correct_answer vs answers_v9.answer
  - Report mismatches (potential quality issues)
  - Report NULL DB answers where answers_v9 has an answer (fillable)
"""

import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent.parent
ANSWERS_DB = PROJECT_ROOT / "veriseti" / "zkitap" / "answers_v9.db"


def _fold(s):
    return s.translate(str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")).lower()


def _canon(s):
    return re.sub(r"\W+", "_", _fold(s or "")).strip("_")


# Load all question_answer_pairs
print("[load] answers_v9.db...")
conn = sqlite3.connect(str(ANSWERS_DB))
qa_pairs = conn.execute(
    "SELECT book_name, page_number, question_number, answer_text FROM question_answer_pairs"
).fetchall()
extracted = conn.execute(
    "SELECT book_name, page_number, question_number, answer, confidence FROM extracted_answers"
).fetchall()
print(f"  question_answer_pairs: {len(qa_pairs):,}")
print(f"  extracted_answers: {len(extracted):,}\n")

# Index by (book_canon, page)
qa_idx: dict = {}
for book, page, qno, ans in qa_pairs:
    if not (book and page is not None and ans):
        continue
    bk = _canon(book)
    qa_idx.setdefault((bk, int(page)), {})[int(qno) if qno else 0] = (ans or "").strip()

extracted_idx: dict = {}
for book, page, qno, ans, conf in extracted:
    if not (book and page is not None and ans):
        continue
    bk = _canon(book)
    extracted_idx.setdefault((bk, int(page)), {})[int(qno) if qno else 0] = (
        (ans or "").strip().upper(),
        conf,
    )

print(
    f"[indexed] qa pairs: {len(qa_idx):,} pages | extracted: {len(extracted_idx):,} pages\n"
)

# Now cross-check DB
from sqlalchemy import create_engine, text

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

print("[scan] active DB rows...")
with eng.connect() as c:
    rows = c.execute(
        text("""
        SELECT id::text, source_book, source_page, correct_answer
        FROM question_bank
        WHERE is_active=true AND source_book IS NOT NULL AND source_page IS NOT NULL
    """)
    ).fetchall()
print(f"  active rows: {len(rows):,}\n")

stats = {
    "pages_with_qa_match": 0,
    "rows_with_qa_match": 0,
    "answer_agreement": 0,
    "answer_disagreement": 0,
    "db_null_v9_has": 0,
    "extracted_high_conf_only": 0,
    "no_v9_data": 0,
}
disagree_samples = []
fillable_samples = []
disagree_letters = Counter()

# Group rows by (book, page) for processing
from collections import defaultdict

rows_by_page = defaultdict(list)
for r in rows:
    bk = _canon(r.source_book)
    rows_by_page[(bk, int(r.source_page))].append(r)

for key, page_rows in rows_by_page.items():
    qa_data = qa_idx.get(key, {})
    ex_data = extracted_idx.get(key, {})
    if not qa_data and not ex_data:
        stats["no_v9_data"] += len(page_rows)
        continue

    stats["pages_with_qa_match"] += 1
    for r in page_rows:
        stats["rows_with_qa_match"] += 1
        db_ans = (r.correct_answer or "").strip().upper()

        # Pick highest-confidence answer from any source
        v9_ans = None
        for qno, ans in qa_data.items():
            v9_ans = ans.strip().upper() if ans else None
            if v9_ans:
                break
        if not v9_ans:
            for qno, (ans, conf) in ex_data.items():
                if ans and conf and conf > 0.7:
                    v9_ans = ans
                    break

        if not db_ans and v9_ans:
            stats["db_null_v9_has"] += 1
            if len(fillable_samples) < 3:
                fillable_samples.append(
                    f"  {r.id[:8]} p{r.source_page} db=NULL v9={v9_ans}"
                )
        elif db_ans and v9_ans:
            if db_ans == v9_ans:
                stats["answer_agreement"] += 1
            else:
                stats["answer_disagreement"] += 1
                disagree_letters[(db_ans, v9_ans)] += 1
                if len(disagree_samples) < 5:
                    disagree_samples.append(
                        f"  {r.id[:8]} p{r.source_page} db={db_ans} v9={v9_ans} book={r.source_book[:35]}"
                    )

print("[result]")
for k, v in stats.items():
    print(f"  {k}: {v:,}")

if stats["answer_agreement"] + stats["answer_disagreement"] > 0:
    ratio = stats["answer_agreement"] / (
        stats["answer_agreement"] + stats["answer_disagreement"]
    )
    print(f"\nAgreement ratio: {ratio * 100:.1f}%")

print("\n[top disagreement patterns]")
for (db, v9), n in disagree_letters.most_common(8):
    print(f"  db={db} ↔ v9={v9}: {n}")

if disagree_samples:
    print("\n[disagree samples]")
    for s in disagree_samples:
        print(s)

if fillable_samples:
    print("\n[fillable samples]")
    for s in fillable_samples:
        print(s)
