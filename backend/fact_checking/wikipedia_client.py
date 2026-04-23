"""
Wikipedia API Client

Bu modül, Türkçe Wikipedia'dan bilgi doğrulaması yapar.

Features:
- tr.wikipedia.org API entegrasyonu
- Rate limiting (10 req/sec)
- Content caching (TTL: 1 saat)

Requirements: REQ-4.3
"""

import asyncio
import hashlib
import logging
import time
from typing import Any

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WikipediaVerificationResult(BaseModel):
    """Wikipedia doğrulama sonucu"""
    found: bool = Field(description="Bilgi bulundu mu")
    confidence: float = Field(ge=0.0, le=1.0, description="Güven skoru")
    status: str = Field(description="true/false/partially_true/unverified")
    evidence: str | None = Field(default=None, description="Kanıt metni")
    page_title: str | None = Field(default=None, description="Wikipedia sayfa başlığı")
    page_url: str | None = Field(default=None, description="Wikipedia sayfa URL'i")


class WikipediaClient:
    """
    Türkçe Wikipedia API client'ı.

    Rate limiting ve caching ile bilgi doğrulaması yapar.
    """

    API_URL = "https://tr.wikipedia.org/w/api.php"
    RATE_LIMIT = 10  # requests per second
    CACHE_TTL = 3600  # 1 hour

    def __init__(
        self,
        rate_limit: int = 10,
        cache_enabled: bool = True,
    ):
        """
        Args:
            rate_limit: Saniye başına istek limiti
            cache_enabled: Cache aktif mi
        """
        self.rate_limit = rate_limit
        self.cache_enabled = cache_enabled

        self._cache: dict[str, dict[str, Any]] = {}
        self._last_request_time = 0.0
        self._request_count = 0
        self._embedding_model = None

    async def verify_claim(self, claim: str) -> WikipediaVerificationResult:
        """
        Bir iddiayı Wikipedia'da doğrula.

        Args:
            claim: Doğrulanacak iddia

        Returns:
            WikipediaVerificationResult: Doğrulama sonucu
        """
        # Rate limiting
        await self._rate_limit()

        try:
            # Önce arama yap
            search_results = await self._search(claim)

            if not search_results:
                return WikipediaVerificationResult(
                    found=False,
                    confidence=0.0,
                    status="unverified",
                    evidence=None,
                )

            # İlk sonucun içeriğini al
            page_title = search_results[0]["title"]
            content = await self._get_page_content(page_title)

            if not content:
                return WikipediaVerificationResult(
                    found=False,
                    confidence=0.0,
                    status="unverified",
                    evidence=None,
                )

            # İddiayı içerikte doğrula
            verification = self._verify_claim_in_content(claim, content)

            return WikipediaVerificationResult(
                found=True,
                confidence=verification["confidence"],
                status=verification["status"],
                evidence=verification["evidence"],
                page_title=page_title,
                page_url=f"https://tr.wikipedia.org/wiki/{page_title.replace(' ', '_')}",
            )

        except Exception as e:
            logger.error(f"Wikipedia verification error: {e}")
            return WikipediaVerificationResult(
                found=False,
                confidence=0.0,
                status="unverified",
                evidence=None,
            )

    async def _rate_limit(self):
        """Rate limiting uygula"""
        current_time = time.time()

        # Her saniyede rate_limit kadar istek
        if current_time - self._last_request_time >= 1.0:
            self._request_count = 0
            self._last_request_time = current_time

        if self._request_count >= self.rate_limit:
            sleep_time = 1.0 - (current_time - self._last_request_time)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            self._request_count = 0
            self._last_request_time = time.time()

        self._request_count += 1

    async def _search(self, query: str) -> list[dict[str, Any]]:
        """
        Wikipedia'da arama yap.

        Args:
            query: Arama sorgusu

        Returns:
            List[Dict]: Arama sonuçları
        """
        cache_key = f"search_{hashlib.md5(query.encode()).hexdigest()}"

        # Cache kontrol
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["timestamp"] < self.CACHE_TTL:
                return cached["data"]

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 5,
        }

        try:
            async with aiohttp.ClientSession() as session, session.get(
                self.API_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10.0),
            ) as resp:
                if resp.status != 200:
                    return []

                data = await resp.json()
                results = data.get("query", {}).get("search", [])

                # Cache'e kaydet
                if self.cache_enabled:
                    self._cache[cache_key] = {
                        "timestamp": time.time(),
                        "data": results,
                    }

                return results

        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []

    async def _get_page_content(self, title: str) -> str | None:
        """
        Wikipedia sayfa içeriğini al.

        Args:
            title: Sayfa başlığı

        Returns:
            str: Sayfa içeriği
        """
        cache_key = f"page_{hashlib.md5(title.encode()).hexdigest()}"

        # Cache kontrol
        if self.cache_enabled and cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["timestamp"] < self.CACHE_TTL:
                return cached["data"]

        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "format": "json",
            "utf8": 1,
        }

        try:
            async with aiohttp.ClientSession() as session, session.get(
                self.API_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10.0),
            ) as resp:
                if resp.status != 200:
                    return None

                data = await resp.json()
                pages = data.get("query", {}).get("pages", {})

                # İlk sayfanın içeriğini al
                for page_id, page_data in pages.items():
                    if page_id != "-1":
                        content = page_data.get("extract", "")

                        # Cache'e kaydet
                        if self.cache_enabled:
                            self._cache[cache_key] = {
                                "timestamp": time.time(),
                                "data": content,
                            }

                        return content

                return None

        except Exception as e:
            logger.error(f"Wikipedia page content error: {e}")
            return None

    def _verify_claim_in_content(
        self, claim: str, content: str
    ) -> dict[str, Any]:
        """
        İddiayı içerikte doğrula.

        Args:
            claim: Doğrulanacak iddia
            content: Sayfa içeriği

        Returns:
            Dict: Doğrulama sonucu
        """
        claim_lower = claim.lower()
        content_lower = content.lower()

        # Tam eşleşme kontrolü
        if claim_lower in content_lower:
            return {
                "status": "true",
                "confidence": 0.85,
                "evidence": self._extract_evidence(content, claim),
            }

        # Kelime tabanlı eşleşme
        claim_words = set(claim_lower.split())
        content_words = set(content_lower.split())

        # Stop words çıkar
        stop_words = {
            "ve", "veya", "ile", "için", "bu", "şu", "o",
            "bir", "mi", "mı", "mu", "mü", "ne", "nasıl",
            "de", "da", "den", "dan", "dır", "dir",
        }
        claim_words = claim_words - stop_words

        if not claim_words:
            return {
                "status": "unverified",
                "confidence": 0.0,
                "evidence": None,
            }

        # Eşleşen kelime oranı
        matching_words = claim_words & content_words
        match_ratio = len(matching_words) / len(claim_words)

        if match_ratio >= 0.8:
            return {
                "status": "partially_true",
                "confidence": 0.7 * match_ratio,
                "evidence": content[:500],
            }
        if match_ratio >= 0.5:
            return {
                "status": "unverified",
                "confidence": 0.3,
                "evidence": content[:300],
            }
        return {
            "status": "unverified",
            "confidence": 0.0,
            "evidence": None,
        }

    def _extract_evidence(self, content: str, claim: str) -> str:
        """
        İçerikten ilgili kanıtı çıkar.

        Args:
            content: Tam içerik
            claim: İddia

        Returns:
            str: Kanıt parçası
        """
        claim_lower = claim.lower()
        content_lower = content.lower()

        # İddianın geçtiği cümleyi bul
        try:
            index = content_lower.find(claim_lower)
            if index != -1:
                # Önceki ve sonraki 200 karakteri al
                start = max(0, index - 100)
                end = min(len(content), index + len(claim) + 100)
                return "..." + content[start:end] + "..."
        except Exception:
            pass

        # Fallback: İlk 500 karakter
        return content[:500]

    def clear_cache(self):
        """Cache'i temizle"""
        self._cache.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Cache istatistiklerini al"""
        return {
            "entries": len(self._cache),
            "total_size": sum(
                len(str(v.get("data", "")))
                for v in self._cache.values()
            ),
        }
