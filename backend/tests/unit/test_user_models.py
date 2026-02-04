"""
Unit Tests for User Pydantic Models
NO MOCKS - Pure validation and data model testing

Coverage target: 100%
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from models.user import KullaniciBase, KullaniciOlustur, Kullanici, OgrenciProfili
from models.enums import KullaniciRolu, SinavTipi, OgrenmeStili


class TestKullaniciBase:
    """Test KullaniciBase model"""

    def test_kullanici_base_valid(self):
        """Test creating valid base user"""
        user = KullaniciBase(
            email="test@example.com",
            ad_soyad="Ahmet Yılmaz",
            telefon="05551234567",
            aktif=True,
        )

        assert user.email == "test@example.com"
        assert user.ad_soyad == "Ahmet Yılmaz"
        assert user.telefon == "05551234567"
        assert user.aktif is True

    def test_kullanici_base_minimal(self):
        """Test base user with minimal fields"""
        user = KullaniciBase(email="minimal@test.com", ad_soyad="Test User")

        assert user.email == "minimal@test.com"
        assert user.ad_soyad == "Test User"
        assert user.telefon is None
        assert user.aktif is True  # Default value

    def test_kullanici_base_invalid_email(self):
        """Test invalid email raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            KullaniciBase(email="invalid-email", ad_soyad="Test User")

        errors = exc_info.value.errors()
        assert any(e["type"] == "value_error" for e in errors)

    def test_kullanici_base_short_name(self):
        """Test name too short raises error"""
        with pytest.raises(ValidationError) as exc_info:
            KullaniciBase(email="test@example.com", ad_soyad="A")  # Too short (min 2)

        errors = exc_info.value.errors()
        assert any("min_length" in str(e) for e in errors)

    def test_kullanici_base_long_name(self):
        """Test name too long raises error"""
        with pytest.raises(ValidationError):
            KullaniciBase(
                email="test@example.com", ad_soyad="A" * 101  # Too long (max 100)
            )

    @pytest.mark.parametrize(
        "email",
        [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.com",
            "user123@test-domain.com",
        ],
    )
    def test_kullanici_base_valid_emails(self, email):
        """Test various valid email formats"""
        user = KullaniciBase(email=email, ad_soyad="Test User")
        assert user.email == email

    @pytest.mark.parametrize(
        "invalid_email",
        ["notanemail", "@example.com", "user@", "user @example.com", "user@.com"],
    )
    def test_kullanici_base_invalid_emails(self, invalid_email):
        """Test various invalid emails"""
        with pytest.raises(ValidationError):
            KullaniciBase(email=invalid_email, ad_soyad="Test")


