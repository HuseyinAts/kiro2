"""
YouTube Video Modelleri ve Enum'lar

TYT/AYT video kesifleri icin veri modelleri.
"""

from dataclasses import dataclass, field
from enum import Enum


class SubjectType(Enum):
    """TYT/AYT Konu turleri"""

    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    SOSYAL = "sosyal"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    INGILIZCE = "ingilizce"
    EDEBIYAT = "edebiyat"


class DifficultyLevel(Enum):
    """Zorluk seviyeleri"""

    BASLANGIC = "baslangic"
    ORTA = "orta"
    ILERI = "ileri"
    SINAVA_OZEL = "sinava_ozel"


class ExamType(Enum):
    """Sinav turleri"""

    TYT = "TYT"
    AYT = "AYT"
    YDT = "YDT"
    MSU = "MSU"


@dataclass
class VideoMetadata:
    """Video metadata - YouTube video bilgileri"""

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
    relevance_keywords: list[str] = field(default_factory=list)
    turkish_content_score: float | None = None
    content_relevance_score: float | None = None

    def to_dict(self) -> dict:
        """Video metadata'yi dict'e cevir"""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "channel_id": self.channel_id,
            "duration": self.duration,
            "view_count": self.view_count,
            "upload_date": self.upload_date,
            "thumbnail": self.thumbnail,
            "description": self.description,
            "quality_score": self.quality_score,
            "subject": self.subject.value,
            "difficulty": self.difficulty.value,
            "exam_type": self.exam_type.value,
            "language": self.language,
            "relevance_keywords": self.relevance_keywords,
            "turkish_content_score": self.turkish_content_score,
            "content_relevance_score": self.content_relevance_score,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
        subject: SubjectType | None = None,
        difficulty: DifficultyLevel | None = None,
        exam_type: ExamType | None = None,
    ) -> "VideoMetadata":
        """Dict'ten VideoMetadata olustur"""
        return cls(
            video_id=data.get("video_id", ""),
            title=data.get("title", ""),
            channel=data.get("channel", ""),
            channel_id=data.get("channel_id", ""),
            duration=data.get("duration", "0:00"),
            view_count=data.get("view_count", 0),
            upload_date=data.get("upload_date", ""),
            thumbnail=data.get("thumbnail", ""),
            description=data.get("description", ""),
            quality_score=data.get("quality_score", 5.0),
            subject=subject or SubjectType(data.get("subject", "matematik")),
            difficulty=difficulty or DifficultyLevel(data.get("difficulty", "orta")),
            exam_type=exam_type or ExamType(data.get("exam_type", "TYT")),
            language=data.get("language", "tr"),
            relevance_keywords=data.get("relevance_keywords", []),
            turkish_content_score=data.get("turkish_content_score"),
            content_relevance_score=data.get("content_relevance_score"),
        )


# Backward compatibility - eski enum degerlerini de destekle
SUBJECT_ALIASES = {
    "turkce": SubjectType.TURKCE,
    "matematik": SubjectType.MATEMATIK,
    "fizik": SubjectType.FIZIK,
    "kimya": SubjectType.KIMYA,
    "biyoloji": SubjectType.BIYOLOJI,
}

DIFFICULTY_ALIASES = {
    "baslangic": DifficultyLevel.BASLANGIC,
    "orta": DifficultyLevel.ORTA,
    "ileri": DifficultyLevel.ILERI,
}
