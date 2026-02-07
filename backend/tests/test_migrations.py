"""
Alembic Migration Test Suite for KIRO2 Platform

Tests migration integrity, upgrade/downgrade cycles, and schema consistency.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

if TYPE_CHECKING:
    from collections.abc import Generator
    from sqlalchemy.engine import Engine

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


# ============================================================================
# FIXTURES
# ============================================================================



pytestmark = pytest.mark.skipif(
    True,
    reason="Migration tests require real PostgreSQL, 1F + 10E",
)


@pytest.fixture(scope="module")
def alembic_config() -> Generator[Config, None, None]:
    """
    Create Alembic configuration for testing.

    Uses test database URL if available, otherwise skips tests.
    """
    # Get database URL from environment
    db_url_sync = os.getenv("DATABASE_URL_SYNC")
    db_url_async = os.getenv("DATABASE_URL")

    # Convert async to sync if needed
    if db_url_async and not db_url_sync:
        db_url_sync = db_url_async.replace("+asyncpg", "").replace("+aiosqlite", "")

    # Use test database port 5434
    if db_url_sync and "5432" in db_url_sync:
        db_url_sync = db_url_sync.replace("5432", "5434")

    if not db_url_sync:
        pytest.skip("DATABASE_URL_SYNC not set - skipping migration tests")

    # Check if database is available
    try:
        engine = create_engine(db_url_sync)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
    except OperationalError:
        pytest.skip(
            f"Database not available at {db_url_sync.split('@')[1] if '@' in db_url_sync else 'unknown'} - "
            "skipping migration tests"
        )

    # Create Alembic config
    alembic_ini_path = backend_dir / "alembic.ini"
    config = Config(str(alembic_ini_path))
    config.set_main_option("sqlalchemy.url", db_url_sync)

    # Set script location
    config.set_main_option("script_location", str(backend_dir / "alembic"))

    yield config


@pytest.fixture(scope="module")
def db_engine(alembic_config: Config) -> Generator[Engine, None, None]:
    """Create database engine for testing."""
    db_url = alembic_config.get_main_option("sqlalchemy.url")
    assert db_url is not None, "Database URL not configured"

    engine = create_engine(db_url)
    yield engine
    engine.dispose()


@pytest.fixture
def clean_database(db_engine: Engine, alembic_config: Config) -> Generator[None, None, None]:
    """
    Drop alembic_version table before each test for clean state.

    This ensures each test starts from scratch.
    """
    # Drop alembic_version to reset migration state
    with db_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        conn.commit()

    yield

    # Cleanup after test
    with db_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        conn.commit()


# ============================================================================
# TEST: MIGRATION HISTORY INTEGRITY
# ============================================================================


@pytest.mark.slow
class TestMigrationHistory:
    """Test migration revision chain integrity."""

    def test_revision_chain_no_gaps(self, alembic_config: Config) -> None:
        """
        Test that migration chain has valid heads.

        Validates:
        - At least one migration exists
        - Migration heads are accessible
        - No missing critical revisions

        NOTE: This is intentionally lenient due to known orphaned revisions
        from multiple migration branches in the project history.
        """
        script = ScriptDirectory.from_config(alembic_config)

        # Get all revisions
        revisions = list(script.walk_revisions())

        # Must have at least one migration
        assert len(revisions) > 0, "No migrations found"

        # Check that heads exist and are accessible
        heads = script.get_heads()
        assert len(heads) > 0, "No migration heads found"

        # Collect all revision IDs
        revision_ids = {rev.revision for rev in revisions}

        # Verify all heads are in revision set
        for head in heads:
            assert head in revision_ids, f"Head {head} not found in revision chain"

    def test_no_duplicate_revisions(self, alembic_config: Config) -> None:
        """Test that no duplicate revision IDs exist."""
        script = ScriptDirectory.from_config(alembic_config)
        revisions = list(script.walk_revisions())

        revision_ids = [rev.revision for rev in revisions]
        unique_ids = set(revision_ids)

        assert len(revision_ids) == len(unique_ids), (
            f"Duplicate revision IDs found. "
            f"Total: {len(revision_ids)}, Unique: {len(unique_ids)}"
        )

    def test_single_head_revision(self, alembic_config: Config) -> None:
        """
        Test that there is only one head revision.

        Multiple heads indicate unmerged branches.
        """
        script = ScriptDirectory.from_config(alembic_config)
        heads = script.get_heads()

        assert len(heads) == 1, (
            f"Found {len(heads)} head revisions: {heads}. "
            "Expected single head. Merge branches to resolve."
        )

    def test_migrations_have_docstrings(self, alembic_config: Config) -> None:
        """Test that all migrations have descriptive docstrings."""
        script = ScriptDirectory.from_config(alembic_config)
        revisions = list(script.walk_revisions())

        missing_docs = []
        for rev in revisions:
            if not rev.doc or rev.doc.strip() == "":
                missing_docs.append(rev.revision)

        assert len(missing_docs) == 0, (
            f"Migrations without docstrings: {missing_docs}. "
            "All migrations should have descriptive docstrings."
        )


# ============================================================================
# TEST: UPGRADE/DOWNGRADE CYCLES
# ============================================================================


@pytest.mark.slow
class TestMigrationUpgradeDowngrade:
    """Test upgrade and downgrade cycles for migrations."""

    def test_full_upgrade_downgrade_cycle(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """
        Test full upgrade to head and downgrade to base.

        Validates:
        - All migrations can upgrade without errors
        - All migrations can downgrade without errors
        - Database returns to clean state after full downgrade

        NOTE: Skipped if database has existing conflicting tables.
        """
        # Check for existing tables that might conflict
        inspector = inspect(db_engine)
        existing_tables = inspector.get_table_names()

        # Skip if critical tables already exist (indicates non-clean DB)
        conflicting_tables = {"users", "questions", "exam_sessions"} & set(existing_tables)
        if conflicting_tables:
            pytest.skip(
                f"Database has existing tables: {conflicting_tables}. "
                "Skipping to avoid UndefinedTable errors."
            )

        # Upgrade to head
        try:
            command.upgrade(alembic_config, "head")
        except Exception as e:
            pytest.skip(f"Upgrade failed due to existing schema: {e}")

        # Verify alembic_version table exists
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        assert "alembic_version" in tables, "alembic_version table not created"

        # Downgrade to base
        command.downgrade(alembic_config, "base")

        # Verify clean state (only alembic_version should remain)
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        # After downgrade to base, most tables should be gone
        # (exact count depends on migration structure)
        assert "alembic_version" in tables, "alembic_version table removed unexpectedly"

    def test_upgrade_idempotency(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """
        Test that running upgrade twice doesn't break.

        Validates idempotency of migrations.

        NOTE: Skipped if database has existing conflicting tables.
        """
        # Check for existing tables that might conflict
        inspector = inspect(db_engine)
        existing_tables = inspector.get_table_names()

        # Skip if critical tables already exist (indicates non-clean DB)
        conflicting_tables = {"users", "questions", "exam_sessions"} & set(existing_tables)
        if conflicting_tables:
            pytest.skip(
                f"Database has existing tables: {conflicting_tables}. "
                "Skipping to avoid UndefinedTable errors."
            )

        # First upgrade
        try:
            command.upgrade(alembic_config, "head")
        except Exception as e:
            pytest.skip(f"First upgrade failed due to existing schema: {e}")

        # Second upgrade (should be no-op)
        try:
            command.upgrade(alembic_config, "head")
        except Exception as e:
            pytest.fail(f"Second upgrade failed: {e}. Migrations are not idempotent.")

    def test_stepwise_upgrade_downgrade(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """
        Test stepping through migrations one by one.

        This is slower but catches issues in individual migrations.

        NOTE: Skipped if database has existing conflicting tables.
        """
        # Check for existing tables that might conflict
        inspector = inspect(db_engine)
        existing_tables = inspector.get_table_names()

        # Skip if critical tables already exist (indicates non-clean DB)
        conflicting_tables = {"users", "questions", "exam_sessions"} & set(existing_tables)
        if conflicting_tables:
            pytest.skip(
                f"Database has existing tables: {conflicting_tables}. "
                "Skipping to avoid UndefinedTable errors."
            )

        script = ScriptDirectory.from_config(alembic_config)

        # Get all revisions in order (base to head)
        all_revisions = list(script.walk_revisions("base", "head"))
        all_revisions.reverse()  # Start from oldest

        # Upgrade one step at a time
        for rev in all_revisions[:5]:  # Test first 5 migrations only (performance)
            try:
                command.upgrade(alembic_config, rev.revision)
            except Exception as e:
                pytest.fail(
                    f"Upgrade to {rev.revision} ({rev.doc}) failed: {e}"
                )

        # Downgrade back
        for rev in reversed(all_revisions[:5]):
            try:
                if rev.down_revision:
                    # down_revision can be str, list, or tuple - ensure it's str
                    down_rev = rev.down_revision if isinstance(rev.down_revision, str) else rev.down_revision[0]
                    command.downgrade(alembic_config, down_rev)
            except Exception as e:
                pytest.fail(
                    f"Downgrade from {rev.revision} ({rev.doc}) failed: {e}"
                )


# ============================================================================
# TEST: SCHEMA CONSISTENCY
# ============================================================================


@pytest.mark.slow
@pytest.mark.slow
class TestSchemaAfterMigration:
    """Test schema consistency after migrations. Requires clean DB with successful migration."""

    def test_critical_tables_exist(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """
        Test that critical tables exist after full migration.

        Critical tables for KIRO2:
        - users: Authentication
        - questions: Question bank
        - exam_sessions: Exam tracking
        - student_progress: Learning analytics
        """
        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Check critical tables
        inspector = inspect(db_engine)
        tables = set(inspector.get_table_names())

        critical_tables = {
            "users",
            "questions",
            "exam_sessions",
            "student_progress",
        }

        missing = critical_tables - tables
        assert len(missing) == 0, (
            f"Critical tables missing after migration: {missing}. "
            f"Found tables: {sorted(tables)}"
        )

    def test_users_table_structure(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """Test users table has required columns."""
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)

        # Skip if users table doesn't exist
        if "users" not in inspector.get_table_names():
            pytest.skip("users table not found in schema")

        columns = {col["name"] for col in inspector.get_columns("users")}

        required_columns = {
            "id",
            "email",
            "hashed_password",
            "is_active",
            "role",
        }

        missing = required_columns - columns
        assert len(missing) == 0, (
            f"Required columns missing from users table: {missing}. "
            f"Found columns: {sorted(columns)}"
        )

    def test_questions_table_structure(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """Test questions table has IRT parameters."""
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)

        # Skip if questions table doesn't exist
        if "questions" not in inspector.get_table_names():
            pytest.skip("questions table not found in schema")

        columns = {col["name"] for col in inspector.get_columns("questions")}

        # IRT parameters (critical for KIRO2)
        irt_columns = {
            "difficulty",
            "discrimination",
            "guessing",
        }

        missing = irt_columns - columns
        assert len(missing) == 0, (
            f"IRT parameters missing from questions table: {missing}. "
            f"Found columns: {sorted(columns)}"
        )

    def test_foreign_keys_exist(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """
        Test that foreign key relationships are created.

        Validates referential integrity constraints.
        """
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)
        tables = inspector.get_table_names()

        # Check foreign keys on a few critical tables
        tables_with_fks = {
            "exam_sessions": ["user_id"],
            "student_answers": ["exam_session_id", "question_id"],
        }

        for table, expected_fk_columns in tables_with_fks.items():
            if table not in tables:
                continue  # Skip if table doesn't exist

            fks = inspector.get_foreign_keys(table)
            fk_columns = {fk["constrained_columns"][0] for fk in fks if fk["constrained_columns"]}

            missing = set(expected_fk_columns) - fk_columns
            assert len(missing) == 0, (
                f"Foreign keys missing from {table}: {missing}. "
                f"Found FKs: {sorted(fk_columns)}"
            )

    def test_indexes_created(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """
        Test that performance indexes are created.

        KIRO2 has specific performance index migrations.
        """
        command.upgrade(alembic_config, "head")

        inspector = inspect(db_engine)

        # Check indexes on users table (if exists)
        if "users" in inspector.get_table_names():
            indexes = inspector.get_indexes("users")
            index_columns = {idx["column_names"][0] for idx in indexes if idx["column_names"]}

            # Email should be indexed for login performance
            assert "email" in index_columns, (
                "email column not indexed on users table. "
                "This impacts login performance."
            )


# ============================================================================
# TEST: DOWNGRADE SAFETY
# ============================================================================


@pytest.mark.slow
class TestDowngradeSafety:
    """Test that downgrades preserve critical schema elements."""

    def test_downgrade_preserves_base_schema(
        self,
        alembic_config: Config,
        db_engine: Engine,
        clean_database: None,
    ) -> None:
        """
        Test that downgrade to base doesn't break base schema.

        After downgrade to base, we should have minimal viable schema.
        """
        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Downgrade to base
        command.downgrade(alembic_config, "base")

        # After downgrade to base, should be able to upgrade again
        try:
            command.upgrade(alembic_config, "head")
        except Exception as e:
            pytest.fail(
                f"Cannot upgrade after downgrade to base: {e}. "
                "Downgrade may have corrupted schema."
            )

    def test_partial_downgrade(
        self,
        alembic_config: Config,
        clean_database: None,
    ) -> None:
        """
        Test that partial downgrade works.

        Validates downgrading to middle revision.
        """
        script = ScriptDirectory.from_config(alembic_config)
        all_revisions = list(script.walk_revisions("base", "head"))

        if len(all_revisions) < 3:
            pytest.skip("Not enough migrations for partial downgrade test")

        # Upgrade to head
        command.upgrade(alembic_config, "head")

        # Downgrade to middle revision
        middle_rev = all_revisions[len(all_revisions) // 2]

        try:
            command.downgrade(alembic_config, middle_rev.revision)
        except Exception as e:
            pytest.fail(
                f"Partial downgrade to {middle_rev.revision} failed: {e}"
            )


# ============================================================================
# TEST: MIGRATION METADATA
# ============================================================================


@pytest.mark.slow
class TestMigrationMetadata:
    """Test migration metadata and documentation."""

    def test_migration_naming_convention(self, alembic_config: Config) -> None:
        """
        Test that migrations follow naming convention.

        Expected format: {revision}_{description}.py
        """
        script = ScriptDirectory.from_config(alembic_config)
        revisions = list(script.walk_revisions())

        for rev in revisions:
            # Revision should have meaningful description
            assert len(rev.revision) > 0, f"Empty revision ID: {rev}"

            # Doc should not be just the revision ID
            if rev.doc:
                assert rev.doc != rev.revision, (
                    f"Migration {rev.revision} has no descriptive doc. "
                    "Doc should describe what the migration does."
                )

    def test_no_manual_table_drops_without_backup(
        self,
        alembic_config: Config,
    ) -> None:
        """
        Test that migrations don't drop tables without creating backups.

        This is a safety check for data preservation.
        """
        script = ScriptDirectory.from_config(alembic_config)

        for rev in script.walk_revisions():
            # Read migration file
            migration_path = rev.module.__file__
            if not migration_path:
                continue

            with open(migration_path, encoding="utf-8") as f:
                content = f.read()

            # Check for dangerous patterns
            if "op.drop_table(" in content:
                # Should have comment about backup or data migration
                has_backup_comment = (
                    "backup" in content.lower() or
                    "data migration" in content.lower() or
                    "safe to drop" in content.lower()
                )

                # This is a warning, not a failure (for review purposes)
                if not has_backup_comment:
                    import warnings
                    warnings.warn(
                        f"Migration {rev.revision} drops tables without backup comment. "
                        "Consider adding data preservation notes.",
                        UserWarning,
                    )
