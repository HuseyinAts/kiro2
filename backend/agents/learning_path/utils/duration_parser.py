"""
ISO 8601 Duration Parser for YouTube and other video platforms.

Converts ISO 8601 duration strings (e.g., PT1H30M15S) to minutes.
"""
from __future__ import annotations

import logging
import math
import re

logger = logging.getLogger(__name__)

# Pre-compiled regex for ISO 8601 duration
# Format: P[n]Y[n]M[n]DT[n]H[n]M[n]S
ISO_8601_DURATION_PATTERN = re.compile(
    r"^P"
    r"(?:(?P<years>\d+)Y)?"
    r"(?:(?P<months>\d+)M)?"
    r"(?:(?P<days>\d+)D)?"
    r"(?:T"
    r"(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?"
    r")?$"
)

DEFAULT_DURATION_MINUTES = 10


def parse_iso8601_duration(duration: str | None, default: int = DEFAULT_DURATION_MINUTES) -> int:
    """
    Parse ISO 8601 duration string to minutes.

    Args:
        duration: ISO 8601 duration string (e.g., "PT1H30M")
        default: Default value if parsing fails

    Returns:
        Duration in minutes

    Examples:
        >>> parse_iso8601_duration("PT1H")
        60
        >>> parse_iso8601_duration("PT30M")
        30
        >>> parse_iso8601_duration("PT1H30M15S")
        91
        >>> parse_iso8601_duration(None)
        10
    """
    if not duration:
        return default

    duration = duration.strip().upper()

    match = ISO_8601_DURATION_PATTERN.match(duration)
    if not match:
        logger.warning(f"Invalid ISO 8601 duration format: {duration}")
        return default

    try:
        groups = match.groupdict()

        # Extract components (default to 0 if not present)
        years = int(groups.get("years") or 0)
        months = int(groups.get("months") or 0)
        days = int(groups.get("days") or 0)
        hours = int(groups.get("hours") or 0)
        minutes = int(groups.get("minutes") or 0)
        seconds = float(groups.get("seconds") or 0)

        # Convert to total minutes
        # Use ceiling for seconds to ensure any partial minute rounds up
        seconds_in_minutes = math.ceil(seconds / 60) if seconds > 0 else 0

        total_minutes = (
            years * 525600  # ~365.25 days * 24 hours * 60 min
            + months * 43800  # ~30.4 days * 24 hours * 60 min
            + days * 1440  # 24 hours * 60 min
            + hours * 60
            + minutes
            + seconds_in_minutes
        )

        # Ensure at least 1 minute for non-zero durations
        if total_minutes == 0 and (years or months or days or hours or minutes or seconds):
            total_minutes = 1

        return total_minutes if total_minutes > 0 else default

    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing duration {duration}: {e}")
        return default


def format_duration_minutes(minutes: int) -> str:
    """
    Format minutes to human-readable Turkish string.

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted string (e.g., "1 saat 30 dakika")

    Examples:
        >>> format_duration_minutes(90)
        '1 saat 30 dakika'
        >>> format_duration_minutes(30)
        '30 dakika'
        >>> format_duration_minutes(1560)
        '1 gün 2 saat'
    """
    if minutes < 1:
        return "1 dakikadan az"

    hours, mins = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts = []
    if days > 0:
        parts.append(f"{days} gün")
    if hours > 0:
        parts.append(f"{hours} saat")
    if mins > 0:
        parts.append(f"{mins} dakika")

    return " ".join(parts) if parts else "1 dakikadan az"
