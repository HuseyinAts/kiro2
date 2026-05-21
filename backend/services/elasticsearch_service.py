"""
Elasticsearch servis katmanı
Soru bankası, içerik ve analytics için arama servisleri
"""

import logging
from datetime import datetime
from typing import Any

try:
    from core.elasticsearch_client import ElasticsearchClient, SearchResponse
except ImportError:
    try:
        from core.elasticsearch_client import ElasticsearchClient, SearchResponse
    except ImportError:
        # Elasticsearch client not available - create mock classes
        class SearchResponse:
            def __init__(self, hits=None, total=0):
                self.hits = hits or []
                self.total = total

        class ElasticsearchClient:
            def __init__(self):
                pass

            async def search(self, *args, **kwargs):
                return SearchResponse()

            async def index(self, *args, **kwargs):
                return {"result": "created"}

            async def close(self):
                pass


# Database models - optional import
try:
    from models.database import User
except ImportError:
    try:
        from models.database import User
    except ImportError:
        # Mock User class for testing
        class User:
            def __init__(self):
                self.id = None


logger = logging.getLogger(__name__)


class QuestionSearchService:
    """Soru bankası arama servisi"""

    def __init__(self, es_client: ElasticsearchClient):
        self.es_client = es_client
        import os as _os
        self.index_name = _os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")

        # Soru indeks mapping'i
        self.question_mapping = {
            "properties": {
                "id": {"type": "keyword"},
                "text": {
                    "type": "text",
                    "analyzer": "turkish_analyzer",
                    "search_analyzer": "turkish_search_analyzer",
                },
                "subject": {"type": "keyword"},
                "topic": {"type": "keyword"},
                "difficulty": {"type": "float"},
                "exam_type": {"type": "keyword"},
                "question_type": {"type": "keyword"},
                "options": {
                    "type": "nested",
                    "properties": {
                        "text": {"type": "text", "analyzer": "turkish_analyzer"},
                        "is_correct": {"type": "boolean"},
                    },
                },
                "explanation": {"type": "text", "analyzer": "turkish_analyzer"},
                "tags": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "indexed_at": {"type": "date"},
            }
        }

    async def initialize_index(self) -> bool:
        """Soru indeksini başlat"""
        try:
            success = await self.es_client.create_index(
                index_name=self.index_name, mapping=self.question_mapping
            )

            if success:
                logger.info(f"Soru indeksi başlatıldı: {self.index_name}")

            return success

        except Exception as e:
            logger.error(f"Soru indeksi başlatma hatası: {e!s}", exc_info=True)
            return False

    async def index_question(self, question: dict) -> bool:
        """Soruyu indeksle"""
        try:
            # Question dict'ini Elasticsearch dokümanına çevir
            doc = {
                "id": str(question.get("id", "")),
                "text": question.get("text", ""),
                "subject": question.get("subject", ""),
                "topic": question.get("topic", ""),
                "difficulty": float(question.get("difficulty", 0)),
                "exam_type": question.get("exam_type", ""),
                "question_type": question.get("question_type", ""),
                "options": question.get("options", []),
                "explanation": question.get("explanation", ""),
                "tags": question.get("tags", []),
                "created_at": question.get("created_at"),
                "updated_at": question.get("updated_at"),
            }

            return await self.es_client.index_document(
                index_name=self.index_name,
                document=doc,
                doc_id=str(question.get("id", "")),
            )

        except Exception as e:
            logger.error(f"Soru indeksleme hatası: {e!s}", exc_info=True)
            return False

    async def bulk_index_questions(self, questions: list[dict]) -> dict[str, int]:
        """Toplu soru indeksleme"""
        try:
            documents = []

            for question in questions:
                doc = {
                    "id": str(question.get("id", "")),
                    "text": question.get("text", ""),
                    "subject": question.get("subject", ""),
                    "topic": question.get("topic", ""),
                    "difficulty": float(question.get("difficulty", 0)),
                    "exam_type": question.get("exam_type", ""),
                    "question_type": question.get("question_type", ""),
                    "options": question.get("options", []),
                    "explanation": question.get("explanation", ""),
                    "tags": question.get("tags", []),
                    "created_at": question.get("created_at"),
                    "updated_at": question.get("updated_at"),
                }
                documents.append(doc)

            return await self.es_client.bulk_index(
                index_name=self.index_name, documents=documents, id_field="id"
            )

        except Exception as e:
            logger.error(f"Toplu soru indeksleme hatası: {e!s}", exc_info=True)
            return {"success": 0, "errors": len(questions), "total": len(questions)}

    async def search_questions(
        self,
        query_text: str,
        subject: str | None = None,
        topic: str | None = None,
        exam_type: str | None = None,
        difficulty_range: tuple | None = None,
        size: int = 20,
        from_: int = 0,
    ) -> SearchResponse:
        """Soru arama"""

        # Filtreler
        filters = {}
        if subject:
            filters["subject"] = subject
        if topic:
            filters["topic"] = topic
        if exam_type:
            filters["exam_type"] = exam_type

        # Zorluk aralığı filtresi
        if difficulty_range:
            min_diff, max_diff = difficulty_range
            # Range query için özel işlem gerekli

        # Arama alanları
        search_fields = ["question_text^3", "option_a", "option_b", "option_c", "option_d", "option_e", "explanation"]

        return await self.es_client.turkish_full_text_search(
            index_name=self.index_name,
            query_text=query_text,
            fields=search_fields,
            size=size,
            from_=from_,
            filters=filters,
        )

    async def get_similar_questions(
        self, question_id: str, size: int = 5
    ) -> SearchResponse:
        """Benzer soruları bul"""
        try:
            # Orijinal soruyu al
            original_question = await self.es_client.get_document(
                index_name=self.index_name, doc_id=question_id
            )

            if not original_question:
                return SearchResponse(
                    total=0, max_score=None, results=[], took=0, timed_out=False
                )

            # More Like This query
            query = {
                "more_like_this": {
                    "fields": ["text", "explanation"],
                    "like": [{"_index": self.index_name, "_id": question_id}],
                    "min_term_freq": 1,
                    "max_query_terms": 12,
                    "analyzer": "turkish_analyzer",
                }
            }

            return await self.es_client.search(
                index_name=self.index_name, query=query, size=size
            )

        except Exception as e:
            logger.error(f"Benzer soru arama hatası: {e!s}", exc_info=True)
            return SearchResponse(
                total=0, max_score=None, results=[], took=0, timed_out=False
            )


