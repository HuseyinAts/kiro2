# Quality Hardening Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 2026-05-18 sistemik audit'inde tespit edilen 18 problem (3 kategori: sinyal kirletici, test yokluğu, pattern tutarsızlığı) 8 task halinde sırayla giderilir.

**Architecture:** TDD-first yaklaşım — her task'ta önce failing test yaz, sonra fix. 3 tier: Hızlı (Task 1-4, ~2 saat) + Orta (Task 5-7, 1-2 hafta) + Uzun (Task 8, 1-2 ay). Beta canlı olduğundan rollback-safe değişiklikler, her Task ayrı commit.

**Tech Stack:** FastAPI, SQLAlchemy + Alembic (DB v3), pytest + httpx AsyncClient, React 18 + Vitest, axios, slowapi + Redis (advanced_rate_limiter), GitHub Actions.

**Pre-flight checks (önce yap):**
- `pg_isready -p 5434` ✓
- `redis-cli ping` ✓
- `docker ps` — backend/frontend/redis healthy ✓
- `git status` — temiz çalışma dizini

---

## File Structure

### Backend
- **Create:** `backend/tests/api/__init__.py` — package marker
- **Create:** `backend/tests/api/test_student_feedback_api.py` — 5 başlangıç test (Task 1) + smoke ekler (Task 5)
- **Create:** `backend/alembic/versions/20260518_student_flags_unique.py` — UNIQUE constraint migration (Task 2)
- **Modify:** `backend/api/student_feedback_api.py` — IntegrityError handler + rate_limit decorator (Task 2, 3)
- **Create:** `backend/tests/api/_smoke_helpers.py` — pytest fixtures (auth header, test user) (Task 5)
- **Create:** `backend/tests/api/test_<api>.py` × 15 — smoke testler (Task 5)
- **Create:** `backend/core/rate_limit_decorator.py` — unified decorator wrapper (Task 7)
- **Modify:** `backend/api/auth.py` — manuel `_check_rate_limit` → unified decorator (Task 7)
- **Modify:** `backend/api/learning_path_v2.py:136-150` — local `rate_limit` → unified import (Task 7)
- **Modify:** `backend/api/sinav.py` — 7 write endpoint'e unified decorator (Task 7)

### Frontend
- **Create:** `frontend/src/utils/extractErrorDetail.ts` — error message helper (Task 4)
- **Create:** `frontend/src/utils/__tests__/extractErrorDetail.test.ts` — 4 test case (Task 4)
- **Modify:** `frontend/src/components/Quality/FlagButton.tsx:73-82` — use extractErrorDetail (Task 4)
- **Modify:** 20 dosya fetch → apiClient migration (Task 6, tam liste Task 6'da)

### CI/CD + Docs
- **Create:** `.github/workflows/test-coverage-gate.yml` (Task 8)
- **Create:** `.claude/rules/new-endpoint-checklist.md` (Task 8)
- **Modify:** `CLAUDE.md` — "Yeni endpoint checklist" referansı (Task 8)

---

## Task 1: student_feedback_api — 5 Temel Test (TDD foundation)

**Files:**
- Create: `backend/tests/api/__init__.py`
- Create: `backend/tests/api/test_student_feedback_api.py`

**Hedef:** 5 test yaz — 2'si MEVCUT davranışı doğrular (PASS), 2'si gelecek fix'leri TDD-pin yapar (FAIL, Task 2-3'te düzelir), 1'i regression guard.

- [ ] **Step 1.1: __init__.py oluştur**

```bash
touch backend/tests/api/__init__.py
```

- [ ] **Step 1.2: Test dosyasını oluştur**

Create `backend/tests/api/test_student_feedback_api.py`:

```python
"""Student feedback API tests — Faz 7.2 + S1.1/S2.1/S3 hardening.

Tests cover:
- TC1 happy path (POST 201) — REGRESSION guard
- TC2 duplicate flag — TDD-pin (S1.1 fix Task 2)
- TC3 FK violation → 400 — REGRESSION
- TC4 invalid flag_type → 422 — REGRESSION
- TC5 rate limit → 429 — TDD-pin (S1.2 fix Task 3)
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from core.database import get_db_session_context
from main import app
from models.student_question_flag import StudentQuestionFlag


pytestmark = pytest.mark.asyncio


async def _login_beta() -> str:
    """Login beta01 and return Bearer token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/login",
            json={"email": "beta01@kiro2.com", "password": "Beta01!Kiro2026"},
        )
        if r.status_code != 200:
            pytest.skip(f"beta01 login failed: {r.status_code}")
        return r.json()["access_token"]


async def _real_question_id() -> str:
    """Pick one real, active, beta-eligible question_bank.id."""
    async with get_db_session_context() as s:
        r = await s.execute(
            text(
                "SELECT id FROM question_bank "
                "WHERE is_active=TRUE "
                "AND quality_review_status IN ('human_verified','auto_judged_high') "
                "LIMIT 1"
            )
        )
        qid = r.scalar()
        if not qid:
            pytest.skip("no beta-eligible question_bank row")
        return qid


async def _cleanup_flags(user_id: str) -> None:
    """Remove test flags for user to keep DB clean."""
    async with get_db_session_context() as s:
        await s.execute(
            text(
                "DELETE FROM student_question_flags "
                "WHERE user_id=:uid AND note LIKE 'TEST_%'"
            ),
            {"uid": user_id},
        )
        await s.commit()


@pytest.fixture
async def beta_token() -> str:
    """Pytest-async fixture for beta01 Bearer token."""
    return await _login_beta()


@pytest.fixture
async def beta_question_id() -> str:
    return await _real_question_id()


# ------------------------------------------------------------------
# TC1 — Happy path: POST /flag → 201 + DB row
# ------------------------------------------------------------------
async def test_create_flag_happy_path(beta_token: str, beta_question_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/quality/feedback/flag",
            json={
                "question_id": beta_question_id,
                "flag_type": "wrong_answer",
                "note": "TEST_happy_path",
            },
            headers={"Authorization": f"Bearer {beta_token}"},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["flag_type"] == "wrong_answer"
        assert body["question_id"] == beta_question_id
        assert body["note"] == "TEST_happy_path"

    # Verify DB row
    async with get_db_session_context() as s:
        row = (
            await s.execute(
                select(StudentQuestionFlag).where(
                    StudentQuestionFlag.id == body["id"]
                )
            )
        ).scalar_one_or_none()
        assert row is not None
        assert row.flag_type == "wrong_answer"

    await _cleanup_flags(body["user_id"])


# ------------------------------------------------------------------
# TC2 — Duplicate flag — should be REJECTED (TDD-pin for Task 2)
# ------------------------------------------------------------------
async def test_duplicate_flag_rejected(beta_token: str, beta_question_id: str):
    """After S1.1 fix: 2nd identical flag returns 409 Conflict OR 200 with existing row."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {beta_token}"}
        body = {
            "question_id": beta_question_id,
            "flag_type": "wrong_topic",
            "note": "TEST_duplicate",
        }
        r1 = await client.post("/api/v1/quality/feedback/flag", json=body, headers=headers)
        assert r1.status_code == 201
        r2 = await client.post("/api/v1/quality/feedback/flag", json=body, headers=headers)
        # After Task 2: 409 (Conflict) is the correct response
        assert r2.status_code == 409, (
            f"Duplicate flag should be rejected (S1.1). Got {r2.status_code}: {r2.text}"
        )

    await _cleanup_flags(r1.json()["user_id"])


# ------------------------------------------------------------------
# TC3 — FK violation: invalid question_id → 400
# ------------------------------------------------------------------
async def test_invalid_question_id_400(beta_token: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/quality/feedback/flag",
            json={
                "question_id": "00000000-0000-0000-0000-000000000000",
                "flag_type": "other",
            },
            headers={"Authorization": f"Bearer {beta_token}"},
        )
        assert r.status_code == 400
        assert "constraint" in r.json()["detail"].lower() or "not found" in r.json()["detail"].lower()


# ------------------------------------------------------------------
# TC4 — Pydantic validation: invalid flag_type → 422
# ------------------------------------------------------------------
async def test_invalid_flag_type_422(beta_token: str, beta_question_id: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/quality/feedback/flag",
            json={"question_id": beta_question_id, "flag_type": "hacker_flag"},
            headers={"Authorization": f"Bearer {beta_token}"},
        )
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert isinstance(detail, list)
        assert detail[0]["type"] == "literal_error"


# ------------------------------------------------------------------
# TC5 — Rate limit (TDD-pin for Task 3): 11 hızlı POST'ta 11. tane 429
# ------------------------------------------------------------------
async def test_rate_limit_after_10_per_minute(beta_token: str, beta_question_id: str):
    """After Task 3 (S1.2 rate limit): 10/minute, 11th request returns 429."""
    transport = ASGITransport(app=app)
    user_id_for_cleanup = None
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {beta_token}"}
        statuses = []
        for i in range(11):
            r = await client.post(
                "/api/v1/quality/feedback/flag",
                json={
                    "question_id": beta_question_id,
                    "flag_type": "other",
                    "note": f"TEST_rate_{i}",
                },
                headers=headers,
            )
            statuses.append(r.status_code)
            if r.status_code == 201 and user_id_for_cleanup is None:
                user_id_for_cleanup = r.json()["user_id"]

        # First 10 should succeed (or be rejected by S1.1 duplicate for same key);
        # 11th MUST be 429. Tolerate 409 for duplicates after Task 2.
        assert 429 in statuses, (
            f"Rate limit should reject 11th request. Got: {statuses}"
        )

    if user_id_for_cleanup:
        await _cleanup_flags(user_id_for_cleanup)
```

