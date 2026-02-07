"""
Task 98.1: Khan Academy API Client
OAuth integration and content fetching for Khan Academy Turkish content
"""

import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import secrets

logger = logging.getLogger(__name__)


class KhanContentType(str, Enum):
    """Khan Academy content types"""

    VIDEO = "video"
    EXERCISE = "exercise"
    ARTICLE = "article"
    PROJECT = "project"


class KhanSubject(str, Enum):
    """Khan Academy subjects (Turkish available)"""

    MATH = "math"
    SCIENCE = "science"
    COMPUTING = "computing"
    ECONOMICS = "economics"
    ARTS_HUMANITIES = "arts-humanities"


class KhanContentMetadata(BaseModel):
    """Khan Academy content metadata"""

    content_id: str
    title: str
    description: Optional[str] = None
    content_type: KhanContentType
    subject: KhanSubject
    topic: Optional[str] = None

    # Video specific
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None

    # Exercise specific
    exercise_url: Optional[str] = None
    problem_count: Optional[int] = None

    # Language
    language: str = "tr"  # Turkish
    has_turkish: bool = True

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    difficulty_level: Optional[str] = None  # beginner, intermediate, advanced


class KhanUserProgress(BaseModel):
    """Khan Academy user progress"""

    user_id: str
    content_id: str
    content_type: KhanContentType

    # Progress tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None

    # Video progress
    video_seconds_watched: Optional[int] = None
    video_completed: bool = False

    # Exercise progress
    problems_attempted: int = 0
    problems_correct: int = 0
    proficiency_level: Optional[str] = None  # practicing, mastered, etc.

    # Points and energy
    energy_points: int = 0
    badges_earned: List[str] = Field(default_factory=list)


class KhanCertificate(BaseModel):
    """Khan Academy certificate/badge"""

    certificate_id: str
    user_id: str
    badge_name: str
    badge_category: str  # mastery, challenge, etc.
    description: str
    icon_url: str
    earned_at: datetime
    verification_url: Optional[str] = None


