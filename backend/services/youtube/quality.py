"""
YouTube Module - Quality Scoring
================================
Video quality scoring algorithms.

Extracted from youtube_discovery.py
"""

import logging
from datetime import datetime
from typing import Any, Dict

from .config import TRUSTED_CHANNELS
from .types import DifficultyLevel, ExamType, SubjectType

logger = logging.getLogger(__name__)


class QualityScorer:
    """Video quality scoring service."""

    def calculate_quality_score_fast(
        self, video_data: Dict, subject: SubjectType, exam_type: ExamType
    ) -> float:
        """Hızlı kalite puanı hesaplama (performance optimized)"""
        score = 5.0  # Base score

        title_lower = video_data.get("title", "").lower()

        # Hızlı başlık kontrolü
        if subject.value in title_lower:
            score += 2.0
        if exam_type.value.lower() in title_lower:
            score += 2.0
        if any(
            keyword in title_lower
            for keyword in ["konu anlatım", "ders", "2025", "2024"]
        ):
            score += 1.0

        # Hızlı kanal kontrolü
        channel_lower = video_data.get("channel", "").lower()
        if any(
            keyword in channel_lower for keyword in ["öğretmen", "akademi", "eğitim"]
        ):
            score += 1.0

        return min(score, 10.0)

    def calculate_quality_score(
        self, video_data: Dict, subject: SubjectType, exam_type: ExamType
    ) -> float:
        """Video kalite puanı hesapla"""
        score = 0.0

        # Kanal güvenilirliği (40% ağırlık)
        channel_score = self._get_channel_quality(video_data.get("channel", ""), subject)
        score += channel_score * 0.4

        # Başlık relevansı (25% ağırlık)
        title_score = self._calculate_title_relevance(
            video_data.get("title", ""), subject, exam_type
        )
        score += title_score * 0.25

        # View count normalized (15% ağırlık)
        view_count = video_data.get("view_count", 0)
        view_score = min(view_count / 100000, 10) / 10  # 100k+ view = max score
        score += view_score * 0.15

        # Video süresi (10% ağırlık)
        duration_score = self._calculate_duration_score(video_data.get("duration", ""))
        score += duration_score * 0.10

        # Upload date (10% ağırlık)
        date_score = self._calculate_date_score(video_data.get("upload_date", ""))
        score += date_score * 0.10

        return min(score, 10.0)  # Maksimum 10 puan

    async def calculate_dynamic_quality_score(
        self,
        video_data: Dict,
        subject: SubjectType,
        difficulty: DifficultyLevel,
        exam_type: ExamType,
        student_level: int = 5,
        llm_analysis: Dict[str, Any] = None,
    ) -> float:
        """Öğrenci seviyesine göre dinamik kalite puanı hesaplama"""

        # Temel kalite puanı
        base_score = self.calculate_quality_score(video_data, subject, exam_type)

        # LLM analizi varsayılan değerler
        if llm_analysis is None:
            llm_analysis = {
                "relevance_score": 7.0,
                "educational_quality": 8.0,
                "level_appropriateness": 8.0,
                "turkish_content": True,
            }

        # Öğrenci seviyesine göre adaptasyon
        level_factor = 1.0
        if student_level <= 3:  # Başlangıç seviye
            if difficulty == DifficultyLevel.BASLANGIC:
                level_factor = 1.3  # Başlangıç videoları tercih et
            elif difficulty == DifficultyLevel.ILERI:
                level_factor = 0.7  # İleri videoları cezalandır
        elif student_level >= 8:  # İleri seviye
            if difficulty == DifficultyLevel.ILERI:
                level_factor = 1.2  # İleri videoları tercih et
            elif difficulty == DifficultyLevel.BASLANGIC:
                level_factor = 0.8  # Başlangıç videoları azalt

        # LLM skorlarını entegre et
        relevance_score = llm_analysis.get("relevance_score", 7.0)
        educational_quality = llm_analysis.get("educational_quality", 8.0)
        level_appropriateness = llm_analysis.get("level_appropriateness", 8.0)
        turkish_content = llm_analysis.get("turkish_content", True)

        # Final score calculation
        final_score = (
            base_score * 0.3
            + relevance_score * 0.25  # %30 temel score
            + educational_quality * 0.25  # %25 LLM relevance
            + level_appropriateness * 0.2  # %25 eğitim kalitesi  # %20 seviye uygunluğu
        ) * level_factor

        # Türkçe içerik bonusu
        if turkish_content:
            final_score *= 1.1

        return min(final_score, 10.0)

    def _get_channel_quality(self, channel_name: str, subject: SubjectType) -> float:
        """Kanal kalite puanı al"""
        subject_channels = TRUSTED_CHANNELS.get(subject.value, [])

        for channel in subject_channels:
            if channel["name"].lower() in channel_name.lower():
                return channel["quality"]

        # Genel eğitim kanalı kontrolü
        educational_keywords = ["öğretmen", "akademi", "eğitim", "ders", "kurs", "okul"]
        for keyword in educational_keywords:
            if keyword in channel_name.lower():
                return 7.0

        return 5.0  # Varsayılan puan

    def _calculate_title_relevance(
        self, title: str, subject: SubjectType, exam_type: ExamType
    ) -> float:
        """Başlık relevans puanı"""
        title_lower = title.lower()
        score = 0.0

        # Konu adı varlığı
        if subject.value in title_lower:
            score += 3.0

        # Sınav türü varlığı
        if exam_type.value.lower() in title_lower:
            score += 3.0

        # Eğitim anahtar kelimeleri
        edu_keywords = [
            "konu anlatımı",
            "ders",
            "öğretim",
            "anlatım",
            "hazırlık",
            "çözüm",
        ]
        for keyword in edu_keywords:
            if keyword in title_lower:
                score += 1.0
                break

        # Yıl varlığı (güncellik)
        if "2025" in title_lower or "2024" in title_lower:
            score += 1.0

        # Türkçe olduğunu gösteren işaretler
        turkish_indicators = ["türkçe", "tr", "turkish"]
        for indicator in turkish_indicators:
            if indicator in title_lower:
                score += 1.0
                break

        return min(score, 10.0)

    def _calculate_duration_score(self, duration: str) -> float:
        """Video süre puanı"""
        try:
            parts = duration.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                total_seconds = minutes * 60 + seconds
            elif len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
                total_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                return 5.0

            # İdeal süre 10-45 dakika arası
            if 600 <= total_seconds <= 2700:  # 10-45 dakika
                return 10.0
            elif 300 <= total_seconds <= 3600:  # 5-60 dakika
                return 8.0
            elif total_seconds <= 300:  # Çok kısa
                return 6.0
            else:  # Çok uzun
                return 7.0

        except ValueError:
            return 5.0

    def _calculate_date_score(self, upload_date: str) -> float:
        """Upload tarihi puanı"""
        if not upload_date:
            return 5.0

        # Güncellik puanı
        if "2025" in upload_date or "2024" in upload_date:
            return 10.0
        elif "2023" in upload_date:
            return 8.0
        elif "2022" in upload_date:
            return 6.0
        else:
            return 4.0


# Singleton instance
_quality_scorer: QualityScorer = None


def get_quality_scorer() -> QualityScorer:
    """Get quality scorer singleton."""
    global _quality_scorer
    if _quality_scorer is None:
        _quality_scorer = QualityScorer()
    return _quality_scorer


__all__ = ["QualityScorer", "get_quality_scorer"]
