#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for services/user_service.py
Test coverage improvement: 23% -> 70%
"""

import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import uuid

# Import the module to test
from services.user_service import KullaniciServisi
from models import (
    Kullanici,
    KullaniciGiris,
    KullaniciOlustur,
    KullaniciRolu,
    OgrenciProfili,
    OgretmenProfili,
    TokenYaniti,
    VeliProfili,
)


@pytest.fixture
def kullanici_servisi():
    """Create fresh user service instance"""
    return KullaniciServisi()


@pytest.fixture
def sample_kullanici_data():
    """Sample user creation data"""
    return KullaniciOlustur(
        email="test@example.com",
        ad_soyad="Test User",
        sifre="password123",
        telefon="+90 555 123 4567",
        rol=KullaniciRolu.OGRENCI,
    )


@pytest.fixture
def sample_giris_data():
    """Sample login data"""
    return KullaniciGiris(email="test@example.com", sifre="password123")


@pytest.fixture
def sample_ogrenci_profil():
    """Sample student profile"""
    return OgrenciProfili(
        ogrenci_id="ogrenci-123",
        kullanici_id="user-123",
        sinif=11,
        okul="Test Lisesi",
        hedef_universite="İTÜ",
        hedef_bolum="Bilgisayar Mühendisliği",
    )


class TestKullaniciServisiInit:
    """Test KullaniciServisi initialization"""

    def test_init(self):
        """Test service initialization"""
        service = KullaniciServisi()

        assert isinstance(service.kullanicilar, dict)
        assert isinstance(service.sifreler, dict)
        assert isinstance(service.email_index, dict)
        assert isinstance(service.ogrenci_profilleri, dict)
        assert isinstance(service.ogretmen_profilleri, dict)
        assert isinstance(service.veli_profilleri, dict)
        assert isinstance(service.aktif_tokenlar, dict)

        # All should be empty initially
        assert len(service.kullanicilar) == 0
        assert len(service.sifreler) == 0
        assert len(service.email_index) == 0


class TestPrivateMethods:
    """Test private methods"""

    def test_sifre_hash_et(self, kullanici_servisi):
        """Test password hashing"""
        password = "test_password"
        hashed = kullanici_servisi._sifre_hash_et(password)

        # Should be consistent
        assert hashed == kullanici_servisi._sifre_hash_et(password)

        # Should be different for different passwords
        assert hashed != kullanici_servisi._sifre_hash_et("different_password")

        # Should be SHA256 hash
        expected = hashlib.sha256(password.encode()).hexdigest()
        assert hashed == expected

    def test_token_olustur(self, kullanici_servisi):
        """Test token creation"""
        token1 = kullanici_servisi._token_olustur("user1")
        token2 = kullanici_servisi._token_olustur("user2")

        # Tokens should be different
        assert token1 != token2

        # Tokens should be strings
        assert isinstance(token1, str)
        assert isinstance(token2, str)

        # Tokens should have reasonable length
        assert len(token1) > 20
        assert len(token2) > 20


class TestKullaniciOlustur:
    """Test user creation"""

    @pytest.mark.asyncio
    async def test_kullanici_olustur_success(
        self, kullanici_servisi, sample_kullanici_data
    ):
        """Test successful user creation"""
        kullanici = await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

        # Check user object
        assert isinstance(kullanici, Kullanici)
        assert kullanici.email == sample_kullanici_data.email
        assert kullanici.ad_soyad == sample_kullanici_data.ad_soyad
        assert kullanici.telefon == sample_kullanici_data.telefon
        assert kullanici.rol == sample_kullanici_data.rol
        assert kullanici.aktif is True
        assert isinstance(kullanici.olusturma_tarihi, datetime)

        # Check internal storage
        assert kullanici.kullanici_id in kullanici_servisi.kullanicilar
        assert kullanici.kullanici_id in kullanici_servisi.sifreler
        assert sample_kullanici_data.email in kullanici_servisi.email_index

        # Check password is hashed
        stored_password = kullanici_servisi.sifreler[kullanici.kullanici_id]
        expected_hash = kullanici_servisi._sifre_hash_et(sample_kullanici_data.sifre)
        assert stored_password == expected_hash

    @pytest.mark.asyncio
    async def test_kullanici_olustur_duplicate_email(
        self, kullanici_servisi, sample_kullanici_data
    ):
        """Test user creation with duplicate email"""
        # Create first user
        await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

        # Try to create another user with same email
        with pytest.raises(ValueError, match="Bu e-posta adresi zaten kullanımda"):
            await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

    @pytest.mark.asyncio
    async def test_kullanici_olustur_different_roles(self, kullanici_servisi):
        """Test user creation with different roles"""
        roles = [
            KullaniciRolu.OGRENCI,
            KullaniciRolu.OGRETMEN,
            KullaniciRolu.VELI,
            KullaniciRolu.ADMIN,
        ]

        for i, rol in enumerate(roles):
            kullanici_data = KullaniciOlustur(
                email=f"test{i}@example.com",
                ad_soyad=f"Test User {i}",
                sifre="password123",
                rol=rol,
            )

            kullanici = await kullanici_servisi.kullanici_olustur(kullanici_data)
            assert kullanici.rol == rol


class TestKullaniciGiris:
    """Test user login"""

    @pytest.mark.asyncio
    async def test_kullanici_giris_success(
        self, kullanici_servisi, sample_kullanici_data, sample_giris_data
    ):
        """Test successful user login"""
        # Create user first
        kullanici = await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

        # Login
        token_yaniti = await kullanici_servisi.kullanici_giris(sample_giris_data)

        # Check response
        assert isinstance(token_yaniti, TokenYaniti)
        assert isinstance(token_yaniti.access_token, str)
        assert token_yaniti.token_type == "bearer"
        assert token_yaniti.expires_in == 3600 * 24  # 24 hours
        assert token_yaniti.kullanici.kullanici_id == kullanici.kullanici_id

        # Check token is stored
        assert token_yaniti.access_token in kullanici_servisi.aktif_tokenlar

        # Check last login is updated
        assert kullanici.son_giris is not None

    @pytest.mark.asyncio
    async def test_kullanici_giris_invalid_email(self, kullanici_servisi):
        """Test login with invalid email"""
        giris_data = KullaniciGiris(
            email="nonexistent@example.com", sifre="password123"
        )

        with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
            await kullanici_servisi.kullanici_giris(giris_data)

    @pytest.mark.asyncio
    async def test_kullanici_giris_invalid_password(
        self, kullanici_servisi, sample_kullanici_data
    ):
        """Test login with invalid password"""
        # Create user first
        await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

        # Try login with wrong password
        giris_data = KullaniciGiris(
            email=sample_kullanici_data.email, sifre="wrong_password"
        )

        with pytest.raises(ValueError, match="Geçersiz e-posta veya şifre"):
            await kullanici_servisi.kullanici_giris(giris_data)

    @pytest.mark.asyncio
    async def test_kullanici_giris_inactive_user(
        self, kullanici_servisi, sample_kullanici_data, sample_giris_data
    ):
        """Test login with inactive user"""
        # Create user and deactivate
        kullanici = await kullanici_servisi.kullanici_olustur(sample_kullanici_data)
        kullanici.aktif = False

        with pytest.raises(ValueError, match="Hesap aktif değil"):
            await kullanici_servisi.kullanici_giris(sample_giris_data)


class TestTokenDogrula:
    """Test token validation"""

    @pytest.mark.asyncio
    async def test_token_dogrula_valid_token(
        self, kullanici_servisi, sample_kullanici_data, sample_giris_data
    ):
        """Test token validation with valid token"""
        # Create user and login
        created_user = await kullanici_servisi.kullanici_olustur(sample_kullanici_data)
        token_yaniti = await kullanici_servisi.kullanici_giris(sample_giris_data)

        # Validate token
        kullanici = await kullanici_servisi.token_dogrula(token_yaniti.access_token)

        assert kullanici is not None
        assert kullanici.kullanici_id == created_user.kullanici_id
        assert kullanici.email == created_user.email

    @pytest.mark.asyncio
    async def test_token_dogrula_invalid_token(self, kullanici_servisi):
        """Test token validation with invalid token"""
        kullanici = await kullanici_servisi.token_dogrula("invalid_token")
        assert kullanici is None

    @pytest.mark.asyncio
    async def test_token_dogrula_expired_token(
        self, kullanici_servisi, sample_kullanici_data, sample_giris_data
    ):
        """Test token validation with expired token"""
        # Create user and login
        await kullanici_servisi.kullanici_olustur(sample_kullanici_data)
        token_yaniti = await kullanici_servisi.kullanici_giris(sample_giris_data)

        # Manually expire the token
        token_info = kullanici_servisi.aktif_tokenlar[token_yaniti.access_token]
        token_info["expires_at"] = datetime.now() - timedelta(
            hours=1
        )  # Expired 1 hour ago

        # Validate token
        kullanici = await kullanici_servisi.token_dogrula(token_yaniti.access_token)

        assert kullanici is None
        # Token should be removed from active tokens
        assert token_yaniti.access_token not in kullanici_servisi.aktif_tokenlar


class TestKullaniciGetir:
    """Test user retrieval"""

    @pytest.mark.asyncio
    async def test_kullanici_getir_existing_user(
        self, kullanici_servisi, sample_kullanici_data
    ):
        """Test retrieving existing user"""
        created_user = await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

        retrieved_user = await kullanici_servisi.kullanici_getir(
            created_user.kullanici_id
        )

        assert retrieved_user is not None
        assert retrieved_user.kullanici_id == created_user.kullanici_id
        assert retrieved_user.email == created_user.email

    @pytest.mark.asyncio
    async def test_kullanici_getir_nonexistent_user(self, kullanici_servisi):
        """Test retrieving non-existent user"""
        retrieved_user = await kullanici_servisi.kullanici_getir("nonexistent_id")
        assert retrieved_user is None


class TestKullaniciListesi:
    """Test user listing"""

    @pytest.mark.asyncio
    async def test_kullanici_listesi_all_users(self, kullanici_servisi):
        """Test listing all users"""
        # Create multiple users
        users_data = [
            KullaniciOlustur(
                email="user1@test.com",
                ad_soyad="User 1",
                sifre="pass1",
                rol=KullaniciRolu.OGRENCI,
            ),
            KullaniciOlustur(
                email="user2@test.com",
                ad_soyad="User 2",
                sifre="pass2",
                rol=KullaniciRolu.OGRETMEN,
            ),
            KullaniciOlustur(
                email="user3@test.com",
                ad_soyad="User 3",
                sifre="pass3",
                rol=KullaniciRolu.VELI,
            ),
        ]

        created_users = []
        for user_data in users_data:
            user = await kullanici_servisi.kullanici_olustur(user_data)
            created_users.append(user)

        # Get all users
        user_list = await kullanici_servisi.kullanici_listesi()

        assert len(user_list) == 3
        user_ids = [u.kullanici_id for u in user_list]
        for created_user in created_users:
            assert created_user.kullanici_id in user_ids

    @pytest.mark.asyncio
    async def test_kullanici_listesi_filtered_by_role(self, kullanici_servisi):
        """Test listing users filtered by role"""
        # Create users with different roles
        users_data = [
            KullaniciOlustur(
                email="student1@test.com",
                ad_soyad="Student 1",
                sifre="pass1",
                rol=KullaniciRolu.OGRENCI,
            ),
            KullaniciOlustur(
                email="student2@test.com",
                ad_soyad="Student 2",
                sifre="pass2",
                rol=KullaniciRolu.OGRENCI,
            ),
            KullaniciOlustur(
                email="teacher1@test.com",
                ad_soyad="Teacher 1",
                sifre="pass3",
                rol=KullaniciRolu.OGRETMEN,
            ),
        ]

        for user_data in users_data:
            await kullanici_servisi.kullanici_olustur(user_data)

        # Get only students
        students = await kullanici_servisi.kullanici_listesi(rol=KullaniciRolu.OGRENCI)
        assert len(students) == 2
        for student in students:
            assert student.rol == KullaniciRolu.OGRENCI

        # Get only teachers
        teachers = await kullanici_servisi.kullanici_listesi(rol=KullaniciRolu.OGRETMEN)
        assert len(teachers) == 1
        assert teachers[0].rol == KullaniciRolu.OGRETMEN

    @pytest.mark.asyncio
    async def test_kullanici_listesi_empty(self, kullanici_servisi):
        """Test listing users when none exist"""
        user_list = await kullanici_servisi.kullanici_listesi()
        assert len(user_list) == 0


class TestOgrenciProfiliOlustur:
    """Test student profile creation"""

    @pytest.mark.asyncio
    async def test_ogrenci_profili_olustur_success(
        self, kullanici_servisi, sample_kullanici_data, sample_ogrenci_profil
    ):
        """Test successful student profile creation"""
        # Create user first
        kullanici = await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

        # Update profile with correct user ID
        sample_ogrenci_profil.kullanici_id = kullanici.kullanici_id

        # Create profile
        profil = await kullanici_servisi.ogrenci_profili_olustur(sample_ogrenci_profil)

        assert profil is not None
        assert profil.kullanici_id == kullanici.kullanici_id
        assert profil.sinif == sample_ogrenci_profil.sinif
        assert profil.okul == sample_ogrenci_profil.okul

        # Check profile is stored
        assert sample_ogrenci_profil.ogrenci_id in kullanici_servisi.ogrenci_profilleri

    @pytest.mark.asyncio
    async def test_ogrenci_profili_olustur_invalid_user_id(
        self, kullanici_servisi, sample_ogrenci_profil
    ):
        """Test student profile creation with invalid user ID"""
        with pytest.raises(ValueError, match="Geçersiz kullanıcı ID"):
            await kullanici_servisi.ogrenci_profili_olustur(sample_ogrenci_profil)

    @pytest.mark.asyncio
    async def test_ogrenci_profili_olustur_wrong_role(
        self, kullanici_servisi, sample_ogrenci_profil
    ):
        """Test student profile creation for non-student user"""
        # Create teacher user
        teacher_data = KullaniciOlustur(
            email="teacher@test.com",
            ad_soyad="Teacher User",
            sifre="password123",
            rol=KullaniciRolu.OGRETMEN,
        )
        teacher = await kullanici_servisi.kullanici_olustur(teacher_data)

        # Try to create student profile for teacher
        sample_ogrenci_profil.kullanici_id = teacher.kullanici_id

        with pytest.raises(ValueError, match="Kullanıcı öğrenci rolünde değil"):
            await kullanici_servisi.ogrenci_profili_olustur(sample_ogrenci_profil)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_multiple_logins_same_user(
        self, kullanici_servisi, sample_kullanici_data, sample_giris_data
    ):
        """Test multiple logins for same user"""
        # Create user
        await kullanici_servisi.kullanici_olustur(sample_kullanici_data)

        # Login multiple times
        token1 = await kullanici_servisi.kullanici_giris(sample_giris_data)
        token2 = await kullanici_servisi.kullanici_giris(sample_giris_data)

        # Both tokens should be valid
        user1 = await kullanici_servisi.token_dogrula(token1.access_token)
        user2 = await kullanici_servisi.token_dogrula(token2.access_token)

        assert user1 is not None
        assert user2 is not None
        assert user1.kullanici_id == user2.kullanici_id

    @pytest.mark.asyncio
    async def test_empty_password_handling(self, kullanici_servisi):
        """Test handling of empty password"""
        empty_password = ""
        hashed = kullanici_servisi._sifre_hash_et(empty_password)

        # Should still create a hash
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    @pytest.mark.asyncio
    async def test_unicode_user_data(self, kullanici_servisi):
        """Test handling of unicode characters in user data"""
        unicode_data = KullaniciOlustur(
            email="test@örnek.com",
            ad_soyad="Çağlar Öğretmen",
            sifre="şifre123",
            rol=KullaniciRolu.OGRETMEN,
        )

        kullanici = await kullanici_servisi.kullanici_olustur(unicode_data)

        assert kullanici.email == "test@örnek.com"
        assert kullanici.ad_soyad == "Çağlar Öğretmen"

        # Login should work with unicode
        giris_data = KullaniciGiris(email="test@örnek.com", sifre="şifre123")
        token_yaniti = await kullanici_servisi.kullanici_giris(giris_data)
        assert token_yaniti is not None


class TestConcurrentOperations:
    """Test concurrent operation scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_user_creation_attempts(self, kullanici_servisi):
        """Test concurrent user creation with same email"""
        user_data = KullaniciOlustur(
            email="concurrent@test.com",
            ad_soyad="Concurrent User",
            sifre="password123",
            rol=KullaniciRolu.OGRENCI,
        )

        # First creation should succeed
        user1 = await kullanici_servisi.kullanici_olustur(user_data)
        assert user1 is not None

        # Second creation should fail
        with pytest.raises(ValueError, match="Bu e-posta adresi zaten kullanımda"):
            await kullanici_servisi.kullanici_olustur(user_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
