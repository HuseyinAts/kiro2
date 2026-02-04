"""
Comprehensive unit tests for User models
Testing user management, authentication, and profile models
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from models.user import (
    KullaniciBase,
    KullaniciOlustur,
    Kullanici,
    OgrenciProfili,
    OgretmenProfili,
    VeliProfili,
    KullaniciGiris,
    TokenYaniti,
)
from models.enums import KullaniciRolu, OgrenmeStili, SinavTipi


class TestKullaniciBase:
    """Test base user model"""

    def test_valid_kullanici_base(self):
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
        """Test base user with minimal required fields"""
        user = KullaniciBase(email="minimal@test.com", ad_soyad="Test User")

        assert user.email == "minimal@test.com"
        assert user.ad_soyad == "Test User"
        assert user.aktif is True  # Default value

    def test_invalid_email(self):
        """Test validation fails for invalid email"""
        with pytest.raises(ValidationError):
            KullaniciBase(email="not-an-email", ad_soyad="Test User")

    def test_ad_soyad_too_short(self):
        """Test validation fails for name too short"""
        with pytest.raises(ValidationError):
            KullaniciBase(
                email="test@example.com", ad_soyad="A"  # Less than 2 characters
            )

    def test_ad_soyad_too_long(self):
        """Test validation fails for name too long"""
        with pytest.raises(ValidationError):
            KullaniciBase(
                email="test@example.com", ad_soyad="A" * 101  # More than 100 characters
            )


class TestKullaniciOlustur:
    """Test user creation model with password validation"""

    def test_valid_strong_password(self):
        """Test creating user with strong password"""
        user = KullaniciOlustur(
            email="strong@test.com",
            ad_soyad="Strong User",
            sifre="StrongP@ss123",
            rol=KullaniciRolu.OGRENCI,
        )

        assert user.sifre == "StrongP@ss123"
        assert user.rol == KullaniciRolu.OGRENCI

    def test_password_too_short(self):
        """Test password validation fails for short password"""
        with pytest.raises(ValidationError):
            KullaniciOlustur(
                email="test@test.com",
                ad_soyad="Test User",
                sifre="Short1!",  # Only 7 characters
                rol=KullaniciRolu.OGRENCI,
            )

    def test_password_no_uppercase(self):
        """Test password validation fails without uppercase letter"""
        with pytest.raises(ValidationError, match="büyük harf"):
            KullaniciOlustur(
                email="test@test.com",
                ad_soyad="Test User",
                sifre="nouppercase123!",
                rol=KullaniciRolu.OGRENCI,
            )

    def test_password_no_lowercase(self):
        """Test password validation fails without lowercase letter"""
        with pytest.raises(ValidationError, match="küçük harf"):
            KullaniciOlustur(
                email="test@test.com",
                ad_soyad="Test User",
                sifre="NOLOWERCASE123!",
                rol=KullaniciRolu.OGRENCI,
            )

    def test_password_no_digit(self):
        """Test password validation fails without digit"""
        with pytest.raises(ValidationError, match="rakam"):
            KullaniciOlustur(
                email="test@test.com",
                ad_soyad="Test User",
                sifre="NoDigit@Pass",
                rol=KullaniciRolu.OGRENCI,
            )

    def test_password_no_special_char(self):
        """Test password validation fails without special character"""
        with pytest.raises(ValidationError, match="özel karakter"):
            KullaniciOlustur(
                email="test@test.com",
                ad_soyad="Test User",
                sifre="NoSpecial123",
                rol=KullaniciRolu.OGRENCI,
            )

    @pytest.mark.parametrize(
        "weak_password",
        [
            "Password123!",  # Contains 'password'
            "Admin123!@#",  # Contains 'admin'
            "Welcome123!",  # Contains 'welcome'
            "Test1234!@#",  # Contains 'test'
        ],
    )
    def test_common_weak_passwords(self, weak_password):
        """Test validation fails for common weak passwords"""
        with pytest.raises(ValidationError, match="yaygın"):
            KullaniciOlustur(
                email="test@test.com",
                ad_soyad="Test User",
                sifre=weak_password,
                rol=KullaniciRolu.OGRENCI,
            )

    def test_password_too_long(self):
        """Test password validation fails for too long password"""
        with pytest.raises(ValidationError):
            KullaniciOlustur(
                email="test@test.com",
                ad_soyad="Test User",
                sifre="A" * 129 + "a1!",  # More than 128 characters
                rol=KullaniciRolu.OGRENCI,
            )

    @pytest.mark.parametrize(
        "special_char",
        [
            "!",
            "@",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            ",",
            ".",
            "?",
            ":",
            "{",
            "}",
            "|",
            "<",
            ">",
            "_",
            "-",
            "+",
            "=",
            "[",
            "]",
            "\\",
            "/",
            "~",
            "`",
        ],
    )
    def test_various_special_characters(self, special_char):
        """Test various special characters are accepted"""
        password = f"Valid{special_char}Pass123"
        user = KullaniciOlustur(
            email="test@test.com",
            ad_soyad="Test User",
            sifre=password,
            rol=KullaniciRolu.OGRENCI,
        )
        assert user.sifre == password

    def test_all_user_roles(self):
        """Test creating users with different roles"""
        for rol in [
            KullaniciRolu.OGRENCI,
            KullaniciRolu.OGRETMEN,
            KullaniciRolu.VELI,
            KullaniciRolu.ADMIN,
        ]:
            user = KullaniciOlustur(
                email=f"{rol}@test.com",
                ad_soyad=f"{rol} User",
                sifre="Valid@Pass123",
                rol=rol,
            )
            assert user.rol == rol


class TestKullanici:
    """Test full user model"""

    def test_complete_kullanici(self):
        """Test creating complete user"""
        user = Kullanici(
            kullanici_id="user123",
            email="complete@test.com",
            ad_soyad="Complete User",
            rol=KullaniciRolu.OGRENCI,
            telefon="05551234567",
            aktif=True,
            son_giris=datetime.now(),
        )

        assert user.kullanici_id == "user123"
        assert user.email == "complete@test.com"
        assert user.rol == KullaniciRolu.OGRENCI
        assert user.son_giris is not None

    def test_kullanici_minimal(self):
        """Test user with minimal fields"""
        user = Kullanici(
            kullanici_id="min123",
            email="min@test.com",
            ad_soyad="Min User",
            rol=KullaniciRolu.VELI,
        )

        assert user.kullanici_id == "min123"
        assert user.son_giris is None


class TestOgrenciProfili:
    """Test student profile model"""

    def test_complete_ogrenci_profili(self):
        """Test creating complete student profile"""
        profil = OgrenciProfili(
            ogrenci_id="ogr123",
            kullanici_id="user123",
            sinif_seviyesi=11,
            okul_adi="Atatürk Lisesi",
            hedef_sinav=SinavTipi.TYT,
            hedef_universiteler=["Boğaziçi", "ODTÜ", "İTÜ"],
            ogrenme_stili=OgrenmeStili.GORSEL,
            guclu_alanlar=["Matematik", "Fizik"],
            zayif_alanlar=["Tarih", "Coğrafya"],
            gunluk_calisma_hedefi=240,
            veli_onay=True,
            veli_kullanici_id="veli123",
        )

        assert profil.ogrenci_id == "ogr123"
        assert profil.sinif_seviyesi == 11
        assert profil.hedef_sinav == SinavTipi.TYT
        assert len(profil.hedef_universiteler) == 3
        assert profil.ogrenme_stili == OgrenmeStili.GORSEL
        assert profil.gunluk_calisma_hedefi == 240
        assert profil.veli_onay is True

    def test_ogrenci_minimal(self):
        """Test student profile with minimal fields"""
        profil = OgrenciProfili(
            ogrenci_id="min123",
            kullanici_id="user123",
            sinif_seviyesi=9,
            hedef_sinav=SinavTipi.TYT,
        )

        assert profil.ogrenci_id == "min123"
        assert profil.sinif_seviyesi == 9
        assert profil.veli_onay is False  # Default

    @pytest.mark.parametrize("sinif", [9, 10, 11, 12])
    def test_valid_sinif_seviyeleri(self, sinif):
        """Test valid grade levels"""
        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=sinif,
            hedef_sinav=SinavTipi.TYT,
        )
        assert profil.sinif_seviyesi == sinif

    @pytest.mark.parametrize("invalid_sinif", [8, 13, 0, -1, 15])
    def test_invalid_sinif_seviyeleri(self, invalid_sinif):
        """Test invalid grade levels"""
        with pytest.raises(ValidationError):
            OgrenciProfili(
                ogrenci_id="test",
                kullanici_id="user",
                sinif_seviyesi=invalid_sinif,
                hedef_sinav=SinavTipi.TYT,
            )

    @pytest.mark.parametrize("calisma_hedefi", [30, 240, 600])
    def test_valid_calisma_hedefi(self, calisma_hedefi):
        """Test valid daily study goals"""
        profil = OgrenciProfili(
            ogrenci_id="test",
            kullanici_id="user",
            sinif_seviyesi=10,
            hedef_sinav=SinavTipi.TYT,
            gunluk_calisma_hedefi=calisma_hedefi,
        )
        assert profil.gunluk_calisma_hedefi == calisma_hedefi

    @pytest.mark.parametrize("invalid_hedef", [29, 601, 0, -10, 1000])
    def test_invalid_calisma_hedefi(self, invalid_hedef):
        """Test invalid daily study goals"""
        with pytest.raises(ValidationError):
            OgrenciProfili(
                ogrenci_id="test",
                kullanici_id="user",
                sinif_seviyesi=10,
                hedef_sinav=SinavTipi.TYT,
                gunluk_calisma_hedefi=invalid_hedef,
            )

    def test_all_sinav_tipleri(self):
        """Test all exam types"""
        for sinav_tip in [SinavTipi.TYT, SinavTipi.AYT, SinavTipi.YDT]:
            profil = OgrenciProfili(
                ogrenci_id="test",
                kullanici_id="user",
                sinif_seviyesi=12,
                hedef_sinav=sinav_tip,
            )
            assert profil.hedef_sinav == sinav_tip


class TestOgretmenProfili:
    """Test teacher profile model"""

    def test_complete_ogretmen_profili(self):
        """Test creating complete teacher profile"""
        profil = OgretmenProfili(
            ogretmen_id="ogt123",
            kullanici_id="user123",
            okul_adi="Atatürk Lisesi",
            brans="Matematik",
            deneyim_yili=15,
            sinif_listesi=["9A", "10B", "11C", "12D"],
        )

        assert profil.ogretmen_id == "ogt123"
        assert profil.okul_adi == "Atatürk Lisesi"
        assert profil.brans == "Matematik"
        assert profil.deneyim_yili == 15
        assert len(profil.sinif_listesi) == 4

    def test_ogretmen_minimal(self):
        """Test teacher profile with minimal fields"""
        profil = OgretmenProfili(
            ogretmen_id="min123",
            kullanici_id="user123",
            okul_adi="Test Okulu",
            brans="Fizik",
        )

        assert profil.ogretmen_id == "min123"
        assert profil.deneyim_yili is None
        assert len(profil.sinif_listesi) == 0

    @pytest.mark.parametrize("deneyim", [0, 10, 25, 50])
    def test_valid_deneyim_yillari(self, deneyim):
        """Test valid experience years"""
        profil = OgretmenProfili(
            ogretmen_id="test",
            kullanici_id="user",
            okul_adi="Test",
            brans="Test",
            deneyim_yili=deneyim,
        )
        assert profil.deneyim_yili == deneyim

    @pytest.mark.parametrize("invalid_deneyim", [-1, 51, 100])
    def test_invalid_deneyim_yillari(self, invalid_deneyim):
        """Test invalid experience years"""
        with pytest.raises(ValidationError):
            OgretmenProfili(
                ogretmen_id="test",
                kullanici_id="user",
                okul_adi="Test",
                brans="Test",
                deneyim_yili=invalid_deneyim,
            )


class TestVeliProfili:
    """Test parent profile model"""

    def test_complete_veli_profili(self):
        """Test creating complete parent profile"""
        profil = VeliProfili(
            veli_id="veli123",
            kullanici_id="user123",
            cocuk_ogrenci_ids=["ogr1", "ogr2", "ogr3"],
            email_bildirimleri=True,
            sms_bildirimleri=True,
        )

        assert profil.veli_id == "veli123"
        assert len(profil.cocuk_ogrenci_ids) == 3
        assert profil.email_bildirimleri is True
        assert profil.sms_bildirimleri is True

    def test_veli_minimal(self):
        """Test parent profile with minimal fields"""
        profil = VeliProfili(veli_id="min123", kullanici_id="user123")

        assert profil.veli_id == "min123"
        assert len(profil.cocuk_ogrenci_ids) == 0
        assert profil.email_bildirimleri is True  # Default
        assert profil.sms_bildirimleri is False  # Default

    def test_veli_multiple_children(self):
        """Test parent with multiple children"""
        profil = VeliProfili(
            veli_id="multi",
            kullanici_id="user",
            cocuk_ogrenci_ids=[f"ogr{i}" for i in range(1, 6)],
        )

        assert len(profil.cocuk_ogrenci_ids) == 5

    def test_veli_notification_preferences(self):
        """Test different notification preference combinations"""
        # Both notifications
        profil1 = VeliProfili(
            veli_id="v1",
            kullanici_id="u1",
            email_bildirimleri=True,
            sms_bildirimleri=True,
        )
        assert profil1.email_bildirimleri and profil1.sms_bildirimleri

        # Only email
        profil2 = VeliProfili(
            veli_id="v2",
            kullanici_id="u2",
            email_bildirimleri=True,
            sms_bildirimleri=False,
        )
        assert profil2.email_bildirimleri and not profil2.sms_bildirimleri

        # No notifications
        profil3 = VeliProfili(
            veli_id="v3",
            kullanici_id="u3",
            email_bildirimleri=False,
            sms_bildirimleri=False,
        )
        assert not profil3.email_bildirimleri and not profil3.sms_bildirimleri


class TestKullaniciGiris:
    """Test user login model"""

    def test_valid_giris(self):
        """Test valid login credentials"""
        giris = KullaniciGiris(email="user@test.com", sifre="ValidPass123!")

        assert giris.email == "user@test.com"
        assert giris.sifre == "ValidPass123!"

    def test_invalid_email_giris(self):
        """Test login with invalid email"""
        with pytest.raises(ValidationError):
            KullaniciGiris(email="not-valid-email", sifre="SomePassword123!")


class TestTokenYaniti:
    """Test token response model"""

    def test_complete_token_yaniti(self):
        """Test complete token response"""
        user = Kullanici(
            kullanici_id="user123",
            email="test@test.com",
            ad_soyad="Test User",
            rol=KullaniciRolu.OGRENCI,
        )

        token = TokenYaniti(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
            expires_in=3600,
            kullanici=user,
        )

        assert token.access_token.startswith("eyJ")
        assert token.token_type == "bearer"
        assert token.expires_in == 3600
        assert token.kullanici.kullanici_id == "user123"

    def test_token_default_type(self):
        """Test token response with default type"""
        user = Kullanici(
            kullanici_id="user123",
            email="test@test.com",
            ad_soyad="Test User",
            rol=KullaniciRolu.ADMIN,
        )

        token = TokenYaniti(access_token="test_token", expires_in=7200, kullanici=user)

        assert token.token_type == "bearer"  # Default value
        assert token.expires_in == 7200
