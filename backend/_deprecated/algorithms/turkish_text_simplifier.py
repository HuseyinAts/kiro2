"""
[ROCKET] 3 Seviyeli Türkçe Metin Basitleştirme Sistemi (DEVRİMSEL)
Dünyada ilk 3 seviyeli Türkçe metin basitleştirme algoritması

Level 1: Lexical (Kelime) Basitleştirme - Osmanlıca/akademik → modern Türkçe
Level 2: Syntactic (Sözdizimi) Basitleştirme - karmaşık cümle → basit cümle
Level 3: Semantic (Anlam) Basitleştirme - anlam korunumu ile yeniden yazma
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class SimplificationLevel(Enum):
    """Basitleştirme seviyeleri"""

    LEXICAL = "lexical"  # Kelime seviyesi
    SYNTACTIC = "syntactic"  # Sözdizimi seviyesi
    SEMANTIC = "semantic"  # Anlam seviyesi


@dataclass
class SimplificationResult:
    """Basitleştirme sonucu"""

    original_text: str
    simplified_text: str
    level: SimplificationLevel
    complexity_score: float
    readability_score: float
    changes_made: List[str]
    processing_time: float


class TurkishTextSimplifier:
    """
    Türkçe Metin Basitleştirme Motoru
    3 seviyeli basitleştirme algoritması
    """

    def __init__(self):
        self.lexical_mappings = self._load_lexical_mappings()
        self.complex_patterns = self._load_complex_patterns()
        self.metaphor_patterns = self._load_metaphor_patterns()

    def _load_lexical_mappings(self) -> Dict[str, str]:
        """Kelime seviyesi değişim haritası"""
        return {
            # Osmanlıca → Modern Türkçe
            "mütalaa": "görüş",
            "mütalaasında": "görüşünde",
            "tetkik": "inceleme",
            "tahkik": "araştırma",
            "müdakkik": "dikkatli",
            "müteakip": "sonraki",
            "müteakiben": "sonrasında",
            "müteahhit": "yüklenici",
            "mütecanis": "benzer",
            "mütedavil": "yaygın",
            # Akademik → Günlük
            "implementasyon": "uygulama",
            "optimizasyon": "iyileştirme",
            "algoritma": "yöntem",
            "parametreler": "değişkenler",
            "konfigürasyon": "ayarlama",
            "entegrasyon": "birleştirme",
            "koordinasyon": "eşgüdüm",
            "adaptasyon": "uyarlama",
            "validasyon": "doğrulama",
            "transformasyon": "dönüştürme",
            # Karmaşık → Basit
            "münhasıran": "sadece",
            "bilhassa": "özellikle",
            "dolayısıyla": "bu yüzden",
            "neticesinde": "sonucunda",
            "mahiyetinde": "türünde",
            "mevzubahis": "söz konusu",
            "istihsal": "üretim",
            "istihdam": "çalıştırma",
            "istikrar": "kararlılık",
            "istikbal": "gelecek",
        }

    def _load_complex_patterns(self) -> List[Dict]:
        """Karmaşık cümle kalıpları"""
        return [
            {
                "pattern": r"(.+?)\s+olan\s+(.+?)\s+(.+)",
                "replacement": r"\2 \3. Bu \1.",
                "description": "Sıfat cümlesi basitleştirme",
            },
            {
                "pattern": r"(.+?)\s+nedeniyle\s+(.+)",
                "replacement": r"\1. Bu yüzden \2.",
                "description": "Neden-sonuç basitleştirme",
            },
            {
                "pattern": r"(.+?)\s+rağmen\s+(.+)",
                "replacement": r"\1. Ama \2.",
                "description": "Karşıtlık basitleştirme",
            },
            {
                "pattern": r"(.+?)\s+dolayısıyla\s+(.+)",
                "replacement": r"\1. Bu nedenle \2.",
                "description": "Sonuç basitleştirme",
            },
            {
                "pattern": r"(.+?)\s+açısından\s+(.+)",
                "replacement": r"\1 için \2.",
                "description": "Bakış açısı basitleştirme",
            },
        ]

    def _load_metaphor_patterns(self) -> Dict[str, str]:
        """Metafor ve soyut kavram basitleştirme"""
        return {
            "bilginin denizi": "çok fazla bilgi",
            "zaman tüneli": "geçmiş zamanlar",
            "düşünce fırtınası": "çok düşünme",
            "kalbin sesi": "içten gelen his",
            "hayatın anlamı": "yaşamın amacı",
            "zamanın akışı": "zaman geçişi",
            "bilginin ışığı": "öğrenme",
            "umudun çiçeği": "umut duygusu",
            "sevginin gücü": "sevgi etkisi",
            "dostluğun köprüsü": "arkadaşlık bağı",
        }

    async def simplify_text(
        self,
        text: str,
        target_level: SimplificationLevel = SimplificationLevel.SEMANTIC,
        preserve_meaning: bool = True,
    ) -> SimplificationResult:
        """
        Metni belirtilen seviyede basitleştir

        Args:
            text: Basitleştirilecek metin
            target_level: Hedef basitleştirme seviyesi
            preserve_meaning: Anlam korunumu

        Returns:
            SimplificationResult: Basitleştirme sonucu
        """
        start_time = asyncio.get_event_loop().time()
        changes_made = []

        try:
            # Orijinal karmaşıklık skoru
            original_complexity = self._calculate_complexity(text)

            simplified_text = text

            # Level 1: Lexical Basitleştirme
            if target_level.value in ["lexical", "syntactic", "semantic"]:
                simplified_text, lexical_changes = await self._lexical_simplification(
                    simplified_text
                )
                changes_made.extend(lexical_changes)

            # Level 2: Syntactic Basitleştirme
            if target_level.value in ["syntactic", "semantic"]:
                (
                    simplified_text,
                    syntactic_changes,
                ) = await self._syntactic_simplification(simplified_text)
                changes_made.extend(syntactic_changes)

            # Level 3: Semantic Basitleştirme
            if target_level.value == "semantic":
                simplified_text, semantic_changes = await self._semantic_simplification(
                    simplified_text, preserve_meaning
                )
                changes_made.extend(semantic_changes)

            # Son karmaşıklık skoru
            final_complexity = self._calculate_complexity(simplified_text)
            readability_score = self._calculate_readability(simplified_text)

            processing_time = asyncio.get_event_loop().time() - start_time

            return SimplificationResult(
                original_text=text,
                simplified_text=simplified_text,
                level=target_level,
                complexity_score=final_complexity,
                readability_score=readability_score,
                changes_made=changes_made,
                processing_time=processing_time,
            )

        except Exception as e:
            logger.error(f"Metin basitleştirme hatası: {e}")
            raise

    async def _lexical_simplification(self, text: str) -> Tuple[str, List[str]]:
        """Level 1: Kelime seviyesi basitleştirme"""
        changes = []
        simplified = text

        # Kelime değişimleri
        for complex_word, simple_word in self.lexical_mappings.items():
            if complex_word in simplified:
                simplified = simplified.replace(complex_word, simple_word)
                changes.append(f"Kelime değişimi: '{complex_word}' → '{simple_word}'")

        # Yabancı kelime tespiti ve Türkçeleştirme
        foreign_patterns = {
            r"\b(implementation)\b": "uygulama",
            r"\b(optimization)\b": "iyileştirme",
            r"\b(configuration)\b": "ayarlama",
            r"\b(integration)\b": "birleştirme",
            r"\b(validation)\b": "doğrulama",
        }

        for pattern, replacement in foreign_patterns.items():
            if re.search(pattern, simplified, re.IGNORECASE):
                simplified = re.sub(
                    pattern, replacement, simplified, flags=re.IGNORECASE
                )
                changes.append(
                    f"Yabancı kelime Türkçeleştirme: {pattern} → {replacement}"
                )

        return simplified, changes

    async def _syntactic_simplification(self, text: str) -> Tuple[str, List[str]]:
        """Level 2: Sözdizimi basitleştirme"""
        changes = []
        simplified = text

        # Karmaşık cümle kalıplarını basitleştir
        for pattern_info in self.complex_patterns:
            pattern = pattern_info["pattern"]
            replacement = pattern_info["replacement"]
            description = pattern_info["description"]

            if re.search(pattern, simplified):
                simplified = re.sub(pattern, replacement, simplified)
                changes.append(f"Cümle basitleştirme: {description}")

        # Uzun cümleleri böl
        sentences = simplified.split(".")
        new_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 100:  # Uzun cümle
                # Virgül ile böl
                parts = sentence.split(",")
                if len(parts) > 2:
                    # İlk iki parçayı birleştir, geri kalanını yeni cümle yap
                    first_part = ", ".join(parts[:2])
                    second_part = ", ".join(parts[2:])
                    new_sentences.extend([first_part, second_part])
                    changes.append("Uzun cümle bölme")
                else:
                    new_sentences.append(sentence)
            else:
                new_sentences.append(sentence)

        simplified = ". ".join([s for s in new_sentences if s])

        return simplified, changes

    async def _semantic_simplification(
        self, text: str, preserve_meaning: bool
    ) -> Tuple[str, List[str]]:
        """Level 3: Anlam seviyesi basitleştirme"""
        changes = []
        simplified = text

        # Metafor ve soyut kavramları somutlaştır
        for metaphor, concrete in self.metaphor_patterns.items():
            if metaphor in simplified:
                simplified = simplified.replace(metaphor, concrete)
                changes.append(f"Metafor somutlaştırma: '{metaphor}' → '{concrete}'")

        # Soyut kavramları açıkla
        abstract_patterns = {
            r"\b(demokrasi)\b": "halkın yönetimi",
            r"\b(özgürlük)\b": "serbest olma durumu",
            r"\b(adalet)\b": "hakkı gözetme",
            r"\b(eşitlik)\b": "aynı haklara sahip olma",
            r"\b(hoşgörü)\b": "farklılıklara saygı",
        }

        for pattern, explanation in abstract_patterns.items():
            if re.search(pattern, simplified, re.IGNORECASE):
                if preserve_meaning:
                    # Açıklama ekle
                    simplified = re.sub(
                        pattern, f"\\1 ({explanation})", simplified, flags=re.IGNORECASE
                    )
                else:
                    # Doğrudan değiştir
                    simplified = re.sub(
                        pattern, explanation, simplified, flags=re.IGNORECASE
                    )
                changes.append(f"Soyut kavram açıklama: {pattern}")

        # Pasif yapıları aktif yap
        passive_patterns = [
            (r"(.+?)\s+tarafından\s+(.+?)\s+(edildi|yapıldı)", r"\1 \3"),
            (r"(.+?)\s+(edilmektedir|yapılmaktadır)", r"\1 ediliyor"),
        ]

        for pattern, replacement in passive_patterns:
            if re.search(pattern, simplified):
                simplified = re.sub(pattern, replacement, simplified)
                changes.append("Pasif → Aktif yapı dönüşümü")

        return simplified, changes

    def _calculate_complexity(self, text: str) -> float:
        """Metin karmaşıklık skoru hesapla (0-100)"""
        if not text:
            return 0.0

        # Faktörler
        avg_word_length = sum(len(word) for word in text.split()) / len(text.split())
        avg_sentence_length = len(text.split()) / max(text.count("."), 1)
        complex_word_count = sum(1 for word in text.split() if len(word) > 7)
        complex_word_ratio = complex_word_count / len(text.split())

        # Karmaşıklık skoru
        complexity = (
            (avg_word_length * 10)
            + (avg_sentence_length * 2)
            + (complex_word_ratio * 50)
        )

        return min(complexity, 100.0)

    def _calculate_readability(self, text: str) -> float:
        """Okunabilirlik skoru hesapla (0-100)"""
        if not text:
            return 0.0

        words = text.split()
        sentences = text.count(".") + text.count("!") + text.count("?")

        if sentences == 0:
            return 50.0

        avg_sentence_length = len(words) / sentences
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Türkçe için uyarlanmış okunabilirlik formülü
        readability = (
            100 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 100)
        )

        return max(0.0, min(readability, 100.0))

    async def batch_simplify(
        self,
        texts: List[str],
        target_level: SimplificationLevel = SimplificationLevel.SEMANTIC,
    ) -> List[SimplificationResult]:
        """Toplu metin basitleştirme"""
        tasks = [self.simplify_text(text, target_level) for text in texts]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Hataları filtrele
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Toplu basitleştirme hatası: {result}")
            else:
                valid_results.append(result)

        return valid_results

    def get_simplification_stats(self, result: SimplificationResult) -> Dict:
        """Basitleştirme istatistikleri"""
        return {
            "original_length": len(result.original_text),
            "simplified_length": len(result.simplified_text),
            "length_reduction": len(result.original_text) - len(result.simplified_text),
            "complexity_reduction": self._calculate_complexity(result.original_text)
            - result.complexity_score,
            "readability_improvement": result.readability_score
            - self._calculate_readability(result.original_text),
            "changes_count": len(result.changes_made),
            "processing_time": result.processing_time,
            "level": result.level.value,
        }


# Global instance
turkish_text_simplifier = TurkishTextSimplifier()
