"""
Database Migration Tests (DB-01 + DB-02)
Türkiye Üniversite Sınavları Hazırlık Platformu

Tests cover:
- Alembic configuration validation
- Migration file existence and structure
- Migration function presence (upgrade/downgrade)
- Revision chain integrity
- Async support in env.py
- Import validation
- Critical migration existence (cascade deletes)
"""

import ast
import sys
from pathlib import Path
from typing import List, Set

import pytest


@pytest.fixture
def backend_root() -> Path:
    """Get backend root directory."""
    current_file = Path(__file__).resolve()
    # Navigate up: test_migrations.py -> db -> tests -> backend
    return current_file.parent.parent.parent


@pytest.fixture
def alembic_dir(backend_root: Path) -> Path:
    """Get alembic directory."""
    return backend_root / "alembic"


@pytest.fixture
def alembic_versions_dir(alembic_dir: Path) -> Path:
    """Get alembic versions directory."""
    return alembic_dir / "versions"


@pytest.fixture
def migration_files(alembic_versions_dir: Path) -> List[Path]:
    """Get all migration files."""
    if not alembic_versions_dir.exists():
        return []
    return [
        f
        for f in alembic_versions_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.endswith(".pyc")
    ]


def test_alembic_config_exists(backend_root: Path) -> None:
    """Test that alembic.ini configuration file exists."""
    alembic_ini = backend_root / "alembic.ini"
    assert alembic_ini.exists(), "alembic.ini file must exist in backend directory"
    assert alembic_ini.is_file(), "alembic.ini must be a file"

    # Verify it's readable and has content
    content = alembic_ini.read_text(encoding="utf-8")
    assert len(content) > 0, "alembic.ini must not be empty"
    assert "[alembic]" in content, "alembic.ini must contain [alembic] section"


def test_migration_files_exist(migration_files: List[Path]) -> None:
    """Test that at least 3 migration files exist in versions directory."""
    assert (
        len(migration_files) >= 3
    ), f"Expected at least 3 migration files, found {len(migration_files)}"

    # Verify files have .py extension
    for migration_file in migration_files:
        assert migration_file.suffix == ".py", f"{migration_file.name} must be a .py file"


def test_migration_has_upgrade_function(migration_files: List[Path]) -> None:
    """Test that each migration file has an upgrade() function."""
    for migration_file in migration_files:
        content = migration_file.read_text(encoding="utf-8")

        # Parse the Python file
        try:
            tree = ast.parse(content, filename=str(migration_file))
        except SyntaxError as e:
            pytest.fail(f"Migration file {migration_file.name} has syntax error: {e}")

        # Find all function definitions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        assert (
            "upgrade" in functions
        ), f"Migration {migration_file.name} must have upgrade() function"


def test_migration_has_downgrade_function(migration_files: List[Path]) -> None:
    """Test that each migration file has a downgrade() function."""
    for migration_file in migration_files:
        content = migration_file.read_text(encoding="utf-8")

        # Parse the Python file
        try:
            tree = ast.parse(content, filename=str(migration_file))
        except SyntaxError as e:
            pytest.fail(f"Migration file {migration_file.name} has syntax error: {e}")

        # Find all function definitions
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        assert (
            "downgrade" in functions
        ), f"Migration {migration_file.name} must have downgrade() function"


def test_migration_revision_chain(migration_files: List[Path]) -> None:
    """Test that migration revision IDs are unique (no duplicates in chain)."""
    revisions: Set[str] = set()
    duplicate_revisions: List[str] = []

    for migration_file in migration_files:
        content = migration_file.read_text(encoding="utf-8")

        # Extract revision ID using regex-like pattern
        for line in content.split("\n"):
            if line.strip().startswith("revision:"):
                # Extract revision ID
                # Format: revision: str = "abc123def456"
                parts = line.split("=")
                if len(parts) >= 2:
                    revision_id = parts[1].strip().strip('"').strip("'")
                    if revision_id in revisions:
                        duplicate_revisions.append(
                            f"{migration_file.name}: {revision_id}"
                        )
                    revisions.add(revision_id)
                break

    assert (
        len(duplicate_revisions) == 0
    ), f"Found duplicate revision IDs: {', '.join(duplicate_revisions)}"


def test_env_py_has_async_support(alembic_dir: Path) -> None:
    """Test that alembic/env.py has async migration support."""
    env_file = alembic_dir / "env.py"

    assert env_file.exists(), "alembic/env.py must exist"

    content = env_file.read_text(encoding="utf-8")

    # Check for async-related imports, functions, or async driver handling
    # env.py may use asyncpg driver conversion or explicit async functions
    has_async_support = (
        "run_async_migrations" in content
        or "asyncio" in content
        or "async def" in content
        or "asyncpg" in content
        or "aiosqlite" in content
    )

    assert (
        has_async_support
    ), "alembic/env.py must have async migration support (async functions or async driver handling)"


def test_migration_imports_valid(
    migration_files: List[Path], backend_root: Path
) -> None:
    """Test that each migration can be imported without syntax errors."""
    # Add backend to sys.path for imports
    sys.path.insert(0, str(backend_root))

    errors: List[str] = []

    for migration_file in migration_files:
        # Skip disabled migrations
        if migration_file.name.endswith(".disabled"):
            continue

        try:
            # Parse the file to check for syntax errors
            content = migration_file.read_text(encoding="utf-8")
            ast.parse(content, filename=str(migration_file))
        except SyntaxError as e:
            errors.append(f"{migration_file.name}: {e}")
        except Exception as e:
            # Other parsing errors
            errors.append(f"{migration_file.name}: Unexpected error - {e}")

    assert (
        len(errors) == 0
    ), "Migration files have import/syntax errors:\n" + "\n".join(errors)


def test_cascade_migration_exists(alembic_versions_dir: Path) -> None:
    """Test that the cascade delete migration (4aec28c6c9e0) exists."""
    cascade_migration = alembic_versions_dir / "4aec28c6c9e0_add_cascade_deletes_to_foreign_keys.py"

    assert (
        cascade_migration.exists()
    ), "Cascade delete migration (4aec28c6c9e0_add_cascade_deletes_to_foreign_keys.py) must exist"

    # Verify it has the correct revision ID
    content = cascade_migration.read_text(encoding="utf-8")
    assert (
        '4aec28c6c9e0' in content
    ), "Cascade migration must have revision ID 4aec28c6c9e0"
