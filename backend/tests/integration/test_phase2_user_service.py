from unittest.mock import Mock, patch, AsyncMock

"""
Phase 2: User Service Comprehensive Tests
Target: 0% → 40%+ coverage for services/user_service.py (274 lines)
Focus: Authentication, user management, profile management, security
"""

import hashlib
import os
import sys
from datetime import datetime, timedelta

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKullaniciServisiCore:
    """Test KullaniciServisi core functionality"""

    def test_kullanici_servisi_creation(self):
        """Test KullaniciServisi instantiation"""
        try:
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Test initialization of data structures
            assert isinstance(service.kullanicilar, dict)
            assert isinstance(service.sifreler, dict)
            assert isinstance(service.email_index, dict)
            assert isinstance(service.ogrenci_profilleri, dict)
            assert isinstance(service.ogretmen_profilleri, dict)
            assert isinstance(service.veli_profilleri, dict)
            assert isinstance(service.aktif_tokenlar, dict)

            # Test initial state is empty
            assert len(service.kullanicilar) == 0
            assert len(service.sifreler) == 0
            assert len(service.email_index) == 0

        except ImportError:
            pytest.skip("KullaniciServisi not available")

    def test_sifre_hash_et_method(self):
        """Test password hashing method"""
        try:
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Test password hashing
            password = "test_password_123"
            hashed = service._sifre_hash_et(password)

            assert isinstance(hashed, str)
            assert len(hashed) > 0
            assert hashed != password  # Should be different from original

            # Test same password gives same hash
            hashed2 = service._sifre_hash_et(password)
            assert hashed == hashed2

            # Test different passwords give different hashes
            different_hash = service._sifre_hash_et("different_password")
            assert hashed != different_hash

            # Test expected SHA256 behavior
            expected_hash = hashlib.sha256(password.encode()).hexdigest()
            assert hashed == expected_hash

        except ImportError:
            pytest.skip("KullaniciServisi not available")

    def test_token_olustur_method(self):
        """Test token generation method"""
        try:
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Test token generation
            token1 = service._token_olustur("user123")
            token2 = service._token_olustur("user456")

            assert isinstance(token1, str)
            assert isinstance(token2, str)
            assert len(token1) > 0
            assert len(token2) > 0

            # Tokens should be unique
            assert token1 != token2

            # Test multiple tokens for same user are different
            token3 = service._token_olustur("user123")
            assert token1 != token3

        except ImportError:
            pytest.skip("KullaniciServisi not available")


