"""
Kullanıcı yönetimi veri modelleri
SECURITY FIX: Strong password policy validation
"""
import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .enums import KullaniciRolu, OgrenmeStili, SinavTipi


class KullaniciBase(BaseModel):
    """Temel kullanıcı bilgileri"""

    email: EmailStr = Field(..., description="Kullanıcı e-posta adresi")
    ad_soyad: str = Field(..., min_length=2, max_length=100, description="Ad ve soyad")
    telefon: Optional[str] = Field(None, max_length=15, description="Telefon numarası")
    aktif: bool = Field(True, description="Hesap aktif durumu")


class KullaniciOlustur(KullaniciBase):
    """
    Kullanıcı oluşturma modeli
    SECURITY FIX: Strong password policy (min 8 chars, complexity requirements)
    """

    sifre: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Kullanıcı şifresi (min 8 karakter, büyük/küçük harf, rakam, özel karakter)",
    )
    rol: KullaniciRolu = Field(..., description="Kullanıcı rolü")

    @field_validator("sifre")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        SECURITY FIX: Strong password validation
        Requirements:
        - Min 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
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
        common_passwords = [
            "password",
            "password123",
            "12345678",
            "qwerty123",
            "admin123",
            "welcome123",
            "password1",
            "test1234",
        ]
        # Remove special characters for comparison
        base_password = re.sub(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', "", v).lower()
        if base_password in common_passwords:
            raise ValueError(
                "Bu şifre çok yaygın kullanılmaktadır, daha güçlü bir şifre seçin"
            )

        return v


class Kullanici(KullaniciBase):
    """Tam kullanıcı modeli"""

    kullanici_id: str = Field(..., description="Benzersiz kullanıcı ID")
    rol: KullaniciRolu = Field(..., description="Kullanıcı rolü")
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_giris: Optional[datetime] = Field(None, description="Son giriş tarihi")

    class Config:
        from_attributes = True


class OgrenciProfili(BaseModel):
    """Öğrenci profil bilgileri"""

    ogrenci_id: str = Field(..., description="Öğrenci ID")
    kullanici_id: str = Field(..., description="Bağlı kullanıcı ID")

    # Eğitim Bilgileri
    sinif_seviyesi: int = Field(..., ge=9, le=12, description="Sınıf seviyesi (9-12)")
    okul_adi: Optional[str] = Field(None, max_length=200, description="Okul adı")
    hedef_sinav: SinavTipi = Field(..., description="Hedeflenen sınav türü")
    hedef_universiteler: List[str] = Field(
        default_factory=list, description="Hedef üniversiteler"
    )

    # Öğrenme Özellikleri
    ogrenme_stili: Optional[OgrenmeStili] = Field(None, description="Öğrenme stili")
    guclu_alanlar: List[str] = Field(
        default_factory=list, description="Güçlü olduğu konular"
    )
    zayif_alanlar: List[str] = Field(
        default_factory=list, description="Zayıf olduğu konular"
    )
    gunluk_calisma_hedefi: Optional[int] = Field(
        None, ge=30, le=600, description="Günlük çalışma hedefi (dakika)"
    )

    # Güvenlik ve İzinler
    veli_onay: bool = Field(False, description="Veli onayı durumu")
    veli_kullanici_id: Optional[str] = Field(None, description="Veli kullanıcı ID")

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_guncelleme: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class OgretmenProfili(BaseModel):
    """Öğretmen profil bilgileri"""

    ogretmen_id: str = Field(..., description="Öğretmen ID")
    kullanici_id: str = Field(..., description="Bağlı kullanıcı ID")

    # Mesleki Bilgiler
    okul_adi: str = Field(..., max_length=200, description="Çalıştığı okul")
    brans: str = Field(..., max_length=50, description="Branş/Alan")
    deneyim_yili: Optional[int] = Field(None, ge=0, le=50, description="Deneyim yılı")

    # Sınıf Yönetimi
    sinif_listesi: List[str] = Field(
        default_factory=list, description="Sorumlu olduğu sınıflar"
    )

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_guncelleme: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class VeliProfili(BaseModel):
    """Veli profil bilgileri"""

    veli_id: str = Field(..., description="Veli ID")
    kullanici_id: str = Field(..., description="Bağlı kullanıcı ID")

    # Çocuk Bilgileri
    cocuk_ogrenci_ids: List[str] = Field(
        default_factory=list, description="Çocuk öğrenci ID'leri"
    )

    # İletişim Tercihleri
    email_bildirimleri: bool = Field(True, description="E-posta bildirimi tercihi")
    sms_bildirimleri: bool = Field(False, description="SMS bildirimi tercihi")

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=datetime.now)
    son_guncelleme: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class KullaniciGiris(BaseModel):
    """Kullanıcı giriş modeli - Hem 'sifre' hem 'password' kabul eder"""

    email: EmailStr = Field(..., description="E-posta adresi")
    sifre: Optional[str] = Field(None, description="Şifre (Türkçe)")
    password: Optional[str] = Field(None, description="Şifre (İngilizce)")

    class Config:
        # Hem 'sifre' hem 'password' field'ını kabul et
        extra = "allow"

    def get_password(self) -> str:
        """Şifreyi döndür (sifre veya password, hangisi varsa)"""
        return self.sifre or self.password or ""


class TokenYaniti(BaseModel):
    """Token yanıt modeli - Supports both backend (Turkish) and frontend (English) formats"""

    # Backend format (Turkish) - backward compatibility
    access_token: str = Field(..., description="Erişim token'ı")
    token_type: str = Field("bearer", description="Token türü")
    expires_in: int = Field(..., description="Token geçerlilik süresi (saniye)")
    kullanici: Kullanici = Field(..., description="Kullanıcı bilgileri")

    # Frontend format (English) - new fields
    success: Optional[bool] = Field(None, description="Success status for frontend")
    token: Optional[str] = Field(None, description="Access token (English alias)")
    refreshToken: Optional[str] = Field(None, description="Refresh token for frontend")
    user: Optional[dict] = Field(None, description="User object in frontend format")
