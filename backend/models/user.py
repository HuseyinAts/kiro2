"""
Kullanıcı yönetimi veri modelleri
SECURITY FIX: Strong password policy validation
TIMEZONE FIX: Using timezone-aware datetime
"""

import re
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .enums import KullaniciRolu, OgrenmeStili, SinavTipi


class KullaniciBase(BaseModel):
    """Temel kullanıcı bilgileri.

    Tüm kullanıcı modellerinin temelini oluşturur.
    Email, ad-soyad ve telefon gibi temel bilgileri içerir.

    Attributes:
        email: Kullanıcı e-posta adresi (unique)
        ad_soyad: Kullanıcının tam adı (2-100 karakter)
        telefon: Telefon numarası (opsiyonel, max 15 karakter)
        aktif: Hesap aktiflik durumu (varsayılan True)
    """

    email: EmailStr = Field(..., description="Kullanıcı e-posta adresi")
    ad_soyad: str = Field(..., min_length=2, max_length=100, description="Ad ve soyad")
    telefon: str | None = Field(None, max_length=15, description="Telefon numarası")
    aktif: bool = Field(True, description="Hesap aktif durumu")


class KullaniciOlustur(KullaniciBase):
    """Kullanıcı oluşturma modeli.

    Yeni kullanıcı kaydı için gerekli tüm bilgileri içerir.
    Güçlü şifre politikası uygulanır.

    Attributes:
        sifre: Kullanıcı şifresi (güçlü şifre kuralları uygulanır)
        rol: Kullanıcı rolü (OGRENCI, OGRETMEN, VELI, ADMIN)

    Note:
        Şifre en az 8 karakter olmalı ve şunları içermeli:
        - En az bir büyük harf
        - En az bir küçük harf
        - En az bir rakam
        - En az bir özel karakter
    """

    sifre: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Kullanıcı şifresi (min 8 karakter, büyük/küçük harf, rakam, özel karakter)",
    )
    rol: KullaniciRolu = Field(..., description="Kullanıcı rolü")
    birth_date: date = Field(
        ..., description="Doğum tarihi (KVKK reşitlik / veli onayı için)"
    )
    veli_email: EmailStr | None = Field(
        None, description="Veli e-postası (18 yaş altı için zorunlu, KVKK Faz 1)"
    )

    @field_validator("sifre")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Güçlü şifre doğrulaması yapar.

        Şifrenin güvenlik gereksinimlerini karşıladığını kontrol eder.

        Args:
            v: Doğrulanacak şifre

        Returns:
            str: Doğrulanmış şifre

        Raises:
            ValueError: Şifre gereksinimleri karşılanmazsa

        Requirements:
            - Min 8 karakter
            - En az bir büyük harf
            - En az bir küçük harf
            - En az bir rakam
            - En az bir özel karakter (!@#$%^&* vb.)
        """
        if len(v) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır")

        if len(v) > 128:
            raise ValueError("Şifre en fazla 128 karakter olabilir")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Şifre en az bir büyük harf içermelidir")

        if not re.search(r"[a-z]", v):
            raise ValueError("Şifre en az bir küçük harf içermelidir")

        if not re.search(r"\d", v):
            raise ValueError("Şifre en az bir rakam içermelidir")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', v):
            raise ValueError("Şifre en az bir özel karakter içermelidir (!@#$%^&* vb.)")

        # Check for common weak passwords (check base password without special chars)
        # Extended list includes Turkish common passwords (SECURITY FIX #27)
        common_passwords = [
            # English common passwords
            "password",
            "password123",
            "password1",
            "passw0rd",
            "12345678",
            "123456789",
            "1234567890",
            "qwerty123",
            "qwertyuiop",
            "qwerty12",
            "admin123",
            "administrator",
            "letmein",
            "welcome123",
            "welcome1",
            "welcome",
            "test1234",
            "test123",
            "testing123",
            "abc12345",
            "abcd1234",
            "abcdefgh",
            "monkey123",
            "dragon123",
            "master123",
            "football",
            "baseball",
            "basketball",
            "sunshine",
            "princess",
            "shadow123",
            "superman",
            "batman123",
            "spiderman",
            "michael1",
            "jordan23",
            "ashley123",
            "iloveyou",
            "trustno1",
            "whatever",
            # Turkish common passwords
            "sifre123",
            "sifremi",
            "parola123",
            "turkiye1",
            "istanbul1",
            "ankara123",
            "galatasaray",
            "fenerbahce",
            "besiktas",
            "trabzon",
            "antalya",
            "izmir123",
            "ogrenci",
            "ogrenci1",
            "okul1234",
            "universite",
            "sinav123",
            "yks12345",
            "merhaba1",
            "hosgeld",
            "nasilsin",
            "annebaba",
            "ailem123",
            "evim1234",
            "aslan123",
            "kaplan12",
            "kartal12",
            "mustafa1",
            "mehmet12",
            "ahmet123",
            "fatma123",
            "ayse1234",
            "zeynep12",
            "atatürk",
            "ataturk1",
            "cumhur",
        ]
        # Remove special characters for comparison
        base_password = re.sub(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', "", v).lower()
        if base_password in common_passwords:
            raise ValueError(
                "Bu şifre çok yaygın kullanılmaktadır, daha güçlü bir şifre seçin"
            )

        return v


class Kullanici(KullaniciBase):
    """Tam kullanıcı modeli.

    Veritabanında saklanan kullanıcı bilgilerinin tamamını içerir.
    Bu model API response'larında kullanılır (şifre hariç).

    Attributes:
        kullanici_id: Benzersiz kullanıcı kimliği (UUID)
        rol: Kullanıcı rolü
        olusturma_tarihi: Hesap oluşturulma tarihi (UTC)
        son_giris: Son giriş tarihi (UTC, opsiyonel)

    Config:
        from_attributes: SQLAlchemy model'lerinden otomatik dönüşüm
    """

    kullanici_id: str = Field(..., alias="id", description="Benzersiz kullanıcı ID")
    rol: KullaniciRolu = Field(..., description="Kullanıcı rolü")
    olusturma_tarihi: datetime = Field(default_factory=lambda: datetime.now(UTC))
    son_giris: datetime | None = Field(None, description="Son giriş tarihi")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OgrenciProfilOlusturGirdi(BaseModel):
    """POST /auth/ogrenci-profil gövdesi — öğrenci/kullanıcı ID istemciden kabul edilmez."""

    sinif_seviyesi: int = Field(..., ge=9, le=12, description="Sınıf seviyesi (9-12)")
    okul_adi: str | None = Field(None, max_length=200, description="Okul adı")
    hedef_sinav: SinavTipi = Field(..., description="Hedeflenen sınav türü")
    hedef_universiteler: list[str] = Field(default_factory=list)
    ogrenme_stili: OgrenmeStili | None = None
    guclu_alanlar: list[str] = Field(default_factory=list)
    zayif_alanlar: list[str] = Field(default_factory=list)
    gunluk_calisma_hedefi: int | None = Field(None, ge=30, le=600)

    model_config = ConfigDict(from_attributes=True)


class OgretmenProfilOlusturGirdi(BaseModel):
    """POST /auth/ogretmen-profil gövdesi — öğretmen/kullanıcı ID istemciden kabul edilmez."""

    okul_adi: str = Field(..., max_length=200)
    brans: str = Field(..., max_length=50)
    deneyim_yili: int | None = Field(None, ge=0, le=50)
    sinif_listesi: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class VeliProfilOlusturGirdi(BaseModel):
    """POST /auth/veli-profil gövdesi — çocuk listesi ayrı eşleştirme uçlarından; oluşturmada gönderilmez."""

    email_bildirimleri: bool = True
    sms_bildirimleri: bool = False

    model_config = ConfigDict(from_attributes=True)


class OgrenciProfili(BaseModel):
    """Öğrenci profil bilgileri.

    Öğrenci kullanıcılarına özel profil bilgilerini içerir.
    Eğitim durumu, öğrenme özellikleri ve veli onay bilgileri bulunur.

    Attributes:
        ogrenci_id: Öğrenci profil kimliği
        kullanici_id: İlişkili kullanıcı kimliği
        sinif_seviyesi: Sınıf seviyesi (9-12)
        okul_adi: Okul adı (opsiyonel)
        hedef_sinav: Hedeflenen sınav türü
        hedef_universiteler: Hedef üniversite listesi
        ogrenme_stili: Tespit edilen öğrenme stili
        guclu_alanlar: Güçlü olunan konular
        zayif_alanlar: Geliştirilmesi gereken konular
        gunluk_calisma_hedefi: Günlük çalışma hedefi (dakika)
        veli_onay: Veli onay durumu
        veli_kullanici_id: Veli kullanıcı kimliği
    """

    ogrenci_id: str = Field(..., description="Öğrenci ID")
    kullanici_id: str = Field(..., description="Bağlı kullanıcı ID")

    # Eğitim Bilgileri
    sinif_seviyesi: int = Field(..., ge=9, le=12, description="Sınıf seviyesi (9-12)")
    okul_adi: str | None = Field(None, max_length=200, description="Okul adı")
    hedef_sinav: SinavTipi = Field(..., description="Hedeflenen sınav türü")
    hedef_universiteler: list[str] = Field(
        default_factory=list, description="Hedef üniversiteler"
    )

    # Öğrenme Özellikleri
    ogrenme_stili: OgrenmeStili | None = Field(None, description="Öğrenme stili")
    guclu_alanlar: list[str] = Field(
        default_factory=list, description="Güçlü olduğu konular"
    )
    zayif_alanlar: list[str] = Field(
        default_factory=list, description="Zayıf olduğu konular"
    )
    gunluk_calisma_hedefi: int | None = Field(
        None, ge=30, le=600, description="Günlük çalışma hedefi (dakika)"
    )

    # Güvenlik ve İzinler
    veli_onay: bool = Field(False, description="Veli onayı durumu")
    veli_kullanici_id: str | None = Field(None, description="Veli kullanıcı ID")

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_guncelleme: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class OgretmenProfili(BaseModel):
    """Öğretmen profil bilgileri"""

    ogretmen_id: str = Field(..., description="Öğretmen ID")
    kullanici_id: str = Field(..., description="Bağlı kullanıcı ID")

    # Mesleki Bilgiler
    okul_adi: str = Field(..., max_length=200, description="Çalıştığı okul")
    brans: str = Field(..., max_length=50, description="Branş/Alan")
    deneyim_yili: int | None = Field(None, ge=0, le=50, description="Deneyim yılı")

    # Sınıf Yönetimi
    sinif_listesi: list[str] = Field(
        default_factory=list, description="Sorumlu olduğu sınıflar"
    )

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_guncelleme: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class VeliProfili(BaseModel):
    """Veli profil bilgileri"""

    veli_id: str = Field(..., description="Veli ID")
    kullanici_id: str = Field(..., description="Bağlı kullanıcı ID")

    # Çocuk Bilgileri
    cocuk_ogrenci_ids: list[str] = Field(
        default_factory=list, description="Çocuk öğrenci ID'leri"
    )

    # İletişim Tercihleri
    email_bildirimleri: bool = Field(True, description="E-posta bildirimi tercihi")
    sms_bildirimleri: bool = Field(False, description="SMS bildirimi tercihi")

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_guncelleme: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class KullaniciGiris(BaseModel):
    """Kullanıcı giriş modeli.

    Login endpoint'i için kullanılır. Hem Türkçe 'sifre' hem de
    İngilizce 'password' field'ını destekler (backward compatibility).

    Attributes:
        email: Kullanıcı e-posta adresi
        sifre: Şifre (Türkçe field adı)
        password: Şifre (İngilizce field adı, uyumluluk için)

    Methods:
        get_password: Hangi field doluysa o şifreyi döndürür
    """

    email: EmailStr = Field(..., description="E-posta adresi")
    sifre: str | None = Field(None, description="Şifre (Türkçe)")
    password: str | None = Field(None, description="Şifre (İngilizce)")

    model_config = ConfigDict(
        # Hem 'sifre' hem 'password' field'ını kabul et
        extra="allow"
    )

    def get_password(self) -> str:
        """Şifreyi döndürür.

        'sifre' veya 'password' field'larından hangisi doluysa
        onu döndürür. Her ikisi de boşsa boş string döner.

        Returns:
            str: Kullanıcı şifresi
        """
        return self.sifre or self.password or ""


class TokenYaniti(BaseModel):
    """Token yanıt modeli - Supports both backend (Turkish) and frontend (English) formats"""

    # Backend format (Turkish) - backward compatibility
    access_token: str = Field(..., description="Erişim token'ı")
    token_type: str = Field("bearer", description="Token türü")
    expires_in: int = Field(..., description="Token geçerlilik süresi (saniye)")
    kullanici: Kullanici = Field(..., description="Kullanıcı bilgileri")

    # Frontend format (English) - new fields
    success: bool | None = Field(None, description="Success status for frontend")
    token: str | None = Field(None, description="Access token (English alias)")
    refreshToken: str | None = Field(None, description="Refresh token for frontend")
    user: dict | None = Field(None, description="User object in frontend format")


# ==================== BACKWARD COMPATIBILITY ALIASES ====================
# These aliases allow importing with English names for compatibility
# Usage: from models.user import User, UserCreate, UserLogin
User = Kullanici
UserCreate = KullaniciOlustur
UserLogin = KullaniciGiris
StudentProfile = OgrenciProfili
TeacherProfile = OgretmenProfili
ParentProfile = VeliProfili
TokenResponse = TokenYaniti
