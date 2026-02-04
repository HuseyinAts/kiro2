# Database Migrations Guide - KIRO2

## Overview

Complete guide for managing database migrations with Alembic in the KIRO2 educational platform.

---

## Current Status

### Migration History

```
Initial → 60e185cfcca9 (unified_schema) → f822e22c28c6 (current)
```

### Database Schema

**Current Version:** `f822e22c28c6`
**Tables:** 15 tables
**Status:** ✅ Synchronized with models

#### Core Tables

1. **kullanicilar** (16 columns) - User accounts
2. **ogrenme_profilleri** (23 columns) - Learning profiles
3. **sorular** (27 columns) - Question bank
4. **sinavlar** (17 columns) - Exams
5. **sinav_sonuclari** (20 columns) - Exam results
6. **cozulen_sorular** (11 columns) - Student answers
7. **ogrenme_yollari** (19 columns) - Learning paths
8. **icerik_kaynaklari** (17 columns) - Content resources
9. **performans_analizleri** (17 columns) - Performance analytics
10. **cache_entries** (6 columns) - Cache storage
11. **user_sessions** (9 columns) - User sessions
12. **audit_logs** (9 columns) - System audit logs

#### Relationship Tables

13. **ogrenci_ogretmen** (2 columns) - Student-Teacher
14. **ogrenci_veli** (2 columns) - Student-Parent

---

## Quick Reference

### Common Commands

```bash
# Check current version
cd backend
py -m alembic current

# Show migration history
py -m alembic history --verbose

# Create new migration (auto-detect changes)
py -m alembic revision --autogenerate -m "Description"

# Create empty migration (manual)
py -m alembic revision -m "Description"

# Upgrade to latest
py -m alembic upgrade head

# Upgrade by 1 version
py -m alembic upgrade +1

# Downgrade by 1 version
py -m alembic downgrade -1

# Show current SQL (don't execute)
py -m alembic upgrade head --sql

# Stamp database to specific version (without running migrations)
py -m alembic stamp head
```

---

## Creating Migrations

### 1. Auto-Generate Migration

**When to use:** After changing SQLAlchemy models

```bash
# 1. Modify your models in models_unified.py
# Example: Add new column
class Kullanici(Base):
    # ... existing columns ...
    yeni_alan = Column(String(255))  # New field

# 2. Generate migration
cd backend
py -m alembic revision --autogenerate -m "Add yeni_alan to kullanicilar"

# 3. Review generated migration
# Check: alembic/versions/XXXXX_add_yeni_alan_to_kullanicilar.py

# 4. Apply migration
py -m alembic upgrade head
```

**Important:** Always review auto-generated migrations before applying!

---

### 2. Manual Migration

**When to use:** For complex changes, data migrations, or custom SQL

```bash
# Create empty migration
py -m alembic revision -m "Custom data migration"
```

Edit the generated file:

```python
"""Custom data migration

Revision ID: abc123
Revises: previous_version
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add your SQL/Python code here

    # Example: Add column with default
    op.add_column(
        'kullanicilar',
        sa.Column('yeni_alan', sa.String(255), nullable=True)
    )

    # Set default value for existing rows
    op.execute("""
        UPDATE kullanicilar
        SET yeni_alan = 'default_value'
        WHERE yeni_alan IS NULL
    """)

    # Make column non-nullable
    op.alter_column(
        'kullanicilar',
        'yeni_alan',
        nullable=False
    )

def downgrade() -> None:
    # Reverse the changes
    op.drop_column('kullanicilar', 'yeni_alan')
```

---

## Migration Examples

### Example 1: Add New Table

```python
def upgrade() -> None:
    op.create_table(
        'yeni_tablo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ad', sa.String(255), nullable=False),
        sa.Column('olusturma_tarihi', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Add index
    op.create_index(
        'idx_yeni_tablo_ad',
        'yeni_tablo',
        ['ad']
    )

def downgrade() -> None:
    op.drop_index('idx_yeni_tablo_ad', table_name='yeni_tablo')
    op.drop_table('yeni_tablo')
```

---

### Example 2: Add Column