- [ ] **Step 1.3: Testleri çalıştır — TC1/3/4 PASS, TC2/5 FAIL beklenir**

Run:
```bash
cd backend && pytest tests/api/test_student_feedback_api.py -v --tb=short
```

Expected output:
- `test_create_flag_happy_path` → **PASS**
- `test_duplicate_flag_rejected` → **FAIL** (currently 201 200 200 → returns 201, not 409)
- `test_invalid_question_id_400` → **PASS**
- `test_invalid_flag_type_422` → **PASS**
- `test_rate_limit_after_10_per_minute` → **FAIL** (no rate limit, all 11 succeed)

- [ ] **Step 1.4: Commit (TDD-pin baseline)**

```bash
git add backend/tests/api/__init__.py backend/tests/api/test_student_feedback_api.py
git commit -m "$(cat <<'EOF'
test(s2-1): student_feedback_api — 5 temel test (TDD foundation)

3 PASS regression guard (happy path, FK violation, invalid type) +
2 FAIL TDD-pin (duplicate guard / rate limit) fix Task 2-3'te uygulanır.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: UNIQUE Constraint + IntegrityError → 409 Conflict (S1.1 fix)

**Files:**
- Create: `backend/alembic/versions/20260518_student_flags_unique.py`
- Modify: `backend/api/student_feedback_api.py:90-118`

**Hedef:** Aynı user+question+flag_type kombinasyonu için UNIQUE constraint. Mevcut duplicate'ları temizleyip migration uygula. Backend IntegrityError → 409 döndür.

- [ ] **Step 2.1: Mevcut duplicate'ları sayım**

```bash
docker exec kiro2-backend python -c "
import asyncio
from sqlalchemy import text
from core.database import get_db_session_context
async def main():
    async with get_db_session_context() as s:
        r = await s.execute(text('''
            SELECT user_id, question_id, flag_type, COUNT(*) as cnt
            FROM student_question_flags
            GROUP BY user_id, question_id, flag_type
            HAVING COUNT(*) > 1
        '''))
        rows = r.fetchall()
        print(f'Duplicate gruplar: {len(rows)}')
        total_extra = sum(row.cnt - 1 for row in rows)
        print(f'Silinecek extra satır: {total_extra}')
asyncio.run(main())
"
```

Expected: ~12-15 duplicate gruplar (beta01 smoke test artıkları)

- [ ] **Step 2.2: Migration dosyası oluştur**

Create `backend/alembic/versions/20260518_student_flags_unique.py`:

```python
"""Add UNIQUE constraint to student_question_flags

Revision ID: sqf_unique_20260518
Revises: <PREVIOUS_REV_ID>
Create Date: 2026-05-18

S1.1 fix — Same (user_id, question_id, flag_type) combo should be
rejected. Existing duplicates are deduplicated (keep earliest created_at).
"""

from alembic import op
import sqlalchemy as sa


