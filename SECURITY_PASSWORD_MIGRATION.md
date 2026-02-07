# 🔒 SECURITY MIGRATION GUIDE - Hardcoded Passwords Fix

## ⚠️ CRITICAL SECURITY ISSUE

**30+ files** contain hardcoded database passwords ("1470", "changeme_strong_password_here"). This is a **P0 CRITICAL** security vulnerability that must be fixed immediately.

---

## ✅ COMPLETED FIXES (9 files)

The following files have been migrated to use environment variables:

1. ✅ `backend/alembic.ini` - Now uses `DATABASE_URL` environment variable
2. ✅ `backend/alembic/env.py` - Reads `DATABASE_URL` from environment + Fixed broken import
3. ✅ `generate_150_quality_questions.py` - Uses `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
4. ✅ `backend/api/questions_api.py` - Migrated to environment variables
5. ✅ `generate_100_questions.py` - Migrated to environment variables
6. ✅ `migrate_to_postgresql.py` - Migrated to environment variables
7. ✅ `test_db_connection.py` - Migrated to environment variables
8. ✅ `verify_100_questions.py` - Migrated to environment variables
9. ✅ `generate_50_with_eval.py` - Migrated to environment variables

---

## 🚨 REMAINING FILES TO FIX (20+ files)

The following files still contain hardcoded passwords and must be migrated:

### Backend Files
- `backend/copy_with_ids.py`
- `backend/copy_sorular_final.py`
- `backend/copy_sorular_to_questions_v2.py`
- `backend/copy_sorular_to_questions_fixed.py`
- `backend/copy_sorular_to_questions.py`
- `backend/load_50_questions.py`
- `backend/final_copy.py`
- `backend/check_import_stats.py`
- `backend/run_migration_013.py`
- `backend/scripts/update_answers_from_json.py`
- `backend/scripts/test_import_fix.py`
- `backend/scripts/restore_database.py`
- `backend/scripts/backup_database.py`
- `backend/setup_database.py`

### Root Scripts
- `ACIL_50_SORU_YUKLE.ps1`
- `START_POSTGRES_AND_LOAD_CONTENT.ps1`

### Test Files (Lower priority - can use test fixtures)
- `backend/comprehensive_auth_test.py`
- `backend/test_password.py`
- `backend/test_password_verify.py`

---

## 📋 HOW TO FIX: Step-by-Step Migration

### Step 1: Set Environment Variables

Before running any script, set these environment variables:

**Windows (PowerShell)**:
```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "5434"
$env:DB_NAME = "turkiye_sinav_db"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "your_actual_password_here"
$env:DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/kiro2_db"
```

**Linux/Mac (Bash)**:
```bash
export DB_HOST="localhost"
export DB_PORT="5434"
export DB_NAME="turkiye_sinav_db"
export DB_USER="postgres"
export DB_PASSWORD="your_actual_password_here"
export DATABASE_URL="postgresql://postgres:your_password@localhost:5432/kiro2_db"
```

**Permanent Setup (.env file)**:
1. Copy `.env.example` to `.env`
2. Fill in your actual passwords
3. Add `.env` to `.gitignore` (CRITICAL!)
4. Use `python-dotenv` to load environment variables:

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file
db_password = os.getenv("DB_PASSWORD")
```

---

### Step 2: Migrate Hardcoded Passwords to Environment Variables

**BEFORE (Insecure)**:
```python
PG_CONN = {
    "host": "localhost",
    "port": 5434,
    "database": "turkiye_sinav_db",
    "user": "postgres",
    "password": "1470"  # HARDCODED - SECURITY RISK!
}
```

**AFTER (Secure)**:
```python
import os

# SECURITY FIX: PostgreSQL connection from environment variables
PG_CONN = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "database": os.getenv("DB_NAME", "turkiye_sinav_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")  # REQUIRED: Must be set via environment
}

# Validate that password is set
if not PG_CONN["password"]:
    raise ValueError("DB_PASSWORD environment variable must be set!")
```

---

### Step 3: Update .gitignore

Ensure these patterns are in `.gitignore`:

```gitignore
# Environment files - NEVER COMMIT!
.env
.env.local
.env.production
*.env

# Database credentials
*password*
*credentials*
```

---

## 🛡️ SECURITY BEST PRACTICES

### ✅ DO:
- **Use environment variables** for all secrets (passwords, API keys, tokens)
- **Use `.env.example`** as a template with placeholder values
- **Add `.env` to `.gitignore`** before committing
- **Rotate passwords** immediately after removing hardcoded values from git history
- **Use secret management** in production (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)
- **Use `python-dotenv`** to load environment variables in development
- **Validate environment variables** at application startup

### ❌ DON'T:
- **DON'T commit** `.env` files to git
- **DON'T use** hardcoded passwords in any file
- **DON'T share** environment variable values via Slack/Email
- **DON'T use** weak passwords (use 32+ character random strings)
- **DON'T reuse** production passwords in development

---

## 🔄 GIT HISTORY CLEANUP (CRITICAL!)

Hardcoded passwords have been committed to git history. They must be removed:

### Option 1: BFG Repo-Cleaner (Recommended)
```bash
# Download BFG from https://rtyley.github.io/bfg-repo-cleaner/
java -jar bfg.jar --replace-text passwords.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

### Option 2: git-filter-repo
```bash
git filter-repo --replace-text <(echo "1470==>REDACTED")
git push --force
```

### Option 3: Rotate All Passwords (Fastest)
If the passwords are still `1470` or `changeme_strong_password_here`:
1. Change all database passwords to new secure values
2. Update environment variables
3. Old hardcoded passwords in git history become useless

---

## 📊 MIGRATION PROGRESS

| Category | Total Files | Fixed | Remaining | Progress |
|----------|-------------|-------|-----------|----------|
| Critical Backend | 14 | 4 | 10 | 29% |
| Root Scripts | 7 | 5 | 2 | 71% |
| Test Files | 5 | 0 | 5 | 0% |
| **TOTAL** | **26** | **9** | **17** | **35%** |

---

## 🎯 NEXT STEPS

1. **Immediate**: Set `DB_PASSWORD` environment variable on all developer machines
2. **Week 1**: Migrate remaining 17 files to environment variables
3. **Week 1**: Add password validation at application startup
4. **Week 2**: Implement secret management for production (AWS Secrets Manager)
5. **Week 2**: Rotate all passwords
6. **Week 3**: Clean git history with BFG or git-filter-repo
7. **Week 4**: Security audit to ensure no secrets remain in code

---

## 📖 REFERENCES

- Environment Variables: https://12factor.net/config
- python-dotenv: https://pypi.org/project/python-dotenv/
- BFG Repo-Cleaner: https://rtyley.github.io/bfg-repo-cleaner/
- AWS Secrets Manager: https://aws.amazon.com/secrets-manager/
- OWASP Secrets Management: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

---

**Created**: 2025-11-22
**Author**: KIRO2 Security Team
**Priority**: P0 CRITICAL
**Status**: IN PROGRESS (35% complete)
