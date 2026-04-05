# KIRO2 Auth Import Graph

**Generated:** 2026-04-05
**Purpose:** Document the actual import chains between auth modules
**Status:** VERIFIED - NO CODE CHANGES

---

## 1. IMPORT SUMMARY

| From | To | Count | Status |
|------|-----|-------|--------|
| `core.dependencies` | 93 API files | 95 imports | ✅ PRIMARY |
| `core.auth_dependencies` | 7 API files | 9 imports | ⚠️ SECONDARY |
| `core.jwt_auth` | 50+ API files | 50+ imports | ✅ ACTIVE |
| `core.rbac_system` | 13 API files | 13 imports | ✅ ACTIVE |
| `core.unified_auth_service` | ~10 files | ~10 imports | ⚠️ PARTIAL |
| `core.consolidated_auth_dependencies` | 0 files | 0 imports | ❌ DEAD |

---

## 2. PRIMARY IMPORT CHAIN

### 2.1 Entry Point: `core/dependencies.py`

```
API FILES (93 files, 95 imports)
    │
    └─> from core.dependencies import get_current_user
              │
              ├─> from core.jwt_auth import get_jwt_manager
              │         │
              │         ├─> from models.enums_db import UserRole
              │         │         └─> JWTManager.create_access_token(role.jwt_value)
              │         │
              │         ├─> from core.config import settings
              │         │         └─> JWT_SECRET, JWT_ALGORITHM
              │         │
              │         └─> Redis connection (blacklist)
              │
              └─> from core.rbac_system import get_rbac_manager
                        └─> RBAC checks
```

### 2.2 Key Files Importing `get_current_user`

| File | Import Statement |
|------|------------------|
| `api/auth.py` | `from core.dependencies import get_current_user, JWT_SECRET, ...` |
| `api/question_bank_api.py` | `from core.dependencies import get_current_user` |
| `api/learning_path_v2.py` | `from core.dependencies import get_current_user` |
| `api/exam_api.py` | `from core.dependencies import get_current_user` |
| `api/gamification_api.py` | `from core.dependencies import get_current_user` |
| `api/social_api.py` | `from core.dependencies import get_current_user` |
| `api/admin.py` | `from core.dependencies import get_current_user` |
| `api/parent.py` | `from core.dependencies import get_current_user` |
| `api/ogretmen.py` | `from core.dependencies import get_current_user` |
| ... (83 more files) | |

### 2.3 Files Importing `get_jwt_manager`

| File | Usage |
|------|-------|
| `api/auth.py` | Token creation, blacklist check |
| `api/learning_path_v2.py` | Token validation |
| `api/manipulatives_api.py` | Token validation |
| `api/khan_routes.py` | Token validation |
| `services/learning_path_service.py` | Service-level token operations |
| `services/auth_service.py` | Auth service operations |
| ... (43 more files) | |

---

## 3. SECONDARY IMPORT CHAIN

### 3.1 `core/auth_dependencies.py`

```
API FILES (7 files)
    │
    └─> from core.auth_dependencies import authenticate_user, require_roles, ...
              │
              ├─> from core.enhanced_authentication import ...
              │         └─> Multi-provider auth (OAuth2, 2FA, etc.)
              │
              ├─> from core.rbac_system import get_rbac_manager
              │         └─> RBAC checks
              │
              └─> from core.jwt_auth import get_jwt_manager
                        └─> Token operations
```

### 3.2 Key Files Using auth_dependencies

| File | Imports |
|------|---------|
| `api/auth.py` | `AuthenticationDependency`, `AuthorizationDependency` |
| `api/ogretmen.py` | `require_roles` |
| `api/parent.py` | `require_student_owner_or_privileged` |
| `api/khan_routes.py` | `require_roles` |
| `api/manipulatives_api.py` | `require_roles` |
| `api/exam_api.py` | `authenticate_user`, `require_roles` |
| `api/exam_results_api.py` | `authenticate_user` |

---

## 4. DEAD CODE CHAIN

### 4.1 `core/consolidated_auth_dependencies.py`

```
ZERO IMPORTERS
    │
    └─> This file is NEVER imported by any runtime code
              │
              ├─> Would delegate to: core.auth_dependencies
              │         └─> Would delegate to: core.enhanced_authentication
              │
              └─> Would provide: get_authenticated_user
                        └─> BUT: This function is NEVER called
```

**Status:** ❌ DEAD CODE - Created for consolidation but never adopted

---

## 5. TOKEN CREATION CHAINS

### 5.1 Standard Token Creation (jwt_auth.py)

