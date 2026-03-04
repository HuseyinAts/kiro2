# PostgreSQL Question Import Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Load 77,336 production questions from `d-dataset/eslesmis_sorucevap.jsonl` into the `question_bank` PostgreSQL table with subject/exam_type classification.

**Architecture:** Add 3 new columns to `question_bank` via Alembic migration (source_book, source_page, pipeline_metadata JSONB). Create a standalone import script that reads JSONL, classifies subject/exam from book names, generates deterministic UUIDs, and batch-inserts with ON CONFLICT DO NOTHING. Create a default topic hierarchy entry for uncategorized questions.

**Tech Stack:** Python 3.11, SQLAlchemy (asyncpg), Alembic, PostgreSQL 15 (port 5434), uuid5

---

### Task 1: Add New Columns via Alembic Migration

**Files:**
- Create: `backend/alembic/versions/20260304_add_pipeline_source_columns.py`

**Step 1: Create the migration file**

```python
"""Add source_book, source_page, pipeline_metadata to question_bank

Revision ID: 20260304_pipeline
Revises: (auto-detect head)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260304_pipeline"
down_revision = None  # Will be set by --autogenerate or manually
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("question_bank", sa.Column("source_book", sa.String(300), nullable=True))
    op.add_column("question_bank", sa.Column("source_page", sa.Integer(), nullable=True))
    op.add_column("question_bank", sa.Column("pipeline_metadata", JSONB(), server_default="{}", nullable=True))
    op.create_index("idx_qbank_source_book", "question_bank", ["source_book"])

def downgrade():
    op.drop_index("idx_qbank_source_book", table_name="question_bank")
    op.drop_column("question_bank", "pipeline_metadata")
    op.drop_column("question_bank", "source_page")
    op.drop_column("question_bank", "source_book")
```

**Step 2: Update QuestionBankItem model**

Add 3 new fields to `backend/models/question_bank.py` in the QuestionBankItem class, after the `quality_review_status` field (~line 400):

```python
    # ========================================================================
    # Pipeline Source Tracking (d-dataset import)
    # ========================================================================
    source_book: Mapped[Optional[str]] = mapped_column(String(300))
    source_page: Mapped[Optional[int]] = mapped_column(Integer)
    pipeline_metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # Full provenance from JSONL
```

**Step 3: Run the migration**

```bash
cd backend && alembic upgrade head
```

Expected: Migration applied, 3 new columns visible in question_bank table.

**Step 4: Verify**

```bash
cd backend && python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:changeme@localhost:5434/kiro2_db')
with engine.connect() as conn:
    result = conn.execute(text(\"SELECT column_name FROM information_schema.columns WHERE table_name='question_bank' AND column_name IN ('source_book','source_page','pipeline_metadata')\"))
    cols = [r[0] for r in result]
    print('New columns:', cols)
    assert len(cols) == 3, f'Expected 3, got {len(cols)}'
print('OK')
"
```

**Step 5: Commit**

```bash
git add backend/alembic/versions/20260304_add_pipeline_source_columns.py backend/models/question_bank.py
git commit -m "feat(backend): add source_book, source_page, pipeline_metadata to question_bank"
```

---

### Task 2: Create Default Topic Hierarchy Entry

The `question_bank.primary_topic_id` is a required FK. We need a default topic for imported questions.

**Files:**
- Modify: Import script (created in Task 3) will handle this inline

**Step 1: Create default topic via SQL in import script**

The import script will ensure these topics exist before inserting questions:

```python
DEFAULT_TOPICS = {
    "MATEMATIK": {"code": "MAT", "name_tr": "Matematik"},
    "GEOMETRI": {"code": "GEO", "name_tr": "Geometri"},
    "FIZIK": {"code": "FIZ", "name_tr": "Fizik"},
    "KIMYA": {"code": "KIM", "name_tr": "Kimya"},
    "BIYOLOJI": {"code": "BIY", "name_tr": "Biyoloji"},
    "EDEBIYAT": {"code": "EDB", "name_tr": "Türk Dili ve Edebiyatı"},
    "TURKCE": {"code": "TUR", "name_tr": "Türkçe"},
    "TARIH": {"code": "TAR", "name_tr": "Tarih"},
    "COGRAFYA": {"code": "COG", "name_tr": "Coğrafya"},
    "SOSYAL": {"code": "SOS", "name_tr": "Sosyal Bilimler"},
    "FEN": {"code": "FEN", "name_tr": "Fen Bilimleri"},
    "INGILIZCE": {"code": "ING", "name_tr": "İngilizce"},
    "GENEL": {"code": "GEN", "name_tr": "Genel"},
}
```

