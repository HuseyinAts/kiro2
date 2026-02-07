"""
Timezone Utilities - Phase 3.0
Comprehensive timezone handling for KIRO2 platform

Provides automatic UTC conversion, Turkish timezone support, and datetime utilities
to eliminate timezone-naive datetime bugs across the platform.

Key Features:
- Automatic UTC timezone awareness
- Turkish (Europe/Istanbul) timezone conversion
- Safe datetime parsing and formatting
- ORM integration helpers
- Request/response datetime conversion

Migration Path:
- Replace: datetime.now() → now_utc()
- Replace: datetime.now(timezone.utc) → now_utc() (utcnow deprecated in Python 3.12+)
- Use: to_turkish_time(dt) for user-facing timestamps
- Use: ensure_utc(dt) to guarantee UTC timezone
"""

from datetime import datetime, date, timezone, timedelta
from typing import Optional, Any, Dict
from zoneinfo import ZoneInfo
import re

# Turkish timezone (Europe/Istanbul = UTC+3)
TURKISH_TIMEZONE = ZoneInfo("Europe/Istanbul")
UTC_TIMEZONE = timezone.utc


# ================================================================
# CORE DATETIME UTILITIES
# ================================================================

def now_utc() -> datetime:
    """
    Get current UTC time with timezone awareness

    REPLACEMENT FOR:
    - datetime.now() → now_utc()
    - datetime.now(timezone.utc) → now_utc() (deprecated)

    Returns:
        datetime: Current time in UTC with timezone info

    Example:
        >>> now = now_utc()
        >>> print(now)  # 2025-11-22 15:30:00+00:00
    """
    return datetime.now(UTC_TIMEZONE)


def now_turkish() -> datetime:
    """
    Get current time in Turkish timezone (Europe/Istanbul)

    Returns:
        datetime: Current time in Turkish timezone

    Example:
        >>> now = now_turkish()
        >>> print(now)  # 2025-11-22 18:30:00+03:00 (UTC+3)
    """
    return datetime.now(TURKISH_TIMEZONE)


def today_utc() -> date:
    """
    Get today's date in UTC

    Returns:
        date: Today's date in UTC

    Example:
        >>> today = today_utc()
        >>> print(today)  # 2025-11-22
    """
    return now_utc().date()


def today_turkish() -> date:
    """
    Get today's date in Turkish timezone

    Returns:
        date: Today's date in Turkish timezone
    """
    return now_turkish().date()


# ================================================================
# TIMEZONE CONVERSION UTILITIES
# ================================================================

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure datetime is in UTC timezone

    Handles:
    - Timezone-naive datetimes → assumed UTC, made aware
    - Non-UTC timezone-aware → converted to UTC
    - Already UTC → returned as-is
    - None → returned as None

    Args:
        dt: Input datetime (can be naive or aware)

    Returns:
        datetime: UTC timezone-aware datetime or None

    Example:
        >>> naive_dt = datetime(2025, 11, 22, 15, 30)  # Naive
        >>> utc_dt = ensure_utc(naive_dt)
        >>> print(utc_dt)  # 2025-11-22 15:30:00+00:00
    """
    if dt is None:
        return None

    # Already UTC timezone-aware
    if dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) == timedelta(0):
        return dt

    # Timezone-naive → assume UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC_TIMEZONE)

    # Other timezone → convert to UTC
    return dt.astimezone(UTC_TIMEZONE)


def to_turkish_time(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert datetime to Turkish timezone (Europe/Istanbul)

    Args:
        dt: Input datetime (UTC or other timezone)

    Returns:
        datetime: Turkish timezone-aware datetime or None

    Example:
        >>> utc_dt = now_utc()  # 15:30:00 UTC
        >>> tr_dt = to_turkish_time(utc_dt)
        >>> print(tr_dt)  # 18:30:00+03:00 (3 hours ahead)
    """
    if dt is None:
        return None

    # Ensure UTC first
    utc_dt = ensure_utc(dt)

    # Convert to Turkish timezone
    return utc_dt.astimezone(TURKISH_TIMEZONE)


