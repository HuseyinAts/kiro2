"""
Fixation Point Detector - Göz Odak Noktası Tespiti
REQ-1: Fixation Point Detection

Eye-tracking araştırmalarına dayalı fixation point hesaplama:
- Short words (1-3): first letter bold
- Medium words (4-7): first 2-3 letters bold
- Long words (8+): first 3-4 letters bold
- Turkish-specific: vowel harmony aware
"""

import logging
from dataclasses import dataclass
from enum import Enum

from core.turkish_nlp_utils import normalize_tr

from .syllabifier import TurkishSyllabifier

logger = logging.getLogger(__name__)


class WordLength(Enum):
    """Kelime uzunluğu kategorileri"""

    SHORT = "short"  # 1-3 karakter
    MEDIUM = "medium"  # 4-7 karakter
    LONG = "long"  # 8+ karakter


@dataclass
class FixationPoint:
    """Fixation point veri yapısı"""

    word: str
    bold_start: int  # Bold başlangıç indeksi
    bold_end: int  # Bold bitiş indeksi
    bold_text: str  # Bold yapılacak kısım
    normal_text: str  # Normal kalacak kısım
    word_length_category: WordLength
    syllable_aware: bool  # Syllable sınırına dikkat edildi mi
    confidence: float


class FixationPointDetector:
    """
    Fixation Point Detector

    Eye-tracking araştırmalarına dayalı optimal bold pattern hesaplar:
    - Rayner & Pollatsek (1989): Optimal viewing position
    - McConkie & Rayner (1975): Eye movement research
    - Türkçe'ye özel: Syllable boundary awareness
    """

    def __init__(
        self,
        short_bold_chars: int = 1,
        medium_bold_chars: tuple[int, int] = (2, 3),
        long_bold_chars: tuple[int, int] = (3, 4),
        use_syllable_awareness: bool = True,
    ):
        """
        Args:
            short_bold_chars: Short words için bold karakter sayısı
            medium_bold_chars: Medium words için bold karakter aralığı (min, max)
            long_bold_chars: Long words için bold karakter aralığı (min, max)
            use_syllable_awareness: Syllable sınırlarına dikkat et
        """
        self.short_bold_chars = short_bold_chars
        self.medium_bold_chars = medium_bold_chars
        self.long_bold_chars = long_bold_chars
        self.use_syllable_awareness = use_syllable_awareness

        self.syllabifier = TurkishSyllabifier() if use_syllable_awareness else None

        # Cache
        self._cache: dict[str, FixationPoint] = {}

    def detect(self, word: str, use_cache: bool = True) -> FixationPoint:
        """
        Kelime için fixation point hesapla

        Args:
            word: İşlenecek kelime
            use_cache: Cache kullanılsın mı

        Returns:
            FixationPoint: Hesaplanan fixation point
        """
        if not word:
            return FixationPoint(
                word=word,
                bold_start=0,
                bold_end=0,
                bold_text="",
                normal_text="",
                word_length_category=WordLength.SHORT,
                syllable_aware=False,
                confidence=1.0,
            )

        cache_key = normalize_tr(word)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Kelime uzunluğu kategorisi
            length_category = self._categorize_length(len(word))

            # Bold karakter sayısını hesapla
            bold_count = self._calculate_bold_count(word, length_category)

            # Syllable-aware adjustment
            syllable_aware = False
            if self.use_syllable_awareness and self.syllabifier:
                adjusted_bold_count = self._syllable_aware_adjustment(word, bold_count)
                if adjusted_bold_count != bold_count:
                    bold_count = adjusted_bold_count
                    syllable_aware = True

            # Bold sınırlarını belirle
            bold_start = 0
            bold_end = min(bold_count, len(word))

            result = FixationPoint(
                word=word,
                bold_start=bold_start,
                bold_end=bold_end,
                bold_text=word[bold_start:bold_end],
                normal_text=word[bold_end:],
                word_length_category=length_category,
                syllable_aware=syllable_aware,
                confidence=0.9 if syllable_aware else 0.8,
            )

            if use_cache:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Fixation point detection error ({word}): {e}")
            # Fallback: İlk 2 karakter bold
            bold_end = min(2, len(word))
            return FixationPoint(
                word=word,
                bold_start=0,
                bold_end=bold_end,
                bold_text=word[:bold_end],
                normal_text=word[bold_end:],
                word_length_category=WordLength.SHORT,
                syllable_aware=False,
                confidence=0.5,
            )

    def _categorize_length(self, length: int) -> WordLength:
        """Kelime uzunluğunu kategorize et"""
        if length <= 3:
            return WordLength.SHORT
        if length <= 7:
            return WordLength.MEDIUM
        return WordLength.LONG

    def _calculate_bold_count(self, word: str, category: WordLength) -> int:
        """Bold karakter sayısını hesapla"""
        length = len(word)

        if category == WordLength.SHORT:
            return self.short_bold_chars

        if category == WordLength.MEDIUM:
            # 4-7 karakter: %30-40 bold
            min_bold, max_bold = self.medium_bold_chars
            target_ratio = 0.35
            calculated = int(length * target_ratio)
            return max(min_bold, min(max_bold, calculated))

        # LONG
        # 8+ karakter: %25-35 bold
        min_bold, max_bold = self.long_bold_chars
        target_ratio = 0.30
        calculated = int(length * target_ratio)
        return max(min_bold, min(max_bold, calculated))

    def _syllable_aware_adjustment(self, word: str, bold_count: int) -> int:
        """Syllable sınırına göre bold sayısını ayarla"""
        if not self.syllabifier:
            return bold_count

        syllable_result = self.syllabifier.syllabify(word)
        if not syllable_result.syllables:
            return bold_count

        # İlk hecenin uzunluğunu kontrol et
        first_syllable = syllable_result.syllables[0]
        first_syllable_len = len(first_syllable.text)

        # Bold sayısı ilk heceden küçükse, ilk heceyi tam bold yap
        if bold_count < first_syllable_len <= bold_count + 1:
            return first_syllable_len

        # Bold sayısı hece ortasında kalıyorsa, hece sınırına ayarla
        boundaries = self.syllabifier.get_syllable_boundaries(word)
        for boundary in boundaries:
            # Bold count hece sınırına yakınsa, sınıra ayarla
            if abs(bold_count - boundary) <= 1:
                return boundary

        return bold_count

    def batch_detect(
        self, words: list[str], use_cache: bool = True
    ) -> list[FixationPoint]:
        """Birden fazla kelime için fixation point hesapla"""
        return [self.detect(word, use_cache) for word in words]

    def get_optimal_bold_ratio(self, word: str) -> float:
        """Optimal bold oranını döndür"""
        fixation = self.detect(word)
        if not word:
            return 0.0
        return fixation.bold_end / len(word)

    def clear_cache(self):
        """Cache'i temizle"""
        self._cache.clear()
        if self.syllabifier:
            self.syllabifier.clear_cache()

    def get_cache_stats(self) -> dict:
        """Cache istatistiklerini döndür"""
        return {
            "fixation_cache_size": len(self._cache),
            "syllabifier_cache": self.syllabifier.get_cache_stats()
            if self.syllabifier
            else None,
        }
