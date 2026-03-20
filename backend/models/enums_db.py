"""
SQLAlchemy ORM Enum tanımları
database.py'den ayrıştırıldı (2026-01-10)
"""

import enum


class UserRole(enum.Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    ADMIN = "ADMIN"


class ExamType(str, enum.Enum):
    """Exam type enum - inherits from str for value-based lookup"""
    TYT = "tyt"
    AYT = "ayt"
    YDT = "ydt"
    DENEME = "deneme"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None


class QuestionDifficulty(str, enum.Enum):
    """Question difficulty enum - inherits from str for value-based lookup"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None


class LearningStyle(enum.Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class SubjectArea(str, enum.Enum):
    """Subject area enum - inherits from str for value-based lookup"""
    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN = "fen"
    SOSYAL = "sosyal"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    INGILIZCE = "ingilizce"

    @classmethod
    def _missing_(cls, value):
        """Handle case-insensitive lookup"""
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None


# EBA TV Content Enums
class EBAContentCategory(enum.Enum):
    """EBA TV içerik kategorileri"""
    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN_BILIMLERI = "fen_bilimleri"
    SOSYAL_BILGILER = "sosyal_bilgiler"
    INGILIZCE = "ingilizce"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    EDEBIYAT = "edebiyat"


class EBAGradeLevel(enum.Enum):
    """EBA TV sınıf seviyeleri"""
    SINIF_5 = "5"
    SINIF_6 = "6"
    SINIF_7 = "7"
    SINIF_8 = "8"  # LGS
    SINIF_9 = "9"
    SINIF_10 = "10"
    SINIF_11 = "11"
    SINIF_12 = "12"  # YKS


class EBAVideoQuality(enum.Enum):
    """EBA video kalite seviyeleri"""
    LOW = "low"  # 0-4 puan
    MEDIUM = "medium"  # 4-7 puan
    HIGH = "high"  # 7-10 puan
