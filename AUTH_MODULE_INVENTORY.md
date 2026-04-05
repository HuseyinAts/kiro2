# KIRO2 Backend Auth Module Inventory

**Generated:** 2026-04-05
**Purpose:** Complete inventory of all authentication-related modules
**Status:** VERIFIED - NO CODE CHANGES

---

## 1. AUTH MODULE INVENTORY

### 1.1 Core Authentication Modules (backend/core/)

| # | File Path | Role | LOC | Status | Notes |
|---|-----------|------|-----|--------|-------|
| 1 | `core/auth.py` | JWT + bcrypt + RBAC basic | 313 | **ACTIVE** | Main entry point documented in header |
| 2 | `core/jwt_auth.py` | JWT Manager with refresh tokens + blacklist | 400+ | **ACTIVE** | Redis-backed blacklist, docker-aware |
| 3 | `core/dependencies.py` | FastAPI dependency injection (`get_current_user`) | 300+ | **ACTIVE** | **PRIMARY AUTH ENTRY** - used by 112 API files |
| 4 | `core/auth_dependencies.py` | AuthenticationDependency + AuthorizationDependency | 250+ | **ACTIVE** | Delegates to enhanced_auth + rbac |
| 5 | `core/enhanced_authentication.py` | Comprehensive auth consolidation (~50KB) | 1200+ | **ACTIVE** | Multi-provider, session, 2FA, device fingerprint |
| 6 | `core/unified_auth_service.py` | Unified Auth + AuthZ service (~30KB) | 800+ | **ACTIVE** | JWT, RBAC, 2FA, session management consolidated |
| 7 | `core/consolidated_auth_dependencies.py` | Replaces old dependencies.py | 200+ | **ACTIVE** | Wrapper around auth_dependencies + rbac |

### 1.2 Authorization Modules

| # | File Path | Role | Status | Notes |
|---|-----------|------|--------|-------|
| 8 | `core/rbac_system.py` | Hierarchical RBAC with inheritance | **ACTIVE** | Full permission system |
| 9 | `core/authorization.py` | IDOR protection helpers | **ACTIVE** | `require_roles()`, `require_owner_or_roles()` |
| 10 | `core/auth_middleware.py` | Auth + AuthZ middleware | **ACTIVE** | AuthenticationMiddleware, AuthorizationMiddleware |

### 1.3 Specialized Auth Modules

| # | File Path | Role | Status | Notes |
|---|-----------|------|--------|-------|
| 11 | `core/two_factor_auth.py` | TOTP 2FA + backup codes | **ACTIVE** | REQ-1.5, REQ-1.6 compliance |
| 12 | `core/passwordless_auth.py` | Magic link + WebAuthn | **ACTIVE** | REQ-5.1-5.6 compliance |
| 13 | `core/oauth2_service.py` | Google OAuth2 | **ACTIVE** | REQ-2.1-2.6 compliance |
| 14 | `core/biometric_auth_service.py` | Touch ID / Face ID | **ACTIVE** | REQ-4.1-4.6 compliance |
| 15 | `core/learning_path_auth.py` | JWT for learning path API | **ACTIVE** | Uses `core.jwt_auth` directly |
| 16 | `core/session_auth_caching.py` | Session caching (in-memory) | **ACTIVE** | 2-hour TTL, fallback only |

### 1.4 Security Utilities

| # | File Path | Role | Status | Notes |
|---|-----------|------|--------|-------|
| 17 | `core/auth_rate_limiting.py` | Brute force protection | **ACTIVE** | In-memory, not Redis-backed |
| 18 | `core/auth_security_utils.py` | Threat analysis, GeoIP, TOTP | **ACTIVE** | SecurityLevel, ThreatType enums |

### 1.5 API Layer

| # | File Path | Role | Status | Notes |
|---|-----------|------|--------|-------|
| 19 | `api/auth.py` | Auth endpoints (login, register, logout, refresh) | **ACTIVE** | 61KB, uses `core.jwt_auth`, `core.dependencies` |

### 1.6 Duplicate/Related Files

| # | File Path | Role | Status | Notes |
|---|-----------|------|--------|-------|
| 20 | `core/jwt_auth_docker.py` | Docker-specific JWT (almost identical to jwt_auth.py) | **LEGACY** | File is ~60 lines, essentially duplicate |
| 21 | `api/two_factor_auth_api.py` | 2FA API endpoints | **ACTIVE** | Delegates to core/two_factor_auth.py |
| 22 | `api/enhanced_auth_api.py` | Enhanced auth endpoints | **ACTIVE** | Delegates to core/enhanced_authentication.py |

---

## 2. AUTH FLOW ARCHITECTURE

### 2.1 Token/JWT Flow

