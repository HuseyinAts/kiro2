import re
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

import structlog

logger = structlog.get_logger(__name__)


class YKSTrendAnalyzer:
    """
    Analyzes linguistic trends of OSYM exams and calculates reading difficulty.
    Uses the Atesman Readability Index for Turkish texts.
    Enhanced with August 2026 Gemini Ultra heuristics.
    """

    TURKISH_VOWELS: ClassVar[set[str]] = set("aeıioöuüAEIİOÖUÜ")

    # Cache system for DB query
    _trend_cache: ClassVar[dict[str, Any]] = {}
    _cache_ttl = timedelta(hours=1)

    @classmethod
    def _number_to_turkish_syllables(cls, num_str: str) -> int:
        """
        Approximate syllable count for numbers.
        Each digit broadly corresponds to syllables when spoken.
        e.g., 0 (sı-fır)=2, 1 (bir)=1, 2 (i-ki)=2, 3 (üç)=1, 4 (dört)=1, 5 (beş)=1,
        6 (al-tı)=2, 7 (ye-di)=2, 8 (se-kiz)=2, 9 (do-kuz)=2.
        For large numbers this is an approximation.
        """
        digit_syllables = {
            "0": 2,
            "1": 1,
            "2": 2,
            "3": 1,
            "4": 1,
            "5": 1,
            "6": 2,
            "7": 2,
            "8": 2,
            "9": 2,
        }

        # If it's a year like 1923 (bin dokuz yüz yirmi üç -> 1+2+1+2+1 = 7 syllables)
        # This is a complex NLP problem, but we can approximate:
        if (len(num_str) == 4 and num_str.startswith("19")) or (
            len(num_str) == 4 and num_str.startswith("20")
        ):  # e.g. 1999
            return 7

        return sum(digit_syllables.get(d, 0) for d in num_str if d.isdigit()) or 1

    @classmethod
    def count_syllables(cls, word: str) -> int:
        """
        In Turkish, the number of syllables is generally equal to the number of vowels.
        Enhanced to handle numbers, percentages, and acronyms (e.g., TBMM, TDK).
        """
        # If it's a pure number or decimal (e.g. 3.14)
        if re.match(r"^[0-9.,%]+$", word):
            return cls._number_to_turkish_syllables(word)

        # Count standard vowels
        vowel_count = sum(1 for char in word if char in cls.TURKISH_VOWELS)

        # If no vowels, it's likely an acronym (like TDK, MEB - wait MEB has E, but TBMM has none)
        if vowel_count == 0:
            # Check if it contains alphabetical characters
            if re.search(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]", word):
                # Count consonants as syllables (Te-Be-Me-Me)
                alpha_chars = re.sub(r"[^a-zA-ZçğıöşüÇĞİÖŞÜ]", "", word)
                return max(1, len(alpha_chars))
            return 1

        return vowel_count

    @classmethod
    def analyze_exam_text(cls, text: str) -> dict[str, Any]:
        """
        Parses text and calculates linguistics metrics:
        - avg_word_length
        - avg_words_per_sentence
        - atesman_readability_index
        - question_length_chars
        """
        if not text or not text.strip():
            return {
                "avg_word_length": 0.0,
                "avg_words_per_sentence": 0.0,
                "atesman_readability_index": 0.0,
                "question_length_chars": 0,
            }

        text = text.strip()
        total_chars = len(text)

        # 1. Smart Sentence Boundary Detection
        # Split by . ! ? but ignore abbreviations like Prof. Dr. vb.
        # Negative lookbehind for common Turkish abbreviations
        abbreviations = (
            r"(?<!\bProf)(?<!\bDr)(?<!\bAv)(?<!\bMüh)(?<!\bDoç)(?<!\bvb)(?<!\bvs)"
        )
        # Also ignore decimal numbers e.g. 3.14
        decimal_protection = r"(?<!\b\d)"
        sentence_regex = abbreviations + decimal_protection + r"[.!?]+(?:\s+|$)"

        sentences = [s.strip() for s in re.split(sentence_regex, text) if s.strip()]
        total_sentences = len(sentences) if sentences else 1

        # 2. Smart Word Tokenization
        # Keep words with apostrophes (Ali'nin) and decimals/percentages (3.14, %50)
        word_regex = r"[a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+(?:['.][a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+)*"
        words = re.findall(word_regex, text)
        total_words = len(words) if words else 1

        # Calculate averages
        total_word_length = sum(len(w) for w in words)
        avg_word_length = total_word_length / total_words
        avg_words_per_sentence = total_words / total_sentences

        # Calculate syllables for Atesman Index
        total_syllables = sum(cls.count_syllables(w) for w in words)

        # Atesman Readability Formula:
        # 198.825 - 40.175 * (Syllables / Words) - 2.610 * (Words / Sentences)
        syllables_per_word = total_syllables / total_words
        words_per_sentence = total_words / total_sentences

        atesman_index = (
            198.825 - (40.175 * syllables_per_word) - (2.610 * words_per_sentence)
        )
        atesman_index = max(0.0, min(100.0, atesman_index))

        return {
            "avg_word_length": round(avg_word_length, 2),
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "atesman_readability_index": round(atesman_index, 2),
            "question_length_chars": total_chars,
        }

    @classmethod
    async def build_linguistic_trend_addon(
        cls, db_session, exam_type: str, subject: str
    ) -> str:
        """
        Fetches the latest linguistic trend from the database and formats an addon string for the LLM prompt.
        Uses in-memory caching and fallback to prevent database overwhelming and LLM pipeline failure.
        """
        cache_key = f"{exam_type}_{subject}"
        now = datetime.now(UTC)

        # 1. Cache hit?
        if cache_key in cls._trend_cache:
            cached_item = cls._trend_cache[cache_key]
            if now - cached_item["timestamp"] < cls._cache_ttl:
                cached_addon: str = cached_item["addon_string"]
                return cached_addon

        # 2. Cache miss -> DB Query with Fallback
        trend_addon_string = ""
        try:
            if db_session:
                from sqlalchemy import select

                from models.osym_trends import OSYMLinguisticTrend

                stmt = (
                    select(OSYMLinguisticTrend)
                    .filter_by(exam_type=exam_type, subject=subject)
                    .order_by(OSYMLinguisticTrend.year.desc())
                    .limit(1)
                )

                result = await db_session.execute(stmt)
                trend = result.scalar_one_or_none()

                if trend:
                    difficulty_level = "Orta"
                    if trend.atesman_readability_index < 50:
                        difficulty_level = "Zor (Akademik/Karmaşık)"
                    elif trend.atesman_readability_index > 70:
                        difficulty_level = "Kolay (Sade/Açık)"

                    trend_addon_string = (
                        f"\n\nDİKKAT (Linguistik ve Bilişsel Trend Kalibrasyonu):\n"
                        f"- Üreteceğin soruda cümleler ortalama {trend.avg_words_per_sentence:.1f} kelime uzunluğunda olmalıdır.\n"
                        f"- Kelimeler ortalama {trend.avg_word_length:.1f} karakter uzunluğunda olmalıdır.\n"
                        f"- Metnin Ateşman Okunabilirlik düzeyi yaklaşık {trend.atesman_readability_index:.1f} ({difficulty_level}) seviyesinde olmalıdır.\n"
                        f"- Soru metni toplamda {trend.question_length_chars} karakter sınırlarında tutulmalıdır.\n"
                        f"- Sınavın hedef kitlesi için hedeflenen Bilişsel Yük Skoru (Cognitive Load) 0-100 üzerinden {trend.cognitive_load_score} seviyesindedir. Karmaşıklığı buna göre ayarla.\n"
                        f"Lütfen YKS güncel dil trendlerine birebir uyun.\n"
                    )
        except Exception as e:
            logger.error(
                "Failed to fetch OSYMLinguisticTrend from DB",
                error=str(e),
                exam_type=exam_type,
                subject=subject,
            )
            # Fallback to empty string on failure, don't break LLM pipeline
            trend_addon_string = ""

        # 3. Save to cache
        cls._trend_cache[cache_key] = {
            "timestamp": now,
            "addon_string": trend_addon_string,
        }

        return trend_addon_string
