"""
Normalization Tool (REQ-7)
Turkce metin normalizasyonu - informal -> formal

Supports both JPype (direct Zemberek access) and HTTP backend.
"""

import logging
import re
from typing import Any

from .base import BaseToolHandler

logger = logging.getLogger(__name__)

# Informal to formal mappings
INFORMAL_MAP = {
    # Common abbreviations
    "mrb": "merhaba",
    "slm": "selam",
    "nbr": "ne haber",
    "naber": "ne haber",
    "nslsn": "nasılsın",
    "nasilsin": "nasılsın",
    "tsk": "teşekkür",
    "tesekkur": "teşekkür",
    "tmm": "tamam",
    "ok": "tamam",
    "okey": "tamam",
    "evt": "evet",
    "hyr": "hayır",
    "bi": "bir",
    "bisey": "bir şey",
    "birsey": "bir şey",
    "bisi": "bir şey",
    "yok": "yok",
    "valla": "vallahi",
    "vallaa": "vallahi",
    "hadi": "haydi",
    "hde": "haydi",
    "bnce": "bence",
    "snce": "sence",
    "dmi": "değil mi",
    "degil mi": "değil mi",
    "kib": "kendine iyi bak",
    "bb": "bay bay",
    "görüşürüz": "görüşürüz",
    "gorusuruz": "görüşürüz",
}

# Emoji/emoticon to text (REQ-7.3)
EMOJI_MAP = {
    # Emoticons
    ":)": "(gülümseme)",
    ":D": "(geniş gülümseme)",
    ":(": "(üzgün)",
    ";)": "(göz kırpma)",
    ":P": "(dil çıkarma)",
    "<3": "(kalp)",
    ":*": "(öpücük)",
    "xD": "(kahkaha)",
    "^^": "(mutlu)",
    # Unicode emojis - Common
    "😀": "(gülümseme)",
    "😃": "(gülümseme)",
    "😄": "(gülümseme)",
    "😁": "(geniş gülümseme)",
    "😆": "(gülme)",
    "😅": "(ter gülümseme)",
    "🤣": "(yerde yatarak gülme)",
    "😂": "(sevinç gözyaşı)",
    "🙂": "(hafif gülümseme)",
    "🙃": "(ters gülümseme)",
    "😉": "(göz kırpma)",
    "😊": "(mutlu gülümseme)",
    "😇": "(melek)",
    # Sad/Negative
    "😢": "(ağlama)",
    "😭": "(hüngür hüngür ağlama)",
    "😔": "(üzgün)",
    "😞": "(hayal kırıklığı)",
    "😟": "(endişeli)",
    "😕": "(şaşkın)",
    "🙁": "(hafif üzgün)",
    "☹️": "(üzgün yüz)",
    "😣": "(sabırlı)",
    "😖": "(sıkıntılı)",
    "😫": "(yorgun)",
    "😩": "(bitkin)",
    "😤": "(öfkeli)",
    "😠": "(kızgın)",
    "😡": "(çok kızgın)",
    # Love/Heart
    "❤️": "(kalp)",
    "🧡": "(turuncu kalp)",
    "💛": "(sarı kalp)",
    "💚": "(yeşil kalp)",
    "💙": "(mavi kalp)",
    "💜": "(mor kalp)",
    "🖤": "(siyah kalp)",
    "💕": "(iki kalp)",
    "💞": "(dönen kalpler)",
    "💓": "(atan kalp)",
    "💗": "(büyüyen kalp)",
    "💖": "(pırıl pırıl kalp)",
    "💘": "(ok ile kalp)",
    "💝": "(kurdeleli kalp)",
    "😍": "(aşık gözler)",
    "🥰": "(sevgi dolu)",
    "😘": "(öpücük gönderme)",
    "😗": "(öpücük)",
    "😚": "(kapalı gözle öpücük)",
    "😙": "(gülümseyerek öpücük)",
    # Gestures
    "👍": "(beğenme)",
    "👎": "(beğenmeme)",
    "👏": "(alkış)",
    "🙏": "(dua/teşekkür)",
    "🤝": "(el sıkışma)",
    "✌️": "(zafer işareti)",
    "🤞": "(şanslar)",
    "👋": "(el sallama)",
    "🖐️": "(beş parmak)",
    "✋": "(dur)",
    "👌": "(tamam)",
    "🤙": "(ara beni)",
    "💪": "(güç)",
    # Common expressions
    "🔥": "(ateş)",
    "💯": "(yüz puan)",
    "✅": "(onay)",
    "❌": "(red)",
    "⭐": "(yıldız)",
    "🌟": "(parlak yıldız)",
    "💫": "(baş dönmesi)",
    "✨": "(parıltı)",
    "🎉": "(kutlama)",
    "🎊": "(konfeti)",
    "🎈": "(balon)",
    "🎁": "(hediye)",
    "🏆": "(kupa)",
    "🥇": "(altın madalya)",
    "🥈": "(gümüş madalya)",
    "🥉": "(bronz madalya)",
    # Education related
    "📚": "(kitaplar)",
    "📖": "(açık kitap)",
    "📝": "(yazma)",
    "✏️": "(kalem)",
    "🎓": "(mezuniyet)",
    "🧠": "(beyin)",
    "💡": "(fikir)",
    "❓": "(soru)",
    "❗": "(ünlem)",
    "📊": "(grafik)",
    "📈": "(yükseliş grafiği)",
    "📉": "(düşüş grafiği)",
}


