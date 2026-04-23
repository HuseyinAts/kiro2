"""
YouTube Video Kesif Sistemi - Backward Compatibility Wrapper

DEPRECATED: Bu dosya backward compatibility icin tutuluyor.
Yeni kod icin backend/services/youtube/ modulu kullanin.

Kullanim:
    # Eski (calismaya devam eder):
    from backend.services.youtube_discovery import YouTubeDiscovery

    # Yeni (tercih edilen):
    from backend.services.youtube import YouTubeDiscovery

Migration:
    1. Import'lari guncelle:
       - from backend.services.youtube_discovery import X
       + from backend.services.youtube import X

    2. Enum degerleri guncellendi (Turkce karakterler kaldirildi):
       - DifficultyLevel.BASLANGIC.value = "baslangic" (eski: "baslanigc")
       - SubjectType.TURKCE.value = "turkce" (eski: "turkce")
"""

import warnings

# Backward compatibility imports
from services.youtube import (
    CacheManagerMixin,
    DifficultyLevel,
    ExamType,
    QualityScorerMixin,
    SearchEngineMixin,
    SubjectType,
    TurkishFilterMixin,
    VideoMetadata,
    YouTubeDiscovery,
    get_youtube_discovery,
)

# Deprecation warning
warnings.warn(
    "youtube_discovery module is deprecated. "
    "Use 'from backend.services.youtube import YouTubeDiscovery' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "CacheManagerMixin",
    "DifficultyLevel",
    "ExamType",
    "QualityScorerMixin",
    "SearchEngineMixin",
    "SubjectType",
    "TurkishFilterMixin",
    "VideoMetadata",
    "YouTubeDiscovery",
    "get_youtube_discovery",
]