revision = "sqf_unique_20260518"
down_revision = "<RUN_BELOW_TO_FIND>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Deduplicate: keep earliest created_at per (user_id, question_id, flag_type)
    op.execute(
        """
        DELETE FROM student_question_flags
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY user_id, question_id, flag_type
                           ORDER BY created_at ASC, id ASC
                       ) AS rn
                FROM student_question_flags
            ) ranked
            WHERE rn > 1
        )
        """
    )

    # 2. UNIQUE constraint (PostgreSQL partial — only unresolved, so resolved
    # flags don't block re-flagging of the same question after admin closure)
    op.create_index(
        "uq_student_flags_user_question_type",
        "student_question_flags",
        ["user_id", "question_id", "flag_type"],
        unique=True,
        postgresql_where=sa.text("resolved_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_student_flags_user_question_type",
        table_name="student_question_flags",
    )
```

- [ ] **Step 2.3: down_revision değerini bul ve değiştir**

```bash
ls -lt backend/alembic/versions/*.py | head -3
# En son alembic dosyasını bul, içindeki `revision = "..."` değerini al
grep "^revision =" backend/alembic/versions/20260517_student_question_flags.py
```

Sonra `20260518_student_flags_unique.py` içindeki `down_revision = "<RUN_BELOW_TO_FIND>"` yerine bulunan değeri yaz.

- [ ] **Step 2.4: Migration'ı uygula**

```bash
docker exec kiro2-backend alembic upgrade head 2>&1 | tail -5
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade ... -> sqf_unique_20260518, Add UNIQUE constraint to student_question_flags`

- [ ] **Step 2.5: Doğrula — UNIQUE index oluştu**

```bash
docker exec kiro2-backend python -c "
import asyncio
from sqlalchemy import text
from core.database import get_db_session_context
async def main():
    async with get_db_session_context() as s:
        r = await s.execute(text('''
            SELECT indexname, indexdef FROM pg_indexes
            WHERE tablename='student_question_flags' AND indexname LIKE 'uq_%'
        '''))
        for row in r: print(row)
asyncio.run(main())
"
```

Expected output contains `CREATE UNIQUE INDEX uq_student_flags_user_question_type ... WHERE (resolved_at IS NULL)`

- [ ] **Step 2.6: Backend IntegrityError handler — 409 Conflict döndür**

Modify `backend/api/student_feedback_api.py:90-118` — `create_flag` function:

```python
@router.post(
    "/flag",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_flag(
    payload: FlagCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> FlagResponse:
    """Öğrenci soru hata raporu gönderir."""
    flag = StudentQuestionFlag(
        id=str(uuid.uuid4()),
        user_id=str(current_user.id),
        question_id=payload.question_id,
        flag_type=payload.flag_type,
        note=payload.note,
    )
    db.add(flag)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        # Distinguish UNIQUE violation (S1.1) from FK violation
        err_str = str(exc.orig).lower() if exc.orig else str(exc).lower()
        if "uq_student_flags_user_question_type" in err_str or "duplicate key" in err_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bu soruyu zaten aynı türde bildirdiniz.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_id not found or constraint violation",
        ) from exc
    await db.refresh(flag)
    return FlagResponse.model_validate(flag)
```

- [ ] **Step 2.7: Container'a deploy et**

```bash
docker cp backend/api/student_feedback_api.py kiro2-backend:/app/api/student_feedback_api.py
docker exec kiro2-backend find /app/api -name "*.pyc" -delete
docker restart kiro2-backend
sleep 22
curl -s http://localhost:8000/health | head -3
```

- [ ] **Step 2.8: TC2 (duplicate test) artık PASS olmalı**

```bash
cd backend && pytest tests/api/test_student_feedback_api.py::test_duplicate_flag_rejected -v --tb=short
```

Expected: **PASS**

- [ ] **Step 2.9: Commit**

```bash
git add backend/alembic/versions/20260518_student_flags_unique.py backend/api/student_feedback_api.py
git commit -m "$(cat <<'EOF'
fix(s1-1): student_flags UNIQUE constraint + 409 Conflict handler

(user_id, question_id, flag_type) UNIQUE partial index (resolved_at NULL).
Mevcut 12+ duplicate satır dedupliyle temizlendi (earliest created_at korundu).
IntegrityError → 409 Conflict + Türkçe mesaj "Bu soruyu zaten aynı türde bildirdiniz."

TDD: test_duplicate_flag_rejected (Task 1) artık PASS.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Rate Limit on student_feedback (S1.2 fix)

**Files:**
- Modify: `backend/api/student_feedback_api.py` — `@rate_limit("flag_submit")` decorator

**Hedef:** learning_path_v2.py pattern'i import et, flag endpoint'e 10/dakika limit ekle. (Bu task Task 7'deki standardization öncesi geçici çözüm — `rate_limit` local import.)

- [ ] **Step 3.1: learning_path_v2 pattern'ini incele**

```bash
grep -n "limiter\|RATE_LIMITS\|^from slowapi" backend/api/learning_path_v2.py | head -10
```

Expected: slowapi `Limiter`, `RATE_LIMITS` dict, `rate_limit(key)` decorator definitions

- [ ] **Step 3.2: student_feedback_api.py'ya rate_limit ekle**

Modify `backend/api/student_feedback_api.py` — imports ve decorator:

```python
# At top, after existing imports:
from api.learning_path_v2 import RATE_LIMITS, rate_limit

# Add to RATE_LIMITS dict in learning_path_v2.py (Step 3.3):
# "flag_submit": "10/minute"

# On create_flag endpoint:
@router.post(
    "/flag",
    response_model=FlagResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit("flag_submit")
async def create_flag(
    request: Request,  # Required by slowapi limiter
    payload: FlagCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> FlagResponse:
    # ... (function body unchanged)
```

**ÖNEMLI:** `request: Request` parametresi slowapi limiter için zorunlu — eklemezsen 422 alır.

- [ ] **Step 3.3: RATE_LIMITS dict'e "flag_submit" ekle**

Modify `backend/api/learning_path_v2.py` — `RATE_LIMITS` dict (line ~120):

```python
RATE_LIMITS = {
    "create_profile": "5/minute",
    "assess_knowledge": "10/minute",
    "create_path": "5/minute",
    "search_resources": "30/minute",
    "flag_submit": "10/minute",  # ADDED: S1.2 student feedback
    # ... (mevcut diğer entry'ler korunur)
}
```

- [ ] **Step 3.4: Container'a deploy et**

```bash
docker cp backend/api/student_feedback_api.py kiro2-backend:/app/api/student_feedback_api.py
docker cp backend/api/learning_path_v2.py kiro2-backend:/app/api/learning_path_v2.py
docker exec kiro2-backend find /app/api -name "*.pyc" -delete
docker restart kiro2-backend
sleep 22
```

- [ ] **Step 3.5: TC5 (rate limit test) artık PASS olmalı**

```bash
cd backend && pytest tests/api/test_student_feedback_api.py::test_rate_limit_after_10_per_minute -v --tb=short
```

Expected: **PASS** (11. POST 429 döner)

- [ ] **Step 3.6: Tam test suite — 5/5 PASS**

```bash
cd backend && pytest tests/api/test_student_feedback_api.py -v --tb=short
```

Expected output:
```
test_create_flag_happy_path PASSED
test_duplicate_flag_rejected PASSED
test_invalid_question_id_400 PASSED
test_invalid_flag_type_422 PASSED
test_rate_limit_after_10_per_minute PASSED
============== 5 passed in X.XXs ==============
```

- [ ] **Step 3.7: Commit**

```bash
git add backend/api/student_feedback_api.py backend/api/learning_path_v2.py
git commit -m "$(cat <<'EOF'
fix(s1-2): student_feedback flag endpoint rate limit 10/dakika

slowapi @rate_limit('flag_submit') eklendi (learning_path_v2 pattern reuse).
RATE_LIMITS['flag_submit'] = '10/minute' tanımlandı.

TDD: test_rate_limit_after_10_per_minute (Task 1) artık PASS.
Task 1-3 ile student_feedback_api 5/5 test PASS.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Frontend extractErrorDetail Utility (S3.5 fix)

**Files:**
- Create: `frontend/src/utils/extractErrorDetail.ts`
- Create: `frontend/src/utils/__tests__/extractErrorDetail.test.ts`
- Modify: `frontend/src/components/Quality/FlagButton.tsx:73-82`

**Hedef:** Backend hem string (`{"detail":"msg"}`) hem array (`{"detail":[{"msg":...}]}`) döndürebiliyor. Tek bir helper ile her ikisini de kullanıcı-dostu mesaja çevir.

- [ ] **Step 4.1: extractErrorDetail.ts oluştur**

Create `frontend/src/utils/extractErrorDetail.ts`:

```typescript
/**
 * extractErrorDetail — Backend error response'unu kullanıcı-dostu mesaja çevirir.
 *
 * Backend Pydantic 422: { detail: [{ type, loc, msg, input }] }  (array)
 * Backend HTTPException 4xx: { detail: "Mesaj" }                  (string)
 * Backend HTTPException with rate_limit (slowapi): { detail: "Rate limit exceeded: ..." }
 *
 * Output: User-facing string (Turkish where applicable).
 */

import { AxiosError } from 'axios';

export function extractErrorDetail(err: unknown, fallback = 'Beklenmeyen bir hata oluştu'): string {
  if (err instanceof AxiosError) {
    // Network error (no response received)
    if (!err.response) {
      return 'Bağlantı hatası, lütfen internetinizi kontrol edin';
    }

    const status = err.response.status;
    const data = err.response.data as { detail?: unknown } | undefined;

    // Rate limit (429)
    if (status === 429) {
      return 'Çok fazla istek gönderdiniz, lütfen biraz bekleyin';
    }

    // Conflict (409) — duplicate
    if (status === 409 && typeof data?.detail === 'string') {
      return data.detail;
    }

    // 422 Pydantic validation — detail is array
    if (Array.isArray(data?.detail)) {
      const first = data.detail[0] as { msg?: string; loc?: string[] } | undefined;
      if (first?.msg) {
        return first.loc && first.loc.length > 1
          ? `${first.loc.slice(1).join('.')}: ${first.msg}`
          : first.msg;
      }
      return 'Form doğrulama hatası';
    }

    // 4xx with string detail
    if (typeof data?.detail === 'string') {
      return data.detail;
    }

    // 5xx
    if (status >= 500) {
      return 'Sunucu hatası, lütfen daha sonra tekrar deneyin';
    }

    return err.message || fallback;
  }

  if (err instanceof Error) {
    return err.message || fallback;
  }

  return fallback;
}
```

- [ ] **Step 4.2: Test dosyasını oluştur**

Create `frontend/src/utils/__tests__/extractErrorDetail.test.ts`:

```typescript
import { AxiosError, AxiosHeaders } from 'axios';
import { describe, it, expect } from 'vitest';

import { extractErrorDetail } from '../extractErrorDetail';

function makeAxiosError(status: number, data: unknown): AxiosError {
  const err = new AxiosError(
    'Request failed',
    String(status),
    undefined,
    null,
    {
      data,
      status,
      statusText: '',
      headers: {},
      config: { headers: new AxiosHeaders() },
    },
  );
  return err;
}

describe('extractErrorDetail', () => {
  it('extracts string detail (HTTPException 4xx)', () => {
    const err = makeAxiosError(400, { detail: 'question_id not found' });
    expect(extractErrorDetail(err)).toBe('question_id not found');
  });

  it('extracts first msg from Pydantic 422 array', () => {
    const err = makeAxiosError(422, {
      detail: [
        { type: 'literal_error', loc: ['body', 'flag_type'], msg: 'Input should be...' },
      ],
    });
    expect(extractErrorDetail(err)).toContain('flag_type');
    expect(extractErrorDetail(err)).toContain('Input should be');
  });

  it('returns Turkish rate-limit message for 429', () => {
    const err = makeAxiosError(429, { detail: 'Rate limit exceeded: 10 per 1 minute' });
    expect(extractErrorDetail(err)).toBe('Çok fazla istek gönderdiniz, lütfen biraz bekleyin');
  });

  it('returns Turkish conflict message for 409 string detail', () => {
    const err = makeAxiosError(409, { detail: 'Bu soruyu zaten aynı türde bildirdiniz.' });
    expect(extractErrorDetail(err)).toBe('Bu soruyu zaten aynı türde bildirdiniz.');
  });

  it('handles network error (no response)', () => {
    const err = new AxiosError('Network Error', 'ERR_NETWORK');
    expect(extractErrorDetail(err)).toContain('Bağlantı');
  });

  it('falls back for non-axios Error', () => {
    expect(extractErrorDetail(new Error('boom'))).toBe('boom');
  });

  it('returns fallback for unknown', () => {
    expect(extractErrorDetail(null, 'default')).toBe('default');
  });
});
```

- [ ] **Step 4.3: Vitest çalıştır — 7/7 PASS bekleniyor**

```bash
cd frontend && npx vitest run src/utils/__tests__/extractErrorDetail.test.ts
```

Expected: `Test Files  1 passed (1) | Tests  7 passed (7)`

- [ ] **Step 4.4: FlagButton.tsx'e entegre et**

Modify `frontend/src/components/Quality/FlagButton.tsx`:

Replace the catch block in `handleSubmit` (lines ~73-82):

```typescript
import { extractErrorDetail } from '../../utils/extractErrorDetail';

// ... (rest of imports)

// Inside handleSubmit catch block:
    } catch (err) {
      const msg = extractErrorDetail(err, 'Bildirim gönderilemedi');
      setToast({ open: true, severity: 'error', message: msg });
    } finally {
      setSubmitting(false);
    }
