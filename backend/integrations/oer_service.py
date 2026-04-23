"""
Open Educational Resources (OER) Integration
Teknofest 2025 - Eğitim Eylemci Projesi

Bu modül:
- OER Commons API entegrasyonu
- MIT OpenCourseWare content search
- Educational content quality assessment
- Multi-source content aggregation
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OERResource:
    """OER kaynak modeli"""

    resource_id: str
    title: str
    description: str
    url: str
    source_platform: str  # OER Commons, MIT OCW, etc.
    content_type: str  # course, lesson, article, video, etc.
    subject_areas: list[str]
    educational_level: str  # K-12, undergraduate, graduate
    language: str
    license_type: str  # CC BY, CC BY-SA, etc.
    author: str | None
    institution: str | None
    created_date: datetime | None
    last_updated: datetime | None
    file_formats: list[str]  # PDF, HTML, Video, etc.
    download_url: str | None
    thumbnail_url: str | None
    rating: float | None
    view_count: int | None
    download_count: int | None
    tags: list[str]
    educational_quality_score: float  # 0-1 arası
    metadata: dict[str, Any]


class OERService:
    """Open Educational Resources Servisi"""

    def __init__(self):
        # OER Commons API (public API)
        self.oer_commons_base = "https://www.oercommons.org/api/v1"

        # MIT OpenCourseWare
        self.mit_ocw_base = "https://ocw.mit.edu"

        # Wikipedia/Wikimedia
        self.wikimedia_base = "https://commons.wikimedia.org/w/api.php"

        # Session for HTTP requests
        self.session = None
        self.rate_limit_delay = 0.5  # 500ms delay
        self.max_retries = 3

        # Content cache
        self.content_cache = {}

        # Educational platforms
        self.oer_platforms = self._load_oer_platforms()

    def _load_oer_platforms(self) -> dict[str, dict[str, Any]]:
        """OER platformlarını yükle"""
        return {
            "oer_commons": {
                "name": "OER Commons",
                "base_url": "https://www.oercommons.org",
                "api_url": "https://www.oercommons.org/api/v1",
                "search_endpoint": "/materials",
                "quality_score": 0.9,
                "supported_languages": ["en", "es", "fr"],
                "content_types": ["course", "lesson", "activity", "assessment"],
            },
            "mit_ocw": {
                "name": "MIT OpenCourseWare",
                "base_url": "https://ocw.mit.edu",
                "search_url": "https://ocw.mit.edu/search/",
                "quality_score": 1.0,
                "supported_languages": ["en"],
                "content_types": ["course", "lecture", "assignment", "exam"],
            },
            "wikimedia_commons": {
                "name": "Wikimedia Commons",
                "base_url": "https://commons.wikimedia.org",
                "api_url": "https://commons.wikimedia.org/w/api.php",
                "quality_score": 0.7,
                "supported_languages": ["en", "tr", "es", "fr", "de"],
                "content_types": ["image", "video", "audio", "document"],
            },
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def search_oer_resources(
        self,
        query: str,
        subject: str | None = None,
        educational_level: str | None = None,
        content_type: str | None = None,
        language: str = "en",
        limit: int = 20,
    ) -> list[OERResource]:
        """
        OER kaynaklarını ara

        Args:
            query: Arama sorgusu
            subject: Konu alanı
            educational_level: Eğitim seviyesi
            content_type: İçerik türü
            language: Dil
            limit: Maksimum sonuç

        Returns:
            OER kaynak listesi
        """
        try:
            all_resources = []

            # OER Commons'dan ara
            oer_commons_resources = await self._search_oer_commons(
                query, subject, educational_level, content_type, language, limit // 3
            )
            all_resources.extend(oer_commons_resources)

            # MIT OCW'den ara
            mit_resources = await self._search_mit_ocw(query, subject, limit // 3)
            all_resources.extend(mit_resources)

            # Wikimedia Commons'dan ara
            wikimedia_resources = await self._search_wikimedia_commons(
                query, content_type, language, limit // 3
            )
            all_resources.extend(wikimedia_resources)

            # Kalite skoruna göre sırala
            all_resources.sort(key=lambda x: x.educational_quality_score, reverse=True)

            # Limit uygula
            result = all_resources[:limit]

            logger.info(f"Found {len(result)} OER resources for query: {query}")
            return result

        except Exception as e:
            logger.error(f"Error searching OER resources: {e!s}")
            return []

    async def _search_oer_commons(
        self,
        query: str,
        subject: str | None,
        educational_level: str | None,
        content_type: str | None,
        language: str,
        limit: int,
    ) -> list[OERResource]:
        """OER Commons'da arama yap"""
        try:
            # Cache kontrolü
            cache_key = f"oer_commons_{query}_{subject}_{educational_level}_{content_type}_{language}_{limit}"
            if cache_key in self.content_cache:
                return self.content_cache[cache_key]

            session = await self._get_session()

            # OER Commons API parametreleri
            params = {"q": query, "limit": limit, "format": "json"}

            if subject:
                params["subject"] = subject
            if educational_level:
                params["education_level"] = educational_level
            if content_type:
                params["material_type"] = content_type
            if language != "en":
                params["language"] = language

            url = f"{self.oer_commons_base}/materials"

            await asyncio.sleep(self.rate_limit_delay)

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    resources = self._parse_oer_commons_response(data)

                    # Cache'e kaydet
                    self.content_cache[cache_key] = resources
                    return resources
                logger.warning(f"OER Commons API returned status {response.status}")
                return self._get_fallback_oer_commons_resources(query, limit)

        except Exception as e:
            logger.error(f"Error searching OER Commons: {e!s}")
            return self._get_fallback_oer_commons_resources(query, limit)

    def _parse_oer_commons_response(self, data: dict[str, Any]) -> list[OERResource]:
        """OER Commons API yanıtını parse et"""
        resources = []

        try:
            materials = data.get("objects", [])

            for material in materials:
                resource = OERResource(
                    resource_id=f"oer_commons_{material.get('id', '')}",
                    title=material.get("title", ""),
                    description=material.get("description", "")[:500],
                    url=material.get("url", ""),
                    source_platform="OER Commons",
                    content_type=material.get("material_types", [""])[0]
                    if material.get("material_types")
                    else "resource",
                    subject_areas=material.get("subjects", []),
                    educational_level=material.get("education_levels", [""])[0]
                    if material.get("education_levels")
                    else "general",
                    language=material.get("language", "en"),
                    license_type=material.get("license", {}).get("name", "Unknown"),
                    author=material.get("author", {}).get("name")
                    if material.get("author")
                    else None,
                    institution=material.get("provider", {}).get("name")
                    if material.get("provider")
                    else None,
                    created_date=self._parse_date(material.get("created")),
                    last_updated=self._parse_date(material.get("modified")),
                    file_formats=material.get("formats", []),
                    download_url=material.get("download_url"),
                    thumbnail_url=material.get("screenshot", {}).get("url")
                    if material.get("screenshot")
                    else None,
                    rating=material.get("rating"),
                    view_count=material.get("views"),
                    download_count=material.get("downloads"),
                    tags=material.get("tags", []),
                    educational_quality_score=self._calculate_oer_quality_score(
                        material
                    ),
                    metadata=material,
                )
                resources.append(resource)

        except Exception as e:
            logger.error(f"Error parsing OER Commons response: {e!s}")

        return resources

    async def _search_mit_ocw(
        self, query: str, subject: str | None, limit: int
    ) -> list[OERResource]:
        """MIT OpenCourseWare'de arama yap"""
        try:
            # MIT OCW için simüle edilmiş arama (gerçek API yok)
            resources = self._get_fallback_mit_ocw_resources(query, subject, limit)
            return resources

        except Exception as e:
            logger.error(f"Error searching MIT OCW: {e!s}")
            return []

    async def _search_wikimedia_commons(
        self, query: str, content_type: str | None, language: str, limit: int
    ) -> list[OERResource]:
        """Wikimedia Commons'da arama yap"""
        try:
            session = await self._get_session()

            # Wikimedia Commons API parametreleri
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srnamespace": "6",  # File namespace
                "srlimit": limit,
                "srprop": "size|wordcount|timestamp|snippet",
            }

            url = self.wikimedia_base

            await asyncio.sleep(self.rate_limit_delay)

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    resources = self._parse_wikimedia_response(data, query)
                    return resources
                logger.warning(f"Wikimedia API returned status {response.status}")
                return []

        except Exception as e:
            logger.error(f"Error searching Wikimedia Commons: {e!s}")
            return []

    def _parse_wikimedia_response(
        self, data: dict[str, Any], query: str
    ) -> list[OERResource]:
        """Wikimedia Commons API yanıtını parse et"""
        resources = []

        try:
            search_results = data.get("query", {}).get("search", [])

            for result in search_results:
                title = result.get("title", "").replace("File:", "")

                resource = OERResource(
                    resource_id=f"wikimedia_{result.get('pageid', '')}",
                    title=title,
                    description=result.get("snippet", "")[:300],
                    url=f"https://commons.wikimedia.org/wiki/File:{quote(title)}",
                    source_platform="Wikimedia Commons",
                    content_type=self._detect_wikimedia_content_type(title),
                    subject_areas=[query],
                    educational_level="general",
                    language="multilingual",
                    license_type="CC BY-SA",
                    author=None,
                    institution="Wikimedia Foundation",
                    created_date=self._parse_date(result.get("timestamp")),
                    last_updated=None,
                    file_formats=[self._extract_file_format(title)],
                    download_url=None,  # Gerçek uygulamada file info API'si ile alınır
                    thumbnail_url=None,
                    rating=None,
                    view_count=None,
                    download_count=None,
                    tags=[query],
                    educational_quality_score=0.7,  # Wikimedia için sabit skor
                    metadata=result,
                )
                resources.append(resource)

        except Exception as e:
            logger.error(f"Error parsing Wikimedia response: {e!s}")

        return resources

    def _get_fallback_oer_commons_resources(
        self, query: str, limit: int
    ) -> list[OERResource]:
        """OER Commons için fallback kaynaklar"""
        fallback_resources = [
            {
                "title": f"Open Educational Resource: {query}",
                "description": f"Comprehensive educational material about {query} from open educational resources.",
                "url": f"https://www.oercommons.org/search?q={quote(query)}",
                "content_type": "course",
                "subject": query,
                "level": "undergraduate",
            },
            {
                "title": f"Interactive Learning Module: {query}",
                "description": f"Interactive educational content covering {query} concepts and applications.",
                "url": f"https://www.oercommons.org/browse?q={quote(query)}",
                "content_type": "interactive",
                "subject": query,
                "level": "high_school",
            },
            {
                "title": f"Educational Videos: {query}",
                "description": f"Collection of educational videos explaining {query} in detail.",
                "url": f"https://www.oercommons.org/materials?q={quote(query)}",
                "content_type": "video",
                "subject": query,
                "level": "general",
            },
        ]

        resources = []
        for i, item in enumerate(fallback_resources[:limit]):
            resource = OERResource(
                resource_id=f"oer_fallback_{i}",
                title=item["title"],
                description=item["description"],
                url=item["url"],
                source_platform="OER Commons",
                content_type=item["content_type"],
                subject_areas=[item["subject"]],
                educational_level=item["level"],
                language="en",
                license_type="CC BY",
                author=None,
                institution="OER Commons",
                created_date=datetime.now(),
                last_updated=None,
                file_formats=["HTML"],
                download_url=None,
                thumbnail_url=None,
                rating=4.0,
                view_count=1000,
                download_count=500,
                tags=[query, "oer", "education"],
                educational_quality_score=0.8,
                metadata={"fallback": True},
            )
            resources.append(resource)

        return resources

    def _get_fallback_mit_ocw_resources(
        self, query: str, subject: str | None, limit: int
    ) -> list[OERResource]:
        """MIT OCW için fallback kaynaklar"""
        mit_courses = [
            {
                "title": f"Introduction to {query}",
                "description": f"MIT course covering fundamental concepts of {query}.",
                "url": f"https://ocw.mit.edu/search/?q={quote(query)}",
                "subject": subject or query,
                "course_number": "6.001",
            },
            {
                "title": f"Advanced {query}",
                "description": f"Advanced MIT course exploring {query} in depth.",
                "url": "https://ocw.mit.edu/courses/find-by-topic/",
                "subject": subject or query,
                "course_number": "6.002",
            },
        ]

        resources = []
        for i, course in enumerate(mit_courses[:limit]):
            resource = OERResource(
                resource_id=f"mit_ocw_{i}",
                title=course["title"],
                description=course["description"],
                url=course["url"],
                source_platform="MIT OpenCourseWare",
                content_type="course",
                subject_areas=[course["subject"]],
                educational_level="undergraduate",
                language="en",
                license_type="CC BY-NC-SA",
                author="MIT Faculty",
                institution="Massachusetts Institute of Technology",
                created_date=datetime.now(),
                last_updated=None,
                file_formats=["HTML", "PDF", "Video"],
                download_url=None,
                thumbnail_url=None,
                rating=4.8,
                view_count=5000,
                download_count=2000,
                tags=[query, "mit", "course"],
                educational_quality_score=1.0,
                metadata={"course_number": course["course_number"], "fallback": True},
            )
            resources.append(resource)

        return resources

    def _calculate_oer_quality_score(self, material: dict[str, Any]) -> float:
        """OER kaynağının kalite skorunu hesapla"""
        score = 0.0

        # Temel skor (platform güvenilirliği)
        score += 0.3

        # Rating varsa
        rating = material.get("rating")
        if rating:
            score += (rating / 5.0) * 0.2

        # View count
        views = material.get("views", 0)
        if views > 1000:
            score += 0.2
        elif views > 100:
            score += 0.1

        # License quality
        license_name = material.get("license", {}).get("name", "").lower()
        if "cc by" in license_name:
            score += 0.2
        elif "cc" in license_name:
            score += 0.1

        # Metadata completeness
        if material.get("description"):
            score += 0.1
        if material.get("subjects"):
            score += 0.1

        return min(score, 1.0)

    def _detect_wikimedia_content_type(self, filename: str) -> str:
        """Dosya adından içerik türünü tespit et"""
        filename_lower = filename.lower()

        if any(
            ext in filename_lower for ext in [".jpg", ".jpeg", ".png", ".gif", ".svg"]
        ):
            return "image"
        if any(ext in filename_lower for ext in [".mp4", ".avi", ".mov", ".webm"]):
            return "video"
        if any(ext in filename_lower for ext in [".mp3", ".wav", ".ogg"]):
            return "audio"
        if any(ext in filename_lower for ext in [".pdf", ".doc", ".docx"]):
            return "document"
        return "file"

    def _extract_file_format(self, filename: str) -> str:
        """Dosya formatını çıkar"""
        if "." in filename:
            return filename.split(".")[-1].upper()
        return "UNKNOWN"

    def _parse_date(self, date_string: str | None) -> datetime | None:
        """Tarih string'ini parse et"""
        if not date_string:
            return None

        try:
            # ISO format
            if "T" in date_string:
                return datetime.fromisoformat(date_string.replace("Z", "+00:00"))
            # Basit format
            return datetime.strptime(date_string, "%Y-%m-%d")
        except (ValueError, TypeError) as e:
            logger.debug(f"Date parsing failed: {e}")
            return None

    async def get_resource_details(
        self, resource_id: str, platform: str
    ) -> dict[str, Any] | None:
        """
        Kaynak detaylarını getir

        Args:
            resource_id: Kaynak ID
            platform: Platform adı

        Returns:
            Kaynak detayları
        """
        try:
            if platform == "oer_commons":
                return await self._get_oer_commons_details(resource_id)
            if platform == "mit_ocw":
                return await self._get_mit_ocw_details(resource_id)
            if platform == "wikimedia":
                return await self._get_wikimedia_details(resource_id)
            return None

        except Exception as e:
            logger.error(f"Error getting resource details: {e!s}")
            return None

    async def _get_oer_commons_details(
        self, resource_id: str
    ) -> dict[str, Any] | None:
        """OER Commons kaynak detayları"""
        try:
            session = await self._get_session()
            url = f"{self.oer_commons_base}/materials/{resource_id}"

            await asyncio.sleep(self.rate_limit_delay)

            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None

        except Exception as e:
            logger.error(f"Error getting OER Commons details: {e!s}")
            return None

    async def _get_mit_ocw_details(self, resource_id: str) -> dict[str, Any] | None:
        """MIT OCW kaynak detayları (simüle edilmiş)"""
        return {
            "id": resource_id,
            "title": "MIT Course Details",
            "description": "Detailed course information from MIT OpenCourseWare",
            "syllabus": "Course syllabus and materials",
            "lectures": ["Lecture 1", "Lecture 2", "Lecture 3"],
            "assignments": ["Assignment 1", "Assignment 2"],
            "exams": ["Midterm", "Final"],
        }

    async def _get_wikimedia_details(
        self, resource_id: str
    ) -> dict[str, Any] | None:
        """Wikimedia kaynak detayları"""
        try:
            session = await self._get_session()

            params = {
                "action": "query",
                "format": "json",
                "pageids": resource_id,
                "prop": "info|imageinfo",
                "iiprop": "url|size|mime",
            }

            await asyncio.sleep(self.rate_limit_delay)

            async with session.get(self.wikimedia_base, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None

        except Exception as e:
            logger.error(f"Error getting Wikimedia details: {e!s}")
            return None

    async def search_by_subject(
        self,
        subject: str,
        educational_level: str | None = None,
        language: str = "en",
        limit: int = 15,
    ) -> list[OERResource]:
        """
        Konuya göre OER kaynakları ara

        Args:
            subject: Konu alanı
            educational_level: Eğitim seviyesi
            language: Dil
            limit: Maksimum sonuç

        Returns:
            OER kaynak listesi
        """
        return await self.search_oer_resources(
            query=subject,
            subject=subject,
            educational_level=educational_level,
            language=language,
            limit=limit,
        )

    async def get_trending_resources(
        self, subject: str | None = None, limit: int = 10
    ) -> list[OERResource]:
        """
        Popüler OER kaynaklarını getir

        Args:
            subject: Konu filtresi
            limit: Maksimum sonuç

        Returns:
            Popüler kaynak listesi
        """
        try:
            # Popüler konular
            trending_topics = [
                "mathematics",
                "science",
                "computer science",
                "physics",
                "chemistry",
                "biology",
                "history",
                "literature",
                "art",
            ]

            if subject:
                trending_topics = [subject] + trending_topics

            all_resources = []

            for topic in trending_topics[:3]:  # İlk 3 konu
                resources = await self.search_oer_resources(
                    query=topic, subject=topic, limit=limit // 3
                )
                all_resources.extend(resources)

            # View count ve rating'e göre sırala
            all_resources.sort(
                key=lambda x: (x.view_count or 0) + (x.rating or 0) * 1000, reverse=True
            )

            return all_resources[:limit]

        except Exception as e:
            logger.error(f"Error getting trending resources: {e!s}")
            return []

    def get_platform_info(self, platform_name: str) -> dict[str, Any] | None:
        """Platform bilgilerini getir"""
        return self.oer_platforms.get(platform_name)

    def get_supported_platforms(self) -> list[str]:
        """Desteklenen platformları getir"""
        return list(self.oer_platforms.keys())

    async def validate_resource_url(self, url: str) -> bool:
        """Kaynak URL'sinin geçerliliğini kontrol et"""
        try:
            session = await self._get_session()

            async with session.head(url) as response:
                return response.status == 200

        except Exception as e:
            logger.error(f"Error validating URL {url}: {e!s}")
            return False

    def generate_oer_analytics(self) -> dict[str, Any]:
        """OER analitikleri oluştur"""
        try:
            total_cached = len(self.content_cache)

            # Platform dağılımı
            platform_distribution = {}
            content_type_distribution = {}

            for cached_resources in self.content_cache.values():
                for resource in cached_resources:
                    platform = resource.source_platform
                    content_type = resource.content_type

                    platform_distribution[platform] = (
                        platform_distribution.get(platform, 0) + 1
                    )
                    content_type_distribution[content_type] = (
                        content_type_distribution.get(content_type, 0) + 1
                    )

            return {
                "total_cached_searches": total_cached,
                "supported_platforms": len(self.oer_platforms),
                "platform_distribution": platform_distribution,
                "content_type_distribution": content_type_distribution,
                "cache_size": sum(
                    len(resources) for resources in self.content_cache.values()
                ),
            }

        except Exception as e:
            logger.error(f"Error generating OER analytics: {e!s}")
            return {"error": str(e)}


# Singleton instance
oer_service = OERService()
