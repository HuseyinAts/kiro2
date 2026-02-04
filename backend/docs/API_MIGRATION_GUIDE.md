# API Migration Guide: v1 → v2

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Target Audience**: API Clients, Frontend Developers, Third-party Integrators

---

## Table of Contents

1. [Overview](#overview)
2. [Version Negotiation](#version-negotiation)
3. [Deprecation Timeline](#deprecation-timeline)
4. [Breaking Changes](#breaking-changes)
5. [Migration Examples](#migration-examples)
6. [Testing Your Migration](#testing-your-migration)
7. [Support](#support)

---

## Overview

Kiro2 Egitim API is transitioning from **v1** to **v2** to provide:

✅ **Enhanced Security** - 2FA support, improved authentication
✅ **Better Performance** - Optimized queries, async processing
✅ **Improved Validation** - Stricter input validation
✅ **Consistent Response Format** - Standardized error responses
✅ **New Features** - Advanced analytics, real-time features

### Migration Timeline

| Date | Milestone |
|------|-----------|
| **2025-11-11** | v2 API released (stable) |
| **2026-05-11** | v1 deprecated (6 months) |
| **2026-11-11** | v1 sunset (12 months) |

---

## Version Negotiation

### Method 1: URL Path (Recommended)

**v1 Endpoint**:
```bash
GET https://api.kiro2.com/api/v1/users
```

**v2 Endpoint**:
```bash
GET https://api.kiro2.com/api/v2/users
```

### Method 2: Accept Header

```bash
curl -H "Accept: application/vnd.kiro2.v2+json" \
  https://api.kiro2.com/api/users
```

### Method 3: Query Parameter

```bash
GET https://api.kiro2.com/api/users?version=v2
```

**Priority Order**: Path > Header > Query > Default (v1)

---

## Deprecation Timeline

### Phase 1: v2 Release (2025-11-11)

- ✅ v2 API available and stable
- ✅ v1 continues to work (no changes)
- ✅ All documentation updated

### Phase 2: v1 Deprecated (2026-05-11)

**Deprecation Headers Added**:
```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Wed, 11 Nov 2026 00:00:00 GMT
X-API-Warn: Deprecated: Use v2 for enhanced security
Link: <https://api.kiro2.com/api/v2/users>; rel="deprecation"
```

**Actions**:
- Monitor deprecation warnings in logs
- Plan migration to v2
- Test thoroughly

### Phase 3: v1 Sunset (2026-11-11)

**v1 Endpoints Return 410 Gone**:
```json
{
  "error": "api_version_sunset",
  "message": "API version 'v1' has been sunset and is no longer available",
  "sunset_date": "2026-11-11T00:00:00Z",
  "successor": "v2"
}
```

**Actions**:
- ⚠️ All clients MUST migrate to v2
- v1 endpoints no longer functional

---

## Breaking Changes

### 1. Authentication

#### v1: Simple JWT
```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "token": "eyJhbGc...",
  "user": { ... }
}
```

#### v2: 2FA Support
```bash
POST /api/v2/auth/login
{
  "email": "user@example.com",
  "password": "password123",
  "totp_token": "123456"  # Required if 2FA enabled
}

Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": { ... },
  "requires_2fa": false
}
```

**Migration Steps**:
1. Check `requires_2fa` in initial response
2. If true, prompt for TOTP token
3. Retry with `totp_token` field
4. Handle 2FA setup flow if needed

---

### 2. Error Response Format

#### v1: Inconsistent Format
```json
{
  "error": "User not found"
}
```

#### v2: Standardized Format
```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found",
    "details": {
      "user_id": "123"
    },
    "timestamp": "2025-11-11T10:00:00Z"
  }
}
```

**Migration Steps**:
1. Update error parsing logic
2. Handle structured error codes
3. Use error.code for programmatic handling

---

### 3. Pagination

#### v1: Simple Offset
```bash
GET /api/v1/questions?page=1&per_page=20

Response:
{
  "questions": [...],
  "total": 100,
  "page": 1,
  "per_page": 20
}
```

#### v2: Cursor-based
```bash
GET /api/v2/questions?limit=20&cursor=eyJpZCI6MTIzfQ==

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ==",
    "has_more": true,
    "total": 100
  }
}
```

**Benefits**:
- Consistent results (no skipped items)
- Better performance for large datasets
- Real-time data support

**Migration Steps**:
1. Replace `page` parameter with `cursor`
2. Use `next_cursor` for pagination
3. Check `has_more` instead of calculating pages

---

### 4. User Profile Response

#### v1: Flat Structure
```json
{
  "id": "123",
  "email": "user@example.com",
  "first_name": "Ali",
  "last_name": "Yılmaz",
  "grade": 12,
  "school": "Ankara Fen Lisesi"
}
```

#### v2: Nested Structure
```json
{
  "id": "123",
  "email": "user@example.com",
  "profile": {
    "first_name": "Ali",
    "last_name": "Yılmaz",
    "full_name": "Ali Yılmaz"
  },
  "student_info": {
    "grade": 12,
    "school": "Ankara Fen Lisesi",
    "target_exam": "TYT",
    "target_score": 450
  },
  "preferences": {
    "learning_style": "visual",
    "notifications_enabled": true
  }
}
```

**Migration Steps**:
1. Update response parsing to handle nested objects
2. Access `profile.first_name` instead of `first_name`
3. Use new `full_name` field if available

---

## Migration Examples

### Example 1: Update Auth Client

**Before (v1)**:
```javascript
async function login(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();
  localStorage.setItem('token', data.token);
  return data.user;
}
```

**After (v2)**:
```javascript
async function login(email, password, totpToken = null) {
  const response = await fetch('/api/v2/auth/login', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      totp_token: totpToken
    })
  });

  const data = await response.json();

  // Check if 2FA required
  if (data.requires_2fa && !totpToken) {
    throw new Error2FARequired('2FA token required');
  }

  localStorage.setItem('token', data.access_token);
  return data.user;
}
```

---

### Example 2: Update Pagination Logic

**Before (v1)**:
```python
async def fetch_all_questions():
    all_questions = []
    page = 1
    per_page = 50

    while True:
        response = await client.get(
            f'/api/v1/questions?page={page}&per_page={per_page}'
        )
        data = response.json()

        all_questions.extend(data['questions'])

        if page * per_page >= data['total']:
            break

        page += 1

    return all_questions
```

**After (v2)**:
```python
async def fetch_all_questions():
    all_questions = []
    cursor = None

    while True:
        url = '/api/v2/questions?limit=50'
        if cursor:
            url += f'&cursor={cursor}'

        response = await client.get(url)
        data = response.json()

        all_questions.extend(data['data'])

        if not data['pagination']['has_more']:
            break

        cursor = data['pagination']['next_cursor']

    return all_questions
```

---

### Example 3: Update Error Handling

**Before (v1)**:
```typescript
try {
  const user = await api.getUser(userId);
} catch (error) {
  // Simple string error
  alert(error.message);
}
```

**After (v2)**:
```typescript
try {
  const user = await api.getUser(userId);
} catch (error) {
  // Structured error handling
  switch (error.code) {
    case 'USER_NOT_FOUND':
      showNotFoundMessage();
      break;
    case 'UNAUTHORIZED':
      redirectToLogin();
      break;
    case 'RATE_LIMIT_EXCEEDED':
      showRateLimitWarning(error.details.retry_after);
      break;
    default:
      showGenericError(error.message);
  }
}
```

---

## Testing Your Migration

### 1. Run in Parallel

Test v2 endpoints alongside v1 without removing v1 integration:

```javascript
// Dual-version testing
const v1Response = await fetch('/api/v1/endpoint');
const v2Response = await fetch('/api/v2/endpoint');

// Compare responses
assert.equal(v1Response.data.length, v2Response.data.length);
```

### 2. Use Feature Flags

```javascript
const USE_V2_API = process.env.FEATURE_FLAG_API_V2 === 'true';

const endpoint = USE_V2_API
  ? '/api/v2/users'
  : '/api/v1/users';
```

### 3. Monitor Metrics

Track during migration:
- Response times (v1 vs v2)
- Error rates
- Success rates
- Feature parity

### 4. Gradual Rollout

1. **Phase 1**: 10% of traffic → v2
2. **Phase 2**: 50% of traffic → v2
3. **Phase 3**: 100% of traffic → v2

---

## Migration Checklist

### Pre-Migration

- [ ] Read full migration guide
- [ ] Review breaking changes
- [ ] Identify affected endpoints
- [ ] Set up v2 test environment
- [ ] Create migration timeline

### During Migration

- [ ] Update authentication flow (2FA support)
- [ ] Update error handling (structured errors)
- [ ] Update pagination logic (cursor-based)
- [ ] Update response parsing (nested structure)
- [ ] Test all integrated endpoints
- [ ] Monitor deprecation warnings
- [ ] Run parallel v1/v2 tests

### Post-Migration

- [ ] Verify all endpoints use v2
- [ ] Remove v1 references from code
- [ ] Update API documentation
- [ ] Monitor error rates
- [ ] Train team on v2 features

---

## Common Pitfalls

### 1. Forgetting 2FA Token
❌ **Wrong**:
```javascript
fetch('/api/v2/auth/login', {
  body: JSON.stringify({ email, password })
})
```

✅ **Correct**:
```javascript
fetch('/api/v2/auth/login', {
  body: JSON.stringify({
    email,
    password,
    totp_token: has2FA ? token : null
  })
})
```

### 2. Hardcoding Version in Client
❌ **Wrong**:
```javascript
const API_BASE = 'https://api.kiro2.com/api/v1';
```

✅ **Correct**:
```javascript
const API_VERSION = process.env.API_VERSION || 'v2';
const API_BASE = `https://api.kiro2.com/api/${API_VERSION}`;
```

### 3. Ignoring Deprecation Headers
❌ **Wrong**:
```javascript
// Ignoring response headers
const data = await response.json();
```

✅ **Correct**:
```javascript
const data = await response.json();

// Check for deprecation
if (response.headers.get('Deprecation')) {
  console.warn('API deprecated:', response.headers.get('Sunset'));
}
```

---

## Support

### Documentation
- **API Reference**: https://docs.kiro2.com/api
- **Changelog**: https://docs.kiro2.com/changelog
- **Examples**: https://github.com/kiro2/examples

### Contact
- **Email**: api-support@kiro2.com
- **Slack**: #api-migration
- **Office Hours**: Monday-Friday 9:00-17:00 (Turkey Time)

### Migration Assistance
Need help migrating? Contact us for:
- Code review of your integration
- Migration timeline planning
- Testing support
- Emergency hotline during migration

---

## FAQ

### Q: Do I need to migrate immediately?
**A**: No. v1 will continue working until sunset date (2026-11-11). However, we recommend migrating within 6 months to benefit from v2 features.

### Q: Can I use both v1 and v2 simultaneously?
**A**: Yes! You can gradually migrate endpoints. Use path-based versioning to control which version each request uses.

### Q: Will v2 be backward compatible?
**A**: No, v2 has breaking changes. However, we provide this guide and support to make migration smooth.

### Q: What if I miss the sunset date?
**A**: v1 endpoints will return 410 Gone after sunset. Your application will break. Plan ahead!

### Q: Are there new features exclusive to v2?
**A**: Yes! 2FA, improved analytics, real-time features, and better performance are v2-exclusive.

### Q: How do I test v2 without affecting production?
**A**: Use query parameter versioning in development: `?version=v2`

---

**Last Updated**: 2025-11-11
**Version**: 1.0
**Status**: ✅ v2 Released | v1 Stable | Migration Window Open