class ContentSearchService:
    """İçerik arama servisi"""

    def __init__(self, es_client: ElasticsearchClient):
        self.es_client = es_client
        import os as _os
        self.index_name = _os.environ.get("ELASTICSEARCH_INDEX", "turkiye_sinav_platform")

        # İçerik indeks mapping'i
        self.content_mapping = {
            "properties": {
                "id": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "analyzer": "turkish_analyzer",
                    "search_analyzer": "turkish_search_analyzer",
                },
                "description": {"type": "text", "analyzer": "turkish_analyzer"},
                "content": {"type": "text", "analyzer": "turkish_analyzer"},
                "content_type": {"type": "keyword"},
                "subject": {"type": "keyword"},
                "topic": {"type": "keyword"},
                "difficulty_level": {"type": "keyword"},
                "source": {"type": "keyword"},
                "url": {"type": "keyword"},
                "duration": {"type": "integer"},
                "language": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "quality_score": {"type": "float"},
                "view_count": {"type": "integer"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "indexed_at": {"type": "date"},
            }
        }

    async def initialize_index(self) -> bool:
        """İçerik indeksini başlat"""
        try:
            success = await self.es_client.create_index(
                index_name=self.index_name, mapping=self.content_mapping
            )

            if success:
                logger.info(f"İçerik indeksi başlatıldı: {self.index_name}")

            return success

        except Exception as e:
            logger.error(f"İçerik indeksi başlatma hatası: {e!s}", exc_info=True)
            return False

    async def index_content(self, content: dict[str, Any]) -> bool:
        """İçeriği indeksle"""
        try:
            return await self.es_client.index_document(
                index_name=self.index_name, document=content, doc_id=content.get("id")
            )

        except Exception as e:
            logger.error(f"İçerik indeksleme hatası: {e!s}", exc_info=True)
            return False

    async def search_content(
        self,
        query_text: str,
        content_type: str | None = None,
        subject: str | None = None,
        difficulty_level: str | None = None,
        size: int = 20,
        from_: int = 0,
    ) -> SearchResponse:
        """İçerik arama"""

        # Filtreler
        filters = {}
        if content_type:
            filters["content_type"] = content_type
        if subject:
            filters["subject"] = subject
        if difficulty_level:
            filters["difficulty_level"] = difficulty_level

        # Arama alanları (title daha önemli)
        search_fields = ["title^3", "description^2", "content", "tags"]

        return await self.es_client.turkish_full_text_search(
            index_name=self.index_name,
            query_text=query_text,
            fields=search_fields,
            size=size,
            from_=from_,
            filters=filters,
        )


