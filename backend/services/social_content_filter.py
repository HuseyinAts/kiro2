"""
Social Content Filter — 7-Layer Content Moderation Pipeline

Layer 1: Length check
Layer 2: Turkish blacklist (kufur/hakaret)
Layer 3: Anti-flirt patterns
Layer 4: Personal info detection (telefon, email, TC kimlik)
Layer 5: Emoji abuse detection
Layer 6: Spam detection
Layer 7: AI classification (placeholder, timeout 500ms)

Kullanim:
    filter = SocialContentFilter()
    result = await filter.filter_content("merhaba", sender_id="abc")
    if not result.passed:
        reject(result.blocked_layer)
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class LayerResult:
    layer_name: str
    passed: bool
    confidence: float = 1.0
    details: str = ""
    matched_patterns: list[str] = field(default_factory=list)


@dataclass
class FilterResult:
    passed: bool
    blocked_layer: str | None = None
    flag_reason: str = "clean"
    confidence: float = 1.0
    details: dict[str, LayerResult] = field(default_factory=dict)
    processing_ms: int = 0
    content_hash: str = ""
    sanitized_content: str | None = None


# ---------------------------------------------------------------------------
# Turkish NLP helpers
# ---------------------------------------------------------------------------


def _normalize_tr(text: str) -> str:
    """NFC normalize + Turkish lowercase mapping."""
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u0130", "i").replace("I", "\u0131")  # İ->i, I->ı
    return text.lower()


def _strip_evasion(text: str) -> str:
    """Remove leetspeak and common evasion chars for Turkish."""
    mapping = {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "@": "a",
        "$": "s",
        "!": "i",
        "*": "",
        ".": "",
    }
    result = []
    for ch in text:
        result.append(mapping.get(ch, ch))
    return "".join(result)


# ---------------------------------------------------------------------------
# Layer 2: Turkish blacklist
# ---------------------------------------------------------------------------

_BLACKLIST_HEAVY = [
    "amk",
    "aq",
    "amq",
    "amina",
    "amına",
    "orospu",
    "orosbu",
    "orospucocugu",
    "siktir",
    "siktirgit",
    "sikeyim",
    "sikerim",
    "yarrak",
    "yarak",
    "tasak",
    "taşak",
    "pezevenk",
]

_BLACKLIST_INSULTS = [
    "salak",
    "aptal",
    "gerizekalı",
    "gerizekali",
    "dangalak",
    "ahmak",
    "budala",
    "embesil",
    "moron",
    "andaval",
    "mankafa",
    "beyinsiz",
    "sersem",
    "ezik",
]

_BLACKLIST_DISCRIMINATORY = [
    "gavur",
    "kafir",
]

_ALL_BLACKLIST = _BLACKLIST_HEAVY + _BLACKLIST_INSULTS + _BLACKLIST_DISCRIMINATORY
_BLACKLIST_SET = {_normalize_tr(w) for w in _ALL_BLACKLIST}

# Pre-compile word-boundary regex for each blacklist term
_BLACKLIST_PATTERNS = [
    re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in _BLACKLIST_SET
]


# ---------------------------------------------------------------------------
# Layer 3: Anti-flirt patterns
# ---------------------------------------------------------------------------

_FLIRT_PATTERNS_RAW = {
    "endearments": [
        r"\b(sevgilim|a[sş]k[ıi]m|can[ıi]m|bebe[gğ]im|tatl[ıi]m)\b",
        r"\b(g[uü]zelim|yak[ıi][sş][ıi]kl[ıi]m|hayat[ıi]m)\b",
        r"\b(bir\s*tanem|mele[gğ]im|prensesim|prensim)\b",
        r"\b(a[sş]ko|a[sş]kitom|bebi[sş]|tatl[ıi][sş])\b",
    ],
    "solicitation": [
        r"\bnumaran[ıi]?\s*(ver|at|yolla|g[oö]nder)\b",
        r"\bnumara\s*(ver|atar?\s*m[ıi]s[ıi]n|yolla)\b",
        r"\b(bulu[sş]al[ıi]m|bulu[sş]ak|g[oö]r[uü][sş]elim)\b",
        r"\b(tan[ıi][sş]al[ıi]m|tan[ıi][sş]mak\s*ist)\b",
        r"\b([cç][ıi]kal[ıi]m|[cç][ıi]kar\s*m[ıi]s[ıi]n)\b",
    ],
    "social_media": [
        r"\b(instagram|insta|instagramm?[ıi]n)\b",
        r"\b(snapchat|snap|snapim)\b",
        r"\b(whatsapp|wp|watsapp)\b",
        r"\b(telegram|tele)\b",
        r"\b(tiktok|tik\s*tok)\b",
        r"\b(dm\s*(at|gel|yaz)|[oö]zelden?\s*(yaz|gel))\b",
        r"\b(discord|dc\s*(gel|ver))\b",
    ],
}

_FLIRT_COMPILED: dict[str, list[re.Pattern]] = {}
for _cat, _pats in _FLIRT_PATTERNS_RAW.items():
    _FLIRT_COMPILED[_cat] = [re.compile(p, re.IGNORECASE) for p in _pats]


# ---------------------------------------------------------------------------
# Layer 4: Personal info patterns
# ---------------------------------------------------------------------------

_PERSONAL_INFO_PATTERNS = {
    "phone_tr": [
        re.compile(r"(?:0|\+90|90)\s*5\d{2}\s*\d{3}\s*\d{2}\s*\d{2}"),
        re.compile(r"\b05\d{9}\b"),
        re.compile(r"\b5\d{2}[\s.\-]?\d{3}[\s.\-]?\d{2}[\s.\-]?\d{2}\b"),
    ],
    "email": [
        re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    ],
    "social_handle": [
        re.compile(r"@[a-zA-Z0-9._]{3,30}"),
    ],
    "tc_kimlik": [
        re.compile(r"\b[1-9]\d{10}\b"),
    ],
    "address": [
        re.compile(
            r"\b(mahalle|mahallesi|mah\.|sokak|sok\.|cadde|cad\."
            r"|apartman|apt\.|daire|kat)\b",
            re.IGNORECASE,
        ),
    ],
}


# ---------------------------------------------------------------------------
# Layer 5: Inappropriate emojis
# ---------------------------------------------------------------------------

_INAPPROPRIATE_EMOJIS = {
    "\U0001f346",  # eggplant
    "\U0001f351",  # peach
    "\U0001f4a6",  # sweat droplets
    "\U0001f608",  # smiling devil
    "\U0001f445",  # tongue
    "\U0001f48b",  # kiss mark
    "\U0001f975",  # hot face
    "\U0001f924",  # drooling
}


# ---------------------------------------------------------------------------
# Main filter class
# ---------------------------------------------------------------------------


class SocialContentFilter:
    """7-layer content moderation pipeline for KIRO2 social features."""

    def __init__(self, redis_client=None):
        self._redis = redis_client

    async def filter_content(
        self,
        text: str,
        sender_id: str,
        content_type: str = "chat_message",
    ) -> FilterResult:
        """Run text through 7-layer pipeline. Short-circuits on first BLOCK."""
        start = time.monotonic()
        normalized = _normalize_tr(text)
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        results: dict[str, LayerResult] = {}

        layers = [
            ("length", lambda t: self._check_length(t, text)),
            ("blacklist", self._check_blacklist),
            ("flirt", self._check_flirt),
            ("personal_info", lambda t: self._check_personal_info(t, text)),
            ("emoji_abuse", lambda t: self._check_emoji_abuse(text)),
            ("spam", lambda t: self._check_spam(t, text)),
        ]

        blocked_layer = None
        flag_reason = "clean"

        for layer_name, checker in layers:
            result = checker(normalized)
            results[layer_name] = result
            if not result.passed:
                blocked_layer = layer_name
                flag_reason = layer_name
                break

        elapsed_ms = int((time.monotonic() - start) * 1000)
        sanitized = self._sanitize_pii(text) if blocked_layer != "length" else None

        return FilterResult(
            passed=(blocked_layer is None),
            blocked_layer=blocked_layer,
            flag_reason=flag_reason,
            confidence=results[blocked_layer].confidence if blocked_layer else 1.0,
            details=results,
            processing_ms=elapsed_ms,
            content_hash=content_hash,
            sanitized_content=sanitized,
        )

    # -- Layer 1: Length --

    @staticmethod
    def _check_length(normalized: str, raw: str) -> LayerResult:
        stripped = raw.strip()
        if not stripped:
            return LayerResult("length", False, 1.0, "Empty message")
        if len(stripped) > 2000:
            return LayerResult("length", False, 1.0, f"Too long: {len(stripped)} chars")
        return LayerResult("length", True)

    # -- Layer 2: Turkish blacklist --

    @staticmethod
    def _check_blacklist(normalized: str) -> LayerResult:
        # Check with evasion stripped too
        variants = [normalized, _strip_evasion(normalized), normalized.replace(" ", "")]
        matched = []
        for variant in variants:
            for pat in _BLACKLIST_PATTERNS:
                m = pat.search(variant)
                if m:
                    matched.append(m.group())
        if matched:
            return LayerResult(
                "blacklist",
                False,
                0.95,
                "Blacklisted word detected",
                list(set(matched)),
            )
        return LayerResult("blacklist", True)

    # -- Layer 3: Anti-flirt --

    @staticmethod
    def _check_flirt(normalized: str) -> LayerResult:
        matched = []
        for cat, patterns in _FLIRT_COMPILED.items():
            for pat in patterns:
                m = pat.search(normalized)
                if m:
                    matched.append(f"{cat}:{m.group()}")
        if matched:
            return LayerResult(
                "flirt",
                False,
                0.90,
                "Flirt pattern detected",
                matched,
            )
        return LayerResult("flirt", True)

    # -- Layer 4: Personal info --

    @staticmethod
    def _check_personal_info(normalized: str, raw: str) -> LayerResult:
        matched = []
        for cat, patterns in _PERSONAL_INFO_PATTERNS.items():
            for pat in patterns:
                m = pat.search(raw)
                if m:
                    matched.append(f"{cat}:{m.group()}")
        if matched:
            return LayerResult(
                "personal_info",
                False,
                0.95,
                "Personal info detected",
                matched,
            )
        return LayerResult("personal_info", True)

    # -- Layer 5: Emoji abuse --

    @staticmethod
    def _check_emoji_abuse(raw: str) -> LayerResult:
        # Count emojis using Unicode ranges
        emoji_count = sum(1 for ch in raw if ch in _INAPPROPRIATE_EMOJIS)
        if emoji_count >= 2:
            return LayerResult(
                "emoji_abuse",
                False,
                0.80,
                f"Inappropriate emojis: {emoji_count}",
            )

        # Check consecutive emoji spam (any emoji, >10)
        import emoji as emoji_lib

        emoji_chars = [ch for ch in raw if emoji_lib.is_emoji(ch)]
        if len(emoji_chars) > 10:
            text_chars = len(
                [ch for ch in raw if not emoji_lib.is_emoji(ch) and not ch.isspace()]
            )
            if text_chars == 0 or len(emoji_chars) / max(text_chars, 1) > 1.0:
                return LayerResult(
                    "emoji_abuse",
                    False,
                    0.70,
                    f"Emoji spam: {len(emoji_chars)} emojis",
                )
        return LayerResult("emoji_abuse", True)

    # -- Layer 6: Spam detection --

    @staticmethod
    def _check_spam(normalized: str, raw: str) -> LayerResult:
        # Repeated chars (>5 consecutive same char)
        if re.search(r"(.)\1{5,}", normalized):
            return LayerResult("spam", False, 0.85, "Repeated characters")

        # ALL CAPS (>80% uppercase, min 10 chars)
        alpha = [ch for ch in raw if ch.isalpha()]
        if len(alpha) >= 10:
            upper_ratio = sum(1 for ch in alpha if ch.isupper()) / len(alpha)
            if upper_ratio > 0.8:
                return LayerResult("spam", False, 0.75, "ALL CAPS message")

        # Excessive punctuation
        if re.search(r"[!?]{6,}", raw):
            return LayerResult("spam", False, 0.70, "Excessive punctuation")

        # Multiple URLs
        urls = re.findall(r"https?://\S+", raw)
        if len(urls) > 2:
            return LayerResult("spam", False, 0.80, f"Multiple URLs: {len(urls)}")

        return LayerResult("spam", True)

    # -- PII sanitizer --

    @staticmethod
    def _sanitize_pii(text: str) -> str:
        """Replace detected PII with [***]."""
        result = text
        for _cat, patterns in _PERSONAL_INFO_PATTERNS.items():
            for pat in patterns:
                result = pat.sub("[***]", result)
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_instance: SocialContentFilter | None = None


def get_social_content_filter(redis_client=None) -> SocialContentFilter:
    """Get or create the global filter instance."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        _instance = SocialContentFilter(redis_client=redis_client)
    return _instance
