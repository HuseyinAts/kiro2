# Security Hardening Documentation
**Task 23: Security Hardening Implementation**

## Overview

Bu doküman, Learning Path Video API için uygulanan güvenlik sertleştirme önlemlerini açıklar.

## Implemented Security Measures

### 1. Input Validation (Pydantic Validators)

**Location:** `backend/core/input_validation.py`

**Features:**
- Tüm kullanıcı girdileri için Pydantic validator'ları
- Whitelist-based validation (sadece izin verilen değerler)
- String length limits
- Type validation
- Custom validation rules

**Validated Fields:**
- `subject`: Konu adı (alfanumerik + Türkçe karakterler, max 100 char)
- `difficulty`: Zorluk seviyesi (whitelist: başlangıç, kolay, orta, zor, ileri)
- `exam_type`: Sınav tipi (whitelist: TYT, AYT, LGS, KPSS, DGS, ALES)
- `learning_style`: Öğrenme stili (whitelist: visual, auditory, kinesthetic, reading)
- `goals`: Hedefler listesi (1-10 items, max 200 char each)
- `currentLevel`: Seviye dictionary (0-100 arası integer değerler)

**Example Usage:**
```python
from core.input_validation import ValidatedStudentProfileRequest

@router.post("/recommendations")
async def get_recommendations(
    request: ValidatedStudentProfileRequest  # Otomatik validation
):
    # Request otomatik olarak validate edildi
    pass
```

### 2. Input Sanitization

**Location:** `backend/core/input_validation.py`

**Features:**
- HTML escape (XSS prevention)
- Null byte removal
- Control character removal
- Whitespace trimming
- Max length enforcement

**Sanitization Process:**
```python
from core.input_validation import SecurityValidator

# String sanitization
clean_text = SecurityValidator.sanitize_string(user_input, max_length=200)

# List sanitization
clean_goals = SecurityValidator.validate_goals(goals_list)

# Dictionary sanitization
clean_level = SecurityValidator.validate_current_level(level_dict)
```

### 3. SQL Injection Prevention

**Location:** `backend/core/sql_injection_prevention.py`

**Features:**
- Parameterized queries (prepared statements)
- SQL pattern detection
- Identifier validation (table/column names)
- Safe query builder
- Query parameter validation

**SQL Injection Patterns Detected:**
- SQL keywords (SELECT, INSERT, UPDATE, DELETE, DROP, etc.)
- Comment markers (--, /*, */)
- Union-based injection (UNION SELECT)
- Boolean-based injection (OR 1=1, '=')
- System table access (INFORMATION_SCHEMA, SYSOBJECTS)

**Safe Query Building:**
```python
from core.sql_injection_prevention import SafeQueryBuilder

# Safe query with parameterization
builder = SafeQueryBuilder("video_cache")
builder.where(subject="matematik", difficulty="orta")
builder.order_by("quality_score")
builder.limit(20)

results = await builder.execute(session)
```

**Why Parameterized Queries?**
- User input never directly concatenated into SQL
- Database driver handles escaping
- Prevents all SQL injection attacks
- Performance benefit (query plan caching)

### 4. XSS Prevention

**Location:** `backend/core/xss_prevention.py`

**Features:**
- HTML escaping
- Dangerous tag removal (script, iframe, object, etc.)
- Event handler removal (onclick, onload, etc.)
- Dangerous protocol removal (javascript:, data:, etc.)
- Secure JSON response
- Security headers

**XSS Patterns Detected:**
- Script tags: `<script>`, `</script>`
- Event handlers: `onclick=`, `onload=`, `onerror=`
- Dangerous tags: `<iframe>`, `<object>`, `<embed>`
- Dangerous protocols: `javascript:`, `data:`, `vbscript:`

**Output Encoding:**
```python
from core.xss_prevention import XSSPrevention, SecureJSONResponse

# Text sanitization
clean_text = XSSPrevention.sanitize_text(user_input, allow_html=False)

# Dictionary sanitization
clean_data = XSSPrevention.sanitize_dict(response_data)

# Secure JSON response (automatic sanitization)
return SecureJSONResponse(content=data)
```

**Security Headers Added:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'; ...`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), microphone=(), ...`

### 5. CORS Policy Update

**Location:** `backend/core/cors_security.py`

**Features:**
- Environment-based origin whitelist
- Strict origin validation
- Credential handling
- Preflight request support
- Configurable headers and methods

**Allowed Origins:**

**Production:**
- `https://kiro2.app`
- `https://www.kiro2.app`
- `https://api.kiro2.app`
- `https://teknofest-egitim.com`
- `https://www.teknofest-egitim.com`

**Development:**
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`
- `http://127.0.0.1:5173`

**Allowed Methods:**
- GET, POST, PUT, DELETE, PATCH, OPTIONS

**Allowed Headers:**
- Authorization
- Content-Type
- Accept
- X-Request-ID
- X-API-Key
- X-CSRF-Token

**CORS Configuration:**
```python
from core.cors_security import setup_cors

app = FastAPI()
setup_cors(app)  # Automatic environment-based configuration
```

### 6. Comprehensive Security Middleware

**Location:** `backend/middleware/comprehensive_security_middleware.py`

