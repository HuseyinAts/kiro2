# Design Document - Database Migration Doğrulama

## Architecture Overview

Alembic migration doğrulama sistemi. PreMigration hooks, dry run testing, schema consistency, data integrity validation ile %95 hata azaltma sağlar.

## Components

### 1. PreMigration Hook (app/db/hooks/pre_migration.py)
- **Purpose**: Migration öncesi validation
- **Dependencies**: alembic>=1.13.0, psycopg2>=2.9.9
- **Key Features**:
  - Schema backup (pg_dump)
  - SQL syntax validation
  - Dependency checking
  - Error reporting

### 2. Dry Run Tester (app/db/testing/dry_run.py)
- **Purpose**: Test ortamında migration deneme
- **Dependencies**: pytest>=7.4.0
- **Key Features**:
  - Test DB creation (production copy)
  - Upgrade/downgrade testing
  - Execution time tracking
  - Affected rows reporting

### 3. Schema Consistency Checker (app/db/validation/schema_checker.py)
- **Purpose**: SQLAlchemy model vs DB schema uyumu
- **Dependencies**: sqlalchemy>=2.0.0
- **Key Features**:
  - Table comparison
  - Column type/nullable/default checking
  - Index verification
  - Foreign key validation
  - Auto migration script generation

### 4. Data Integrity Validator (app/db/validation/integrity_validator.py)
- **Purpose**: Migration sonrası veri bütünlüğü
- **Dependencies**: asyncpg>=0.29.0
- **Key Features**:
  - Row count comparison
  - Orphaned record detection
  - Unique constraint validation
  - Not null constraint checking
  - Auto rollback on violation

### 5. Rollback Manager (app/db/rollback/manager.py)
- **Purpose**: Güvenli rollback
- **Dependencies**: alembic>=1.13.0
- **Key Features**:
  - Dry run before rollback
  - Data integrity check after rollback
  - Backup restore capability
  - Manual intervention detection

### 6. Migration History Tracker (app/db/history/tracker.py)
- **Purpose**: Migration geçmişi
- **Dependencies**: sqlalchemy>=2.0.0
- **Key Features**:
  - Revision tracking
  - Execution metrics
  - Error logging
  - Dependency graph
  - Audit reporting

### 7. Performance Analyzer (app/db/analysis/performance.py)
- **Purpose**: Migration performans etkisi
- **Dependencies**: asyncpg>=0.29.0
- **Key Features**:
  - EXPLAIN ANALYZE
  - Lock duration estimation
  - Migration time prediction
  - CONCURRENTLY recommendation
  - Downtime warning

### 8. CI/CD Integration (scripts/ci/test_migrations.py)
- **Purpose**: Pipeline'da otomatik test
- **Dependencies**: pytest>=7.4.0
- **Key Features**:
  - Clean DB initialization
  - Sequential migration testing
  - Downgrade testing
  - PR blocking on failure

## Correctness Properties

### Property 1: Backup Completeness
```python
@given(schema=st.text())
def test_backup_completeness(schema):
    backup = pre_migration_hook.create_backup(schema)
    assert backup.is_complete() and backup.is_valid()
```

### Property 2: Rollback Safety
```python
@given(migration=st.text())
def test_rollback_safety(migration):
    initial_state = get_schema_state()
    apply_migration(migration)
    rollback_migration(migration)
    final_state = get_schema_state()
    assert initial_state == final_state
```

### Property 3: Data Integrity Preservation
```python
@given(table=st.text())
def test_data_integrity(table):
    before_count = get_row_count(table)
    apply_migration()
    after_count = get_row_count(table)
    assert before_count == after_count
```

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Migration success rate | >= 99% | >= 95% |
| Rollback time | < 5s | < 10s |
| Dry run time | < 30s | < 60s |
| Backup time | < 2min | < 5min |

## Security Considerations

- Backup encryption
- Migration lock (Redis)
- Audit logging
- Access control

## Monitoring

- Migration success rate (%)
- Data loss incidents (count)
- Rollback success rate (%)
- Average migration time (s)
- Schema consistency (%)
