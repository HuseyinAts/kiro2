# Design Document - Auth Enhancement

## Overview

Auth Enhancement sistemi, kimlik doğrulama sistemini MFA, OAuth2, SSO, biometric auth ve passwordless authentication ile güçlendirir. Gelişmiş güvenlik özellikleri ve modern authentication yöntemleri sağlar.

**Temel Özellikler:**
- Multi-Factor Authentication (TOTP)
- OAuth2 social login (Google, GitHub)
- SAML 2.0 SSO
- Biometric authentication (Touch ID, Face ID)
- Passwordless auth (Magic Link, WebAuthn/FIDO2)
- Advanced session management
- Role-Based Access Control (RBAC)
- Account security features

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Layer                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Password   │  │    OAuth2    │  │     SSO      │
│     Auth     │  │  (Google)    │  │  (SAML 2.0)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Factor Authentication                         │
│         (TOTP, Backup Codes, Email Verification)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Biometric   │  │ Passwordless │  │   Session    │
│    Auth      │  │(Magic Link)  │  │  Management  │
└──────────────┘  └──────────────┘  └──────┬───────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              Role-Based Access Control                           │
│         (Student, Teacher, Admin + Permissions)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
backend/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── password_auth.py          # Traditional password
│   │   ├── mfa.py                    # TOTP, backup codes
│   │   ├── oauth2.py                 # Google, GitHub OAuth
│   │   ├── sso.py                    # SAML 2.0 SSO
│   │   ├── biometric.py              # Biometric auth
│   │   ├── passwordless.py           # Magic link, WebAuthn
│   │   ├── session.py                # Session management
│   │   ├── rbac.py                   # Role-based access
│   │   └── security.py               # Account security
│   ├── models/
│   │   ├── user.py                   # User model
│   │   ├── mfa_device.py             # MFA devices
│   │   ├── oauth_account.py          # OAuth accounts
│   │   └── session.py                # Session model
│   └── api/v1/
│       └── auth.py                   # Auth endpoints
├── tests/
│   └── auth/
│       ├── test_mfa.py
│       ├── test_oauth2.py
│       └── test_session.py
└── requirements_auth.txt
```

## Data Models

```python
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class MFAMethod(str, Enum):
    TOTP = "totp"
    BACKUP_CODE = "backup_code"
    EMAIL = "email"

class User(BaseModel):
    id: int
    email: EmailStr
    password_hash: Optional[str]
    role: UserRole
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    backup_codes: List[str] = []
    oauth_accounts: List[str] = []
    created_at: datetime
    last_login: Optional[datetime]

class Session(BaseModel):
    session_id: str
    user_id: int
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

class OAuthAccount(BaseModel):
    provider: str  # google, github
    provider_user_id: str
    user_id: int
    access_token: str
    refresh_token: Optional[str]
    expires_at: datetime
```

## Correctness Properties

### Property 1: MFA Token Validity
*For any* TOTP token, *it SHALL be valid only within 30-second time window.*

**Validates: Requirements REQ-1.3**

### Property 2: Session Timeout Enforcement
*For any* session, *it SHALL expire after 30 minutes of inactivity or 24 hours absolute.*

**Validates: Requirements REQ-6.2**

### Property 3: OAuth2 State Parameter
*For any* OAuth2 flow, *state parameter SHALL prevent CSRF attacks.*

**Validates: Requirements REQ-2.3**

### Property 4: Role Permission Inheritance
*For any* role hierarchy, *child roles SHALL inherit parent permissions.*

**Validates: Requirements REQ-7.3**

## Testing Strategy

### Unit Tests
- Test TOTP generation and validation
- Test OAuth2 token exchange
- Test session timeout logic
- Test RBAC permission checks

### Property-Based Tests
- Generate random TOTP tokens
- Verify session timeout enforcement
- Verify OAuth2 state validation
- Verify role permission inheritance

### Integration Tests
- Test full MFA flow
- Test OAuth2 login flow
- Test SSO SAML flow
- Test session management

**Test Configuration**: Minimum 100 iterations per property test

## Security Considerations

### Password Security
- Bcrypt hashing (rounds=12)
- Minimum 8 characters
- Complexity requirements

### Token Security
- Cryptographically secure random generation
- Short expiration times
- One-time use enforcement

### Session Security
- HttpOnly, Secure, SameSite cookies
- IP + User-Agent binding
- Concurrent session limits

### MFA Security
- TOTP secret encryption at rest
- Backup codes hashed
- Rate limiting on verification attempts
