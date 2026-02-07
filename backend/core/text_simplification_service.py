"""
Metin Basitleştirme Servisi
Task 80: Text Simplification for Dyslexia Support
Requirements: REQ-50.57 - REQ-50.72

Bu servis, disleksi desteği için metinleri basitleştirir:
- Karmaşık kelime tespiti ve değiştirme
- Uzun cümle bölme
- Flesch-Kincaid okunabilirlik skoru hesaplama
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ComplexWord:
    """Karmaşık kelime bilgisi"""

    word: str
    complexity_score: float
    position: int
    suggested_replacements: List[str]
    frequency_score: float


@dataclass
class SimplificationResult:
    """Basitleştirme sonucu"""

    original_text: str
    simplified_text: str
    complex_words_replaced: int
    sentences_split: int
    readability_improvement: float
    original_flesch_score: float
    simplified_flesch_score: float
    suggestions: List[Dict]


class TextSimplificationService:
    """Türkçe metin basitleştirme servisi"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_word_frequency_db()
        self._initialize_synonym_dictionary()

    def _initialize_word_frequency_db(self):
        """Türkçe kelime frekans veritabanını başlat"""
        # Türkçe'de en sık kullanılan 5000 kelime (basitleştirilmiş liste)
        # Gerçek uygulamada bu bir dosyadan veya veritabanından yüklenmelidir
        self.common_words = {
            # Temel kelimeler (frekans: 1.0 - en sık)
            "ve",
            "bir",
            "bu",
            "için",
            "ile",
            "da",
            "de",
            "var",
            "yok",
            "gibi",
            "çok",
            "daha",
            "en",
            "kadar",
            "sonra",
            "önce",
            "şimdi",
            "bugün",
            "yarın",
            "dün",
            "gün",
            "saat",
            "dakika",
            "yıl",
            "ay",
            "hafta",
            # Yaygın fiiller
            "olmak",
            "yapmak",
            "etmek",
            "gelmek",
            "gitmek",
            "almak",
            "vermek",
            "görmek",
            "bilmek",
            "söylemek",
            "demek",
            "istemek",
            "gelmek",
            # Yaygın isimler
            "insan",
            "kişi",
            "çocuk",
            "anne",
            "baba",
            "arkadaş",
            "öğrenci",
            "öğretmen",
            "okul",
            "ev",
            "iş",
            "yer",
            "zaman",
            "şey",
            "durum",
            # Sıfatlar
            "iyi",
            "kötü",
            "güzel",
            "büyük",
            "küçük",
            "yeni",
            "eski",
            "uzun",
            "kısa",
            "kolay",
            "zor",
            "hızlı",
            "yavaş",
            "sıcak",
            "soğuk",
        }

        # Kelime frekans skorları (0.0 - 1.0)
        self.word_frequency = {}
        for word in self.common_words:
            self.word_frequency[word] = 1.0

        self.logger.info(
            f"Kelime frekans veritabanı başlatıldı: {len(self.common_words)} kelime"
        )

    def _initialize_synonym_dictionary(self):
        """Türkçe eşanlamlı kelime sözlüğünü başlat"""
        # Karmaşık -> Basit eşanlamlılar
        self.synonyms = {
            # Akademik/Osmanlıca -> Modern Türkçe
            "müteakip": ["sonraki", "daha sonra"],
            "mahiyet": ["özellik", "nitelik"],
            "müşahede": ["gözlem", "izleme"],
            "istihsal": ["üretim", "yapım"],
            "teşebbüs": ["girişim", "deneme"],
            "mütalaaa": ["inceleme", "okuma"],
            "müracaat": ["başvuru", "istek"],
            "istifade": ["yararlanma", "kullanma"],
            "tahsis": ["ayırma", "verme"],
            "tedvin": ["düzenleme", "hazırlama"],
            # Karmaşık kelimeler -> Basit alternatifler
            "kullanmak": ["kullanmak"],  # Zaten basit
            "gerçekleştirmek": ["yapmak", "tamamlamak"],
            "oluşturmak": ["yapmak", "kurmak"],
            "değerlendirmek": ["incelemek", "bakmak"],
            "belirlemek": ["saptamak", "bulmak"],
            "sağlamak": ["vermek", "sunmak"],
            "geliştirmek": ["iyileştirmek", "büyütmek"],
            "uygulamak": ["yapmak", "kullanmak"],
            "açıklamak": ["anlatmak", "söylemek"],
            "tanımlamak": ["anlatmak", "belirtmek"],
            # Teknik terimler -> Günlük dil
            "algoritma": ["yöntem", "işlem"],
            "parametre": ["değer", "ayar"],
            "optimizasyon": ["iyileştirme", "en iyi hale getirme"],
            "implementasyon": ["uygulama", "yapım"],
            "konfigürasyon": ["ayar", "düzenleme"],
            "validasyon": ["doğrulama", "kontrol"],
            "iterasyon": ["tekrar", "döngü"],
            "entegrasyon": ["birleştirme", "bağlama"],
        }

        self.logger.info(f"Eşanlamlı sözlük başlatıldı: {len(self.synonyms)} kelime")

    # Task 80.1: Karmaşık Kelime Tespiti
    def detect_complex_words(
        self, text: str, complexity_threshold: float = 0.6
    ) -> List[ComplexWord]:
        """
        Metindeki karmaşık kelimeleri tespit et

        Args:
            text: Analiz edilecek metin
            complexity_threshold: Karmaşıklık eşiği (0.0-1.0)

        Returns:
            Karmaşık kelime listesi

        Requirements: REQ-50.57, REQ-50.58, REQ-50.59, REQ-50.60
        """
        complex_words = []

        # Metni kelimelere ayır
        words = re.findall(r"\b\w+\b", text.lower())

        for i, word in enumerate(words):
            # Kelime karmaşıklık skorunu hesapla
            complexity_score = self._calculate_word_complexity(word)

            # Eşik değerini aşan kelimeleri tespit et
            if complexity_score >= complexity_threshold:
                # Frekans skorunu hesapla
                frequency_score = self._get_word_frequency(word)

                # Basit eşanlamlıları bul
                replacements = self._find_simple_synonyms(word)

                complex_word = ComplexWord(
                    word=word,
                    complexity_score=complexity_score,
                    position=i,
                    suggested_replacements=replacements,
                    frequency_score=frequency_score,
                )

                complex_words.append(complex_word)

        self.logger.info(f"Tespit edilen karmaşık kelime sayısı: {len(complex_words)}")
        return complex_words

    def _calculate_word_complexity(self, word: str) -> float:
        """
        Kelimenin karmaşıklık skorunu hesapla

        Faktörler:
        - Kelime uzunluğu
        - Hece sayısı
        - Frekans (ne kadar nadir o kadar karmaşık)
        - Türkçe kök-ek yapısı
        """
        score = 0.0

        # 1. Uzunluk faktörü (0-0.4)
        length = len(word)
        if length <= 4:
            length_score = 0.0
        elif length <= 7:
            length_score = 0.1
        elif length <= 10:
            length_score = 0.2
        elif length <= 13:
            length_score = 0.3
        else:
            length_score = 0.4

        score += length_score

        # 2. Hece sayısı faktörü (0-0.3)
        syllable_count = self._count_syllables(word)
        if syllable_count <= 2:
            syllable_score = 0.0
        elif syllable_count <= 3:
            syllable_score = 0.1
        elif syllable_count <= 4:
            syllable_score = 0.2
        else:
            syllable_score = 0.3

        score += syllable_score

        # 3. Frekans faktörü (0-0.3)
        frequency = self._get_word_frequency(word)
        frequency_score = 0.3 * (1.0 - frequency)  # Nadir kelimeler daha karmaşık

        score += frequency_score

        return min(score, 1.0)

    def _count_syllables(self, word: str) -> int:
        """Türkçe kelimede hece sayısını say"""
        # Türkçe sesli harfler
        vowels = "aeıioöuü"
        count = 0

        for char in word.lower():
            if char in vowels:
                count += 1

        return max(count, 1)  # En az 1 hece

    def _get_word_frequency(self, word: str) -> float:
        """
        Kelimenin frekans skorunu al (0.0-1.0)
        1.0 = çok sık kullanılan
        0.0 = çok nadir
        """
        if word in self.word_frequency:
            return self.word_frequency[word]

        # Bilinmeyen kelimeler için varsayılan düşük frekans
        return 0.2

    def _find_simple_synonyms(self, word: str) -> List[str]:
        """Kelime için basit eşanlamlılar bul"""
        if word in self.synonyms:
            return self.synonyms[word]

        return []

    # Task 80.2: Basit Eşanlamlı Değiştirme
    def replace_with_synonyms(
        self,
        text: str,
        complex_words: List[ComplexWord],
        require_confirmation: bool = False,
    ) -> Tuple[str, List[Dict]]:
        """
        Karmaşık kelimeleri basit eşanlamlılarıyla değiştir

        Args:
            text: Orijinal metin
            complex_words: Karmaşık kelime listesi
            require_confirmation: Kullanıcı onayı gerekli mi?

        Returns:
            (Basitleştirilmiş metin, Değişiklik listesi)

        Requirements: REQ-50.61, REQ-50.62, REQ-50.63, REQ-50.64
        """
        simplified_text = text
        replacements = []

        # Kelimeleri pozisyona göre sırala (sondan başa doğru değiştir)
        sorted_words = sorted(complex_words, key=lambda x: x.position, reverse=True)

        for complex_word in sorted_words:
            if not complex_word.suggested_replacements:
                continue

            # En uygun eşanlamlıyı seç (ilk öneri)
            replacement = complex_word.suggested_replacements[0]

            # Bağlam duyarlı değiştirme
            pattern = r"\b" + re.escape(complex_word.word) + r"\b"

            # Değiştirme öncesi kontrol
            if require_confirmation:
                # Kullanıcı onayı için bilgi kaydet
                replacements.append(
                    {
                        "original": complex_word.word,
                        "replacement": replacement,
                        "alternatives": complex_word.suggested_replacements[1:],
                        "position": complex_word.position,
                        "complexity_score": complex_word.complexity_score,
                        "requires_confirmation": True,
                    }
                )
            else:
                # Otomatik değiştir
                simplified_text = re.sub(
                    pattern, replacement, simplified_text, flags=re.IGNORECASE
                )

                replacements.append(
                    {
                        "original": complex_word.word,
                        "replacement": replacement,
                        "alternatives": complex_word.suggested_replacements[1:],
                        "position": complex_word.position,
                        "complexity_score": complex_word.complexity_score,
                        "applied": True,
                    }
                )

        self.logger.info(f"Değiştirilen kelime sayısı: {len(replacements)}")
        return simplified_text, replacements

    # Task 80.3: Uzun Cümle Bölme
    def split_long_sentences(
        self, text: str, max_sentence_length: int = 20
    ) -> Tuple[str, int]:
        """
        Uzun cümleleri daha kısa cümlelere böl

        Args:
            text: Orijinal metin
            max_sentence_length: Maksimum kelime sayısı

        Returns:
            (Bölünmüş metin, Bölünen cümle sayısı)

        Requirements: REQ-50.65, REQ-50.66, REQ-50.67, REQ-50.68
        """
        # Cümlelere ayır
        sentences = re.split(r"([.!?]+)", text)

        simplified_sentences = []
        split_count = 0

        for i in range(0, len(sentences), 2):
            if i >= len(sentences):
                break

            sentence = sentences[i].strip()
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else "."

            if not sentence:
                continue

            # Cümle uzunluğunu kontrol et
            words = sentence.split()

            if len(words) > max_sentence_length:
                # Uzun cümleyi böl
                split_sentences = self._split_sentence(sentence, max_sentence_length)

                # Bölünen cümleleri ekle
                for j, split_sent in enumerate(split_sentences):
                    if j == len(split_sentences) - 1:
                        simplified_sentences.append(split_sent + punctuation)
                    else:
                        simplified_sentences.append(split_sent + ".")

                split_count += 1
            else:
                # Cümle yeterince kısa
                simplified_sentences.append(sentence + punctuation)

        simplified_text = " ".join(simplified_sentences)

        self.logger.info(f"Bölünen cümle sayısı: {split_count}")
        return simplified_text, split_count

    def _split_sentence(self, sentence: str, max_length: int) -> List[str]:
        """
        Tek bir uzun cümleyi bağlaçlardan böl

        Bölme stratejisi:
        1. Bağlaçları tespit et (ve, ama, fakat, ancak, çünkü, için)
        2. En uygun bölme noktasını seç
        3. Anlamı koruyarak böl
        """
        words = sentence.split()

        # Türkçe bağlaçlar
        conjunctions = [
            "ve",
            "ama",
            "fakat",
            "ancak",
            "çünkü",
            "için",
            "ki",
            "veya",
            "ya da",
        ]

        # Bağlaç pozisyonlarını bul
        conjunction_positions = []
        for i, word in enumerate(words):
            if word.lower() in conjunctions:
                conjunction_positions.append(i)

        if not conjunction_positions:
            # Bağlaç yoksa virgüllerden böl
            return self._split_by_commas(sentence, max_length)

        # En uygun bölme noktasını seç (cümle ortasına yakın)
        mid_point = len(words) // 2
        best_position = min(conjunction_positions, key=lambda x: abs(x - mid_point))

        # Cümleyi böl
        first_part = " ".join(words[:best_position])
        second_part = " ".join(words[best_position + 1 :])  # Bağlacı atla

        result = []

        # İlk parçayı ekle
        if first_part:
            result.append(first_part)

        # İkinci parça hala uzunsa, tekrar böl
        if len(second_part.split()) > max_length:
            result.extend(self._split_sentence(second_part, max_length))
        else:
            result.append(second_part)

        return result

    def _split_by_commas(self, sentence: str, max_length: int) -> List[str]:
        """Virgüllerden cümle böl"""
        parts = sentence.split(",")

        if len(parts) <= 1:
            # Virgül yoksa, zorla böl
            words = sentence.split()
            mid = len(words) // 2
            return [" ".join(words[:mid]), " ".join(words[mid:])]

        # Virgüllü parçaları birleştir
        result = []
        current = []

        for part in parts:
            current.append(part.strip())
            if len(" ".join(current).split()) >= max_length:
                result.append(" ".join(current))
                current = []

        if current:
            result.append(" ".join(current))

        return result

    # Task 80.4: Flesch-Kincaid Skoru
    def calculate_flesch_kincaid_score(self, text: str) -> Dict[str, float]:
        """
        Türkçe metin için Flesch-Kincaid okunabilirlik skorunu hesapla

        Türkçe adaptasyonu:
        - Flesch Reading Ease: 206.835 - 1.015 * (kelime/cümle) - 84.6 * (hece/kelime)
        - Flesch-Kincaid Grade Level: 0.39 * (kelime/cümle) + 11.8 * (hece/kelime) - 15.59

        Args:
            text: Analiz edilecek metin

        Returns:
            Okunabilirlik skorları ve seviye tahmini

        Requirements: REQ-50.69, REQ-50.70, REQ-50.71, REQ-50.72
        """
        # Cümle sayısını hesapla
        sentences = re.split(r"[.!?]+", text)
        sentence_count = len([s for s in sentences if s.strip()])

        if sentence_count == 0:
            return {
                "flesch_reading_ease": 0.0,
                "flesch_kincaid_grade": 0.0,
                "grade_level": "Hesaplanamadı",
                "difficulty": "Bilinmiyor",
            }

        # Kelime sayısını hesapla
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)

        if word_count == 0:
            return {
                "flesch_reading_ease": 0.0,
                "flesch_kincaid_grade": 0.0,
                "grade_level": "Hesaplanamadı",
                "difficulty": "Bilinmiyor",
            }

        # Hece sayısını hesapla
        total_syllables = sum(self._count_syllables(word) for word in words)

        # Ortalama değerleri hesapla
        avg_words_per_sentence = word_count / sentence_count
        avg_syllables_per_word = total_syllables / word_count

        # Flesch Reading Ease (0-100, yüksek = kolay)
        flesch_reading_ease = (
            206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_syllables_per_word
        )

        # Flesch-Kincaid Grade Level (sınıf seviyesi)
        flesch_kincaid_grade = (
            0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59
        )

        # Zorluk seviyesini belirle
        if flesch_reading_ease >= 90:
            difficulty = "Çok Kolay"
            grade_level = "İlkokul 1-2"
        elif flesch_reading_ease >= 80:
            difficulty = "Kolay"
            grade_level = "İlkokul 3-4"
        elif flesch_reading_ease >= 70:
            difficulty = "Oldukça Kolay"
            grade_level = "Ortaokul 5-6"
        elif flesch_reading_ease >= 60:
            difficulty = "Standart"
            grade_level = "Ortaokul 7-8"
        elif flesch_reading_ease >= 50:
            difficulty = "Oldukça Zor"
            grade_level = "Lise 9-10"
        elif flesch_reading_ease >= 30:
            difficulty = "Zor"
            grade_level = "Lise 11-12"
        else:
            difficulty = "Çok Zor"
            grade_level = "Üniversite"

        return {
            "flesch_reading_ease": round(flesch_reading_ease, 2),
            "flesch_kincaid_grade": round(flesch_kincaid_grade, 2),
            "grade_level": grade_level,
            "difficulty": difficulty,
            "statistics": {
                "sentence_count": sentence_count,
                "word_count": word_count,
                "syllable_count": total_syllables,
                "avg_words_per_sentence": round(avg_words_per_sentence, 2),
                "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            },
        }

    def get_improvement_suggestions(
        self, original_score: Dict[str, float], simplified_score: Dict[str, float]
    ) -> List[str]:
        """
        Okunabilirlik iyileştirme önerileri sun

        Requirements: REQ-50.72
        """
        suggestions = []

        original_ease = original_score.get("flesch_reading_ease", 0)
        simplified_ease = simplified_score.get("flesch_reading_ease", 0)

        improvement = simplified_ease - original_ease

        if improvement > 10:
            suggestions.append("✓ Metin okunabilirliği önemli ölçüde iyileştirildi")
        elif improvement > 5:
            suggestions.append("✓ Metin okunabilirliği iyileştirildi")
        elif improvement > 0:
            suggestions.append("✓ Metin okunabilirliğinde hafif iyileşme")
        else:
            suggestions.append("⚠ Metin okunabilirliğinde iyileşme sağlanamadı")

        # Spesifik öneriler
        stats = original_score.get("statistics", {})
        avg_words = stats.get("avg_words_per_sentence", 0)

        if avg_words > 20:
            suggestions.append("💡 Cümleleri daha kısa tutun (ortalama 15-20 kelime)")

        if original_ease < 50:
            suggestions.append("💡 Daha basit kelimeler kullanın")
            suggestions.append("💡 Uzun cümleleri bölün")

        if original_ease < 30:
            suggestions.append("💡 Teknik terimleri açıklayın")
            suggestions.append("💡 Pasif cümleleri aktif hale getirin")

        return suggestions

    # Ana Basitleştirme Fonksiyonu
    def simplify_text(
        self,
        text: str,
        complexity_threshold: float = 0.6,
        max_sentence_length: int = 20,
        replace_synonyms: bool = True,
        split_sentences: bool = True,
        require_confirmation: bool = False,
    ) -> SimplificationResult:
        """
        Metni kapsamlı şekilde basitleştir

        Args:
            text: Basitleştirilecek metin
            complexity_threshold: Karmaşıklık eşiği
            max_sentence_length: Maksimum cümle uzunluğu
            replace_synonyms: Eşanlamlı değiştirme yapılsın mı?
            split_sentences: Cümle bölme yapılsın mı?
            require_confirmation: Kullanıcı onayı gerekli mi?

        Returns:
            Basitleştirme sonucu
        """
        self.logger.info("Metin basitleştirme başlatıldı")

        # Orijinal metin skorunu hesapla
        original_flesch = self.calculate_flesch_kincaid_score(text)

        simplified_text = text
        complex_words_replaced = 0
        sentences_split = 0
        all_suggestions = []

        # 1. Karmaşık kelimeleri tespit et
        complex_words = self.detect_complex_words(text, complexity_threshold)

        # 2. Eşanlamlı değiştirme
        if replace_synonyms and complex_words:
            simplified_text, replacements = self.replace_with_synonyms(
                simplified_text, complex_words, require_confirmation
            )
            complex_words_replaced = len(
                [r for r in replacements if r.get("applied", False)]
            )
            all_suggestions.extend(replacements)

        # 3. Uzun cümleleri böl
        if split_sentences:
            simplified_text, sentences_split = self.split_long_sentences(
                simplified_text, max_sentence_length
            )

        # Basitleştirilmiş metin skorunu hesapla
        simplified_flesch = self.calculate_flesch_kincaid_score(simplified_text)

        # İyileştirme önerilerini al
        improvement_suggestions = self.get_improvement_suggestions(
            original_flesch, simplified_flesch
        )

        all_suggestions.extend(
            [
                {"type": "improvement", "text": suggestion}
                for suggestion in improvement_suggestions
            ]
        )

        # Okunabilirlik iyileştirmesini hesapla
        readability_improvement = (
            simplified_flesch["flesch_reading_ease"]
            - original_flesch["flesch_reading_ease"]
        )

        result = SimplificationResult(
            original_text=text,
            simplified_text=simplified_text,
            complex_words_replaced=complex_words_replaced,
            sentences_split=sentences_split,
            readability_improvement=round(readability_improvement, 2),
            original_flesch_score=original_flesch["flesch_reading_ease"],
            simplified_flesch_score=simplified_flesch["flesch_reading_ease"],
            suggestions=all_suggestions,
        )

        self.logger.info(
            f"Basitleştirme tamamlandı - "
            f"Değiştirilen kelime: {complex_words_replaced}, "
            f"Bölünen cümle: {sentences_split}, "
            f"Okunabilirlik iyileştirmesi: {readability_improvement:.2f}"
        )

        return result


# Global servis instance
text_simplification_service = TextSimplificationService()
