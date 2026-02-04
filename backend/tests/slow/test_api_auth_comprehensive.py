"""
Comprehensive tests for api.auth module
Target: 90%+ coverage for authentication API endpoints
"""
import pytest
import jwt
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from api.auth import router as auth_router
from core.dependencies import JWT_SECRET, JWT_ALGORITHM


@pytest.fixture
def app():
    """Create FastAPI app for testing"""
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def valid_user_data():
    """Valid user registration data"""
    return {
        "username": "test_user",
        "email": "test@example.com",
        "password": "secure_password123",
        "full_name": "Test User",
        "role": "student",
    }


@pytest.fixture
def valid_login_data():
    """Valid login credentials"""
    return {"username": "test_user", "password": "secure_password123"}


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing"""
    payload = {
        "sub": "test_user_123",
        "username": "test_user",
        "role": "student",
        "email": "test@example.com",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


class TestAuthRegistration:
    """Test user registration endpoint"""

    def test_register_user_success(self, client, valid_user_data):
        """Test successful user registration"""
        with patch("api.auth.create_user") as mock_create_user:
            mock_create_user.return_value = {
                "id": "123",
                "username": "test_user",
                "email": "test@example.com",
                "role": "student",
            }

            response = client.post("/auth/register", json=valid_user_data)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["username"] == "test_user"
            assert data["email"] == "test@example.com"
            assert "password" not in data  # Password should not be returned

    def test_register_user_duplicate_username(self, client, valid_user_data):
        """Test registration with duplicate username"""
        with patch("api.auth.create_user") as mock_create_user:
            mock_create_user.side_effect = ValueError("Kullanıcı adı zaten mevcut")

            response = client.post("/auth/register", json=valid_user_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "zaten mevcut" in data["detail"]

    def test_register_user_duplicate_email(self, client, valid_user_data):
        """Test registration with duplicate email"""
        with patch("api.auth.create_user") as mock_create_user:
            mock_create_user.side_effect = ValueError("Email adresi zaten kayıtlı")

            response = client.post("/auth/register", json=valid_user_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "zaten kayıtlı" in data["detail"]

    def test_register_user_invalid_email(self, client, valid_user_data):
        """Test registration with invalid email format"""
        valid_user_data["email"] = "invalid-email"

        response = client.post("/auth/register", json=valid_user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_weak_password(self, client, valid_user_data):
        """Test registration with weak password"""
        valid_user_data["password"] = "123"

        with patch("api.auth.validate_password") as mock_validate:
            mock_validate.return_value = False

            response = client.post("/auth/register", json=valid_user_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_user_missing_fields(self, client):
        """Test registration with missing required fields"""
        incomplete_data = {
            "username": "test_user"
            # Missing other required fields
        }

        response = client.post("/auth/register", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_turkish_characters(self, client):
        """Test registration with Turkish characters"""
        turkish_data = {
            "username": "türkçe_kullanıcı",
            "email": "türkçe@örnek.com",
            "password": "güvenli_şifre123",
            "full_name": "Türkçe İsim Örnekü",
            "role": "öğrenci",
        }

        with patch("api.auth.create_user") as mock_create_user:
            mock_create_user.return_value = {
                "id": "124",
                "username": "türkçe_kullanıcı",
                "email": "türkçe@örnek.com",
                "role": "öğrenci",
            }

            response = client.post("/auth/register", json=turkish_data)

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "türkçe" in data["username"]

    def test_register_user_different_roles(self, client, valid_user_data):
        """Test registration with different user roles"""
        roles = ["student", "teacher", "parent", "admin"]

        for role in roles:
            with patch("api.auth.create_user") as mock_create_user:
                valid_user_data["role"] = role
                valid_user_data["username"] = f"user_{role}"

                mock_create_user.return_value = {
                    "id": f"id_{role}",
                    "username": f"user_{role}",
                    "email": "test@example.com",
                    "role": role,
                }

                response = client.post("/auth/register", json=valid_user_data)

                assert response.status_code == status.HTTP_201_CREATED
                data = response.json()
                assert data["role"] == role


class TestAuthLogin:
    """Test user login endpoint"""

    def test_login_success(self, client, valid_login_data):
        """Test successful login"""
        with patch("api.auth.authenticate_user") as mock_auth, patch(
            "api.auth.create_access_token"
        ) as mock_token:
            mock_auth.return_value = {
                "id": "123",
                "username": "test_user",
                "email": "test@example.com",
                "role": "student",
            }
            mock_token.return_value = "valid.jwt.token"

            response = client.post("/auth/login", json=valid_login_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            assert "user" in data

    def test_login_invalid_credentials(self, client, valid_login_data):
        """Test login with invalid credentials"""
        with patch("api.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            response = client.post("/auth/login", json=valid_login_data)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert (
                "Invalid credentials" in data["detail"] or "Geçersiz" in data["detail"]
            )

    def test_login_wrong_password(self, client, valid_login_data):
        """Test login with wrong password"""
        valid_login_data["password"] = "wrong_password"

        with patch("api.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            response = client.post("/auth/login", json=valid_login_data)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client, valid_login_data):
        """Test login with non-existent username"""
        valid_login_data["username"] = "nonexistent_user"

        with patch("api.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            response = client.post("/auth/login", json=valid_login_data)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        incomplete_data = {
            "username": "test_user"
            # Missing password
        }

        response = client.post("/auth/login", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_credentials(self, client):
        """Test login with empty credentials"""
        empty_data = {"username": "", "password": ""}

        response = client.post("/auth/login", json=empty_data)

        assert (
            response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            or response.status_code == status.HTTP_401_UNAUTHORIZED
        )

    def test_login_turkish_username(self, client):
        """Test login with Turkish username"""
        turkish_login = {"username": "türkçe_kullanıcı", "password": "güvenli_şifre123"}

        with patch("api.auth.authenticate_user") as mock_auth, patch(
            "api.auth.create_access_token"
        ) as mock_token:
            mock_auth.return_value = {
                "id": "124",
                "username": "türkçe_kullanıcı",
                "email": "türkçe@örnek.com",
                "role": "öğrenci",
            }
            mock_token.return_value = "valid.jwt.token"

            response = client.post("/auth/login", json=turkish_login)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "türkçe" in data["user"]["username"]

    def test_login_different_user_roles(self, client, valid_login_data):
        """Test login for different user roles"""
        roles = ["student", "teacher", "parent", "admin"]

        for role in roles:
            with patch("api.auth.authenticate_user") as mock_auth, patch(
                "api.auth.create_access_token"
            ) as mock_token:
                mock_auth.return_value = {
                    "id": f"id_{role}",
                    "username": "test_user",
                    "email": "test@example.com",
                    "role": role,
                }
                mock_token.return_value = f"token_for_{role}"

                response = client.post("/auth/login", json=valid_login_data)

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["user"]["role"] == role


class TestAuthTokenVerification:
    """Test token verification endpoint"""

    def test_verify_token_valid(self, client, valid_jwt_token):
        """Test verification of valid token"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/auth/verify", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "test_user"

    def test_verify_token_invalid(self, client):
        """Test verification of invalid token"""
        headers = {"Authorization": "Bearer invalid.jwt.token"}

        response = client.get("/auth/verify", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_expired(self, client):
        """Test verification of expired token"""
        import time

        # Create expired token
        expired_payload = {
            "sub": "test_user",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.get("/auth/verify", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_missing_authorization(self, client):
        """Test verification without authorization header"""
        response = client.get("/auth/verify")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_malformed_header(self, client):
        """Test verification with malformed authorization header"""
        headers = {"Authorization": "InvalidFormat token"}

        response = client.get("/auth/verify", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_empty_token(self, client):
        """Test verification with empty token"""
        headers = {"Authorization": "Bearer "}

        response = client.get("/auth/verify", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthLogout:
    """Test user logout endpoint"""

    def test_logout_success(self, client, valid_jwt_token):
        """Test successful logout"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("api.auth.invalidate_token") as mock_invalidate:
            mock_invalidate.return_value = True

            response = client.post("/auth/logout", headers=headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
            assert "logged out" in data["message"].lower() or "çıkış" in data["message"]

    def test_logout_without_token(self, client):
        """Test logout without token"""
        response = client.post("/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token"""
        headers = {"Authorization": "Bearer invalid.token"}

        response = client.post("/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthPasswordReset:
    """Test password reset functionality"""

    def test_request_password_reset_success(self, client):
        """Test successful password reset request"""
        reset_data = {"email": "test@example.com"}

        with patch("api.auth.send_password_reset_email") as mock_send_email:
            mock_send_email.return_value = True

            response = client.post("/auth/password-reset/request", json=reset_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data

    def test_request_password_reset_invalid_email(self, client):
        """Test password reset request with invalid email"""
        reset_data = {"email": "nonexistent@example.com"}

        with patch("api.auth.send_password_reset_email") as mock_send_email:
            mock_send_email.side_effect = ValueError("Email bulunamadı")

            response = client.post("/auth/password-reset/request", json=reset_data)

            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_reset_password_success(self, client):
        """Test successful password reset"""
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "new_secure_password123",
        }

        with patch("api.auth.reset_password_with_token") as mock_reset:
            mock_reset.return_value = True

            response = client.post("/auth/password-reset/confirm", json=reset_data)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data

    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token"""
        reset_data = {
            "token": "invalid_reset_token",
            "new_password": "new_secure_password123",
        }

        with patch("api.auth.reset_password_with_token") as mock_reset:
            mock_reset.side_effect = ValueError("Geçersiz token")

            response = client.post("/auth/password-reset/confirm", json=reset_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_password_weak_password(self, client):
        """Test password reset with weak password"""
        reset_data = {"token": "valid_reset_token", "new_password": "123"}

        with patch("api.auth.validate_password") as mock_validate:
            mock_validate.return_value = False

            response = client.post("/auth/password-reset/confirm", json=reset_data)

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAuthRefreshToken:
    """Test token refresh functionality"""

    def test_refresh_token_success(self, client, valid_jwt_token):
        """Test successful token refresh"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        with patch("api.auth.create_access_token") as mock_token:
            mock_token.return_value = "new.jwt.token"

            response = client.post("/auth/refresh", headers=headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert data["access_token"] == "new.jwt.token"

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token"""
        headers = {"Authorization": "Bearer invalid.token"}

        response = client.post("/auth/refresh", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_expired(self, client):
        """Test token refresh with expired token"""
        import time

        expired_payload = {"sub": "test_user", "exp": int(time.time()) - 3600}
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = client.post("/auth/refresh", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthUserProfile:
    """Test user profile management"""

    def test_get_current_user_profile(self, client, valid_jwt_token):
        """Test getting current user profile"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}

        response = client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "username" in data
        assert "email" in data
        assert "role" in data

    def test_update_user_profile(self, client, valid_jwt_token):
        """Test updating user profile"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        update_data = {"full_name": "Updated Full Name", "email": "updated@example.com"}

        with patch("api.auth.update_user_profile") as mock_update:
            mock_update.return_value = {
                "id": "123",
                "username": "test_user",
                "email": "updated@example.com",
                "full_name": "Updated Full Name",
                "role": "student",
            }

            response = client.put("/auth/me", json=update_data, headers=headers)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "updated@example.com"
            assert data["full_name"] == "Updated Full Name"

    def test_change_password(self, client, valid_jwt_token):
        """Test changing user password"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        password_data = {
            "current_password": "old_password",
            "new_password": "new_secure_password123",
        }

        with patch("api.auth.change_user_password") as mock_change:
            mock_change.return_value = True

            response = client.post(
                "/auth/change-password", json=password_data, headers=headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data

    def test_change_password_wrong_current(self, client, valid_jwt_token):
        """Test changing password with wrong current password"""
        headers = {"Authorization": f"Bearer {valid_jwt_token}"}
        password_data = {
            "current_password": "wrong_password",
            "new_password": "new_secure_password123",
        }

        with patch("api.auth.change_user_password") as mock_change:
            mock_change.side_effect = ValueError("Mevcut şifre yanlış")

            response = client.post(
                "/auth/change-password", json=password_data, headers=headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAuthenticationIntegration:
    """Integration tests for authentication flow"""

    def test_complete_auth_flow(self, client, valid_user_data, valid_login_data):
        """Test complete authentication flow: register -> login -> verify -> logout"""
        # Register user
        with patch("api.auth.create_user") as mock_create:
            mock_create.return_value = {
                "id": "123",
                "username": "test_user",
                "email": "test@example.com",
                "role": "student",
            }

            register_response = client.post("/auth/register", json=valid_user_data)
            assert register_response.status_code == status.HTTP_201_CREATED

        # Login
        with patch("api.auth.authenticate_user") as mock_auth, patch(
            "api.auth.create_access_token"
        ) as mock_token:
            mock_auth.return_value = {
                "id": "123",
                "username": "test_user",
                "email": "test@example.com",
                "role": "student",
            }
            mock_token.return_value = "valid.jwt.token"

            login_response = client.post("/auth/login", json=valid_login_data)
            assert login_response.status_code == status.HTTP_200_OK
            token = login_response.json()["access_token"]

        # Verify token
        headers = {"Authorization": f"Bearer {token}"}
        verify_response = client.get("/auth/verify", headers=headers)
        assert verify_response.status_code == status.HTTP_200_OK

        # Logout
        with patch("api.auth.invalidate_token") as mock_invalidate:
            mock_invalidate.return_value = True

            logout_response = client.post("/auth/logout", headers=headers)
            assert logout_response.status_code == status.HTTP_200_OK

    def test_auth_error_handling_consistency(self, client):
        """Test that auth errors are handled consistently"""
        # Test various invalid requests
        invalid_requests = [
            ("POST", "/auth/register", {"username": ""}),
            ("POST", "/auth/login", {"username": "", "password": ""}),
            ("GET", "/auth/verify", {}),
            ("POST", "/auth/logout", {}),
        ]

        for method, endpoint, data in invalid_requests:
            if method == "POST":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)

            # Should return appropriate error status
            assert response.status_code in [400, 401, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