```
api/auth.py::login()
    │
    └─> JWTManager.create_access_token()
              │
              ├─> settings.JWT_SECRET
              ├─> settings.JWT_ALGORITHM
              └─> role.jwt_value  ← LOWERCASE
                        │
                        └─> Token payload: {"sub": "1", "role": "student", ...}
```

### 5.2 Legacy Token Creation (jwt_auth_docker.py)

```
[Docker-specific code path - possibly api/auth.py in Docker]
    │
    └─> JWTManager.create_access_token() [jwt_auth_docker.py]
              │
              ├─> settings.JWT_SECRET (same)
              ├─> settings.JWT_ALGORITHM (same)
              └─> role.value  ← UPPERCASE (INCONSISTENT!)
                        │
                        └─> Token payload: {"sub": "1", "role": "STUDENT", ...}
```

---

## 6. ENUM IMPORT CHAINS

### 6.1 Canonical UserRole

```
models/enums_db.py
    │
    └─> class UserRole(str, Enum)
              │
              ├─> STUDENT = "STUDENT"
              ├─> TEACHER = "TEACHER"
              ├─> PARENT = "PARENT"
              └─> ADMIN = "ADMIN"
                    
Imported by:
  ├─> core/jwt_auth.py (for jwt_value property)
  ├─> core/jwt_auth_docker.py (for .value - UPPERCASE)
  ├─> core/auth_middleware.py
  ├─> core/unified_auth_service.py
  ├─> api/auth.py (for role mapping)
  └─> models/ (all model files)
```

### 6.2 jwt_value Property Chain

```
models.enums_db.UserRole
    │
    └─> @property jwt_value(self)
              │
              └─> Returns: self.value.lower()
                        │
                        └─> "STUDENT".lower() → "student"

Used by:
  └─> core/jwt_auth.py::JWTManager.create_access_token()
```

---

## 7. REQUEST VALIDATION CHAIN

### 7.1 Standard Validation

```
HTTP Request
    │
    ├─> HTTPBearer header OR httpOnly cookie
    │
    └─> Depends(get_current_user) [core/dependencies.py]
              │
              ├─> get_jwt_manager().is_blacklisted_async(token)
              │         │
              │         └─> Redis:BLACKLIST:{token_hash}
              │
              ├─> jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
              │         │
              │         └─> Returns: {"sub": "1", "role": "student", ...}
              │
              └─> AuthenticatedUser(**payload)
                        │
                        └─> role = "student" (string, not enum)
```

### 7.2 RBAC Check Chain

```
AuthenticatedUser(role="student")
    │
    └─> require_roles(user, ["student", "teacher"])
              │
              └─> get_rbac_manager().check_role(user.role, allowed_roles)
                        │
                        └─> role == "student" ✓
```

---

## 8. GRAPHICAL SUMMARY

```
┌─────────────────────────────────────────────────────────────────┐
│                         RUNTIME GRAPH                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   93 API Files                                                  │
│       │                                                         │
│       └─> core.dependencies.get_current_user ─────────┐        │
│                           │                             │        │
│                           │                             │        │
│       ┌───────────────────┼───────────────────┐         │        │
│       │                   │                   │         │        │
│       ▼                   ▼                   ▼         ▼        │
│  jwt_auth.py        rbac_system.py      enhanced_auth ─┘        │
│  (JWTManager)       (RBACManager)       (Multi-provider)        │
│       │                   │                   │                 │
│       │                   │                   │                 │
│       ▼                   │                   │                 │
│  Redis blacklist          │                   │                 │
│  (token invalidation)     │                   │                 │
│                           │                   │                 │
│                           ▼                   ▼                 │
│                     DB queries          OAuth2/2FA              │
│                     ( RBAC checks )     (special auth)           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                         DEAD CODE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   consolidated_auth_dependencies.py ──► 0 importers (DEAD)       │
│                                                                 │
│   auth.py::AuthService ──────────────► Replaced by jwt_auth.py │
│                                                                 │
│   jwt_auth_docker.py ─────────────────► Legacy (role mismatch!)  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. FILE COUNT BY MODULE

| Module | Import Count | Files |
|--------|-------------|-------|
| `core.dependencies` | 95 | 93 |
| `core.jwt_auth` | 50+ | 50+ |
| `core.rbac_system` | 13 | 13 |
| `core.auth_dependencies` | 9 | 7 |
| `core.enhanced_authentication` | 13 | 13 |
| `core.unified_auth_service` | ~10 | ~10 |
| `core.consolidated_auth_dependencies` | **0** | **0** |

---

*Report Generated: 2026-04-05*
*Analysis only - no code modifications made*
