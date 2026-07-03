"""Faz 0 Step 1 — organizations + org_memberships tabloları.

TDD: bu test önce RED (tablolar DB'de yok), migration sonrası GREEN.
Model yapısı (unit) + DB varlığı (integration) doğrular.
"""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from models.organization import Organization, OrgMembership


def _engine():
    # override=True: conftest TESTING modunda DATABASE_URL'i sqlite'a set eder;
    # bu DB-doğrulama testleri gerçek postgres (5434/kiro2) hedefler.
    load_dotenv(
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=True
    )
    raw = os.environ.get("DATABASE_URL", "").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    if not raw.startswith("postgresql"):
        pytest.skip("gerçek postgres DATABASE_URL yok")
    return create_engine(
        make_url(raw).set(host="localhost", port=5434, database="kiro2")
    )


def test_model_structure():
    """Model kolonları + konvansiyonlar (DB'siz)."""
    assert Organization.__tablename__ == "organizations"
    assert OrgMembership.__tablename__ == "org_memberships"
    # VARCHAR PK (users.id deseni)
    assert isinstance(Organization.__table__.c.id.type.python_type, type)
    assert Organization.__table__.c.id.primary_key
    # kurumsal alanlar
    for col in ("name", "org_type", "status", "kvkk_role", "license_seats"):
        assert col in Organization.__table__.c
    # membership FK'leri
    for col in ("organization_id", "user_id", "org_role"):
        assert col in OrgMembership.__table__.c


def test_tables_exist_in_db():
    """Migration sonrası DB'de tablolar mevcut olmalı."""
    eng = _engine()
    with eng.connect() as c:
        for t in ("organizations", "org_memberships"):
            n = c.execute(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_name=:t AND table_schema='public'"
                ),
                {"t": t},
            ).scalar()
            assert n == 1, f"tablo {t} DB'de yok"


def test_membership_fk_and_unique():
    """org_memberships FK'leri + (org,user) unique kısıtı DB'de olmalı."""
    eng = _engine()
    with eng.connect() as c:
        fks = c.execute(
            text(
                "SELECT count(*) FROM information_schema.table_constraints "
                "WHERE table_name='org_memberships' AND constraint_type='FOREIGN KEY'"
            )
        ).scalar()
        assert fks >= 2, "org_memberships 2 FK bekleniyor (org + user)"
        uq = c.execute(
            text(
                "SELECT count(*) FROM information_schema.table_constraints "
                "WHERE table_name='org_memberships' AND constraint_type='UNIQUE'"
            )
        ).scalar()
        assert uq >= 1, "org_memberships unique (org,user) bekleniyor"
