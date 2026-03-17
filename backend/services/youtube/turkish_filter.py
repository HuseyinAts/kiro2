"""
Turkce Icerik Filtreleme Mixin

DEPRECATED: Use nlp.py TurkishContentFilter for standalone usage.
This mixin is kept for backward compatibility with YouTubeDiscovery.
"""

import logging
import re
from typing import TYPE_CHECKING

from .models import DifficultyLevel, SubjectType

if TYPE_CHECKING:
    from .discovery import YouTubeDiscovery

logger = logging.getLogger(__name__)


# Turkce karakterler (Unicode diacritics — not ASCII equivalents)
TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")

# Turkce egitim terimleri
TURKISH_EDUCATION_WORDS = {
    "matematik",
    "fizik",
    "kimya",
    "biyoloji",
    "turkce",
    "edebiyat",
    "tarih",
    "cografya",
    "felsefe",
    "sosyal",
    "universite",
    "sinav",
    "tyt",
    "ayt",
    "yks",
    "konu",
    "anlatim",
    "ders",
    "ogretmen",
    "akademi",
    "egitim",
    "cozum",
    "soru",
    "test",
    "deneme",
    "hazirlik",
    "kursu",
    "ogrenci",
    "ogrenme",
    "aciklama",
}

# Ingilizce kelimeler (red flag)
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

# Konu anahtar kelimeleri
SUBJECT_KEYWORDS = {
    SubjectType.MATEMATIK: [
        "matematik",
        "geometri",
        "analiz",
        "trigonometri",
        "fonksiyon",
        "turev",
        "integral",
    ],
    SubjectType.FIZIK: [
        "fizik",
        "mekanik",
        "elektrik",
        "manyetizma",
        "optik",
        "termodinamik",
        "hareket",
    ],
    SubjectType.KIMYA: [
        "kimya",
        "atom",
        "molekul",
        "reaksiyon",
        "element",
        "periyodik",
        "organik",
    ],
    SubjectType.BIYOLOJI: [
        "biyoloji",
        "hucre",
        "dna",
        "protein",
        "metabolizma",
        "ekosistem",
        "evrim",
    ],
    SubjectType.TURKCE: [
        "turkce",
        "dil",
        "gramer",
        "yazim",
        "sozcuk",
        "cumle",
        "paragraf",
    ],
    SubjectType.EDEBIYAT: [
        "edebiyat",
        "siir",
        "roman",
        "hikaye",
        "yazar",
        "eser",
        "donem",
    ],
    SubjectType.TARIH: [
        "tarih",
        "osmanli",
        "cumhuriyet",
        "savas",
        "devrim",
        "medeniyet",
        "kultur",
    ],
    SubjectType.COGRAFYA: [
        "cografya",
        "harita",
        "iklim",
        "nufus",
        "ekonomi",
        "bolge",
        "sehir",
    ],
    SubjectType.SOSYAL: [
        "sosyal",
        "toplum",
        "ekonomi",
        "siyaset",
        "hukuk",
        "sosyoloji",
        "felsefe",
    ],
    SubjectType.INGILIZCE: [
        "ingilizce",
        "english",
        "grammar",
        "vocabulary",
        "tense",
        "kelime",
    ],
}


class TurkishFilterMixin:
    """Turkce icerik filtreleme mixin'i"""

    def _is_turkish_content(self: "YouTubeDiscovery", text: str) -> bool:
        """Turkce icerik tespiti - gelismis NLP"""
        if not text:
            return False

        # Metni normalize et
        text_lower = text.lower()

        # Turkce karakter orani
        char_count = len([c for c in text if c.isalpha()])
        turkish_char_count = len([c for c in text if c in TURKISH_CHARS])
        turkish_char_ratio = turkish_char_count / max(char_count, 1)

        # Turkce kelime tespiti
        words = re.findall(r"\b\w+\b", text_lower)
        turkish_word_count = len([w for w in words if w in TURKISH_EDUCATION_WORDS])

        # Ingilizce kelime tespiti (red flag)
        english_word_count = len([w for w in words if w in ENGLISH_WORDS])

        # Skor hesaplama
        score = 0

        # Turkce karakter bonusu
        if turkish_char_ratio > 0.1:
            score += 3

        # Turkce egitim kelimesi bonusu
        if turkish_word_count > 0:
            score += 4

        # Ingilizce kelime cezasi
        if english_word_count > 2:
            score -= 3

        # Kanal ismi kontrolu
        if any(
            word in text_lower for word in ["akademi", "egitim", "ogretmen", "kurs"]
        ):
            score += 2

        return score >= 3

    def _filter_turkish_content(
        self: "YouTubeDiscovery", videos: list[dict]
    ) -> list[dict]:
        """Turkce icerik filtreleme"""
        filtered_videos = []

        for video in videos:
            title = video.get("title", "")
            channel = video.get("channel", "")
            description = video.get("description", "")

            # Turkce icerik kontrolu
            text_to_check = f"{title} {channel} {description}"
            is_turkish = self._is_turkish_content(text_to_check)

            if is_turkish:
                video["turkish_content_score"] = 10.0
                filtered_videos.append(video)
            else:
                # Turkce olmayan icerigi dusuk skorla isaretle
                video["turkish_content_score"] = 2.0
                logger.debug(f"Non-Turkish content filtered: {title[:50]}")

        return filtered_videos

    def _advanced_content_filtering(
        self: "YouTubeDiscovery",
        videos: list[dict],
        subject: SubjectType,
        difficulty: DifficultyLevel,
    ) -> list[dict]:
        """Gelismis icerik filtreleme"""

        # Once Turkce filtresi uygula
        turkish_videos = self._filter_turkish_content(videos)

        filtered_videos = []
        subject_words = SUBJECT_KEYWORDS.get(subject, [])

        for video in turkish_videos:
            title = video.get("title", "").lower()
            channel = video.get("channel", "").lower()

            # Konu uygunluk skoru
            subject_score = 0
            for keyword in subject_words:
                if keyword in title or keyword in channel:
                    subject_score += 1

            # TYT/AYT uygunluk
            exam_keywords = ["tyt", "ayt", "yks", "universite", "sinav"]
            exam_score = sum(
                1 for keyword in exam_keywords if keyword in title or keyword in channel
            )

            # Toplam uygunluk skoru
            relevance_score = subject_score * 2 + exam_score

            if relevance_score > 0:  # En az bir konu kelimesi olmali
                video["content_relevance_score"] = min(10.0, relevance_score * 2)
                filtered_videos.append(video)
            else:
                logger.debug(
                    f"Low relevance content filtered: {video.get('title', '')[:50]}"
                )

        return filtered_videos
