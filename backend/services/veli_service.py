"""
Veli takip sistemi servisi
TIMEZONE FIX: Using timezone-aware datetime
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from models.dashboard import Bildirim
from services.user_service import kullanici_servisi


class VeliRaporu(BaseModel):
    """Veli için haftalık rapor modeli"""

    rapor_id: str = Field(..., description="Rapor ID")
    ogrenci_id: str = Field(..., description="Öğrenci ID")
    ogrenci_ad_soyad: str = Field(..., description="Öğrenci adı soyadı")
    rapor_donemi: str = Field(..., description="Rapor dönemi")
    baslangic_tarihi: datetime = Field(..., description="Dönem başlangıç tarihi")
    bitis_tarihi: datetime = Field(..., description="Dönem bitiş tarihi")

    # Genel İstatistikler
    toplam_calisma_suresi: int = Field(
        ..., description="Toplam çalışma süresi (dakika)"
    )
    tamamlanan_sinav_sayisi: int = Field(..., description="Tamamlanan sınav sayısı")
    ortalama_basari_orani: float = Field(..., description="Ortalama başarı oranı (%)")

    # Performans Verileri
    en_basarili_konular: list[str] = Field(
        default_factory=list, description="En başarılı konular"
    )
    gelisim_gereken_konular: list[str] = Field(
        default_factory=list, description="Gelişim gereken konular"
    )
    haftalik_ilerleme: str = Field(..., description="Haftalık ilerleme durumu")

    # Öneriler
    veli_onerileri: list[str] = Field(
        default_factory=list, description="Veli için öneriler"
    )
    destek_alanlari: list[str] = Field(
        default_factory=list, description="Destek alınması gereken alanlar"
    )

    # Meta Veriler
    olusturma_tarihi: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class VeliOnayTalebi(BaseModel):
    """Veli onay talebi modeli"""

    talep_id: str = Field(..., description="Talep ID")
    ogrenci_id: str = Field(..., description="Öğrenci ID")
    veli_id: str = Field(..., description="Veli ID")
    talep_tipi: str = Field(..., description="Talep türü")
    talep_aciklamasi: str = Field(..., description="Talep açıklaması")
    durum: str = Field("beklemede", description="Onay durumu")
    talep_tarihi: datetime = Field(default_factory=lambda: datetime.now(UTC))
    yanit_tarihi: datetime | None = Field(None, description="Yanıt tarihi")
    veli_notu: str | None = Field(None, description="Veli notu")

    model_config = ConfigDict(from_attributes=True)


class VeliServisi:
    """Veli takip sistemi servisi"""

    def __init__(self) -> None:
        """Veli takip servisini başlatır."""
        # In-memory veri saklama (production'da database kullanılacak)
        self.veli_raporlari: dict[str, VeliRaporu] = {}
        self.veli_onay_talepleri: dict[str, VeliOnayTalebi] = {}
        self.veli_bildirimleri: dict[str, list[Bildirim]] = {}
        self.cocuk_performans_verileri: dict[str, dict[str, Any]] = {}

    async def veli_cocuklarini_getir(self, veli_id: str) -> list[dict[str, Any]]:
        """Velinin cocuklarinin listesini DB'den getir (SQLAlchemy session)"""
        from sqlalchemy import text

        from core.database import get_db_session_context

        _ALLOWED_NAME_COLS = {"ad_soyad", "full_name", "name"}

        try:
            async with get_db_session_context() as session:
                # 1) Veli kullanicisinin DB'de var oldugunu dogrula
                veli_row = await session.execute(
                    text("SELECT id FROM users WHERE id = :veli_id"),
                    {"veli_id": veli_id},
                )
                if not veli_row.first():
                    raise ValueError("Veli profili bulunamadi")

                # 2) parent_student_links tablosu var mi?
                links_exist = await session.execute(
                    text(
                        "SELECT EXISTS("
                        "  SELECT 1 FROM information_schema.tables"
                        "  WHERE table_schema='public'"
                        "    AND table_name='parent_student_links'"
                        ")"
                    )
                )
                if not links_exist.scalar():
                    return []

                # 3) ad_soyad kolonunu esnek bul (whitelist ile)
                col_result = await session.execute(
                    text(
                        "SELECT column_name"
                        " FROM information_schema.columns"
                        " WHERE table_name='users'"
                        "   AND column_name IN ('ad_soyad','full_name','name')"
                        " LIMIT 1"
                    )
                )
                name_col = col_result.scalar()
                name_expr = name_col if name_col in _ALLOWED_NAME_COLS else "email"

                # 4) Ana sorgu (name_expr whitelist'ten — SQL injection riski yok)
                rows = await session.execute(
                    text(
                        f"SELECT u.id::text AS ogrenci_id,"
                        f" u.{name_expr} AS ad_soyad,"
                        f" u.email, u.created_at AS son_giris"
                        f" FROM parent_student_links psl"
                        f" JOIN users u ON u.id = psl.student_id"
                        f" WHERE psl.parent_id = :veli_id"
                    ),
                    {"veli_id": veli_id},
                )
                return [
                    {
                        "ogrenci_id": r.ogrenci_id,
                        "ad_soyad": r.ad_soyad or r.email,
                        "sinif_seviyesi": None,
                        "okul_adi": None,
                        "hedef_sinav": "TYT/AYT",
                        "veli_onay": True,
                        "son_giris": r.son_giris,
                    }
                    for r in rows
                ]

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Cocuk listesi alinirken hata: {e!s}")

    async def cocuk_performansini_getir(
        self, veli_id: str, ogrenci_id: str
    ) -> dict[str, Any]:
        """Belirli bir çocuğun performans verilerini getir"""
        # CRITICAL SECURITY FIX: This function was returning 100% FRAUDULENT DATA to parents!
        # DISABLED until real database implementation is completed
        # Previous behavior: Returned fake performance data (fake study hours, fake exam scores)
        # This is an ETHICAL VIOLATION and LEGAL LIABILITY
        raise NotImplementedError(
            "Performans verisi henüz gerçek veritabanı ile entegre edilmedi. "
            "Mock veri döndürülmesi etik ihlal olduğu için bu özellik devre dışı bırakılmıştır. "
            "Lütfen gerçek database entegrasyonunu tamamlayın."
        )

    async def haftalik_rapor_olustur(self, veli_id: str, ogrenci_id: str) -> VeliRaporu:
        """Haftalık veli raporu oluştur"""
        # CRITICAL SECURITY FIX: This function was returning 100% HARDCODED FAKE DATA to parents!
        # DISABLED until real database implementation is completed
        # Previous behavior:
        #   - toplam_calisma_suresi=420 (FAKE: always 7 hours)
        #   - tamamlanan_sinav_sayisi=3 (FAKE: always 3 exams)
        #   - ortalama_basari_orani=78.5 (FAKE: always 78.5%)
        #   - All topics, recommendations hardcoded
        # This is an ETHICAL VIOLATION and LEGAL LIABILITY
        raise NotImplementedError(
            "Haftalık rapor özelliği henüz gerçek veritabanı ile entegre edilmedi. "
            "Hardcoded sahte veri döndürülmesi etik ihlal olduğu için bu özellik devre dışı bırakılmıştır. "
            "Lütfen gerçek database entegrasyonunu tamamlayın."
        )

    async def onay_talebi_olustur(
        self, ogrenci_id: str, talep_tipi: str, aciklama: str
    ) -> VeliOnayTalebi:
        """Veli onay talebi oluştur"""
        try:
            # Öğrenci profilini getir
            ogrenci_profili = await kullanici_servisi.ogrenci_profili_getir(ogrenci_id)
            if not ogrenci_profili or not ogrenci_profili.veli_kullanici_id:
                raise ValueError("Öğrenci profili veya veli bilgisi bulunamadı")

            # Talep ID oluştur
            talep_id = str(uuid.uuid4())

            # Onay talebi oluştur
            talep = VeliOnayTalebi(
                talep_id=talep_id,
                ogrenci_id=ogrenci_id,
                veli_id=ogrenci_profili.veli_kullanici_id,
                talep_tipi=talep_tipi,
                talep_aciklamasi=aciklama,
            )

            # Talebi kaydet
            self.veli_onay_talepleri[talep_id] = talep

            # Veliye bildirim gönder
            await self._veli_bildirimi_gonder(
                ogrenci_profili.veli_kullanici_id,
                "Onay Talebi",
                f"Çocuğunuz için yeni bir onay talebi: {talep_tipi}",
                "uyari",
            )

            return talep

        except Exception as e:
            raise ValueError(f"Onay talebi oluşturulurken hata: {e!s}")

    async def onay_talebi_yanitla(
        self, veli_id: str, talep_id: str, onay: bool, not_: str | None = None
    ) -> VeliOnayTalebi:
        """Veli onay talebini yanıtla"""
        try:
            # Talep kontrolü
            if talep_id not in self.veli_onay_talepleri:
                raise ValueError("Onay talebi bulunamadı")

            talep = self.veli_onay_talepleri[talep_id]

            # Veli yetkisi kontrolü
            if talep.veli_id != veli_id:
                raise ValueError("Bu talebi yanıtlama yetkiniz yok")

            # Talebi güncelle
            talep.durum = "onaylandi" if onay else "reddedildi"
            talep.yanit_tarihi = datetime.now()
            talep.veli_notu = not_

            # Öğrenciye bildirim gönder
            await self._ogrenci_bildirimi_gonder(
                talep.ogrenci_id,
                "Onay Yanıtı",
                f"Veli onay talebiniz {talep.durum}",
                "bilgi" if onay else "uyari",
            )

            return talep

        except Exception as e:
            raise ValueError(f"Onay talebi yanıtlanırken hata: {e!s}")

    async def veli_bildirimlerini_getir(self, veli_id: str) -> list[Bildirim]:
        """Velinin bildirimlerini getir"""
        return self.veli_bildirimleri.get(veli_id, [])

    async def bildirim_okundu_isaretle(self, veli_id: str, bildirim_id: str) -> bool:
        """Bildirimi okundu olarak işaretle"""
        try:
            bildirimler = self.veli_bildirimleri.get(veli_id, [])
            for bildirim in bildirimler:
                if bildirim.bildirim_id == bildirim_id:
                    bildirim.okundu = True
                    return True
            return False
        except Exception:
            return False

    async def _veli_yetki_kontrolu(self, veli_id: str, ogrenci_id: str) -> bool:
        """Velinin öğrenci üzerinde yetkisi olup olmadığını kontrol et"""
        veli_profili = await kullanici_servisi.veli_profili_getir(veli_id)
        if not veli_profili:
            raise ValueError("Veli profili bulunamadı")

        if ogrenci_id not in veli_profili.cocuk_ogrenci_ids:
            raise ValueError("Bu öğrenci üzerinde yetkiniz yok")

        return True

    async def _mock_performans_verisi_olustur(self, ogrenci_id: str) -> dict[str, Any]:
        """
        DEPRECATED AND DISABLED: This function was generating 100% FRAUDULENT DATA!

        Previous fraudulent behavior:
        - toplam_calisma_suresi: 1800 (FAKE: always 30 hours)
        - tamamlanan_sinav_sayisi: 12 (FAKE: always 12 exams)
        - ortalama_basari_orani: 76.3 (FAKE: always 76.3%)
        - All subject scores, trends, recommendations were HARDCODED LIES

        This function has been PERMANENTLY DISABLED as it constitutes:
        1. ETHICAL VIOLATION - Lying to parents about their children's performance
        2. LEGAL LIABILITY - Fraudulent misrepresentation
        3. KVKK/GDPR VIOLATION - Processing fake personal data

        DO NOT RE-ENABLE THIS FUNCTION. Implement real database queries instead.
        """
        raise NotImplementedError(
            "FRAUDULENT DATA GENERATOR - PERMANENTLY DISABLED. "
            "This function was returning fake performance data to parents. "
            "Implement real database queries instead."
        )

    async def _veli_bildirimi_gonder(
        self, veli_id: str, baslik: str, mesaj: str, tip: str
    ) -> None:
        """Veliye bildirim gönder"""
        bildirim = Bildirim(
            bildirim_id=str(uuid.uuid4()), baslik=baslik, mesaj=mesaj, tip=tip
        )

        if veli_id not in self.veli_bildirimleri:
            self.veli_bildirimleri[veli_id] = []

        self.veli_bildirimleri[veli_id].append(bildirim)

    async def _ogrenci_bildirimi_gonder(
        self, ogrenci_id: str, baslik: str, mesaj: str, tip: str
    ) -> None:
        """Öğrenciye bildirim gönder (öğrenci servisi ile entegre edilecek)"""
        # Bu method öğrenci bildirim servisi ile entegre edilecek


# Global servis instance
veli_servisi = VeliServisi()
