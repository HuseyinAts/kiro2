import re
from typing import ClassVar


class TurkishReadabilityService:
    """
    Analyzes Turkish text to calculate readability metrics, primarily the Ateşman Readability Index.
    Ateşman formula: 198.825 - (40.175 * Syllables / Words) - (2.610 * Words / Sentences)
    """

    VOWELS: ClassVar[set[str]] = set("aeıioöuüAEIİOÖUÜ")

    @classmethod
    def count_syllables(cls, word: str) -> int:
        """
        Counts syllables in a Turkish word.
        Since every Turkish syllable contains exactly one vowel, we can count the vowels.
        This heuristic is O(n) and highly accurate for Turkish linguistics.
        """
        count = sum(1 for char in word if char in cls.VOWELS)
        # Even if a word has 0 vowels (like an abbreviation or a number),
        # we consider it at least 1 syllable if it contains letters/numbers.
        return max(1, count) if word.strip() else 0

    @classmethod
    def split_sentences(cls, text: str) -> list[str]:
        """
        Splits text into sentences.
        A basic regex splitting by . ! ? followed by space or end of string.
        For production, a robust NLP library like NLTK or Zemberek might be preferred,
        but this regex is sufficient for standard OSYM exam layouts.
        """
        # Split by . ! ? followed by a space and a capital letter, or end of string.
        # But we also have to keep the punctuation.
        # Simple split: find punctuation, split.
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def split_words(cls, text: str) -> list[str]:
        """
        Splits text into words, removing punctuation.
        """
        # Find all sequences of alphanumeric chars including Turkish chars
        return re.findall(r"[a-zA-Z0-9ğüşıöçĞÜŞİÖÇ]+", text)

    @classmethod
    def analyze_text(cls, text: str) -> dict[str, float]:
        """
        Analyzes text and returns syllable, word, and sentence counts,
        along with the Ateşman Readability Index.
        """
        if not text or not text.strip():
            return {
                "syllable_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "atesman_index": 0.0,
                "avg_word_length": 0.0,
                "avg_words_per_sentence": 0.0,
            }

        sentences = cls.split_sentences(text)
        words = cls.split_words(text)

        sentence_count = len(sentences)
        word_count = len(words)

        # If there are no words, return 0 for metrics
        if word_count == 0:
            return {
                "syllable_count": 0,
                "word_count": 0,
                "sentence_count": sentence_count,
                "atesman_index": 0.0,
                "avg_word_length": 0.0,
                "avg_words_per_sentence": 0.0,
            }

        syllable_count = sum(cls.count_syllables(w) for w in words)
        char_count = sum(len(w) for w in words)

        # To prevent division by zero in sentence ratio, ensure sentence_count is at least 1
        safe_sentence_count = max(1, sentence_count)

        # Ateşman formula
        syllables_per_word = syllable_count / word_count
        words_per_sentence = word_count / safe_sentence_count

        atesman_index = (
            198.825 - (40.175 * syllables_per_word) - (2.610 * words_per_sentence)
        )

        return {
            "syllable_count": syllable_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "atesman_index": round(atesman_index, 3),
            "avg_word_length": round(char_count / word_count, 3),
            "avg_words_per_sentence": round(words_per_sentence, 3),
        }
