"""Faz 0 Step 2 — kimlik çekirdeği organization_id retrofit.

Kapsam: users, student_profiles, teacher_profiles, parent_profiles.
nullable org_id FK + org_legacy_default backfill. NOT NULL flip AYRI tur.
TDD: RED (kolon yok) → migration → GREEN (kolon var + 0 NULL).
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

IDENTITY_TABLES = ["users", "student_profiles", "teacher_profiles", "parent_profiles"]
LEGACY_ORG = "org_legacy_default"


def _engine():
    load_dotenv(
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True
    )
    raw = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not raw.startswith("postgresql"):
        pytest.skip("gerçek postgres DATABASE_URL yok")
    return create_engine(
        make_url(raw).set(host="127.0.0.1", port=5434, database="kiro2")
    )


def test_org_id_column_exists():
    eng = _engine()
    with eng.connect() as c:
        for t in IDENTITY_TABLES:
            n = c.execute(
                text(
                    "SELECT count(*) FROM information_schema.columns "
                    "WHERE table_name=:t AND column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert n == 1, f"{t}.organization_id kolonu yok"


def test_org_id_fk_to_organizations():
    eng = _engine()
    with eng.connect() as c:
        for t in IDENTITY_TABLES:
            fk = c.execute(
                text(
                    "SELECT count(*) FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "  ON tc.constraint_name=kcu.constraint_name "
                    "WHERE tc.table_name=:t AND tc.constraint_type='FOREIGN KEY' "
                    "  AND kcu.column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert fk >= 1, f"{t}.organization_id FK yok"


def test_legacy_org_exists():
    eng = _engine()
    with eng.connect() as c:
        n = c.execute(
            text("SELECT count(*) FROM organizations WHERE id=:i"), {"i": LEGACY_ORG}
        ).scalar()
        assert n == 1, "org_legacy_default kaydı yok"


def test_all_identity_rows_backfilled():
    """Backfill sonrası hiçbir satırda org_id NULL olmamalı (NOT NULL flip ön koşulu)."""
    eng = _engine()
    with eng.connect() as c:
        for t in IDENTITY_TABLES:
            nulls = c.execute(
                text(f"SELECT count(*) FROM {t} WHERE organization_id IS NULL")
            ).scalar()
            assert nulls == 0, f"{t}: {nulls} satır org_id NULL (backfill eksik)"