Uses deterministic UUIDs: `uuid5(NAMESPACE, code)` so topic IDs are stable across re-runs.

---

### Task 3: Create the Import Script

**Files:**
- Create: `backend/scripts/import_d_dataset.py`

**Step 1: Write the import script**

```python
#!/usr/bin/env python3
"""
Import d-dataset questions into question_bank table.

Usage:
    cd backend
    python scripts/import_d_dataset.py [--dry-run] [--batch-size 1000] [--jsonl-path PATH]

Reads: d-dataset/eslesmis_sorucevap.jsonl (77,336 questions)
Target: question_bank table (PostgreSQL 15, port 5434)
"""

import argparse
import json
import os
import sys
import unicodedata
import uuid
from collections import Counter
from pathlib import Path
from time import time

# Deterministic namespace for UUID generation
KIRO2_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

# --- Subject Classification ---

SUBJECT_PATTERNS = [
    # AYT-specific math topics FIRST (before generic 'matematik')
    (["trigonometri", "türev", "turev", "integral", "logaritma",
      "polinom", "fonksiyon", "diziler", "limit ve süreklilik"],
     "MATEMATIK", "AYT"),
    (["katı cisim", "kati cisim", "analitik geometri"], "GEOMETRI", "AYT"),
    # Generic subjects
    (["geometri", "üçgen", "ucgen", "dörtgen", "dortgen"], "GEOMETRI", None),
    (["matematik", "problemler", "sayılar", "sayilar", "matemateik",
      "matemat,k", "matematiğin", "matematig", "problemin"], "MATEMATIK", None),
    (["fizik", "fizipedia", "neofizik"], "FIZIK", None),
    (["kimya", "aromat"], "KIMYA", None),
    (["biyoloji"], "BIYOLOJI", None),
    (["edebiyat"], "EDEBIYAT", "AYT"),
    (["paragraf", "türkçe", "turkce", "türkce", "dil bilgisi", "dilbilgisi",
      "sözcük", "sozcuk", "anlam", "atasözleri", "atasozu", "kurgulu"], "TURKCE", "TYT"),
    (["tarih"], "TARIH", None),
    (["coğrafya", "cografya"], "COGRAFYA", None),
    (["sosyal"], "SOSYAL", "TYT"),
    (["fen bilim"], "FEN", "TYT"),
    (["ingilizce", "ydt"], "INGILIZCE", "YDT"),
]

# Manual overrides for tricky books
BOOK_OVERRIDES = {
    # Generic TYT Soru Bankası books — contain mixed subjects, classify as GENEL
    "ACİL-2025-TYT-Soru Bankası": ("GENEL", "TYT"),
    "ACİL-2025-TYT-Soeu Bankası": ("GENEL", "TYT"),
    "2019-2020-ACİL-TYT-Soru Bankası": ("GENEL", "TYT"),
}


def normalize_tr(text: str) -> str:
    """Turkish-aware lowercase normalization."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()


def classify_book(book_name: str) -> tuple[str, str]:
    """Classify book into (subject, exam_type)."""
    # Check overrides first
    for override_name, (subj, exam) in BOOK_OVERRIDES.items():
        if normalize_tr(override_name) == normalize_tr(book_name):
            return subj, exam

    bn = normalize_tr(book_name)

    # Detect subject
    subject = None
    default_exam = None
    for patterns, subj, defexam in SUBJECT_PATTERNS:
        for p in patterns:
            if p in bn:
                subject = subj
                default_exam = defexam
                break
        if subject:
            break

    if subject is None:
        subject = "GENEL"

    # Detect exam type from name
    exam = None
    if "ayt" in bn:
        exam = "AYT"
    if "tyt" in bn:
        exam = "TYT" if exam is None else exam
    if "ydt" in bn:
        exam = "YDT"

    if exam is None:
        exam = default_exam or "TYT"

    return subject, exam


def generate_question_id(book_name: str, page: int, q_num: int) -> str:
    """Generate deterministic UUID from question identity."""
    key = f"{book_name}|{page}|{q_num}"
    return str(uuid.uuid5(KIRO2_NAMESPACE, key))


def generate_topic_id(subject_code: str) -> str:
    """Generate deterministic UUID for topic."""
    return str(uuid.uuid5(KIRO2_NAMESPACE, f"topic_{subject_code}"))


DEFAULT_TOPICS = {
    "MATEMATIK": ("MAT", "Matematik"),
    "GEOMETRI": ("GEO", "Geometri"),
    "FIZIK": ("FIZ", "Fizik"),
    "KIMYA": ("KIM", "Kimya"),
    "BIYOLOJI": ("BIY", "Biyoloji"),
    "EDEBIYAT": ("EDB", "Türk Dili ve Edebiyatı"),
    "TURKCE": ("TUR", "Türkçe"),
    "TARIH": ("TAR", "Tarih"),
    "COGRAFYA": ("COG", "Coğrafya"),
    "SOSYAL": ("SOS", "Sosyal Bilimler"),
    "FEN": ("FEN", "Fen Bilimleri"),
    "INGILIZCE": ("ING", "İngilizce"),
    "GENEL": ("GEN", "Genel"),
}

# Fields that go into question_bank columns (not pipeline_metadata)
DIRECT_FIELDS = {"text", "options", "answer", "book_name", "page_number",
                 "question_number", "quality_score", "confidence"}


def build_row(entry: dict, subject: str, exam_type: str) -> dict:
    """Transform a JSONL entry into a question_bank row dict."""
    options = entry.get("options", {})
    q_id = generate_question_id(
        entry["book_name"],
        entry["page_number"],
        entry["question_number"],
    )
    topic_code = DEFAULT_TOPICS.get(subject, ("GEN", "Genel"))[0]
    topic_id = generate_topic_id(topic_code)

    # Pipeline metadata: everything except direct-mapped fields
    metadata = {k: v for k, v in entry.items() if k not in DIRECT_FIELDS}

    return {
        "id": q_id,
        "question_text": entry.get("text", ""),
        "option_a": options.get("A", ""),
        "option_b": options.get("B", ""),
        "option_c": options.get("C", ""),
        "option_d": options.get("D", ""),
        "option_e": options.get("E"),
        "correct_answer": entry.get("answer", "A"),
        "primary_topic_id": topic_id,
        "exam_type": exam_type,
        "subject_area": subject,
        "grade_level": 11,  # Default for YKS prep
        "quality_score": entry.get("quality_score") or 0.0,
        "calibration_quality_score": entry.get("confidence") or 0.0,
        "quality_review_status": "approved",  # Pipeline-validated
        "source_book": entry.get("book_name"),
        "source_page": entry.get("page_number"),
        "pipeline_metadata": json.dumps(metadata, ensure_ascii=False),
        "is_active": True,
        "is_public": False,
        "osym_format_compliant": True,
    }


def main():
    parser = argparse.ArgumentParser(description="Import d-dataset → question_bank")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and classify only, don't insert")
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--jsonl-path", type=str,
                        default=str(Path(__file__).parent.parent.parent / "d-dataset" / "eslesmis_sorucevap.jsonl"))
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5434/kiro2_db"
    )

    print("=" * 60)
    print("d-dataset → question_bank Import")
    print("=" * 60)
    print(f"JSONL: {args.jsonl_path}")
    print(f"DB: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print(f"Batch size: {args.batch_size}")
    print(f"Dry run: {args.dry_run}")
    print()

    # --- Phase 1: Parse and classify ---
    t0 = time()
    rows = []
    subject_counts = Counter()
    exam_counts = Counter()
    errors = []

    with open(args.jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                subject, exam_type = classify_book(entry.get("book_name", ""))
                subject_counts[subject] += 1
                exam_counts[exam_type] += 1
                row = build_row(entry, subject, exam_type)
                rows.append(row)
            except Exception as e:
                errors.append((line_num, str(e)))

    t_parse = time() - t0
    print(f"Parsed {len(rows)} questions in {t_parse:.1f}s ({len(errors)} errors)")
    print()
    print("Subject distribution:")
    for subj, cnt in subject_counts.most_common():
        print(f"  {subj:15s}: {cnt:6d}")
    print()
    print("Exam type distribution:")
    for exam, cnt in exam_counts.most_common():
        print(f"  {exam:5s}: {cnt:6d}")

    if errors:
        print(f"\nFirst 5 errors:")
        for ln, err in errors[:5]:
            print(f"  Line {ln}: {err}")

    if args.dry_run:
        print("\n[DRY RUN] No database changes made.")
        return

    # --- Phase 2: Insert into PostgreSQL ---
    from sqlalchemy import create_engine, text

    engine = create_engine(db_url)

    with engine.begin() as conn:
        # Ensure topic_hierarchy entries exist
        print("\nCreating default topics...")
        for subject, (code, name_tr) in DEFAULT_TOPICS.items():
            topic_id = generate_topic_id(code)
            conn.execute(text("""
                INSERT INTO topic_hierarchy (id, level, code, name_tr, is_active)
                VALUES (:id, 1, :code, :name_tr, true)
                ON CONFLICT (code) DO NOTHING
            """), {"id": topic_id, "code": code, "name_tr": name_tr})
        print(f"  {len(DEFAULT_TOPICS)} topics ensured")

        # Batch insert questions
        print(f"\nInserting {len(rows)} questions in batches of {args.batch_size}...")
        inserted = 0
        skipped = 0

        for i in range(0, len(rows), args.batch_size):
            batch = rows[i:i + args.batch_size]
            for row in batch:
                result = conn.execute(text("""
                    INSERT INTO question_bank (
                        id, question_text, option_a, option_b, option_c, option_d, option_e,
                        correct_answer, primary_topic_id, exam_type, subject_area, grade_level,
                        quality_score, calibration_quality_score, quality_review_status,
                        source_book, source_page, pipeline_metadata,
                        is_active, is_public, osym_format_compliant
                    ) VALUES (
                        :id, :question_text, :option_a, :option_b, :option_c, :option_d, :option_e,
                        :correct_answer, :primary_topic_id, :exam_type, :subject_area, :grade_level,
                        :quality_score, :calibration_quality_score, :quality_review_status,
                        :source_book, :source_page, :pipeline_metadata::jsonb,
                        :is_active, :is_public, :osym_format_compliant
                    )
                    ON CONFLICT (id) DO NOTHING
                """), row)
                if result.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1

            pct = min(100, (i + len(batch)) / len(rows) * 100)
            print(f"  [{pct:5.1f}%] {i + len(batch):,}/{len(rows):,} processed "
                  f"({inserted:,} inserted, {skipped:,} skipped)")

    # --- Phase 3: Verify ---
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM question_bank"))
        total = result.scalar()
        result2 = conn.execute(text(
            "SELECT subject_area, COUNT(*) FROM question_bank "
            "GROUP BY subject_area ORDER BY COUNT(*) DESC"
        ))
        print(f"\n{'='*60}")
        print(f"RESULTS")
        print(f"{'='*60}")
        print(f"Total in question_bank: {total:,}")
        print(f"Inserted: {inserted:,}")
        print(f"Skipped (duplicate): {skipped:,}")
        print(f"Errors: {len(errors)}")
        print(f"\nBy subject:")
        for row in result2:
            print(f"  {row[0]:15s}: {row[1]:6d}")

    engine.dispose()
    print(f"\nDone in {time() - t0:.1f}s")


if __name__ == "__main__":
    main()
```