class TestPasswordValidation:
    """Test strong password validation (SECURITY FIX)"""

    def test_password_valid_strong(self):
        """Test creating user with strong password"""
        user = KullaniciOlustur(
            email="test@example.com",
            ad_soyad="Test User",
            sifre="StrongP@ssw0rd",
            rol=KullaniciRolu.OGRENCI,
        )

        assert user.sifre == "StrongP@ssw0rd"

    def test_password_too_short(self):
        """Test password too short (min 8 chars)"""
        with pytest.raises(ValidationError) as exc_info:
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                sifre="Short1!",  # Only 7 chars
                rol=KullaniciRolu.OGRENCI,
            )

        errors = exc_info.value.errors()
        # Pydantic v2: error message is in 'msg' or 'ctx.error'
        error_msg = errors[0].get("msg") or str(
            errors[0].get("ctx", {}).get("error", "")
        )
        # Accept both Turkish and English messages
        assert ("8 karakter" in error_msg) or ("at least 8 characters" in error_msg)

    def test_password_too_long(self):
        """Test password too long (max 128 chars)"""
        long_password = "A" * 129 + "a1!"

        with pytest.raises(ValidationError) as exc_info:
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                sifre=long_password,
                rol=KullaniciRolu.OGRENCI,
            )

        errors = exc_info.value.errors()
        error_msg = errors[0].get("msg") or str(
            errors[0].get("ctx", {}).get("error", "")
        )
        # Accept both Turkish and English messages
        assert ("128 karakter" in error_msg) or ("at most 128 characters" in error_msg)

    def test_password_no_uppercase(self):
        """Test password without uppercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                sifre="weakpass123!",  # No uppercase
                rol=KullaniciRolu.OGRENCI,
            )

        errors = exc_info.value.errors()
        error_msg = errors[0].get("msg") or str(
            errors[0].get("ctx", {}).get("error", "")
        )
        assert "büyük harf" in error_msg

    def test_password_no_lowercase(self):
        """Test password without lowercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                sifre="WEAKPASS123!",  # No lowercase
                rol=KullaniciRolu.OGRENCI,
            )

        errors = exc_info.value.errors()
        error_msg = errors[0].get("msg") or str(
            errors[0].get("ctx", {}).get("error", "")
        )
        assert "küçük harf" in error_msg

    def test_password_no_digit(self):
        """Test password without digit"""
        with pytest.raises(ValidationError) as exc_info:
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                sifre="WeakPassword!",  # No digit
                rol=KullaniciRolu.OGRENCI,
            )

        errors = exc_info.value.errors()
        error_msg = errors[0].get("msg") or str(
            errors[0].get("ctx", {}).get("error", "")
        )
        assert "rakam" in error_msg

    def test_password_no_special_char(self):
        """Test password without special character"""
        with pytest.raises(ValidationError) as exc_info:
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                sifre="WeakPassword123",  # No special char
                rol=KullaniciRolu.OGRENCI,
            )

        errors = exc_info.value.errors()
        error_msg = errors[0].get("msg") or str(
            errors[0].get("ctx", {}).get("error", "")
        )
        assert "özel karakter" in error_msg

    @pytest.mark.parametrize(
        "weak_password",
        [
            "password",
            "password123",
            "12345678",
            "qwerty123",
            "admin123",
            "welcome123",
            "password1",
            "test1234",
        ],
    )
    def test_password_common_weak(self, weak_password):
        """Test common weak passwords are rejected"""
        # Test base weak password with minimum complexity added
        # Validator removes special chars and checks base password

        # Try to create user with weak password base + complexity chars
        test_password = weak_password.capitalize() + "1!"

        # Check if base password (without special chars and digits after weak part) is caught
        import re

        base = re.sub(
            r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', "", test_password
        ).lower()

        # If base matches weak password, should be rejected
        if weak_password in base:
            with pytest.raises(ValidationError) as exc_info:
                KullaniciOlustur(
                    email="test@example.com",
                    ad_soyad="Test User",
                    sifre=test_password,
                    rol=KullaniciRolu.OGRENCI,
                )
            # Verify it's caught
            errors = exc_info.value.errors()
            error_msg = errors[0].get("msg") or str(
                errors[0].get("ctx", {}).get("error", "")
            )
            assert ("yaygın" in error_msg) or ("common" in error_msg)
        else:
            # If transformed password no longer contains weak base, it may pass - that's ok
            pass

    @pytest.mark.parametrize(
        "strong_password",
        [
            "MyP@ssw0rd2024",
            "Secur3P@ss!",
            "C0mpl3x&Strong",
            "T3st!ng#2024",
            "V@lid_P@ssw0rd1",
        ],
    )
    def test_password_strong_variations(self, strong_password):
        """Test various strong passwords"""
        user = KullaniciOlustur(
            email="test@example.com",
            ad_soyad="Test User",
            sifre=strong_password,
            rol=KullaniciRolu.OGRENCI,
        )

        assert user.sifre == strong_password