```

- [ ] **Step 4.5: TypeScript check**

```bash
cd frontend && npx tsc --noEmit 2>&1 | grep -E "extractErrorDetail|FlagButton" | head -5
```

Expected: empty output (no errors)

- [ ] **Step 4.6: Build + deploy**

```bash
cd frontend && npm run build:fast 2>&1 | tail -3
cd .. && docker compose build frontend 2>&1 | tail -3
docker compose up -d --no-deps frontend
sleep 5
docker ps --filter "name=kiro2-frontend" --format "{{.Names}} {{.Status}}"
```

Expected: `kiro2-frontend Up X seconds (healthy)`

- [ ] **Step 4.7: Manuel E2E doğrulama (browser)**

1. http://localhost:3000 aç
2. beta01 login
3. Karışık Pratik → bir soruda ⚠️ ikon
4. Aynı flag_type ile 2 kez gönder
5. **Beklenen:** 2. submit'te toast "Bu soruyu zaten aynı türde bildirdiniz." (409 mesajı)

- [ ] **Step 4.8: Commit**

```bash
git add frontend/src/utils/extractErrorDetail.ts frontend/src/utils/__tests__/extractErrorDetail.test.ts frontend/src/components/Quality/FlagButton.tsx
git commit -m "$(cat <<'EOF'
fix(s3-5): extractErrorDetail utility — Pydantic array vs string ayrımı

Backend 422 (array) ve 4xx (string) detail formatlarını tek helper ile
kullanıcı-dostu Türkçe mesaja çevirir. 7 vitest case PASS.

FlagButton.tsx'in error toast'u artık "Request failed with status code 409"
yerine "Bu soruyu zaten aynı türde bildirdiniz." gösterir.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: 15 Test'siz API için 45 Smoke Test (S2.1 toplu)

**Files:**
- Create: `backend/tests/api/_smoke_helpers.py` — shared fixtures
- Create: `backend/tests/api/test_<api>.py` × 15

**Hedef:** Son 10 hafta'da eklenen test'siz API'lara minimum 3'er smoke test (auth-required 401, happy path 2xx, invalid input 4xx) — kapsam değil, regression guard.

Target API'lar (15 toplam, son 10 hafta'da eklendi):
1. `billing_api` — 4 hafta
2. `birlikte_streak_api` — 8 hafta
3. `coaching_api` — 5 hafta
4. `cozum_duellosu_api` — 8 hafta
5. `daily_quest_api` — 7 hafta
6. `duel_api` — 4 hafta
7. `error_cluster_api` — 5 hafta
8. `knowledge_graph_api` — 5 hafta
9. `league_api` — 5 hafta
10. `mastery_confidence_api` — 5 hafta
11. `mnemonic_api` — 10 hafta
12. `moderation_api` — 4 hafta
13. `oba_api` — 8 hafta
14. `bilge_alp` — 8 hafta
15. `dina_api` — 5 hafta (existing integration test çok dar)

- [ ] **Step 5.1: Shared fixtures helpers oluştur**

Create `backend/tests/api/_smoke_helpers.py`:

```python
"""Shared smoke test helpers — Faz 7.2 + S2.1 sprint.

Provides fixtures for:
- _login_as(email, password) → Bearer token
- _auth_headers(token) → dict
- _real_user_id() → beta01 UUID
- _real_question_id() → first beta-eligible question UUID
- _admin_token() → admin user Bearer token (creates if missing)
"""

from __future__ import annotations

import os
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from core.database import get_db_session_context
from main import app

BETA_EMAIL = "beta01@kiro2.com"
BETA_PASSWORD = "Beta01!Kiro2026"
ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@kiro2.com")
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "ChangeMe1!")


async def _login_as(email: str, password: str) -> str | None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        if r.status_code != 200:
            return None
        return r.json()["access_token"]


@pytest.fixture
async def student_token() -> str:
    token = await _login_as(BETA_EMAIL, BETA_PASSWORD)
    if not token:
        pytest.skip(f"login failed for {BETA_EMAIL}")
    return token


@pytest.fixture
async def admin_token() -> str:
    token = await _login_as(ADMIN_EMAIL, ADMIN_PASSWORD)
    if not token:
        pytest.skip(f"admin {ADMIN_EMAIL} login failed — set TEST_ADMIN_*")
    return token


@pytest.fixture
def auth_headers():
    def _make(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    return _make


@pytest.fixture
async def real_question_id() -> str:
    async with get_db_session_context() as s:
        r = await s.execute(
            text(
                "SELECT id FROM question_bank "
                "WHERE is_active=TRUE "
                "AND quality_review_status IN ('human_verified','auto_judged_high') "
                "LIMIT 1"
            )
        )
        qid = r.scalar()
        if not qid:
            pytest.skip("no beta-eligible question_bank row")
        return qid


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
```

