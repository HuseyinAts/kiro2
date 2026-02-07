"""
YouTube Module - Types and Data Models
======================================
Shared types, enums, and data classes for YouTube video discovery.

Extracted from youtube_discovery.py
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class SubjectType(Enum):
    """TYT/AYT Konu türleri"""

    MATEMATIK = "matematik"
    TURKCE = "türkçe"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    SOSYAL = "sosyal"
    TARIH = "tarih"
    COGRAFYA = "coğrafya"
    FELSEFE = "felsefe"
    INGILIZCE = "ingilizce"
    EDEBIYAT = "edebiyat"


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""

    BASLANGIC = "başlangıç"
    ORTA = "orta"
    ILERI = "ileri"
    SINAVA_OZEL = "sınava özel"


class ExamType(Enum):
    """Sınav türleri"""

    TYT = "TYT"
    AYT = "AYT"
    YDT = "YDT"
    MSU = "MSÜ"


@dataclass
class VideoMetadata:
    """Video metadata"""

    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: str
    view_count: int
    upload_date: str
    thumbnail: str
    description: str
    quality_score: float
    subject: SubjectType
    difficulty: DifficultyLevel
    exam_type: ExamType
    language: str = "tr"
    relevance_keywords: List[str] = field(default_factory=list)
    turkish_content_score: Optional[float] = None
    content_relevance_score: Optional[float] = None


__all__ = [
    "SubjectType",
    "DifficultyLevel",
    "ExamType",
    "VideoMetadata",
]
