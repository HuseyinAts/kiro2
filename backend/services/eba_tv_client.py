"""
Task 97.1: EBA TV API Client
MEB EBA TV API entegrasyonu - Video katalog çekme

EBA TV (Eğitim Bilişim Ağı - MEB resmi eğitim platformu)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EBAGradeLevel(str, Enum):
    """EBA sınıf seviyesi"""

    ILKOKUL_1 = "ilkokul_1"
    ILKOKUL_2 = "ilkokul_2"
    ILKOKUL_3 = "ilkokul_3"
    ILKOKUL_4 = "ilkokul_4"
    ORTAOKUL_5 = "ortaokul_5"
    ORTAOKUL_6 = "ortaokul_6"
    ORTAOKUL_7 = "ortaokul_7"
    ORTAOKUL_8 = "ortaokul_8"
    LISE_9 = "lise_9"
    LISE_10 = "lise_10"
    LISE_11 = "lise_11"
    LISE_12 = "lise_12"


class EBASubject(str, Enum):
    """EBA ders konuları"""

    MATEMATIK = "matematik"
    TURKCE = "turkce"
    FEN_BILGISI = "fen_bilgisi"
    SOSYAL_BILGILER = "sosyal_bilgiler"
    FIZIK = "fizik"
    KIMYA = "kimya"
    BIYOLOJI = "biyoloji"
    TARIH = "tarih"
    COGRAFYA = "cografya"
    FELSEFE = "felsefe"
    INGILIZCE = "ingilizce"
    ALMANCA = "almanca"
    FRANSIZCA = "fransizca"


class EBAVideoMetadata(BaseModel):
    """EBA video metadata"""

    video_id: str
    title: str
    description: str | None = None
    duration_seconds: int
    thumbnail_url: str | None = None
    video_url: str
    subject: EBASubject
    grade_level: EBAGradeLevel
    topic: str | None = None
    subtopics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    publish_date: datetime | None = None
    view_count: int = 0
    quality: str = "720p"  # 360p, 480p, 720p, 1080p
    has_turkish_subtitle: bool = True  # EBA always Turkish
    curriculum_aligned: bool = True

    # MEB specific fields
    meb_content_id: str | None = None
    kazanim_codes: list[str] = Field(default_factory=list)  # Müfredat kazanım kodları


class EBACatalogFilter(BaseModel):
    """EBA katalog filtreleme parametreleri"""

    subject: EBASubject | None = None
    grade_level: EBAGradeLevel | None = None
    topic: str | None = None
    min_duration: int | None = None  # seconds
    max_duration: int | None = None  # seconds
    search_query: str | None = None
    page: int = 1
    page_size: int = 20


class EBATVClient:
    """
    EBA TV API Client

    Task 97.1: MEB API bağlantısı
    - API authentication
    - Rate limiting (max 100 requests/minute)
    - Error handling ve retry logic
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://eba.gov.tr/api/v1",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Rate limiting: 100 requests/minute
        self.rate_limit_max = 100
        self.rate_limit_window = 60  # seconds
        self.request_timestamps: list[datetime] = []

        self.client = httpx.AsyncClient(timeout=timeout, headers=self._get_headers())

    def _get_headers(self) -> dict[str, str]:
        """API request headers"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Kiro-Platform/1.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def _check_rate_limit(self) -> None:
        """
        Rate limiting kontrolü
        100 requests/minute limit
        """
        now = datetime.now()

        # Remove old timestamps (older than 1 minute)
        self.request_timestamps = [
            ts
            for ts in self.request_timestamps
            if (now - ts).total_seconds() < self.rate_limit_window
        ]

        # Check if limit exceeded
        if len(self.request_timestamps) >= self.rate_limit_max:
            # Wait until oldest request is outside window
            oldest = self.request_timestamps[0]
            wait_seconds = self.rate_limit_window - (now - oldest).total_seconds()

            if wait_seconds > 0:
                logger.warning(
                    f"Rate limit reached. Waiting {wait_seconds:.1f} seconds..."
                )
                await asyncio.sleep(wait_seconds)

        # Add current timestamp
        self.request_timestamps.append(now)

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> dict[str, Any]:
        """
        Make API request with retry logic
        """
        await self._check_rate_limit()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Rate limit hit. Waiting {wait_time}s before retry..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                if e.response.status_code == 401:  # Unauthorized
                    logger.error("API authentication failed. Check API key.", exc_info=True)
                    raise

                if e.response.status_code >= 500:  # Server error
                    if attempt < self.max_retries - 1:
                        wait_time = 2**attempt
                        logger.warning(f"Server error. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    raise

                raise

            except httpx.RequestError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Request failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise

        raise Exception(f"Failed after {self.max_retries} retries")

    async def get_video_catalog(
        self, filters: EBACatalogFilter | None = None
    ) -> list[EBAVideoMetadata]:
        """
        Task 97.2: Video katalog çekme

        EBA'dan video kataloğunu çeker
        """
        if filters is None:
            filters = EBACatalogFilter()

        params = {"page": filters.page, "page_size": filters.page_size}

        if filters.subject:
            params["subject"] = filters.subject.value

        if filters.grade_level:
            params["grade_level"] = filters.grade_level.value

        if filters.topic:
            params["topic"] = filters.topic

        if filters.search_query:
            params["search"] = filters.search_query

        if filters.min_duration:
            params["min_duration"] = filters.min_duration

        if filters.max_duration:
            params["max_duration"] = filters.max_duration

        try:
            response = await self._make_request("GET", "/videos", params=params)

            videos = []
            for video_data in response.get("videos", []):
                try:
                    video = self._parse_video_metadata(video_data)
                    videos.append(video)
                except Exception as e:
                    logger.warning(f"Failed to parse video {video_data.get('id')}: {e}")
                    continue

            logger.info(f"[EBA] Fetched {len(videos)} videos from catalog")
            return videos

        except Exception as e:
            logger.error(f"Failed to fetch video catalog: {e}", exc_info=True)
            raise

    def _parse_video_metadata(self, data: dict[str, Any]) -> EBAVideoMetadata:
        """Parse EBA API response to EBAVideoMetadata"""

        # Parse publish date
        publish_date = None
        if data.get("publish_date"):
            try:
                publish_date = datetime.fromisoformat(data["publish_date"])
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse publish_date: {e}")

        return EBAVideoMetadata(
            video_id=data["id"],
            title=data["title"],
            description=data.get("description"),
            duration_seconds=data.get("duration", 0),
            thumbnail_url=data.get("thumbnail"),
            video_url=data["url"],
            subject=EBASubject(data["subject"]),
            grade_level=EBAGradeLevel(data["grade_level"]),
            topic=data.get("topic"),
            subtopics=data.get("subtopics", []),
            keywords=data.get("keywords", []),
            publish_date=publish_date,
            view_count=data.get("view_count", 0),
            quality=data.get("quality", "720p"),
            has_turkish_subtitle=True,
            curriculum_aligned=data.get("curriculum_aligned", True),
            meb_content_id=data.get("meb_content_id"),
            kazanim_codes=data.get("kazanim_codes", []),
        )

    async def get_video_details(self, video_id: str) -> EBAVideoMetadata | None:
        """
        Belirli bir videonun detaylarını çeker
        """
        try:
            response = await self._make_request("GET", f"/videos/{video_id}")
            return self._parse_video_metadata(response)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Video not found: {video_id}")
                return None
            raise

    async def search_videos(
        self,
        query: str,
        subject: EBASubject | None = None,
        grade_level: EBAGradeLevel | None = None,
        limit: int = 20,
    ) -> list[EBAVideoMetadata]:
        """
        Video arama
        """
        filters = EBACatalogFilter(
            search_query=query,
            subject=subject,
            grade_level=grade_level,
            page_size=limit,
        )

        return await self.get_video_catalog(filters)

    async def get_subjects_taxonomy(self) -> dict[str, list[str]]:
        """
        Task 97.3: Konu bazlı filtreleme

        EBA'dan ders taksonomisini çeker (ders → konular hiyerarşisi)
        """
        try:
            response = await self._make_request("GET", "/taxonomy/subjects")

            # Response format: { "matematik": ["Sayılar", "Geometri", ...], ... }
            taxonomy = {}
            for subject, topics in response.get("subjects", {}).items():
                taxonomy[subject] = topics

            logger.info(f"[EBA] Fetched taxonomy for {len(taxonomy)} subjects")
            return taxonomy

        except Exception as e:
            logger.error(f"Failed to fetch subjects taxonomy: {e}", exc_info=True)
            # Return default taxonomy if API fails
            return self._get_default_taxonomy()

    def _get_default_taxonomy(self) -> dict[str, list[str]]:
        """Fallback taxonomy if API fails"""
        return {
            "matematik": [
                "Sayılar ve İşlemler",
                "Geometri ve Ölçme",
                "Veri İşleme",
                "Cebir",
            ],
            "fizik": [
                "Kuvvet ve Hareket",
                "Enerji",
                "Elektrik",
                "Optik",
                "Dalga ve Titreşim",
            ],
            "kimya": [
                "Maddenin Yapısı",
                "Kimyasal Tepkimeler",
                "Asit ve Bazlar",
                "Organik Kimya",
            ],
            "biyoloji": ["Hücre", "Genetik", "Ekosistem", "İnsan Anatomisi"],
        }

    async def get_curriculum_alignment(
        self, grade_level: EBAGradeLevel, subject: EBASubject
    ) -> dict[str, Any]:
        """
        Müfredat uyumluluğu bilgisi
        Hangi kazanımlar hangi videolarla eşleşiyor
        """
        try:
            params = {"grade_level": grade_level.value, "subject": subject.value}

            response = await self._make_request(
                "GET", "/curriculum/alignment", params=params
            )

            return response

        except Exception as e:
            logger.error(f"Failed to fetch curriculum alignment: {e}", exc_info=True)
            return {}

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Mock EBA API için test client (development)
class MockEBATVClient(EBATVClient):
    """
    Development için mock EBA client
    Gerçek API bağlantısı olmadan test edilebilir
    """

    def __init__(self):
        super().__init__(api_key="mock_key")

    async def get_video_catalog(
        self, filters: EBACatalogFilter | None = None
    ) -> list[EBAVideoMetadata]:
        """Mock video catalog"""

        if filters is None:
            filters = EBACatalogFilter()

        # Generate mock videos
        mock_videos = [
            EBAVideoMetadata(
                video_id=f"eba_mock_{i}",
                title=f"Matematik - Kareköklü Sayılar Dersi {i+1}",
                description="MEB müfredatına uygun kareköklü sayılar konusu anlatımı",
                duration_seconds=900 + i * 60,
                thumbnail_url=f"https://eba.gov.tr/thumbnails/mock_{i}.jpg",
                video_url=f"https://eba.gov.tr/videos/mock_{i}.mp4",
                subject=EBASubject.MATEMATIK,
                grade_level=EBAGradeLevel.ORTAOKUL_8,
                topic="Sayılar ve İşlemler",
                subtopics=["Kareköklü Sayılar", "Karekök Alma"],
                keywords=["karekök", "sayılar", "matematik"],
                publish_date=datetime.now() - timedelta(days=i * 10),
                view_count=1000 + i * 100,
                quality="720p",
                has_turkish_subtitle=True,
                curriculum_aligned=True,
                meb_content_id=f"MEB-MAT-8-{i}",
                kazanim_codes=[f"8.1.{i}.1", f"8.1.{i}.2"],
            )
            for i in range(filters.page_size)
        ]

        # Apply filters
        if filters.subject:
            mock_videos = [v for v in mock_videos if v.subject == filters.subject]

        if filters.grade_level:
            mock_videos = [
                v for v in mock_videos if v.grade_level == filters.grade_level
            ]

        logger.info(f"[MOCK EBA] Generated {len(mock_videos)} mock videos")
        return mock_videos

    async def get_subjects_taxonomy(self) -> dict[str, list[str]]:
        """Mock taxonomy"""
        return self._get_default_taxonomy()


# Factory function
def get_eba_client(use_mock: bool = False) -> EBATVClient:
    """
    EBA client factory

    Args:
        use_mock: True for development/testing, False for production
    """
    if use_mock:
        return MockEBATVClient()

    # Production: Load from environment
    import os

    api_key = os.getenv("EBA_API_KEY")

    if not api_key:
        logger.warning("EBA_API_KEY not found. Using mock client.")
        return MockEBATVClient()

    return EBATVClient(api_key=api_key)