```
┌─────────────────────────────────────────────────────────────┐
│ TOKEN CREATION                                              │
│                                                             │
│ api/auth.py (login endpoint)                                │
│     │                                                        │
│     ├──> AuthService.hash_password()  [core/auth.py]        │
│     │                                                        │
│     ├──> JWTManager.create_access_token()  [core/jwt_auth.py]│
│     │    │                                                    │
│     │    └──> Uses: jwt_secret_key, jwt_algorithm            │
│     │         from core.config.settings                      │
│     │                                                        │
│     └──> Sets httpOnly cookie "access_token"                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TOKEN VALIDATION (per request)                             │
│                                                             │
│ core/dependencies.py :: get_current_user()                  │
│     │                                                        │
│     ├── 1. Try HTTPBearer header                           │
│     ├── 2. Fallback: httpOnly cookie "access_token"         │
│     │                                                        │
│     ├──> JWTManager.is_blacklisted_async()  [core/jwt_auth] │
│     │    │                                                    │
│     │    └──> Redis blacklist check                          │
│     │         └──> In-memory fallback if Redis unavailable   │
│     │                                                        │
│     └──> jwt.decode(token, JWT_SECRET, JWT_ALGORITHM)       │
│          │                                                   │
│          └──> Returns: AuthenticatedUser(id, username, role) │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Current User Resolution

| Entry Point | File | Used By |
|-------------|------|---------|
| **PRIMARY** `get_current_user()` | `core/dependencies.py` | 112 API files |
| `get_authenticated_user()` | `core/consolidated_auth_dependencies.py` | Wrapper |
| `authenticate_user()` | `core/auth_dependencies.py` | Delegates |
| `get_current_user_from_token()` | `core/learning_path_auth.py` | Learning path only |

### 2.3 Role/Permission Control

| System | File | Implementation |
|--------|------|----------------|
| **PRIMARY** RBAC | `core/rbac_system.py` | `get_rbac_manager()` singleton |
| Legacy RBAC | `core/auth.py` | `AuthService` class (basic) |
| IDOR Protection | `core/authorization.py` | `require_owner_or_roles()` |
| Role Helpers | `core/consolidated_auth_dependencies.py` | `RoleBasedAuth` class |

### 2.4 Session/Cookie Role

| Aspect | Implementation |
|--------|---------------|
| Token Storage | httpOnly cookie `access_token` (frontend) |
| Cookie Path | `/api` or `/api/v1/auth` |
| Refresh Token | httpOnly cookie `refresh_token` |
| Blacklist | Redis-backed with in-memory fallback |
| Session Cache | `core/session_auth_caching.py` (2-hour TTL, in-memory only) |

---

## 3. ACTIVE vs LEGACY CLASSIFICATION

### 3.1 Active Authority Sources

| # | Authority Source | Type | Used By |
|---|------------------|------|---------|
| 1 | `core/dependencies.py::get_current_user` | **PRIMARY** | 112 API files |
| 2 | `core/jwt_auth.py::JWTManager` | **PRIMARY** | Token management |
| 3 | `core/rbac_system.py` | **PRIMARY** | Role/permission system |
| 4 | `core/config.py` | **PRIMARY** | JWT settings (secret, algorithm, expiry) |

### 3.2 Legacy/Duplicate Modules

| # | File | Issue | Recommendation |
|---|------|-------|----------------|
| 1 | `core/jwt_auth_docker.py` | Near-duplicate of `jwt_auth.py` (~60 lines) | Merge or delete |
| 2 | `core/auth.py::AuthService` | Duplicates functionality in `jwt_auth.py` | Deprecate, use `jwt_auth.py` |
| 3 | `core/auth_dependencies.py` | Legacy wrapper, now delegates to `enhanced_authentication` | Consolidate |

### 3.3 Modules with Overlap

| Module A | Module B | Overlap |
|----------|----------|---------|
| `core/auth.py` (AuthService) | `core/jwt_auth.py` (JWTManager) | Password hashing, token creation |
| `core/auth_dependencies.py` | `core/consolidated_auth_dependencies.py` | Both provide FastAPI dependencies |
| `core/authorization.py` | `core/rbac_system.py` | Role checking |
| `core/session_auth_caching.py` | `core/jwt_auth.py` (Redis cache) | Session caching |

---

## 4. ENUM DUPLICATION ANALYSIS

### 4.1 UserRole Enum Locations

| File | Enum Definition | Usage |
|------|-----------------|-------|
| `models/enums_db.py` | **CANONICAL** `UserRole` | DB models, migrations |
| `core/jwt_auth.py` | `UserRole (str, Enum)` | JWT payload |
| `core/auth_middleware.py` | `UserRole (str, Enum)` | Middleware |
| `core/unified_auth_service.py` | `UserRole (str, Enum)` | Unified service |
| `core/auth.py` | (uses `models.user.KullaniciRolu`) | Legacy |

**Risk:** 4 separate `UserRole` enum definitions could cause type mismatch

### 4.2 TokenType Enum Locations

| File | Enum Definition |
|------|-----------------|
| `core/jwt_auth.py` | `TokenType (str, Enum)` - ACCESS, REFRESH, RESET_PASSWORD, EMAIL_VERIFICATION |
| `core/enhanced_authentication.py` | `TokenType (Enum)` - ACCESS, REFRESH, RESET, VERIFICATION, SESSION, API_KEY |
| `core/unified_auth_service.py` | `TokenType (str, Enum)` - ACCESS, REFRESH, RESET_PASSWORD, EMAIL_VERIFICATION, TWO_FACTOR |

**Risk:** 3 separate `TokenType` definitions

---

## 5. KEY FINDINGS

### 5.1 Active Authority (Source of Truth)

| Component | File | Evidence |
|-----------|------|----------|
| **Auth Entry Point** | `core/dependencies.py` | 112 API files import from here |
| **Token Management** | `core/jwt_auth.py` | JWTManager singleton with blacklist |
| **RBAC System** | `core/rbac_system.py` | get_rbac_manager() singleton |
| **Config** | `core/config.py` | jwt_secret_key, jwt_algorithm from settings |

### 5.2 Import Dependencies (112 API files)

```python
# How APIs get current user - 2 patterns:
# Pattern 1 (PRIMARY): from core.dependencies import get_current_user
# Pattern 2: from core.auth_dependencies import authenticate_user

