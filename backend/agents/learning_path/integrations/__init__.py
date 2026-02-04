"""
External Service Integrations

This package contains integrations with external services:
- YouTubeIntegration: YouTube API integration
- KhanIntegration: Khan Academy API integration
- OERIntegration: Open Educational Resources integration
- ChatIntegration: Chat interface integration
- FormIntegration: Form interface integration
"""

from .youtube_integration import YouTubeIntegration
from .khan_integration import KhanIntegration
from .oer_integration import OERIntegration
from .chat_integration import ChatIntegration
from .form_integration import FormIntegration

__all__ = [
    "YouTubeIntegration",
    "KhanIntegration",
    "OERIntegration",
    "ChatIntegration",
    "FormIntegration",
]
