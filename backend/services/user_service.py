"""
Basit kullanıcı yönetimi servisi
SECURITY FIX: Strong password validation integrated
"""
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from passlib.context import CryptContext

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
from core.password_validator import PasswordValidator, PasswordValidationError

# SECURITY FIX: bcrypt password hashing (replaces weak SHA-256)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class KullaniciServisi:
    """Basit kullanıcı yönetimi servisi - In-memory implementation"""

    def __init__(self):
        # In-memory veri saklama (production'da database kullanılacak)
        self.kullanicilar: Dict[str, Kullanici] = {}
        self.sifreler: Dict[str, str] = {}  # kullanici_id -> hashed_password
        self.email_index: Dict[str, str] = {}  # email -> kullanici_id
        self.ogrenci_profilleri: Dict[str, OgrenciProfili] = {}
        self.ogretmen_profilleri: Dict[str, OgretmenProfili] = {}
        self.veli_profilleri: Dict[str, VeliProfili] = {}
        self.aktif_tokenlar: Dict[str, Dict] = {}  # token -> user_info

    def _sifre_hash_et(self, sifre: str) -> str:
        """Şifreyi bcrypt ile hash'le (SECURITY FIX: SHA-256 → bcrypt)"""
        return pwd_context.hash(sifre)

    def _sifre_dogrula(self, sifre: str, hashed_sifre: str) -> bool:
        """Şifre doğrulama (bcrypt verify)"""
        return pwd_context.verify(sifre, hashed_sifre)

    def _token_olustur(self, kullanici_id: str) -> str:
        """Basit token oluştur"""
        return secrets.token_urlsafe(32)

    async def kullanici_olustur(self, kullanici_data: KullaniciOlustur) -> Kullanici:
        """
        Yeni kullanıcı oluştur
        SECURITY FIX: Strong password validation (12+ chars, complexity)
        """
        # E-posta kontrolü
        if kullanici_data.email in self.email_index:
            raise ValueError("Bu e-posta adresi zaten kullanımda")

        # SECURITY FIX: Validate password strength
        try:
            PasswordValidator.validate(
                kullanici_data.sifre, username=kullanici_data.email.split("@")[0]
            )
        except PasswordValidationError as e:
            raise ValueError(f"Şifre gereksinimleri karşılanmıyor: {str(e)}")

        # Kullanıcı ID oluştur
        kullanici_id = str(uuid.uuid4())

        # Kullanıcı oluştur
        kullanici = Kullanici(
            kullanici_id=kullanici_id,
            email=kullanici_data.email,
            ad_soyad=kullanici_data.ad_soyad,
            telefon=kullanici_data.telefon,
            rol=kullanici_data.rol,
            aktif=True,
            olusturma_tarihi=datetime.now(),
        )

        # Veri kaydet
        self.kullanicilar[kullanici_id] = kullanici
        self.sifreler[kullanici_id] = self._sifre_hash_et(kullanici_data.sifre)
        self.email_index[kullanici_data.email] = kullanici_id

        return kullanici

    async def kullanici_giris(self, giris_data: KullaniciGiris) -> TokenYaniti:
        """Kullanıcı girişi"""
        # E-posta kontrolü
        if giris_data.email not in self.email_index:
            raise ValueError("Geçersiz e-posta veya şifre")

        kullanici_id = self.email_index[giris_data.email]
        kullanici = self.kullanicilar[kullanici_id]

        # Şifre kontrolü (SECURITY FIX: bcrypt verify)
        if not self._sifre_dogrula(giris_data.sifre, self.sifreler[kullanici_id]):
            raise ValueError("Geçersiz e-posta veya şifre")

        # Aktif kullanıcı kontrolü
        if not kullanici.aktif:
            raise ValueError("Hesap aktif değil")

        # Token oluştur
        token = self._token_olustur(kullanici_id)
        expires_in = 3600 * 24  # 24 saat

        # Token kaydet
        self.aktif_tokenlar[token] = {
            "kullanici_id": kullanici_id,
            "expires_at": datetime.now() + timedelta(seconds=expires_in),
        }

        # Son giriş güncelle
        kullanici.son_giris = datetime.now()

        return TokenYaniti(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            kullanici=kullanici,
        )

    async def token_dogrula(self, token: str) -> Optional[Kullanici]:
        """Token doğrula ve kullanıcı bilgilerini döndür"""
        if token not in self.aktif_tokenlar:
            return None

        token_info = self.aktif_tokenlar[token]

        # Token süresi kontrolü
        if datetime.now() > token_info["expires_at"]:
            del self.aktif_tokenlar[token]
            return None

        kullanici_id = token_info["kullanici_id"]
        return self.kullanicilar.get(kullanici_id)

    async def kullanici_getir(self, kullanici_id: str) -> Optional[Kullanici]:
        """Kullanıcı bilgilerini getir"""
        return self.kullanicilar.get(kullanici_id)

    async def kullanici_listesi(
        self, rol: Optional[KullaniciRolu] = None
    ) -> List[Kullanici]:
        """Kullanıcı listesi getir"""
        kullanicilar = list(self.kullanicilar.values())

        if rol:
            kullanicilar = [k for k in kullanicilar if k.rol == rol]

        return kullanicilar

    async def ogrenci_profili_olustur(
        self, profil_data: OgrenciProfili
    ) -> OgrenciProfili:
        """Öğrenci profili oluştur"""
        # Kullanıcı kontrolü
        if profil_data.kullanici_id not in self.kullanicilar:
            raise ValueError("Geçersiz kullanıcı ID")

        kullanici = self.kullanicilar[profil_data.kullanici_id]
        if kullanici.rol != KullaniciRolu.OGRENCI:
            raise ValueError("Kullanıcı öğrenci rolünde değil")

        # Profil kaydet
        self.ogrenci_profilleri[profil_data.ogrenci_id] = profil_data
        return profil_data

    async def ogrenci_profili_getir(self, ogrenci_id: str) -> Optional[OgrenciProfili]:
        """Öğrenci profili getir"""
        return self.ogrenci_profilleri.get(ogrenci_id)

    async def ogretmen_profili_olustur(
        self, profil_data: OgretmenProfili
    ) -> OgretmenProfili:
        """Öğretmen profili oluştur"""
        # Kullanıcı kontrolü
        if profil_data.kullanici_id not in self.kullanicilar:
            raise ValueError("Geçersiz kullanıcı ID")

        kullanici = self.kullanicilar[profil_data.kullanici_id]
        if kullanici.rol != KullaniciRolu.OGRETMEN:
            raise ValueError("Kullanıcı öğretmen rolünde değil")

        # Profil kaydet
        self.ogretmen_profilleri[profil_data.ogretmen_id] = profil_data
        return profil_data

    async def ogretmen_profili_getir(
        self, ogretmen_id: str
    ) -> Optional[OgretmenProfili]:
        """Öğretmen profili getir"""
        return self.ogretmen_profilleri.get(ogretmen_id)

    async def veli_profili_olustur(self, profil_data: VeliProfili) -> VeliProfili:
        """Veli profili oluştur"""
        # Kullanıcı kontrolü
        if profil_data.kullanici_id not in self.kullanicilar:
            raise ValueError("Geçersiz kullanıcı ID")

        kullanici = self.kullanicilar[profil_data.kullanici_id]
        if kullanici.rol != KullaniciRolu.VELI:
            raise ValueError("Kullanıcı veli rolünde değil")

        # Profil kaydet
        self.veli_profilleri[profil_data.veli_id] = profil_data
        return profil_data

    async def veli_profili_getir(self, veli_id: str) -> Optional[VeliProfili]:
        """Veli profili getir"""
        return self.veli_profilleri.get(veli_id)

    async def kullanici_cikis(self, token: str) -> bool:
        """Kullanıcı çıkışı - token'ı geçersiz kıl"""
        if token in self.aktif_tokenlar:
            del self.aktif_tokenlar[token]
            return True
        return False

    async def kullanici_guncelle(
        self, kullanici_id: str, kullanici_data: Dict
    ) -> Optional[Kullanici]:
        """Kullanıcı bilgilerini güncelle"""
        if kullanici_id not in self.kullanicilar:
            return None

        kullanici = self.kullanicilar[kullanici_id]

        # Güncellenebilir alanları kontrol et ve güncelle
        if "ad_soyad" in kullanici_data:
            kullanici.ad_soyad = kullanici_data["ad_soyad"]

        if "telefon" in kullanici_data:
            kullanici.telefon = kullanici_data["telefon"]

        if "aktif" in kullanici_data:
            kullanici.aktif = kullanici_data["aktif"]

        if "rol" in kullanici_data:
            # Rol değişikliği dikkatli yapılmalı
            try:
                yeni_rol = KullaniciRolu(kullanici_data["rol"])
                kullanici.rol = yeni_rol
            except ValueError:
                raise ValueError("Geçersiz rol değeri")

        # Son güncelleme zamanını ayarla
        kullanici.son_guncelleme = datetime.now()

        return kullanici

    async def kullanici_sil(self, kullanici_id: str) -> bool:
        """Kullanıcıyı sil"""
        if kullanici_id not in self.kullanicilar:
            return False

        # Kullanıcıyı ve ilgili verileri sil
        kullanici = self.kullanicilar[kullanici_id]

        # E-posta index'ini temizle
        if kullanici.email in self.email_index:
            del self.email_index[kullanici.email]

        # Şifreyi sil
        if kullanici_id in self.sifreler:
            del self.sifreler[kullanici_id]

        # Profilleri sil
        # Öğrenci profili
        for ogrenci_id, profil in list(self.ogrenci_profilleri.items()):
            if profil.kullanici_id == kullanici_id:
                del self.ogrenci_profilleri[ogrenci_id]

        # Öğretmen profili
        for ogretmen_id, profil in list(self.ogretmen_profilleri.items()):
            if profil.kullanici_id == kullanici_id:
                del self.ogretmen_profilleri[ogretmen_id]

        # Veli profili
        for veli_id, profil in list(self.veli_profilleri.items()):
            if profil.kullanici_id == kullanici_id:
                del self.veli_profilleri[veli_id]

        # Aktif token'ları sil
        tokens_to_remove = []
        for token, token_info in self.aktif_tokenlar.items():
            if token_info["kullanici_id"] == kullanici_id:
                tokens_to_remove.append(token)

        for token in tokens_to_remove:
            del self.aktif_tokenlar[token]

        # Kullanıcıyı sil
        del self.kullanicilar[kullanici_id]

        return True


# Global servis instance
kullanici_servisi = KullaniciServisi()


# Removed duplicate - use get_current_user from core.dependencies instead
