# PHASE 2.7: AUTH API INTEGRATION TESTING GUIDE

**Tarih**: 2025-11-22
**Phase**: Auth API Migration Testing
**Status**: ✅ Complete
**File**: `backend/api/auth_refactored.py` (690 lines)

---

## 🎯 OVERVIEW

This document provides comprehensive testing guidance for the migrated authentication API that now uses the refactored user service with full database persistence.

**Key Changes:**
- ✅ Removed in-memory storage from auth endpoints
- ✅ Added database session dependency injection
- ✅ Enhanced security with IP/User-Agent tracking
- ✅ Improved session management with database persistence

---

## 🧪 UNIT TESTING

### Test 1: User Registration

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models.database import Base
from core.dependencies import get_db


# Fixture for test database
@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_user_registration_success(client):
    """Test successful user registration"""
    response = client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "test@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Test User",
            "rol": "ogrenci",
            "telefon": "+905551234567",
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Kullanıcı kaydı başarıyla oluşturuldu"


def test_user_registration_duplicate_email(client):
    """Test registration with duplicate email"""
    # First registration
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "duplicate@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Test User",
            "rol": "ogrenci",
        }
    )

    # Second registration with same email
    response = client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "duplicate@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Another User",
            "rol": "ogrenci",
        }
    )

    assert response.status_code == 400
    assert "Bu e-posta adresi zaten kullanımda" in response.json()["detail"]


def test_user_registration_weak_password(client):
    """Test registration with weak password"""
    response = client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "weak@example.com",
            "sifre": "123",  # Too weak
            "ad_soyad": "Test User",
            "rol": "ogrenci",
        }
    )

    assert response.status_code == 400
    assert "Şifre gereksinimleri" in response.json()["detail"]
```

---

### Test 2: User Login

```python
def test_user_login_success(client):
    """Test successful login"""
    # First register a user
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "login@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Login Test",
            "rol": "ogrenci",
        }
    )

    # Then login
    response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "login@example.com",
            "sifre": "SecureP@ss123",
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Frontend format checks
    assert data["success"] is True
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "login@example.com"
    assert data["user"]["rol"] == "ogrenci"

    # Backward compatibility checks
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_user_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "nonexistent@example.com",
            "sifre": "WrongPassword123!",
        }
    )

    assert response.status_code == 401
    assert "Geçersiz e-posta veya şifre" in response.json()["detail"]


def test_user_login_inactive_account(client, db_session):
    """Test login with inactive account"""
    # Register user
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "inactive@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Inactive User",
            "rol": "ogrenci",
        }
    )

    # Deactivate user in database
    from models.database import User
    user = db_session.query(User).filter_by(email="inactive@example.com").first()
    user.is_active = False
    db_session.commit()

    # Try to login
    response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "inactive@example.com",
            "sifre": "SecureP@ss123",
        }
    )

    assert response.status_code == 401
    assert "Hesap aktif değil" in response.json()["detail"]
```

---

### Test 3: Token Validation & Profile

```python
def test_get_current_user_with_valid_token(client):
    """Test getting current user with valid token"""
    # Register and login
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "profile@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Profile Test",
            "rol": "ogrenci",
        }
    )

    login_response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "profile@example.com",
            "sifre": "SecureP@ss123",
        }
    )

    token = login_response.json()["token"]

    # Get profile
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == "profile@example.com"


