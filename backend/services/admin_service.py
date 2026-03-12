"""
Admin Panel Servis Katmanı
Kullanıcı yönetimi, dashboard istatistikleri ve içerik yönetimi servisleri
"""
import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

from models import Kullanici, KullaniciOlustur, KullaniciRolu
from services.soru_bankasi_service import soru_bankasi_servisi
from services.user_service import kullanici_servisi


class AdminAuthorizationError(Exception):
    """Admin yetkilendirme hatası"""


def admin_required(func):
    """
    Admin yetkisi gerektiren metodlar için decorator
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # İlk parametre genellikle kullanıcı ID'si veya kullanıcı objesi olmalı
        current_user = kwargs.get("current_user") or (args[0] if args else None)

        if not await self._admin_yetkisi_kontrol(current_user):
            raise AdminAuthorizationError("Bu işlem için admin yetkisi gereklidir")

        return await func(self, *args, **kwargs)

    return wrapper


def super_admin_required(func):
    """
    Süper admin yetkisi gerektiren metodlar için decorator
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        current_user = kwargs.get("current_user") or (args[0] if args else None)

        if not await self._super_admin_yetkisi_kontrol(current_user):
            raise AdminAuthorizationError(
                "Bu işlem için süper admin yetkisi gereklidir"
            )

        return await func(self, *args, **kwargs)

    return wrapper