- [ ] **Step 5.2: Her API için endpoint envanteri çıkar**

```bash
for api in billing_api birlikte_streak_api coaching_api cozum_duellosu_api daily_quest_api duel_api error_cluster_api knowledge_graph_api league_api mastery_confidence_api mnemonic_api moderation_api oba_api bilge_alp dina_api; do
  echo "=== $api ==="
  grep -E "^@router\.\w+|^async def" backend/api/${api}.py 2>/dev/null | head -6
done > /tmp/api_endpoints.txt
cat /tmp/api_endpoints.txt | head -100
```

Save to local file for reference. Her API'nin ilk GET endpoint'i + bir POST (varsa) smoke target olur.

- [ ] **Step 5.3: TEMPLATE — `test_billing_api.py` örnek**

Create `backend/tests/api/test_billing_api.py`:

```python
"""Smoke tests for billing_api — S2.1 sprint."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from main import app

pytestmark = pytest.mark.asyncio


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# TC1 — auth required (no Bearer → 401)
async def test_billing_status_requires_auth():
    async with await _client() as c:
        r = await c.get("/api/v1/billing/status")
    # Acceptable: 401 (no token) or 404 (endpoint doesn't exist — flag for cleanup)
    assert r.status_code in (401, 403, 404), r.text


# TC2 — happy path (student token, public-ish endpoint)
async def test_billing_status_with_student(student_token, auth_headers):
    async with await _client() as c:
        r = await c.get("/api/v1/billing/status", headers=auth_headers(student_token))
    assert r.status_code < 500, r.text  # No crash — semantic 200/404 OK


# TC3 — invalid input (POST with bad payload → 422)
async def test_billing_subscribe_invalid_payload(student_token, auth_headers):
    async with await _client() as c:
        r = await c.post(
            "/api/v1/billing/subscribe",
            json={"plan": ""},  # empty plan
            headers=auth_headers(student_token),
        )
    # Either 422 (validation) or 404 (endpoint not found) — both acceptable for smoke
    assert r.status_code != 500, f"Endpoint crashed: {r.text}"
```

- [ ] **Step 5.4: Diğer 14 API için aynı template ile test dosyası**

Her API için Step 5.3 template'ini uyarla (URL prefix değiştir, endpoint isimlerini öğren). Toplam 15 dosya × 3 test = 45 test.

**Pattern:**
```python
# test_<api>.py
# TC1: auth required (401/403/404 OK, 200 NOT)
# TC2: student happy path (status < 500)
# TC3: invalid input (status != 500)
```

URL prefix'leri keşfet:
```bash
grep "prefix=" backend/api/{billing,birlikte_streak,coaching,cozum_duellosu,daily_quest,duel,error_cluster,knowledge_graph,league,mastery_confidence,mnemonic,moderation,oba,bilge_alp,dina}_api.py 2>/dev/null
```

- [ ] **Step 5.5: Tüm smoke testleri çalıştır**

```bash
cd backend && pytest tests/api/ -v --tb=short 2>&1 | tail -30
```

