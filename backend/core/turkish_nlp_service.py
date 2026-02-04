"""
Türkçe NLP Servisi - Zemberek entegrasyonu ile morfolojik analiz
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MorphologicalAnalysis:
    """Morfolojik analiz sonucu"""

    word: str
    root: str
    suffixes: list[str]
    pos_tag: str  # Part of speech
    derivational_depth: int
    is_compound: bool
    compound_parts: list[str]
    complexity_score: float


@dataclass
class TextNormalizationResult:
    """Metin normalizasyon sonucu"""

    original_text: str
    normalized_text: str
    corrections: list[dict[str, str]]
    encoding_issues_fixed: int
    turkish_chars_normalized: int


class TurkishNLPService:
    """
    Türkçe doğal dil işleme servisi
    Zemberek-NLP entegrasyonu ile morfolojik analiz ve metin işleme
    """

    def __init__(self):
        self.zemberek_server_url = "http://localhost:6789"  # Zemberek server
        self.session: aiohttp.ClientSession | None = None

        # Türkçe karakter dönüşüm tablosu
        self.turkish_char_map = {
            "ç": "c",
            "ğ": "g",
            "ı": "i",
            "ö": "o",
            "ş": "s",
            "ü": "u",
            "Ç": "C",
            "Ğ": "G",
            "I": "I",
            "Ö": "O",
            "Ş": "S",
            "Ü": "U",
        }

        # Türkçe karakter normalizasyon
        self.normalize_map = {
            "â": "a",
            "î": "i",
            "û": "u",
            "ô": "o",
            "Â": "A",
            "Î": "I",
            "Û": "U",
            "Ô": "O",
        }

        # Yaygın yazım hataları
        self.common_corrections = {
            "birşey": "bir şey",
            "herşey": "her şey",
            "neden": "neden",
            "hemde": "hem de",
            "yinede": "yine de",
            "birde": "bir de",
            "herzaman": "her zaman",
            "herkes": "herkes",
            "hiçbirşey": "hiçbir şey",
        }

        # Karmaşıklık faktörleri
        self.complexity_weights = {
            "suffix_count": 0.15,
            "derivational_depth": 0.20,
            "compound_complexity": 0.25,
            "phonetic_changes": 0.10,
            "semantic_ambiguity": 0.30,
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def initialize(self) -> bool:
        """
        NLP servisini başlat ve Zemberek bağlantısını test et
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                )

            # Zemberek server'ın çalışıp çalışmadığını kontrol et
            health_check = await self._check_zemberek_health()

            if health_check:
                logger.info("Türkçe NLP servisi başarıyla başlatıldı")
                return True
            logger.warning(
                "Zemberek server'a bağlanılamadı, fallback modda çalışılacak"
            )
            return False

        except Exception as e:
            logger.error(f"NLP servisi başlatılırken hata: {e}")
            return False

    async def _check_zemberek_health(self) -> bool:
        """Zemberek server sağlık kontrolü"""
        try:
            async with self.session.get(
                f"{self.zemberek_server_url}/health"
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def analyze_morphology(self, word: str) -> MorphologicalAnalysis | None:
        """
        Kelimenin morfolojik analizini yap

        Args:
            word: Analiz edilecek kelime

        Returns:
            MorphologicalAnalysis: Morfolojik analiz sonucu
        """
        try:
            # Önce kelimeyi temizle
            clean_word = self._clean_word(word)

            if not clean_word:
                return None

            # Zemberek ile analiz yap
            zemberek_result = await self._call_zemberek_morphology(clean_word)

            if zemberek_result:
                return self._parse_zemberek_result(clean_word, zemberek_result)
            # Fallback: basit analiz
            return self._fallback_morphology_analysis(clean_word)

        except Exception as e:
            logger.error(f"Morfolojik analiz hatası: {e}")
            return self._fallback_morphology_analysis(word)

    async def _call_zemberek_morphology(self, word: str) -> dict | None:
        """Zemberek API'ye morfoloji analizi çağrısı"""
        try:
            if not self.session:
                return None

            payload = {"word": word}

            async with self.session.post(
                f"{self.zemberek_server_url}/morphology/analyze", json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                logger.warning(f"Zemberek API hatası: {response.status}")
                return None

        except Exception as e:
            logger.error(f"Zemberek API çağrısı hatası: {e}")
            return None

    def _parse_zemberek_result(self, word: str, result: dict) -> MorphologicalAnalysis:
        """Zemberek sonucunu parse et"""
        try:
            # Zemberek sonuç formatını parse et
            analyses = result.get("analyses", [])

            if not analyses:
                return self._fallback_morphology_analysis(word)

            # İlk analizi al (en olası)
            first_analysis = analyses[0]

            root = first_analysis.get("root", word)
            suffixes = first_analysis.get("suffixes", [])
            pos_tag = first_analysis.get("pos", "UNKNOWN")

            # Türetim derinliğini hesapla
            derivational_depth = len(
                [s for s in suffixes if s.get("type") == "DERIVATIONAL"]
            )

            # Birleşik kelime kontrolü
            is_compound = first_analysis.get("isCompound", False)
            compound_parts = first_analysis.get("compoundParts", [])

            # Karmaşıklık skoru hesapla
            complexity_score = self._calculate_complexity_score(
                len(suffixes), derivational_depth, len(compound_parts)
            )

            return MorphologicalAnalysis(
                word=word,
                root=root,
                suffixes=[s.get("suffix", "") for s in suffixes],
                pos_tag=pos_tag,
                derivational_depth=derivational_depth,
                is_compound=is_compound,
                compound_parts=compound_parts,
                complexity_score=complexity_score,
            )

        except Exception as e:
            logger.error(f"Zemberek sonuç parse hatası: {e}")
            return self._fallback_morphology_analysis(word)

    def _fallback_morphology_analysis(self, word: str) -> MorphologicalAnalysis:
        """Zemberek olmadan basit morfoloji analizi"""

        # Basit kök-ek ayrımı (heuristik)
        root, suffixes = self._simple_root_suffix_split(word)

        # Basit karmaşıklık hesaplama
        complexity_score = min(1.0, len(suffixes) * 0.2 + len(word) * 0.05)

        return MorphologicalAnalysis(
            word=word,
            root=root,
            suffixes=suffixes,
            pos_tag="UNKNOWN",
            derivational_depth=len(suffixes),
            is_compound=False,
            compound_parts=[],
            complexity_score=complexity_score,
        )

    def _simple_root_suffix_split(self, word: str) -> tuple[str, list[str]]:
        """Basit kök-ek ayrımı (heuristik)"""

        # Yaygın Türkçe ekleri
        common_suffixes = [
            "lar",
            "ler",
            "dan",
            "den",
            "tan",
            "ten",
            "nın",
            "nin",
            "nun",
            "nün",
            "nda",
            "nde",
            "nı",
            "ni",
            "nu",
            "nü",
            "ya",
            "ye",
            "yla",
            "yle",
            "dır",
            "dir",
            "dur",
            "dür",
            "tır",
            "tir",
            "tur",
            "tür",
        ]

        suffixes = []
        remaining = word.lower()

        # Sondan başlayarak ekleri bul
        for suffix in sorted(common_suffixes, key=len, reverse=True):
            if remaining.endswith(suffix) and len(remaining) > len(suffix):
                suffixes.insert(0, suffix)
                remaining = remaining[: -len(suffix)]
                break

        return remaining, suffixes

    def _calculate_complexity_score(
        self, suffix_count: int, derivational_depth: int, compound_parts: int
    ) -> float:
        """Kelime karmaşıklık skoru hesapla"""

        score = (
            suffix_count * self.complexity_weights["suffix_count"]
            + derivational_depth * self.complexity_weights["derivational_depth"]
            + compound_parts * self.complexity_weights["compound_complexity"]
        )

        return min(1.0, score)

    async def normalize_text(self, text: str) -> TextNormalizationResult:
        """
        Metni normalize et ve temizle

        Args:
            text: Normalize edilecek metin

        Returns:
            TextNormalizationResult: Normalizasyon sonucu
        """
        try:
            original_text = text
            corrections = []
            encoding_fixes = 0
            turkish_char_fixes = 0

            # 1. Encoding sorunlarını düzelt
            normalized_text, encoding_fixes = self._fix_encoding_issues(text)

            # 2. Türkçe karakterleri normalize et
            normalized_text, turkish_char_fixes = self._normalize_turkish_chars(
                normalized_text
            )

            # 3. Yaygın yazım hatalarını düzelt
            normalized_text, corrections = self._fix_common_errors(normalized_text)

            # 4. Whitespace'leri temizle
            normalized_text = self._clean_whitespace(normalized_text)

            return TextNormalizationResult(
                original_text=original_text,
                normalized_text=normalized_text,
                corrections=corrections,
                encoding_issues_fixed=encoding_fixes,
                turkish_chars_normalized=turkish_char_fixes,
            )

        except Exception as e:
            logger.error(f"Metin normalizasyon hatası: {e}")
            return TextNormalizationResult(
                original_text=text,
                normalized_text=text,
                corrections=[],
                encoding_issues_fixed=0,
                turkish_chars_normalized=0,
            )

    def _fix_encoding_issues(self, text: str) -> tuple[str, int]:
        """Encoding sorunlarını düzelt"""
        fixes = 0

        try:
            # UTF-8 normalize
            normalized = unicodedata.normalize("NFC", text)

            # Yaygın encoding sorunları
            encoding_fixes = {
                "Ã§": "ç",
                "Ã¶": "ö",
                "Ã¼": "ü",
                "Ä±": "ı",
                "Ä°": "İ",
                "Åž": "ş",
                "Ä": "ğ",
                "â€™": "'",
                "â€œ": '"',
                "â€": '"',
            }

            for broken, fixed in encoding_fixes.items():
                if broken in normalized:
                    normalized = normalized.replace(broken, fixed)
                    fixes += 1

            return normalized, fixes

        except Exception:
            return text, 0

    def _normalize_turkish_chars(self, text: str) -> tuple[str, int]:
        """Türkçe karakterleri normalize et"""
        fixes = 0
        normalized = text

        # Eski Türkçe karakterleri modern karşılıklarına çevir
        for old_char, new_char in self.normalize_map.items():
            if old_char in normalized:
                normalized = normalized.replace(old_char, new_char)
                fixes += 1

        return normalized, fixes

    def _fix_common_errors(self, text: str) -> tuple[str, list[dict[str, str]]]:
        """Yaygın yazım hatalarını düzelt"""
        corrections = []
        normalized = text

        for wrong, correct in self.common_corrections.items():
            if wrong in normalized.lower():
                # Case-sensitive replacement
                pattern = re.compile(re.escape(wrong), re.IGNORECASE)
                matches = pattern.findall(normalized)

                if matches:
                    normalized = pattern.sub(correct, normalized)
                    corrections.append(
                        {"original": wrong, "corrected": correct, "count": len(matches)}
                    )

        return normalized, corrections

    def _clean_whitespace(self, text: str) -> str:
        """Whitespace'leri temizle"""
        # Çoklu boşlukları tek boşluğa çevir
        text = re.sub(r"\s+", " ", text)

        # Başta ve sonda boşlukları temizle
        text = text.strip()

        # Noktalama işaretlerinden önce/sonra boşlukları düzelt
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r"([,.!?;:])\s+", r"\1 ", text)

        return text

    def _clean_word(self, word: str) -> str:
        """Kelimeyi analiz için temizle"""
        if not word:
            return ""

        # Noktalama işaretlerini kaldır
        cleaned = re.sub(r"[^\w\sçğıöşüÇĞIİÖŞÜ]", "", word)

        # Boşlukları kaldır
        cleaned = cleaned.strip()

        return cleaned

    @lru_cache(maxsize=1000)
    def get_word_complexity(self, word: str) -> float:
        """Kelime karmaşıklığını hesapla (cached)"""
        try:
            # Basit karmaşıklık hesaplama
            length_factor = min(1.0, len(word) / 20)  # Uzunluk faktörü

            # Türkçe karakter yoğunluğu
            turkish_chars = sum(1 for c in word if c in "çğıöşüÇĞIİÖŞÜ")
            turkish_factor = turkish_chars / len(word) if word else 0

            # Genel karmaşıklık skoru
            complexity = (length_factor * 0.6) + (turkish_factor * 0.4)

            return min(1.0, complexity)

        except Exception:
            return 0.5  # Orta karmaşıklık

    async def analyze_text_complexity(self, text: str) -> dict[str, Any]:
        """
        Metnin genel karmaşıklığını analiz et

        Args:
            text: Analiz edilecek metin

        Returns:
            Dict: Karmaşıklık analizi sonucu
        """
        try:
            words = text.split()

            if not words:
                return {
                    "overall_complexity": 0.0,
                    "word_count": 0,
                    "avg_word_length": 0.0,
                    "complex_words": [],
                    "readability_score": 0.0,
                }

            # Her kelime için karmaşıklık hesapla
            word_complexities = []
            complex_words = []

            for word in words:
                clean_word = self._clean_word(word)
                if clean_word:
                    complexity = self.get_word_complexity(clean_word)
                    word_complexities.append(complexity)

                    if complexity > 0.7:  # Karmaşık kelimeler
                        complex_words.append(
                            {"word": clean_word, "complexity": complexity}
                        )

            # Genel istatistikler
            overall_complexity = sum(word_complexities) / len(word_complexities)
            avg_word_length = sum(len(word) for word in words) / len(words)

            # Basit okunabilirlik skoru
            readability_score = max(0.0, 1.0 - overall_complexity)

            return {
                "overall_complexity": round(overall_complexity, 3),
                "word_count": len(words),
                "avg_word_length": round(avg_word_length, 2),
                "complex_words": complex_words[:10],  # İlk 10 karmaşık kelime
                "readability_score": round(readability_score, 3),
            }

        except Exception as e:
            logger.error(f"Metin karmaşıklık analizi hatası: {e}")
            return {
                "overall_complexity": 0.5,
                "word_count": 0,
                "avg_word_length": 0.0,
                "complex_words": [],
                "readability_score": 0.5,
                "error": str(e),
            }

    async def close(self):
        """Servisi kapat"""
        if self.session:
            await self.session.close()
            self.session = None


# Global instance
turkish_nlp_service = TurkishNLPService()