def test_get_current_user_with_invalid_token(client):
    """Test getting current user with invalid token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_12345"}
    )

    assert response.status_code == 401


def test_validate_token_endpoint(client):
    """Test token validation endpoint"""
    # Register and login
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "validate@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Validate Test",
            "rol": "ogrenci",
        }
    )

    login_response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "validate@example.com",
            "sifre": "SecureP@ss123",
        }
    )

    token = login_response.json()["token"]

    # Validate token
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True

    # Validate invalid token
    response = client.post(
        "/api/v1/auth/validate",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == 200
    assert response.json()["valid"] is False
```

---

### Test 4: Logout

```python
def test_user_logout_success(client):
    """Test successful logout"""
    # Register and login
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "logout@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Logout Test",
            "rol": "ogrenci",
        }
    )

    login_response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "logout@example.com",
            "sifre": "SecureP@ss123",
        }
    )

    token = login_response.json()["token"]

    # Logout
    response = client.post(
        "/api/v1/auth/cikis",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert "Başarıyla çıkış yapıldı" in response.json()["message"]

    # Verify token is invalidated
    profile_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert profile_response.status_code == 401


def test_logout_all_devices(client):
    """Test logout from all devices"""
    # Register user
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "multidevice@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Multi Device Test",
            "rol": "ogrenci",
        }
    )

    # Login from "device 1"
    login1 = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "multidevice@example.com",
            "sifre": "SecureP@ss123",
        }
    )
    token1 = login1.json()["token"]

    # Login from "device 2"
    login2 = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "multidevice@example.com",
            "sifre": "SecureP@ss123",
        }
    )
    token2 = login2.json()["token"]

    # Logout all devices using token1
    response = client.post(
        "/api/v1/auth/logout-all",
        headers={"Authorization": f"Bearer {token1}"}
    )

    assert response.status_code == 200
    assert "oturum sonlandırıldı" in response.json()["message"]

    # Verify both tokens are invalidated
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token1}"}
    ).status_code == 401

    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token2}"}
    ).status_code == 401
```

---

### Test 5: Session Tracking (IP & User-Agent)

```python
def test_session_tracking_ip_and_user_agent(client, db_session):
    """Test that login tracks IP and User-Agent"""
    # Register user
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "tracking@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Tracking Test",
            "rol": "ogrenci",
        }
    )

    # Login with custom headers
    response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "tracking@example.com",
            "sifre": "SecureP@ss123",
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )

    assert response.status_code == 200
    token = response.json()["token"]

    # Verify session was created with tracking info
    from models.database import Session as DBSession
    session = db_session.query(DBSession).filter_by(token=token).first()

    assert session is not None
    assert session.user_agent == "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    assert session.ip_address is not None  # TestClient provides testclient IP
    assert session.is_active is True
    assert session.expires_at is not None


def test_session_expiration_check(client, db_session):
    """Test that expired sessions are not valid"""
    from datetime import datetime, timedelta, timezone
    from models.database import Session as DBSession, User

    # Register user
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "expired@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Expired Test",
            "rol": "ogrenci",
        }
    )

    # Login
    response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "expired@example.com",
            "sifre": "SecureP@ss123",
        }
    )

    token = response.json()["token"]

    # Manually expire the session in database
    session = db_session.query(DBSession).filter_by(token=token).first()
    session.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    # Try to use expired token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
```

---

## 🔄 INTEGRATION TESTING

### Test 6: Complete User Flow

```python
def test_complete_user_lifecycle(client, db_session):
    """Test complete user lifecycle: register → login → profile → update → logout"""

    # Step 1: Register
    register_response = client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "lifecycle@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Life Cycle Test",
            "rol": "ogrenci",
            "telefon": "+905551234567",
        }
    )
    assert register_response.status_code == 201

    # Step 2: Login
    login_response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "lifecycle@example.com",
            "sifre": "SecureP@ss123",
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Step 3: Get Profile
    profile_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["user"]["email"] == "lifecycle@example.com"

    # Step 4: Update Profile
    update_response = client.put(
        "/api/v1/auth/profile",
        json={
            "ad_soyad": "Updated Name",
            "telefon": "+905559999999",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["success"] is True

    # Step 5: Verify Update
    profile_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    user = profile_response.json()["user"]
    assert user["ad"] == "Updated"
    assert user["soyad"] == "Name"
    assert user["telefon"] == "+905559999999"

    # Step 6: Logout
    logout_response = client.post(
        "/api/v1/auth/cikis",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_response.status_code == 200

    # Step 7: Verify Logout
    profile_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 401
```

---

## 📊 PERFORMANCE TESTING

### Test 7: Concurrent Logins

```python
import concurrent.futures

def test_concurrent_login_performance(client):
    """Test system handles concurrent logins"""

    # Register test users
    for i in range(10):
        client.post(
            "/api/v1/auth/kayit",
            json={
                "email": f"concurrent{i}@example.com",
                "sifre": "SecureP@ss123",
                "ad_soyad": f"Concurrent User {i}",
                "rol": "ogrenci",
            }
        )

    # Concurrent login function
    def login_user(user_id):
        response = client.post(
            "/api/v1/auth/giris",
            json={
                "email": f"concurrent{user_id}@example.com",
                "sifre": "SecureP@ss123",
            }
        )
        return response.status_code == 200

    # Execute concurrent logins
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(login_user, range(10)))

    # Verify all logins succeeded
    assert all(results), "Some concurrent logins failed"
```

---

## 🔒 SECURITY TESTING

### Test 8: SQL Injection Protection

```python
def test_sql_injection_protection(client):
    """Test that SQL injection attempts are prevented"""

    # Try SQL injection in email field
    response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "admin'--",
            "sifre": "' OR '1'='1",
        }
    )

    # Should fail authentication, not expose SQL error
    assert response.status_code == 401
    assert "SQL" not in response.json()["detail"].upper()


def test_token_fixation_attack_prevention(client):
    """Test that old tokens can't be reused after logout"""

    # Register and login
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "fixation@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Fixation Test",
            "rol": "ogrenci",
        }
    )

    login_response = client.post(
        "/api/v1/auth/giris",
        json={
            "email": "fixation@example.com",
            "sifre": "SecureP@ss123",
        }
    )

    old_token = login_response.json()["token"]

    # Logout
    client.post(
        "/api/v1/auth/cikis",
        headers={"Authorization": f"Bearer {old_token}"}
    )

    # Try to reuse old token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {old_token}"}
    )

    assert response.status_code == 401


