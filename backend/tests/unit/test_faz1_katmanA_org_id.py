"""Faz 1 Katman A — yüksek-PII tablolara organization_id retrofit.

9 tablo: org_id NOT NULL + FK + backfill (0 NULL). Cross-tenant izolasyon,
BaseRepository org-scoped model olarak muamele için hazır (ORM wiring ayrı tur).
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

KATMAN_A = [
    "fsrs_cards",
    "fsrs_reviews",
    "fsrs_schedules",
    "student_abilities",
    "bkt_states",
    "student_knowledge_states",
    "performance_history",
    "kvkk_consents",
    "exam_sessions",
]


def _engine():
    load_dotenv(
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True
    )
    raw = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not raw.startswith("postgresql"):
        pytest.skip("gerçek postgres yok")
    return create_engine(
        make_url(raw).set(host="127.0.0.1", port=5434, database="kiro2")
    )


def test_org_id_column_notnull():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            nn = c.execute(
                text(
                    "SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_name=:t AND column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert nn == "NO", f"{t}.organization_id yok/nullable ({nn})"


def test_no_null_org_id():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            n = c.execute(
                text(f"SELECT count(*) FROM {t} WHERE organization_id IS NULL")
            ).scalar()
            assert n == 0, f"{t}: {n} NULL org_id"


def test_fk_to_organizations():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            fk = c.execute(
                text(
                    "SELECT count(*) FROM information_schema.key_column_usage kcu "
                    "JOIN information_schema.table_constraints tc "
                    "  ON tc.constraint_name=kcu.constraint_name "
                    "WHERE tc.table_name=:t AND tc.constraint_type='FOREIGN KEY' "
                    "  AND kcu.column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert fk >= 1, f"{t}.organization_id FK yok"


def test_server_default_legacy():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            d = c.execute(
                text(
                    "SELECT column_default FROM information_schema.columns "
                    "WHERE table_name=:t AND column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert d and "org_legacy_default" in d, f"{t} server_default yok"
