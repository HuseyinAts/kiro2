# Auth Integration Tests

## Overview

Comprehensive authentication and RBAC integration tests for KIRO2 platform.

## Test File Structure

```
backend/tests/integration/auth/
├── __init__.py
├── test_auth_full_flow.py  # 24 integration tests (F-01 series)
└── README.md               # This file
```

## Test Coverage (F-01 Series)

### F-01: Registration (4 tests)
- **F-01.01**: `test_register_returns_201_or_200` - Valid registration
- **F-01.02**: `test_register_duplicate_email_rejected` - Duplicate email (409/400)
- **F-01.03**: `test_register_weak_password_rejected` - Weak password (422)
- **F-01.04**: `test_register_missing_email_rejected` - Missing email (422)
- **F-01.24**: `test_register_email_format_validation` - Invalid email format (422)

### F-02: Login (6 tests)
- **F-01.05**: `test_login_success` - Valid credentials return token
- **F-01.06**: `test_login_wrong_password` - Wrong password (401)
- **F-01.07**: `test_login_nonexistent_user` - Non-existent user (401, no email leak)
- **F-01.08**: `test_login_returns_access_token` - Response has `access_token`
- **F-01.09**: `test_login_returns_refresh_token` - Response has `refresh_token`
- **F-01.14**: `test_token_type_is_bearer` - `token_type` is "bearer"
- **F-01.15**: `test_login_updates_last_login` - `last_login` field updated

### F-03: Profile / Token (4 tests)
- **F-01.10**: `test_profile_with_valid_token` - Valid Bearer token (200)
- **F-01.11**: `test_profile_without_token` - No token (401/403)
- **F-01.12**: `test_profile_with_expired_token` - Expired token (401)
- **F-01.13**: `test_profile_with_invalid_token` - Invalid token (401/403)

### F-04: Security (3 tests)
- **F-01.16**: `test_register_creates_student_by_default` - Default role is student
- **F-01.17**: `test_password_is_hashed` - Password hashing (bcrypt)
- **F-01.23**: `test_auth_response_no_password_leak` - No password in response

### F-05: RBAC (3 tests)
- **F-01.18**: `test_rbac_student_cannot_access_admin` - Student blocked from admin (403)
- **F-01.19**: `test_rbac_admin_can_access_admin` - Admin can access admin endpoints
- **F-01.20**: `test_idor_student_a_cannot_see_student_b` - IDOR protection (403)

### F-06: Rate Limiting & 2FA (2 tests)
- **F-01.21**: `test_rate_limit_login` - Rapid attempts return 429
- **F-01.22**: `test_2fa_setup_endpoint_exists` - 2FA endpoint exists

## Running Tests

### Run All Auth Tests
```bash
cd backend
pytest tests/integration/auth/test_auth_full_flow.py -v
```

### Run Specific Test
```bash
pytest tests/integration/auth/test_auth_full_flow.py::test_login_success -v
```

### Run with Coverage
```bash
pytest tests/integration/auth/test_auth_full_flow.py --cov=api.auth --cov-report=term-missing
```

### Parallel Execution
```bash
pytest tests/integration/auth/test_auth_full_flow.py -n auto
```

## Mocking Strategy

Tests use `unittest.mock` to mock:
- Database sessions (`mock_db_session`)
- User service methods (`kullanici_servisi`)
- Database queries (`get_db`)
- Token validation (`token_dogrula`)

## Key Assertions

### ✅ Meaningful Assertions (KIRO2 Standard)
```python
assert response.status_code == status.HTTP_200_OK
assert "access_token" in data
assert data["token_type"].lower() == "bearer"
assert mock_db_user.last_login is not None
```

### ❌ NEVER Use (Reward Hacking)
```python
assert True  # FORBIDDEN
assert 1 == 1  # FORBIDDEN
pass  # Empty test - FORBIDDEN
```

## Security Tests

### Password Security
- Bcrypt hashing verified
- Password not leaked in responses
- Weak password rejection (422)

### RBAC / Authorization
- Student cannot access admin endpoints (403)
- Admin can access admin endpoints
- IDOR protection (Student A cannot see Student B)

### Email Enumeration Prevention
- Login returns same error for non-existent user
- No "user not found" leak

## Integration Test Patterns

### HTTP Client Setup
```python
async with AsyncClient(
    transport=ASGITransport(app=app),
    base_url="http://test"
) as client:
    response = await client.post("/api/v1/auth/giris", json={...})
```

### Database Mocking
```python
with patch("api.auth.get_db") as mock_get_db:
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_get_db.return_value = mock_db
```

### Service Mocking
```python
with patch(
    "services.user_service.kullanici_servisi.kullanici_olustur",
    new_callable=AsyncMock
) as mock_create:
    mock_create.return_value = mock_user
```

## Verification Feedback Loop

After any code change, run:

```bash
# 1. Linting
cd backend && ruff check tests/integration/auth --select=E,F,W

# 2. Type checking (if applicable)
mypy tests/integration/auth

# 3. Run tests
pytest tests/integration/auth/test_auth_full_flow.py -x --tb=short
```

## Coverage Targets

| Module | Target Coverage |
|--------|----------------|
| `backend/api/auth.py` | 75%+ |
| Auth endpoints | 80%+ |
| Security features | 90%+ |

## Common Issues

### Issue: httpx.AsyncClient Import Error
**Solution**: Ensure `httpx` is installed: `pip install httpx`

### Issue: Mock Not Working
**Solution**: Check patch path matches import structure in tested code

### Issue: Test Timeout
**Solution**: Ensure all AsyncMock calls are properly awaited

## References

- [Backend API Auth](../../../api/auth.py)
- [User Models](../../../models/user_models.py)
- [KIRO2 Testing Rules](../../../../.claude/rules/testing.md)
- [Security Rules](../../../../.claude/rules/security.md)

## Next Steps

1. Add E2E tests with real database (Docker)
2. Add performance tests (load testing)
3. Add security penetration tests
4. Add API contract tests (OpenAPI validation)

---

**Created**: 2026-01-28
**Standards**: Boris Cherny Verification Feedback Loops
**Coverage**: 24 tests, F-01 series