def test_brute_force_protection(client):
    """Test that multiple failed login attempts are handled"""

    # Register user
    client.post(
        "/api/v1/auth/kayit",
        json={
            "email": "bruteforce@example.com",
            "sifre": "SecureP@ss123",
            "ad_soyad": "Brute Force Test",
            "rol": "ogrenci",
        }
    )

    # Attempt multiple failed logins
    failed_attempts = 0
    for _ in range(10):
        response = client.post(
            "/api/v1/auth/giris",
            json={
                "email": "bruteforce@example.com",
                "sifre": "WrongPassword123!",
            }
        )
        if response.status_code == 401:
            failed_attempts += 1

    # All attempts should fail with 401
    assert failed_attempts == 10

    # TODO: Implement rate limiting to return 429 after X attempts
```

---

## 📝 MANUAL TESTING CHECKLIST

### Registration Flow:
- [ ] Register new user with valid data → Success
- [ ] Register with duplicate email → Error 400
- [ ] Register with weak password → Error 400
- [ ] Register with invalid email format → Error 422
- [ ] Register with missing fields → Error 422

### Login Flow:
- [ ] Login with valid credentials → Success with token
- [ ] Login with invalid email → Error 401
- [ ] Login with invalid password → Error 401
- [ ] Login with inactive account → Error 401
- [ ] Verify IP address is tracked in session
- [ ] Verify User-Agent is tracked in session

### Profile Management:
- [ ] Get profile with valid token → Success
- [ ] Get profile with invalid token → Error 401
- [ ] Get profile with expired token → Error 401
- [ ] Update profile with valid data → Success
- [ ] Update profile without authentication → Error 401

### Logout Flow:
- [ ] Logout with valid token → Success
- [ ] Try to use token after logout → Error 401
- [ ] Logout from all devices → All sessions invalidated
- [ ] Verify database session record has is_active=False

### Token Validation:
- [ ] Validate valid token → {valid: true}
- [ ] Validate invalid token → {valid: false}
- [ ] Validate expired token → {valid: false}

---

## 🚀 RUNNING THE TESTS

### Setup Test Environment:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Create test database
pytest --setup-show

# Run all tests
pytest backend/tests/test_auth_integration.py -v

# Run specific test
pytest backend/tests/test_auth_integration.py::test_user_registration_success -v

# Run with coverage
pytest --cov=backend/api backend/tests/test_auth_integration.py
```

### Expected Coverage:

| Module | Coverage Target |
|--------|----------------|
| auth_refactored.py | 85%+ |
| user_service_refactored.py | 90%+ |
| session_repository.py | 95%+ |
| user_repository.py | 90%+ |

---

## 📈 MIGRATION VERIFICATION

### Before Migration (auth.py):
```python
# Lines 114-118: Hybrid approach (BAD)
kullanici_servisi.aktif_tokenlar[token] = {
    "kullanici_id": db_user.id,
    "expires_at": datetime.now() + timedelta(seconds=expires_in),
}
kullanici_servisi.kullanicilar[db_user.id] = kullanici
```

### After Migration (auth_refactored.py):
```python
# Full database persistence (GOOD)
service = get_kullanici_servisi(db)
token_yaniti = await service.kullanici_giris(
    giris_data,
    ip_address=ip_address,
    user_agent=user_agent,
)
# No in-memory storage! All in database.
```

---

## ✅ SUCCESS CRITERIA

**Phase 2.7 Complete When:**
- ✅ All unit tests pass (100%)
- ✅ All integration tests pass (100%)
- ✅ Security tests pass (SQL injection, token fixation)
- ✅ Performance tests show no regression
- ✅ Manual testing checklist complete
- ✅ Code coverage >= 85%
- ✅ No in-memory storage references in auth_refactored.py
- ✅ Database sessions properly tracked with IP/User-Agent
- ✅ Old auth.py can be safely removed

---

## 🎯 NEXT STEPS

1. **Replace auth.py with auth_refactored.py**
   ```bash
   # Backup old file
   mv backend/api/auth.py backend/api/auth_OLD_BACKUP.py

   # Activate new file
   mv backend/api/auth_refactored.py backend/api/auth.py
   ```

2. **Update main.py imports** (if needed)
   ```python
   from api.auth import router as auth_router
   # Should now use the refactored version
   ```

3. **Run full test suite**
   ```bash
   pytest backend/tests/ -v --cov=backend
   ```

4. **Deploy to staging** for real-world testing

5. **Phase 2.8**: Migrate exam service (sinav_motoru_service.py)

---

**Generated**: 2025-11-22
**File**: auth_refactored.py (690 lines)
**Tests Written**: 8 comprehensive tests
**Coverage Target**: 85%+
**Production Ready**: ✅ Yes (after testing)
