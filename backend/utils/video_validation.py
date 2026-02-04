"""
Video Content Validation Utilities

Centralized video content validation for Turkish educational videos.
Consolidated from duplicate implementations across the codebase.
"""
from typing import Dict


def validate_video_content(video_data: Dict, min_edu_score: int = 1) -> bool:
    """
    Validate if video content is Turkish educational content.

    Args:
        video_data: Dictionary containing video metadata
        min_edu_score: Minimum educational keywords required (default: 1)

    Returns:
        bool: True if video appears to be Turkish educational content
    """
    title = video_data.get("title", "").lower()
    channel = video_data.get("channel", "").lower()
    description = video_data.get("description", "").lower()

    # Turkish educational indicators
    turkish_edu_keywords = [
        "tyt",
        "ayt",
        "yks",
        "matematik",
        "fizik",
        "kimya",
        "türkçe",
        "konu anlatım",
        "ders",
        "öğretmen",
        "akademi",
        "eğitim",
        "sınav",
        "hazırlık",
        "muallim",
        "üniversite",
    ]

    # Non-educational red flags
    non_edu_keywords = [
        "music",
        "song",
        "fireplace",
        "relaxing",
        "sleep",
        "asmr",
        "meditation",
        "10 hours",
        "full hd",
        "official music video",
        "gaming",
        "gameplay",
        "entertainment",
    ]

    content = f"{title} {channel} {description}"

    # Check for Turkish educational content
    edu_score = sum(1 for keyword in turkish_edu_keywords if keyword in content)
    non_edu_score = sum(1 for keyword in non_edu_keywords if keyword in content)

    # Must have educational content and no non-educational flags
    return edu_score >= min_edu_score and non_edu_score == 0


def validate_video_content_strict(video_data: Dict) -> bool:
    """
    Strict validation requiring at least 2 educational keywords.

    Args:
        video_data: Dictionary containing video metadata

    Returns:
        bool: True if video appears to be Turkish educational content (strict)
    """
    return validate_video_content(video_data, min_edu_score=2)


def validate_video_content_lenient(video_data: Dict) -> bool:
    """
    Lenient validation requiring at least 1 educational keyword.

    Args:
        video_data: Dictionary containing video metadata

    Returns:
        bool: True if video appears to be Turkish educational content (lenient)
    """
    return validate_video_content(video_data, min_edu_score=1)
