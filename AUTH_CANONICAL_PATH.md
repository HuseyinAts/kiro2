# KIRO2 Auth Canonical Path

**Generated:** 2026-04-05
**Purpose:** Document the ACTUAL production auth flow with real file/function names
**Status:** VERIFIED - NO CODE CHANGES

---

## 1. PRODUCTION AUTH FLOW

### 1.1 Canonical Request Path

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TOKEN CREATION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

USER LOGIN
    │
    ▼
api/auth.py::login_secure()
    │
    ├─> 1. Validate credentials
    │         │
    │         └─> AuthService.authenticate_user() [core/auth.py]
    │                   │
    │                   └─> bcrypt.verify(password, stored_hash)
    │
    ├─> 2. Get user role
    │         │
    │         └─> db.query(User).filter(User.id == user_id)
    │                   │
    │                   └─> user.role → UserRole enum (UPPERCASE: "STUDENT")
    │
    ├─> 3. Create access token
    │         │
    │         └─> get_jwt_manager().create_access_token() [core/jwt_auth.py]
    │                   │
    │                   ├─> JWTManager.create_access_token()
    │                   │         │
    │                   │         ├─> jwt.encode({
    │                   │         │       "sub": user_id,
    │                   │         │       "role": role.jwt_value,  ← "student" (lowercase)
    │                   │         │       "type": "access",
    │                   │         │       "exp": datetime.utcnow() + 15min
    │                   │         │   }, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    │                   │         │
    │                   │         └─> Returns: JWT string
    │                   │
    │                   └─> Store in Redis blacklist (empty initially)
    │
    └─> 4. Set httpOnly cookie
              │
              └─> response.set_cookie(
                      key="access_token",
                      value=jwt_string,
                      httponly=True,
                      secure=not IS_DEV,
                      samesite="lax",
                      max_age=15*60
                  )

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOKEN VALIDATION FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

PROTECTED API REQUEST
    │
    ▼
Any API endpoint
    │
    └─> Depends(get_current_user) [core/dependencies.py:55]
              │
              ├─> 1. Extract token
              │         │
              │         ├─> Try: Authorization header (Bearer token)
              │         │
              │         └─> Fallback: request.cookies.get("access_token")
              │
              ├─> 2. Check blacklist
              │         │
              │         └─> get_jwt_manager().is_blacklisted_async(token)
              │                   │
              │                   ├─> Redis GET "blacklist:{token_hash}"
              │                   │
              │                   └─> If found → HTTP 401 "Token has been revoked"
              │
              ├─> 3. Decode token
              │         │
              │         └─> jwt.decode(
              │                   token,
              │                   settings.JWT_SECRET,
              │                   algorithms=[settings.JWT_ALGORITHM]
              │               )
              │                   │
              │                   └─> Returns payload: {
              │                           "sub": "1",
              │                           "role": "student",  ← lowercase
              │                           "type": "access",
              │                           "exp": 1743849600
              │                       }
              │
              └─> 4. Create AuthenticatedUser
                        │
                        └─> AuthenticatedUser(
                                id=payload["sub"],           # "1"
                                username=payload.get("username", ""),
                                role=payload["role"],        # "student" (string!)
                                email=payload.get("email")
                            )

═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                           RBAC CHECK FLOW                                    │
└─────────────────────────────────────────────────────────────────────────────┘

PROTECTED RESOURCE
    │
    ▼
@require_roles(["student", "teacher"])
    │
    └─> core/authorization.py::require_roles()
              │
              ├─> 1. Get user role
              │         │
              │         └─> current_user.role  # "student" (string)
              │
              ├─> 2. Check against allowed roles
              │         │
              │         └─> if current_user.role not in allowed_roles:
              │                   raise HTTP 403 Forbidden
              │
              └─> 3. If allowed → proceed to endpoint

```

---

## 2. KEY FILES AND FUNCTIONS

### 2.1 Token Creation

| File | Function | Line | Purpose |
|------|----------|------|---------|
| `api/auth.py` | `login_secure()` | ~100 | Login endpoint |
| `core/auth.py` | `AuthService.authenticate_user()` | ~150 | Credential validation |
| `core/jwt_auth.py` | `JWTManager.create_access_token()` | ~110 | JWT creation |
| `core/jwt_auth.py` | `JWTManager.create_refresh_token()` | ~130 | Refresh token creation |

### 2.2 Token Validation

| File | Function | Line | Purpose |
|------|----------|------|---------|
| `core/dependencies.py` | `get_current_user()` | ~55 | **PRIMARY AUTH ENTRY POINT** |
| `core/jwt_auth.py` | `JWTManager.is_blacklisted_async()` | ~200 | Blacklist check |
| `core/jwt_auth.py` | `JWTManager.verify_token()` | ~180 | Token verification |
| `core/dependencies.py` | `AuthenticatedUser` | ~40 | Response model |

### 2.3 Authorization

| File | Function | Line | Purpose |
|------|----------|------|---------|
| `core/authorization.py` | `require_roles()` | ~30 | Role-based access check |
| `core/authorization.py` | `require_owner_or_roles()` | ~50 | IDOR protection |
| `core/rbac_system.py` | `get_rbac_manager()` | ~100 | RBAC singleton |
| `core/rbac_system.py` | `RBACManager.check_permission()` | ~150 | Permission check |

---

## 3. CANONICAL DATA FLOW

### 3.1 Token Payload Structure

```python
# Access Token Payload (jwt_auth.py:110-120)
{
    "sub": "123",                    # User ID (string)
    "role": "student",               # Role (lowercase string!)
    "type": "access",                # Token type
    "email": "user@example.com",     # Optional email
    "username": "testuser",          # Optional username
    "exp": 1743849600,               # Expiry timestamp
    "iat": 1743846000,               # Issued at
    "jti": "unique-token-id"         # JWT ID (for blacklist)
}
```

### 3.2 AuthenticatedUser Structure

```python
# core/dependencies.py:40-50
class AuthenticatedUser(BaseModel):
    id: str                          # From token "sub"
    username: str                    # From token
    role: str                        # From token "role" (STRING, not enum!)
    email: str | None = None         # From token
```

### 3.3 Role Value Mapping

```python
# Token creation: UPPERCASE enum → lowercase string
UserRole.STUDENT           →  "student"   (via .jwt_value)
UserRole.TEACHER           →  "teacher"
UserRole.PARENT            →  "parent"
UserRole.ADMIN             →  "admin"

# RBAC check: string comparison
"student" in ["student", "teacher"]  →  ✅ ALLOW
"student" in ["admin"]              →  ❌ DENY
```

---

## 4. BLACKLIST FLOW

### 4.1 Token Invalidation (Logout)

```
USER LOGOUT
    │
    ▼
api/auth.py::logout()
    │
    └─> get_jwt_manager().revoke_token()
              │
              ├─> 1. Decode token (without verification to get jti)
              │         └─> payload = jwt.decode(token, options={"verify_signature": False})
              │
              ├─> 2. Add to Redis blacklist
              │         │
              │         └─> Redis SET "blacklist:{jti}" "revoked" EX 604800  (7 days)
              │
              └─> 3. Clear httpOnly cookie
                        └─> response.delete_cookie("access_token")
```

### 4.2 Token Validation with Blacklist

```
get_current_user()
    │
    ├─> Extract token
    │
    ├─> Decode header to get jti (without full verification)
    │         └─> unverified_header = jwt.get_unverified_header(token)
    │
    ├─> Check Redis
    │         └─> EXISTS "blacklist:{jti}"
    │              │
    │              ├─> YES → raise HTTP 401 "Token revoked"
    │              │
    │              └─> NO → continue to verify_signature
    │
    └─> Full jwt.decode() with signature verification
```

---

## 5. REDIS-BACKED SESSION

### 5.1 Session Storage

```python
# core/jwt_auth.py - Refresh token storage
async def store_refresh_token(self, user_id: str, token: str, expires_at: datetime):
    # Store in refresh_tokens table (DB)
    # OR store in Redis for short-lived sessions
```

### 5.2 Rate Limiting (auth_rate_limiting.py)

```python
# In-memory rate limiter (NOT Redis-backed)
AuthRateLimiter:
    max_attempts = 5      # per window
    window = 60 seconds   # per user
    lockout = 300 seconds # after max_attempts
```

---

## 6. DUAL AUTH SUPPORT

### 6.1 Cookie Auth (Frontend)

```
Browser Request
    │
    └─> Automatic httpOnly cookie inclusion
              │
              └─> cookie: access_token=xxx; refresh_token=yyy
```

### 6.2 Bearer Auth (API Clients)

```
API Client Request
    │
    └─> Authorization: Bearer <jwt_token>
```

### 6.3 get_current_user Resolution

```python
# core/dependencies.py::get_current_user()
async def get_current_user(
    credentials = HTTPBearer(auto_error=False)
) -> AuthenticatedUser:
    #
    if credentials:
        # Bearer token from Authorization header
        token = credentials.credentials
    else:
        # Fallback to httpOnly cookie
        token = request.cookies.get("access_token")

    # Rest of validation...
```

---

## 7. CRITICAL PATH SUMMARY

### 7.1 Primary Authority Chain

```
QUESTION: Bugün production auth için asıl otorite hangi dosya/fonksiyon zinciri?

ANSWER:

1. REQUEST → Depends(get_current_user)
   File: core/dependencies.py:55
   Function: get_current_user()
   Import: 93 API files, 95 imports

2. → JWTManager.is_blacklisted_async()
   File: core/jwt_auth.py:200
   Function: JWTManager.is_blacklisted_async()
   Purpose: Redis blacklist check

3. → jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
   File: core/jwt_auth.py:180
   Function: JWTManager.verify_token()
   Purpose: Cryptographic verification

4. → AuthenticatedUser(id, username, role, email)
   File: core/dependencies.py:40
   Class: AuthenticatedUser
   Purpose: Typed user representation

5. → require_roles() OR require_owner_or_roles()
   File: core/authorization.py:30
   Function: require_roles()
   Purpose: Authorization check
```

### 7.2 Token Creation Chain

```
1. api/auth.py::login_secure()
   File: api/auth.py:100
   Purpose: Login endpoint

2. → JWTManager.create_access_token()
   File: core/jwt_auth.py:110
   Purpose: Create JWT with role.jwt_value (lowercase)

3. → Redis blacklist initialization
   File: core/jwt_auth.py
   Purpose: Empty blacklist for new token
```

---

## 8. DECISION TABLE

| Module | Status | Action |
|--------|--------|--------|
| `core/dependencies.py::get_current_user` | ✅ PRIMARY | KEEP |
| `core/jwt_auth.py::JWTManager` | ✅ PRIMARY | KEEP |
| `core/rbac_system.py` | ✅ ACTIVE | KEEP |
| `core/authorization.py` | ✅ ACTIVE | KEEP |
| `api/auth.py::login_secure` | ✅ ACTIVE | KEEP |
| `core/auth_dependencies.py` | ⚠️ SECONDARY | ALIAS to primary |
| `core/consolidated_auth_dependencies.py` | ❌ DEAD | DELETE |
| `core/jwt_auth_docker.py` | ⚠️ LEGACY | MERGE with jwt_auth.py |
| `core/auth.py::AuthService` | ⚠️ LEGACY | DEPRECATE (duplicates jwt_auth) |
| `core/enhanced_authentication.py` | ⚠️ PARTIAL | KEEP for special auth (OAuth2, 2FA) |
| `core/unified_auth_service.py` | ⚠️ PARTIAL | ADOPT or DEPRECATE |

---

*Report Generated: 2026-04-05*
*Analysis only - no code modifications made*