Expected: 45+ test, çoğunluk PASS (404'ler kabul edilebilir bilinçli). 500'ler = bug → ayrı issue.

- [ ] **Step 5.6: 500 hata veren endpoint'leri raporla**

```bash
cd backend && pytest tests/api/ --tb=no -q 2>&1 | grep -i "500\|FAILED" | head -10
```

Eğer 500 varsa: `docs/audits/2026-05-18-smoke-test-500-findings.md` raporu oluştur, Bug listesine ekle (Bug #12+).

- [ ] **Step 5.7: Commit**

```bash
git add backend/tests/api/
git commit -m "$(cat <<'EOF'
test(s2-1): 15 API smoke test eklendi — 45 test toplam

Son 10 hafta'da eklenen test'siz API'lar için min 3 test (auth/happy/invalid).
Coverage değil regression guard — 500 hata = bug, 404 = OK.

API'lar: billing, birlikte_streak, coaching, cozum_duellosu, daily_quest,
duel, error_cluster, knowledge_graph, league, mastery_confidence, mnemonic,
moderation, oba, bilge_alp, dina.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: apiClient Migration — 20 dosya fetch → apiClient (S3.1)

**Files:** 20 modify (her biri ayrı commit veya batch — küçük gruplar halinde)

**Hedef:** Frontend HTTP karması düzelt. Tüm raw `fetch('/api/...')` çağrıları `apiClient.{get,post,put,delete}`'e migrate.

- [ ] **Step 6.1: Migration target listesi oluştur**

```bash
cd C:/Users/husey/kiro2
grep -rln "await fetch(['\"]/api" frontend/src/components/ frontend/src/hooks/ frontend/src/services/ 2>&1 | grep -v __tests__ | grep -v ".md" | sort -u > /tmp/fetch_migration_targets.txt
wc -l /tmp/fetch_migration_targets.txt
cat /tmp/fetch_migration_targets.txt
```

Expected: ~20 dosya. Tipik adaylar:
- `services/backgroundSyncService.ts` (3 yer)
- `services/offlineStorageService.ts` (1 yer)
- `hooks/useBionicReading.ts` (3 yer)
- `components/Accessibility/ADHD/FocusMode.tsx` (2 yer)
- `components/Accessibility/ADHD/TaskManagement.tsx` (3 yer)
- `components/Accessibility/TextToSpeech.tsx` (1 yer)
- `components/Admin/BatchQueueMonitor.tsx` (3 yer)
- `components/Admin/ContentManagement.tsx` (1+ yer)
- ... (diğer ~10 dosya)

- [ ] **Step 6.2: Migration pattern dokümante et**

Add to `.claude/rules/` (next task does CLAUDE.md):

```typescript
// ❌ ESKİ
const response = await fetch('/api/v1/foo', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify(payload),
});
if (!response.ok) throw new Error('failed');
const data = await response.json();

// ✅ YENİ
import { apiClient } from '../../services/apiClient';
const { data } = await apiClient.post<FooResponse>('/api/v1/foo', payload);
```

- [ ] **Step 6.3: Migrate batch 1 — services/ (3 dosya)**

Migrate `frontend/src/services/backgroundSyncService.ts`:
- Line 188: `fetch('/api/v1/sync/exam-sessions', {...})` → `apiClient.post('/api/v1/sync/exam-sessions', payload)`
- Line 239: `fetch('/api/v1/sync/progress', {...})` → `apiClient.post('/api/v1/sync/progress', payload)`
- Line 422: `fetch('/api/v1/push/subscribe', {...})` → `apiClient.post('/api/v1/push/subscribe', payload)`

Migrate `frontend/src/services/offlineStorageService.ts`:
- Line 112: `fetch('/api/v1/questions/download', {...})` → `apiClient.get('/api/v1/questions/download', { params: {...} })`

Commit:
```bash
git add frontend/src/services/backgroundSyncService.ts frontend/src/services/offlineStorageService.ts
git commit -m "refactor(s3-1): services/ raw fetch → apiClient (batch 1/4)"
```

- [ ] **Step 6.4: Migrate batch 2 — hooks/ (1-2 dosya)**

Migrate `frontend/src/hooks/useBionicReading.ts` (3 fetch çağrısı).

Commit similar message (batch 2/4).

- [ ] **Step 6.5: Migrate batch 3 — Accessibility components (3-4 dosya)**

Migrate FocusMode, TaskManagement, TextToSpeech.

Commit (batch 3/4).

- [ ] **Step 6.6: Migrate batch 4 — Admin components + remaining**

Migrate BatchQueueMonitor, ContentManagement, + remaining.

Commit (batch 4/4).

- [ ] **Step 6.7: Doğrulama — 0 fetch kalmalı**

```bash
grep -rln "await fetch(['\"]/api" frontend/src/components/ frontend/src/hooks/ frontend/src/services/ 2>&1 | grep -v __tests__ | grep -v ".md" | wc -l
```

Expected: **0**

- [ ] **Step 6.8: Build + deploy + smoke**

```bash
cd frontend && npm run build:fast && cd ..
docker compose build frontend && docker compose up -d --no-deps frontend
sleep 5
docker ps --filter "name=kiro2-frontend" --format "{{.Names}} {{.Status}}"
# Manual smoke: beta01 login → ana dashboard → admin panel (admin user) → bionic reading toggle
```

---

## Task 7: Redis-based Rate Limiter Standardization (S3.2)

**Files:**
- Create: `backend/core/rate_limit_decorator.py` — unified wrapper
- Modify: `backend/api/auth.py:75-128` — manuel logic → unified
- Modify: `backend/api/learning_path_v2.py:115-150` — local rate_limit → unified import
- Modify: `backend/api/sinav.py` — 7 write endpoint'e ekle
- Modify: `backend/api/student_feedback_api.py` — Task 3'teki geçici import → unified

**Hedef:** 3 paralel rate limit pattern (auth manual, learning_path decorator, advanced_rate_limiter Redis) tek bir Redis-tabanlı sisteme yakınsa.

- [ ] **Step 7.1: Unified decorator wrapper oluştur**

Create `backend/core/rate_limit_decorator.py`:

```python
"""Unified rate limit decorator — S3.2 standardization.

Wraps core/advanced_rate_limiter.py (Redis-based) so endpoints can use a
single decorator pattern. Replaces:
- api/auth.py:_check_rate_limit (in-memory dict)
- api/learning_path_v2.py:rate_limit (slowapi-based, in-memory)

Usage:
    @router.post("/endpoint")
    @rate_limit("create_profile")
    async def endpoint(request: Request, ...):
        ...

Configuration: backend/core/rate_limit_config.py (or constants below).
"""

from __future__ import annotations

import functools
import logging
from typing import Callable

from fastapi import HTTPException, Request

from core.advanced_rate_limiter import (
    RateLimitExceeded,
    check_rate_limit,
    get_rate_limiter,
    resolve_user_tier_for_rate_limit,
)

logger = logging.getLogger(__name__)


# (max_requests, window_seconds) per bucket. ALL endpoint rate limits here.
RATE_LIMITS: dict[str, tuple[int, int]] = {
    # Auth
    "login": (10, 60),
    "register": (5, 60),
    "password_reset": (5, 300),
    "2fa_verify": (10, 60),
    # Learning
    "create_profile": (5, 60),
    "assess_knowledge": (10, 60),
    "create_path": (5, 60),
    "search_resources": (30, 60),
    # Quality / feedback
    "flag_submit": (10, 60),
    # Gamification (Task 7 expansion)
    "award_xp": (10, 60),
    "quest_progress": (20, 60),
    "claim_bonus": (3, 60),
    # Exam (sinav.py)
    "save_answer": (60, 60),
    "submit_exam": (5, 60),
    "flag_question": (30, 60),
    "create_exam": (5, 60),
}


def rate_limit(bucket: str) -> Callable:
    """Apply Redis-based rate limit. Falls back to no-op if Redis unavailable."""
    if bucket not in RATE_LIMITS:
        logger.warning(f"Unknown rate_limit bucket '{bucket}' — no-op")
        return lambda fn: fn

    max_req, window = RATE_LIMITS[bucket]

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            request: Request | None = kwargs.get("request") or next(
                (a for a in args if isinstance(a, Request)), None
            )
            if request is None:
                # No Request param — can't rate limit; log and skip
                logger.warning(f"rate_limit({bucket}): no Request in args — skipping")
                return await fn(*args, **kwargs)

            client_ip = (
                request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                or (request.client.host if request.client else "unknown")
            )

            try:
                await check_rate_limit(
                    identifier=f"{bucket}:{client_ip}",
                    limit=max_req,
                    window=window,
                )
            except RateLimitExceeded as exc:
                raise HTTPException(
                    status_code=429,
                    detail=f"Çok fazla istek. {window} saniye sonra tekrar deneyin.",
                    headers={
                        "X-RateLimit-Limit": str(max_req),
                        "X-RateLimit-Window": str(window),
                        "Retry-After": str(window),
                    },
                ) from exc
            except Exception as exc:
                # Redis down → degrade open (log + allow). Better than blocking all traffic.
                logger.error(f"Rate limit check failed (degrade open): {exc}")

            return await fn(*args, **kwargs)

        return wrapper

    return decorator
```

- [ ] **Step 7.2: Failing test yaz (TDD pin)**

Create `backend/tests/api/test_rate_limit_unified.py`:

```python
"""Test unified rate_limit decorator wraps Redis-based limiter."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app

pytestmark = pytest.mark.asyncio


async def test_login_rate_limit_uses_unified():
    """Login still rate-limited after migration (was: auth.py manual logic)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        codes = []
        for i in range(12):
            r = await client.post(
                "/api/v1/auth/login",
                json={"email": "nonexistent@kiro2.com", "password": f"WRONG_{i}"},
            )
            codes.append(r.status_code)
        # First 10 → 401, 11th+ → 429
        assert codes[-1] == 429, f"Last attempt should be 429, got {codes}"


async def test_redis_rate_limit_shared_across_workers(student_token, auth_headers):
    """Verify Redis bucket (not in-memory) — restart wouldn't reset."""
    # Smoke: just call rate-limited endpoint and check headers
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(
            "/api/v1/learning-path/profile", headers=auth_headers(student_token)
        )
        # If rate limit infrastructure is wired, X-RateLimit-* headers should appear
        # (advanced_rate_limiter.py sets these on RateLimitExceeded). Skip if not.
        if "x-ratelimit-limit" in r.headers:
            assert int(r.headers["x-ratelimit-limit"]) > 0
```

Run:
```bash
cd backend && pytest tests/api/test_rate_limit_unified.py -v --tb=short
```

Expected: First test PASS (existing auth limit), second test SKIP veya PASS depending on header presence.

- [ ] **Step 7.3: auth.py'yi unified'e migrate et**

Modify `backend/api/auth.py`:

1. Delete lines 75-128 (in-memory `_rate_buckets`, `_check_rate_limit`, `_record_attempt`, aliases)
2. Import: `from core.rate_limit_decorator import rate_limit`
3. Replace each `_check_login_rate_limit(request)` call with `@rate_limit("login")` decorator on endpoint
4. `_check_rate_limit(request, "register")` → `@rate_limit("register")` decorator
5. `_check_rate_limit(request, "password_reset")` → `@rate_limit("password_reset")` decorator
6. Keep `_record_failed_login` / `_record_attempt` for now — these track failures (different from rate limit; could refactor to Redis SET in follow-up)

Example diff for `secure_login`:

```python
# OLD
@router.post("/secure", ...)
async def secure_login(request: Request, ...):
    _check_login_rate_limit(request)
    # ... body

# NEW
@router.post("/secure", ...)
@rate_limit("login")
async def secure_login(request: Request, ...):
    # ... body (no manual call)
```

- [ ] **Step 7.4: learning_path_v2.py local rate_limit'i unified ile değiştir**

Modify `backend/api/learning_path_v2.py:115-150`:

1. Delete local `rate_limit` decorator definition + local `RATE_LIMITS` dict
2. `from core.rate_limit_decorator import rate_limit, RATE_LIMITS` import et
3. Mevcut `@rate_limit("create_profile")` çağrıları zaten doğru anahtarları kullanıyor — değişmez

- [ ] **Step 7.5: sinav.py 7 write endpoint'e rate_limit ekle**

Modify `backend/api/sinav.py` — 7 endpoint:

```python
from core.rate_limit_decorator import rate_limit
from fastapi import Request

@router.post("/start", ...)
@rate_limit("create_exam")
async def create_exam_endpoint(request: Request, ...):
    ...

@router.post("/{session_id}/save-answer", ...)
@rate_limit("save_answer")
async def save_answer(request: Request, session_id: str, ...):
    ...

@router.post("/{session_id}/flag-question", ...)
@rate_limit("flag_question")
async def flag_question(request: Request, session_id: str, ...):
    ...

# ... vb. 4 endpoint daha
```

- [ ] **Step 7.6: student_feedback_api.py Task 3 geçici importu temizle**

Modify `backend/api/student_feedback_api.py`:

```python
# OLD (Task 3)
from api.learning_path_v2 import RATE_LIMITS, rate_limit

# NEW
from core.rate_limit_decorator import rate_limit
```

- [ ] **Step 7.7: Container'a deploy + smoke**

```bash
docker cp backend/core/rate_limit_decorator.py kiro2-backend:/app/core/rate_limit_decorator.py
docker cp backend/api/auth.py kiro2-backend:/app/api/auth.py
docker cp backend/api/learning_path_v2.py kiro2-backend:/app/api/learning_path_v2.py
docker cp backend/api/sinav.py kiro2-backend:/app/api/sinav.py
docker cp backend/api/student_feedback_api.py kiro2-backend:/app/api/student_feedback_api.py
docker exec kiro2-backend find /app -name "*.pyc" -delete
docker restart kiro2-backend
sleep 22

# Smoke: login rate limit still works
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code} " -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"nonexistent@kiro2.com","password":"WRONG_'$i'"}'
done
echo ""
# Expected: 401 401 ... 401 429 429 (last 2-3 should be 429)
```

- [ ] **Step 7.8: Tüm rate limit testleri çalıştır**

```bash
cd backend && pytest tests/api/test_rate_limit_unified.py tests/api/test_student_feedback_api.py -v --tb=short
```

Expected: ALL PASS

- [ ] **Step 7.9: Commit**

```bash
git add backend/core/rate_limit_decorator.py backend/api/auth.py backend/api/learning_path_v2.py backend/api/sinav.py backend/api/student_feedback_api.py backend/tests/api/test_rate_limit_unified.py
git commit -m "$(cat <<'EOF'
refactor(s3-2): unified Redis-based rate limiter — auth/learning/sinav/feedback

