"""
Elasticsearch Client
Manages Elasticsearch connections and operations for search functionality
"""

import logging
from dataclasses import dataclass
from typing import Any

from elasticsearch import AsyncElasticsearch, NotFoundError

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Elasticsearch search result"""

    hits: list[dict[str, Any]]
    total: int
    took: int
    max_score: float | None = None

    @property
    def results(self):
        """Alias for hits — backwards compat"""
        return self.hits


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
        hosts: list[str] | None = None,
        username: str | None = None,
        password: str | None = None,
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
        self._client: AsyncElasticsearch | None = None

    async def _ensure_connected(self) -> None:
        """Lazy-init the AsyncElasticsearch client if not already done"""
        if self._client is None:
            import os

            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            if (
                self.hosts == ["http://localhost:9200"]
                and es_url != "http://localhost:9200"
            ):
                self.hosts = [es_url]
            if self.username and self.password:
                self._client = AsyncElasticsearch(
                    self.hosts,
                    basic_auth=(self.username, self.password),
                    verify_certs=self.verify_certs,
                )
            else:
                self._client = AsyncElasticsearch(self.hosts)

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
        mappings: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> bool:
        """Create an index with optional mappings and settings"""
        await self._ensure_connected()
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
        document: dict[str, Any],
        doc_id: str | None = None,
    ) -> bool:
        """Index a document"""
        await self._ensure_connected()
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
        query: dict[str, Any],
        size: int = 10,
        from_: int = 0,
        source_includes: list[str] | None = None,
    ) -> SearchResult:
        """Search documents.

        `source_includes` verilirse ES YALNIZ o alanları döndürür. Beyaz liste
        bilinçli (kara liste değil): index'e yeni bir hassas alan eklendiğinde
        kara liste sessizce sızdırır, beyaz liste sızdırmaz.
        """
        await self._ensure_connected()
        try:
            response = await self._client.search(
                index=index_name,
                query=query,
                size=size,
                from_=from_,
                source_includes=source_includes,
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
        await self._ensure_connected()
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

    async def get_index_stats(self, index_name: str) -> IndexStats | None:
        """Get index statistics"""
        await self._ensure_connected()
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

    async def turkish_full_text_search(
        self,
        index_name: str,
        query_text: str,
        fields: list | None = None,
        size: int = 10,
        from_: int = 0,
        filters: dict | None = None,
        source_includes: list[str] | None = None,
    ) -> SearchResult:
        """Turkish full-text search with multi-field support.

        `source_includes` verilirse ES YALNIZ o alanları döndürür — bkz.
        `search()`. Varsayılan arama alanlarından `explanation` 27 Tem 2026'da
        ÇIKARILDI: bu depoda explanation'ın içeriği düpedüz "Doğru cevap: A
        (Güven: %76, Kaynak: bayes_2of4_orig)" biçiminde. Aranabilir olması,
        kaynak filtrelense bile bir cevap oracle'ı: canlı ölçümde
        "Doğru cevap: E" sorgusu ilk 10 sonucun 4'ünü E yaptı (beklenen ~2).
        """
        if not self._client:
            import os

            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            self._client = AsyncElasticsearch([es_url])
        try:
            search_fields = fields or [
                "question_text^2",
                "option_a",
                "option_b",
                "option_c",
                "option_d",
                "option_e",
            ]
            must = [
                {
                    "multi_match": {
                        "query": query_text,
                        "fields": search_fields,
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                }
            ]
            filter_clauses = []
            if filters:
                for k, v in filters.items():
                    if v is not None:
                        filter_clauses.append({"term": {k: v}})
            query = (
                {"bool": {"must": must, "filter": filter_clauses}}
                if filter_clauses
                else {"bool": {"must": must}}
            )
            response = await self._client.search(
                index=index_name,
                query=query,
                size=size,
                from_=from_,
                source_includes=source_includes,
            )
            return SearchResult(
                hits=[
                    {"id": h["_id"], **h["_source"]} for h in response["hits"]["hits"]
                ],
                total=response["hits"]["total"]["value"],
                took=response["took"],
                max_score=response["hits"].get("max_score"),
            )
        except Exception as e:
            logger.error(f"Turkish full-text search failed: {e}")
            return SearchResult(hits=[], total=0, took=0)

    async def get_document(self, index_name: str, doc_id: str) -> dict:
        """Get a single document by ID"""
        if not self._client:
            import os

            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            self._client = AsyncElasticsearch([es_url])
        try:
            response = await self._client.get(index=index_name, id=doc_id)
            return response["_source"] if response["found"] else None  # type: ignore[no-any-return]
        except Exception as e:
            logger.error(f"Get document failed: {e}")
            return None

    async def bulk_index(self, index_name: str, documents: list) -> dict:
        """Bulk index a list of documents"""
        if not self._client:
            import os

            es_url = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
            self._client = AsyncElasticsearch([es_url])
        try:
            operations = []
            for doc in documents:
                doc_id = doc.get("id")
                operations.append({"index": {"_index": index_name, "_id": doc_id}})
                operations.append(doc)
            response = await self._client.bulk(operations=operations, refresh=True)
            errors = [i for i in response["items"] if i.get("index", {}).get("error")]
            return {"indexed": len(documents) - len(errors), "errors": len(errors)}
        except Exception as e:
            logger.error(f"Bulk index failed: {e}")
            return {"indexed": 0, "errors": len(documents)}

    async def list_indices(self) -> list[str]:
        """List all user-created indices (skips system indices starting with '.')"""
        await self._ensure_connected()
        try:
            response = await self._client.cat.indices(format="json")
            return [
                idx["index"] for idx in response if not idx["index"].startswith(".")
            ]
        except Exception as e:
            logger.error(f"Failed to list indices: {e}")
            return []

    @property
    def client(self):
        """Expose raw AsyncElasticsearch client"""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._client is not None


# Singleton instance
_elasticsearch_client: ElasticsearchClient | None = None


def get_elasticsearch_client() -> ElasticsearchClient:
    """Get global Elasticsearch client instance"""
    global _elasticsearch_client  # noqa: PLW0603 — modül-tekil istemci, bilinçli

    if _elasticsearch_client is None:
        from core.config import settings

        es_url = settings.elasticsearch_url
        es_user = settings.elasticsearch_user
        es_pass = settings.elasticsearch_password
        _elasticsearch_client = ElasticsearchClient(
            hosts=[es_url],
            username=es_user,
            password=es_pass
        )

    return _elasticsearch_client


# Export classes and functions
__all__ = [
    "ElasticsearchClient",
    "IndexStats",
    "SearchResult",
    "get_elasticsearch_client",
]