class NormalizationHandler(BaseToolHandler):
    """Text normalization tool handler"""

    tool_name = "normalization"

    async def _call_jpype(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Normalize text using JPype bridge.

        Args:
            text: Turkish text to normalize

        Returns:
            NormalizationResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        changes: list[dict[str, str]] = []
        normalized = text

        # Try JPype normalization first
        try:
            result = await self.bridge.normalize_async(text)
            jpype_normalized = result.get("normalized", text)

            if jpype_normalized != text:
                normalized = jpype_normalized
                changes.append({
                    "original": text,
                    "normalized": jpype_normalized,
                    "change_type": "jpype_normalization",
                })
        except Exception as e:
            logger.debug(f"[Normalization] JPype normalizer unavailable: {e}")

        # Apply additional normalizations
        normalized, additional_changes = self._apply_normalizations(normalized)
        changes.extend(additional_changes)

        return {
            "original": text,
            "normalized": normalized,
            "changes": changes,
            "change_count": len(changes),
        }

    async def _call_backend(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Normalize Turkish text

        Args:
            text: Turkish text to normalize

        Returns:
            NormalizationResult as dictionary
        """
        changes: list[dict[str, str]] = []
        normalized = text

        # Try backend normalization first
        try:
            response = await self._post("/normalize", {"text": text})
            backend_normalized = response.get("normalized", text)

            if backend_normalized != text:
                normalized = backend_normalized
                changes.append({
                    "original": text,
                    "normalized": backend_normalized,
                    "change_type": "backend_normalization",
                })
        except Exception as e:
            logger.debug(f"[Normalization] Backend unavailable: {e}")

        # Apply additional normalizations
        normalized, additional_changes = self._apply_normalizations(normalized)
        changes.extend(additional_changes)

        return {
            "original": text,
            "normalized": normalized,
            "changes": changes,
            "change_count": len(changes),
        }

    def _apply_normalizations(
        self, text: str
    ) -> tuple[str, list[dict[str, str]]]:
        """Apply all normalization rules"""
        changes = []
        normalized = text

        # 1. Fix repeated characters (çoooook -> çok)
        normalized, repeat_changes = self._fix_repeated_chars(normalized)
        changes.extend(repeat_changes)

        # 2. Convert informal to formal
        normalized, informal_changes = self._convert_informal(normalized)
        changes.extend(informal_changes)

        # 3. Convert emoji/emoticons
        normalized, emoji_changes = self._convert_emojis(normalized)
        changes.extend(emoji_changes)

        # 4. Apply Turkish case rules
        normalized, case_changes = self._fix_turkish_case(normalized)
        changes.extend(case_changes)

        return normalized, changes

    def _fix_repeated_chars(
        self, text: str
    ) -> tuple[str, list[dict[str, str]]]:
        """Fix repeated characters (çoooook -> çok)"""
        changes = []

        # Pattern: 3+ repeated characters
        pattern = re.compile(r"(.)\1{2,}")

        def replace_repeated(match):
            char = match.group(1)
            original = match.group(0)
            # Keep max 1 repetition for emphasis (e.g., "evet" not "eveet")
            replacement = char
            if original != replacement:
                changes.append({
                    "original": original,
                    "normalized": replacement,
                    "change_type": "repeated",
                })
            return replacement

        normalized = pattern.sub(replace_repeated, text)
        return normalized, changes

    def _convert_informal(
        self, text: str
    ) -> tuple[str, list[dict[str, str]]]:
        """Convert informal text to formal"""
        changes = []
        normalized = text

        # Word-by-word replacement
        words = text.split()
        new_words = []

        for word in words:
            word_lower = word.lower()
            if word_lower in INFORMAL_MAP:
                formal = INFORMAL_MAP[word_lower]
                # Preserve original case pattern
                if word[0].isupper():
                    formal = formal.capitalize()
                new_words.append(formal)
                changes.append({
                    "original": word,
                    "normalized": formal,
                    "change_type": "informal",
                })
            else:
                new_words.append(word)

        normalized = " ".join(new_words)
        return normalized, changes

    def _convert_emojis(
        self, text: str
    ) -> tuple[str, list[dict[str, str]]]:
        """Convert emoji/emoticons to text"""
        changes = []
        normalized = text

        for emoji, text_equiv in EMOJI_MAP.items():
            if emoji in normalized:
                normalized = normalized.replace(emoji, text_equiv)
                changes.append({
                    "original": emoji,
                    "normalized": text_equiv,
                    "change_type": "emoji",
                })

        return normalized, changes

    def _fix_turkish_case(
        self, text: str
    ) -> tuple[str, list[dict[str, str]]]:
        """Apply Turkish uppercase/lowercase rules"""
        changes = []

        # Turkish I/İ and i/ı rules
        # This is tricky - only fix obvious errors

        # Common mistakes:
        # - "ISTANBUL" should be "İSTANBUL"
        # - "istanbul" is correct
        # - "Istanbul" should be "İstanbul"

        normalized = text

        # Fix uppercase I that should be İ in Turkish words
        turkish_words_with_i = [
            ("ISTANBUL", "İSTANBUL"),
            ("Istanbul", "İstanbul"),
            ("IZMIR", "İZMİR"),
            ("Izmir", "İzmir"),
            ("ISPARTA", "ISPARTA"),  # This one stays with I
        ]

        for wrong, correct in turkish_words_with_i:
            if wrong in normalized and wrong != correct:
                normalized = normalized.replace(wrong, correct)
                changes.append({
                    "original": wrong,
                    "normalized": correct,
                    "change_type": "case",
                })

        return normalized, changes