**Step 2: Run dry-run to verify classification**

```bash
cd backend && python scripts/import_d_dataset.py --dry-run
```

Expected: 77,336 questions parsed, ~95% classified, 0 errors.

**Step 3: Run the actual import**

```bash
cd backend && python scripts/import_d_dataset.py
```

Expected: 77,336 inserted, 0 skipped (first run), 0 errors.

**Step 4: Verify in database**

```bash
cd backend && python -c "
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:changeme@localhost:5434/kiro2_db')
with engine.connect() as conn:
    total = conn.execute(text('SELECT COUNT(*) FROM question_bank')).scalar()
    print(f'Total questions: {total:,}')
    assert total >= 77000, f'Expected 77K+, got {total}'
print('PASS')
"
```

**Step 5: Commit**

```bash
git add backend/scripts/import_d_dataset.py
git commit -m "feat(backend): add d-dataset import script for question_bank (77K questions)"
```

---

### Task 4: Add Unclassified Book Handling

The dry-run from Task 3 will show ~3,877 unclassified questions (5%). These fall into patterns we can fix.

**Files:**
- Modify: `backend/scripts/import_d_dataset.py`

**Step 1: Analyze unclassified books from dry-run output**

Known unclassified patterns:
- `ACİL-2025-TYT-Soru Bankası` → GENEL, TYT (mixed-subject book)
- `Mikro Orijinal-*-12liDeneme-*` → infer from Tyt/Ayt in name, GENEL subject
- `Krallar Karmasi * Paket Deneme` → GENEL, AYT
- `Krallar Karması Türkce Brans` → TURKCE, TYT
- `Deneme Deposu Tyt` → GENEL, TYT
- `Cap Tyt Konu Anlatımlı` → GENEL, TYT
- `Esen * 6lı Deneme` → GENEL, TYT/AYT

