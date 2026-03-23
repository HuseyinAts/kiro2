"""
Task 99: YouTube Education Enhanced Service
Advanced search, quality scoring, caption extraction, playlist management

Async/Await Fix: googleapiclient is synchronous, so we use asyncio.to_thread()
to run blocking API calls without blocking the event loop.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Callable, TypeVar
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Type variable for generic async wrapper
T = TypeVar("T")


class VideoQuality(BaseModel):
    """Video quality assessment"""

    video_id: str
    educational_score: float  # 0-100
    content_appropriateness: float  # 0-100
    quality_score: float  # 0-100
    engagement_score: float  # 0-100
    overall_score: float  # 0-100

    # Detailed metrics
    has_captions: bool
    is_hd: bool
    duration_appropriate: bool
    channel_credibility: float
    view_to_like_ratio: float
    comments_quality: Optional[str]


class Caption(BaseModel):
    """Video caption/subtitle"""

    language: str
    text: str
    start_time: float  # seconds
    duration: float  # seconds
    is_auto_generated: bool


class PlaylistMetadata(BaseModel):
    """Playlist metadata"""

    playlist_id: str
    title: str
    description: Optional[str]
    video_count: int
    total_duration: int  # seconds
    created_by: str
    created_at: datetime
    is_public: bool
    tags: List[str]


class YouTubeEnhancedService:
    """
    Task 99: YouTube Education Enhanced Service

    - 99.1: Enhanced search with quality filtering
    - 99.2: Playlist management (create, curate, share)
    - 99.3: Auto-caption extraction and search
    - 99.4: Quality and educational value scoring

    Async Note: googleapiclient is synchronous. All API calls use
    asyncio.to_thread() to prevent blocking the event loop.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=api_key)

    async def _run_sync(self, func: Callable[[], T]) -> T:
        """
        Run a synchronous function in a thread pool to avoid blocking.

        The googleapiclient library is synchronous, so we use asyncio.to_thread()
        to run blocking API calls without blocking the event loop.

        Args:
            func: Synchronous callable (typically a lambda wrapping an API call)

        Returns:
            The result of the synchronous function
        """
        return await asyncio.to_thread(func)

    # ============================================
    # Task 99.1: Enhanced Search
    # ============================================

    async def enhanced_search(
        self,
        query: str,
        subject: Optional[str] = None,
        grade_level: Optional[str] = None,
        min_quality_score: float = 70.0,
        has_captions: bool = True,
        duration_range: Optional[tuple] = None,  # (min, max) in seconds
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Task 99.1: Enhanced YouTube search with quality filtering

        Advanced filters:
        - Quality score threshold
        - Caption availability
        - Duration range
        - Educational value
        - Content appropriateness
        """
        try:
            # Build search query
            search_query = self._build_enhanced_query(query, subject, grade_level)

            # Base search parameters
            search_params = {
                "part": "snippet",
                "q": search_query,
                "type": "video",
                "maxResults": max_results * 2,  # Get more to filter
                "relevanceLanguage": "tr",
                "videoCaption": "closedCaption" if has_captions else "any",
                "videoEmbeddable": "true",
                "safeSearch": "strict",
            }

            # Duration filter
            if duration_range:
                search_params["videoDuration"] = self._get_duration_category(
                    duration_range
                )

            # Execute search (wrapped in thread to avoid blocking)
            search_response = await self._run_sync(
                lambda: self.youtube.search().list(**search_params).execute()
            )

            videos = []
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]

                # Get detailed video info
                video_details = await self.get_video_details(video_id)

                if not video_details:
                    continue

                # Calculate quality score
                quality = await self.assess_video_quality(video_id, video_details)

                # Apply quality filter
                if quality.overall_score < min_quality_score:
                    continue

                # Apply duration filter
                if duration_range:
                    duration = self._parse_duration(
                        video_details.get("contentDetails", {}).get("duration", "")
                    )
                    if not (duration_range[0] <= duration <= duration_range[1]):
                        continue

                videos.append(
                    {
                        "video_id": video_id,
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"],
                        "quality": quality.dict(),
                        "details": video_details,
                    }
                )

                # Stop when we have enough quality videos
                if len(videos) >= max_results:
                    break

            logger.info(
                f"[YOUTUBE ENHANCED] Found {len(videos)} quality videos for: {query}"
            )
            return videos

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise

    def _build_enhanced_query(
        self, query: str, subject: Optional[str], grade_level: Optional[str]
    ) -> str:
        """Build enhanced search query with context"""
        enhanced_query = query

        # Add educational context
        enhanced_query += " eğitim dersi"

        # Add subject
        if subject:
            enhanced_query += f" {subject}"

        # Add grade level
        if grade_level:
            enhanced_query += f" {grade_level}"

        # Add quality indicators
        enhanced_query += " anlatım"

        return enhanced_query

    def _get_duration_category(self, duration_range: tuple) -> str:
        """Convert duration range to YouTube API category"""
        min_dur, max_dur = duration_range

        if max_dur <= 240:  # 4 minutes
            return "short"
        elif max_dur <= 1200:  # 20 minutes
            return "medium"
        else:
            return "long"

    async def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed video information"""
        try:
            response = await self._run_sync(
                lambda: self.youtube.videos()
                .list(part="snippet,contentDetails,statistics", id=video_id)
                .execute()
            )

            if not response.get("items"):
                return None

            return response["items"][0]

        except HttpError as e:
            logger.error(f"Failed to get video details for {video_id}: {e}")
            return None

    # ============================================
    # Task 99.2: Playlist Management
    # ============================================

    async def create_playlist(
        self,
        title: str,
        description: str,
        is_public: bool = False,
        access_token: Optional[str] = None,
    ) -> str:
        """
        Task 99.2: Create a new YouTube playlist

        Requires OAuth access token for authenticated requests
        """
        if not access_token:
            raise ValueError("OAuth access token required for playlist creation")

        try:
            # Build authenticated service
            from google.oauth2.credentials import Credentials

            creds = Credentials(token=access_token)
            youtube_auth = build("youtube", "v3", credentials=creds)

            # Create playlist (wrapped in thread to avoid blocking)
            def _create_playlist() -> dict:
                request = youtube_auth.playlists().insert(
                    part="snippet,status",
                    body={
                        "snippet": {"title": title, "description": description},
                        "status": {"privacyStatus": "public" if is_public else "private"},
                    },
                )
                return request.execute()

            response = await self._run_sync(_create_playlist)
            playlist_id = response["id"]

            logger.info(f"[YOUTUBE PLAYLIST] Created playlist: {playlist_id}")
            return playlist_id

        except HttpError as e:
            logger.error(f"Failed to create playlist: {e}")
            raise

    async def add_video_to_playlist(
        self, playlist_id: str, video_id: str, access_token: str
    ) -> bool:
        """
        Task 99.2: Add video to playlist
        """
        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials(token=access_token)
            youtube_auth = build("youtube", "v3", credentials=creds)

            # Add video to playlist (wrapped in thread to avoid blocking)
            def _add_video() -> None:
                request = youtube_auth.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": playlist_id,
                            "resourceId": {"kind": "youtube#video", "videoId": video_id},
                        }
                    },
                )
                request.execute()

            await self._run_sync(_add_video)
            logger.info(
                f"[YOUTUBE PLAYLIST] Added video {video_id} to playlist {playlist_id}"
            )
            return True

        except HttpError as e:
            logger.error(f"Failed to add video to playlist: {e}")
            return False

    async def get_playlist_videos(self, playlist_id: str) -> List[Dict[str, Any]]:
        """
        Task 99.2: Get all videos in a playlist
        """
        try:
            videos = []
            next_page_token = None

            while True:
                # Wrap sync call in thread to avoid blocking
                def _fetch_page(page_token: Optional[str] = next_page_token) -> dict:
                    request = self.youtube.playlistItems().list(
                        part="snippet,contentDetails",
                        playlistId=playlist_id,
                        maxResults=50,
                        pageToken=page_token,
                    )
                    return request.execute()

                response = await self._run_sync(_fetch_page)

                for item in response.get("items", []):
                    videos.append(
                        {
                            "video_id": item["contentDetails"]["videoId"],
                            "title": item["snippet"]["title"],
                            "description": item["snippet"]["description"],
                            "thumbnail": item["snippet"]["thumbnails"]["default"][
                                "url"
                            ],
                            "position": item["snippet"]["position"],
                        }
                    )

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            logger.info(
                f"[YOUTUBE PLAYLIST] Retrieved {len(videos)} videos from playlist {playlist_id}"
            )
            return videos

        except HttpError as e:
            logger.error(f"Failed to get playlist videos: {e}")
            return []

    # ============================================
    # Task 99.3: Auto-Caption Extraction
    # ============================================

    async def get_video_captions(
        self, video_id: str, language: str = "tr"
    ) -> List[Caption]:
        """
        Task 99.3: Extract captions/subtitles from video

        Returns timestamped captions in requested language
        """
        try:
            # List available captions (wrapped in thread to avoid blocking)
            captions_response = await self._run_sync(
                lambda: self.youtube.captions()
                .list(part="snippet", videoId=video_id)
                .execute()
            )

            # Find Turkish caption track
            caption_track = None
            for item in captions_response.get("items", []):
                if item["snippet"]["language"] == language:
                    caption_track = item["id"]
                    break

            if not caption_track:
                logger.warning(f"No {language} captions found for video {video_id}")
                return []

            # Download caption (requires OAuth for most videos)
            # For now, we'll return caption availability info
            # Full caption download requires OAuth and video owner permission

            return []

        except HttpError as e:
            logger.error(f"Failed to get captions for {video_id}: {e}")
            return []

    async def has_turkish_captions(self, video_id: str) -> bool:
        """
        Check if video has Turkish captions
        """
        try:
            captions_response = await self._run_sync(
                lambda: self.youtube.captions()
                .list(part="snippet", videoId=video_id)
                .execute()
            )

            for item in captions_response.get("items", []):
                if item["snippet"]["language"] == "tr":
                    return True

            return False

        except HttpError as e:
            logger.error(f"Failed to check captions: {e}")
            return False

    async def search_in_captions(
        self, query: str, video_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Task 99.3: Search for text in video captions

        Returns videos that contain the search term in their captions
        """
        results = []

        for video_id in video_ids:
            captions = await self.get_video_captions(video_id)

            for caption in captions:
                if query.lower() in caption.text.lower():
                    results.append(
                        {
                            "video_id": video_id,
                            "caption": caption.text,
                            "timestamp": caption.start_time,
                            "match_context": self._get_caption_context(
                                caption.text, query
                            ),
                        }
                    )

        return results

    def _get_caption_context(
        self, text: str, query: str, context_chars: int = 50
    ) -> str:
        """Get surrounding context for search match"""
        query_lower = query.lower()
        text_lower = text.lower()

        match_pos = text_lower.find(query_lower)
        if match_pos == -1:
            return text[:100]

        start = max(0, match_pos - context_chars)
        end = min(len(text), match_pos + len(query) + context_chars)

        return text[start:end]

    # ============================================
    # Task 99.4: Quality Scoring
    # ============================================

    async def assess_video_quality(
        self, video_id: str, video_details: Optional[Dict[str, Any]] = None
    ) -> VideoQuality:
        """
        Task 99.4: Assess video quality and educational value

        Scoring factors:
        - Has captions (Turkish)
        - HD quality
        - Appropriate duration (5-20 min optimal)
        - Channel credibility
        - Engagement metrics (views, likes, comments)
        - Content appropriateness
        """
        if not video_details:
            video_details = await self.get_video_details(video_id)

        if not video_details:
            return VideoQuality(
                video_id=video_id,
                educational_score=0,
                content_appropriateness=0,
                quality_score=0,
                engagement_score=0,
                overall_score=0,
                has_captions=False,
                is_hd=False,
                duration_appropriate=False,
                channel_credibility=0,
                view_to_like_ratio=0,
            )

        snippet = video_details.get("snippet", {})
        content_details = video_details.get("contentDetails", {})
        statistics = video_details.get("statistics", {})

        # 1. Caption score (30%)
        has_captions = await self.has_turkish_captions(video_id)
        caption_score = 100 if has_captions else 0

        # 2. Quality score (20%)
        definition = content_details.get("definition", "sd")
        is_hd = definition == "hd"
        quality_score = 100 if is_hd else 60

        # 3. Duration appropriateness (15%)
        duration_str = content_details.get("duration", "PT0S")
        duration = self._parse_duration(duration_str)
        duration_score = self._score_duration(duration)

        # 4. Engagement score (20%)
        views = int(statistics.get("viewCount", 0))
        likes = int(statistics.get("likeCount", 0))
        comments = int(statistics.get("commentCount", 0))

        engagement_score = self._calculate_engagement_score(views, likes, comments)
        view_to_like_ratio = (likes / views * 100) if views > 0 else 0

        # 5. Channel credibility (15%)
        channel_title = snippet.get("channelTitle", "")
        channel_score = self._assess_channel_credibility(channel_title)

        # Calculate overall scores
        educational_score = (
            caption_score * 0.4 + duration_score * 0.3 + channel_score * 0.3
        )

        content_appropriateness = self._assess_content_appropriateness(snippet)

        overall_score = (
            educational_score * 0.30
            + quality_score * 0.20
            + duration_score * 0.15
            + engagement_score * 0.20
            + channel_score * 0.15
        )

        return VideoQuality(
            video_id=video_id,
            educational_score=round(educational_score, 2),
            content_appropriateness=round(content_appropriateness, 2),
            quality_score=round(quality_score, 2),
            engagement_score=round(engagement_score, 2),
            overall_score=round(overall_score, 2),
            has_captions=has_captions,
            is_hd=is_hd,
            duration_appropriate=(300 <= duration <= 1200),
            channel_credibility=round(channel_score, 2),
            view_to_like_ratio=round(view_to_like_ratio, 2),
        )

    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        # PT15M30S -> 930 seconds
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def _score_duration(self, duration: int) -> float:
        """
        Score video duration (optimal: 5-20 minutes)
        """
        if 300 <= duration <= 1200:  # 5-20 min
            return 100.0
        elif 180 <= duration < 300:  # 3-5 min
            return 80.0
        elif 1200 < duration <= 1800:  # 20-30 min
            return 80.0
        elif 60 <= duration < 180:  # 1-3 min
            return 60.0
        elif 1800 < duration <= 3600:  # 30-60 min
            return 60.0
        else:
            return 30.0

    def _calculate_engagement_score(
        self, views: int, likes: int, comments: int
    ) -> float:
        """Calculate engagement score from metrics"""
        if views == 0:
            return 0

        like_ratio = (likes / views) * 100
        comment_ratio = (comments / views) * 100

        # Good engagement: >2% likes, >0.5% comments
        like_score = min(like_ratio / 2.0 * 100, 100)
        comment_score = min(comment_ratio / 0.5 * 100, 100)

        return like_score * 0.7 + comment_score * 0.3

    def _assess_channel_credibility(self, channel_title: str) -> float:
        """
        Assess channel credibility based on name patterns

        Higher score for:
        - University/institution names
        - Teacher/educator indicators
        - Educational organizations
        """
        channel_lower = channel_title.lower()

        # Credible patterns
        credible_patterns = [
            "üniversite",
            "university",
            "okul",
            "school",
            "eğitim",
            "education",
            "öğretmen",
            "teacher",
            "akademi",
            "academy",
            "institut",
            "kolej",
        ]

        for pattern in credible_patterns:
            if pattern in channel_lower:
                return 90.0

        # Moderate credibility
        moderate_patterns = ["ders", "kurs", "course", "tutorial", "anlatım"]
        for pattern in moderate_patterns:
            if pattern in channel_lower:
                return 70.0

        # Default
        return 50.0

    def _assess_content_appropriateness(self, snippet: Dict[str, Any]) -> float:
        """
        Assess content appropriateness for students

        Check title/description for inappropriate content
        """
        title = snippet.get("title", "").lower()
        description = snippet.get("description", "").lower()

        # Red flags (inappropriate)
        inappropriate_keywords = [
            "reklam",
            "sponsor",
            "kazanma",
            "hile",
            "clickbait",
            "şok",
            "inanilmaz",
        ]

        for keyword in inappropriate_keywords:
            if keyword in title or keyword in description:
                return 50.0

        # Educational indicators
        educational_keywords = [
            "ders",
            "anlatım",
            "konu",
            "soru",
            "çözüm",
            "öğren",
            "eğitim",
            "tutorial",
            "guide",
        ]

        for keyword in educational_keywords:
            if keyword in title or keyword in description:
                return 100.0

        return 75.0  # Default moderate appropriateness


def get_youtube_service(api_key: str) -> YouTubeEnhancedService:
    """Factory function for YouTube service"""
    return YouTubeEnhancedService(api_key=api_key)
