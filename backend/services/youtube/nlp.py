"""
YouTube Module - Turkish NLP
============================
Turkish content detection and filtering.

Extracted from youtube_discovery.py
"""

import logging
import re

from core.turkish_nlp_utils import normalize_tr

from .config import SUBJECT_KEYWORDS
from .models import DifficultyLevel, SubjectType

logger = logging.getLogger(__name__)


class TurkishContentFilter:
    """Turkish content detection and filtering service."""

    # Türkçe eğitim terminolojisi
    TURKISH_EDUCATION_WORDS = {
        "matematik",
        "fizik",
        "kimya",
        "biyoloji",
        "türkçe",
        "edebiyat",
        "tarih",
        "coğrafya",
        "felsefe",
        "sosyal",
        "üniversite",
        "sınav",
        "tyt",
        "ayt",
        "yks",
        "konu",
        "anlatım",
        "ders",
        "öğretmen",
        "akademi",
        "eğitim",
        "çözüm",
        "soru",
        "test",
        "deneme",
        "hazırlık",
        "kursu",
        "öğrenci",
        "öğrenme",
        "açıklama",
    }

    # İngilizce kelimeler (red flag)
    ENGLISH_WORDS = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "they",
        "have",
        "will",
        "you",
        "can",
        "all",
        "were",
        "been",
        "said",
        "what",
        "use",
        "your",
        "how",
        "our",
        "out",
        "many",
        "time",
        "very",
        "when",
        "much",
        "new",
        "would",
        "there",
        "each",
        "which",
        "their",
        "make",
        "like",
        "into",
        "him",
        "has",
        "two",
        "more",
        "go",
        "no",
        "way",
        "could",
        "my",
        "than",
        "first",
        "water",
        "long",
        "little",
        "most",
        "after",
        "school",
        "learn",
        "tutorial",
        "course",
        "lesson",
        "study",
        "guide",
    }

    def is_turkish_content(self, text: str) -> bool:
        """Türkçe içerik tespiti - gelişmiş NLP"""
        if not text:
            return False

        # Türkçe karakterler
        turkish_chars = set("çğıöşüÇĞIİÖŞÜ")

        # Metni normalize et (Turkish-safe lowercase)
        text_lower = normalize_tr(text)

        # Türkçe karakter oranı
        char_count = len([c for c in text if c.isalpha()])
        turkish_char_count = len([c for c in text if c in turkish_chars])
        turkish_char_ratio = turkish_char_count / max(char_count, 1)

        # Türkçe kelime tespiti
        words = re.findall(r"\b\w+\b", text_lower)
        turkish_word_count = len(
            [w for w in words if w in self.TURKISH_EDUCATION_WORDS]
        )

        # İngilizce kelime tespiti
        english_word_count = len([w for w in words if w in self.ENGLISH_WORDS])

        # Skor hesaplama
        score = 0

        # Türkçe karakter bonusu
        if turkish_char_ratio > 0.1:
            score += 3

        # Türkçe eğitim kelimesi bonusu
        if turkish_word_count > 0:
            score += 4

        # İngilizce kelime cezası
        if english_word_count > 2:
            score -= 3

        # Kanal ismi kontrolü
        if any(
            word in text_lower for word in ["akademi", "eğitim", "öğretmen", "kurs"]
        ):
            score += 2

        return score >= 3

    def filter_turkish_content(self, videos: list[dict]) -> list[dict]:
        """Türkçe içerik filtreleme"""
        filtered_videos = []

        for video in videos:
            title = video.get("title", "")
            channel = video.get("channel", "")
            description = video.get("description", "")

            # Türkçe içerik kontrolü
            text_to_check = f"{title} {channel} {description}"
            is_turkish = self.is_turkish_content(text_to_check)

            if is_turkish:
                video["turkish_content_score"] = 10.0
                filtered_videos.append(video)
            else:
                # Türkçe olmayan içeriği düşük skorla işaretle
                video["turkish_content_score"] = 2.0
                logger.debug(f"Non-Turkish content filtered: {title[:50]}")

        return filtered_videos

    def advanced_content_filtering(
        self, videos: list[dict], subject: SubjectType, difficulty: DifficultyLevel
    ) -> list[dict]:
        """Gelişmiş içerik filtreleme"""

        # Önce Türkçe filtresi uygula
        turkish_videos = self.filter_turkish_content(videos)

        # Konu uygunluk filtreleme
        subject_words = SUBJECT_KEYWORDS.get(subject.value, [])

        filtered_videos = []

        for video in turkish_videos:
            title = normalize_tr(video.get("title", ""))
            channel = normalize_tr(video.get("channel", ""))

            # Konu uygunluk skoru
            subject_score = 0
            for keyword in subject_words:
                if keyword in title or keyword in channel:
                    subject_score += 1

            # TYT/AYT uygunluk
            exam_keywords = ["tyt", "ayt", "yks", "üniversite", "sınav"]
            exam_score = sum(
                1 for keyword in exam_keywords if keyword in title or keyword in channel
            )

            # Toplam uygunluk skoru
            relevance_score = subject_score * 2 + exam_score

            if relevance_score > 0:  # En az bir konu kelimesi olmalı
                video["content_relevance_score"] = min(10.0, relevance_score * 2)
                filtered_videos.append(video)
            else:
                logger.debug(
                    f"Low relevance content filtered: {video.get('title', '')[:50]}"
                )

        return filtered_videos


# Singleton instance
_turkish_filter: TurkishContentFilter = None


def get_turkish_filter() -> TurkishContentFilter:
    """Get Turkish content filter singleton."""
    global _turkish_filter
    if _turkish_filter is None:
        _turkish_filter = TurkishContentFilter()
    return _turkish_filter


__all__ = ["TurkishContentFilter", "get_turkish_filter"]
