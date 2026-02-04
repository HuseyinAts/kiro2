"""
SQLAlchemy Database Models
Teknofest 2025 - Türkiye Üniversite Sınav Hazırlık Platformu
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class KullaniciRolu(PyEnum):
    """Kullanıcı rolleri"""

    OGRENCI = "ogrenci"
    OGRETMEN = "ogretmen"
    VELI = "veli"
    ADMIN = "admin"


class SinavTipi(PyEnum):
    """Sınav tipleri"""

    TYT = "tyt"
    AYT = "ayt"
    YDT = "ydt"
    DENEME = "deneme"
    KONU_TARAMA = "konu_tarama"


class ZorlukSeviyesi(PyEnum):
    """Zorluk seviyeleri"""

    KOLAY = "kolay"
    ORTA = "orta"
    ZOR = "zor"
    UZMAN = "uzman"


class OgrenmeStili(PyEnum):
    """Öğrenme stilleri"""

    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"
    MIXED = "mixed"


# Kullanıcı Modelleri
class Kullanici(Base):
    """Temel kullanıcı modeli"""

    __tablename__ = "kullanicilar"
    __table_args__ = {"extend_existing": True}

    kullanici_id = Column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    ad_soyad = Column(String(255), nullable=False)
    sifre_hash = Column(String(255), nullable=False)
    rol = Column(Enum(KullaniciRolu), nullable=False)
    aktif = Column(Boolean, default=True)
    email_dogrulandi = Column(Boolean, default=False)
    kayit_tarihi = Column(DateTime(timezone=True), server_default=func.now())
    son_giris = Column(DateTime(timezone=True))

    # İlişkiler
    ogrenci_profili = relationship(
        "OgrenciProfili", back_populates="kullanici", uselist=False
    )
    ogretmen_profili = relationship(
        "OgretmenProfili", back_populates="kullanici", uselist=False
    )
    veli_profili = relationship(
        "VeliProfili", back_populates="kullanici", uselist=False
    )


class OgrenciProfili(Base):
    """Öğrenci profil bilgileri"""

    __tablename__ = "ogrenci_profilleri"
    __table_args__ = {"extend_existing": True}

    profil_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kullanici_id = Column(
        String(36), ForeignKey("kullanicilar.kullanici_id"), nullable=False
    )
    sinif = Column(Integer)  # 9, 10, 11, 12
    okul_adi = Column(String(255))
    hedef_universite = Column(String(255))
    hedef_bolum = Column(String(255))
    ogrenme_stili = Column(Enum(OgrenmeStili))
    mevcut_seviye = Column(Float, default=5.0)  # 0-10 arası
    hedef_puan = Column(Integer)
    guncelleme_tarihi = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    kullanici = relationship("Kullanici", back_populates="ogrenci_profili")
    sinav_sonuclari = relationship("SinavSonucu", back_populates="ogrenci")
    ogrenme_oturumlari = relationship("OgrenmeOturumu", back_populates="ogrenci")


class OgretmenProfili(Base):
    """Öğretmen profil bilgileri"""

    __tablename__ = "ogretmen_profilleri"
    __table_args__ = {"extend_existing": True}

    profil_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kullanici_id = Column(
        String(36), ForeignKey("kullanicilar.kullanici_id"), nullable=False
    )
    okul_adi = Column(String(255))
    brans = Column(String(100))
    deneyim_yili = Column(Integer)
    guncelleme_tarihi = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    kullanici = relationship("Kullanici", back_populates="ogretmen_profili")


class VeliProfili(Base):
    """Veli profil bilgileri"""

    __tablename__ = "veli_profilleri"
    __table_args__ = {"extend_existing": True}

    profil_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kullanici_id = Column(
        String(36), ForeignKey("kullanicilar.kullanici_id"), nullable=False
    )
    cocuk_sayisi = Column(Integer, default=1)
    guncelleme_tarihi = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    kullanici = relationship("Kullanici", back_populates="veli_profili")


# Sınav Modelleri
class SinavSablonu(Base):
    """Sınav şablonları (TYT, AYT, YDT)"""

    __tablename__ = "sinav_sablonlari"
    __table_args__ = {"extend_existing": True}

    sablon_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ad = Column(String(255), nullable=False)
    tip = Column(Enum(SinavTipi), nullable=False)
    aciklama = Column(Text)
    sure_dakika = Column(Integer, nullable=False)  # Dakika cinsinden
    toplam_soru_sayisi = Column(Integer, nullable=False)
    konu_dagilimi = Column(
        JSON
    )  # {"matematik": 40, "turkce": 40, "fen": 20, "sosyal": 20}
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    sinavlar = relationship("Sinav", back_populates="sablon")


class Sinav(Base):
    """Öğrenci sınav oturumları"""

    __tablename__ = "sinavlar"
    __table_args__ = {"extend_existing": True}

    sinav_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ogrenci_id = Column(
        String(36), ForeignKey("ogrenci_profilleri.profil_id"), nullable=False
    )
    sablon_id = Column(
        String(36), ForeignKey("sinav_sablonlari.sablon_id"), nullable=False
    )
    baslangic_zamani = Column(DateTime(timezone=True), server_default=func.now())
    bitis_zamani = Column(DateTime(timezone=True))
    durum = Column(
        String(50), default="devam_ediyor"
    )  # devam_ediyor, tamamlandi, iptal_edildi
    mevcut_soru_index = Column(Integer, default=0)
    kalan_sure_saniye = Column(Integer)

    # İlişkiler
    sablon = relationship("SinavSablonu", back_populates="sinavlar")
    cevaplar = relationship("SinavCevabi", back_populates="sinav")
    sonuc = relationship("SinavSonucu", back_populates="sinav", uselist=False)


class SoruBankasi(Base):
    """Soru bankası"""

    __tablename__ = "soru_bankasi"
    __table_args__ = {"extend_existing": True}

    soru_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    konu = Column(String(255), nullable=False, index=True)
    alt_konu = Column(String(255), index=True)
    zorluk_seviyesi = Column(Enum(ZorlukSeviyesi), nullable=False, index=True)
    soru_metni = Column(Text, nullable=False)
    secenekler = Column(
        JSON
    )  # {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."}
    dogru_cevap = Column(String(1), nullable=False)  # A, B, C, D, E
    aciklama = Column(Text)

    # IRT Parametreleri
    irt_a_parametresi = Column(Float)  # Discrimination (ayırt edicilik)
    irt_b_parametresi = Column(Float)  # Difficulty (zorluk)
    irt_c_parametresi = Column(Float)  # Guessing (şans faktörü)

    # Türkçe Morfoloji Parametreleri
    morfoloji_karmasikligi = Column(Float)  # 0-1 arası
    kok_kelime_sayisi = Column(Integer)
    ek_sayisi = Column(Integer)

    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    cevaplar = relationship("SinavCevabi", back_populates="soru")


class SinavCevabi(Base):
    """Öğrenci sınav cevapları"""

    __tablename__ = "sinav_cevaplari"
    __table_args__ = {"extend_existing": True}

    cevap_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sinav_id = Column(String(36), ForeignKey("sinavlar.sinav_id"), nullable=False)
    soru_id = Column(String(36), ForeignKey("soru_bankasi.soru_id"), nullable=False)
    verilen_cevap = Column(String(1))  # A, B, C, D, E veya None (boş)
    dogru_mu = Column(Boolean)
    cevaplama_suresi_saniye = Column(Integer)
    cevaplama_zamani = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    sinav = relationship("Sinav", back_populates="cevaplar")
    soru = relationship("SoruBankasi", back_populates="cevaplar")


class SinavSonucu(Base):
    """Sınav sonuçları ve analizleri"""

    __tablename__ = "sinav_sonuclari"
    __table_args__ = {"extend_existing": True}

    sonuc_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sinav_id = Column(String(36), ForeignKey("sinavlar.sinav_id"), nullable=False)
    ogrenci_id = Column(
        String(36), ForeignKey("ogrenci_profilleri.profil_id"), nullable=False
    )

    # Temel Sonuçlar
    toplam_dogru = Column(Integer, default=0)
    toplam_yanlis = Column(Integer, default=0)
    toplam_bos = Column(Integer, default=0)
    net_puan = Column(Float)  # Doğru - (Yanlış/4)
    yuzdelik_dilim = Column(Float)

    # Konu Bazlı Analizler
    konu_analizleri = Column(JSON)  # {"matematik": {"dogru": 8, "yanlis": 2}, ...}

    # ZPD ve Kişiselleştirme
    zpd_alt_sinir = Column(Float)
    zpd_ust_sinir = Column(Float)
    optimal_zorluk = Column(Float)
    kulturel_uyum_skoru = Column(Float)

    # IRT Analizleri
    irt_yetenek_seviyesi = Column(Float)  # Theta değeri
    irt_guven_araligi = Column(JSON)  # {"alt": -1.2, "ust": 0.8}

    hesaplama_tarihi = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    sinav = relationship("Sinav", back_populates="sonuc")
    ogrenci = relationship("OgrenciProfili", back_populates="sinav_sonuclari")


# Öğrenme ve Kişiselleştirme Modelleri
class OgrenmeStiliProfili(Base):
    """VARK + Felder-Silverman hibrit öğrenme stili profili"""

    __tablename__ = "ogrenme_stili_profilleri"
    __table_args__ = {"extend_existing": True}

    profil_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ogrenci_id = Column(
        String(36), ForeignKey("ogrenci_profilleri.profil_id"), nullable=False
    )

    # VARK Duyusal Tercihler (0-1 arası)
    vark_visual = Column(Float, default=0.25)  # Görsel
    vark_auditory = Column(Float, default=0.25)  # İşitsel
    vark_reading = Column(Float, default=0.25)  # Okuma-yazma
    vark_kinesthetic = Column(Float, default=0.25)  # Kinestetik

    # Felder-Silverman Bilişsel Süreçler (-1 ile +1 arası)
    fs_aktif_reflektif = Column(Float, default=0.0)  # Aktif ↔ Reflektif
    fs_duyusal_sezgisel = Column(Float, default=0.0)  # Duyusal ↔ Sezgisel
    fs_gorsel_sozel = Column(Float, default=0.0)  # Görsel ↔ Sözel
    fs_sirali_butunsel = Column(Float, default=0.0)  # Sıralı ↔ Bütünsel

    # Hibrit Profil Bilgileri
    dominant_stil = Column(String(50))  # "visual_aktif_duyusal_gorsel_sirali" gibi
    guven_seviyesi = Column(Float, default=0.5)  # 0-1 arası

    son_guncelleme = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # İlişkiler
    ogrenci = relationship("OgrenciProfili")


class KulturelBaglamProfili(Base):
    """Türk kültürü faktörleri profili"""

    __tablename__ = "kulturel_baglam_profilleri"
    __table_args__ = {"extend_existing": True}

    profil_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ogrenci_id = Column(
        String(36), ForeignKey("ogrenci_profilleri.profil_id"), nullable=False
    )

    # Türk Kültürü Faktörleri (0-1 arası)
    grup_calismasi_tercihi = Column(Float, default=0.8)
    ogretmene_saygi_seviyesi = Column(Float, default=0.9)
    aile_katilim_derecesi = Column(Float, default=0.7)
    akran_rekabet_egilimi = Column(Float, default=0.6)
    otorite_kabul_seviyesi = Column(Float, default=0.8)
    toplumsal_onay_ihtiyaci = Column(Float, default=0.6)
    basari_odaklilik = Column(Float, default=0.8)
    kolektif_kimlik_gucu = Column(Float, default=0.7)

    tespit_tarihi = Column(DateTime(timezone=True), server_default=func.now())
    guncelleme_tarihi = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    ogrenci = relationship("OgrenciProfili")


class MaarifDegerleriProfili(Base):
    """MEB Maarif değerleri profili"""

    __tablename__ = "maarif_degerleri_profilleri"
    __table_args__ = {"extend_existing": True}

    profil_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ogrenci_id = Column(
        String(36), ForeignKey("ogrenci_profilleri.profil_id"), nullable=False
    )

    # Milli Değerler (0-1 arası)
    vatan_sevgisi = Column(Float, default=0.8)
    millet_bilinci = Column(Float, default=0.7)
    aile_birligi = Column(Float, default=0.9)
    bayrak_sevgisi = Column(Float, default=0.8)
    istiklal_ruhu = Column(Float, default=0.7)

    # Evrensel Değerler (0-1 arası)
    adalet = Column(Float, default=0.8)
    dostluk = Column(Float, default=0.9)
    durustluk = Column(Float, default=0.8)
    ozgurluk = Column(Float, default=0.7)
    esitlik = Column(Float, default=0.8)
    baris = Column(Float, default=0.9)

    # Kök Değerler (0-1 arası)
    sabir = Column(Float, default=0.7)
    saygi = Column(Float, default=0.9)
    sevgi = Column(Float, default=0.8)
    sorumluluk = Column(Float, default=0.8)
    duyarlilik = Column(Float, default=0.7)
    hosgoru = Column(Float, default=0.8)

    tespit_tarihi = Column(DateTime(timezone=True), server_default=func.now())
    guncelleme_tarihi = Column(DateTime(timezone=True), onupdate=func.now())

    # İlişkiler
    ogrenci = relationship("OgrenciProfili")


class OgrenmeOturumu(Base):
    """Öğrenci öğrenme oturumları ve davranışsal veriler"""

    __tablename__ = "ogrenme_oturumlari"
    __table_args__ = {"extend_existing": True}

    oturum_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ogrenci_id = Column(
        String(36), ForeignKey("ogrenci_profilleri.profil_id"), nullable=False
    )

    # Oturum Bilgileri
    baslangic_zamani = Column(DateTime(timezone=True), server_default=func.now())
    bitis_zamani = Column(DateTime(timezone=True))
    sure_dakika = Column(Integer)
    konu = Column(String(255))
    ogrenme_modu = Column(String(50))  # "bireysel", "grup", "karma"

    # Davranışsal Veriler
    video_izleme_suresi = Column(Integer, default=0)  # Saniye
    metin_okuma_suresi = Column(Integer, default=0)  # Saniye
    interaktif_etkilesim = Column(Integer, default=0)  # Tıklama sayısı
    not_alma_sikligi = Column(Integer, default=0)
    soru_sorma_sayisi = Column(Integer, default=0)

    # Performans Metrikleri
    basari_orani = Column(Float)  # 0-1 arası
    odaklanma_skoru = Column(Float)  # 0-1 arası
    motivasyon_seviyesi = Column(Float)  # 0-1 arası

    # İlişkiler
    ogrenci = relationship("OgrenciProfili", back_populates="ogrenme_oturumlari")


# İçerik ve Kaynak Modelleri
class EgitimIcerigi(Base):
    """Eğitim içerikleri (video, metin, interaktif)"""

    __tablename__ = "egitim_icerikleri"
    __table_args__ = {"extend_existing": True}

    icerik_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    baslik = Column(String(500), nullable=False)
    aciklama = Column(Text)
    icerik_tipi = Column(String(50), nullable=False)  # "video", "metin", "interaktif"
    konu = Column(String(255), nullable=False, index=True)
    alt_konu = Column(String(255), index=True)
    zorluk_seviyesi = Column(Enum(ZorlukSeviyesi), nullable=False)

    # İçerik Verileri
    url = Column(String(1000))
    dosya_yolu = Column(String(500))
    sure_dakika = Column(Integer)

    # Kalite ve Erişilebilirlik
    kalite_skoru = Column(Float, default=0.5)  # 0-1 arası
    erisebilirlik_skoru = Column(Float, default=0.5)  # 0-1 arası
    bionic_reading_destegi = Column(Boolean, default=False)
    basitlestirme_seviyesi = Column(Integer)  # 1, 2, 3 veya None

    # MEB Maarif Uyumu
    maarif_uyum_skoru = Column(Float, default=0.5)  # 0-1 arası
    uyumlu_degerler = Column(JSON)  # ["vatan_sevgisi", "adalet", ...]

    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime(timezone=True), server_default=func.now())


# Sistem ve Monitoring Modelleri
class SistemMetrikleri(Base):
    """Sistem performans metrikleri"""

    __tablename__ = "sistem_metrikleri"
    __table_args__ = {"extend_existing": True}

    metrik_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metrik_adi = Column(String(255), nullable=False)
    deger = Column(Float, nullable=False)
    birim = Column(String(50))
    kategori = Column(String(100))  # "performance", "usage", "error"
    kayit_zamani = Column(DateTime(timezone=True), server_default=func.now())


class AgentPerformansMetrikleri(Base):
    """AI Agent performans metrikleri"""

    __tablename__ = "agent_performans_metrikleri"
    __table_args__ = {"extend_existing": True}

    metrik_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_adi = Column(String(100), nullable=False)
    islem_tipi = Column(String(100), nullable=False)
    yanit_suresi_ms = Column(Integer)
    basari_durumu = Column(Boolean)
    hata_mesaji = Column(Text)
    kayit_zamani = Column(DateTime(timezone=True), server_default=func.now())