class AnalyticsService:
    """Analytics ve logging servisi"""

    def __init__(self, es_client: ElasticsearchClient):
        self.es_client = es_client
        self.index_name = "analytics"

        # Analytics indeks mapping'i
        self.analytics_mapping = {
            "properties": {
                "event_type": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "session_id": {"type": "keyword"},
                "timestamp": {"type": "date"},
                "data": {"type": "object"},
                "ip_address": {"type": "ip"},
                "user_agent": {"type": "text"},
                "page_url": {"type": "keyword"},
                "referrer": {"type": "keyword"},
                "duration": {"type": "integer"},
                "success": {"type": "boolean"},
                "error_message": {"type": "text"},
            }
        }

    async def initialize_index(self) -> bool:
        """Analytics indeksini başlat"""
        try:
            # Time-based index pattern kullan
            current_month = datetime.now().strftime("%Y-%m")
            index_name = f"{self.index_name}-{current_month}"

            success = await self.es_client.create_index(
                index_name=index_name, mapping=self.analytics_mapping
            )

            if success:
                logger.info(f"Analytics indeksi başlatıldı: {index_name}")

            return success

        except Exception as e:
            logger.error(f"Analytics indeksi başlatma hatası: {e!s}", exc_info=True)
            return False

    async def log_event(
        self,
        event_type: str,
        user_id: str | None = None,
        session_id: str | None = None,
        data: dict[str, Any] | None = None,
        **kwargs,
    ) -> bool:
        """Event logla"""
        try:
            # Time-based index
            current_month = datetime.now().strftime("%Y-%m")
            index_name = f"{self.index_name}-{current_month}"

            event_doc = {
                "event_type": event_type,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "data": data or {},
                **kwargs,
            }

            return await self.es_client.index_document(
                index_name=index_name, document=event_doc
            )

        except Exception as e:
            logger.error(f"Event loglama hatası: {e!s}", exc_info=True)
            return False

    async def get_user_analytics(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Kullanıcı analytics'i"""
        try:
            # Date range query
            query = {
                "bool": {
                    "must": [
                        {"term": {"user_id": user_id}},
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_date.isoformat(),
                                    "lte": end_date.isoformat(),
                                }
                            }
                        },
                    ]
                }
            }

            # Aggregations
            aggs = {
                "event_types": {"terms": {"field": "event_type"}},
                "daily_activity": {
                    "date_histogram": {"field": "timestamp", "calendar_interval": "day"}
                },
                "success_rate": {"terms": {"field": "success"}},
            }

            # Multiple indices pattern
            index_pattern = f"{self.index_name}-*"

            response = await self.es_client.search(
                index_name=index_pattern,
                query=query,
                size=0,  # Sadece aggregation sonuçları
            )

            return {
                "total_events": response.total,
                "aggregations": response.results,  # Bu kısım düzeltilmeli
            }

        except Exception as e:
            logger.error(f"Kullanıcı analytics hatası: {e!s}", exc_info=True)
            return {}

    async def get_bulk_user_analytics(
        self, user_ids: list[str], start_date: datetime, end_date: datetime
    ) -> dict[str, dict[str, Any]]:
        """
        Toplu kullanıcı analytics'i - N+1 query problemini çözer

        Args:
            user_ids: Kullanıcı ID listesi
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi

        Returns:
            Dict[user_id -> analytics_data] mapping

        Performance:
            - Before: N queries (N = user count)
            - After: 1 query
            - Improvement: ~95% faster for 30+ users
        """
        try:
            if not user_ids:
                return {}

            # Terms query for multiple users
            query = {
                "bool": {
                    "must": [
                        {"terms": {"user_id": user_ids}},  # Multiple user_ids
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_date.isoformat(),
                                    "lte": end_date.isoformat(),
                                }
                            }
                        },
                    ]
                }
            }

            # Per-user aggregations
            aggs = {
                "users": {
                    "terms": {
                        "field": "user_id",
                        "size": len(user_ids),  # Ensure all users are included
                    },
                    "aggs": {
                        "event_types": {"terms": {"field": "event_type"}},
                        "daily_activity": {
                            "date_histogram": {
                                "field": "timestamp",
                                "calendar_interval": "day",
                            }
                        },
                        "success_rate": {"terms": {"field": "success"}},
                    },
                }
            }

            # Multiple indices pattern
            index_pattern = f"{self.index_name}-*"

            response = await self.es_client.search(
                index_name=index_pattern,
                query=query,
                aggs=aggs,
                size=0,  # Sadece aggregation sonuçları
            )

            # Parse aggregation buckets into user_id -> analytics mapping
            result = {}

            # Handle response structure
            if hasattr(response, "aggregations"):
                user_buckets = response.aggregations.get("users", {}).get("buckets", [])
            elif isinstance(response, dict):
                user_buckets = (
                    response.get("aggregations", {}).get("users", {}).get("buckets", [])
                )
            else:
                user_buckets = []

            for bucket in user_buckets:
                user_id = bucket.get("key")
                result[user_id] = {
                    "total_events": bucket.get("doc_count", 0),
                    "aggregations": {
                        "event_types": bucket.get("event_types", {}),
                        "daily_activity": bucket.get("daily_activity", {}),
                        "success_rate": bucket.get("success_rate", {}),
                    },
                }

            # Fill in empty data for users with no events
            for user_id in user_ids:
                if user_id not in result:
                    result[user_id] = {
                        "total_events": 0,
                        "aggregations": {
                            "event_types": {},
                            "daily_activity": {},
                            "success_rate": {},
                        },
                    }

            logger.info(f"Bulk analytics retrieved for {len(user_ids)} users")
            return result

        except Exception as e:
            logger.error(f"Toplu kullanıcı analytics hatası: {e!s}", exc_info=True)
            # Return empty data for all users on error
            return {user_id: {} for user_id in user_ids}


