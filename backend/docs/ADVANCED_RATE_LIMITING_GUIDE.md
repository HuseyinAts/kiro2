# Advanced Rate Limiting Guide

**Document Version**: 1.0
**Sprint**: Phase 2 Sprint 6
**Last Updated**: 2025-11-12
**Status**: ✅ Implemented

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Implementation](#implementation)
5. [API Endpoints](#api-endpoints)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Monitoring](#monitoring)

---

## Overview

### What is Advanced Rate Limiting?

Advanced Rate Limiting is a **distributed, Redis-based rate limiting system** that protects the Kiro2 platform from abuse while providing fair access to all users based on their subscription tier.

### Key Benefits

✅ **Distributed**: Works across multiple server instances
✅ **Accurate**: Uses sliding window algorithm
✅ **Flexible**: Tier-based and endpoint-specific limits
✅ **Standards-Compliant**: RFC 6585 compliant headers
✅ **User-Friendly**: Clear error messages and retry information

### Use Cases

- Prevent API abuse and DDoS attacks
- Ensure fair resource allocation
- Protect expensive operations (AI, exports)
- Monetization through tier-based limits

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         RateLimitMiddleware (Intercepts all)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         AdvancedRateLimiter (Business Logic)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                   │
│                           ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Redis (Sorted Sets Storage)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Sliding Window Algorithm

```
Time Window (60 seconds):
├──────────────────────────────────────────────────────────────┤
│ Request Timestamps (Redis Sorted Set):                       │
│ ┌─────┬─────┬─────┬─────┬─────────────────────────────┐   │
│ │ T1  │ T2  │ T3  │ T4  │ T5 (Current)                │   │
│ └─────┴─────┴─────┴─────┴─────────────────────────────┘   │
│                                                               │
│ Algorithm:                                                    │
│ 1. Remove entries older than (now - window)                  │
│ 2. Count remaining entries                                   │
│ 3. If count >= limit: REJECT                                 │
│ 4. Else: ADD current timestamp and ACCEPT                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Tier-based Rate Limits

Three user tiers with different limits:

| Tier    | Default | Auth | Export | AI   |
|---------|---------|------|--------|------|
| FREE    | 60/min  | 10   | 2      | 20   |
| PREMIUM | 300/min | 30   | 10     | 100  |
| ADMIN   | 10k/min | 1000 | 1000   | 1000 |

**Implementation**:
```python
class UserTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ADMIN = "admin"
```

### 2. Endpoint-specific Limits

Critical endpoints have custom limits:

```python
endpoint_limits = {
    "/api/v1/auth/login": {"limit": 5, "window": 60},      # 5 per minute
    "/api/v1/auth/register": {"limit": 3, "window": 60},   # 3 per minute
    "/api/v1/kvkk/privacy/export": {"limit": 2, "window": 3600}, # 2 per hour
    "/api/v1/ai/chat": {"limit": 20, "window": 60},        # 20 per minute
}
```

### 3. RFC 6585 Compliant Headers

Every response includes rate limit information:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699876543
X-RateLimit-Window: 60
```

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699876543
Retry-After: 15
```

### 4. User/IP-based Identification

```
Priority:
1. User ID (if authenticated)
2. IP address (if not authenticated)
```

This prevents abuse from unauthenticated users while tracking authenticated users accurately.

### 5. Automatic Tier Detection

```python
def _get_user_tier(request: Request) -> UserTier:
    user = request.state.user

    if user.role in ["admin", "superadmin"]:
        return UserTier.ADMIN
    elif user.is_premium:
        return UserTier.PREMIUM
    else:
        return UserTier.FREE
```

---

## Implementation

### Core Components

#### 1. `AdvancedRateLimiter` (core/advanced_rate_limiter.py)

**Purpose**: Core rate limiting business logic

**Key Methods**:
```python
async def check_rate_limit(
    identifier: str,
    endpoint: str,
    tier: UserTier = UserTier.FREE,
    window: int = 60
) -> Tuple[bool, Dict[str, int]]:
    """
    Check if request is within rate limit

    Returns:
        (allowed: bool, info: dict)
    """
```

**Redis Key Format**:
```
ratelimit:{tier}:{endpoint}:{identifier}

Examples:
ratelimit:free:/api/v1/ai/chat:192.168.1.100
ratelimit:premium:/api/v1/auth/login:user-uuid-1234
ratelimit:admin:/api/v1/kvkk/privacy/export:admin-uuid-5678
```

#### 2. `RateLimitMiddleware` (core/rate_limit_middleware.py)

**Purpose**: FastAPI middleware to apply rate limiting

**Flow**:
```python
1. Check if path should be rate limited (exclude /health, /docs)
2. Get user tier from request.state.user
3. Get identifier (user ID or IP)
4. Call rate limiter
5. If exceeded: Return 429
6. Else: Add headers and continue
```

**Excluded Paths**:
```python
excluded_paths = [
    "/health",
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics"
]
```

#### 3. `RateLimitAPI` (api/rate_limit_api.py)

**Purpose**: Management endpoints for rate limiting

**Endpoints**:
- `GET /api/v1/rate-limit/status` - Current status
- `GET /api/v1/rate-limit/config` - User's limits
- `GET /api/v1/rate-limit/my-tier` - Tier information
- `POST /api/v1/rate-limit/reset` - Reset limit (Admin)
- `GET /api/v1/rate-limit/admin/statistics` - Statistics (Admin)

---

## API Endpoints

### User Endpoints

#### 1. Get Current Rate Limit Status

```http
GET /api/v1/rate-limit/status
Authorization: Bearer {token}
```

**Response**:
```json
{
  "tier": "free",
  "limit": 60,
  "remaining": 45,
  "reset": 1699876543,
  "reset_datetime": "2025-11-12T10:15:43",
  "window": 60
}
```

#### 2. Get Rate Limit Configuration

```http
GET /api/v1/rate-limit/config
Authorization: Bearer {token}
```

**Response**:
```json
{
  "tier": "free",
  "limits": {
    "tier_limits": {
      "default": 60,
      "auth": 10,
      "export": 2,
      "ai": 20
    },
    "endpoint_limits": {
      "/api/v1/auth/login": {"limit": 5, "window": 60},
      "/api/v1/auth/register": {"limit": 3, "window": 60}
    },
    "description": {
      "default": "General API endpoints",
      "auth": "Authentication endpoints (login, register, etc.)",
      "export": "Data export and deletion endpoints",
      "ai": "AI-powered features (chat, recommendations, etc.)"
    }
  }
}
```

#### 3. Get My Tier

```http
GET /api/v1/rate-limit/my-tier
Authorization: Bearer {token}
```

**Response**:
```json
{
  "current_tier": "free",
  "tier_info": {
    "name": "Ücretsiz",
    "description": "Temel özellikler",
    "requests_per_minute": 60,
    "can_upgrade": true
  },
  "upgrade_available": true
}
```

### Admin Endpoints

#### 4. Reset User Rate Limit

```http
POST /api/v1/rate-limit/reset
Authorization: Bearer {admin-token}
Content-Type: application/json

{
  "user_id": "user-uuid-1234",
  "endpoint": "/api/v1/ai/chat"  // Optional
}
```

**Response**:
```json
{
  "success": true,
  "message": "Rate limit reset for user user-uuid-1234 on endpoint /api/v1/ai/chat",
  "user_id": "user-uuid-1234",
  "endpoint": "/api/v1/ai/chat"
}
```

#### 5. Get Rate Limit Statistics

```http
GET /api/v1/rate-limit/admin/statistics
Authorization: Bearer {admin-token}
```

**Response**:
```json
{
  "period": "last_24_hours",
  "total_requests": 125000,
  "rate_limited_requests": 350,
  "rate_limit_percentage": 0.28,
  "top_endpoints": [
    {
      "endpoint": "/api/v1/auth/login",
      "violations": 120,
      "limit": 5
    }
  ],
  "tier_distribution": {
    "free": 245000,
    "premium": 78000,
    "admin": 2000
  }
}
```

---

## Configuration

### Environment Variables

```bash
# Redis connection for rate limiting
REDIS_URL=redis://localhost:6379/0
```

### Customizing Limits

Edit `core/advanced_rate_limiter.py`:

```python
self.tier_limits = {
    UserTier.FREE: {
        "default": 60,  # Change this
        "auth": 10,
        "export": 2,
        "ai": 20,
    },
    # ...
}

self.endpoint_limits = {
    "/api/v1/auth/login": {"limit": 5, "window": 60},  # Change this
    # Add more endpoints
}
```

### User Model

Ensure User model has premium fields:

```python
class User(Base):
    # ...
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
```

---

## Testing

### Manual Testing

#### 1. Test Rate Limit Enforcement

```bash
# Make 61 requests to exceed FREE tier limit (60/min)
for i in {1..61}; do
  curl -H "Authorization: Bearer {token}" \
       http://localhost:8000/api/v1/some-endpoint
done

# 61st request should return 429
```

#### 2. Test Rate Limit Headers

```bash
curl -v -H "Authorization: Bearer {token}" \
     http://localhost:8000/api/v1/some-endpoint

# Check response headers:
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 59
# X-RateLimit-Reset: {timestamp}
```

#### 3. Test Endpoint-specific Limits

```bash
# Login endpoint: 5 per minute
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
       -H "Content-Type: application/json" \
       -d '{"email":"test@test.com","password":"test123"}'
done

# 6th request should return 429
```

#### 4. Test Tier Differences

```bash
# FREE user: 60/min
curl -H "Authorization: Bearer {free-token}" \
     http://localhost:8000/api/v1/rate-limit/config

# PREMIUM user: 300/min
curl -H "Authorization: Bearer {premium-token}" \
     http://localhost:8000/api/v1/rate-limit/config
```

### Automated Testing

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_rate_limit_enforcement(client: AsyncClient, auth_token: str):
    """Test that rate limit is enforced after threshold"""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Make 60 requests (FREE tier limit)
    for _ in range(60):
        response = await client.get("/api/v1/some-endpoint", headers=headers)
        assert response.status_code == 200

    # 61st request should be rate limited
    response = await client.get("/api/v1/some-endpoint", headers=headers)
    assert response.status_code == 429
    assert "X-RateLimit-Limit" in response.headers
    assert "Retry-After" in response.headers
```

---

## Monitoring

### Key Metrics to Track

1. **Rate Limit Violations**
   - Count of 429 responses
   - Top violating IPs/users
   - Top violating endpoints

2. **Tier Distribution**
   - Requests per tier
   - Premium adoption rate

3. **Redis Performance**
   - Connection pool usage
   - Command latency
   - Memory usage

4. **Business Metrics**
   - Conversion to premium (due to rate limits)
   - Feature usage by tier

### Logging

All rate limit events are logged:

```python
# Rate limit exceeded
logger.warning(
    "rate_limit_exceeded",
    identifier=identifier,
    endpoint=endpoint,
    tier=tier.value,
    count=current_count,
    limit=limit
)
```

### Alerting

Set up alerts for:
- High rate limit violation rate (>5%)
- Specific user/IP with many violations
- Redis connection failures

---

## Error Handling

### 429 Too Many Requests Response

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 15 seconds.",
  "limit": 60,
  "window": 60,
  "retry_after": 15
}
```

### Graceful Degradation

If Redis is unavailable:
- Middleware catches exception
- Logs error
- **Allows request to proceed** (fail-open strategy)
- Alert sent to admin

```python
except Exception as e:
    logger.error("rate_limit_middleware_error", error=str(e))
    # Continue without rate limiting on error
    return await call_next(request)
```

---

## Best Practices

### For Developers

1. **Test thoroughly** - Ensure rate limiting doesn't block legitimate users
2. **Monitor Redis** - Keep an eye on memory and performance
3. **Adjust limits** - Based on actual usage patterns
4. **Document custom limits** - When adding endpoint-specific limits

### For API Clients

1. **Check headers** - Always read `X-RateLimit-*` headers
2. **Implement backoff** - Use `Retry-After` header
3. **Cache responses** - Reduce unnecessary requests
4. **Upgrade tier** - If consistently hitting limits

### For Operations

1. **Scale Redis** - Use Redis Cluster for high traffic
2. **Monitor violations** - Track unusual patterns
3. **Adjust limits** - During special events
4. **Review regularly** - Ensure limits match business needs

---

## Integration with Other Systems

### KVKK Compliance

Rate limiting protects KVKK endpoints:

```python
"/api/v1/kvkk/privacy/export": {"limit": 2, "window": 3600}  # 2 per hour
```

This prevents abuse of data export functionality.

### 2FA Authentication

Login attempts are strictly limited:

```python
"/api/v1/auth/login": {"limit": 5, "window": 60}  # 5 per minute
```

This prevents brute-force attacks on user accounts.

### AI Features

AI endpoints have generous limits for premium users:

```python
tier_limits = {
    UserTier.FREE: {"ai": 20},     # 20 AI requests/min
    UserTier.PREMIUM: {"ai": 100}  # 100 AI requests/min
}
```

---

## Troubleshooting

### Issue: User getting 429 unexpectedly

**Cause**: User sharing IP with many others (NAT/proxy)

**Solution**:
1. Check if user is authenticated (should use user ID not IP)
2. Whitelist IP if legitimate
3. Suggest user to upgrade to premium

### Issue: Redis connection errors

**Cause**: Redis is down or unreachable

**Solution**:
1. Check Redis status: `redis-cli ping`
2. Verify `REDIS_URL` in environment
3. Restart Redis if needed
4. System fails open - requests allowed during outage

### Issue: Rate limit too strict

**Cause**: Limits don't match actual usage

**Solution**:
1. Review metrics and adjust limits
2. Consider endpoint-specific limits
3. Implement burst allowance for specific users

---

## Roadmap

### Phase 2 ✅ (Current - Sprint 6)
- [x] Redis-based distributed rate limiting
- [x] Tier-based limits (FREE/PREMIUM/ADMIN)
- [x] Endpoint-specific limits
- [x] RFC 6585 headers
- [x] Sliding window algorithm
- [x] Management API

### Phase 3 🔄 (Future Enhancements)
- [ ] Burst allowance (allow short bursts above limit)
- [ ] Dynamic limits based on server load
- [ ] Geographic rate limiting
- [ ] Custom limits per user (not just tier)
- [ ] Rate limit analytics dashboard
- [ ] Webhook notifications for violations

---

## References

### Standards
- **RFC 6585**: Additional HTTP Status Codes (429 Too Many Requests)
- **RFC 6750**: OAuth 2.0 Bearer Token Usage
- **Redis Commands**: [ZADD](https://redis.io/commands/zadd/), [ZREMRANGEBYSCORE](https://redis.io/commands/zremrangebyscore/), [ZCARD](https://redis.io/commands/zcard/)

### Libraries
- `redis.asyncio`: Async Redis client for Python
- `FastAPI`: Web framework with middleware support
- `Starlette`: ASGI framework (middleware base)

### Internal Documents
- [ARCHITECTURE_REVIEW.md](./ARCHITECTURE_REVIEW.md) - Sprint 6 planning
- [API_MIGRATION_GUIDE.md](./API_MIGRATION_GUIDE.md) - API versioning
- [KVKK_COMPLIANCE_GUIDE.md](./KVKK_COMPLIANCE_GUIDE.md) - KVKK compliance

---

**Document Version**: 1.0
**Last Review**: 2025-11-12
**Next Review**: 2025-12-12
**Status**: ✅ Active
