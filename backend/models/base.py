"""
SQLAlchemy Base Declarative
Circular import'u onlemek icin Base ayri dosyada

IMPORTANT: models/ icindeki dosyalar SADECE relative import kullanmali:
    from .base import Base        # DOGRU
    from .database import Base    # DOGRU
    from models.base import Base  # YANLIS - cift MetaData olusturur!

Bu kural scripts/check_model_imports.py ile CI'da kontrol edilir.
"""

from sqlalchemy.orm import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()

# ---------------------------------------------------------
# SQLite Dialect Fixes for PostgreSQL Types
# Enables running create_all() on in-memory SQLite for tests
# without raising CompileError for Postgres-specific columns
# ---------------------------------------------------------
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
try:
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
except ImportError:
    PGUUID = UUID

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(ARRAY, "sqlite")
def compile_array_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(PGUUID, "sqlite")
def compile_pguuid_sqlite(type_, compiler, **kw):
    return "TEXT"
