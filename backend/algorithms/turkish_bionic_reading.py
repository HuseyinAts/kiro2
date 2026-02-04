"""
Türkçe Bionic Reading Algoritması
Disleksi için Türkçe'ye özel okuma desteği

Bu modül, Bionic Reading tekniğini Türkçe'nin zengin morfolojik yapısına uyarlar.
Zemberek NLP entegrasyonu ile kök-ek ayrımı yaparak, köklerin %40'ını bold yapar,
ekleri hiç bold yapmaz.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class BionicReadingResult:
    """Bionic Reading sonuç modeli"""

    original_text: str
    bionic_text: str
    processing_time_ms: float
    word_count: int
    bold_ratio: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class TurkishMorphologyAnalysis:
    """Türkçe morfolojik analiz sonucu"""

    word: str
    root: str
    suffixes: List[str]
    is_compound: bool
    analysis_confidence: float


# Zemberek import with fallback
try:
    from zemberek.morphology import TurkishMorphology

    ZEMBEREK_AVAILABLE = True
except ImportError:
    try:
        from zemberek import TurkishMorphology

        ZEMBEREK_AVAILABLE = True
    except ImportError:
        ZEMBEREK_AVAILABLE = False


class ZemberekMorphologyAnalyzer:
    """Zemberek NLP entegrasyonu with fallback to mock"""

    def __init__(self):
        self.morphology_analyzer = self._initialize_analyzer()

        # Basit kök-ek sözlüğü (fallback için)
        self.root_suffix_patterns = {
            # Fiil çekimleri
            r"(.+)(yor|ıyor|iyor|uyor|üyor)$": (r"\1", ["yor"]),
            r"(.+)(du|dı|tu|tı)$": (r"\1", ["du"]),
            r"(.+)(acak|ecek)$": (r"\1", ["acak"]),
            r"(.+)(mış|miş|muş|müş)$": (r"\1", ["mış"]),
            # İsim çekimleri
            r"(.+)(lar|ler)$": (r"\1", ["lar"]),
            r"(.+)(ın|in|un|ün)$": (r"\1", ["ın"]),
            r"(.+)(da|de|ta|te)$": (r"\1", ["da"]),
            r"(.+)(dan|den|tan|ten)$": (r"\1", ["dan"]),
            r"(.+)(nın|nin|nun|nün)$": (r"\1", ["nın"]),
            # Sıfat-fiil ekleri
            r"(.+)(dığı|diği|duğu|düğü)$": (r"\1", ["dığı"]),
            r"(.+)(arak|erek)$": (r"\1", ["arak"]),
            # Birleşik kelimeler
            r"(.+)(sız|siz|suz|süz)$": (r"\1", ["sız"]),
        }

    def _initialize_analyzer(self):
        """Initialize Zemberek analyzer with proper error handling"""

        if not ZEMBEREK_AVAILABLE:
            return None

        try:
            if hasattr(TurkishMorphology, "createWithDefaults"):
                return TurkishMorphology.createWithDefaults()
            elif hasattr(TurkishMorphology, "builder"):
                return TurkishMorphology.builder().build()
            else:
                return TurkishMorphology()
        except Exception as e:
            logger.warning(f"Failed to initialize Zemberek: {e}")
            return None

    async def analyze(self, word: str) -> Optional[TurkishMorphologyAnalysis]:
        """Kelimeyi morfolojik olarak analiz et"""
        try:
            clean_word = word.lower().strip()

            # Try Zemberek first if available
            if self.morphology_analyzer:
                try:
                    analysis_results = self.morphology_analyzer.analyze(clean_word)
                    if analysis_results:
                        analysis = analysis_results[0]
                        return TurkishMorphologyAnalysis(
                            word=word,
                            root=analysis.getLemma()
                            if hasattr(analysis, "getLemma")
                            else clean_word,
                            suffixes=analysis.getMorphemes()[1:]
                            if hasattr(analysis, "getMorphemes")
                            else [],
                            is_compound=False,
                            analysis_confidence=0.9,
                        )
                except Exception as e:
                    logger.debug(f"Zemberek analysis failed for '{word}': {e}")

            # Fallback to pattern matching
            for pattern, (root_pattern, suffixes) in self.root_suffix_patterns.items():
                match = re.match(pattern, clean_word)
                if match:
                    root = match.group(1)
                    if len(root) >= 2:  # Minimum kök uzunluğu
                        return TurkishMorphologyAnalysis(
                            word=word,
                            root=root,
                            suffixes=suffixes,
                            is_compound=False,
                            analysis_confidence=0.7,
                        )

            # Eğer pattern bulunamazsa, kelimenin kendisi kök
            return TurkishMorphologyAnalysis(
                word=word,
                root=clean_word,
                suffixes=[],
                is_compound=False,
                analysis_confidence=0.6,
            )

        except Exception as e:
            logger.error(f"Morfolojik analiz hatası: {e}")
            return None


class TurkishBionicReading:
    """
    Türkçe Bionic Reading Algoritması

    Bionic Reading tekniğini Türkçe'nin ek yapısına uyarlar:
    - Köklerin %40'ı bold yapılır
    - Ekler hiç bold yapılmaz
    - Minimum 2, maksimum 4 karakter bold
    """

    def __init__(self):
        self.zemberek = ZemberekMorphologyAnalyzer()

        # Türkçe'ye özel Bionic Reading kuralları
        self.bionic_rules = {
            "root_bold_ratio": 0.4,  # Kökün %40'ı bold
            "suffix_bold_ratio": 0.0,  # Ekler hiç bold değil
            "min_bold_chars": 2,  # Minimum 2 karakter bold
            "max_bold_chars": 4,  # Maksimum 4 karakter bold
            "min_word_length": 3,  # Minimum kelime uzunluğu
        }

        # Noktalama işaretleri
        self.punctuation_chars = ".,!?;:()[]{}\"'-"

        # Cache için basit dictionary
        self._analysis_cache: Dict[str, TurkishMorphologyAnalysis] = {}

    async def apply_bionic_reading(
        self, text: str, use_cache: bool = True
    ) -> BionicReadingResult:
        """
        Metne Türkçe Bionic Reading uygula

        Args:
            text: İşlenecek metin
            use_cache: Cache kullanılsın mı

        Returns:
            BionicReadingResult: İşlem sonucu
        """
        start_time = datetime.now()

        try:
            if not text or not text.strip():
                return BionicReadingResult(
                    original_text=text,
                    bionic_text=text,
                    processing_time_ms=0,
                    word_count=0,
                    bold_ratio=0.0,
                    success=True,
                )

            words = text.split()
            bionic_words = []
            total_chars = 0
            bold_chars = 0

            for word in words:
                bionic_word = await self._process_word(word, use_cache)
                bionic_words.append(bionic_word)

                # İstatistik hesaplama
                clean_word, _ = self._separate_punctuation(word)
                total_chars += len(clean_word)
                bold_chars += self._count_bold_chars(bionic_word)

            bionic_text = " ".join(bionic_words)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return BionicReadingResult(
                original_text=text,
                bionic_text=bionic_text,
                processing_time_ms=processing_time,
                word_count=len(words),
                bold_ratio=bold_chars / max(total_chars, 1),
                success=True,
            )

        except Exception as e:
            logger.error(f"Bionic Reading hatası: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return BionicReadingResult(
                original_text=text,
                bionic_text=text,
                processing_time_ms=processing_time,
                word_count=0,
                bold_ratio=0.0,
                success=False,
                error_message=str(e),
            )

    async def _process_word(self, word: str, use_cache: bool) -> str:
        """Tek kelimeyi işle"""

        # Noktalama işaretlerini ayır
        clean_word, punctuation = self._separate_punctuation(word)

        if len(clean_word) < self.bionic_rules["min_word_length"]:
            # Çok kısa kelimeler için Bionic uygulanmaz
            return word

        try:
            # Cache kontrolü
            cache_key = clean_word.lower()
            if use_cache and cache_key in self._analysis_cache:
                analysis = self._analysis_cache[cache_key]
            else:
                # Zemberek ile kök ve ek analizi
                analysis = await self.zemberek.analyze(clean_word)
                if use_cache and analysis:
                    self._analysis_cache[cache_key] = analysis

            if analysis and analysis.root:
                bionic_word = self._apply_turkish_bionic_rules(
                    analysis.root, "".join(analysis.suffixes)
                )
                return f"{bionic_word}{punctuation}"
            else:
                # Analiz başarısızsa basit bold uygula
                return self._apply_simple_bionic(clean_word, punctuation)

        except Exception as e:
            logger.warning(f"Kelime işleme hatası ({word}): {e}")
            return self._apply_simple_bionic(clean_word, punctuation)

    def _apply_turkish_bionic_rules(self, root: str, suffixes: str) -> str:
        """Türkçe'ye özel Bionic Reading kuralları uygula"""

        if not root:
            return root + suffixes

        # KÖKÜN ilk %40'ı bold (İngilizce'den farklı!)
        bold_length = max(
            self.bionic_rules["min_bold_chars"],
            min(
                self.bionic_rules["max_bold_chars"],
                int(len(root) * self.bionic_rules["root_bold_ratio"]),
            ),
        )

        # Kök uzunluğunu aşmayacak şekilde ayarla
        bold_length = min(bold_length, len(root))

        # Türkçe'ye özel: Ekler hiç bold yapılmaz
        bionic_word = f"**{root[:bold_length]}**{root[bold_length:]}{suffixes}"

        return bionic_word

    def _apply_simple_bionic(self, clean_word: str, punctuation: str) -> str:
        """Basit Bionic Reading uygula (analiz başarısızsa)"""

        bold_length = max(
            self.bionic_rules["min_bold_chars"],
            min(self.bionic_rules["max_bold_chars"], len(clean_word) // 3),
        )

        return f"**{clean_word[:bold_length]}**{clean_word[bold_length:]}{punctuation}"

    def _separate_punctuation(self, word: str) -> Tuple[str, str]:
        """Kelime ve noktalama işaretlerini ayır"""
        punctuation = ""
        clean_word = word

        # Sondaki noktalama işaretlerini ayır
        while clean_word and clean_word[-1] in self.punctuation_chars:
            punctuation = clean_word[-1] + punctuation
            clean_word = clean_word[:-1]

        return clean_word, punctuation

    async def turkish_bionic_reading(self, text: str) -> str:
        """
        Türkçe Bionic Reading uygula (test uyumluluğu için)

        Args:
            text: İşlenecek metin

        Returns:
            str: Bionic Reading uygulanmış metin
        """
        result = await self.apply_bionic_reading(text)
        return result.bionic_text

    def _count_bold_chars(self, bionic_word: str) -> int:
        """Bold karakterlerin sayısını hesapla"""
        # **text** formatındaki bold karakterleri say
        bold_pattern = r"\*\*([^*]+)\*\*"
        matches = re.findall(bold_pattern, bionic_word)
        return sum(len(match) for match in matches)

    def clear_cache(self):
        """Analiz cache'ini temizle"""
        self._analysis_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Cache istatistiklerini döndür"""
        return {
            "cache_size": len(self._analysis_cache),
            "cache_keys": list(self._analysis_cache.keys())[:10],  # İlk 10 anahtar
        }


# Örnek kullanım ve test fonksiyonları
async def test_turkish_bionic_reading():
    """Test fonksiyonu"""

    bionic_reader = TurkishBionicReading()

    test_texts = [
        "Çocuklar bahçede oynuyorlar.",
        "Öğrenciler derslerini çalışıyorlar.",
        "Kitapları okumayı seviyorum.",
        "Türkiye'nin en güzel şehirlerinden biri İstanbul'dur.",
        "Matematik dersinde başarılı olmak için düzenli çalışmak gerekir.",
    ]

    print("Türkçe Bionic Reading Test Sonuçları:")
    print("=" * 50)

    for text in test_texts:
        result = await bionic_reader.apply_bionic_reading(text)

        print(f"Orijinal: {result.original_text}")
        print(f"Bionic:   {result.bionic_text}")
        print(f"İşlem süresi: {result.processing_time_ms:.2f}ms")
        print(f"Bold oranı: {result.bold_ratio:.2%}")
        print("-" * 30)


if __name__ == "__main__":
    asyncio.run(test_turkish_bionic_reading())