# Direct imports from auth modules:
from core.jwt_auth import get_jwt_manager  # 50+ files
from core.enhanced_authentication import ...  # 13 files
from core.rbac_system import ...  # 13 files
from core.authorization import require_student_owner_or_privileged  # auth.py only
```

### 5.3 Dead Code Assessment

| File | Dead Code Evidence |
|------|---------------------|
| `core/auth.py::AuthService` | Still imported by `api/auth.py` (line 82+) but `jwt_auth.py` is primary |
| `core/jwt_auth_docker.py` | Docker-specific JWT, essentially duplicate of `jwt_auth.py` |
| `core/session_auth_caching.py` | In-memory only, no Redis backing - may be superseded by `jwt_auth.py` Redis cache |

---

## 6. SECURITY RISK ASSESSMENT

### 6.1 Confirmed Security Features

| Feature | Implementation | Status |
|---------|---------------|--------|
| Password Hashing | bcrypt via passlib | ✅ |
| JWT Expiry | 15 min access, 7 day refresh | ✅ |
| Token Blacklist | Redis-backed with in-memory fallback | ✅ |
| 2FA | TOTP via pyotp | ✅ |
| Rate Limiting | AuthRateLimiter (in-memory) | ⚠️ Not Redis |
| IDOR Protection | `require_owner_or_roles()` | ✅ |
| HTTP-only Cookies | `access_token`, `refresh_token` | ✅ |

### 6.2 Security Risks from Fragmentation

| Risk | Severity | Description |
|------|----------|-------------|
| Enum mismatch | MEDIUM | 4 UserRole definitions could cause runtime errors |
| Duplicate token creation | MEDIUM | `AuthService.create_access_token` vs `JWTManager.create_access_token` |
| Inconsistent rate limiting | MEDIUM | `auth_rate_limiting.py` in-memory only, Redis could help |
| Unclear authority | LOW | 3 different auth entry points could confuse developers |

---

## 7. SUMMARY STATISTICS

| Metric | Count |
|--------|-------|
| Total Auth-Related Files | 22 |
| Core Auth Modules | 18 |
| API Auth Files | 4 |
| **ACTIVE** (used in production) | 19 |
| **LEGACY/DUPLICATE** | 3 |
| FastAPI Dependency Entry Points | 3 |
| JWT Manager Classes | 2 (jwt_auth.py + jwt_auth_docker.py) |
| UserRole Enum Definitions | 4 |
| TokenType Enum Definitions | 3 |

---

## 8. CRITICAL 10 AUTH FILES (Priority Order)

| # | File | Priority Reason |
|---|------|-----------------|
| 1 | `core/dependencies.py` | **PRIMARY** - 112 API files depend on `get_current_user()` |
| 2 | `core/jwt_auth.py` | **PRIMARY** - Token management + blacklist |
| 3 | `core/rbac_system.py` | **PRIMARY** - Role/permission system |
| 4 | `core/enhanced_authentication.py` | **ACTIVE** - Multi-provider auth, session management |
| 5 | `core/unified_auth_service.py` | **ACTIVE** - Consolidated auth+authz service |
| 6 | `api/auth.py` | **ACTIVE** - Auth endpoints (61KB) |
| 7 | `core/config.py` | **CRITICAL** - JWT settings source |
| 8 | `core/authorization.py` | **ACTIVE** - IDOR protection |
| 9 | `core/two_factor_auth.py` | **ACTIVE** - 2FA implementation |
| 10 | `core/auth_rate_limiting.py` | **ACTIVE** - Brute force protection |

---

*Report Generated: 2026-04-05*
*No code changes made - analysis only*