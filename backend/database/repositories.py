"""
Repository Pattern Implementation
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu

Bu dosya tüm database işlemleri için repository pattern implementasyonu içerir.
Her model için CRUD operasyonları ve özel sorgular burada tanımlanır.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import all models from models_backup to avoid circular dependency
from .models_backup import (
    AgentPerformansMetrikleri,
    EgitimIcerigi,
    Kullanici,
    KullaniciRolu,
    KulturelBaglamProfili,
    MaarifDegerleriProfili,
    OgrenciProfili,
    OgrenmeOturumu,
    OgrenmeStili,
    OgrenmeStiliProfili,
    Sinav,
    SinavCevabi,
    SinavSablonu,
    SinavSonucu,
    SinavTipi,
    SistemMetrikleri,
    SoruBankasi,
    ZorlukSeviyesi,
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Temel repository sınıfı"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def commit(self):
        """Transaction'ı commit et"""
        await self.session.commit()

    async def rollback(self):
        """Transaction'ı rollback et"""
        await self.session.rollback()


class KullaniciRepository(BaseRepository):
    """Kullanıcı repository"""

    async def create_kullanici(self, kullanici_data: dict) -> Kullanici:
        """Yeni kullanıcı oluştur"""
        kullanici = Kullanici(**kullanici_data)
        self.session.add(kullanici)
        await self.session.flush()
        await self.session.refresh(kullanici)
        return kullanici

    async def get_by_email(self, email: str) -> Kullanici | None:
        """Email ile kullanıcı bul"""
        result = await self.session.execute(
            select(Kullanici).where(Kullanici.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, kullanici_id: str) -> Kullanici | None:
        """ID ile kullanıcı bul"""
        result = await self.session.execute(
            select(Kullanici)
            .options(
                selectinload(Kullanici.ogrenci_profili),
                selectinload(Kullanici.ogretmen_profili),
                selectinload(Kullanici.veli_profili),
            )
            .where(Kullanici.kullanici_id == kullanici_id)
        )
        return result.scalar_one_or_none()

    async def update_son_giris(self, kullanici_id: str):
        """Son giriş zamanını güncelle"""
        await self.session.execute(
            update(Kullanici)
            .where(Kullanici.kullanici_id == kullanici_id)
            .values(son_giris=datetime.now())
        )

    async def get_kullanicilar_by_rol(self, rol: KullaniciRolu) -> list[Kullanici]:
        """Role göre kullanıcıları getir"""
        result = await self.session.execute(
            select(Kullanici).where(Kullanici.rol == rol)
        )
        return result.scalars().all()


class OgrenciRepository(BaseRepository):
    """Öğrenci repository"""

    async def create_ogrenci_profili(self, profil_data: dict) -> OgrenciProfili:
        """Öğrenci profili oluştur"""
        profil = OgrenciProfili(**profil_data)
        self.session.add(profil)
        await self.session.flush()
        await self.session.refresh(profil)
        return profil

    async def get_by_kullanici_id(self, kullanici_id: str) -> OgrenciProfili | None:
        """Kullanıcı ID ile öğrenci profili bul"""
        result = await self.session.execute(
            select(OgrenciProfili)
            .options(selectinload(OgrenciProfili.kullanici))
            .where(OgrenciProfili.kullanici_id == kullanici_id)
        )
        return result.scalar_one_or_none()

    async def get_by_profil_id(self, profil_id: str) -> OgrenciProfili | None:
        """Profil ID ile öğrenci bul"""
        result = await self.session.execute(
            select(OgrenciProfili)
            .options(
                selectinload(OgrenciProfili.kullanici),
                selectinload(OgrenciProfili.sinav_sonuclari),
                selectinload(OgrenciProfili.ogrenme_oturumlari),
            )
            .where(OgrenciProfili.profil_id == profil_id)
        )
        return result.scalar_one_or_none()

    async def update_mevcut_seviye(self, profil_id: str, yeni_seviye: float):
        """Öğrencinin mevcut seviyesini güncelle"""
        await self.session.execute(
            update(OgrenciProfili)
            .where(OgrenciProfili.profil_id == profil_id)
            .values(mevcut_seviye=yeni_seviye, guncelleme_tarihi=datetime.now())
        )

    async def get_ogrenciler_by_sinif(self, sinif: int) -> list[OgrenciProfili]:
        """Sınıfa göre öğrencileri getir"""
        result = await self.session.execute(
            select(OgrenciProfili)
            .options(selectinload(OgrenciProfili.kullanici))
            .where(OgrenciProfili.sinif == sinif)
        )
        return result.scalars().all()


class SinavRepository(BaseRepository):
    """Sınav repository"""

    async def create_sinav_sablonu(self, sablon_data: dict) -> SinavSablonu:
        """Sınav şablonu oluştur"""
        sablon = SinavSablonu(**sablon_data)
        self.session.add(sablon)
        await self.session.flush()
        await self.session.refresh(sablon)
        return sablon

    async def get_sablon_by_tip(self, tip: SinavTipi) -> list[SinavSablonu]:
        """Tipe göre sınav şablonlarını getir"""
        result = await self.session.execute(
            select(SinavSablonu).where(
                and_(SinavSablonu.tip == tip, SinavSablonu.aktif == True)
            )
        )
        return result.scalars().all()

    async def create_sinav(self, sinav_data: dict) -> Sinav:
        """Yeni sınav oturumu oluştur"""
        sinav = Sinav(**sinav_data)
        self.session.add(sinav)
        await self.session.flush()
        await self.session.refresh(sinav)
        return sinav

    async def get_sinav_by_id(self, sinav_id: str) -> Sinav | None:
        """Sınav ID ile sınav bul"""
        result = await self.session.execute(
            select(Sinav)
            .options(
                selectinload(Sinav.sablon),
                selectinload(Sinav.cevaplar),
                selectinload(Sinav.sonuc),
            )
            .where(Sinav.sinav_id == sinav_id)
        )
        return result.scalar_one_or_none()

    async def get_aktif_sinavlar(self, ogrenci_id: str) -> list[Sinav]:
        """Öğrencinin aktif sınavlarını getir"""
        result = await self.session.execute(
            select(Sinav)
            .options(selectinload(Sinav.sablon))
            .where(and_(Sinav.ogrenci_id == ogrenci_id, Sinav.durum == "devam_ediyor"))
        )
        return result.scalars().all()

    async def update_sinav_durumu(
        self, sinav_id: str, durum: str, bitis_zamani: datetime = None
    ):
        """Sınav durumunu güncelle"""
        update_data = {"durum": durum}
        if bitis_zamani:
            update_data["bitis_zamani"] = bitis_zamani

        await self.session.execute(
            update(Sinav).where(Sinav.sinav_id == sinav_id).values(**update_data)
        )

    async def get_sinav_gecmisi(self, ogrenci_id: str, limit: int = 10) -> list[Sinav]:
        """Öğrencinin sınav geçmişini getir"""
        result = await self.session.execute(
            select(Sinav)
            .options(selectinload(Sinav.sablon), selectinload(Sinav.sonuc))
            .where(Sinav.ogrenci_id == ogrenci_id)
            .order_by(Sinav.baslangic_zamani.desc())
            .limit(limit)
        )
        return result.scalars().all()


class SoruRepository(BaseRepository):
    """Soru bankası repository"""

    async def create_soru(self, soru_data: dict) -> SoruBankasi:
        """Yeni soru oluştur"""
        soru = SoruBankasi(**soru_data)
        self.session.add(soru)
        await self.session.flush()
        await self.session.refresh(soru)
        return soru

    async def get_sorular_by_konu(
        self,
        konu: str,
        zorluk_seviyesi: ZorlukSeviyesi | None = None,
        limit: int = 50,
    ) -> list[SoruBankasi]:
        """Konuya göre soruları getir"""
        query = select(SoruBankasi).where(
            and_(SoruBankasi.konu == konu, SoruBankasi.aktif == True)
        )

        if zorluk_seviyesi:
            query = query.where(SoruBankasi.zorluk_seviyesi == zorluk_seviyesi)

        query = query.limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_rastgele_sorular(
        self,
        konu_dagilimi: dict[str, int],
        zorluk_seviyesi: ZorlukSeviyesi | None = None,
    ) -> list[SoruBankasi]:
        """Konu dağılımına göre rastgele sorular getir"""
        sorular = []

        for konu, sayi in konu_dagilimi.items():
            dialect = self.session.bind.dialect.name if self.session.bind else "sqlite"
            if dialect == "postgresql":
                query = select(SoruBankasi).tablesample(func.bernoulli(20)).where(
                    and_(SoruBankasi.konu == konu, SoruBankasi.aktif == True)
                )
            else:
                query = select(SoruBankasi).where(
                    and_(SoruBankasi.konu == konu, SoruBankasi.aktif == True)
                )

            if zorluk_seviyesi:
                query = query.where(SoruBankasi.zorluk_seviyesi == zorluk_seviyesi)

            if dialect == "postgresql":
                query = query.limit(sayi)
                result = await self.session.execute(query)
                rows = result.scalars().all()
                if len(rows) < sayi:
                    fallback_query = select(SoruBankasi).where(
                        and_(SoruBankasi.konu == konu, SoruBankasi.aktif == True)
                    )
                    if zorluk_seviyesi:
                        fallback_query = fallback_query.where(SoruBankasi.zorluk_seviyesi == zorluk_seviyesi)
                    fallback_query = fallback_query.limit(sayi)
                    result = await self.session.execute(fallback_query)
                    rows = result.scalars().all()
                sorular.extend(rows)
            else:
                query = query.order_by(func.random()).limit(sayi)
                result = await self.session.execute(query)
                sorular.extend(result.scalars().all())

        return sorular

    async def get_soru_by_id(self, soru_id: str) -> SoruBankasi | None:
        """Soru ID ile soru bul"""
        result = await self.session.execute(
            select(SoruBankasi).where(SoruBankasi.soru_id == soru_id)
        )
        return result.scalar_one_or_none()

    async def update_irt_parametreleri(
        self, soru_id: str, a_param: float, b_param: float, c_param: float
    ):
        """Sorunun IRT parametrelerini güncelle"""
        await self.session.execute(
            update(SoruBankasi)
            .where(SoruBankasi.soru_id == soru_id)
            .values(
                irt_a_parametresi=a_param,
                irt_b_parametresi=b_param,
                irt_c_parametresi=c_param,
            )
        )


class SinavCevabiRepository(BaseRepository):
    """Sınav cevabı repository"""

    async def create_cevap(self, cevap_data: dict) -> SinavCevabi:
        """Sınav cevabı kaydet"""
        cevap = SinavCevabi(**cevap_data)
        self.session.add(cevap)
        await self.session.flush()
        await self.session.refresh(cevap)
        return cevap

    async def get_cevaplar_by_sinav(self, sinav_id: str) -> list[SinavCevabi]:
        """Sınava ait tüm cevapları getir"""
        result = await self.session.execute(
            select(SinavCevabi)
            .options(selectinload(SinavCevabi.soru))
            .where(SinavCevabi.sinav_id == sinav_id)
            .order_by(SinavCevabi.cevaplama_zamani)
        )
        return result.scalars().all()

    async def update_cevap(self, cevap_id: str, yeni_cevap: str, dogru_mu: bool):
        """Cevabı güncelle"""
        await self.session.execute(
            update(SinavCevabi)
            .where(SinavCevabi.cevap_id == cevap_id)
            .values(verilen_cevap=yeni_cevap, dogru_mu=dogru_mu)
        )


class SinavSonucuRepository(BaseRepository):
    """Sınav sonucu repository"""

    async def create_sonuc(self, sonuc_data: dict) -> SinavSonucu:
        """Sınav sonucu oluştur"""
        sonuc = SinavSonucu(**sonuc_data)
        self.session.add(sonuc)
        await self.session.flush()
        await self.session.refresh(sonuc)
        return sonuc

    async def get_sonuc_by_sinav(self, sinav_id: str) -> SinavSonucu | None:
        """Sınav ID ile sonuç bul"""
        result = await self.session.execute(
            select(SinavSonucu).where(SinavSonucu.sinav_id == sinav_id)
        )
        return result.scalar_one_or_none()

    async def get_ogrenci_sonuclari(
        self, ogrenci_id: str, limit: int = 10
    ) -> list[SinavSonucu]:
        """Öğrencinin sınav sonuçlarını getir"""
        result = await self.session.execute(
            select(SinavSonucu)
            .options(selectinload(SinavSonucu.sinav))
            .where(SinavSonucu.ogrenci_id == ogrenci_id)
            .order_by(SinavSonucu.hesaplama_tarihi.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_performans_trendi(
        self, ogrenci_id: str, gun_sayisi: int = 30
    ) -> list[SinavSonucu]:
        """Öğrencinin performans trendini getir"""
        baslangic_tarihi = datetime.now() - timedelta(days=gun_sayisi)

        result = await self.session.execute(
            select(SinavSonucu)
            .where(
                and_(
                    SinavSonucu.ogrenci_id == ogrenci_id,
                    SinavSonucu.hesaplama_tarihi >= baslangic_tarihi,
                )
            )
            .order_by(SinavSonucu.hesaplama_tarihi)
        )
        return result.scalars().all()


class OgrenmeStiliRepository(BaseRepository):
    """Öğrenme stili repository"""

    async def create_profil(self, profil_data: dict) -> OgrenmeStiliProfili:
        """Öğrenme stili profili oluştur"""
        profil = OgrenmeStiliProfili(**profil_data)
        self.session.add(profil)
        await self.session.flush()
        await self.session.refresh(profil)
        return profil

    async def get_by_ogrenci_id(self, ogrenci_id: str) -> OgrenmeStiliProfili | None:
        """Öğrenci ID ile öğrenme stili profili bul"""
        result = await self.session.execute(
            select(OgrenmeStiliProfili).where(
                OgrenmeStiliProfili.ogrenci_id == ogrenci_id
            )
        )
        return result.scalar_one_or_none()

    async def update_profil(self, profil_id: str, update_data: dict):
        """Öğrenme stili profilini güncelle"""
        update_data["son_guncelleme"] = datetime.now()
        await self.session.execute(
            update(OgrenmeStiliProfili)
            .where(OgrenmeStiliProfili.profil_id == profil_id)
            .values(**update_data)
        )


class KulturelBaglamRepository(BaseRepository):
    """Kültürel bağlam repository"""

    async def create_profil(self, profil_data: dict) -> KulturelBaglamProfili:
        """Kültürel bağlam profili oluştur"""
        profil = KulturelBaglamProfili(**profil_data)
        self.session.add(profil)
        await self.session.flush()
        await self.session.refresh(profil)
        return profil

    async def get_by_ogrenci_id(
        self, ogrenci_id: str
    ) -> KulturelBaglamProfili | None:
        """Öğrenci ID ile kültürel bağlam profili bul"""
        result = await self.session.execute(
            select(KulturelBaglamProfili).where(
                KulturelBaglamProfili.ogrenci_id == ogrenci_id
            )
        )
        return result.scalar_one_or_none()


class MaarifDegerleriRepository(BaseRepository):
    """MEB Maarif değerleri repository"""

    async def create_profil(self, profil_data: dict) -> MaarifDegerleriProfili:
        """Maarif değerleri profili oluştur"""
        profil = MaarifDegerleriProfili(**profil_data)
        self.session.add(profil)
        await self.session.flush()
        await self.session.refresh(profil)
        return profil

    async def get_by_ogrenci_id(
        self, ogrenci_id: str
    ) -> MaarifDegerleriProfili | None:
        """Öğrenci ID ile Maarif değerleri profili bul"""
        result = await self.session.execute(
            select(MaarifDegerleriProfili).where(
                MaarifDegerleriProfili.ogrenci_id == ogrenci_id
            )
        )
        return result.scalar_one_or_none()


class OgrenmeOturumuRepository(BaseRepository):
    """Öğrenme oturumu repository"""

    async def create_oturum(self, oturum_data: dict) -> OgrenmeOturumu:
        """Öğrenme oturumu oluştur"""
        oturum = OgrenmeOturumu(**oturum_data)
        self.session.add(oturum)
        await self.session.flush()
        await self.session.refresh(oturum)
        return oturum

    async def get_oturum_by_id(self, oturum_id: str) -> OgrenmeOturumu | None:
        """Oturum ID ile öğrenme oturumu bul"""
        result = await self.session.execute(
            select(OgrenmeOturumu).where(OgrenmeOturumu.oturum_id == oturum_id)
        )
        return result.scalar_one_or_none()

    async def get_ogrenci_oturumlari(
        self, ogrenci_id: str, limit: int = 50
    ) -> list[OgrenmeOturumu]:
        """Öğrencinin öğrenme oturumlarını getir"""
        result = await self.session.execute(
            select(OgrenmeOturumu)
            .where(OgrenmeOturumu.ogrenci_id == ogrenci_id)
            .order_by(OgrenmeOturumu.baslangic_zamani.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def update_oturum_bitis(
        self, oturum_id: str, bitis_zamani: datetime, performans_data: dict
    ):
        """Öğrenme oturumunu bitir ve performans verilerini güncelle"""
        sure_dakika = int((bitis_zamani - datetime.now()).total_seconds() / 60)

        update_data = {
            "bitis_zamani": bitis_zamani,
            "sure_dakika": sure_dakika,
            **performans_data,
        }

        await self.session.execute(
            update(OgrenmeOturumu)
            .where(OgrenmeOturumu.oturum_id == oturum_id)
            .values(**update_data)
        )


class EgitimIcerigiRepository(BaseRepository):
    """Eğitim içeriği repository"""

    async def create_icerik(self, icerik_data: dict) -> EgitimIcerigi:
        """Eğitim içeriği oluştur"""
        icerik = EgitimIcerigi(**icerik_data)
        self.session.add(icerik)
        await self.session.flush()
        await self.session.refresh(icerik)
        return icerik

    async def get_icerikler_by_konu(
        self,
        konu: str,
        icerik_tipi: str | None = None,
        zorluk_seviyesi: ZorlukSeviyesi | None = None,
        limit: int = 20,
    ) -> list[EgitimIcerigi]:
        """Konuya göre eğitim içeriklerini getir"""
        query = select(EgitimIcerigi).where(
            and_(EgitimIcerigi.konu == konu, EgitimIcerigi.aktif == True)
        )

        if icerik_tipi:
            query = query.where(EgitimIcerigi.icerik_tipi == icerik_tipi)

        if zorluk_seviyesi:
            query = query.where(EgitimIcerigi.zorluk_seviyesi == zorluk_seviyesi)

        query = query.order_by(EgitimIcerigi.kalite_skoru.desc()).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_kisisellestirilmis_icerikler(
        self, ogrenci_id: str, konu: str, ogrenme_stili: OgrenmeStili, limit: int = 10
    ) -> list[EgitimIcerigi]:
        """Öğrenciye kişiselleştirilmiş içerikler getir"""
        # Öğrenme stiline göre içerik tipi belirleme
        icerik_tipleri = {
            OgrenmeStili.VISUAL: ["video", "interaktif"],
            OgrenmeStili.AUDITORY: ["video", "podcast"],
            OgrenmeStili.READING: ["metin", "pdf"],
            OgrenmeStili.KINESTHETIC: ["interaktif", "simulasyon"],
            OgrenmeStili.MIXED: ["video", "metin", "interaktif"],
        }

        tercih_edilen_tipler = icerik_tipleri.get(ogrenme_stili, ["video", "metin"])

        query = (
            select(EgitimIcerigi)
            .where(
                and_(
                    EgitimIcerigi.konu == konu,
                    EgitimIcerigi.icerik_tipi.in_(tercih_edilen_tipler),
                    EgitimIcerigi.aktif == True,
                )
            )
            .order_by(
                EgitimIcerigi.kalite_skoru.desc(),
                EgitimIcerigi.maarif_uyum_skoru.desc(),
            )
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()


class MetrikRepository(BaseRepository):
    """Sistem ve agent metrikleri repository"""

    async def create_sistem_metrik(self, metrik_data: dict) -> SistemMetrikleri:
        """Sistem metriği kaydet"""
        metrik = SistemMetrikleri(**metrik_data)
        self.session.add(metrik)
        await self.session.flush()
        await self.session.refresh(metrik)
        return metrik

    async def create_agent_metrik(self, metrik_data: dict) -> AgentPerformansMetrikleri:
        """Agent performans metriği kaydet"""
        metrik = AgentPerformansMetrikleri(**metrik_data)
        self.session.add(metrik)
        await self.session.flush()
        await self.session.refresh(metrik)
        return metrik

    async def get_sistem_metrikleri(
        self, kategori: str | None = None, son_saat: int = 24
    ) -> list[SistemMetrikleri]:
        """Sistem metriklerini getir"""
        baslangic_zamani = datetime.now() - timedelta(hours=son_saat)

        query = select(SistemMetrikleri).where(
            SistemMetrikleri.kayit_zamani >= baslangic_zamani
        )

        if kategori:
            query = query.where(SistemMetrikleri.kategori == kategori)

        query = query.order_by(SistemMetrikleri.kayit_zamani.desc())
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_agent_performans_metrikleri(
        self, agent_adi: str | None = None, son_saat: int = 24
    ) -> list[AgentPerformansMetrikleri]:
        """Agent performans metriklerini getir"""
        baslangic_zamani = datetime.now() - timedelta(hours=son_saat)

        query = select(AgentPerformansMetrikleri).where(
            AgentPerformansMetrikleri.kayit_zamani >= baslangic_zamani
        )

        if agent_adi:
            query = query.where(AgentPerformansMetrikleri.agent_adi == agent_adi)

        query = query.order_by(AgentPerformansMetrikleri.kayit_zamani.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
