# MVP Beta Launch - Deep Analysis Report

## Date: 2026-03-04
## Status: FINDINGS DOCUMENTED

---

## P0: MUST FIX BEFORE BETA (Production Blockers)

### P0-1: Dual Auth System — 93% of Endpoints Broken

**Impact:** 348 of 371 protected endpoints return 401 for logged-in users.

**Root Cause:** Two disconnected auth systems:
- `/login/secure` creates **random tokens** (`secrets.token_urlsafe(32)`) stored in-memory
- `core.dependencies.get_current_user` expects **JWT tokens** (decodes with PyJWT)
- 320 endpoints use JWT auth, only 23 use in-memory auth

**Working endpoints (6%):**
- `auth.py`: /me, /change-password, /profile
- `student_dashboard.py`: /sinav-gecmisi, /hedefler, /hedef-olustur, /profil, /ozet, /bildirimler

**Broken endpoints (93%):**
- ALL semantic search, exam, question bank, analytics, reports, admin, FSRS, etc.

**Fix Options:**

| Option | Effort | Risk | Recommendation |
|--------|--------|------|---------------|
| A. Make /login/secure return JWT | 2-4 hours | Low | **RECOMMENDED** |
| B. Make get_current_user accept both | 4-8 hours | Medium | More robust but complex |
| C. Replace in-memory with JWT everywhere | 1-2 days | High | Best long-term, too risky for beta |

**Option A Fix (Recommended):**
```python
# In auth.py secure_login(), replace random token with JWT:
from core.jwt_auth import jwt_manager

jwt_token = jwt_manager.create_access_token(
    user_id=kullanici.kullanici_id,
    email=kullanici.email,
    role=db_user.role,  # DB role (UserRole enum)
)
jwt_refresh = jwt_manager.create_refresh_token(user_id=kullanici.kullanici_id)

# Set as cookies
response.set_cookie(key="access_token", value=jwt_token, ...)
response.set_cookie(key="refresh_token", value=jwt_refresh, ...)
```

Then update `get_current_user` in `core/dependencies.py` to also check cookies:
```python
# If no Bearer header, try httpOnly cookie
token = credentials.credentials if credentials else request.cookies.get("access_token")
```

---

### P0-2: In-Memory User Service — Data Loss on Restart

**Impact:** Server restart loses ALL:
- Sessions (aktif_tokenlar dict)
- Users registered via /kayit (kullanicilar dict)
- Student/teacher/parent profiles

**Severity:** Every uvicorn restart (deployment, crash, auto-reload) logs out ALL users.

**Fix:** Since DB users already work via `database_authenticate()`, the fix is:
1. Stop using `kullanici_servisi` for token storage
2. Use JWT tokens (self-contained, no server state needed)
3. This is automatically solved by P0-1 fix

---

### P0-3: XSS in Semantic Search Response

**Impact:** `<script>alert(1)</script>` in search query is reflected in response JSON.

**Current:** Search returns question_text as-is, which could contain user-injected XSS.

**Fix:** Frontend should already escape via React (JSX auto-escapes), but API should also sanitize:
```python
from markupsafe import escape
# In search response serialization:
question_text = str(escape(question.question_text))
```

**Risk Level:** Medium — React auto-escapes by default, so actual XSS exploitation requires `dangerouslySetInnerHTML`.

---

## P1: FIX WITHIN FIRST WEEK

### P1-1: No Rate Limiting on Login

**Impact:** Brute force attacks on login are unrestricted. Tested 6 wrong passwords with no rate limit.

**Fix:** Add rate limiting middleware to login endpoint:
```python
# In auth.py
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@router.post("/login/secure")
@limiter.limit("5/minute")
async def secure_login(...):
```

### P1-2: Weak JWT Secret

**Impact:** `dev-jwt-secret` (14 chars) is trivially brute-forceable.

**Fix:** Generate strong secret for production:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Add to `.env`: `JWT_SECRET_KEY=<64-char-random-string>`

### P1-3: Cookie secure=False in /refresh/secure

**Impact:** The refresh endpoint still has `secure=True` hardcoded (only /login/secure was fixed).

**Fix:** Apply same `_is_dev` pattern to refresh endpoint cookie setting.

### P1-4: Logout Doesn't Invalidate Tokens

**Impact:** After logout, old access token still works. Cookie deletion is client-side only.

**Fix with JWT:** Use token blacklist (Redis set) for remaining token lifetime:
```python
async def secure_logout(request: Request, response: Response):
    token = request.cookies.get("access_token")
    if token:
        # Blacklist in Redis (TTL = remaining expiry)
        await redis.setex(f"blacklist:{token}", 86400, "1")
    response.delete_cookie(...)
```

### P1-5: Legacy Frontend API Client

**Impact:** `lib/apiClient.ts` still reads `localStorage.access_token` (never set in httpOnly flow).

**Fix:** Remove or update `lib/apiClient.ts` to use cookies like `services/apiClient.ts`.

---

## P2: BACKLOG (Post-Beta)

### P2-1: question_bank COUNT Query is 766ms

**Finding:** `SELECT count(*) FROM question_bank` takes 766ms (78,550 rows, 1.23 GB table).

**Fix:** Use materialized view or cache for dashboard counts.

### P2-2: No PgBouncer Connection Pooling

**Finding:** 10 active / 100 max connections. No connection pooler for concurrent users.

### P2-3: DEBUG=true in Production

**Finding:** Debug mode exposes stack traces to users.

### P2-4: Orphaned Auth State Fields

**Finding:** `AuthState` interface has `token` and `refreshToken` fields that are always null.

### P2-5: Exam Page Infinite Loading

**Finding:** `/exam/start` shows permanent loading spinner (no exam data, no error message).

---

## Summary

| Priority | Count | Status |
|----------|-------|--------|
| P0 (Blockers) | 3 | Must fix before beta launch |
| P1 (First week) | 5 | Should fix soon after launch |
| P2 (Backlog) | 5 | Can wait |

**Critical Path:** P0-1 (dual auth fix) unblocks 93% of endpoints AND solves P0-2 (in-memory data loss). This is the single most impactful fix.

**Estimated Effort:**
- P0 fixes: 4-6 hours
- P1 fixes: 4-8 hours
- P2 fixes: varies
