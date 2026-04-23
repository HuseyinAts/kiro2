"""YouTube Integration Wrapper"""
import logging
from typing import Any

from agents.learning_path.utils.duration_parser import parse_iso8601_duration

logger = logging.getLogger(__name__)


class YouTubeIntegration:
    """YouTube API integration wrapper"""

    def __init__(self, youtube_service):
        self.service = youtube_service
        logger.info("YouTubeIntegration initialized")

    async def search_videos(
        self, query: str, max_results: int = 10, language: str = "tr"
    ) -> list[dict[str, Any]]:
        """Search YouTube videos"""
        try:
            return await self.service.search(
                query=query, max_results=max_results, language=language
            )
        except Exception as e:
            logger.error(f"YouTube search error: {e!s}")
            return []

    def parse_duration(self, duration_str: str | None, default: int = 10) -> int:
        """
        Parse YouTube ISO 8601 duration to minutes.

        Args:
            duration_str: ISO 8601 duration string (e.g., "PT1H30M15S")
            default: Default value if parsing fails

        Returns:
            Duration in minutes

        Examples:
            >>> integration.parse_duration("PT1H30M")
            90
            >>> integration.parse_duration("PT10M")
            10
        """
        return parse_iso8601_duration(duration_str, default=default)
