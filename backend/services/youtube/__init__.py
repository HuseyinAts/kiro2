"""
YouTube Video Kesif Modulu

TYT/AYT sinav hazirlik videolari icin gelismis kesif sistemi.

Kullanim:
    from backend.services.youtube import YouTubeDiscovery, get_youtube_discovery
    from backend.services.youtube import SubjectType, DifficultyLevel, ExamType
    from backend.services.youtube import VideoMetadata

    # Singleton kullanimi
    discovery = get_youtube_discovery()

    # Video kesfi
    videos = await discovery.discover_videos(
        subject=SubjectType.MATEMATIK,
        difficulty=DifficultyLevel.ORTA,
        exam_type=ExamType.TYT,
        max_results=10
    )
"""

from .cache_manager import CacheManagerMixin
from .discovery import YouTubeDiscovery, get_youtube_discovery
from .models import (
    DIFFICULTY_ALIASES,
    SUBJECT_ALIASES,
    DifficultyLevel,
    ExamType,
    SubjectType,
    VideoMetadata,
)
from .quality_scorer import QualityScorerMixin
from .search_engine import SearchEngineMixin
from .turkish_filter import TurkishFilterMixin

__all__ = [
    # Main class
    "YouTubeDiscovery",
    "get_youtube_discovery",
    # Models
    "SubjectType",
    "DifficultyLevel",
    "ExamType",
    "VideoMetadata",
    # Aliases for backward compat
    "SUBJECT_ALIASES",
    "DIFFICULTY_ALIASES",
    # Mixins (for testing/extension)
    "SearchEngineMixin",
    "QualityScorerMixin",
    "TurkishFilterMixin",
    "CacheManagerMixin",
]
