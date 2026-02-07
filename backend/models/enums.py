"""
Sistem genelinde kullanılan enum tanımları
"""
from enum import Enum


class SinavTipi(str, Enum):
    """ÖSYM sınav türleri"""

    TYT = "TYT"  # Temel Yeterlilik Testi
    AYT = "AYT"  # Alan Yeterlilik Testi
    YDT = "YDT"  # Yabancı Dil Testi


class TurkishExamType(str, Enum):
    """Turkish exam types (alias for international compatibility)"""

    TYT = "tyt"  # Temel Yeterlilik Testi
    AYT = "ayt"  # Alan Yeterlilik Testi
    YKS = "yks"  # Yükseköğretim Kurumları Sınavı
    MSU = "msu"  # Matematik ve Fen Bilimleri Testi
    DIL = "dil"  # Yabancı Dil Testi
    YDT = "ydt"  # Yabancı Dil Testi (alternative naming)


class ZorlukSeviyesi(str, Enum):
    """Soru ve içerik zorluk seviyeleri"""

    KOLAY = "kolay"
    ORTA = "orta"
    ZOR = "zor"


class DifficultyLevel(str, Enum):
    """
    Question and content difficulty levels (English version for international compatibility)

    Compatible with EBA TV API and other international educational APIs
    """

    BEGINNER = "beginner"  # Başlangıç seviyesi
    EASY = "easy"  # Kolay
    MEDIUM = "medium"  # Orta
    HARD = "hard"  # Zor
    EXPERT = "expert"  # İleri/Uzman seviyesi

    @classmethod
    def from_turkish(cls, turkish_level: "ZorlukSeviyesi") -> "DifficultyLevel":
        """
        Convert from Turkish ZorlukSeviyesi to English DifficultyLevel

        Args:
            turkish_level: Turkish difficulty level

        Returns:
            DifficultyLevel: Corresponding English level
        """
        mapping = {
            ZorlukSeviyesi.KOLAY: cls.EASY,
            ZorlukSeviyesi.ORTA: cls.MEDIUM,
            ZorlukSeviyesi.ZOR: cls.HARD,
        }
        return mapping.get(turkish_level, cls.MEDIUM)

    def to_turkish(self) -> "ZorlukSeviyesi":
        """
        Convert to Turkish ZorlukSeviyesi

        Returns:
            ZorlukSeviyesi: Corresponding Turkish level
        """
        mapping = {
            self.BEGINNER: ZorlukSeviyesi.KOLAY,
            self.EASY: ZorlukSeviyesi.KOLAY,
            self.MEDIUM: ZorlukSeviyesi.ORTA,
            self.HARD: ZorlukSeviyesi.ZOR,
            self.EXPERT: ZorlukSeviyesi.ZOR,
        }
        return mapping.get(self, ZorlukSeviyesi.ORTA)


class OgrenmeStili(str, Enum):
    """Öğrenci öğrenme stilleri"""

    GORSEL = "gorsel"
    ISITSEL = "isitsel"
    KINESTETIK = "kinestetik"
    OKUMA_YAZMA = "okuma_yazma"


class IcerikTipi(str, Enum):
    """Eğitim içerik türleri"""

    VIDEO = "video"
    MAKALE = "makale"
    INTERAKTIF = "interaktif"
    QUIZ = "quiz"
    SORU_BANKASI = "soru_bankasi"


class KullaniciRolu(str, Enum):
    """Sistem kullanıcı rolleri"""

    OGRENCI = "ogrenci"
    OGRETMEN = "ogretmen"
    VELI = "veli"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class SinavDurumu(str, Enum):
    """Sınav oturum durumları"""

    HAZIR = "hazir"
    DEVAM_EDIYOR = "devam_ediyor"
    TAMAMLANDI = "tamamlandi"
    IPTAL_EDILDI = "iptal_edildi"


class RaporTipi(str, Enum):
    """Rapor türleri"""

    HAFTALIK = "haftalik"
    AYLIK = "aylik"
    SINAV_SONRASI = "sinav_sonrasi"
    DONEM_SONU = "donem_sonu"


class KarsilastirmaGrubu(str, Enum):
    """Performans karşılaştırma grupları"""

    SINIF = "sinif"
    OKUL = "okul"
    ULUSAL = "ulusal"
