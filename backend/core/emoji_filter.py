"""Emoji filter processor for structlog"""
import re

from structlog.types import EventDict


def remove_emoji_processor(logger, method_name, event_dict: EventDict) -> EventDict:
    """Remove emojis from log messages to prevent encoding errors"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\u2600-\u26FF"  # misc symbols
        "\u2700-\u27BF"  # dingbats
        "\u2B50-\u2B55"  # stars
        "]+",
        flags=re.UNICODE,
    )

    # Clean the main event message
    if "event" in event_dict:
        event_dict["event"] = emoji_pattern.sub("", str(event_dict["event"])).strip()

    # Clean all string values in the dict
    for key, value in list(event_dict.items()):
        if isinstance(value, str):
            event_dict[key] = emoji_pattern.sub("", value).strip()

    return event_dict
