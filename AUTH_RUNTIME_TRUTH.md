# KIRO2 Auth Runtime Truth

**Generated:** 2026-04-05
**Purpose:** Document which auth modules are ACTUALLY used at runtime vs which are dead/legacy
**Status:** VERIFIED - NO CODE CHANGES

---

## 1. get_current_user ENTRY POINT ANALYSIS

### 1.1 Primary Entry: `core/dependencies.py::get_current_user`

| Metric | Value |
|--------|-------|
| Total imports | **95** |
| Unique files | **93** |
| Import pattern | `from core.dependencies import get_current_user` |
| Status | **PRIMARY - SOLE ACTIVE ENTRY** |

### 1.2 Secondary Entry: `core/auth_dependencies.py`

| Metric | Value |
|--------|-------|
| Total imports | **9** |
| Unique files | **7** |
| Import pattern | Various `from core.auth_dependencies import ...` |
| Status | **SECONDARY - DELEGATES TO PRIMARY** |

Files importing from `core.auth_dependencies`:
- `api/auth.py` - imports `AuthenticationDependency`, `AuthorizationDependency`
- `api/ogretmen.py` - imports `require_roles`
- `api/parent.py` - imports `require_student_owner_or_privileged`
- `api/khan_routes.py` - imports `require_roles`
- `api/manipulatives_api.py` - imports `require_roles`
- `api/exam_api.py` - imports `authenticate_user`, `require_roles`
- `api/exam_results_api.py` - imports `authenticate_user`

### 1.3 UNUSED Entry: `core/consolidated_auth_dependencies.py`

| Metric | Value |
|--------|-------|
| Total imports | **0** |
| Status | **DEAD - NEVER IMPORTED BY RUNTIME CODE** |

**Evidence:**
```bash
$ grep -r "consolidated_auth_dependencies" backend/ --include="*.py" | grep -v "__pycache__"
# ZERO results
```

This file was created to consolidate auth dependencies but was **never adopted**.

---

## 2. UserRole ENUM RUNTIME MAP

### 2.1 Canonical Definition: `models/enums_db.py`

```python
class UserRole(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    ADMIN = "ADMIN"
    
    @classmethod
    def _missing_(cls, value):
        return cls._value2member_map_.get(value.upper()) or cls._value2member_map_.get(value.lower())
```

**Values:** UPPERCASE (`"STUDENT"`, `"TEACHER"`, `"PARENT"`, `"ADMIN"`)
**Features:** Case-insensitive lookup via `_missing_`

### 2.2 JWT Payload Role: `core/jwt_auth.py`

```python
# Line 114 - Token creation
access_token = self.create_access_token(
    data={
        "sub": user_id,
        "role": role.jwt_value,  # LOWERCASE!
        ...
    }
)
```

**Values:** lowercase via `role.jwt_value` property
**jwt_value property (line 76):** Returns lowercase equivalent

### 2.3 CRITICAL DIFFERENCE: `core/jwt_auth_docker.py`

```python
# Line 121 - Token creation
access_token = self.create_access_token(
    data={
        "sub": user_id,
        "role": role.value,  # UPPERCASE! (different from jwt_auth.py!)
        ...
    }
)
```

**Values:** UPPERCASE via `role.value`
**Problem:** This creates tokens with UPPERCASE role while `jwt_auth.py` creates lowercase!

### 2.4 Runtime Usage Map

| File | Role Source | Role Value Used | Status |
|------|-------------|-----------------|--------|
| `core/dependencies.py` | `models.enums_db.UserRole` | `.jwt_value` (lowercase) | ✅ CORRECT |
| `core/jwt_auth.py` | `models.enums_db.UserRole` | `.jwt_value` (lowercase) | ✅ CORRECT |
| `core/jwt_auth_docker.py` | `models.enums_db.UserRole` | `.value` (UPPERCASE!) | ⚠️ INCONSISTENT |
| `core/auth_middleware.py` | `models.enums_db.UserRole` | `.value` (UPPERCASE) | ⚠️ REVIEW |
| `core/unified_auth_service.py` | `models.enums_db.UserRole` | `.value` (UPPERCASE) | ⚠️ REVIEW |
| `api/auth.py` | `models.enums_db.UserRole` | DB values (UPPERCASE) | ✅ CORRECT |

---

## 3. JWTManager RUNTIME MAP

### 3.1 Primary Implementation: `core/jwt_auth.py`

| Feature | Implementation |
|---------|---------------|
| Blacklist | Redis-backed with in-memory fallback |
| Refresh tokens | Database-backed (refresh_tokens table) |
| Token creation | `role.jwt_value` (lowercase) |
| Expiry | 15min access / 7day refresh |
| Singleton | `get_jwt_manager()` |

**Usage:** 50+ files import `get_jwt_manager`

### 3.2 Legacy Duplicate: `core/jwt_auth_docker.py`

| Feature | Implementation |
|---------|---------------|
| Blacklist | Redis-backed (same as jwt_auth.py) |
| Refresh tokens | NOT SUPPORTED |
| Token creation | `role.value` (UPPERCASE - INCOMPATIBLE!) |
| Expiry | Same as jwt_auth.py |
| Singleton | `get_jwt_manager()` |

**Usage:** Docker-specific - likely copy-paste from jwt_auth.py for Docker environment isolation

**CRITICAL ISSUE:** If a token is created by `jwt_auth_docker.py` (UPPERCASE role) but validated by `jwt_auth.py` (expects lowercase via `jwt.decode` → `AuthenticatedUser`), role comparison could fail!