```python
def upgrade() -> None:
    # Add nullable column first
    op.add_column(
        'kullanicilar',
        sa.Column('telefon', sa.String(20), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('kullanicilar', 'telefon')
```

---

### Example 3: Modify Column

```python
def upgrade() -> None:
    # Change column type
    op.alter_column(
        'kullanicilar',
        'email',
        type_=sa.String(320),  # Was 255
        existing_type=sa.String(255)
    )

def downgrade() -> None:
    op.alter_column(
        'kullanicilar',
        'email',
        type_=sa.String(255),
        existing_type=sa.String(320)
    )
```

---

### Example 4: Add Foreign Key

```python
def upgrade() -> None:
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_sinav_sonuclari_ogrenci',
        'sinav_sonuclari',
        'kullanicilar',
        ['ogrenci_id'],
        ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    op.drop_constraint(
        'fk_sinav_sonuclari_ogrenci',
        'sinav_sonuclari',
        type_='foreignkey'
    )
```

---

### Example 5: Add Index

```python
def upgrade() -> None:
    # Add index for performance
    op.create_index(
        'idx_sinav_sonuclari_puan',
        'sinav_sonuclari',
        ['puan'],
        postgresql_using='btree'
    )

    # Add composite index
    op.create_index(
        'idx_sinav_sonuclari_ogrenci_sinav',
        'sinav_sonuclari',
        ['ogrenci_id', 'sinav_id']
    )

def downgrade() -> None:
    op.drop_index('idx_sinav_sonuclari_ogrenci_sinav')
    op.drop_index('idx_sinav_sonuclari_puan')
```

---

### Example 6: Data Migration

```python
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # Define table for data operations
    kullanicilar = table(
        'kullanicilar',
        column('id', sa.Integer),
        column('rol', sa.String),
        column('yetki_seviyesi', sa.Integer)
    )

    # Update data
    op.execute(
        kullanicilar.update()
        .where(kullanicilar.c.rol == 'admin')
        .values(yetki_seviyesi=10)
    )

def downgrade() -> None:
    # Reverse data changes if possible
    pass
```

---

## Migration Workflow

### Development Environment

```bash
# 1. Pull latest code
git pull origin main

# 2. Check migration status
py -m alembic current

# 3. Apply any pending migrations
py -m alembic upgrade head

# 4. Make model changes
# Edit models_unified.py

# 5. Generate migration
py -m alembic revision --autogenerate -m "Your change description"

# 6. Review migration file
# Check alembic/versions/XXXXX_your_change.py

# 7. Test migration
py -m alembic upgrade head

# 8. Test downgrade
py -m alembic downgrade -1

# 9. Re-apply
py -m alembic upgrade head

# 10. Commit migration file
git add alembic/versions/XXXXX_your_change.py
git commit -m "Add migration: Your change description"
```

---

### Production Deployment

```bash
# 1. Backup database
pg_dump -U postgres -d turkiye_sinav_db > backup_$(date +%Y%m%d).sql

# 2. Check current version
py -m alembic current

# 3. Preview SQL (don't execute)
py -m alembic upgrade head --sql > migration.sql
# Review migration.sql

# 4. Apply migration
py -m alembic upgrade head

# 5. Verify
py -m alembic current

# 6. Test application
# Run smoke tests

# 7. Monitor for issues
# Check logs, error rates
```

---

## Troubleshooting

### Issue: "Target database is not up to date"

```bash
# Check current version
py -m alembic current

# Check migration history
py -m alembic history

# Stamp to correct version (if database is actually correct)
py -m alembic stamp head
```

---

### Issue: "Can't locate revision"

```bash
# This happens when migration files are missing

# Option 1: Restore missing migration files from git
git checkout main -- alembic/versions/

# Option 2: Stamp database to known good state
py -m alembic stamp <revision_id>
```

---

### Issue: Migration fails halfway

```bash
# 1. Check database state
# Connect to database and inspect

# 2. Manually fix if needed
# Run SQL to clean up

# 3. Stamp to correct version
py -m alembic stamp <last_good_revision>

# 4. Try again or create fix migration
py -m alembic revision -m "Fix previous migration"
```

---

### Issue: "Table already exists"