class TestKullaniciOlustur:
    """Test KullaniciOlustur model"""

    def test_kullanici_olustur_valid(self):
        """Test creating valid new user"""
        user = KullaniciOlustur(
            email="newuser@example.com",
            ad_soyad="Yeni Kullanıcı",
            telefon="05559876543",
            aktif=True,
            sifre="ValidP@ss123",
            rol=KullaniciRolu.OGRENCI,
        )

        assert user.email == "newuser@example.com"
        assert user.ad_soyad == "Yeni Kullanıcı"
        assert user.sifre == "ValidP@ss123"
        assert user.rol == KullaniciRolu.OGRENCI

    @pytest.mark.parametrize(
        "rol",
        [
            KullaniciRolu.OGRENCI,
            KullaniciRolu.OGRETMEN,
            KullaniciRolu.VELI,
            KullaniciRolu.ADMIN,
            KullaniciRolu.SUPER_ADMIN,
        ],
    )
    def test_kullanici_olustur_all_roles(self, rol):
        """Test creating user with each role"""
        user = KullaniciOlustur(
            email="test@example.com",
            ad_soyad="Test User",
            sifre="ValidP@ss123",
            rol=rol,
        )

        assert user.rol == rol

    def test_kullanici_olustur_missing_password(self):
        """Test creating user without password fails"""
        with pytest.raises(ValidationError):
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                rol=KullaniciRolu.OGRENCI
                # Missing sifre
            )

    def test_kullanici_olustur_missing_role(self):
        """Test creating user without role fails"""
        with pytest.raises(ValidationError):
            KullaniciOlustur(
                email="test@example.com",
                ad_soyad="Test User",
                sifre="ValidP@ss123"
                # Missing rol
            )


class TestKullanici:
    """Test full Kullanici model"""

    def test_kullanici_valid(self):
        """Test creating full user model"""
        now = datetime.now()
        user = Kullanici(
            kullanici_id="user-12345",
            email="user@example.com",
            ad_soyad="Tam Kullanıcı",
            telefon="05551112233",
            aktif=True,
            rol=KullaniciRolu.OGRETMEN,
            olusturma_tarihi=now,
            son_giris=now,
        )

        assert user.kullanici_id == "user-12345"
        assert user.email == "user@example.com"
        assert user.rol == KullaniciRolu.OGRETMEN
        assert user.olusturma_tarihi == now
        assert user.son_giris == now

    def test_kullanici_without_login(self):
        """Test user without last login"""
        user = Kullanici(
            kullanici_id="user-001",
            email="new@example.com",
            ad_soyad="New User",
            rol=KullaniciRolu.OGRENCI,
            olusturma_tarihi=datetime.now(),
        )

        assert user.son_giris is None

    def test_kullanici_default_creation_time(self):
        """Test user gets default creation time"""
        user = Kullanici(
            kullanici_id="user-002",
            email="test@example.com",
            ad_soyad="Test",
            rol=KullaniciRolu.VELI,
        )

        assert isinstance(user.olusturma_tarihi, datetime)