class KhanAcademyClient:
    """
    Task 98.1: Khan Academy API Client

    OAuth 2.0 integration with Khan Academy API
    - OAuth authentication flow
    - Turkish content filtering
    - Progress synchronization
    - Certificate retrieval
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: str = "https://www.khanacademy.org/api/v1",
        timeout: int = 30,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.timeout = timeout

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        self.client = httpx.AsyncClient(timeout=timeout, headers=self._get_headers())

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Kiro-Platform/1.0",
        }

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    # ============================================
    # OAuth 2.0 Authentication
    # ============================================

    def get_authorization_url(
        self, redirect_uri: str, state: Optional[str] = None
    ) -> str:
        """
        Task 98.1: Get OAuth authorization URL

        Step 1 of OAuth flow: Redirect user to Khan Academy login
        """
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "user:read progress:read badges:read",
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"https://www.khanacademy.org/api/auth2/authorize?{query_string}"

        logger.info("[KHAN OAUTH] Generated authorization URL")
        return auth_url

    async def exchange_code_for_token(
        self, authorization_code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Task 98.1: Exchange authorization code for access token

        Step 2 of OAuth flow: Exchange code for tokens
        """
        token_url = "https://www.khanacademy.org/api/auth2/token"

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = await self.client.post(token_url, data=data)
            response.raise_for_status()

            token_data = response.json()

            # Store tokens
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data.get("refresh_token")

            # Calculate expiration
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            # Update headers
            self.client.headers.update({"Authorization": f"Bearer {self.access_token}"})

            logger.info("[KHAN OAUTH] Successfully obtained access token")

            return {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.token_expires_at.isoformat(),
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"[KHAN OAUTH] Token exchange failed: {e.response.text}")
            raise Exception(f"OAuth token exchange failed: {e.response.status_code}")

    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token
        """
        if not self.refresh_token:
            raise Exception("No refresh token available")

        token_url = "https://www.khanacademy.org/api/auth2/token"

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = await self.client.post(token_url, data=data)
            response.raise_for_status()

            token_data = response.json()

            self.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]

            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            self.client.headers.update({"Authorization": f"Bearer {self.access_token}"})

            logger.info("[KHAN OAUTH] Access token refreshed")

            return {
                "access_token": self.access_token,
                "expires_at": self.token_expires_at.isoformat(),
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"[KHAN OAUTH] Token refresh failed: {e.response.text}")
            raise Exception(f"Token refresh failed: {e.response.status_code}")

    async def _ensure_valid_token(self):
        """Ensure access token is valid, refresh if needed"""
        if not self.access_token:
            raise Exception("Not authenticated. Please complete OAuth flow first.")

        # Check if token is expired (with 5 min buffer)
        if self.token_expires_at:
            buffer = timedelta(minutes=5)
            if datetime.now() + buffer >= self.token_expires_at:
                logger.info("[KHAN OAUTH] Token expiring soon, refreshing...")
                await self.refresh_access_token()

    # ============================================
    # Task 98.2: Turkish Content Fetching
    # ============================================

    async def get_turkish_content(
        self,
        subject: Optional[KhanSubject] = None,
        content_type: Optional[KhanContentType] = None,
        topic: Optional[str] = None,
        limit: int = 50,
    ) -> List[KhanContentMetadata]:
        """
        Task 98.2: Fetch Turkish content from Khan Academy

        Filters content by language='tr' and specified criteria
        """
        await self._ensure_valid_token()

        params = {"lang": "tr", "limit": limit}  # Turkish only

        if subject:
            params["subject"] = subject.value

        if content_type:
            params["kind"] = content_type.value

        if topic:
            params["topic"] = topic

        try:
            response = await self.client.get(
                f"{self.base_url}/topic-tree", params=params
            )
            response.raise_for_status()

            data = response.json()

            # Parse content items
            content_list = []
            for item in data.get("children", []):
                try:
                    content = self._parse_content_item(item)
                    if content and content.has_turkish:
                        content_list.append(content)
                except Exception as e:
                    logger.warning(f"Failed to parse content item: {e}")
                    continue

            logger.info(
                f"[KHAN CONTENT] Fetched {len(content_list)} Turkish content items"
            )
            return content_list

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch Turkish content: {e.response.text}")
            raise

    def _parse_content_item(
        self, item: Dict[str, Any]
    ) -> Optional[KhanContentMetadata]:
        """Parse Khan Academy content item"""

        # Determine content type
        kind = item.get("kind", "").lower()
        if kind == "video":
            content_type = KhanContentType.VIDEO
        elif kind == "exercise":
            content_type = KhanContentType.EXERCISE
        elif kind == "article":
            content_type = KhanContentType.ARTICLE
        else:
            return None

        # Check if Turkish is available
        has_turkish = "tr" in item.get("translated_languages", [])
        if not has_turkish:
            return None

        # Parse timestamps
        created_at = None
        if item.get("date_added"):
            try:
                created_at = datetime.fromisoformat(item["date_added"])
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse date_added: {e}")
                pass

        return KhanContentMetadata(
            content_id=item["id"],
            title=item.get("translated_title", item.get("title", "")),
            description=item.get("translated_description", item.get("description")),
            content_type=content_type,
            subject=KhanSubject(item.get("subject", "math")),
            topic=item.get("topic_slug"),
            video_url=item.get("download_urls", {}).get("mp4")
            if kind == "video"
            else None,
            duration_seconds=item.get("duration") if kind == "video" else None,
            thumbnail_url=item.get("image_url"),
            exercise_url=item.get("url") if kind == "exercise" else None,
            problem_count=item.get("total_problems") if kind == "exercise" else None,
            language="tr",
            has_turkish=True,
            created_at=created_at,
            difficulty_level=item.get("difficulty"),
        )

    # ============================================
    # Task 98.3: Progress Synchronization
    # ============================================

    async def get_user_progress(self, khan_user_id: str) -> List[KhanUserProgress]:
        """
        Task 98.3: Get user's progress from Khan Academy

        Fetches all progress data for bidirectional sync
        """
        await self._ensure_valid_token()

        try:
            response = await self.client.get(
                f"{self.base_url}/user/{khan_user_id}/progress"
            )
            response.raise_for_status()

            data = response.json()

            progress_list = []
            for item in data.get("progress", []):
                try:
                    progress = self._parse_progress_item(khan_user_id, item)
                    progress_list.append(progress)
                except Exception as e:
                    logger.warning(f"Failed to parse progress item: {e}")
                    continue

            logger.info(f"[KHAN PROGRESS] Fetched {len(progress_list)} progress items")
            return progress_list

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch user progress: {e.response.text}")
            raise

    def _parse_progress_item(
        self, user_id: str, item: Dict[str, Any]
    ) -> KhanUserProgress:
        """Parse Khan Academy progress item"""

        content_type = KhanContentType(item.get("kind", "video"))

        # Parse timestamps
        started_at = None
        completed_at = None
        last_accessed = None

        if item.get("started"):
            try:
                started_at = datetime.fromisoformat(item["started"])
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse started timestamp: {e}")
                pass

        if item.get("completed"):
            try:
                completed_at = datetime.fromisoformat(item["completed"])
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse completed timestamp: {e}")
                pass

        if item.get("last_done"):
            try:
                last_accessed = datetime.fromisoformat(item["last_done"])
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse last_done timestamp: {e}")
                pass

        return KhanUserProgress(
            user_id=user_id,
            content_id=item["id"],
            content_type=content_type,
            started_at=started_at,
            completed_at=completed_at,
            last_accessed=last_accessed,
            video_seconds_watched=item.get("seconds_watched", 0),
            video_completed=item.get("completed", False),
            problems_attempted=item.get("total_done", 0),
            problems_correct=item.get("total_correct", 0),
            proficiency_level=item.get("proficiency"),
            energy_points=item.get("points_earned", 0),
            badges_earned=item.get("badges", []),
        )

    async def update_user_progress(
        self, khan_user_id: str, content_id: str, progress_data: Dict[str, Any]
    ) -> bool:
        """
        Task 98.3: Update user progress on Khan Academy

        Bidirectional sync: Push local progress to Khan Academy
        """
        await self._ensure_valid_token()

        try:
            response = await self.client.post(
                f"{self.base_url}/user/{khan_user_id}/progress/{content_id}",
                json=progress_data,
            )
            response.raise_for_status()

            logger.info(f"[KHAN PROGRESS] Updated progress for content {content_id}")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to update progress: {e.response.text}")
            return False

    # ============================================
    # Task 98.4: Certificate/Badge Integration
    # ============================================

    async def get_user_badges(self, khan_user_id: str) -> List[KhanCertificate]:
        """
        Task 98.4: Get user's earned badges/certificates
        """
        await self._ensure_valid_token()

        try:
            response = await self.client.get(
                f"{self.base_url}/user/{khan_user_id}/badges"
            )
            response.raise_for_status()

            data = response.json()

            certificates = []
            for badge in data.get("badges", []):
                try:
                    cert = self._parse_badge(khan_user_id, badge)
                    certificates.append(cert)
                except Exception as e:
                    logger.warning(f"Failed to parse badge: {e}")
                    continue

            logger.info(f"[KHAN BADGES] Fetched {len(certificates)} badges")
            return certificates

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch badges: {e.response.text}")
            raise

    def _parse_badge(self, user_id: str, badge: Dict[str, Any]) -> KhanCertificate:
        """Parse Khan Academy badge"""

        earned_at = datetime.now()
        if badge.get("date_earned"):
            try:
                earned_at = datetime.fromisoformat(badge["date_earned"])
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse date_earned: {e}")
                pass

        # Generate verification URL
        badge_slug = badge.get("slug", badge["name"].lower().replace(" ", "-"))
        verification_url = (
            f"https://www.khanacademy.org/profile/{user_id}/badges/{badge_slug}"
        )

        return KhanCertificate(
            certificate_id=badge["badge_name"],
            user_id=user_id,
            badge_name=badge.get("translated_name", badge["name"]),
            badge_category=badge.get("badge_category", "mastery"),
            description=badge.get(
                "translated_description", badge.get("description", "")
            ),
            icon_url=badge.get("icon_src", ""),
            earned_at=earned_at,
            verification_url=verification_url,
        )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Mock Khan Academy client for development
class MockKhanAcademyClient(KhanAcademyClient):
    """Development mock for Khan Academy API"""

    def __init__(self):
        super().__init__(client_id="mock_id", client_secret="mock_secret")
        self.access_token = "mock_access_token"
        self.token_expires_at = datetime.now() + timedelta(hours=24)

    async def get_turkish_content(
        self,
        subject: Optional[KhanSubject] = None,
        content_type: Optional[KhanContentType] = None,
        topic: Optional[str] = None,
        limit: int = 50,
    ) -> List[KhanContentMetadata]:
        """Mock Turkish content"""

        mock_content = [
            KhanContentMetadata(
                content_id=f"khan_mock_{i}",
                title=f"Matematik Dersi {i+1} - Türkçe",
                description="Khan Academy Türkçe matematik dersi",
                content_type=KhanContentType.VIDEO,
                subject=subject or KhanSubject.MATH,
                topic="algebra",
                video_url=f"https://cdn.khanacademy.org/videos/mock_{i}.mp4",
                duration_seconds=600 + i * 60,
                thumbnail_url=f"https://cdn.khanacademy.org/thumbnails/mock_{i}.jpg",
                language="tr",
                has_turkish=True,
                difficulty_level="intermediate",
            )
            for i in range(min(limit, 10))
        ]

        logger.info(f"[MOCK KHAN] Generated {len(mock_content)} mock content items")
        return mock_content

    async def get_user_progress(self, khan_user_id: str) -> List[KhanUserProgress]:
        """Mock user progress"""

        mock_progress = [
            KhanUserProgress(
                user_id=khan_user_id,
                content_id=f"khan_mock_{i}",
                content_type=KhanContentType.VIDEO,
                started_at=datetime.now() - timedelta(days=i),
                last_accessed=datetime.now() - timedelta(hours=i),
                video_seconds_watched=300 + i * 50,
                video_completed=i % 2 == 0,
                energy_points=100 + i * 10,
            )
            for i in range(5)
        ]

        return mock_progress

    async def get_user_badges(self, khan_user_id: str) -> List[KhanCertificate]:
        """Mock badges"""

        mock_badges = [
            KhanCertificate(
                certificate_id=f"badge_{i}",
                user_id=khan_user_id,
                badge_name=f"Matematik Ustası {i+1}",
                badge_category="mastery",
                description="Matematik konusunda ustalık kazandınız!",
                icon_url=f"https://cdn.khanacademy.org/badges/badge_{i}.png",
                earned_at=datetime.now() - timedelta(days=i * 7),
                verification_url=f"https://www.khanacademy.org/profile/{khan_user_id}/badges/math-master-{i}",
            )
            for i in range(3)
        ]

        return mock_badges


def get_khan_client(use_mock: bool = False) -> KhanAcademyClient:
    """Khan Academy client factory"""

    if use_mock:
        return MockKhanAcademyClient()

    import os

    client_id = os.getenv("KHAN_ACADEMY_CLIENT_ID")
    client_secret = os.getenv("KHAN_ACADEMY_CLIENT_SECRET")

    if not client_id or not client_secret:
        logger.warning("Khan Academy credentials not found. Using mock client.")
        return MockKhanAcademyClient()

    return KhanAcademyClient(client_id=client_id, client_secret=client_secret)