```bash
# Database has changes not in migrations

# Option 1: Drop and recreate (DEVELOPMENT ONLY!)
# WARNING: This deletes all data!
py -m alembic downgrade base
py -m alembic upgrade head

# Option 2: Stamp and continue (if schema matches)
py -m alembic stamp head
```

---

## Best Practices

### ✅ DO

1. **Always review auto-generated migrations**
```python
# Check for:
# - Correct column types
# - Nullable constraints
# - Default values
# - Index creation
```

2. **Add descriptive migration messages**
```bash
# ✅ GOOD
py -m alembic revision -m "Add email_verified column to kullanicilar"

# ❌ BAD
py -m alembic revision -m "changes"
```

3. **Test migrations on development database first**
```bash
# Create test database
createdb turkiye_sinav_db_test

# Test migration
DATABASE_URL=postgresql://postgres:postgres@localhost/turkiye_sinav_db_test \
  py -m alembic upgrade head
```

4. **Write reversible migrations**
```python
def upgrade():
    op.add_column('table', sa.Column('new_col', sa.String()))

def downgrade():
    op.drop_column('table', 'new_col')  # Always implement!
```

5. **Backup before production migrations**
```bash
pg_dump -U postgres turkiye_sinav_db > backup.sql
```

---

### ❌ DON'T

1. **Don't edit existing migrations**
```bash
# If migration is already applied, create new migration instead
```

2. **Don't skip migration testing**
```bash
# Always test upgrade AND downgrade
```

3. **Don't mix schema and data changes**
```bash
# Create separate migrations for:
# 1. Schema changes
# 2. Data migrations
```

4. **Don't delete migration files**
```bash
# Migration history must be preserved
```

5. **Don't run migrations manually in production**
```bash
# Use controlled deployment process
```

---

## Configuration

### alembic.ini

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/turkiye_sinav_db

# Template for file naming
file_template = %%(rev)s_%%(slug)s

# Logging
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
```

---

### env.py Configuration

Key settings in [alembic/env.py](alembic/env.py):

```python
from models_unified import Base

# Set target metadata
target_metadata = Base.metadata

# Configure context
def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect type changes
            compare_server_default=True  # Detect default changes
        )

        with context.begin_transaction():
            context.run_migrations()
```

---

## Migration Checklist

Before deploying a migration to production:

- [ ] Migration tested on development database
- [ ] Both upgrade() and downgrade() tested
- [ ] Migration file reviewed for correctness
- [ ] Database backup created
- [ ] Downtime window scheduled (if needed)
- [ ] Rollback plan prepared
- [ ] Team notified
- [ ] Monitoring alerts configured
- [ ] Post-migration tests ready

---

## Useful Queries

### Check Migration Status

```sql
-- Current version
SELECT version_num FROM alembic_version;

-- Table list
SELECT tablename FROM pg_tables
WHERE schemaname='public'
ORDER BY tablename;

-- Table structure
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'kullanicilar'
ORDER BY ordinal_position;

-- Indexes
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'sinav_sonuclari';

-- Foreign keys
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

---

## Migration Templates

### Template: Add Column

```python
"""Add <column_name> to <table_name>

Revision ID: XXXXX
"""

def upgrade() -> None:
    op.add_column(
        '<table_name>',
        sa.Column('<column_name>', sa.<Type>(), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('<table_name>', '<column_name>')
```

---

### Template: Create Table

```python
"""Create <table_name> table

Revision ID: XXXXX
"""

def upgrade() -> None:
    op.create_table(
        '<table_name>',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('<table_name>')
```

---

## Summary

### Current State

- ✅ Alembic configured
- ✅ Database versioned (f822e22c28c6)
- ✅ 15 tables in sync with models
- ✅ Migration history preserved

### Key Commands

```bash
# Status
py -m alembic current

# Create
py -m alembic revision --autogenerate -m "Description"

# Apply
py -m alembic upgrade head

# Revert
py -m alembic downgrade -1
```

### Next Steps

1. Create migrations for any future schema changes
2. Always test before production
3. Keep migration history in version control
4. Document complex migrations

---

**Last Updated:** 2025-10-02
**Current Version:** f822e22c28c6
**Author:** KIRO2 Development Team