class TestOgrenciProfili:
    """Test OgrenciProfili model"""

    def test_ogrenci_profili_valid(self):
        """Test creating valid student profile"""
        profil = OgrenciProfili(
            ogrenci_id="ogrenci-123",
            kullanici_id="user-123",
            sinif_seviyesi=11,
            okul_adi="Atatürk Lisesi",
            hedef_sinav=SinavTipi.TYT,
            hedef_universiteler=["Boğaziçi", "ODTÜ", "İTÜ"],
            ogrenme_stili=OgrenmeStili.GORSEL,
            guclu_alanlar=["matematik", "fizik"],
        )

        assert profil.ogrenci_id == "ogrenci-123"
        assert profil.sinif_seviyesi == 11
        assert profil.hedef_sinav == SinavTipi.TYT
        assert len(profil.hedef_universiteler) == 3
        assert profil.ogrenme_stili == OgrenmeStili.GORSEL

    @pytest.mark.parametrize("sinif", [9, 10, 11, 12])
    def test_ogrenci_profili_valid_grades(self, sinif):
        """Test all valid grade levels (9-12)"""
        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=sinif,
            hedef_sinav=SinavTipi.TYT,
        )

        assert profil.sinif_seviyesi == sinif

    @pytest.mark.parametrize("invalid_sinif", [8, 13, 0, -1, 100])
    def test_ogrenci_profili_invalid_grades(self, invalid_sinif):
        """Test invalid grade levels"""
        with pytest.raises(ValidationError):
            OgrenciProfili(
                ogrenci_id="test",
                kullanici_id="user",
                sinif_seviyesi=invalid_sinif,
                hedef_sinav=SinavTipi.TYT,
            )

    @pytest.mark.parametrize(
        "hedef_sinav", [SinavTipi.TYT, SinavTipi.AYT, SinavTipi.YDT]
    )
    def test_ogrenci_profili_exam_types(self, hedef_sinav):
        """Test all target exam types"""
        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=12,
            hedef_sinav=hedef_sinav,
        )

        assert profil.hedef_sinav == hedef_sinav

    def test_ogrenci_profili_minimal(self):
        """Test student profile with minimal fields"""
        profil = OgrenciProfili(
            ogrenci_id="min-123",
            kullanici_id="user-123",
            sinif_seviyesi=9,
            hedef_sinav=SinavTipi.TYT,
        )

        assert profil.okul_adi is None
        assert profil.ogrenme_stili is None
        assert profil.hedef_universiteler == []
        assert profil.guclu_alanlar == []

    def test_ogrenci_profili_okul_adi_max_length(self):
        """Test school name respects max length"""
        long_name = "A" * 200  # Exactly 200 chars (max)

        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=10,
            okul_adi=long_name,
            hedef_sinav=SinavTipi.TYT,
        )

        assert len(profil.okul_adi) == 200

    def test_ogrenci_profili_okul_adi_too_long(self):
        """Test school name too long raises error"""
        with pytest.raises(ValidationError):
            OgrenciProfili(
                ogrenci_id="test",
                kullanici_id="user",
                sinif_seviyesi=10,
                okul_adi="A" * 201,  # Too long
                hedef_sinav=SinavTipi.TYT,
            )

    def test_ogrenci_profili_multiple_universities(self):
        """Test student with multiple target universities"""
        universities = ["Boğaziçi", "ODTÜ", "İTÜ", "Hacettepe", "Bilkent"]

        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=12,
            hedef_sinav=SinavTipi.AYT,
            hedef_universiteler=universities,
        )

        assert len(profil.hedef_universiteler) == 5
        assert "ODTÜ" in profil.hedef_universiteler

    def test_ogrenci_profili_guclu_alanlar(self):
        """Test student strong subjects"""
        subjects = ["matematik", "fizik", "kimya", "biyoloji"]

        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=11,
            hedef_sinav=SinavTipi.TYT,
            guclu_alanlar=subjects,
        )

        assert len(profil.guclu_alanlar) == 4
        assert "matematik" in profil.guclu_alanlar


class TestModelSerialization:
    """Test model serialization"""

    def test_kullanici_to_dict(self):
        """Test converting user to dict"""
        user = Kullanici(
            kullanici_id="test-123",
            email="test@example.com",
            ad_soyad="Test User",
            rol=KullaniciRolu.OGRENCI,
            olusturma_tarihi=datetime.now(),
        )

        data = user.model_dump()
        assert isinstance(data, dict)
        assert data["email"] == "test@example.com"
        assert data["rol"] == KullaniciRolu.OGRENCI

    def test_ogrenci_profili_to_dict(self):
        """Test converting student profile to dict"""
        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=10,
            hedef_sinav=SinavTipi.TYT,
            hedef_universiteler=["ODTÜ"],
        )

        data = profil.model_dump()
        assert isinstance(data, dict)
        assert data["sinif_seviyesi"] == 10
        assert data["hedef_sinav"] == SinavTipi.TYT
        assert isinstance(data["hedef_universiteler"], list)
