# -*- coding: utf-8 -*-
"""
Elasticsearch Client
Manages Elasticsearch connections and operations for search functionality
"""

import logging
from typing import Any, Dict, List, Optional
from elasticsearch import AsyncElasticsearch, NotFoundError
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Elasticsearch search result"""

    hits: List[Dict[str, Any]]
    total: int
    took: int
    max_score: Optional[float] = None


@dataclass
class IndexStats:
    """Elasticsearch index statistics"""

    doc_count: int
    size_in_bytes: int
    name: str


class ElasticsearchClient:
    """
    Elasticsearch client for managing search operations
    """

    def __init__(
        self,
        hosts: List[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_certs: bool = True,
    ):
        """
        Initialize Elasticsearch client

        Args:
            hosts: List of Elasticsearch hosts
            username: Authentication username
            password: Authentication password
            verify_certs: Whether to verify SSL certificates
        """
        self.hosts = hosts or ["http://localhost:9200"]
        self.username = username
        self.password = password
        self.verify_certs = verify_certs
        self._client: Optional[AsyncElasticsearch] = None

    async def connect(self) -> None:
        """Establish connection to Elasticsearch"""
        try:
            if self.username and self.password:
                self._client = AsyncElasticsearch(
                    self.hosts,
                    basic_auth=(self.username, self.password),
                    verify_certs=self.verify_certs,
                )
            else:
                self._client = AsyncElasticsearch(
                    self.hosts,
                    verify_certs=self.verify_certs,
                )

            # Test connection
            await self._client.info()
            logger.info(f"Connected to Elasticsearch: {self.hosts}")

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Elasticsearch connection"""
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Elasticsearch")

    async def create_index(
        self,
        index_name: str,
        mappings: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create an index with optional mappings and settings"""
        try:
            body = {}
            if mappings:
                body["mappings"] = mappings
            if settings:
                body["settings"] = settings

            await self._client.indices.create(index=index_name, body=body)
            logger.info(f"Created index: {index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False

    async def index_document(
        self,
        index_name: str,
        document: Dict[str, Any],
        doc_id: Optional[str] = None,
    ) -> bool:
        """Index a document"""
        try:
            await self._client.index(
                index=index_name,
                id=doc_id,
                document=document,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return False

    async def search(
        self,
        index_name: str,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0,
    ) -> SearchResult:
        """Search documents"""
        try:
            response = await self._client.search(
                index=index_name,
                query=query,
                size=size,
                from_=from_,
            )

            return SearchResult(
                hits=[hit["_source"] for hit in response["hits"]["hits"]],
                total=response["hits"]["total"]["value"],
                took=response["took"],
                max_score=response["hits"].get("max_score"),
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return SearchResult(hits=[], total=0, took=0)

    async def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        try:
            await self._client.indices.delete(index=index_name)
            logger.info(f"Deleted index: {index_name}")
            return True

        except NotFoundError:
            logger.warning(f"Index not found: {index_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return False

    async def get_index_stats(self, index_name: str) -> Optional[IndexStats]:
        """Get index statistics"""
        try:
            stats = await self._client.indices.stats(index=index_name)
            index_stats = stats["indices"][index_name]

            return IndexStats(
                doc_count=index_stats["total"]["docs"]["count"],
                size_in_bytes=index_stats["total"]["store"]["size_in_bytes"],
                name=index_name,
            )

        except Exception as e:
            logger.error(f"Failed to get stats for {index_name}: {e}")
            return None

    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._client is not None


# Singleton instance
_elasticsearch_client: Optional[ElasticsearchClient] = None


def get_elasticsearch_client() -> ElasticsearchClient:
    """Get global Elasticsearch client instance"""
    global _elasticsearch_client

    if _elasticsearch_client is None:
        _elasticsearch_client = ElasticsearchClient()

    return _elasticsearch_client


# Export classes and functions
__all__ = [
    "ElasticsearchClient",
    "SearchResult",
    "IndexStats",
    "get_elasticsearch_client",
]
