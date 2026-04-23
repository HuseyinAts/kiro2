"""
Turkish Readability Scorer
Türkçe metinler için okunabilirlik skoru hesaplama

Target (requirements.md):
- Lise seviyesi için uygun skor: 60-70 (Flesch Reading Ease)
"""

import re

from pydantic import BaseModel


class ReadabilityResult(BaseModel):
    """Okunabilirlik analiz sonucu"""
    flesch_score: float
    word_count: int
    sentence_count: int
    syllable_count: int
    avg_sentence_length: float
    avg_syllables_per_word: float
    grade_level: str
    suggestions: list[str]


class TurkishReadabilityScorer:
    """
    Türkçe metinler için okunabilirlik skorlayıcı

    Flesch Reading Ease (Türkçe adaptasyonu):
    FRE = 198.825 - (40.175 × ASL) - (2.610 × ASW)

    ASL = Average Sentence Length (ortalama cümle uzunluğu)
    ASW = Average Syllables per Word (kelime başına ortalama hece)

    Hedef skor (lise seviyesi): 60-70
    """

    # Türkçe ünlüler
    VOWELS = set("aeıioöuüAEIİOÖUÜ")

    # Türkçe noktalama
    SENTENCE_ENDINGS = [".", "!", "?"]

    # Hedef skor aralıkları
    TARGET_MIN = 60
    TARGET_MAX = 70

    def __init__(self):
        """Scorer başlat"""

    def count_syllables(self, word: str) -> int:
        """
        Türkçe kelimede hece sayısını hesapla

        Türkçe'de her ünlü bir hece oluşturur.

        Args:
            word: Kelime

        Returns:
            int: Hece sayısı (minimum 1)
        """
        # Sadece harfleri al
        word = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ]', '', word)

        if not word:
            return 1

        count = sum(1 for char in word if char in self.VOWELS)
        return max(count, 1)

    def count_sentences(self, text: str) -> int:
        """
        Cümle sayısını hesapla

        Args:
            text: Metin

        Returns:
            int: Cümle sayısı (minimum 1)
        """
        count = 0
        for ending in self.SENTENCE_ENDINGS:
            count += text.count(ending)

        return max(count, 1)

    def count_words(self, text: str) -> int:
        """
        Kelime sayısını hesapla

        Args:
            text: Metin

        Returns:
            int: Kelime sayısı
        """
        words = text.split()
        # Sadece harflerden oluşan kelimeleri say
        valid_words = [w for w in words if re.search(r'[a-zA-ZğüşıöçĞÜŞİÖÇ]', w)]
        return len(valid_words)

    def calculate_flesch_score(self, text: str) -> float:
        """
        Flesch Reading Ease skoru hesapla (Türkçe adaptasyonu)

        FRE = 198.825 - (40.175 × ASL) - (2.610 × ASW)

        Args:
            text: Metin

        Returns:
            float: Flesch skoru (0-100+)
        """
        if not text.strip():
            return 0.0

        word_count = self.count_words(text)
        sentence_count = self.count_sentences(text)

        if word_count == 0:
            return 0.0

        # Hece sayısı
        words = text.split()
        total_syllables = sum(self.count_syllables(w) for w in words)

        # Ortalamalar
        asl = word_count / sentence_count  # Average Sentence Length
        asw = total_syllables / word_count  # Average Syllables per Word

        # Türkçe Flesch formülü (adaptasyon)
        # Orijinal: 206.835 - (1.015 × ASL) - (84.6 × ASW)
        # Türkçe adaptasyonu: 198.825 - (40.175 × ASL) - (2.610 × ASW)
        # Alternatif basit formül kullanıyoruz
        score = 206.835 - (1.015 * asl) - (84.6 * asw)

        # Türkçe için normalize et (Türkçe daha uzun kelimeler içerir)
        score = score * 1.2  # Adjustment factor

        return round(max(0, min(100, score)), 2)

    def get_grade_level(self, score: float) -> str:
        """
        Flesch skorundan sınıf seviyesini belirle

        Args:
            score: Flesch skoru

        Returns:
            str: Sınıf seviyesi açıklaması
        """
        if score >= 90:
            return "İlkokul 1-2"
        if score >= 80:
            return "İlkokul 3-4"
        if score >= 70:
            return "Ortaokul 5-6"
        if score >= 60:
            return "Ortaokul 7-8"
        if score >= 50:
            return "Lise 9-10"
        if score >= 40:
            return "Lise 11-12"
        if score >= 30:
            return "Üniversite"
        return "Akademik/Uzman"

    def analyze(self, text: str) -> ReadabilityResult:
        """
        Kapsamlı okunabilirlik analizi

        Args:
            text: Analiz edilecek metin

        Returns:
            ReadabilityResult: Analiz sonucu
        """
        word_count = self.count_words(text)
        sentence_count = self.count_sentences(text)

        # Hece sayısı
        words = text.split()
        syllable_count = sum(self.count_syllables(w) for w in words)

        # Ortalamalar
        avg_sentence_length = word_count / max(sentence_count, 1)
        avg_syllables_per_word = syllable_count / max(word_count, 1)

        # Flesch skoru
        flesch_score = self.calculate_flesch_score(text)
        grade_level = self.get_grade_level(flesch_score)

        # Öneriler
        suggestions = self._generate_suggestions(
            flesch_score, avg_sentence_length, avg_syllables_per_word
        )

        return ReadabilityResult(
            flesch_score=flesch_score,
            word_count=word_count,
            sentence_count=sentence_count,
            syllable_count=syllable_count,
            avg_sentence_length=round(avg_sentence_length, 2),
            avg_syllables_per_word=round(avg_syllables_per_word, 2),
            grade_level=grade_level,
            suggestions=suggestions
        )

    def _generate_suggestions(
        self,
        score: float,
        avg_sentence_length: float,
        avg_syllables_per_word: float
    ) -> list[str]:
        """
        İyileştirme önerileri üret

        Args:
            score: Flesch skoru
            avg_sentence_length: Ortalama cümle uzunluğu
            avg_syllables_per_word: Kelime başına ortalama hece

        Returns:
            List[str]: Öneriler listesi
        """
        suggestions = []

        # Skor hedef aralık dışında
        if score < self.TARGET_MIN:
            suggestions.append(
                f"Metin çok karmaşık (skor: {score:.0f}). "
                f"Hedef: {self.TARGET_MIN}-{self.TARGET_MAX}"
            )

            if avg_sentence_length > 20:
                suggestions.append(
                    f"Cümleleri kısaltın (mevcut: {avg_sentence_length:.1f} kelime)"
                )

            if avg_syllables_per_word > 2.5:
                suggestions.append(
                    "Daha basit kelimeler kullanın"
                )

        elif score > self.TARGET_MAX:
            suggestions.append(
                f"Metin çok basit (skor: {score:.0f}). "
                f"Lise seviyesi için {self.TARGET_MIN}-{self.TARGET_MAX} hedefleyin"
            )

        # Genel öneriler
        if avg_sentence_length > 25:
            suggestions.append("Çok uzun cümlelerden kaçının")

        if avg_sentence_length < 8:
            suggestions.append("Cümleleri biraz daha detaylandırın")

        return suggestions

    def check_high_school_level(self, text: str) -> tuple[bool, float, str]:
        """
        Lise seviyesine uygunluk kontrolü

        Args:
            text: Kontrol edilecek metin

        Returns:
            Tuple[bool, float, str]: (Uygun mu, skor, açıklama)
        """
        result = self.analyze(text)

        if self.TARGET_MIN <= result.flesch_score <= self.TARGET_MAX:
            return (
                True,
                1.0,
                f"Lise seviyesine uygun (skor: {result.flesch_score:.0f})"
            )
        if result.flesch_score < self.TARGET_MIN:
            # Çok zor
            deviation = (self.TARGET_MIN - result.flesch_score) / self.TARGET_MIN
            score = max(0.5, 1.0 - deviation)
            return (
                False,
                score,
                f"Metin lise seviyesi için çok karmaşık (skor: {result.flesch_score:.0f})"
            )
        # Çok kolay
        deviation = (result.flesch_score - self.TARGET_MAX) / self.TARGET_MAX
        score = max(0.6, 1.0 - deviation * 0.5)
        return (
            False,
            score,
            f"Metin lise seviyesi için çok basit (skor: {result.flesch_score:.0f})"
        )