**Features:**
- User agent validation (blocks security scanners)
- Request size limits (10MB default)
- CORS validation
- Suspicious path detection
- SQL injection detection in query params
- Security headers injection
- Request/response logging

**Blocked User Agents:**
- sqlmap
- nikto
- nmap
- masscan
- nessus
- openvas
- metasploit

**Suspicious Paths Detected:**
- Path traversal: `../`, `..\\`
- System files: `/etc/`, `/proc/`
- Common attack targets: `wp-admin`, `phpmyadmin`
- Sensitive files: `.env`, `.git`

**Middleware Stack:**
```python
from middleware.comprehensive_security_middleware import (
    ComprehensiveSecurityMiddleware,
    InputValidationMiddleware,
    SQLInjectionDetectionMiddleware
)

app.add_middleware(ComprehensiveSecurityMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(SQLInjectionDetectionMiddleware)
```

## Security Best Practices

### 1. Input Validation
✅ **DO:**
- Always use Pydantic models with validators
- Whitelist allowed values
- Set max length limits
- Validate data types

❌ **DON'T:**
- Trust user input
- Use blacklist-based validation
- Skip validation for "internal" endpoints

### 2. SQL Queries
✅ **DO:**
- Always use parameterized queries
- Use SafeQueryBuilder for dynamic queries
- Validate table/column names

❌ **DON'T:**
- Concatenate user input into SQL
- Use string formatting for queries
- Trust "sanitized" input in SQL

### 3. Output Encoding
✅ **DO:**
- Use SecureJSONResponse for API responses
- Escape HTML in user-generated content
- Add security headers to all responses

❌ **DON'T:**
- Return raw user input
- Trust "sanitized" input in output
- Skip encoding for "safe" data

### 4. CORS Configuration
✅ **DO:**
- Use whitelist-based origin validation
- Separate production and development origins
- Validate origin on every request

❌ **DON'T:**
- Use wildcard (*) in production
- Allow all origins
- Skip origin validation

## Testing Security Measures

### 1. Input Validation Tests
```python
# Test invalid subject
response = client.post("/api/youtube/search", json={
    "subject": "<script>alert('XSS')</script>",
    "difficulty": "orta",
    "exam_type": "TYT"
})
assert response.status_code == 400

# Test SQL injection
response = client.post("/api/youtube/search", json={
    "subject": "matematik' OR '1'='1",
    "difficulty": "orta",
    "exam_type": "TYT"
})
assert response.status_code == 400
```

### 2. SQL Injection Tests
```python
# Test SQL injection in query params
response = client.get("/api/youtube/search?subject=matematik' OR '1'='1")
assert response.status_code == 400

# Test SQL injection in path
response = client.get("/api/youtube/search/'; DROP TABLE users; --")
assert response.status_code == 404
```

### 3. XSS Tests
```python
# Test XSS in response
response = client.post("/api/youtube/recommendations", json={
    "goals": ["<script>alert('XSS')</script>"],
    "currentLevel": {"matematik": 50},
    "learningStyle": "visual"
})
assert response.status_code == 200
assert "<script>" not in response.text
```

### 4. CORS Tests
```python
# Test invalid origin
response = client.get(
    "/api/youtube/health",
    headers={"Origin": "https://evil.com"}
)
assert response.status_code == 403

# Test valid origin
response = client.get(
    "/api/youtube/health",
    headers={"Origin": "http://localhost:3001"}
)
assert response.status_code == 200
```

## Security Monitoring

### Metrics to Monitor
- Failed validation attempts
- SQL injection attempts
- XSS attempts
- CORS violations
- Blocked user agents
- Suspicious paths accessed

### Logging
All security events are logged with structured logging:
```json
{
  "timestamp": "2025-11-02T10:30:00Z",
  "level": "WARNING",
  "event": "sql_injection_attempt",
  "ip": "192.168.1.100",
  "path": "/api/youtube/search",
  "details": {
    "parameter": "subject",
    "value": "matematik' OR '1'='1"
  }
}
```

### Alerting
Configure alerts for:
- High rate of validation failures (>10/min)
- SQL injection attempts (any)
- XSS attempts (any)
- CORS violations (>5/min)
- Blocked user agents (any)

## Compliance

### OWASP Top 10 Coverage

✅ **A01:2021 – Broken Access Control**
- CORS validation
- Origin whitelisting

✅ **A03:2021 – Injection**
- SQL injection prevention
- Parameterized queries
- Input validation

✅ **A04:2021 – Insecure Design**
- Security-first architecture
- Defense in depth

✅ **A05:2021 – Security Misconfiguration**
- Secure defaults
- Security headers
- Environment-based configuration

✅ **A07:2021 – Identification and Authentication Failures**
- Rate limiting
- User agent validation

✅ **A08:2021 – Software and Data Integrity Failures**
- Input validation
- Output encoding

## Maintenance

### Regular Security Tasks
1. **Weekly:**
   - Review security logs
   - Check for new attack patterns
   - Update blocked user agents list

2. **Monthly:**
   - Review and update validation rules
   - Test security measures
   - Update dependencies

3. **Quarterly:**
   - Security audit
   - Penetration testing
   - Update security documentation

### Security Updates
- Keep dependencies updated
- Monitor security advisories
- Apply patches promptly

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/core/security.html)

## Contact

For security issues, please contact: security@teknofest-egitim.com
