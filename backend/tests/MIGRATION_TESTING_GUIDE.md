# Migration Testing Guide - KIRO2

## Overview

Comprehensive Alembic migration test suite for the KIRO2 platform. Tests migration integrity, upgrade/downgrade cycles, and schema consistency.

## Test File

**Location**: `c:\Users\husey\kiro2\backend\tests\test_migrations.py`

## Prerequisites

1. **Database Connection**
   - PostgreSQL running on port **5434** (NOT 5432)
   - Set environment variable: `DATABASE_URL_SYNC=postgresql://user:pass@localhost:5434/kiro2`
   - Tests will skip gracefully if database is not available

2. **Environment Setup**
   ```bash
   # Set database URL
   export DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5434/kiro2"

   # Or for async
   export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5434/kiro2"
   ```

## Running Tests

### All Migration Tests

```bash
cd backend
pytest tests/test_migrations.py -v
```

### Specific Test Classes

```bash
# Test migration history integrity
pytest tests/test_migrations.py::TestMigrationHistory -v

# Test upgrade/downgrade cycles
pytest tests/test_migrations.py::TestMigrationUpgradeDowngrade -v

# Test schema consistency
pytest tests/test_migrations.py::TestSchemaAfterMigration -v

# Test downgrade safety
pytest tests/test_migrations.py::TestDowngradeSafety -v

# Test migration metadata
pytest tests/test_migrations.py::TestMigrationMetadata -v
```

### Individual Tests

```bash
# Test revision chain
pytest tests/test_migrations.py::TestMigrationHistory::test_revision_chain_no_gaps -v

# Test critical tables
pytest tests/test_migrations.py::TestSchemaAfterMigration::test_critical_tables_exist -v
```

## Test Coverage

### 1. Migration History Integrity (`TestMigrationHistory`)

- **test_revision_chain_no_gaps**: Validates no orphaned or missing revisions
- **test_no_duplicate_revisions**: Ensures unique revision IDs
- **test_single_head_revision**: Checks for unmerged branches
- **test_migrations_have_docstrings**: Ensures documentation

### 2. Upgrade/Downgrade Cycles (`TestMigrationUpgradeDowngrade`)

- **test_full_upgrade_downgrade_cycle**: Full migration cycle test
- **test_upgrade_idempotency**: Running upgrade twice doesn't break
- **test_stepwise_upgrade_downgrade**: Step-by-step migration validation

### 3. Schema Consistency (`TestSchemaAfterMigration`)

- **test_critical_tables_exist**: Validates core tables (users, questions, exam_sessions, student_progress)
- **test_users_table_structure**: Checks authentication columns
- **test_questions_table_structure**: Validates IRT parameters (difficulty, discrimination, guessing)
- **test_foreign_keys_exist**: Ensures referential integrity
- **test_indexes_created**: Performance index validation

### 4. Downgrade Safety (`TestDowngradeSafety`)

- **test_downgrade_preserves_base_schema**: Base schema integrity
- **test_partial_downgrade**: Middle revision downgrade

### 5. Migration Metadata (`TestMigrationMetadata`)

- **test_migration_naming_convention**: Naming standards
- **test_no_manual_table_drops_without_backup**: Data preservation warnings

## Critical Tables Validated

| Table | Purpose |
|-------|---------|
| `users` | Authentication and user management |
| `questions` | Question bank with IRT parameters |
| `exam_sessions` | Exam tracking |
| `student_progress` | Learning analytics |

## IRT Parameters Validated

KIRO2-specific IRT (Item Response Theory) parameters:

- **difficulty**: Range [-4.0, 4.0]
- **discrimination**: Range [0.2, 4.0]
- **guessing**: Range [0.0, 0.35]

## Performance Considerations

- All tests marked with `@pytest.mark.slow`
- Stepwise tests limited to first 5 migrations (configurable)
- Tests use clean database fixture for isolation

## Skipping Tests

Tests skip gracefully when:

1. **Database not available**: Skips with message about port 5434
2. **Insufficient migrations**: Partial downgrade test needs 3+ migrations
3. **Missing tables**: Schema tests skip if table doesn't exist

## Fixtures

### `alembic_config`
- Module-scoped
- Creates Alembic Config object
- Sets database URL to port 5434
- Skips if database unavailable

### `db_engine`
- Module-scoped
- Creates SQLAlchemy engine for validation
- Auto-disposes after module

### `clean_database`
- Function-scoped
- Drops `alembic_version` before/after each test
- Ensures clean state

## Example Output

```bash
$ pytest tests/test_migrations.py -v

tests/test_migrations.py::TestMigrationHistory::test_revision_chain_no_gaps PASSED
tests/test_migrations.py::TestMigrationHistory::test_no_duplicate_revisions PASSED
tests/test_migrations.py::TestMigrationHistory::test_single_head_revision PASSED
tests/test_migrations.py::TestMigrationUpgradeDowngrade::test_full_upgrade_downgrade_cycle PASSED
tests/test_migrations.py::TestSchemaAfterMigration::test_critical_tables_exist PASSED
tests/test_migrations.py::TestSchemaAfterMigration::test_questions_table_structure PASSED

========================== 6 passed in 45.32s ===========================
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running on port 5434
psql -h localhost -p 5434 -U postgres -d kiro2

# Verify environment variable
echo $DATABASE_URL_SYNC
```

### Migration Chain Issues

```bash
# Check for multiple heads
cd backend
alembic heads

# Merge branches
alembic merge <rev1> <rev2> -m "merge branches"
```

### Clean Database State

```bash
# Drop alembic_version manually
psql -h localhost -p 5434 -U postgres -d kiro2 -c "DROP TABLE IF EXISTS alembic_version CASCADE;"
```

## Integration with CI/CD

Add to `.github/workflows/backend-tests.yml`:

```yaml
- name: Run Migration Tests
  run: |
    cd backend
    pytest tests/test_migrations.py -v --tb=short
  env:
    DATABASE_URL_SYNC: postgresql://postgres:postgres@localhost:5434/kiro2_test
```

## Best Practices

1. **Run before creating new migrations**: Ensures chain integrity
2. **Run before merging PR**: Validates migration safety
3. **Run on database port 5434**: KIRO2 standard (NOT 5432)
4. **Check warnings**: Table drops without backup comments

## Reward Hacking Prevention

Tests follow Boris Cherny standards:

- **NO** `assert True` - All assertions are meaningful
- **NO** fake success patterns
- **NO** coverage manipulation
- All tests validate real migration behavior

## References

- Alembic docs: https://alembic.sqlalchemy.org/
- SQLAlchemy inspection: https://docs.sqlalchemy.org/en/14/core/inspection.html
- KIRO2 migration guide: `backend/alembic/README`