**Step 2: Add these to BOOK_OVERRIDES or refine patterns**

Add broader pattern matches for remaining unclassified books. The key patterns to add:
- `"ilac"` (ilaç/ilacı) → MATEMATIK (Acil Matematiğin İlacı series)
- `"deneme"` with no subject → GENEL
- `"soru bankası"` / `"soru bankas"` with no subject → GENEL
- `"konu anlatımlı"` → GENEL

**Step 3: Re-run dry-run to verify improvement**

```bash
cd backend && python scripts/import_d_dataset.py --dry-run
```

Target: <1% unclassified (subject=GENEL is acceptable for mixed-subject books).

**Step 4: Commit**

```bash
git add backend/scripts/import_d_dataset.py
git commit -m "fix(backend): improve book classification coverage for import"
```

---

### Task 5: Write Tests for Classification Logic

**Files:**
- Create: `backend/tests/test_import_d_dataset.py`

**Step 1: Write the test file**

```python
"""Tests for d-dataset import classification logic."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.import_d_dataset import classify_book, normalize_tr, generate_question_id


class TestNormalizeTr:
    def test_basic(self):
        assert normalize_tr("İSTANBUL") == "istanbul"

    def test_turkish_i(self):
        assert normalize_tr("IŞIK") == "ışık"

    def test_empty(self):
        assert normalize_tr("") == ""


class TestClassifyBook:
    @pytest.mark.parametrize("book,expected_subject,expected_exam", [
        ("345 2025 Ayt Matematik Soru Bankası", "MATEMATIK", "AYT"),
        ("Bilgi Sarmalı-2025-Tyt-Matematik Soru Bankası", "MATEMATIK", "TYT"),
        ("Orijinal-2024-Geometri Soru Bankası", "GEOMETRI", "TYT"),
        ("345 2025 Ayt Fizik Soru Bankası", "FIZIK", "AYT"),
        ("Apotemi Tyt Ayt Kimya 2019-2020", "KIMYA", "TYT"),
        ("Edebiyat Denizi Ayt Edebiyat Soru Bankasi", "EDEBIYAT", "AYT"),
        ("Esen Tyt Türkçe Soru Bankası", "TURKCE", "TYT"),
        ("Mikro Orijinal Tyt Paragraf Soru Bankası 2024", "TURKCE", "TYT"),
        ("Orijinal-2025-Ayt-Matematik Türev", "MATEMATIK", "AYT"),
        ("Orijinal-2025-Analitik Geometri", "GEOMETRI", "AYT"),
        ("345 2025 Tyt Biyoloji Soru Bankası", "BIYOLOJI", "TYT"),
        ("Esen Aps Tyt Ayt Tarih Soru Bankası", "TARIH", "TYT"),
    ])
    def test_known_books(self, book, expected_subject, expected_exam):
        subject, exam = classify_book(book)
        assert subject == expected_subject
        assert exam == expected_exam

    def test_unknown_book_gets_genel(self):
        subject, exam = classify_book("Unknown Publisher Random Book 2025")
        assert subject == "GENEL"


class TestGenerateQuestionId:
    def test_deterministic(self):
        id1 = generate_question_id("Book A", 10, 5)
        id2 = generate_question_id("Book A", 10, 5)
        assert id1 == id2

    def test_different_inputs(self):
        id1 = generate_question_id("Book A", 10, 5)
        id2 = generate_question_id("Book A", 10, 6)
        assert id1 != id2
```

**Step 2: Run tests**

```bash
cd backend && pytest tests/test_import_d_dataset.py -v
```

Expected: All tests PASS.

**Step 3: Commit**

```bash
git add backend/tests/test_import_d_dataset.py
git commit -m "test(backend): add tests for d-dataset import classification"
```

---

### Task 6: Final Verification and Cleanup

**Step 1: Run full import if not done yet**

```bash
cd backend && python scripts/import_d_dataset.py
```

**Step 2: Verify via API (if backend is running)**

```bash
curl -s http://localhost:8000/api/v1/questions/search -X POST \
  -H "Content-Type: application/json" \
  -d '{"exam_type": "TYT", "subject_area": "MATEMATIK", "limit": 3}' | python -m json.tool
```

**Step 3: Run idempotency check (re-run should skip all)**

```bash
cd backend && python scripts/import_d_dataset.py
```

Expected: 0 inserted, 77,336 skipped.

**Step 4: Final commit with all changes**

```bash
git add -A
git commit -m "feat(backend): complete d-dataset PostgreSQL import (77K questions)"
```