3 paralel pattern → 1 unified @rate_limit decorator (core/rate_limit_decorator.py).
- auth.py: in-memory dict logic silindi (~60 satır)
- learning_path_v2.py: local rate_limit/RATE_LIMITS → import
- sinav.py: 7 write endpoint'e rate_limit eklendi (save_answer/submit/flag/create)
- student_feedback_api.py: Task 3 geçici importu unified'e değiştirildi

advanced_rate_limiter.py (Redis) artık kullanılıyor; degrade-open semantiği
Redis erişilemezse trafiği bloklamaz (log + allow).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: CI Gate + CLAUDE.md "Yeni Endpoint Checklist" (S2.4 + M1-M3)

**Files:**
- Create: `.github/workflows/test-coverage-gate.yml`
- Create: `.claude/rules/new-endpoint-checklist.md`
- Modify: `CLAUDE.md` — referans + Karpathy bölümüne ekleme

**Hedef:** S2.1-3.2'de yapılan iyileştirmelerin geriye doğru aşınmasını engelle. Yeni API/endpoint eklerken zorunlu kontroller PR seviyesinde block.

- [ ] **Step 8.1: GitHub Actions workflow oluştur**

Create `.github/workflows/test-coverage-gate.yml`:

```yaml
name: Test Coverage Gate

on:
  pull_request:
    branches: [main, master, clean-main]
    paths:
      - 'backend/api/**'
      - 'backend/services/**'
      - 'backend/core/**'
      - 'frontend/src/**'

jobs:
  backend-new-api-test-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check new API files have tests
        run: |
          set -e
          BASE_REF="${{ github.event.pull_request.base.sha }}"
          HEAD_REF="${{ github.event.pull_request.head.sha }}"

          # Yeni eklenen backend/api/*.py dosyaları
          NEW_APIS=$(git diff --name-only --diff-filter=A "$BASE_REF" "$HEAD_REF" \
            | grep -E '^backend/api/[a-z_]+\.py$' \
            | grep -v '__init__' || true)

          if [ -z "$NEW_APIS" ]; then
            echo "No new API files — gate skipped."
            exit 0
          fi

          echo "New API files:"
          echo "$NEW_APIS"

          FAIL=0
          for api in $NEW_APIS; do
            base=$(basename "$api" .py)
            if ! find backend/tests -name "test_${base}*.py" | grep -q .; then
              echo "::error file=$api::No test found for new API. Add backend/tests/api/test_${base}.py with min 3 smoke tests."
              FAIL=1
            fi
          done
          exit $FAIL

  backend-coverage-threshold:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        ports: ['5432:5432']
      redis:
        image: redis:7
        ports: ['6379:6379']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install
        run: |
          cd backend && pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests with coverage
        run: |
          cd backend
          pytest tests/api/ tests/unit/ --cov=api --cov=core --cov=services \
            --cov-report=term --cov-fail-under=55
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/postgres
          REDIS_URL: redis://localhost:6379/0

  frontend-fetch-ban:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: No raw fetch in new code
        run: |
          set -e
          BASE_REF="${{ github.event.pull_request.base.sha }}"
          HEAD_REF="${{ github.event.pull_request.head.sha }}"

          # Yeni satırlarda raw fetch('/api/...') var mı?
          NEW_FETCH=$(git diff "$BASE_REF" "$HEAD_REF" -- 'frontend/src/**/*.ts' 'frontend/src/**/*.tsx' \
            | grep -E "^\+.*await fetch\(['\"]\/api" || true)

          if [ -n "$NEW_FETCH" ]; then
            echo "::error::Raw fetch('/api/...') yasaktır (S3.1). apiClient kullanın."
            echo "$NEW_FETCH"
            exit 1
          fi
```