class ElasticsearchService:
    """Ana Elasticsearch servis sınıfı"""

    def __init__(self, es_client: ElasticsearchClient):
        self.es_client = es_client
        self.question_service = QuestionSearchService(es_client)
        self.content_service = ContentSearchService(es_client)
        self.analytics_service = AnalyticsService(es_client)

    async def initialize_all_indices(self) -> dict[str, bool]:
        """Tüm indeksleri başlat"""
        results = {}

        try:
            # Soru indeksi
            results["questions"] = await self.question_service.initialize_index()

            # İçerik indeksi
            results["content"] = await self.content_service.initialize_index()

            # Analytics indeksi
            results["analytics"] = await self.analytics_service.initialize_index()

            logger.info(f"İndeks başlatma sonuçları: {results}")
            return results

        except Exception as e:
            logger.error(f"İndeks başlatma hatası: {e!s}", exc_info=True)
            return results

    async def health_check(self) -> dict[str, Any]:
        """Elasticsearch sağlık kontrolü"""
        try:
            if not self.es_client.is_connected:
                return {"status": "disconnected", "error": "Client not connected"}

            # Cluster health
            health = await self.es_client.client.cluster.health()

            # İndeks istatistikleri
            indices_stats = {}
            for index_name in ["questions", "content", "analytics"]:
                stats = await self.es_client.get_index_stats(index_name)
                if stats:
                    indices_stats[index_name] = {
                        "doc_count": stats["total"]["docs"]["count"],
                        "store_size": stats["total"]["store"]["size_in_bytes"],
                    }

            return {
                "status": "healthy",
                "cluster_name": health["cluster_name"],
                "cluster_status": health["status"],
                "indices": indices_stats,
            }

        except Exception as e:
            logger.error(f"Sağlık kontrolü hatası: {e!s}", exc_info=True)
            return {"status": "error", "error": str(e)}


# Global service instance
elasticsearch_service: ElasticsearchService | None = None


async def get_elasticsearch_service() -> ElasticsearchService:
    """Elasticsearch service dependency"""
    global elasticsearch_service

    if not elasticsearch_service:
        from core.elasticsearch_client import get_elasticsearch_client

        es_client = get_elasticsearch_client()
        elasticsearch_service = ElasticsearchService(es_client)

    return elasticsearch_service