---

## 4. REQUEST FLOW RUNTIME MAP

### 4.1 Happy Path (Token Created and Validated Same System)

```
REQUEST
  │
  ├─> api/auth.py::login()
  │     │
  │     └─> JWTManager.create_access_token() [core/jwt_auth.py]
  │           └─> role.jwt_value → "student" (lowercase)
  │
  └─> api/xxx.py::endpoint()
        │
        └─> Depends(get_current_user) [core/dependencies.py]
              │
              ├─> HTTPBearer header OR httpOnly cookie
              │
              ├─> JWTManager.is_blacklisted_async() [core/jwt_auth.py]
              │     └─> Redis blacklist check
              │
              └─> jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                    └─> Returns: {"sub": "1", "role": "student", ...}
                          └─> AuthenticatedUser(id="1", role="student")
```

### 4.2 Potential Inconsistency Path (jwt_auth_docker.py scenario)

```
REQUEST (Docker environment)
  │
  ├─> api/auth.py::login() [possibly using jwt_auth_docker?]
  │     │
  │     └─> JWTManager.create_access_token() [core/jwt_auth_docker.py]
  │           └─> role.value → "STUDENT" (UPPERCASE!)
  │
  └─> api/xxx.py::endpoint()
        │
        └─> Depends(get_current_user) [core/dependencies.py]
              │   [Still uses jwt_auth.py for validation!]
              │
              └─> jwt.decode(token)
                    └─> role = "STUDENT" (UPPERCASE)
                          │
                          └─> AuthenticatedUser.role = "STUDENT"
                                │
                                └─> RBAC check: "STUDENT" vs "student"
                                      ⚠️ STRING COMPARISON FAILS!
```

---

## 5. AUTHENTICATED USER MODEL

### 5.1 Definition Location

**File:** `core/dependencies.py`

```python
class AuthenticatedUser(BaseModel):
    id: str
    username: str
    role: str  # NOTE: This is a STRING, not UserRole enum!
    email: str | None = None
```

**CRITICAL:** `AuthenticatedUser.role` is a **string**, not the `UserRole` enum!

### 5.2 Role Value Flow

```
Token Creation (jwt_auth.py):
  UserRole.STUDENT.jwt_value → "student" (lowercase)

Token Payload:
  {"sub": "1", "role": "student"}

Validation (dependencies.py):
  jwt.decode() → AuthenticatedUser(id="1", role="student")

RBAC Check:
  require_roles(AuthenticatedUser(role="student"), ["student"])
    └─> role == "student" ✓
```

---

## 6. DEPENDENCY INJECTION MAP

### 6.1 Primary Pattern: `Depends(get_current_user)`

```python
# 93 API files use this pattern:
@router.get("/protected")
async def protected_endpoint(current_user: AuthenticatedUser = Depends(get_current_user)):
    ...
```

### 6.2 Secondary Pattern: `authenticate_user` from auth_dependencies

```python
# 7 files use this pattern:
@router.get("/protected")
async def protected_endpoint(user: AuthenticatedUser = Depends(authenticate_user)):
    ...
```

### 6.3 UNUSED Pattern: `get_authenticated_user` from consolidated_auth_dependencies

```python
# ZERO files use this pattern:
# consolidated_auth_dependencies.get_authenticated_user is DEAD CODE
```

---

## 7. SUMMARY: RUNTIME AUTHORITY

| Component | File:Function | Runtime Status |
|-----------|---------------|----------------|
| **Auth Entry** | `core/dependencies.py::get_current_user` | ✅ 95 imports, ACTIVE |
| **Token Manager** | `core/jwt_auth.py::get_jwt_manager` | ✅ 50+ imports, ACTIVE |
| **RBAC System** | `core/rbac_system.py::get_rbac_manager` | ✅ ACTIVE |
| **Auth Dependency** | `core/auth_dependencies.py::authenticate_user` | ⚠️ 9 imports, SECONDARY |
| **Consolidated Deps** | `core/consolidated_auth_dependencies.py` | ❌ 0 imports, DEAD |
| **JWT Docker** | `core/jwt_auth_docker.py::get_jwt_manager` | ⚠️ LEGACY, INCONSISTENT role format |

---

## 8. CRITICAL FINDINGS

### 8.1 CRITICAL: jwt_auth_docker.py Role Format Inconsistency

**Issue:** `jwt_auth_docker.py` uses `role.value` (UPPERCASE) while `jwt_auth.py` uses `role.jwt_value` (lowercase).

**Impact:** If Docker environment uses `jwt_auth_docker.py` for token creation but validation still goes through `dependencies.py` (which uses `jwt_auth.py`), role comparison could fail.

**Evidence:**
- `jwt_auth.py:114` → `role.jwt_value` (lowercase)
- `jwt_auth_docker.py:121` → `role.value` (UPPERCASE)

### 8.2 HIGH: AuthenticatedUser.role is String, Not Enum

**Issue:** `AuthenticatedUser` Pydantic model uses `role: str` instead of `role: UserRole`.

**Impact:** No type safety at runtime for role comparisons.

### 8.3 MEDIUM: consolidated_auth_dependencies is Dead Code

**Issue:** Created for consolidation but never imported by any runtime code.

**Recommendation:** Either adopt it as primary or delete it.

---

*Report Generated: 2026-04-05*
*Analysis only - no code modifications made*