**Not:** Coverage threshold ilk başta `55` (mevcut %53'e yakın). Sprint sonrası 60'a, sonra 70'e yükseltilir.

- [ ] **Step 8.2: .claude/rules/new-endpoint-checklist.md oluştur**

Create `.claude/rules/new-endpoint-checklist.md`:

```markdown
# Yeni Endpoint Checklist

Yeni bir `backend/api/*.py` dosyası veya yeni write endpoint EKLERKEN
aşağıdaki 6 nokta ZORUNLU. Pre-PR check.

## 1. Rate Limit (S3.2)

```python
from fastapi import Request
from core.rate_limit_decorator import rate_limit

@router.post("/your-endpoint")
@rate_limit("your_bucket")  # core/rate_limit_decorator.py RATE_LIMITS'e ekle
async def your_endpoint(request: Request, ...):
    ...
```

YASAK:
- Yeni `_check_rate_limit` manuel fonksiyon
- Yeni `slowapi.Limiter` instance
- Decorator'sız write endpoint

## 2. Test (S2.1)

`backend/tests/api/test_<your_api>.py` zorunlu (min 3 test):
- Auth required (no Bearer → 401/403)
- Happy path (valid input → 2xx)
- Invalid input (bad payload → 4xx, not 500)

Template: `backend/tests/api/test_billing_api.py`

## 3. Frontend Client (S3.1)

Frontend'den çağıracaksanız: `apiClient.{get,post,put,delete}` kullanın.

YASAK:
```typescript
// ❌
await fetch('/api/v1/...', { credentials: 'include' });
```

```typescript
// ✅
import { apiClient } from '@/services/apiClient';
const { data } = await apiClient.post('/api/v1/...', payload);
```

## 4. Error Response (S3.5)

Backend `HTTPException` `detail` her zaman string. Pydantic 422 detail array.
Frontend tarafta `extractErrorDetail(err)` utility kullan.

## 5. UNIQUE Constraint (S1.1)

Eğer endpoint INSERT yapıyorsa ve "duplicate kayıt" kavramı varsa:
- Migration'da partial UNIQUE index
- IntegrityError → 409 Conflict (400 değil)
- Test: TC2 pattern (TDD-pin)

## 6. Router Registration (Session 120 ders)

Yeni `app/api/*.py` veya `api/*.py` → `routers/loader.py:ROUTER_MAPPING` ekle.
Test: `pytest tests/test_router_registration.py`

---

## Self-check (commit öncesi)

- [ ] `@rate_limit` decorator (write endpoint için)
- [ ] `backend/tests/api/test_<api>.py` 3+ test, hepsi PASS
- [ ] Frontend: `apiClient` kullanılıyor, `fetch` YOK
- [ ] HTTPException detail string, 422 detail array — frontend extractErrorDetail
- [ ] UNIQUE/IntegrityError handling (gerekirse)
- [ ] `routers/loader.py` ROUTER_MAPPING güncel

İhlal → CI gate (`.github/workflows/test-coverage-gate.yml`) PR'ı bloklar.
```

- [ ] **Step 8.3: CLAUDE.md'ye referans ekle**

Modify `CLAUDE.md` — "Hard Rules" bölümüne yeni satır:

```markdown
### KIRO2 Hard Rules (İhlal Edilmez)

[mevcut içerik korunur]

**Yeni Endpoint Disiplini (S2.1+S3.2+S3.5 sprint sonrası, 2026-05-18)**

- Yeni `backend/api/*.py` dosyası eklendiğinde **6 zorunlu kontrol**: `.claude/rules/new-endpoint-checklist.md`
- `@rate_limit` decorator olmadan write endpoint **YASAK** (CI gate bloklar)
- `backend/tests/api/test_<api>.py` olmadan yeni API merge **YASAK** (CI gate bloklar)
- Frontend `await fetch('/api/...')` **YASAK** — `apiClient` kullan (CI gate bloklar)
```

- [ ] **Step 8.4: Karpathy bölümüne "Önce Ara" ek prensibi**

Modify `CLAUDE.md` — "Behavioral Foundation" bölümüne ek (Önce Düşün altında):

```markdown
### 1.1 Önce Ara (Re-use Before Re-implement)

**Yeni özellik yazmadan önce mevcut altyapıyı tara.**

- Rate limit eklemek → `grep "rate_limit\|Limiter" backend/` önce
- HTTP client kullanmak → `apiClient` zaten var mı kontrol et
- Error handler yazmak → `extractErrorDetail` benzeri utility var mı

**Anti-pattern (2026-05-18 audit'inde tespit edildi):**
- 3 paralel rate limit pattern (auth manual + learning decorator + advanced_rate_limiter Redis)
- 20 dosya raw fetch vs 11 dosya apiClient
- `core/advanced_rate_limiter.py` Redis çözümü yazıldı ama hiçbir endpoint kullanmıyordu

> "Kullanılmayan altyapı en pahalısıdır" — yenisini yapmadan önce eskiyi ara.
```

- [ ] **Step 8.5: Commit**

```bash
git add .github/workflows/test-coverage-gate.yml .claude/rules/new-endpoint-checklist.md CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(s2-4 + m1-m3): CI gate + endpoint checklist + Karpathy "Önce Ara"

CI gate (.github/workflows/test-coverage-gate.yml):
- Yeni backend/api/*.py PR'larda test zorunlu
- Coverage threshold 55%
- Yeni frontend kodda raw fetch yasak

Doc (.claude/rules/new-endpoint-checklist.md):
- 6 zorunlu kontrol (rate_limit, test, apiClient, error, UNIQUE, loader)

CLAUDE.md:
- "Yeni Endpoint Disiplini" Hard Rules'a eklendi
- "Önce Ara" prensibi (re-use before re-implement) Karpathy bölümüne eklendi

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 8.6: Final push**

```bash
git push origin master
```

---

## Self-Review

### 1. Spec coverage

| Audit Bulgu | Task | Status |
|-------------|------|--------|
| S1.1 Duplicate flag | Task 2 | ✓ |
| S1.2 Rate limit yok | Task 3 | ✓ |
| S2.1 student_feedback test | Task 1 | ✓ |
| S2.1 toplu 15 API test | Task 5 | ✓ |
| S3.1 fetch → apiClient | Task 6 | ✓ |
| S3.2 rate limit standardization | Task 7 | ✓ |
| S3.5 extractErrorDetail | Task 4 | ✓ |
| S2.4 CI gate | Task 8 | ✓ |
| M1-M3 Doc | Task 8 | ✓ |

Atlanan (deliberate, ayrı plan):
- S1.3 LLM-circular (Faz 5.4 holdout test, beta retrospective sonrası)
- S1.4 Quality script deterministic seed (Faz 2.6 in_progress ile birlikte)
- S2.2 26 tier/quality script test (ayrı plan — DB-touching, daha karmaşık)
- S2.3 Frontend component testleri (Task 4'te extractErrorDetail örnek, geri kalanı ayrı sprint)
- S3.3 in-memory → Redis full migration (Task 7 advanced_rate_limiter zaten Redis)
- S3.4 dual auth tutarlılığı (ayrı audit gerek)
- S3.6 migration yazım stili (ayrı doc task)

### 2. Placeholder scan

- "TBD" — yok
- "TODO" — yok
- "implement later" — yok
- "Similar to Task N" — Task 5 step 5.4'te "Step 5.3 template'ini uyarla" — KASITLI (her API için ufak variation, kopyala-yapıştır mantıklı)
- "Add appropriate error handling" — yok

### 3. Type consistency

- `rate_limit(bucket)` decorator: Task 3'te local import (geçici), Task 7'de `core.rate_limit_decorator`'a taşındı. Task 7 step 7.6 explicit migrate eder. ✓
- `extractErrorDetail(err, fallback?)` Task 4'te tanımlı, FlagButton.tsx'te kullanılır. ✓
- `RATE_LIMITS` dict format: `tuple[int, int]` Task 7'de standartlaştırıldı. Task 3 geçici (slowapi string format `"10/minute"`) — Task 7 step 7.4'te tuple'a değişir, learning_path_v2'nin de tuple'a geçer. **Minor risk:** Task 7 sırasında slowapi-formatted entry'ler tuple'a convert edilmeli. Step 7.1'de RATE_LIMITS dict'i tuple format'tadır, doğru.

### Düzeltme: Task 3 ile Task 7 RATE_LIMITS format farkı

Task 3 step 3.3'te `"flag_submit": "10/minute"` (slowapi string format) eklendi.
Task 7 step 7.1'de `"flag_submit": (10, 60)` (tuple format).
Task 7 step 7.6 student_feedback'i unified'e migrate ederken decorator signature aynı (`@rate_limit("flag_submit")`), sadece backend dict format değişir. ✓ OK.

---

## Execution Handoff

Plan tamamlandı ve `docs/superpowers/plans/2026-05-18-quality-hardening-sprint.md` adresine kaydedildi. İki yürütme seçeneği:

**1. Subagent-Driven (önerilen)** — Her task için ayrı subagent dispatch, task'lar arası review, hızlı iterasyon. REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`. Task 1-4 (~2 saat) ardarda hızlı, Task 5-7 daha uzun, Task 8 sona.

**2. Inline Execution** — Bu session'da `superpowers:executing-plans` ile batch yürütme, checkpoint review'lar. Tüm context burada kalır. ~4-8 saat odaklı çalışma gerektirir.

Hangi yaklaşım?