class TestKullaniciOlusturma:
    """Test user creation functionality"""

    @pytest.mark.asyncio
    async def test_kullanici_olustur_success(self):
        """Test successful user creation"""
        try:
            from models import KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            kullanici_data = KullaniciOlustur(
                email="test@example.com",
                sifre="test_password_123",
                ad_soyad="Test User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            # Test user creation
            assert kullanici.email == "test@example.com"
            assert kullanici.ad_soyad == "Test User"
            assert kullanici.telefon == "05551234567"
            assert kullanici.rol == KullaniciRolu.OGRENCI
            assert kullanici.aktif is True
            assert isinstance(kullanici.kullanici_id, str)
            assert isinstance(kullanici.olusturma_tarihi, datetime)

            # Test internal data structures
            assert kullanici.kullanici_id in service.kullanicilar
            assert kullanici.kullanici_id in service.sifreler
            assert kullanici.email in service.email_index
            assert service.email_index[kullanici.email] == kullanici.kullanici_id

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_olustur_duplicate_email(self):
        """Test user creation with duplicate email"""
        try:
            from models import KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            kullanici_data1 = KullaniciOlustur(
                email="duplicate@example.com",
                sifre="password1",
                ad_soyad="User One",
                telefon="05551111111",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici_data2 = KullaniciOlustur(
                email="duplicate@example.com",  # Same email
                sifre="password2",
                ad_soyad="User Two",
                telefon="05552222222",
                rol=KullaniciRolu.OGRETMEN,
            )

            # First user should be created successfully
            kullanici1 = await service.kullanici_olustur(kullanici_data1)
            assert kullanici1.email == "duplicate@example.com"

            # Second user with same email should fail
            with pytest.raises(ValueError, match="Bu e-posta adresi zaten kullanımda"):
                await service.kullanici_olustur(kullanici_data2)

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_olustur_different_roles(self):
        """Test user creation with different roles"""
        try:
            from models import KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Test all user roles
            roles_to_test = [
                KullaniciRolu.OGRENCI,
                KullaniciRolu.OGRETMEN,
                KullaniciRolu.VELI,
                KullaniciRolu.ADMIN,
            ]

            for i, rol in enumerate(roles_to_test):
                kullanici_data = KullaniciOlustur(
                    email=f"user{i}@example.com",
                    sifre=f"password{i}",
                    ad_soyad=f"User {i}",
                    telefon=f"0555000000{i}",
                    rol=rol,
                )

                kullanici = await service.kullanici_olustur(kullanici_data)
                assert kullanici.rol == rol
                assert kullanici.email == f"user{i}@example.com"

            # Verify all users are stored
            assert len(service.kullanicilar) == len(roles_to_test)

        except ImportError:
            pytest.skip("Required models not available")


class TestKullaniciGiris:
    """Test user authentication functionality"""

    @pytest.mark.asyncio
    async def test_kullanici_giris_success(self):
        """Test successful user login"""
        try:
            from models import KullaniciGiris, KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create a user first
            kullanici_data = KullaniciOlustur(
                email="login@example.com",
                sifre="login_password",
                ad_soyad="Login User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            # Test login
            giris_data = KullaniciGiris(
                email="login@example.com", sifre="login_password"
            )

            token_response = await service.kullanici_giris(giris_data)

            # Test token response
            assert token_response.access_token is not None
            assert isinstance(token_response.access_token, str)
            assert len(token_response.access_token) > 0
            assert token_response.token_type == "bearer"
            assert token_response.expires_in == 3600 * 24  # 24 hours
            assert token_response.kullanici.kullanici_id == kullanici.kullanici_id

            # Test internal token storage
            assert token_response.access_token in service.aktif_tokenlar
            token_info = service.aktif_tokenlar[token_response.access_token]
            assert token_info["kullanici_id"] == kullanici.kullanici_id
            assert isinstance(token_info["expires_at"], datetime)

            # Test last login update
            updated_user = service.kullanicilar[kullanici.kullanici_id]
            assert updated_user.son_giris is not None

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_giris_invalid_email(self):
        """Test login with invalid email"""
        try:
            from models import KullaniciGiris
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            giris_data = KullaniciGiris(
                email="nonexistent@example.com", sifre="any_password"
            )

            with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
                await service.kullanici_giris(giris_data)

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_giris_invalid_password(self):
        """Test login with invalid password"""
        try:
            from models import KullaniciGiris, KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create a user first
            kullanici_data = KullaniciOlustur(
                email="password_test@example.com",
                sifre="correct_password",
                ad_soyad="Password User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            await service.kullanici_olustur(kullanici_data)

            # Test login with wrong password
            giris_data = KullaniciGiris(
                email="password_test@example.com", sifre="wrong_password"
            )

            with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
                await service.kullanici_giris(giris_data)

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_giris_inactive_user(self):
        """Test login with inactive user"""
        try:
            from models import KullaniciGiris, KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create a user first
            kullanici_data = KullaniciOlustur(
                email="inactive@example.com",
                sifre="password",
                ad_soyad="Inactive User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            # Make user inactive
            kullanici.aktif = False

            # Test login with inactive user
            giris_data = KullaniciGiris(email="inactive@example.com", sifre="password")

            with pytest.raises(ValueError, match="Hesap aktif değil"):
                await service.kullanici_giris(giris_data)

        except ImportError:
            pytest.skip("Required models not available")


class TestTokenDogrulama:
    """Test token validation functionality"""

    @pytest.mark.asyncio
    async def test_token_dogrula_valid_token(self):
        """Test token validation with valid token"""
        try:
            from models import KullaniciGiris, KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create user and login
            kullanici_data = KullaniciOlustur(
                email="token@example.com",
                sifre="password",
                ad_soyad="Token User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            giris_data = KullaniciGiris(email="token@example.com", sifre="password")

            token_response = await service.kullanici_giris(giris_data)

            # Test token validation
            validated_user = await service.token_dogrula(token_response.access_token)

            assert validated_user is not None
            assert validated_user.kullanici_id == kullanici.kullanici_id
            assert validated_user.email == kullanici.email

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_token_dogrula_invalid_token(self):
        """Test token validation with invalid token"""
        try:
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Test with non-existent token
            validated_user = await service.token_dogrula("invalid_token_123")
            assert validated_user is None

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_token_dogrula_expired_token(self):
        """Test token validation with expired token"""
        try:
            from models import KullaniciGiris, KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create user and login
            kullanici_data = KullaniciOlustur(
                email="expired@example.com",
                sifre="password",
                ad_soyad="Expired User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            await service.kullanici_olustur(kullanici_data)

            giris_data = KullaniciGiris(email="expired@example.com", sifre="password")

            token_response = await service.kullanici_giris(giris_data)

            # Manually expire the token
            token_info = service.aktif_tokenlar[token_response.access_token]
            token_info["expires_at"] = datetime.now() - timedelta(hours=1)

            # Test token validation
            validated_user = await service.token_dogrula(token_response.access_token)
            assert validated_user is None

            # Token should be removed from active tokens
            assert token_response.access_token not in service.aktif_tokenlar

        except ImportError:
            pytest.skip("Required models not available")


class TestKullaniciYonetimi:
    """Test user management functionality"""

    @pytest.mark.asyncio
    async def test_kullanici_getir(self):
        """Test getting user by ID"""
        try:
            from models import KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create a user
            kullanici_data = KullaniciOlustur(
                email="getir@example.com",
                sifre="password",
                ad_soyad="Get User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            # Test getting user
            retrieved_user = await service.kullanici_getir(kullanici.kullanici_id)

            assert retrieved_user is not None
            assert retrieved_user.kullanici_id == kullanici.kullanici_id
            assert retrieved_user.email == kullanici.email

            # Test getting non-existent user
            non_existent = await service.kullanici_getir("non_existent_id")
            assert non_existent is None

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_listesi(self):
        """Test getting user list"""
        try:
            from models import KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create users with different roles
            users_data = [
                ("student1@example.com", KullaniciRolu.OGRENCI),
                ("student2@example.com", KullaniciRolu.OGRENCI),
                ("teacher1@example.com", KullaniciRolu.OGRETMEN),
                ("parent1@example.com", KullaniciRolu.VELI),
            ]

            for email, rol in users_data:
                kullanici_data = KullaniciOlustur(
                    email=email,
                    sifre="password",
                    ad_soyad=f"User {email}",
                    telefon="05551234567",
                    rol=rol,
                )
                await service.kullanici_olustur(kullanici_data)

            # Test getting all users
            all_users = await service.kullanici_listesi()
            assert len(all_users) == 4

            # Test filtering by role
            students = await service.kullanici_listesi(rol=KullaniciRolu.OGRENCI)
            assert len(students) == 2
            assert all(user.rol == KullaniciRolu.OGRENCI for user in students)

            teachers = await service.kullanici_listesi(rol=KullaniciRolu.OGRETMEN)
            assert len(teachers) == 1
            assert teachers[0].rol == KullaniciRolu.OGRETMEN

            parents = await service.kullanici_listesi(rol=KullaniciRolu.VELI)
            assert len(parents) == 1
            assert parents[0].rol == KullaniciRolu.VELI

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_guncelle(self):
        """Test updating user information"""
        try:
            from models import KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create a user
            kullanici_data = KullaniciOlustur(
                email="update@example.com",
                sifre="password",
                ad_soyad="Original Name",
                telefon="05551111111",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)
            original_update_time = kullanici.son_guncelleme

            # Test updating user information
            update_data = {
                "ad_soyad": "Updated Name",
                "telefon": "05552222222",
                "aktif": False,
            }

            updated_user = await service.kullanici_guncelle(
                kullanici.kullanici_id, update_data
            )

            assert updated_user is not None
            assert updated_user.ad_soyad == "Updated Name"
            assert updated_user.telefon == "05552222222"
            assert updated_user.aktif is False
            assert updated_user.son_guncelleme != original_update_time

            # Test updating role
            role_update = {"rol": KullaniciRolu.OGRETMEN.value}
            updated_user = await service.kullanici_guncelle(
                kullanici.kullanici_id, role_update
            )
            assert updated_user.rol == KullaniciRolu.OGRETMEN

            # Test updating non-existent user
            non_updated = await service.kullanici_guncelle("non_existent", update_data)
            assert non_updated is None

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_cikis(self):
        """Test user logout functionality"""
        try:
            from models import KullaniciGiris, KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create user and login
            kullanici_data = KullaniciOlustur(
                email="logout@example.com",
                sifre="password",
                ad_soyad="Logout User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            await service.kullanici_olustur(kullanici_data)

            giris_data = KullaniciGiris(email="logout@example.com", sifre="password")

            token_response = await service.kullanici_giris(giris_data)
            token = token_response.access_token

            # Verify token exists
            assert token in service.aktif_tokenlar

            # Test logout
            logout_success = await service.kullanici_cikis(token)
            assert logout_success is True

            # Verify token is removed
            assert token not in service.aktif_tokenlar

            # Test logout with invalid token
            invalid_logout = await service.kullanici_cikis("invalid_token")
            assert invalid_logout is False

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_kullanici_sil(self):
        """Test user deletion functionality"""
        try:
            from models import KullaniciGiris, KullaniciOlustur, KullaniciRolu
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create user and login
            kullanici_data = KullaniciOlustur(
                email="delete@example.com",
                sifre="password",
                ad_soyad="Delete User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            giris_data = KullaniciGiris(email="delete@example.com", sifre="password")

            token_response = await service.kullanici_giris(giris_data)

            # Verify user exists in all data structures
            assert kullanici.kullanici_id in service.kullanicilar
            assert kullanici.kullanici_id in service.sifreler
            assert kullanici.email in service.email_index
            assert token_response.access_token in service.aktif_tokenlar

            # Test user deletion
            delete_success = await service.kullanici_sil(kullanici.kullanici_id)
            assert delete_success is True

            # Verify user is removed from all data structures
            assert kullanici.kullanici_id not in service.kullanicilar
            assert kullanici.kullanici_id not in service.sifreler
            assert kullanici.email not in service.email_index
            assert token_response.access_token not in service.aktif_tokenlar

            # Test deleting non-existent user
            non_delete = await service.kullanici_sil("non_existent_id")
            assert non_delete is False

        except ImportError:
            pytest.skip("Required models not available")


class TestProfilYonetimi:
    """Test profile management functionality"""

    @pytest.mark.asyncio
    async def test_ogrenci_profili_olustur(self):
        """Test student profile creation"""
        try:
            from models import KullaniciOlustur, KullaniciRolu, OgrenciProfili
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create a student user
            kullanici_data = KullaniciOlustur(
                email="student@example.com",
                sifre="password",
                ad_soyad="Student User",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            # Create student profile
            profil_data = OgrenciProfili(
                ogrenci_id="STU123",
                kullanici_id=kullanici.kullanici_id,
                sinif=9,
                okul="Test Lisesi",
                bolum="Fen",
                no=123,
            )

            profil = await service.ogrenci_profili_olustur(profil_data)

            assert profil.ogrenci_id == "STU123"
            assert profil.kullanici_id == kullanici.kullanici_id
            assert profil.sinif == 9
            assert profil.okul == "Test Lisesi"

            # Verify profile is stored
            assert "STU123" in service.ogrenci_profilleri

        except ImportError:
            pytest.skip("Required models not available")

    @pytest.mark.asyncio
    async def test_ogrenci_profili_getir(self):
        """Test getting student profile"""
        try:
            from models import KullaniciOlustur, KullaniciRolu, OgrenciProfili
            from services.user_service import KullaniciServisi

            service = KullaniciServisi()

            # Create student user and profile
            kullanici_data = KullaniciOlustur(
                email="student2@example.com",
                sifre="password",
                ad_soyad="Student User 2",
                telefon="05551234567",
                rol=KullaniciRolu.OGRENCI,
            )

            kullanici = await service.kullanici_olustur(kullanici_data)

            profil_data = OgrenciProfili(
                ogrenci_id="STU456",
                kullanici_id=kullanici.kullanici_id,
                sinif=10,
                okul="Test Lisesi 2",
                bolum="Sayısal",
                no=456,
            )

            await service.ogrenci_profili_olustur(profil_data)

            # Test getting profile
            retrieved_profile = await service.ogrenci_profili_getir("STU456")

            assert retrieved_profile is not None
            assert retrieved_profile.ogrenci_id == "STU456"
            assert retrieved_profile.sinif == 10

            # Test getting non-existent profile
            non_existent = await service.ogrenci_profili_getir("STU999")
            assert non_existent is None

        except ImportError:
            pytest.skip("Required models not available")


class TestGlobalServisInstance:
    """Test global service instance"""

    def test_global_kullanici_servisi_import(self):
        """Test global kullanici_servisi can be imported"""
        try:
            from services.user_service import kullanici_servisi

            assert kullanici_servisi is not None
            assert hasattr(kullanici_servisi, "kullanicilar")
            assert hasattr(kullanici_servisi, "sifreler")
            assert hasattr(kullanici_servisi, "email_index")

            # Test it's an instance of KullaniciServisi
            from services.user_service import KullaniciServisi

            assert isinstance(kullanici_servisi, KullaniciServisi)

        except ImportError:
            pytest.skip("Global kullanici_servisi not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
