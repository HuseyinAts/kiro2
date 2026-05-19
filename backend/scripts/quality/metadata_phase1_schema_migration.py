#!/usr/bin/env python3
"""
Phase 1: Schema migration for P0-P3 metadata.

Adds columns + creates supporting tables. Idempotent (uses IF NOT EXISTS).
"""

import os
import sys

from sqlalchemy import create_engine, text

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

eng = create_engine(
    os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")
)

MIGRATIONS = [
    # ============= question_bank column additions =============
    # P0: IRT standard errors + audit
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS irt_se_a NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS irt_se_b NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS irt_se_c NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS irt_method_used VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS fisher_info_max NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS fisher_info_theta NUMERIC",
    # P0: Knowledge components (denormalized for fast lookup)
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS kc_ids JSON",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS q_matrix JSON",
    # P0: Embedding meta
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS embedding_model VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMPTZ",
    # P1: Solution + curriculum
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS solution_steps JSON",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS expected_answer_formula TEXT",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS answer_equivalent_forms JSON",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS numeric_tolerance NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS is_math_solvable BOOLEAN DEFAULT FALSE",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS mufredat_kazanim_id VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS mufredat_versiyon VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS osym_section VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS estimated_solve_time_seconds INTEGER",
    # P2: Extended taxonomies + diagnostic
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS solo_level VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS marzano_level VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS dina_slip NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS dina_guess NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS misconception_tags JSON",
    # P3: Visual + recommendation + A/B
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS diagram_type VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS has_alt_text BOOLEAN DEFAULT FALSE",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS alt_text TEXT",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS similar_question_ids JSON",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS variant_id VARCHAR",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS canonical_form_id VARCHAR",
    # Flagging
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS flag_count INTEGER DEFAULT 0",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS last_flagged_date TIMESTAMPTZ",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS ocr_confidence_avg NUMERIC",
    # Quality flags
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS metadata_completeness_score NUMERIC",
    "ALTER TABLE question_bank ADD COLUMN IF NOT EXISTS metadata_filled_at TIMESTAMPTZ",
    # ============= Supporting tables =============
    # Knowledge components (KC) — finer than topic
    """CREATE TABLE IF NOT EXISTS knowledge_components (
        kc_id VARCHAR PRIMARY KEY,
        kc_name VARCHAR NOT NULL,
        parent_topic_id VARCHAR REFERENCES topic_hierarchy(id),
        description TEXT,
        bkt_p_init NUMERIC DEFAULT 0.5,
        bkt_p_transit NUMERIC DEFAULT 0.1,
        bkt_p_guess NUMERIC DEFAULT 0.2,
        bkt_p_slip NUMERIC DEFAULT 0.1,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    # Q ↔ KC mapping (many-to-many with weight)
    """CREATE TABLE IF NOT EXISTS question_kc_mapping (
        question_id VARCHAR NOT NULL,
        kc_id VARCHAR NOT NULL REFERENCES knowledge_components(kc_id),
        weight NUMERIC DEFAULT 1.0,
        PRIMARY KEY (question_id, kc_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_qkc_question ON question_kc_mapping(question_id)",
    "CREATE INDEX IF NOT EXISTS idx_qkc_kc ON question_kc_mapping(kc_id)",
    # Per-option rationales (pedagogy)
    """CREATE TABLE IF NOT EXISTS question_option_rationales (
        id SERIAL PRIMARY KEY,
        question_id VARCHAR NOT NULL,
        option_letter CHAR(1) NOT NULL CHECK (option_letter IN ('A','B','C','D','E')),
        rationale TEXT,
        misconception_tag VARCHAR,
        is_correct BOOLEAN NOT NULL,
        generated_by VARCHAR,
        generated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(question_id, option_letter)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_qor_question ON question_option_rationales(question_id)",
    # SymPy math expressions
    """CREATE TABLE IF NOT EXISTS question_math (
        question_id VARCHAR PRIMARY KEY,
        expected_answer_sympy TEXT,
        numeric_tolerance NUMERIC,
        equivalent_forms JSON,
        is_symbolic_verifiable BOOLEAN DEFAULT FALSE,
        verified_by_sympy BOOLEAN DEFAULT FALSE,
        math_complexity_score NUMERIC,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
    # Curriculum alignment (MEB kazanım)
    """CREATE TABLE IF NOT EXISTS mufredat_kazanim (
        kazanim_id VARCHAR PRIMARY KEY,
        kazanim_text TEXT NOT NULL,
        topic_id VARCHAR,
        grade_level INTEGER,
        exam_type VARCHAR,
        subject_area VARCHAR,
        mufredat_versiyon VARCHAR DEFAULT '2024'
    )""",
]


def run():
    print("[start] Phase 1 schema migration\n")
    success = 0
    skipped = 0
    failed = 0
    for i, sql in enumerate(MIGRATIONS, 1):
        try:
            with eng.begin() as c:
                c.execute(text(sql))
            preview = sql.split("\n")[0][:80]
            print(f"  [{i:2d}] OK  {preview}...")
            success += 1
        except Exception as e:
            msg = str(e).split("\n")[0][:80]
            print(f"  [{i:2d}] FAIL {preview}: {msg}")
            failed += 1

    print(f"\n[summary] success={success}  failed={failed}")
    # Verify
    with eng.connect() as c:
        cols = c.execute(
            text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='question_bank' ORDER BY ordinal_position
        """)
        ).fetchall()
        print(f"\nquestion_bank now has {len(cols)} columns")
        tables = c.execute(
            text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_name IN
              ('knowledge_components', 'question_kc_mapping', 'question_option_rationales',
               'question_math', 'mufredat_kazanim')
            ORDER BY table_name
        """)
        ).fetchall()
        print(f"New tables: {[t.table_name for t in tables]}")


if __name__ == "__main__":
    run()
