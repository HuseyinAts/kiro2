"""Alembic Migration Guard Utilities

Provides defensive DDL helpers using SQLAlchemy inspection.
Prevents transaction failure cascades caused by duplicate table/column/index creation
or dropping non-existent entities.
"""

from __future__ import annotations

import logging
from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Engine

# alembic'in `op` nesnesi calisma zamaninda thread-local bir proxy
# (Operations sinifi) uzerinden dinamik kuruluyor; `alembic/__init__.py`de
# statik bir `op` ozniteligi yok, bu yuzden mypy bunu HER ZAMAN attr-defined
# olarak isaretler (bilinen, yukari-akis/upstream sinirlama -- dinamik proxy
# statik analizle cozulemez). Kok pyproject.toml'daki [[tool.mypy.overrides]]
# listesi benzer ortam/arac sinirlamalarini (types-redis, cachetools stub'i
# yoklugu) ignore_errors=true ile TUM dosyayi kapsayarak kaydediyor; burada
# bunun yerine TEK SATIRLIK, dosyanin geri kalanini (asagidaki no-any-return
# duzeltmesi dahil) denetimden cikarmayan bir bastirma tercih edildi -- bu
# dosya bu kampanyada yeni yazilan bir dosya, mevcut borc degil.
from alembic import op  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


def get_inspector(bind: Engine | Connection | None = None):
    """Get SQLAlchemy Inspector for the current Alembic migration context or bind."""
    if bind is None:
        bind = op.get_bind()
    return sa.inspect(bind)


def table_exists(table_name: str, bind: Engine | Connection | None = None) -> bool:
    """Check if a table exists in the database."""
    inspector = get_inspector(bind)
    # Inspector.has_table()'in donus tipi mypy'ye Any olarak yansiyor (stub
    # sinirlamasi); acik yerel degisken anotasyonu ile no-any-return'u
    # bastirmadan gercek tipi (bool) sabitliyoruz -- ayni desen bu
    # kampanyada ensemble_manager.py / ai_mentor_service.py'de de kullanildi.
    result: bool = inspector.has_table(table_name)
    return result


def column_exists(
    table_name: str, column_name: str, bind: Engine | Connection | None = None
) -> bool:
    """Check if a column exists in a table."""
    inspector = get_inspector(bind)
    if not inspector.has_table(table_name):
        return False
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(
    table_name: str, index_name: str, bind: Engine | Connection | None = None
) -> bool:
    """Check if an index exists on a table."""
    inspector = get_inspector(bind)
    if not inspector.has_table(table_name):
        return False
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def constraint_exists(
    table_name: str, constraint_name: str, bind: Engine | Connection | None = None
) -> bool:
    """Check if a constraint (unique, check, FK, PK) exists on a table."""
    inspector = get_inspector(bind)
    if not inspector.has_table(table_name):
        return False

    # Check unique constraints
    uniques = [
        c["name"] for c in inspector.get_unique_constraints(table_name) if c.get("name")
    ]
    if constraint_name in uniques:
        return True

    # Check foreign keys
    fks = [c["name"] for c in inspector.get_foreign_keys(table_name) if c.get("name")]
    if constraint_name in fks:
        return True

    # Check check constraints if supported
    try:
        checks = [
            c["name"]
            for c in inspector.get_check_constraints(table_name)
            if c.get("name")
        ]
        if constraint_name in checks:
            return True
    except Exception as e:
        # SQLAlchemy dialect/surumlerinde bazen desteklenmiyor (NotImplementedError
        # veya baska bir istisna atabilir, tam kume dokumante degil); bunu
        # "check constraint yok" ile aynen ele almak guvenli defensif desen
        # (bkz. bu depodaki S110 icin ayni gerekce, pyproject.toml ignore).
        # Sessizce yutmuyoruz -- reward-hacking-check bekcisinin AST yolu
        # (yalniz gövdenin pass/.../salt-docstring olup olmadigina bakiyor)
        # yorum-kor oldugu icin, PR #72'de kurulan gercek desen (agents/
        # context/context_manager.py'deki logger.warning ile ayni) tekrar
        # kullanildi: gozlemlenebilirlik icin logla, davranisi degistirme.
        logger.debug(
            "constraint_exists: get_check_constraints('%s') basarisiz oldu, "
            "check constraint yok sayiliyor: %s",
            table_name,
            e,
        )

    return False


def safe_create_table(table_name: str, *columns: Any, **kwargs: Any) -> Any:
    """Safely create table only if it does not already exist."""
    bind = op.get_bind()
    if not table_exists(table_name, bind):
        return op.create_table(table_name, *columns, **kwargs)
    return None


def safe_drop_table(table_name: str, **kwargs: Any) -> None:
    """Safely drop table only if it exists."""
    bind = op.get_bind()
    if table_exists(table_name, bind):
        op.drop_table(table_name, **kwargs)


def safe_add_column(table_name: str, column: sa.Column, **kwargs: Any) -> None:
    """Safely add column only if it does not already exist."""
    bind = op.get_bind()
    if not column_exists(table_name, column.name, bind):
        op.add_column(table_name, column, **kwargs)


def safe_create_index(
    index_name: str, table_name: str, columns: list[str], **kwargs: Any
) -> None:
    """Safely create index only if table exists and index does not exist."""
    bind = op.get_bind()
    if table_exists(table_name, bind) and not index_exists(
        table_name, index_name, bind
    ):
        op.create_index(index_name, table_name, columns, **kwargs)


def safe_drop_index(index_name: str, table_name: str, **kwargs: Any) -> None:
    """Safely drop index only if it exists."""
    bind = op.get_bind()
    if index_exists(table_name, index_name, bind):
        op.drop_index(index_name, table_name=table_name, **kwargs)
