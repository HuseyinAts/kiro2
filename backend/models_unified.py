"""
Unified Database Schema for YKS Hazırlık Platformu
Teknofest 2025 - Birleştirilmiş Veritabanı Modelleri
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    JSON,
    ForeignKey,
    Table,
    UniqueConstraint,
    Index,
    CheckConstraint,
    DECIMAL,
    TIMESTAMP,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid

Base = declarative_base()


# ============= ENUMS =============
class SinavTipi(str, Enum):
    TYT = "TYT"
    AYT = "AYT"
    YDT = "YDT"
    DENEME = "DENEME"


class SinavDurumu(str, Enum):
    HAZIR = "HAZIR"
    DEVAM_EDIYOR = "DEVAM_EDIYOR"
    TAMAMLANDI = "TAMAMLANDI"
    IPTAL = "IPTAL"


class SoruZorluk(str, Enum):
    COK_KOLAY = "COK_KOLAY"
    KOLAY = "KOLAY"
    ORTA = "ORTA"
    ZOR = "ZOR"
    COK_ZOR = "COK_ZOR"


class KullaniciRolu(str, Enum):
    OGRENCI = "OGRENCI"
    OGRETMEN = "OGRETMEN"
    VELI = "VELI"
    ADMIN = "ADMIN"


# ============= ASSOCIATION TABLES =============
ogrenci_veli_association = Table(
    "ogrenci_veli",
    Base.metadata,
    Column("ogrenci_id", UUID(as_uuid=True), ForeignKey("kullanicilar.id")),
    Column("veli_id", UUID(as_uuid=True), ForeignKey("kullanicilar.id")),
)

ogrenci_ogretmen_association = Table(
    "ogrenci_ogretmen",
    Base.metadata,
    Column("ogrenci_id", UUID(as_uuid=True), ForeignKey("kullanicilar.id")),
    Column("ogretmen_id", UUID(as_uuid=True), ForeignKey("kullanicilar.id")),
)


# ============= MAIN MODELS =============
class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad = Column(String(100), nullable=False)
    soyad = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    telefon = Column(String(20))
    rol = Column(String(20), nullable=False, default=KullaniciRolu.OGRENCI)
    parola_hash = Column(String(255), nullable=False)
    aktif = Column(Boolean, default=True)

    # Öğrenci özellikleri
    sinif = Column(Integer)  # 9, 10, 11, 12
    okul = Column(String(255))
    alan = Column(String(50))  # Sayısal, Sözel, Eşit Ağırlık, Dil
    hedef_universite = Column(String(255))
    hedef_bolum = Column(String(255))

    # Timestamps
    kayit_tarihi = Column(TIMESTAMP, default=datetime.utcnow)
    son_giris = Column(TIMESTAMP)
    guncelleme_tarihi = Column(TIMESTAMP, onupdate=datetime.utcnow)

    # Relations
    ogrenme_profili = relationship(
        "OgrenmeProfili", back_populates="kullanici", uselist=False
    )
    sinavlar = relationship("Sinav", back_populates="ogrenci")
    sinav_sonuclari = relationship("SinavSonucu", back_populates="ogrenci")
    cozulen_sorular = relationship("CozulenSoru", back_populates="ogrenci")

    # Many-to-Many relations
    veliler = relationship(
        "Kullanici",
        secondary=ogrenci_veli_association,
        primaryjoin=id == ogrenci_veli_association.c.ogrenci_id,
        secondaryjoin=id == ogrenci_veli_association.c.veli_id,
        backref="ogrenciler",
    )

    ogretmenler = relationship(
        "Kullanici",
        secondary=ogrenci_ogretmen_association,
        primaryjoin=id == ogrenci_ogretmen_association.c.ogrenci_id,
        secondaryjoin=id == ogrenci_ogretmen_association.c.ogretmen_id,
        backref="ogrencileri",
    )

    __table_args__ = (
        Index("idx_kullanici_email", "email"),
        Index("idx_kullanici_rol", "rol"),
    )


class OgrenmeProfili(Base):
    __tablename__ = "ogrenme_profilleri"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kullanici_id = Column(
        UUID(as_uuid=True), ForeignKey("kullanicilar.id"), unique=True
    )

    # VARK profili skorları
    vark_visual = Column(Float, default=0.5)
    vark_auditory = Column(Float, default=0.5)
    vark_reading = Column(Float, default=0.5)
    vark_kinesthetic = Column(Float, default=0.5)

    # Felder-Silverman skorları
    felder_active_reflective = Column(Float, default=0.0)
    felder_sensing_intuitive = Column(Float, default=0.0)
    felder_visual_verbal = Column(Float, default=0.0)
    felder_sequential_global = Column(Float, default=0.0)

    # Hibrit kod (örn: V-ASVS)
    hibrit_kod = Column(String(20))
    dominant_vark = Column(String(20))
    dominant_felder = Column(String(50))

    # Güven metrikleri
    guven_seviyesi = Column(Float, default=0.5)
    tespit_sayisi = Column(Integer, default=0)

    # Kültürel faktörler (Türk öğrenci profili)
    grup_calismasi_tercihi = Column(Float, default=0.5)
    ogretmene_saygi_seviyesi = Column(Float, default=0.7)
    aile_katilim_derecesi = Column(Float, default=0.6)
    akran_rekabet_egilimi = Column(Float, default=0.5)

    # Timestamps
    ilk_tespit_tarihi = Column(TIMESTAMP, default=datetime.utcnow)
    son_guncelleme = Column(TIMESTAMP, onupdate=datetime.utcnow)

    # Davranışsal veriler (JSON)
    davranissal_veriler = Column(JSONB, default={})
    anket_cevaplari = Column(JSONB, default={})

    # Relations
    kullanici = relationship("Kullanici", back_populates="ogrenme_profili")

    __table_args__ = (
        CheckConstraint("guven_seviyesi >= 0 AND guven_seviyesi <= 1"),
        Index("idx_ogrenme_profili_kullanici", "kullanici_id"),
    )


class Soru(Base):
    __tablename__ = "sorular"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kod = Column(String(50), unique=True)

    # Soru içeriği
    metin = Column(Text, nullable=False)
    secenekler = Column(JSONB, nullable=False)  # {"A": "...", "B": "...", ...}
    dogru_cevap = Column(String(1), nullable=False)

    # Kategori bilgileri
    sinav_tipi = Column(String(20), nullable=False)
    konu = Column(String(100), nullable=False)
    alt_konu = Column(String(100))
    kazanim = Column(String(255))

    # IRT parametreleri
    irt_discrimination = Column(Float, default=1.0)  # a parametresi
    irt_difficulty = Column(Float, default=0.0)  # b parametresi
    irt_guessing = Column(Float, default=0.25)  # c parametresi
    irt_upper_asymptote = Column(Float, default=1.0)  # d parametresi

    # Zorluk ve istatistikler
    zorluk = Column(String(20), default=SoruZorluk.ORTA)
    cozulme_sayisi = Column(Integer, default=0)
    dogru_cozulme_sayisi = Column(Integer, default=0)
    ortalama_sure = Column(Float, default=0.0)

    # Morfolojik analiz (Türkçe)
    morfoloji_skoru = Column(Float)
    kelime_sayisi = Column(Integer)
    cumle_karmasikligi = Column(Float)

    # Medya ve görseller
    gorsel_url = Column(String(500))
    video_url = Column(String(500))

    # Metadata
    kaynak = Column(String(100))  # ÖSYM, MEB, vs.
    yil = Column(Integer)
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(TIMESTAMP, default=datetime.utcnow)
    guncelleme_tarihi = Column(TIMESTAMP, onupdate=datetime.utcnow)

    # Relations
    cozumler = relationship("CozulenSoru", back_populates="soru")

    __table_args__ = (
        Index("idx_soru_sinav_tipi", "sinav_tipi"),
        Index("idx_soru_konu", "konu"),
        Index("idx_soru_zorluk", "zorluk"),
        CheckConstraint("irt_discrimination > 0"),
    )


class Sinav(Base):
    __tablename__ = "sinavlar"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kod = Column(String(50), unique=True)
    ogrenci_id = Column(UUID(as_uuid=True), ForeignKey("kullanicilar.id"))

    # Sınav bilgileri
    sinav_tipi = Column(String(20), nullable=False)
    baslik = Column(String(255))
    aciklama = Column(Text)

    # Sınav parametreleri
    toplam_soru = Column(Integer, nullable=False)
    sure_dakika = Column(Integer, nullable=False)
    durum = Column(String(20), default=SinavDurumu.HAZIR)

    # Soru listesi ve cevaplar
    soru_listesi = Column(ARRAY(String))  # Soru ID'leri
    cevaplar = Column(JSONB, default={})  # {"soru_id": "cevap", ...}

    # Zaman bilgileri
    baslama_zamani = Column(TIMESTAMP)
    bitis_zamani = Column(TIMESTAMP)
    kalan_sure = Column(Integer)  # saniye

    # Adaptive parametreler
    hedef_zorluk = Column(Float, default=0.0)
    adaptif_mod = Column(Boolean, default=False)

    # Timestamps
    olusturma_tarihi = Column(TIMESTAMP, default=datetime.utcnow)

    # Relations
    ogrenci = relationship("Kullanici", back_populates="sinavlar")
    sonuc = relationship("SinavSonucu", back_populates="sinav", uselist=False)

    __table_args__ = (
        Index("idx_sinav_ogrenci", "ogrenci_id"),
        Index("idx_sinav_durum", "durum"),
    )


class SinavSonucu(Base):
    __tablename__ = "sinav_sonuclari"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sinav_id = Column(UUID(as_uuid=True), ForeignKey("sinavlar.id"), unique=True)
    ogrenci_id = Column(UUID(as_uuid=True), ForeignKey("kullanicilar.id"))

    # Temel sonuçlar
    dogru_sayisi = Column(Integer, default=0)
    yanlis_sayisi = Column(Integer, default=0)
    bos_sayisi = Column(Integer, default=0)
    net_sayisi = Column(DECIMAL(5, 2))  # Doğru - Yanlış/4
    ham_puan = Column(DECIMAL(5, 2))

    # Performans metrikleri
    basari_yuzdesi = Column(DECIMAL(5, 2))
    siralama = Column(Integer)
    percentile = Column(DECIMAL(5, 2))

    # Konu bazlı performans (JSON)
    konu_performansi = Column(JSONB, default={})

    # Süre analizi
    toplam_sure = Column(Integer)  # saniye
    soru_sureleri = Column(JSONB, default={})  # {"soru_id": süre, ...}

    # IRT skorları
    theta_tahmini = Column(Float)  # Öğrenci yetenek tahmini
    standart_hata = Column(Float)

    # AI analizi
    guclu_konular = Column(ARRAY(String))
    zayif_konular = Column(ARRAY(String))
    oneriler = Column(JSONB, default=[])

    # Timestamps
    tamamlanma_tarihi = Column(TIMESTAMP, default=datetime.utcnow)

    # Relations
    sinav = relationship("Sinav", back_populates="sonuc")
    ogrenci = relationship("Kullanici", back_populates="sinav_sonuclari")

    __table_args__ = (
        Index("idx_sonuc_ogrenci", "ogrenci_id"),
        Index("idx_sonuc_tarih", "tamamlanma_tarihi"),
    )


class CozulenSoru(Base):
    __tablename__ = "cozulen_sorular"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ogrenci_id = Column(UUID(as_uuid=True), ForeignKey("kullanicilar.id"))
    soru_id = Column(UUID(as_uuid=True), ForeignKey("sorular.id"))
    sinav_id = Column(UUID(as_uuid=True), ForeignKey("sinavlar.id"))

    # Çözüm detayları
    verilen_cevap = Column(String(1))
    dogru_mu = Column(Boolean)
    sure = Column(Integer)  # saniye

    # Güven seviyesi (öğrenci tahmini)
    guven_seviyesi = Column(Integer)  # 1-5

    # Tekrar bilgileri
    cozum_sayisi = Column(Integer, default=1)
    ilk_cozum_tarihi = Column(TIMESTAMP, default=datetime.utcnow)
    son_cozum_tarihi = Column(TIMESTAMP, default=datetime.utcnow)

    # Relations
    ogrenci = relationship("Kullanici", back_populates="cozulen_sorular")
    soru = relationship("Soru", back_populates="cozumler")

    __table_args__ = (
        UniqueConstraint("ogrenci_id", "soru_id", "sinav_id"),
        Index("idx_cozulen_ogrenci", "ogrenci_id"),
        Index("idx_cozulen_soru", "soru_id"),
    )


class OgrenmeYolu(Base):
    __tablename__ = "ogrenme_yollari"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ogrenci_id = Column(UUID(as_uuid=True), ForeignKey("kullanicilar.id"))

    # Öğrenme yolu bilgileri
    baslik = Column(String(255), nullable=False)
    hedef = Column(Text)
    konu = Column(String(100))

    # Plan detayları (JSON)
    haftalik_plan = Column(JSONB, default=[])
    gunluk_gorevler = Column(JSONB, default=[])

    # İlerleme
    tamamlanma_yuzdesi = Column(DECIMAL(5, 2), default=0)
    tamamlanan_gorev_sayisi = Column(Integer, default=0)
    toplam_gorev_sayisi = Column(Integer, default=0)

    # ZPD parametreleri
    mevcut_seviye = Column(Float, default=5.0)
    hedef_seviye = Column(Float, default=7.0)
    zpd_alt_sinir = Column(Float)
    zpd_ust_sinir = Column(Float)

    # Adaptasyon verileri
    adaptasyon_sayisi = Column(Integer, default=0)
    son_adaptasyon = Column(TIMESTAMP)
    performans_trendi = Column(String(20))  # YUKSELIS, DUSUS, SABIT

    # Timestamps
    baslangic_tarihi = Column(TIMESTAMP, default=datetime.utcnow)
    bitis_tarihi = Column(TIMESTAMP)

    __table_args__ = (Index("idx_ogrenme_yolu_ogrenci", "ogrenci_id"),)


class IcerikKaynagi(Base):
    __tablename__ = "icerik_kaynaklari"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # İçerik bilgileri
    baslik = Column(String(255), nullable=False)
    aciklama = Column(Text)
    tur = Column(String(50))  # VIDEO, PDF, TEST, OYUN, vb.
    kaynak = Column(String(100))  # YouTube, Khan Academy, EBA, vb.
    url = Column(String(500))

    # Kategori
    konu = Column(String(100))
    alt_konu = Column(String(100))
    sinif_seviyesi = Column(Integer)

    # Öğrenme stili uyumu
    vark_uyum_skorlari = Column(JSONB)  # {"visual": 0.9, "auditory": 0.3, ...}
    felder_uyum_skorlari = Column(JSONB)

    # İstatistikler
    goruntuleme_sayisi = Column(Integer, default=0)
    ortalama_puan = Column(DECIMAL(3, 2))
    tamamlanma_suresi = Column(Integer)  # dakika

    # Metadata
    dil = Column(String(10), default="tr")
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_icerik_konu", "konu"),
        Index("idx_icerik_tur", "tur"),
    )


class PerformansAnaliz(Base):
    __tablename__ = "performans_analizleri"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ogrenci_id = Column(UUID(as_uuid=True), ForeignKey("kullanicilar.id"))

    # Analiz dönemi
    donem_baslangic = Column(TIMESTAMP)
    donem_bitis = Column(TIMESTAMP)

    # Genel metrikler
    toplam_calisma_suresi = Column(Integer)  # dakika
    gunluk_ortalama_sure = Column(Integer)  # dakika
    toplam_cozulen_soru = Column(Integer)
    dogru_orani = Column(DECIMAL(5, 2))

    # Konu bazlı performans (JSON)
    konu_performanslari = Column(JSONB, default={})

    # Trend analizi
    haftalik_trend = Column(JSONB, default=[])
    aylik_trend = Column(JSONB, default=[])

    # AI önerileri
    guclu_yonler = Column(JSONB, default=[])
    gelistirilmesi_gerekenler = Column(JSONB, default=[])
    onerilen_aksiyonlar = Column(JSONB, default=[])

    # Motivasyon metrikleri
    motivasyon_skoru = Column(Float)
    devamlilk_skoru = Column(Float)

    # Timestamps
    analiz_tarihi = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_performans_ogrenci", "ogrenci_id"),
        Index("idx_performans_tarih", "analiz_tarihi"),
    )


# ============= CACHE & SESSION TABLES =============
class CacheEntry(Base):
    __tablename__ = "cache_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSONB)
    ttl = Column(Integer)  # seconds
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    expires_at = Column(TIMESTAMP)

    __table_args__ = (
        Index("idx_cache_key", "key"),
        Index("idx_cache_expires", "expires_at"),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kullanici_id = Column(UUID(as_uuid=True), ForeignKey("kullanicilar.id"))
    token = Column(String(500), unique=True, nullable=False)
    ip_adresi = Column(String(45))
    user_agent = Column(String(500))
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(TIMESTAMP, default=datetime.utcnow)
    son_aktivite = Column(TIMESTAMP, default=datetime.utcnow)
    sonlanma_tarihi = Column(TIMESTAMP)

    __table_args__ = (
        Index("idx_session_token", "token"),
        Index("idx_session_kullanici", "kullanici_id"),
    )


# ============= AUDIT & LOGGING =============
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kullanici_id = Column(UUID(as_uuid=True), ForeignKey("kullanicilar.id"))
    aksiyon = Column(String(100), nullable=False)
    tablo = Column(String(50))
    kayit_id = Column(String(50))
    eski_deger = Column(JSONB)
    yeni_deger = Column(JSONB)
    ip_adresi = Column(String(45))
    tarih = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_kullanici", "kullanici_id"),
        Index("idx_audit_tarih", "tarih"),
        Index("idx_audit_aksiyon", "aksiyon"),
    )
