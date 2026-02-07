# KIRO2 Authentication Guide

Comprehensive guide for implementing authentication in KIRO2 Türkiye Üniversite Sınavları Hazırlık Platformu.

## Table of Contents

- [Overview](#overview)
- [Authentication Flow](#authentication-flow)
- [Registration](#registration)
- [Login](#login)
- [Token Management](#token-management)
- [Profile Management](#profile-management)
- [Role-Based Access Control](#role-based-access-control)
- [Security Best Practices](#security-best-practices)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)

## Overview

KIRO2 uses JWT (JSON Web Token) based authentication with refresh token rotation for secure API access. The platform supports four user roles with different access levels.

### Key Features

- **JWT Access Tokens**: Short-lived tokens (1 hour) for API access
- **Refresh Token Rotation**: Long-lived refresh tokens (7 days) with automatic rotation
- **Strong Password Policy**: Enforced complexity requirements (OWASP compliant)
- **Role-Based Access**: Four user roles with granular permissions
- **Multi-Device Support**: Track and revoke tokens per device
- **Rate Limiting**: Protection against brute force attacks
- **IDOR Prevention**: Authorization checks for all protected resources

### User Roles

| Role | Description | Permissions |
|------|-------------|------------|
| `ogrenci` | Student user (default) | Access to exams, learning paths, personal analytics |
| `veli` | Parent user | View child performance, receive notifications |
| `ogretmen` | Teacher user | Create content, manage classes, view student analytics |
| `admin` | System administrator | User management, system configuration |
| `super_admin` | Super administrator | Full system access, audit logs |

## Authentication Flow

```
┌─────────┐                                              ┌─────────┐
│ Client  │                                              │ Server  │
└────┬────┘                                              └────┬────┘
     │                                                         │
     │ 1. POST /api/v1/auth/kayit                             │
     │────────────────────────────────────────────────────────>│
     │                                                         │
     │ 2. 201 Created (User created)                          │
     │<────────────────────────────────────────────────────────│
     │                                                         │
     │ 3. POST /api/v1/auth/giris                             │
     │    (email, password)                                   │
     │────────────────────────────────────────────────────────>│
     │                                                         │
     │ 4. 200 OK (access_token, refresh_token)                │
     │<────────────────────────────────────────────────────────│
     │                                                         │
     │ 5. GET /api/v1/auth/profil                             │
     │    Authorization: Bearer <access_token>                │
     │────────────────────────────────────────────────────────>│
     │                                                         │
     │ 6. 200 OK (User profile)                               │
     │<────────────────────────────────────────────────────────│
     │                                                         │
     │ ... (45 minutes later - token refresh)                 │
     │                                                         │
     │ 7. POST /api/v1/auth/refresh                           │
     │    Authorization: Bearer <refresh_token>               │
     │────────────────────────────────────────────────────────>│
     │                                                         │
     │ 8. 200 OK (new access_token, new refresh_token)        │
     │<────────────────────────────────────────────────────────│
     │                                                         │
     │ 9. POST /api/v1/auth/cikis                             │
     │    Authorization: Bearer <access_token>                │
     │────────────────────────────────────────────────────────>│
     │                                                         │
     │ 10. 200 OK (Logged out successfully)                   │
     │<────────────────────────────────────────────────────────│
     │                                                         │
```

## Registration

### Endpoint

```
POST /api/v1/auth/kayit
```

### Request Body

```json
{
  "email": "ahmet@example.com",
  "ad_soyad": "Ahmet Yılmaz",
  "sifre": "GucluSifre123!",
  "rol": "ogrenci",
  "telefon": "+905551234567",
  "aktif": true
}
```

### Password Requirements (SECURITY)

Passwords must meet the following criteria:

- **Minimum 8 characters**
- At least **one uppercase letter** (A-Z)
- At least **one lowercase letter** (a-z)
- At least **one digit** (0-9)
- At least **one special character** (!@#$%^&* etc.)
- Cannot be a **common password** (password123, 12345678, etc.)

### Response (201 Created)

```json
{
  "kullanici_id": "usr_1a2b3c4d5e6f",
  "email": "ahmet@example.com",
  "ad_soyad": "Ahmet Yılmaz",
  "rol": "ogrenci",
  "aktif": true,
  "olusturma_tarihi": "2025-11-17T10:30:00Z",
  "son_giris": null
}
```

### Error Responses

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Email already exists | Email address is already registered |
| 400 | Weak password | Password doesn't meet security requirements |
| 422 | Validation error | Invalid email format or missing required fields |

### Example (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/kayit" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmet@example.com",
    "ad_soyad": "Ahmet Yılmaz",
    "sifre": "GucluSifre123!",
    "rol": "ogrenci"
  }'
```

## Login

### Endpoint

```
POST /api/v1/auth/giris
```

### Request Body

```json
{
  "email": "ahmet@example.com",
  "sifre": "GucluSifre123!"
}
```

### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfMWEyYjNjNGQ1ZTZmIiwiZXhwIjoxNzAwNDU2Nzg5fQ.xyz",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfMWEyYjNjNGQ1ZTZmIiwiZXhwIjoxNzAwNDU2Nzg5fQ.abc",
  "token_type": "bearer",
  "expires_in": 3600,
  "kullanici": {
    "kullanici_id": "usr_1a2b3c4d5e6f",
    "email": "ahmet@example.com",
    "ad_soyad": "Ahmet Yılmaz",
    "rol": "ogrenci",
    "aktif": true,
    "son_giris": "2025-11-17T14:30:00Z"
  }
}
```

### Error Responses

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Invalid credentials | Email or password is incorrect |
| 401 | Account disabled | User account has been deactivated |
| 422 | Validation error | Invalid email format |

### Rate Limiting

- **5 failed login attempts** triggers temporary account lock (15 minutes)
- **10 failed attempts** from same IP blocks IP for 1 hour
- Successful login resets failed attempt counter

### Example (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/giris" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ahmet@example.com",
    "sifre": "GucluSifre123!"
  }'
```

## Token Management

### Token Types

#### Access Token
- **Purpose**: API authentication
- **Lifetime**: 1 hour (3600 seconds)
- **Usage**: Send in Authorization header for all protected endpoints
- **Format**: `Authorization: Bearer <access_token>`

#### Refresh Token
- **Purpose**: Renew access tokens without re-login
- **Lifetime**: 7 days
- **Usage**: Send to `/refresh` endpoint to get new access token
- **Rotation**: New refresh token issued with each refresh (old one is revoked)

### Token Refresh

**When to refresh:**
- Access token expires in less than 15 minutes (recommended: 75% of lifetime = 45 min)
- Access token has expired (backend returns 401)
- Proactive refresh before API calls

**Endpoint:**
```
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Security Features:**
- **Token Rotation**: Each refresh generates a new refresh token
- **Old Token Revocation**: Previous refresh token is automatically invalidated
- **Replay Attack Prevention**: Revoked tokens cannot be reused
- **Device Tracking**: Optional IP and User-Agent validation

### Logout (Single Device)

Invalidate current access token:

```
POST /api/v1/auth/cikis
Authorization: Bearer <access_token>
```

### Logout (All Devices)

Revoke all refresh tokens for the user:

```
POST /api/v1/auth/logout-all
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Tüm cihazlardan başarıyla çıkış yapıldı"
}
```

### Revoke Device Tokens

Revoke tokens for a specific device:

```
POST /api/v1/auth/revoke-device
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "device_id": "device_123"
}
```

## Profile Management

### Get Profile

```
GET /api/v1/auth/profil
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "kullanici_id": "usr_1a2b3c4d5e6f",
  "email": "ahmet@example.com",
  "ad_soyad": "Ahmet Yılmaz",
  "rol": "ogrenci",
  "aktif": true,
  "olusturma_tarihi": "2025-11-17T10:30:00Z",
  "son_giris": "2025-11-17T14:30:00Z",
  "telefon": "+905551234567"
}
```

### Create Student Profile

```
POST /api/v1/auth/ogrenci-profil
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "sinif_seviyesi": 12,
  "okul_adi": "Atatürk Anadolu Lisesi",
  "hedef_sinav": "TYT",
  "hedef_universiteler": ["ODTÜ", "Boğaziçi", "İTÜ"],
  "ogrenme_stili": "visual",
  "gunluk_calisma_hedefi": 180,
  "guclu_alanlar": ["matematik", "fizik"],
  "zayif_alanlar": ["tarih", "edebiyat"]
}
```

## Role-Based Access Control

### Authorization Checks

Every protected endpoint performs role-based authorization:

```python
# Example: Student can only access their own data
@router.get("/ogrenci-profil/{ogrenci_id}")
async def get_student_profile(
    ogrenci_id: str,
    current_user: User = Depends(get_current_user)
):
    # IDOR Prevention
    require_student_owner_or_privileged(current_user, ogrenci_id)
    # ... rest of endpoint logic
```

### Permission Matrix

| Endpoint | Student | Parent | Teacher | Admin |
|----------|---------|--------|---------|-------|
| View own profile | ✅ | ✅ | ✅ | ✅ |
| View student analytics | Own only | Child only | Class only | All |
| Create exam | ❌ | ❌ | ✅ | ✅ |
| Manage users | ❌ | ❌ | ❌ | ✅ |
| View audit logs | ❌ | ❌ | ❌ | ✅ |
| System config | ❌ | ❌ | ❌ | Super Admin |

## Security Best Practices

### Client-Side Security

1. **Store tokens securely**
   - Use `httpOnly` cookies (recommended)
   - Or encrypted localStorage/sessionStorage
   - Never store in plain text

2. **Implement token refresh**
   ```typescript
   // Refresh token before expiry
   const TOKEN_LIFETIME = 3600; // 1 hour
   const REFRESH_THRESHOLD = 0.75; // Refresh at 75% lifetime

   setInterval(async () => {
     const tokenAge = Date.now() - tokenIssuedAt;
     if (tokenAge > TOKEN_LIFETIME * REFRESH_THRESHOLD * 1000) {
       await refreshAccessToken();
     }
   }, 60000); // Check every minute
   ```

3. **Handle token expiry gracefully**
   ```typescript
   axios.interceptors.response.use(
     response => response,
     async error => {
       if (error.response?.status === 401) {
         // Try to refresh token
         const refreshed = await refreshAccessToken();
         if (refreshed) {
           // Retry original request
           return axios(error.config);
         } else {
           // Redirect to login
           window.location.href = '/login';
         }
       }
       return Promise.reject(error);
     }
   );
   ```

4. **Use HTTPS in production**
   - All authentication requests must use HTTPS
   - Prevents token interception (man-in-the-middle attacks)

### Backend Security

1. **Password hashing**: bcrypt with salt rounds = 12
2. **JWT secret rotation**: Rotate JWT_SECRET_KEY quarterly
3. **Token blacklist**: Maintain revoked token list in Redis
4. **Rate limiting**: Protect login/register endpoints
5. **Audit logging**: Log all authentication events

### Security Checklist

- [ ] Passwords meet strength requirements
- [ ] JWT tokens expire after 1 hour
- [ ] Refresh tokens rotate on each use
- [ ] HTTPS enabled in production
- [ ] Rate limiting configured (5 failed logins = 15 min block)
- [ ] Token storage is secure (httpOnly cookies)
- [ ] CORS properly configured
- [ ] Authorization checks prevent IDOR
- [ ] Audit logs enabled for auth events
- [ ] Secrets stored in environment variables (not hardcoded)

## Error Handling

### Common Error Codes

| Status Code | Error Type | Description | Solution |
|-------------|------------|-------------|----------|
| 400 | Bad Request | Invalid input data | Check request body schema |
| 401 | Unauthorized | Invalid/expired token | Re-authenticate or refresh token |
| 403 | Forbidden | Insufficient permissions | Check user role |
| 422 | Validation Error | Pydantic validation failed | Fix data format/types |
| 429 | Too Many Requests | Rate limit exceeded | Wait before retrying |
| 500 | Internal Server Error | Server error | Contact support |

### Error Response Format

```json
{
  "detail": "Error message in Turkish",
  "error_code": "AUTH_001",
  "timestamp": "2025-11-17T14:30:00Z"
}
```

### Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "sifre"],
      "msg": "ensure this value has at least 8 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

## Code Examples

### TypeScript/React Example

```typescript
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1/auth';

// Register
async function register(email: string, password: string, name: string) {
  try {
    const response = await axios.post(`${API_URL}/kayit`, {
      email,
      ad_soyad: name,
      sifre: password,
      rol: 'ogrenci'
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
    throw error;
  }
}

// Login
async function login(email: string, password: string) {
  try {
    const response = await axios.post(`${API_URL}/giris`, {
      email,
      sifre: password
    });

    const { access_token, refresh_token } = response.data;

    // Store tokens securely
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('token_issued_at', Date.now().toString());

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
    throw error;
  }
}

// Get profile
async function getProfile() {
  const token = localStorage.getItem('access_token');

  try {
    const response = await axios.get(`${API_URL}/profil`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      // Token expired, try refresh
      const refreshed = await refreshToken();
      if (refreshed) {
        return getProfile(); // Retry
      }
      throw new Error('Session expired, please login again');
    }
    throw error;
  }
}

// Refresh access token
async function refreshToken() {
  const refresh_token = localStorage.getItem('refresh_token');

  try {
    const response = await axios.post(`${API_URL}/refresh`, null, {
      headers: {
        Authorization: `Bearer ${refresh_token}`
      }
    });

    const { access_token, refresh_token: new_refresh_token } = response.data;

    // Update stored tokens
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', new_refresh_token);
    localStorage.setItem('token_issued_at', Date.now().toString());

    return true;
  } catch (error) {
    // Refresh failed, clear tokens and redirect to login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_issued_at');
    return false;
  }
}

// Logout
async function logout() {
  const token = localStorage.getItem('access_token');

  try {
    await axios.post(`${API_URL}/cikis`, null, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
  } finally {
    // Clear local tokens regardless of API response
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_issued_at');
  }
}

// Axios interceptor for automatic token refresh
axios.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshed = await refreshToken();
      if (refreshed) {
        const token = localStorage.getItem('access_token');
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return axios(originalRequest);
      } else {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);
```

### Python Example

```python
import requests
from typing import Optional

API_URL = "http://localhost:8000/api/v1/auth"

class AuthClient:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def register(self, email: str, password: str, name: str) -> dict:
        """Register new user"""
        response = requests.post(
            f"{API_URL}/kayit",
            json={
                "email": email,
                "ad_soyad": name,
                "sifre": password,
                "rol": "ogrenci"
            }
        )
        response.raise_for_status()
        return response.json()

    def login(self, email: str, password: str) -> dict:
        """Login and store tokens"""
        response = requests.post(
            f"{API_URL}/giris",
            json={
                "email": email,
                "sifre": password
            }
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

        return data

    def get_profile(self) -> dict:
        """Get user profile"""
        if not self.access_token:
            raise ValueError("Not authenticated")

        response = requests.get(
            f"{API_URL}/profil",
            headers={"Authorization": f"Bearer {self.access_token}"}
        )

        if response.status_code == 401:
            # Try to refresh token
            if self.refresh_access_token():
                return self.get_profile()  # Retry
            raise ValueError("Session expired")

        response.raise_for_status()
        return response.json()

    def refresh_access_token(self) -> bool:
        """Refresh access token"""
        if not self.refresh_token:
            return False

        try:
            response = requests.post(
                f"{API_URL}/refresh",
                headers={"Authorization": f"Bearer {self.refresh_token}"}
            )
            response.raise_for_status()

            data = response.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]

            return True
        except requests.RequestException:
            self.access_token = None
            self.refresh_token = None
            return False

    def logout(self):
        """Logout and clear tokens"""
        if self.access_token:
            try:
                requests.post(
                    f"{API_URL}/cikis",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
            finally:
                self.access_token = None
                self.refresh_token = None

# Usage
client = AuthClient()

# Register
user = client.register(
    email="ahmet@example.com",
    password="GucluSifre123!",
    name="Ahmet Yılmaz"
)

# Login
tokens = client.login(
    email="ahmet@example.com",
    password="GucluSifre123!"
)

# Get profile
profile = client.get_profile()
print(f"Logged in as: {profile['ad_soyad']}")

# Logout
client.logout()
```

## Related Documentation

- [Error Codes Reference](./error-codes.md)
- [API Reference (OpenAPI)](http://localhost:8000/docs)
- [User Roles and Permissions](./user-roles.md)
- [Security Best Practices](./security.md)

## Support

For authentication issues:
- Check [Error Codes Reference](./error-codes.md)
- Review [Troubleshooting Guide](./troubleshooting.md)
- Contact: support@kiro2.com
- GitHub Issues: https://github.com/kiro2/platform/issues

---

**Last Updated**: 2025-11-17
**Version**: 1.0.0
**Author**: KIRO2 Platform Team
