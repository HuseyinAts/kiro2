#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for api/admin.py
Test coverage improvement: 28% -> 70%
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the module to test
from api.admin import router, admin_kullanici_getir
from models.enums import KullaniciRolu
from models.user import Kullanici, KullaniciOlustur


@pytest.fixture
def app():
    """Create FastAPI app with admin router"""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    return Kullanici(
        id="admin-1",
        email="admin@test.com",
        ad_soyad="Test Admin",
        rol=KullaniciRolu.ADMIN,
        aktif=True,
        olusturma_tarihi=datetime.now(),
    )


@pytest.fixture
def mock_regular_user():
    """Mock regular user"""
    return Kullanici(
        id="user-1",
        email="user@test.com",
        ad_soyad="Test User",
        rol=KullaniciRolu.OGRENCI,
        aktif=True,
        olusturma_tarihi=datetime.now(),
    )


@pytest.fixture
def auth_headers():
    """Authorization headers"""
    return {"Authorization": "Bearer valid_token"}


@pytest.fixture
def invalid_auth_headers():
    """Invalid authorization headers"""
    return {"Authorization": "Bearer invalid_token"}


class TestAdminKullaniciGetir:
    """Test admin_kullanici_getir dependency function"""

    @pytest.mark.asyncio
    async def test_valid_admin_token(self, mock_admin_user):
        """Test valid admin token"""
        with patch("api.admin.kullanici_servisi.token_dogrula") as mock_token_validate:
            mock_token_validate.return_value = mock_admin_user

            from fastapi.security import HTTPAuthorizationCredentials

            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", credentials="valid_token"
            )

            result = await admin_kullanici_getir(credentials)

            assert result == mock_admin_user
            mock_token_validate.assert_called_once_with("valid_token")

    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test invalid token"""
        with patch("api.admin.kullanici_servisi.token_dogrula") as mock_token_validate:
            mock_token_validate.return_value = None

            from fastapi.security import HTTPAuthorizationCredentials
            from fastapi import HTTPException

            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", credentials="invalid_token"
            )

            with pytest.raises(HTTPException) as exc_info:
                await admin_kullanici_getir(credentials)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Geçersiz veya süresi dolmuş token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_non_admin_user(self, mock_regular_user):
        """Test non-admin user trying to access admin endpoints"""
        with patch("api.admin.kullanici_servisi.token_dogrula") as mock_token_validate:
            mock_token_validate.return_value = mock_regular_user

            from fastapi.security import HTTPAuthorizationCredentials
            from fastapi import HTTPException

            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer", credentials="valid_token"
            )

            with pytest.raises(HTTPException) as exc_info:
                await admin_kullanici_getir(credentials)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "admin yetkisi gerekli" in str(exc_info.value.detail)


class TestKullanicilariListele:
    """Test kullanicilari_listele endpoint"""

    @patch("api.admin.admin_servisi.kullanicilari_listele")
    @patch("api.admin.admin_kullanici_getir")
    def test_list_users_success(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test successful user listing"""
        mock_admin_auth.return_value = mock_admin_user
        mock_users = [
            {
                "id": "1",
                "email": "user1@test.com",
                "ad_soyad": "User One",
                "rol": "ogrenci",
                "aktif": True,
            },
            {
                "id": "2",
                "email": "user2@test.com",
                "ad_soyad": "User Two",
                "rol": "ogretmen",
                "aktif": True,
            },
        ]
        mock_admin_service.return_value = mock_users

        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_admin_service.assert_called_once()

    @patch("api.admin.admin_servisi.kullanicilari_listele")
    @patch("api.admin.admin_kullanici_getir")
    def test_list_users_with_filters(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test user listing with filters"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.return_value = []

        response = client.get(
            "/api/v1/admin/users?rol=ogrenci&aktif=true&sayfa=1&sayfa_boyutu=10",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        mock_admin_service.assert_called_once_with(
            rol=KullaniciRolu.OGRENCI, aktif=True, sayfa=1, sayfa_boyutu=10
        )

    @patch("api.admin.admin_servisi.kullanicilari_listele")
    @patch("api.admin.admin_kullanici_getir")
    def test_list_users_service_error(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test user listing with service error"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.side_effect = Exception("Database error")

        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 500
        assert "Kullanıcı listesi alınırken hata" in response.json()["detail"]


class TestKullaniciOlustur:
    """Test kullanici_olustur endpoint"""

    @patch("api.admin.admin_servisi.kullanici_olustur")
    @patch("api.admin.admin_kullanici_getir")
    def test_create_user_success(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test successful user creation"""
        mock_admin_auth.return_value = mock_admin_user
        new_user = {
            "id": "new-user-1",
            "email": "newuser@test.com",
            "ad_soyad": "New User",
            "rol": "ogrenci",
            "aktif": True,
        }
        mock_admin_service.return_value = new_user

        user_data = {
            "email": "newuser@test.com",
            "ad_soyad": "New User",
            "sifre": "password123",
            "rol": "ogrenci",
        }

        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        assert response.json()["email"] == "newuser@test.com"
        mock_admin_service.assert_called_once()

    @patch("api.admin.admin_servisi.kullanici_olustur")
    @patch("api.admin.admin_kullanici_getir")
    def test_create_user_validation_error(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test user creation with validation error"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.side_effect = ValueError("Email already exists")

        user_data = {
            "email": "existing@test.com",
            "ad_soyad": "Test User",
            "sifre": "password123",
            "rol": "ogrenci",
        }

        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 400
        assert "Email already exists" in response.json()["detail"]

    @patch("api.admin.admin_servisi.kullanici_olustur")
    @patch("api.admin.admin_kullanici_getir")
    def test_create_user_server_error(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test user creation with server error"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.side_effect = Exception("Database connection failed")

        user_data = {
            "email": "newuser@test.com",
            "ad_soyad": "New User",
            "sifre": "password123",
            "rol": "ogrenci",
        }

        response = client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 500
        assert "Kullanıcı oluşturulurken hata" in response.json()["detail"]


class TestKullaniciDetay:
    """Test kullanici_detay endpoint"""

    @patch("api.admin.admin_servisi.kullanici_getir")
    @patch("api.admin.admin_kullanici_getir")
    def test_get_user_detail_success(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test successful user detail retrieval"""
        mock_admin_auth.return_value = mock_admin_user
        user_detail = {
            "id": "user-1",
            "email": "user@test.com",
            "ad_soyad": "Test User",
            "rol": "ogrenci",
            "aktif": True,
        }
        mock_admin_service.return_value = user_detail

        response = client.get(
            "/api/v1/admin/users/user-1",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "user-1"
        mock_admin_service.assert_called_once_with("user-1")

    @patch("api.admin.admin_servisi.kullanici_getir")
    @patch("api.admin.admin_kullanici_getir")
    def test_get_user_detail_not_found(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test user detail retrieval when user not found"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.return_value = None

        response = client.get(
            "/api/v1/admin/users/nonexistent-user",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 404
        assert "Kullanıcı bulunamadı" in response.json()["detail"]


class TestKullaniciGuncelle:
    """Test kullanici_guncelle endpoint"""

    @patch("api.admin.admin_servisi.kullanici_guncelle")
    @patch("api.admin.admin_kullanici_getir")
    def test_update_user_success(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test successful user update"""
        mock_admin_auth.return_value = mock_admin_user
        updated_user = {
            "id": "user-1",
            "email": "user@test.com",
            "ad_soyad": "Updated User",
            "rol": "ogrenci",
            "aktif": True,
        }
        mock_admin_service.return_value = updated_user

        update_data = {"ad_soyad": "Updated User", "telefon": "+90 555 123 4567"}

        response = client.put(
            "/api/v1/admin/users/user-1",
            json=update_data,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        assert response.json()["ad_soyad"] == "Updated User"
        mock_admin_service.assert_called_once_with("user-1", update_data)

    @patch("api.admin.admin_servisi.kullanici_guncelle")
    @patch("api.admin.admin_kullanici_getir")
    def test_update_user_validation_error(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test user update with validation error"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.side_effect = ValueError("Invalid role")

        update_data = {"rol": "invalid_role"}

        response = client.put(
            "/api/v1/admin/users/user-1",
            json=update_data,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 400
        assert "Invalid role" in response.json()["detail"]

    @patch("api.admin.admin_servisi.kullanici_guncelle")
    @patch("api.admin.admin_kullanici_getir")
    def test_update_user_server_error(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test user update with server error"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.side_effect = Exception("Database error")

        update_data = {"ad_soyad": "Updated User"}

        response = client.put(
            "/api/v1/admin/users/user-1",
            json=update_data,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 500
        assert "Kullanıcı güncellenirken hata" in response.json()["detail"]


class TestAuthenticationFlow:
    """Test authentication and authorization flow"""

    def test_no_auth_header(self, client):
        """Test request without authorization header"""
        response = client.get("/api/v1/admin/users")
        assert (
            response.status_code == 403
        )  # FastAPI security returns 403 for missing auth

    def test_invalid_auth_header_format(self, client):
        """Test request with invalid authorization header format"""
        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 403

    @patch("api.admin.admin_kullanici_getir")
    def test_authentication_error_propagation(self, mock_admin_auth, client):
        """Test that authentication errors are properly propagated"""
        from fastapi import HTTPException

        mock_admin_auth.side_effect = HTTPException(
            status_code=401, detail="Invalid token"
        )

        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


class TestErrorHandling:
    """Test various error handling scenarios"""

    @patch("api.admin.admin_servisi.kullanicilari_listele")
    @patch("api.admin.admin_kullanici_getir")
    def test_unexpected_error_handling(
        self, mock_admin_auth, mock_admin_service, client, mock_admin_user
    ):
        """Test handling of unexpected errors"""
        mock_admin_auth.return_value = mock_admin_user
        mock_admin_service.side_effect = RuntimeError("Unexpected error")

        response = client.get(
            "/api/v1/admin/users", headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 500
        error_detail = response.json()["detail"]
        assert "Kullanıcı listesi alınırken hata" in error_detail
        assert "Unexpected error" in error_detail


class TestInputValidation:
    """Test input validation for various endpoints"""

    @patch("api.admin.admin_kullanici_getir")
    def test_pagination_validation(self, mock_admin_auth, client, mock_admin_user):
        """Test pagination parameter validation"""
        mock_admin_auth.return_value = mock_admin_user

        # Test invalid page number
        response = client.get(
            "/api/v1/admin/users?sayfa=0",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 422  # Validation error

        # Test invalid page size
        response = client.get(
            "/api/v1/admin/users?sayfa_boyutu=200",
            headers={"Authorization": "Bearer valid_token"},
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON payloads"""
        response = client.post(
            "/api/v1/admin/users",
            data="invalid json",
            headers={
                "Authorization": "Bearer valid_token",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
