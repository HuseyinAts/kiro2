"""
Zemberek NLP Client
Türkçe doğal dil işleme için Zemberek-NLP entegrasyonu

Özellikler:
- Morfolojik analiz
- Yazım kontrolü
- Kelime kökü bulma
- Türkçe karakter doğrulama
"""

import re
from typing import Any, List, Optional, Tuple

from pydantic import BaseModel


class MorphologicalAnalysis(BaseModel):
    """Morfolojik analiz sonucu"""
    word: str
    root: str
    pos: str  # Part of speech
    suffixes: List[str]
    is_valid: bool
    alternatives: List[str]


class SpellCheckResult(BaseModel):
    """Yazım kontrolü sonucu"""
    word: str
    is_correct: bool
    suggestions: List[str]


class ZemberekClient:
    """
    Zemberek-NLP istemcisi

    Zemberek MCP server mevcut değilse fallback işlevsellik sağlar.
    Gerçek Zemberek entegrasyonu için zemberek-mcp kullanılmalıdır.
    """

    # Türkçe karakterler
    TURKISH_CHARS = set("abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ")
    TURKISH_SPECIAL = {"ç", "ğ", "ı", "ö", "ş", "ü", "Ç", "Ğ", "İ", "Ö", "Ş", "Ü"}

    # Yaygın Türkçe yazım hataları
    COMMON_MISTAKES = {
        "acaba": ["aceba"],
        "ayrıca": ["ayrıcada"],
        "belki": ["belkide"],
        "bile": ["bilede"],
        "çünkü": ["cunku", "çünki"],
        "değil": ["degil"],
        "dolayı": ["dolayi"],
        "için": ["icin"],
        "ile": ["yle"],
        "kadar": ["kadarda"],
        "ki": ["kide"],
        "şey": ["sey"],
        "öyle": ["oyle"],
        "böyle": ["boyle"],
    }

    # Basit kök sözlüğü (fallback için)
    WORD_ROOTS = {
        "soruları": "soru",
        "sorular": "soru",
        "soruyu": "soru",
        "denklem": "denklem",
        "denklemler": "denklem",
        "denklemin": "denklem",
        "çözümü": "çözüm",
        "çözümler": "çözüm",
        "hesaplama": "hesapla",
        "hesaplayın": "hesapla",
        "bulunuz": "bul",
        "değeri": "değer",
        "değerleri": "değer",
    }

    def __init__(self, mcp_client: Optional[Any] = None):
        """
        Zemberek client başlat

        Args:
            mcp_client: Zemberek MCP istemcisi (opsiyonel)
        """
        self.mcp = mcp_client
        self._initialized = True

    async def analyze_morphology(self, word: str) -> MorphologicalAnalysis:
        """
        Kelime morfolojik analizi

        Args:
            word: Analiz edilecek kelime

        Returns:
            MorphologicalAnalysis: Analiz sonucu
        """
        # MCP mevcut ise kullan
        if self.mcp:
            try:
                result = await self.mcp.analyze_morphology(word)
                return MorphologicalAnalysis(**result)
            except Exception:
                pass

        # Fallback analiz
        root = self._find_root(word)
        is_valid = self._is_valid_turkish(word)

        return MorphologicalAnalysis(
            word=word,
            root=root,
            pos="unknown",
            suffixes=[],
            is_valid=is_valid,
            alternatives=[]
        )

    async def check_spelling(self, text: str) -> List[SpellCheckResult]:
        """
        Yazım kontrolü

        Args:
            text: Kontrol edilecek metin

        Returns:
            List[SpellCheckResult]: Hatalı kelimeler ve öneriler
        """
        results = []
        words = text.split()

        for word in words:
            # Noktalama işaretlerini temizle
            clean_word = re.sub(r'[^\w]', '', word)
            if not clean_word:
                continue

            is_correct, suggestions = self._check_word(clean_word)

            if not is_correct:
                results.append(SpellCheckResult(
                    word=clean_word,
                    is_correct=False,
                    suggestions=suggestions
                ))

        return results

    async def validate_turkish_text(self, text: str) -> Tuple[bool, List[str], float]:
        """
        Türkçe metin doğrulama

        Args:
            text: Doğrulanacak metin

        Returns:
            Tuple[bool, List[str], float]: (Geçerli mi, Hatalar, Skor)
        """
        errors = []
        words = text.split()
        valid_count = 0
        total_count = 0

        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if not clean_word:
                continue

            total_count += 1

            # Türkçe karakter kontrolü
            if not self._is_valid_turkish(clean_word):
                errors.append(f"Geçersiz karakter: '{word}'")
            else:
                valid_count += 1

            # Yazım kontrolü
            is_correct, _ = self._check_word(clean_word)
            if not is_correct:
                errors.append(f"Olası yazım hatası: '{word}'")

        # Skor hesapla
        score = valid_count / max(total_count, 1)
        is_valid = len(errors) == 0 and score >= 0.9

        return is_valid, errors[:10], round(score, 2)

    async def normalize_text(self, text: str) -> str:
        """
        Türkçe metin normalleştirme

        Args:
            text: Normalleştirilecek metin

        Returns:
            str: Normalleştirilmiş metin
        """
        # I/İ düzeltmesi
        normalized = text.replace("I", "ı").replace("İ", "I")

        # Küçük i büyütme
        # Turkish uppercase: i → İ, ı → I
        result = []
        for i, char in enumerate(normalized):
            if char == 'i' and i == 0:
                # Cümle başı
                result.append('İ')
            else:
                result.append(char)

        return ''.join(result)

    def _find_root(self, word: str) -> str:
        """Basit kök bulma (fallback)"""
        word_lower = word.lower()

        # Sözlükte ara
        if word_lower in self.WORD_ROOTS:
            return self.WORD_ROOTS[word_lower]

        # Basit ek kaldırma
        suffixes = ["lar", "ler", "dır", "dir", "ını", "ini", "nın", "nin",
                    "dan", "den", "da", "de", "ın", "in", "a", "e", "ı", "i"]

        for suffix in suffixes:
            if word_lower.endswith(suffix) and len(word_lower) > len(suffix) + 2:
                return word_lower[:-len(suffix)]

        return word_lower

    def _is_valid_turkish(self, word: str) -> bool:
        """Türkçe karakter kontrolü"""
        # Sadece harfler
        letters_only = re.sub(r'[^\w]', '', word)
        if not letters_only:
            return True

        # Her karakter Türkçe mi
        for char in letters_only:
            if char.isalpha() and char not in self.TURKISH_CHARS:
                return False

        return True

    def _check_word(self, word: str) -> Tuple[bool, List[str]]:
        """Basit yazım kontrolü (fallback)"""
        word_lower = word.lower()

        # Yaygın hatalar sözlüğünde ara
        for correct, mistakes in self.COMMON_MISTAKES.items():
            if word_lower in mistakes:
                return False, [correct]

        # Türkçe olmayan karakterler
        if not self._is_valid_turkish(word):
            return False, []

        # Kısa kelimeler için ek kontrol yok
        if len(word) <= 2:
            return True, []

        return True, []

    async def get_word_suggestions(self, word: str, limit: int = 5) -> List[str]:
        """
        Kelime önerileri

        Args:
            word: Kaynak kelime
            limit: Maksimum öneri sayısı

        Returns:
            List[str]: Öneri listesi
        """
        suggestions = []

        # Yaygın hatalar
        word_lower = word.lower()
        for correct, mistakes in self.COMMON_MISTAKES.items():
            if word_lower in mistakes:
                suggestions.append(correct)

        return suggestions[:limit]

    def turkish_upper(self, text: str) -> str:
        """
        Türkçe büyük harfe çevir

        i → İ
        ı → I

        Args:
            text: Çevrilecek metin

        Returns:
            str: Büyük harfli metin
        """
        result = []
        for char in text:
            if char == 'i':
                result.append('İ')
            elif char == 'ı':
                result.append('I')
            else:
                result.append(char.upper())
        return ''.join(result)

    def turkish_lower(self, text: str) -> str:
        """
        Türkçe küçük harfe çevir

        I → ı
        İ → i

        Args:
            text: Çevrilecek metin

        Returns:
            str: Küçük harfli metin
        """
        result = []
        for char in text:
            if char == 'I':
                result.append('ı')
            elif char == 'İ':
                result.append('i')
            else:
                result.append(char.lower())
        return ''.join(result)
