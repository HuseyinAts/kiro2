"""Faz 0 Step 2 — kimlik çekirdeği organization_id retrofit.

Kapsam: users, student_profiles, teacher_profiles, parent_profiles.
nullable org_id FK + org_legacy_default backfill. NOT NULL flip AYRI tur.
TDD: RED (kolon yok) → migration → GREEN (kolon var + 0 NULL).
"""

from sqlalchemy import text

from tests.pg_sync import sync_pg_engine

IDENTITY_TABLES = ["users", "student_profiles", "teacher_profiles", "parent_profiles"]
LEGACY_ORG = "org_legacy_default"


def _engine():
    # Ortak tanim ve olcum gerekcesi: tests/pg_sync.py
    return sync_pg_engine()


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
            # S608: tablo adi KULLANICI GIRDISI DEGIL -- yukaridaki sabit
            # IDENTITY_TABLES listesinden geliyor. Tablo adi SQL'de bind
            # parametresi olamaz, bu yuzden f-string zorunlu.
            nulls = c.execute(
                text(f"SELECT count(*) FROM {t} WHERE organization_id IS NULL")  # noqa: S608
            ).scalar()
            assert nulls == 0, f"{t}: {nulls} satır org_id NULL (backfill eksik)"