def from_turkish_time(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert Turkish timezone datetime to UTC

    Args:
        dt: Turkish timezone datetime

    Returns:
        datetime: UTC timezone-aware datetime or None

    Example:
        >>> tr_dt = now_turkish()  # 18:30:00+03:00
        >>> utc_dt = from_turkish_time(tr_dt)
        >>> print(utc_dt)  # 15:30:00+00:00
    """
    if dt is None:
        return None

    # If timezone-naive, assume Turkish timezone
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TURKISH_TIMEZONE)

    # Convert to UTC
    return dt.astimezone(UTC_TIMEZONE)


# ================================================================
# DATETIME PARSING UTILITIES
# ================================================================

def parse_datetime(
    dt_str: Optional[str],
    assume_utc: bool = True
) -> Optional[datetime]:
    """
    Safely parse datetime string to timezone-aware datetime

    Handles:
    - ISO 8601 formats (with/without timezone)
    - Common datetime formats
    - Invalid inputs → None

    Args:
        dt_str: Datetime string to parse
        assume_utc: If True and no timezone in string, assume UTC

    Returns:
        datetime: Parsed timezone-aware datetime or None

    Example:
        >>> dt = parse_datetime("2025-11-22T15:30:00Z")
        >>> print(dt)  # 2025-11-22 15:30:00+00:00

        >>> dt = parse_datetime("2025-11-22 15:30:00")  # No timezone
        >>> print(dt)  # 2025-11-22 15:30:00+00:00 (assumed UTC)
    """
    if not dt_str:
        return None

    try:
        # Try ISO format with timezone
        if "Z" in dt_str:
            dt_str = dt_str.replace("Z", "+00:00")

        # Parse datetime
        dt = datetime.fromisoformat(dt_str)

        # Make timezone-aware if naive
        if dt.tzinfo is None and assume_utc:
            dt = dt.replace(tzinfo=UTC_TIMEZONE)

        return ensure_utc(dt)

    except (ValueError, AttributeError):
        return None


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """
    Safely parse date string to date object

    Args:
        date_str: Date string (YYYY-MM-DD format)

    Returns:
        date: Parsed date or None

    Example:
        >>> d = parse_date("2025-11-22")
        >>> print(d)  # 2025-11-22
    """
    if not date_str:
        return None

    try:
        # Try ISO format YYYY-MM-DD
        if isinstance(date_str, str):
            return date.fromisoformat(date_str)
        return date_str
    except (ValueError, AttributeError):
        return None


# ================================================================
# DATETIME FORMATTING UTILITIES
# ================================================================

def format_datetime_utc(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime as ISO 8601 UTC string

    Args:
        dt: Datetime to format

    Returns:
        str: ISO 8601 formatted string (UTC) or None

    Example:
        >>> dt = now_utc()
        >>> print(format_datetime_utc(dt))
        # "2025-11-22T15:30:00.123456+00:00"
    """
    if dt is None:
        return None

    utc_dt = ensure_utc(dt)
    return utc_dt.isoformat()


def format_datetime_turkish(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime as ISO 8601 Turkish timezone string

    Args:
        dt: Datetime to format

    Returns:
        str: ISO 8601 formatted string (Turkish timezone) or None

    Example:
        >>> dt = now_utc()
        >>> print(format_datetime_turkish(dt))
        # "2025-11-22T18:30:00.123456+03:00"
    """
    if dt is None:
        return None

    tr_dt = to_turkish_time(dt)
    return tr_dt.isoformat()


def format_datetime_turkish_display(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime for Turkish user display (DD.MM.YYYY HH:MM)

    Args:
        dt: Datetime to format

    Returns:
        str: Turkish-formatted datetime string or None

    Example:
        >>> dt = now_utc()
        >>> print(format_datetime_turkish_display(dt))
        # "22.11.2025 18:30"
    """
    if dt is None:
        return None

    tr_dt = to_turkish_time(dt)
    return tr_dt.strftime("%d.%m.%Y %H:%M")


def format_date_turkish(d: Optional[date]) -> Optional[str]:
    """
    Format date for Turkish display (DD.MM.YYYY)

    Args:
        d: Date to format

    Returns:
        str: Turkish-formatted date string or None

    Example:
        >>> d = today_utc()
        >>> print(format_date_turkish(d))
        # "22.11.2025"
    """
    if d is None:
        return None

    return d.strftime("%d.%m.%Y")


# ================================================================
# DICTIONARY/JSON DATETIME CONVERSION
# ================================================================

def convert_dict_datetimes_to_utc(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert all datetime values in dictionary to UTC

    Args:
        data: Dictionary potentially containing datetime values

    Returns:
        dict: Dictionary with all datetimes converted to UTC

    Example:
        >>> data = {"created_at": datetime(2025, 11, 22, 15, 30)}
        >>> result = convert_dict_datetimes_to_utc(data)
        >>> print(result["created_at"])
        # 2025-11-22 15:30:00+00:00
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = ensure_utc(value)
        elif isinstance(value, dict):
            result[key] = convert_dict_datetimes_to_utc(value)
        elif isinstance(value, list):
            result[key] = [
                convert_dict_datetimes_to_utc(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def convert_dict_datetimes_to_turkish(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively convert all datetime values in dictionary to Turkish timezone

    Args:
        data: Dictionary potentially containing datetime values

    Returns:
        dict: Dictionary with all datetimes converted to Turkish timezone

    Example:
        >>> data = {"created_at": now_utc()}
        >>> result = convert_dict_datetimes_to_turkish(data)
        >>> print(result["created_at"])
        # 2025-11-22 18:30:00+03:00 (3 hours ahead of UTC)
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = to_turkish_time(value)
        elif isinstance(value, dict):
            result[key] = convert_dict_datetimes_to_turkish(value)
        elif isinstance(value, list):
            result[key] = [
                convert_dict_datetimes_to_turkish(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def format_dict_datetimes_for_api(data: Dict[str, Any], use_turkish: bool = False) -> Dict[str, Any]:
    """
    Format all datetime values in dictionary to ISO strings for API responses

    Args:
        data: Dictionary potentially containing datetime values
        use_turkish: If True, format as Turkish timezone; otherwise UTC

    Returns:
        dict: Dictionary with all datetimes formatted as ISO strings

    Example:
        >>> data = {"created_at": now_utc(), "count": 42}
        >>> result = format_dict_datetimes_for_api(data)
        >>> print(result)
        # {"created_at": "2025-11-22T15:30:00+00:00", "count": 42}
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            if use_turkish:
                result[key] = format_datetime_turkish(value)
            else:
                result[key] = format_datetime_utc(value)
        elif isinstance(value, date) and not isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            result[key] = format_dict_datetimes_for_api(value, use_turkish)
        elif isinstance(value, list):
            result[key] = [
                format_dict_datetimes_for_api(item, use_turkish) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


# ================================================================
# SQLALCHEMY ORM HELPERS
# ================================================================

def get_current_utc_for_db() -> datetime:
    """
    Get current UTC time for database storage

    Use this as default factory for SQLAlchemy DateTime columns:

    Example:
        from sqlalchemy.orm import mapped_column
        from datetime import datetime

        class MyModel(Base):
            created_at = mapped_column(
                DateTime(timezone=True),
                default=get_current_utc_for_db
            )
    """
    return now_utc()


def convert_db_datetime_to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert database datetime to UTC (handles both naive and aware)

    Args:
        dt: Datetime from database

    Returns:
        datetime: UTC timezone-aware datetime or None

    Example:
        >>> db_dt = session.query(User).first().created_at
        >>> utc_dt = convert_db_datetime_to_utc(db_dt)
    """
    return ensure_utc(dt)


# ================================================================
# TIME DELTA UTILITIES
# ================================================================

def seconds_between(dt1: datetime, dt2: datetime) -> float:
    """
    Calculate seconds between two datetimes (handles timezone differences)

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        float: Number of seconds between datetimes (dt1 - dt2)

    Example:
        >>> start = now_utc()
        >>> end = start + timedelta(hours=2, minutes=30)
        >>> seconds = seconds_between(end, start)
        >>> print(seconds)  # 9000.0 (2.5 hours)
    """
    utc_dt1 = ensure_utc(dt1)
    utc_dt2 = ensure_utc(dt2)

    if utc_dt1 is None or utc_dt2 is None:
        return 0.0

    delta = utc_dt1 - utc_dt2
    return delta.total_seconds()


def minutes_between(dt1: datetime, dt2: datetime) -> float:
    """
    Calculate minutes between two datetimes

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        float: Number of minutes between datetimes
    """
    return seconds_between(dt1, dt2) / 60.0


def hours_between(dt1: datetime, dt2: datetime) -> float:
    """
    Calculate hours between two datetimes

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        float: Number of hours between datetimes
    """
    return seconds_between(dt1, dt2) / 3600.0


def days_between(dt1: datetime, dt2: datetime) -> float:
    """
    Calculate days between two datetimes

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        float: Number of days between datetimes
    """
    return seconds_between(dt1, dt2) / 86400.0


# ================================================================
# VALIDATION UTILITIES
# ================================================================

def is_timezone_aware(dt: Optional[datetime]) -> bool:
    """
    Check if datetime is timezone-aware

    Args:
        dt: Datetime to check

    Returns:
        bool: True if timezone-aware, False otherwise

    Example:
        >>> dt = datetime.now()  # Naive
        >>> print(is_timezone_aware(dt))  # False

        >>> dt = now_utc()  # Aware
        >>> print(is_timezone_aware(dt))  # True
    """
    if dt is None:
        return False
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def is_utc(dt: Optional[datetime]) -> bool:
    """
    Check if datetime is in UTC timezone

    Args:
        dt: Datetime to check

    Returns:
        bool: True if UTC timezone, False otherwise
    """
    if not is_timezone_aware(dt):
        return False
    return dt.tzinfo.utcoffset(dt) == timedelta(0)


# ================================================================
# MIGRATION HELPERS
# ================================================================

def migrate_datetime_now_to_utc(code_str: str) -> str:
    """
    Migrate datetime.now() to now_utc() in code string

    This is a code migration helper. Use fix_timezone_naive_datetime.py
    script for bulk file migrations.

    Args:
        code_str: Python code as string

    Returns:
        str: Migrated code with now_utc() calls

    Example:
        >>> code = "created_at = datetime.now()"
        >>> migrated = migrate_datetime_now_to_utc(code)
        >>> print(migrated)  # "created_at = now_utc()"
    """
    # Replace datetime.now() with now_utc()
    code_str = re.sub(
        r'datetime\.now\(\)',
        'now_utc()',
        code_str
    )

    # Replace datetime.now(timezone.utc) with now_utc() (deprecated)
    code_str = re.sub(
        r'datetime\.utcnow\(\)',
        'now_utc()',
        code_str
    )

    return code_str


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    # Core utilities
    "now_utc",
    "now_turkish",
    "today_utc",
    "today_turkish",

    # Timezone conversion
    "ensure_utc",
    "to_turkish_time",
    "from_turkish_time",

    # Parsing
    "parse_datetime",
    "parse_date",

    # Formatting
    "format_datetime_utc",
    "format_datetime_turkish",
    "format_datetime_turkish_display",
    "format_date_turkish",

    # Dictionary conversion
    "convert_dict_datetimes_to_utc",
    "convert_dict_datetimes_to_turkish",
    "format_dict_datetimes_for_api",

    # ORM helpers
    "get_current_utc_for_db",
    "convert_db_datetime_to_utc",

    # Time delta
    "seconds_between",
    "minutes_between",
    "hours_between",
    "days_between",

    # Validation
    "is_timezone_aware",
    "is_utc",

    # Constants
    "TURKISH_TIMEZONE",
    "UTC_TIMEZONE",
]