class AdminService:
    """
    Admin panel servis katmanı
    Kullanıcı yönetimi, dashboard istatistikleri ve içerik yönetimi
    """

    def __init__(self):
        # Admin yetkilendirme seviyeleri
        try:
            self.admin_rolleri = {KullaniciRolu.ADMIN, KullaniciRolu.SUPER_ADMIN}
            self.super_admin_rolleri = {KullaniciRolu.SUPER_ADMIN}
        except AttributeError:
            # SUPER_ADMIN enum değeri yoksa sadece ADMIN kullan
            self.admin_rolleri = {KullaniciRolu.ADMIN}
            self.super_admin_rolleri = {KullaniciRolu.ADMIN}

    # ==================== YETKİLENDİRME KONTROLLERİ ====================

    async def _admin_yetkisi_kontrol(self, kullanici_id_veya_obje) -> bool:
        """
        Kullanıcının admin yetkisi olup olmadığını kontrol et
        """
        try:
            if isinstance(kullanici_id_veya_obje, str):
                kullanici = await kullanici_servisi.kullanici_getir(
                    kullanici_id_veya_obje
                )
            elif hasattr(kullanici_id_veya_obje, "rol"):
                kullanici = kullanici_id_veya_obje
            else:
                return False

            if not kullanici or not kullanici.aktif:
                return False

            return kullanici.rol in self.admin_rolleri

        except Exception as e:
            print(f"Admin yetki kontrolü hatası: {str(e)}")
            return False

    async def _super_admin_yetkisi_kontrol(self, kullanici_id_veya_obje) -> bool:
        """
        Kullanıcının süper admin yetkisi olup olmadığını kontrol et
        """
        try:
            if isinstance(kullanici_id_veya_obje, str):
                kullanici = await kullanici_servisi.kullanici_getir(
                    kullanici_id_veya_obje
                )
            elif hasattr(kullanici_id_veya_obje, "rol"):
                kullanici = kullanici_id_veya_obje
            else:
                return False

            if not kullanici or not kullanici.aktif:
                return False

            return kullanici.rol in self.super_admin_rolleri

        except Exception as e:
            print(f"Süper admin yetki kontrolü hatası: {str(e)}")
            return False

    async def kullanici_yetki_kontrol(
        self, kullanici_id: str, gerekli_rol: KullaniciRolu
    ) -> bool:
        """
        Belirli bir kullanıcının belirli bir role sahip olup olmadığını kontrol et
        """
        try:
            kullanici = await kullanici_servisi.kullanici_getir(kullanici_id)

            if not kullanici or not kullanici.aktif:
                return False

            # Rol hiyerarşisi kontrolü
            rol_hiyerarsi = {
                KullaniciRolu.OGRENCI: 1,
                KullaniciRolu.VELI: 2,
                KullaniciRolu.OGRETMEN: 3,
                KullaniciRolu.ADMIN: 4,
                KullaniciRolu.SUPER_ADMIN: 5,
            }

            kullanici_seviye = rol_hiyerarsi.get(kullanici.rol, 0)
            gerekli_seviye = rol_hiyerarsi.get(gerekli_rol, 0)

            return kullanici_seviye >= gerekli_seviye

        except Exception as e:
            print(f"Kullanıcı yetki kontrolü hatası: {str(e)}")
            return False

    async def admin_aktivite_kaydet(
        self,
        admin_id: str,
        aktivite_tipi: str,
        hedef_id: Optional[str] = None,
        detaylar: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Admin aktivitelerini kaydet (audit log)
        """
        try:
            aktivite = {
                "admin_id": admin_id,
                "aktivite_tipi": aktivite_tipi,
                "hedef_id": hedef_id,
                "detaylar": detaylar or {},
                "zaman": datetime.now().isoformat(),
                "ip_adresi": "127.0.0.1",  # Gerçek implementasyonda request'ten alınacak
            }

            # Gerçek implementasyonda database'e kaydedilecek
            print(f"Admin aktivite kaydedildi: {aktivite}")
            return True

        except Exception as e:
            print(f"Admin aktivite kaydetme hatası: {str(e)}")
            return False

    # ==================== KULLANICI YÖNETİMİ ====================

    @admin_required
    async def kullanicilari_listele(
        self,
        rol: Optional[KullaniciRolu] = None,
        aktif: Optional[bool] = None,
        sayfa: int = 1,
        sayfa_boyutu: int = 20,
        current_user: Optional[str] = None,
    ) -> List[Kullanici]:
        """
        Tüm kullanıcıları listele
        """
        try:
            # Admin aktivitesini kaydet
            await self.admin_aktivite_kaydet(
                current_user,
                "kullanici_listele",
                detaylar={"rol": rol.value if rol else None, "sayfa": sayfa},
            )

            # Basit implementasyon - gerçek database entegrasyonu ile geliştirilecek
            kullanicilar = []

            # Mock data
            for i in range(sayfa_boyutu):
                kullanici = Kullanici(
                    kullanici_id=str(uuid.uuid4()),
                    email=f"kullanici{i}@example.com",
                    ad_soyad=f"Kullannici {i}",
                    rol=rol or KullaniciRolu.OGRENCI,
                    aktif=aktif if aktif is not None else True,
                    olusturma_tarihi=datetime.now() - timedelta(days=i),
                )
                kullanicilar.append(kullanici)

            return kullanicilar

        except AdminAuthorizationError:
            raise
        except Exception as e:
            print(f"Kullanıcı listeleme hatası: {str(e)}")
            return []

    @admin_required
    async def kullanici_olustur(
        self, kullanici_data: KullaniciOlustur, current_user: Optional[str] = None
    ) -> Kullanici:
        """
        Yeni kullanıcı oluştur
        """
        try:
            # Admin/Süper Admin oluşturma için özel kontrol
            if kullanici_data.rol in {KullaniciRolu.ADMIN, KullaniciRolu.SUPER_ADMIN}:
                if not await self._super_admin_yetkisi_kontrol(current_user):
                    raise AdminAuthorizationError(
                        "Admin/Süper Admin oluşturmak için süper admin yetkisi gereklidir"
                    )

            # Kullanıcı servisi üzerinden oluştur
            kullanici = await kullanici_servisi.kullanici_olustur(kullanici_data)

            # Admin aktivitesini kaydet
            await self.admin_aktivite_kaydet(
                current_user,
                "kullanici_olustur",
                hedef_id=kullanici.kullanici_id,
                detaylar={"email": kullanici.email, "rol": kullanici.rol.value},
            )

            return kullanici

        except AdminAuthorizationError:
            raise
        except Exception as e:
            raise ValueError(f"Kullanıcı oluşturma hatası: {str(e)}")

    @admin_required
    async def kullanici_getir(
        self, kullanici_id: str, current_user: Optional[str] = None
    ) -> Optional[Kullanici]:
        """
        Kullanıcı ID ile kullanıcı getir
        """
        try:
            return await kullanici_servisi.kullanici_getir(kullanici_id)
        except Exception as e:
            print(f"Kullanıcı getirme hatası: {str(e)}")
            return None

    @admin_required
    async def kullanici_guncelle(
        self,
        kullanici_id: str,
        kullanici_data: Dict[str, Any],
        current_user: Optional[str] = None,
    ) -> Optional[Kullanici]:
        """
        Kullanıcı bilgilerini güncelle
        """
        try:
            # Hedef kullanıcının rolünü kontrol et
            hedef_kullanici = await kullanici_servisi.kullanici_getir(kullanici_id)
            if hedef_kullanici and hedef_kullanici.rol in {
                KullaniciRolu.ADMIN,
                KullaniciRolu.SUPER_ADMIN,
            }:
                if not await self._super_admin_yetkisi_kontrol(current_user):
                    raise AdminAuthorizationError(
                        "Admin/Süper Admin güncellemek için süper admin yetkisi gereklidir"
                    )

            # Rol değişikliği kontrolü
            if "rol" in kullanici_data:
                yeni_rol = KullaniciRolu(kullanici_data["rol"])
                if yeni_rol in {KullaniciRolu.ADMIN, KullaniciRolu.SUPER_ADMIN}:
                    if not await self._super_admin_yetkisi_kontrol(current_user):
                        raise AdminAuthorizationError(
                            "Admin/Süper Admin rolü atamak için süper admin yetkisi gereklidir"
                        )

            kullanici = await kullanici_servisi.kullanici_guncelle(
                kullanici_id, kullanici_data
            )

            # Admin aktivitesini kaydet
            await self.admin_aktivite_kaydet(
                current_user,
                "kullanici_guncelle",
                hedef_id=kullanici_id,
                detaylar={"guncellenen_alanlar": list(kullanici_data.keys())},
            )

            return kullanici

        except AdminAuthorizationError:
            raise
        except Exception as e:
            raise ValueError(f"Kullanıcı güncelleme hatası: {str(e)}")

    @super_admin_required
    async def kullanici_sil(
        self, kullanici_id: str, current_user: Optional[str] = None
    ) -> bool:
        """
        Kullanıcıyı sil (Sadece süper admin)
        """
        try:
            # Kendini silmeye çalışıyor mu kontrol et
            if kullanici_id == current_user:
                raise AdminAuthorizationError("Kendi hesabınızı silemezsiniz")

            # Hedef kullanıcının bilgilerini al
            hedef_kullanici = await kullanici_servisi.kullanici_getir(kullanici_id)

            sonuc = await kullanici_servisi.kullanici_sil(kullanici_id)

            if sonuc:
                # Admin aktivitesini kaydet
                await self.admin_aktivite_kaydet(
                    current_user,
                    "kullanici_sil",
                    hedef_id=kullanici_id,
                    detaylar={
                        "silinen_email": hedef_kullanici.email
                        if hedef_kullanici
                        else "bilinmiyor",
                        "silinen_rol": hedef_kullanici.rol.value
                        if hedef_kullanici
                        else "bilinmiyor",
                    },
                )

            return sonuc

        except AdminAuthorizationError:
            raise
        except Exception as e:
            print(f"Kullanıcı silme hatası: {str(e)}")
            return False

    # ==================== DASHBOARD İSTATİSTİKLERİ ====================

    @admin_required
    async def dashboard_istatistikleri_getir(
        self, current_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Admin dashboard için genel sistem istatistikleri
        """
        try:
            # Mock istatistikler - gerçek database entegrasyonu ile geliştirilecek
            istatistikler = {
                "kullanici_istatistikleri": {
                    "toplam_kullanici": 1250,
                    "aktif_kullanici": 1180,
                    "rol_dagilimi": {
                        "ogrenci": 1000,
                        "ogretmen": 200,
                        "veli": 45,
                        "admin": 5,
                    },
                    "son_30_gun_kayit": 85,
                },
                "icerik_istatistikleri": {
                    "toplam_soru": await self._toplam_soru_sayisi(),
                    "toplam_egitim_materyali": 450,
                    "onay_bekleyen_icerik": 25,
                },
                "sistem_performansi": {
                    "ortalama_yanit_suresi": "120ms",
                    "uptime": "99.8%",
                    "aktif_oturum": 340,
                },
                "son_aktiviteler": await self._son_aktiviteler_getir(),
            }

            return istatistikler

        except Exception as e:
            print(f"Dashboard istatistikleri hatası: {str(e)}")
            return {}

    async def _toplam_soru_sayisi(self) -> int:
        """
        Toplam soru sayısını getir
        """
        try:
            istatistikler = await soru_bankasi_servisi.istatistikler_getir()
            return istatistikler.get("toplam_soru_sayisi", 0)
        except Exception:
            return 0

    async def _son_aktiviteler_getir(self) -> List[Dict[str, Any]]:
        """
        Son aktiviteleri getir
        """
        try:
            # Mock aktiviteler
            aktiviteler = [
                {
                    "tip": "kullanici_kayit",
                    "mesaj": "Yeni öğrenci kaydı: Ahmet Yılmaz",
                    "zaman": (datetime.now() - timedelta(minutes=5)).isoformat(),
                },
                {
                    "tip": "soru_ekleme",
                    "mesaj": "Matematik konusuna 5 yeni soru eklendi",
                    "zaman": (datetime.now() - timedelta(minutes=15)).isoformat(),
                },
                {
                    "tip": "sinav_tamamlama",
                    "mesaj": "TYT denemesi tamamlandı: 45 öğrenci",
                    "zaman": (datetime.now() - timedelta(minutes=30)).isoformat(),
                },
            ]

            return aktiviteler

        except Exception:
            return []

    # ==================== İÇERİK YÖNETİMİ ====================

    @admin_required
    async def soru_bankasi_listesi(
        self,
        konu: Optional[str] = None,
        zorluk: Optional[str] = None,
        sinav_tipi: Optional[str] = None,
        sayfa: int = 1,
        sayfa_boyutu: int = 20,
        current_user: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Soru bankası listesi
        """
        try:
            sorular = await soru_bankasi_servisi.sorular_listele(
                sinav_tipi=sinav_tipi,
                konu=konu,
                zorluk_seviyesi=zorluk,
                limit=sayfa_boyutu,
                offset=(sayfa - 1) * sayfa_boyutu,
            )

            # Response formatına dönüştür
            soru_listesi = []
            for soru in sorular:
                soru_dict = {
                    "id": soru.id,
                    "soru_metni": soru.question_text[:200] + "..."
                    if len(soru.question_text) > 200
                    else soru.question_text,
                    "sinav_tipi": str(soru.exam_type),
                    "konu": str(soru.subject_area),
                    "zorluk": soru.difficulty_level.value if soru.difficulty_level else "MEDIUM",
                    "olusturma_tarihi": soru.created_at.isoformat(),
                    "aktif": soru.is_active,
                }
                soru_listesi.append(soru_dict)

            return soru_listesi

        except Exception as e:
            print(f"Soru bankası listesi hatası: {str(e)}")
            return []

    @admin_required
    async def soru_ekle(
        self, soru_data: Dict[str, Any], current_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Soru bankasına yeni soru ekle
        """
        try:
            soru = await soru_bankasi_servisi.soru_ekle(soru_data)

            # Admin aktivitesini kaydet
            await self.admin_aktivite_kaydet(
                current_user,
                "soru_ekle",
                hedef_id=soru.id,
                detaylar={
                    "sinav_tipi": str(soru.exam_type),
                    "konu": str(soru.subject_area),
                },
            )

            return {
                "id": soru.id,
                "soru_metni": soru.question_text,
                "sinav_tipi": str(soru.exam_type),
                "konu": str(soru.subject_area),
                "olusturma_tarihi": soru.created_at.isoformat(),
            }

        except AdminAuthorizationError:
            raise
        except Exception as e:
            raise ValueError(f"Soru ekleme hatası: {str(e)}")

    @admin_required
    async def soru_guncelle(
        self,
        soru_id: str,
        soru_data: Dict[str, Any],
        current_user: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Mevcut soruyu güncelle
        """
        try:
            soru = await soru_bankasi_servisi.soru_guncelle(soru_id, soru_data)

            if not soru:
                return None

            # Admin aktivitesini kaydet
            await self.admin_aktivite_kaydet(
                current_user,
                "soru_guncelle",
                hedef_id=soru_id,
                detaylar={"guncellenen_alanlar": list(soru_data.keys())},
            )

            return {
                "id": soru.id,
                "soru_metni": soru.question_text,
                "guncelleme_tarihi": soru.updated_at.isoformat(),
            }

        except AdminAuthorizationError:
            raise
        except Exception as e:
            raise ValueError(f"Soru güncelleme hatası: {str(e)}")

    @admin_required
    async def soru_sil(self, soru_id: str, current_user: Optional[str] = None) -> bool:
        """
        Soruyu sil
        """
        try:
            sonuc = await soru_bankasi_servisi.soru_sil(soru_id)

            if sonuc:
                # Admin aktivitesini kaydet
                await self.admin_aktivite_kaydet(
                    current_user, "soru_sil", hedef_id=soru_id
                )

            return sonuc

        except AdminAuthorizationError:
            raise
        except Exception as e:
            print(f"Soru silme hatası: {str(e)}")
            return False

    @admin_required
    async def egitim_materyalleri_listesi(
        self,
        tur: Optional[str] = None,
        konu: Optional[str] = None,
        onay_durumu: Optional[str] = None,
        sayfa: int = 1,
        sayfa_boyutu: int = 20,
        current_user: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Eğitim materyalleri listesi
        """
        try:
            # Mock eğitim materyalleri
            materyaller = []

            for i in range(sayfa_boyutu):
                materyal = {
                    "id": str(uuid.uuid4()),
                    "baslik": f"Eğitim Materyali {i+1}",
                    "aciklama": f"Bu bir örnek eğitim materyalidir - {i+1}",
                    "tur": tur or "video",
                    "konu": konu or "Matematik",
                    "onay_durumu": onay_durumu or "onaylandi",
                    "olusturma_tarihi": (
                        datetime.now() - timedelta(days=i)
                    ).isoformat(),
                }
                materyaller.append(materyal)

            return materyaller

        except Exception as e:
            print(f"Eğitim materyalleri listesi hatası: {str(e)}")
            return []

    @admin_required
    async def egitim_materyali_ekle(
        self, materyal_data: Dict[str, Any], current_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Yeni eğitim materyali ekle
        """
        try:
            # Mock implementasyon
            materyal = {
                "id": str(uuid.uuid4()),
                "baslik": materyal_data["baslik"],
                "tur": materyal_data["tur"],
                "konu": materyal_data["konu"],
                "olusturma_tarihi": datetime.now().isoformat(),
            }

            # Admin aktivitesini kaydet
            await self.admin_aktivite_kaydet(
                current_user,
                "egitim_materyali_ekle",
                hedef_id=materyal["id"],
                detaylar={
                    "baslik": materyal_data["baslik"],
                    "tur": materyal_data["tur"],
                },
            )

            return materyal

        except AdminAuthorizationError:
            raise
        except Exception as e:
            raise ValueError(f"Eğitim materyali ekleme hatası: {str(e)}")

    @admin_required
    async def egitim_materyali_guncelle(
        self,
        materyal_id: str,
        materyal_data: Dict[str, Any],
        current_user: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Eğitim materyalini güncelle
        """
        try:
            # Mock implementasyon
            materyal = {
                "id": materyal_id,
                "baslik": materyal_data.get("baslik", "Güncellenmiş Materyal"),
                "guncelleme_tarihi": datetime.now().isoformat(),
            }

            return materyal

        except Exception as e:
            raise ValueError(f"Eğitim materyali güncelleme hatası: {str(e)}")

    @admin_required
    async def egitim_materyali_sil(
        self, materyal_id: str, current_user: Optional[str] = None
    ) -> bool:
        """
        Eğitim materyalini sil
        """
        try:
            # Mock implementasyon
            return True
        except Exception as e:
            print(f"Eğitim materyali silme hatası: {str(e)}")
            return False

    @admin_required
    async def egitim_materyali_onay_durumu_guncelle(
        self,
        materyal_id: str,
        onay_data: Dict[str, Any],
        current_user: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Eğitim materyali onay durumunu güncelle
        """
        try:
            # Mock implementasyon
            materyal = {
                "id": materyal_id,
                "onay_durumu": onay_data["onay_durumu"],
                "onay_tarihi": datetime.now().isoformat(),
            }

            return materyal

        except Exception as e:
            raise ValueError(f"Onay durumu güncelleme hatası: {str(e)}")

    # ==================== TOPLU İŞLEMLER ====================

    @admin_required
    async def toplu_soru_yukle(
        self, sorular_data: List[Dict[str, Any]], current_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Toplu soru yükleme
        """
        try:
            basarili_sayisi = 0
            basarisiz_sayisi = 0
            hatalar = []

            for i, soru_data in enumerate(sorular_data):
                try:
                    await self.soru_ekle(soru_data, current_user=current_user)
                    basarili_sayisi += 1
                except Exception as e:
                    basarisiz_sayisi += 1
                    hatalar.append(
                        {
                            "sira": i + 1,
                            "hata": str(e),
                            "soru": soru_data.get("soru_metni", "")[:100],
                        }
                    )

            # Admin aktivitesini kaydet
            await self.admin_aktivite_kaydet(
                current_user,
                "toplu_soru_yukle",
                detaylar={
                    "toplam_soru": len(sorular_data),
                    "basarili": basarili_sayisi,
                    "basarisiz": basarisiz_sayisi,
                },
            )

            return {
                "basarili_sayisi": basarili_sayisi,
                "basarisiz_sayisi": basarisiz_sayisi,
                "hatalar": hatalar,
            }

        except AdminAuthorizationError:
            raise
        except Exception as e:
            raise Exception(f"Toplu soru yükleme hatası: {str(e)}")

    @admin_required
    async def icerik_ara(
        self,
        arama_terimi: str,
        tur: Optional[str] = None,
        sayfa: int = 1,
        sayfa_boyutu: int = 20,
        current_user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        İçerik arama
        """
        try:
            # Mock arama sonuçları
            sonuclar = []

            for i in range(min(10, sayfa_boyutu)):
                sonuc = {
                    "id": str(uuid.uuid4()),
                    "tip": tur or ("soru" if i % 2 == 0 else "egitim_materyali"),
                    "baslik": f"'{arama_terimi}' ile ilgili içerik {i+1}",
                    "aciklama": f"Bu içerik '{arama_terimi}' arama terimiyle eşleşiyor",
                    "relevans_skoru": 0.9 - (i * 0.1),
                }
                sonuclar.append(sonuc)

            return {
                "sonuclar": sonuclar,
                "toplam_sonuc": len(sonuclar),
                "arama_terimi": arama_terimi,
            }

        except Exception as e:
            print(f"İçerik arama hatası: {str(e)}")
            return {"sonuclar": [], "toplam_sonuc": 0, "arama_terimi": arama_terimi}


# Global servis instance'ı
admin_servisi = AdminService()
