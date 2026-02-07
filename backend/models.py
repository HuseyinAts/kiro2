"""
Pydantic models for request/response validation
Ultra simple, no authentication required
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """Chat request model"""

    agent: str = Field(..., description="Agent type: learning, study, or exam")
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(
        None, description="Optional session ID for history tracking"
    )


class ChatResponse(BaseModel):
    """Chat response model"""

    response: str = Field(..., description="Agent response")
    agent: str = Field(..., description="Agent that responded")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None


class AgentInfo(BaseModel):
    """Agent information model"""

    id: str
    name: str
    description: str
    icon: str


class SessionMessage(BaseModel):
    """Session message model"""

    role: str  # 'user' or 'agent'
    content: str
    agent: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class WebSocketMessage(BaseModel):
    """WebSocket message model"""

    type: str  # 'chat', 'status', 'error'
    agent: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ==================== KULLANICI MODELLERİ ====================


class KullaniciRolu(str, Enum):
    """Kullanıcı rolleri"""

    OGRENCI = "ogrenci"
    VELI = "veli"
    OGRETMEN = "ogretmen"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Kullanici(BaseModel):
    """Kullanıcı modeli"""

    kullanici_id: str = Field(..., alias="id")
    email: str
    ad_soyad: str
    telefon: Optional[str] = None
    rol: KullaniciRolu
    aktif: bool = True
    olusturma_tarihi: datetime = Field(..., alias="kayit_tarihi")
    son_giris: Optional[datetime] = None
    son_guncelleme: Optional[datetime] = None
    profil_resmi: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class KullaniciOlustur(BaseModel):
    """Kullanıcı oluşturma modeli"""

    email: str = Field(..., description="Kullanıcı email adresi")
    ad_soyad: str = Field(..., description="Kullanıcı adı soyadı")
    sifre: str = Field(..., description="Kullanıcı şifresi")
    rol: KullaniciRolu = Field(
        default=KullaniciRolu.OGRENCI, description="Kullanıcı rolü"
    )
    aktif: bool = Field(default=True, description="Kullanıcı aktif durumu")


class KullaniciGiris(BaseModel):
    """Kullanıcı giriş modeli - Hem 'sifre' hem 'password' kabul eder"""

    email: str = Field(..., description="Kullanıcı email adresi")
    sifre: Optional[str] = Field(None, description="Kullanıcı şifresi (Türkçe)")
    password: Optional[str] = Field(None, description="Kullanıcı şifresi (İngilizce)")

    model_config = ConfigDict(extra="allow")

    def get_password(self) -> str:
        """Şifreyi döndür (sifre veya password, hangisi varsa)"""
        return self.sifre or self.password or ""


class TokenYaniti(BaseModel):
    """Token yanıt modeli"""

    access_token: str = Field(..., description="Erişim token'ı")
    token_type: str = Field(default="bearer", description="Token tipi")
    expires_in: int = Field(..., description="Token geçerlilik süresi (saniye)")
    kullanici: Kullanici = Field(..., description="Kullanıcı bilgileri")


class OgrenciProfili(BaseModel):
    """Öğrenci profil modeli"""

    ogrenci_id: str
    kullanici_id: str
    sinif: Optional[int] = None
    okul: Optional[str] = None
    hedef_puan: Optional[float] = None


class OgretmenProfili(BaseModel):
    """Öğretmen profil modeli"""

    ogretmen_id: str
    kullanici_id: str
    brans: Optional[str] = None
    okul: Optional[str] = None


class VeliProfili(BaseModel):
    """Veli profil modeli"""

    veli_id: str
    kullanici_id: str
    cocuk_sayisi: Optional[int] = None
