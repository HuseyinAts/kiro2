"""
Enhanced Wikipedia API Integration with Authentication Support
Supports multiple authentication methods for API access
Teknofest 2025 - Eğitim Eylemci Projesi
"""

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """API authentication methods"""

    NONE = "none"
    BEARER_TOKEN = "bearer"
    QUERY_PARAM = "query"
    HEADER = "header"
    COOKIE = "cookie"


@dataclass
class WikipediaArticle:
    """Wikipedia makale modeli"""

    page_id: int
    title: str
    summary: str
    content: str
    url: str
    categories: list[str]
    images: list[str]
    references: list[str]
    language: str
    last_modified: datetime
    word_count: int
    educational_relevance: float  # 0-1 arası eğitim ilgililik skoru


class WikipediaServiceWithAuth:
    """Enhanced Wikipedia API service with authentication support"""

    def __init__(
        self,
        api_key: str | None = None,
        auth_method: AuthMethod = AuthMethod.NONE,
        custom_base_url: str | None = None,
    ):
        """
        Initialize Wikipedia service with optional authentication

        Args:
            api_key: Optional API key for authentication
            auth_method: Method to use for API authentication
            custom_base_url: Optional custom base URL (for proxy servers)
        """
        self.api_key = api_key or os.getenv("WIKIPEDIA_API_KEY", "")
        self.auth_method = auth_method

        # Use custom base URL if provided (for proxy servers that might require auth)
        if custom_base_url:
            self.base_urls = {
                "tr": f"{custom_base_url}/tr",
                "en": f"{custom_base_url}/en",
            }
            self.api_endpoint = f"{custom_base_url}/{{lang}}/api"
        else:
            # Standard Wikipedia URLs (no auth required)
            self.base_urls = {
                "tr": "https://tr.wikipedia.org/api/rest_v1",
                "en": "https://en.wikipedia.org/api/rest_v1",
            }
            self.api_endpoint = "https://{lang}.wikipedia.org/w/api.php"

    def _prepare_auth_headers(self) -> dict[str, str]:
        """Prepare authentication headers based on auth method"""
        headers = {"User-Agent": "TeknofestEducationBot/1.0"}

        if self.api_key and self.auth_method == AuthMethod.BEARER_TOKEN:
            # Bearer token in Authorization header (JWT style)
            headers["Authorization"] = f"Bearer {self.api_key}"
        elif self.api_key and self.auth_method == AuthMethod.HEADER:
            # API key as custom header
            headers["X-API-Key"] = self.api_key

        return headers

    def _prepare_auth_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Add authentication to query parameters if needed"""
        if self.api_key and self.auth_method == AuthMethod.QUERY_PARAM:
            params["api_key"] = self.api_key
        return params

    def _prepare_auth_cookies(self) -> dict[str, str]:
        """Prepare authentication cookies if needed"""
        cookies = {}
        if self.api_key and self.auth_method == AuthMethod.COOKIE:
            cookies["X-API-KEY"] = self.api_key
        return cookies

    async def search_articles(
        self,
        query: str,
        language: str = "tr",
        limit: int = 10,
        educational_filter: bool = True,
    ) -> list[WikipediaArticle]:
        """
        Search Wikipedia articles with authentication

        Args:
            query: Search query
            language: Language code
            limit: Maximum number of results
            educational_filter: Apply educational filter

        Returns:
            List of articles
        """
        try:
            # API URL
            url = self.api_endpoint.format(lang=language)

            # Base parameters
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": limit * 2,
                "srprop": "snippet|titlesnippet|size|wordcount|timestamp",
            }

            # Add authentication to params if needed
            params = self._prepare_auth_params(params)

            # Prepare headers with authentication
            headers = self._prepare_auth_headers()

            # Prepare cookies if needed
            cookies = self._prepare_auth_cookies()

            # Make API request with authentication
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, headers=headers, cookies=cookies
                ) as response:
                    if response.status == 401:
                        logger.error("Authentication failed - Invalid API key")
                        return []
                    if response.status == 403:
                        logger.error("Authorization failed - Insufficient permissions")
                        return []
                    if response.status != 200:
                        logger.error(
                            f"API request failed with status {response.status}"
                        )
                        return []

                    data = await response.json()

                    # Process results
                    articles = []
                    if "query" in data and "search" in data["query"]:
                        for item in data["query"]["search"]:
                            article = WikipediaArticle(
                                page_id=item.get("pageid", 0),
                                title=item.get("title", ""),
                                summary=item.get("snippet", "")
                                .replace("<span class='searchmatch'>", "")
                                .replace("</span>", ""),
                                content="",  # Will be fetched separately if needed
                                url=f"https://{language}.wikipedia.org/wiki/{item.get('title', '').replace(' ', '_')}",
                                categories=[],
                                images=[],
                                references=[],
                                language=language,
                                last_modified=datetime.now(),
                                word_count=item.get("wordcount", 0),
                                educational_relevance=self._calculate_educational_relevance(
                                    item
                                ),
                            )
                            articles.append(article)

                    # Apply educational filter
                    if educational_filter:
                        articles = [
                            a for a in articles if a.educational_relevance > 0.5
                        ]

                    # Sort and limit
                    articles.sort(key=lambda a: a.educational_relevance, reverse=True)

                    logger.info(
                        f"Found {len(articles)} Wikipedia articles for '{query}'"
                    )
                    return articles[:limit]

        except aiohttp.ClientError as e:
            logger.error(f"Network error during Wikipedia search: {e!s}")
            return []
        except Exception as e:
            logger.error(f"Wikipedia search error: {e!s}")
            return []

    async def get_article(
        self, title: str, language: str = "tr"
    ) -> WikipediaArticle | None:
        """
        Get full article content with authentication

        Args:
            title: Article title
            language: Language code

        Returns:
            WikipediaArticle or None
        """
        try:
            url = self.api_endpoint.format(lang=language)

            params = {
                "action": "parse",
                "format": "json",
                "page": title,
                "prop": "text|categories|images|externallinks|sections",
            }

            # Add authentication
            params = self._prepare_auth_params(params)
            headers = self._prepare_auth_headers()
            cookies = self._prepare_auth_cookies()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, headers=headers, cookies=cookies
                ) as response:
                    if response.status == 401:
                        logger.error("Authentication failed when fetching article")
                        return None
                    if response.status != 200:
                        logger.error(f"Failed to fetch article: {response.status}")
                        return None

                    data = await response.json()

                    if "parse" in data:
                        parse_data = data["parse"]

                        # Extract content
                        content = parse_data.get("text", {}).get("*", "")

                        # Extract categories
                        categories = [
                            cat["*"] for cat in parse_data.get("categories", [])
                        ]

                        # Extract images
                        images = parse_data.get("images", [])

                        # Extract references/external links
                        references = parse_data.get("externallinks", [])

                        # Calculate word count from content
                        text_only = re.sub(r"<[^>]+>", "", content)
                        word_count = len(text_only.split())

                        # Create article object
                        article = WikipediaArticle(
                            page_id=parse_data.get("pageid", 0),
                            title=parse_data.get("title", title),
                            summary=text_only[:500] + "..."
                            if len(text_only) > 500
                            else text_only,
                            content=content,
                            url=f"https://{language}.wikipedia.org/wiki/{title.replace(' ', '_')}",
                            categories=categories,
                            images=images,
                            references=references,
                            language=language,
                            last_modified=datetime.now(),
                            word_count=word_count,
                            educational_relevance=self._calculate_content_relevance(
                                content, categories
                            ),
                        )

                        return article

                    return None

        except Exception as e:
            logger.error(f"Error fetching article '{title}': {e!s}")
            return None

    def _calculate_educational_relevance(self, search_result: dict[str, Any]) -> float:
        """Calculate educational relevance score for search results"""
        score = 0.5  # Base score

        # Check title for educational keywords
        title = search_result.get("title", "").lower()
        educational_keywords = [
            "matematik",
            "fizik",
            "kimya",
            "biyoloji",
            "tarih",
            "coğrafya",
            "edebiyat",
            "felsefe",
            "bilim",
            "teori",
            "formül",
            "denklem",
            "mathematics",
            "physics",
            "chemistry",
            "biology",
            "history",
            "geography",
            "literature",
            "philosophy",
            "science",
            "theory",
        ]

        for keyword in educational_keywords:
            if keyword in title:
                score += 0.1

        # Word count factor
        word_count = search_result.get("wordcount", 0)
        if word_count > 1000:
            score += 0.1
        if word_count > 5000:
            score += 0.1

        # Limit score to 1.0
        return min(score, 1.0)

    def _calculate_content_relevance(
        self, content: str, categories: list[str]
    ) -> float:
        """Calculate educational relevance from content and categories"""
        score = 0.5

        # Check categories
        educational_categories = [
            "Education",
            "Science",
            "Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "History",
            "Geography",
            "Literature",
            "Philosophy",
            "Eğitim",
            "Bilim",
            "Matematik",
            "Fizik",
            "Kimya",
            "Biyoloji",
            "Tarih",
            "Coğrafya",
            "Edebiyat",
            "Felsefe",
        ]

        for category in categories:
            for edu_cat in educational_categories:
                if edu_cat.lower() in category.lower():
                    score += 0.15
                    break

        # Content length and structure
        if len(content) > 5000:
            score += 0.1
        if len(content) > 10000:
            score += 0.1

        # Check for educational content patterns
        if "<math>" in content or "formula" in content.lower():
            score += 0.1
        if "references" in content.lower() or "kaynakça" in content.lower():
            score += 0.05

        return min(score, 1.0)

    async def get_article_sections(
        self, title: str, language: str = "tr"
    ) -> list[dict[str, Any]]:
        """Get article sections with authentication"""
        try:
            url = self.api_endpoint.format(lang=language)

            params = {
                "action": "parse",
                "format": "json",
                "page": title,
                "prop": "sections",
            }

            # Add authentication
            params = self._prepare_auth_params(params)
            headers = self._prepare_auth_headers()
            cookies = self._prepare_auth_cookies()

            async with aiohttp.ClientSession() as session, session.get(
                url, params=params, headers=headers, cookies=cookies
            ) as response:
                if response.status != 200:
                    return []

                data = await response.json()

                if "parse" in data and "sections" in data["parse"]:
                    return data["parse"]["sections"]

                return []

        except Exception as e:
            logger.error(f"Error fetching sections: {e!s}")
            return []


# Create a singleton instance for backward compatibility
wikipedia_service_with_auth = WikipediaServiceWithAuth()


# Export the enhanced service
__all__ = [
    "AuthMethod",
    "WikipediaArticle",
    "WikipediaServiceWithAuth",
    "wikipedia_service_with_auth",
]
