"""
Canonical Turkish YouTube Education Channels Registry
=====================================================
Single source of truth for trusted Turkish education channels.
All consumers import from here instead of maintaining inline lists.

Usage:
    from core.youtube_channels import (
        TRUSTED_TURKISH_CHANNELS,
        get_channel_names,
        get_channel_ids,
        get_channels_for_subject,
    )
"""

from __future__ import annotations

# Canonical channel registry — merged from 6 files:
#   turkish_content_filter.py, video_quality_validator.py,
#   advanced_youtube_search.py, semantic_youtube_search.py,
#   youtube_service.py, youtube/config.py
TRUSTED_TURKISH_CHANNELS: dict[str, dict] = {
    "TonguçAkademi": {
        "channel_id": "UC2sUP5sX8jXwkfBfRt9qgjg",
        "aliases": {"Tonguç Akademi", "Tonguc Akademi"},
        "quality_score": 9.5,
        "weight": 1.0,
        "subjects": ["matematik", "fizik", "kimya", "biyoloji"],
    },
    "Khan Academy Türkçe": {
        "channel_id": "UCY0pGqP5L7s7d9HuXndvazA",
        "aliases": set(),
        "quality_score": 8.5,
        "weight": 1.0,
        "subjects": ["matematik", "fizik"],
    },
    "KAMP Online": {
        "channel_id": "",
        "aliases": set(),
        "quality_score": 8.8,
        "weight": 0.95,
        "subjects": ["matematik", "fizik", "kimya"],
    },
    "Hocalara Geldik": {
        "channel_id": "UCnzWmJVXiLDREXMO5aZgqJA",
        "aliases": set(),
        "quality_score": 8.5,
        "weight": 0.9,
        "subjects": ["matematik", "fizik"],
    },
    "MEB Uzaktan Eğitim": {
        "channel_id": "",
        "aliases": set(),
        "quality_score": 8.0,
        "weight": 0.85,
        "subjects": None,  # all subjects
    },
    "EBA": {
        "channel_id": "",
        "aliases": set(),
        "quality_score": 8.0,
        "weight": 0.95,
        "subjects": None,  # all subjects
    },
    "BTK Akademi": {
        "channel_id": "UCzKPRFPpDrqQmz7G8OmRH5Q",
        "aliases": set(),
        "quality_score": 8.0,
        "weight": 0.9,
        "subjects": ["bilgisayar", "teknoloji"],
    },
    "Evrim Ağacı": {
        "channel_id": "UC_xsc5nsdVkHscvA0SWxBAw",
        "aliases": set(),
        "quality_score": 8.0,
        "weight": 0.85,
        "subjects": ["biyoloji", "fen"],
    },
    "Matematik Öğretmeni": {
        "channel_id": "",
        "aliases": {"Matematikçiler", "Matematikciler"},
        "quality_score": 9.0,
        "weight": 0.9,
        "subjects": ["matematik"],
    },
    "Fizik Öğretmeni": {
        "channel_id": "",
        "aliases": {"Fizik Muallimi", "Fizik Akademi"},
        "quality_score": 9.2,
        "weight": 0.92,
        "subjects": ["fizik"],
    },
    "Kimya Öğretmeni": {
        "channel_id": "",
        "aliases": {"Kimya Akademi"},
        "quality_score": 8.5,
        "weight": 0.9,
        "subjects": ["kimya"],
    },
    "Biyoloji Öğretmeni": {
        "channel_id": "",
        "aliases": {"Biyoloji Akademi"},
        "quality_score": 8.3,
        "weight": 0.9,
        "subjects": ["biyoloji"],
    },
    "Türkçe Öğretmeni": {
        "channel_id": "",
        "aliases": {"Türkçe Akademi", "Dil Öğretmeni"},
        "quality_score": 8.6,
        "weight": 0.9,
        "subjects": ["türkçe", "edebiyat"],
    },
    "Barış Özcan": {
        "channel_id": "UCWzx1P6f2EYls1__9RM3qZw",
        "aliases": set(),
        "quality_score": 8.0,
        "weight": 0.8,
        "subjects": ["fen", "teknoloji"],
    },
    "Tarih Öğretmeni": {
        "channel_id": "",
        "aliases": set(),
        "quality_score": 8.4,
        "weight": 0.85,
        "subjects": ["tarih"],
    },
    "Hocawebde": {
        "channel_id": "",
        "aliases": set(),
        "quality_score": 8.7,
        "weight": 0.87,
        "subjects": ["türkçe"],
    },
    "TRT EBA TV": {
        "channel_id": "",
        "aliases": set(),
        "quality_score": 8.9,
        "weight": 0.89,
        "subjects": None,  # all subjects
    },
}


# ---- Pre-computed lookups (built once at import time) ---- #

_all_names: set[str] = set()
_name_to_canonical: dict[str, str] = {}
for _name, _data in TRUSTED_TURKISH_CHANNELS.items():
    _all_names.add(_name)
    _name_to_canonical[_name.lower()] = _name
    for _alias in _data.get("aliases", set()):
        _all_names.add(_alias)
        _name_to_canonical[_alias.lower()] = _name


def get_channel_names() -> set[str]:
    """All channel names + aliases (set for O(1) lookup)."""
    return _all_names.copy()


def get_channel_ids() -> dict[str, float]:
    """channel_id -> weight mapping (only channels with known IDs)."""
    result: dict[str, float] = {}
    for data in TRUSTED_TURKISH_CHANNELS.values():
        cid = data.get("channel_id", "")
        if cid:
            result[cid] = data.get("weight", 0.8)
    return result


def _normalize_subject(s: str) -> str:
    """ASCII-safe subject normalization for matching."""
    # Türkçe büyük harf dönüşümü ÖNCE (.lower() I→i yapıyor, ı olmalı)
    s = s.replace("İ", "i").replace("I", "ı")
    return (
        s.lower()
        .strip()
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ı", "i")
    )


def get_channels_for_subject(subject: str) -> list[dict]:
    """Channels that cover a specific subject (ASCII-normalized matching)."""
    norm_subject = _normalize_subject(subject)
    result: list[dict] = []
    for name, data in TRUSTED_TURKISH_CHANNELS.items():
        subjects = data.get("subjects")
        if subjects is None or any(
            _normalize_subject(s) == norm_subject for s in subjects
        ):
            result.append({"name": name, **data})
    return result


def get_canonical_name(channel_name: str) -> str | None:
    """Resolve alias/variant to canonical channel name (case-insensitive)."""
    return _name_to_canonical.get(channel_name.lower().strip())


def is_trusted_channel(channel_name: str) -> bool:
    """Check if a channel name (or alias) is trusted (case-insensitive, partial match).

    Short names (<4 chars) require exact match to avoid false positives
    (e.g. "eba" matching inside "algebra").
    """
    if not channel_name:
        return False
    lower = channel_name.lower().strip()
    # Exact match (case-insensitive)
    if lower in _name_to_canonical:
        return True
    # Partial match — skip very short strings to avoid false positives
    for known in _name_to_canonical:
        shorter = min(len(known), len(lower))
        if shorter < 4:
            continue
        if known in lower or lower in known:
            return True
    return False


def get_channel_weight(channel_name: str) -> float:
    """Get channel weight by name/alias. Returns 0.0 if unknown."""
    canonical = get_canonical_name(channel_name)
    if canonical and canonical in TRUSTED_TURKISH_CHANNELS:
        return TRUSTED_TURKISH_CHANNELS[canonical].get("weight", 0.8)
    return 0.0
