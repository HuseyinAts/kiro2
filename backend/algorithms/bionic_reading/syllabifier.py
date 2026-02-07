"""
Turkish Syllabifier - Türkçe Heceleme Modülü
REQ-2: Syllable-Based Optimization

Türkçe heceleme kurallarını uygular:
- Vowel harmony (ünlü uyumu)
- Consonant clusters (ünsüz grupları)
- Compound word detection (birleşik kelimeler)
- Syllable weight calculation (hece ağırlığı)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# Türkçe ünlüler
TURKISH_VOWELS = set("aeıioöuüAEIİOÖUÜ")
FRONT_VOWELS = set("eiöüEİÖÜ")  # İnce ünlüler
BACK_VOWELS = set("aıouAIOU")  # Kalın ünlüler
ROUNDED_VOWELS = set("oöuüOÖUÜ")  # Yuvarlak ünlüler
UNROUNDED_VOWELS = set("aeıiAEIİ")  # Düz ünlüler

# Türkçe ünsüzler
TURKISH_CONSONANTS = set("bcçdfgğhjklmnprsştvyzBCÇDFGĞHJKLMNPRSŞTVYZ")


class SyllableWeight(Enum):
    """Hece ağırlığı tipleri"""
    LIGHT = "light"  # CV (açık hece): ka, de
    HEAVY = "heavy"  # CVC veya CVV (kapalı hece): kan, kaan


class VowelHarmony(Enum):
    """Ünlü uyumu tipleri"""
    FRONT = "front"  # İnce ünlüler (e, i, ö, ü)
    BACK = "back"  # Kalın ünlüler (a, ı, o, u)
    MIXED = "mixed"  # Karışık (yabancı kökenli)


@dataclass
class Syllable:
    """Hece veri yapısı"""
    text: str
    weight: SyllableWeight
    vowel: str
    position: int  # 0-indexed position in word
    is_root_syllable: bool = False


@dataclass
class SyllabificationResult:
    """Heceleme sonucu"""
    word: str
    syllables: list[Syllable]
    vowel_harmony: VowelHarmony
    is_compound: bool
    syllable_count: int
    confidence: float


class TurkishSyllabifier:
    """
    Türkçe Heceleme Sınıfı

    Türkçe phonotactics kurallarına göre kelimeleri heceler:
    1. Her hecede bir ünlü bulunur
    2. Hece yapısı: (C)(C)V(C)(C)
    3. Sözcük başında en fazla bir ünsüz
    4. Sözcük sonunda en fazla iki ünsüz
    """

    def __init__(self):
        self._cache: dict[str, SyllabificationResult] = {}

        # Türkçe'de geçerli ünsüz kümeleri
        self.valid_onset_clusters: set[str] = set()  # Türkçe'de sözcük başı ünsüz kümesi yok
        self.valid_coda_clusters = {"nk", "nt", "nç", "st", "şt", "rk", "rt", "lk", "lt"}

    def syllabify(self, word: str, use_cache: bool = True) -> SyllabificationResult:
        """
        Kelimeyi hecele

        Args:
            word: Hecelenecek kelime
            use_cache: Cache kullanılsın mı

        Returns:
            SyllabificationResult: Heceleme sonucu
        """
        if not word:
            return SyllabificationResult(
                word=word,
                syllables=[],
                vowel_harmony=VowelHarmony.BACK,
                is_compound=False,
                syllable_count=0,
                confidence=1.0
            )

        cache_key = word.lower()
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            syllables = self._split_into_syllables(word)
            vowel_harmony = self._detect_vowel_harmony(word)
            is_compound = self._detect_compound(word)

            result = SyllabificationResult(
                word=word,
                syllables=syllables,
                vowel_harmony=vowel_harmony,
                is_compound=is_compound,
                syllable_count=len(syllables),
                confidence=0.9
            )

            if use_cache:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Heceleme hatası ({word}): {e}")
            return SyllabificationResult(
                word=word,
                syllables=[Syllable(word, SyllableWeight.HEAVY, "", 0)],
                vowel_harmony=VowelHarmony.MIXED,
                is_compound=False,
                syllable_count=1,
                confidence=0.5
            )

    def _split_into_syllables(self, word: str) -> list[Syllable]:
        """Kelimeyi hecelere ayır"""
        syllables: list[Syllable] = []
        current_syllable = ""
        position = 0

        i = 0
        while i < len(word):
            char = word[i]

            if char.lower() in TURKISH_VOWELS:
                # Ünlü bulundu, mevcut heceye ekle
                current_syllable += char

                # Sonraki karakterleri kontrol et
                j = i + 1

                # Sonraki ünsüzleri kontrol et
                consonant_buffer = ""
                while j < len(word) and word[j].lower() not in TURKISH_VOWELS:
                    consonant_buffer += word[j]
                    j += 1

                # Ünsüzleri böl: son ünsüz sonraki heceye
                if len(consonant_buffer) > 0:
                    if j < len(word):  # Sonra başka ünlü var
                        # Son ünsüz sonraki heceye gider
                        current_syllable += consonant_buffer[:-1]

                        # Heceyi kaydet
                        vowel = self._find_vowel(current_syllable)
                        weight = self._calculate_weight(current_syllable)
                        syllables.append(Syllable(
                            text=current_syllable,
                            weight=weight,
                            vowel=vowel,
                            position=position
                        ))
                        position += 1

                        # Yeni hece başlat
                        current_syllable = consonant_buffer[-1]
                        i = j - 1
                    else:
                        # Son hece
                        current_syllable += consonant_buffer
                        vowel = self._find_vowel(current_syllable)
                        weight = self._calculate_weight(current_syllable)
                        syllables.append(Syllable(
                            text=current_syllable,
                            weight=weight,
                            vowel=vowel,
                            position=position
                        ))
                        current_syllable = ""
                        i = j - 1
                else:
                    # Ünlüden sonra ünsüz yok
                    vowel = self._find_vowel(current_syllable)
                    weight = self._calculate_weight(current_syllable)
                    syllables.append(Syllable(
                        text=current_syllable,
                        weight=weight,
                        vowel=vowel,
                        position=position
                    ))
                    position += 1
                    current_syllable = ""
            else:
                # Ünsüz, heceye ekle
                current_syllable += char

            i += 1

        # Kalan heceyi ekle
        if current_syllable:
            vowel = self._find_vowel(current_syllable)
            weight = self._calculate_weight(current_syllable)
            syllables.append(Syllable(
                text=current_syllable,
                weight=weight,
                vowel=vowel,
                position=position
            ))

        # İlk heceler genellikle kök heceleridir
        if syllables:
            root_syllable_count = max(1, len(syllables) // 2)
            for i in range(root_syllable_count):
                syllables[i].is_root_syllable = True

        return syllables

    def _find_vowel(self, syllable: str) -> str:
        """Hecedeki ünlüyü bul"""
        for char in syllable:
            if char.lower() in TURKISH_VOWELS:
                return char
        return ""

    def _calculate_weight(self, syllable: str) -> SyllableWeight:
        """Hece ağırlığını hesapla"""
        vowel_count = sum(1 for c in syllable if c.lower() in TURKISH_VOWELS)
        consonant_after_vowel = False

        found_vowel = False
        for char in syllable:
            if char.lower() in TURKISH_VOWELS:
                found_vowel = True
            elif found_vowel and char.lower() in TURKISH_CONSONANTS:
                consonant_after_vowel = True
                break

        # CVC veya CVV = heavy, CV = light
        if consonant_after_vowel or vowel_count > 1:
            return SyllableWeight.HEAVY
        return SyllableWeight.LIGHT

    def _detect_vowel_harmony(self, word: str) -> VowelHarmony:
        """Ünlü uyumunu tespit et"""
        vowels_in_word = [c for c in word if c.lower() in TURKISH_VOWELS]

        if not vowels_in_word:
            return VowelHarmony.BACK

        front_count = sum(1 for v in vowels_in_word if v.lower() in FRONT_VOWELS)
        back_count = sum(1 for v in vowels_in_word if v.lower() in BACK_VOWELS)

        if front_count > 0 and back_count > 0:
            # Karışık ünlüler (yabancı kökenli veya birleşik kelime olabilir)
            if front_count > back_count:
                return VowelHarmony.FRONT
            elif back_count > front_count:
                return VowelHarmony.BACK
            return VowelHarmony.MIXED
        elif front_count > 0:
            return VowelHarmony.FRONT
        else:
            return VowelHarmony.BACK

    def _detect_compound(self, word: str) -> bool:
        """Birleşik kelime tespiti"""
        # Basit birleşik kelime tespiti
        # İki veya daha fazla kök yapısı olabilir
        vowel_harmony = self._detect_vowel_harmony(word)

        # Karışık ünlü uyumu birleşik kelime işareti olabilir
        if vowel_harmony == VowelHarmony.MIXED:
            return True

        # Uzun kelimeler birleşik olabilir
        if len(word) > 12:
            return True

        return False

    def get_first_syllable(self, word: str) -> Optional[Syllable]:
        """İlk heceyi döndür"""
        result = self.syllabify(word)
        if result.syllables:
            return result.syllables[0]
        return None

    def get_syllable_boundaries(self, word: str) -> list[int]:
        """Hece sınırlarının indekslerini döndür"""
        result = self.syllabify(word)
        boundaries = []
        current_pos = 0

        for syllable in result.syllables:
            current_pos += len(syllable.text)
            if current_pos < len(word):
                boundaries.append(current_pos)

        return boundaries

    def clear_cache(self):
        """Cache'i temizle"""
        self._cache.clear()

    def get_cache_stats(self) -> dict:
        """Cache istatistiklerini döndür"""
        return {
            "cache_size": len(self._cache),
            "sample_keys": list(self._cache.keys())[:10]
        }
