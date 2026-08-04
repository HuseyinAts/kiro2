"""
KIRO2 Unified Elasticsearch System
Consolidated Elasticsearch solution combining all ES functionality
"""

import logging
import os
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from elasticsearch import AsyncElasticsearch
    from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError

    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    logger.warning("Elasticsearch not available - install elasticsearch package")


class ElasticsearchConfig(BaseModel):
    """Unified Elasticsearch configuration"""

    host: str = Field(default="localhost")
    port: int = Field(default=9200)
    username: str | None = Field(default=None)
    password: str | None = Field(default=None)
    use_ssl: bool = Field(default=False)
    verify_certs: bool = Field(default=False)
    ca_certs: str | None = Field(default=None)
    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)

    # Index settings
    default_index_prefix: str = Field(default="kiro2")
    default_shards: int = Field(default=1)
    default_replicas: int = Field(default=0)

    # Turkish analysis settings
    enable_turkish_analysis: bool = Field(default=True)
    turkish_stemmer: bool = Field(default=True)

    # Logging settings
    log_queries: bool = Field(default=False)
    log_slow_queries: bool = Field(default=True)
    slow_query_threshold: float = Field(default=1.0)  # seconds

    @classmethod
    def from_env(cls) -> "ElasticsearchConfig":
        """Create config from environment variables"""
        return cls(
            host=os.getenv("ELASTICSEARCH_HOST", "localhost"),
            port=int(os.getenv("ELASTICSEARCH_PORT", "9200")),
            username=os.getenv("ELASTICSEARCH_USER"),
            password=os.getenv("ELASTICSEARCH_PASSWORD"),
            use_ssl=os.getenv("ELASTICSEARCH_USE_SSL", "false").lower() == "true",
            verify_certs=os.getenv("ELASTICSEARCH_VERIFY_CERTS", "false").lower()
            == "true",
            ca_certs=os.getenv("ELASTICSEARCH_CA_CERTS"),
            timeout=int(os.getenv("ELASTICSEARCH_TIMEOUT", "30")),
            max_retries=int(os.getenv("ELASTICSEARCH_MAX_RETRIES", "3")),
            default_index_prefix=os.getenv("ELASTICSEARCH_INDEX_PREFIX", "kiro2"),
            log_queries=os.getenv("ELASTICSEARCH_LOG_QUERIES", "false").lower()
            == "true",
        )


class TurkishAnalyzer:
    """Turkish text analysis settings for Elasticsearch"""

    @staticmethod
    def get_analysis_settings() -> dict[str, Any]:
        """Get Turkish analysis settings"""
        return {
            "analysis": {
                "filter": {
                    "turkish_lowercase": {"type": "lowercase", "language": "turkish"},
                    "turkish_stop": {"type": "stop", "stopwords": "_turkish_"},
                    "turkish_stemmer": {"type": "stemmer", "language": "turkish"},
                    "turkish_synonym": {
                        "type": "synonym",
                        "synonyms": [
                            "matematik,mat",
                            "üniversite,uni",
                            "öğrenci,student",
                            "sınav,test,exam",
                        ],
                    },
                },
                "char_filter": {
                    "turkish_char_filter": {
                        "type": "mapping",
                        "mappings": [
                            "ı => i",
                            "İ => I",
                            "ş => s",
                            "Ş => S",
                            "ğ => g",
                            "Ğ => G",
                            "ü => u",
                            "Ü => U",
                            "ö => o",
                            "Ö => O",
                            "ç => c",
                            "Ç => C",
                        ],
                    }
                },
                "analyzer": {
                    "turkish_analyzer": {
                        "type": "custom",
                        "char_filter": ["turkish_char_filter"],
                        "tokenizer": "standard",
                        "filter": [
                            "turkish_lowercase",
                            "turkish_stop",
                            "turkish_stemmer",
                            "turkish_synonym",
                        ],
                    },
                    "turkish_search_analyzer": {
                        "type": "custom",
                        "char_filter": ["turkish_char_filter"],
                        "tokenizer": "standard",
                        "filter": [
                            "turkish_lowercase",
                            "turkish_stop",
                            "turkish_synonym",
                        ],
                    },
                },
            }
        }


class IndexTemplate:
    """Index template definitions for KIRO2"""

    @staticmethod
    def get_exam_template() -> dict[str, Any]:
        """Get exam index template"""
        return {
            "index_patterns": ["kiro2-exam-*"],
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                **TurkishAnalyzer.get_analysis_settings(),
            },
            "mappings": {
                "properties": {
                    "question_id": {"type": "keyword"},
                    "exam_type": {"type": "keyword"},
                    "subject": {"type": "keyword"},
                    "difficulty": {"type": "integer"},
                    "question_text": {
                        "type": "text",
                        "analyzer": "turkish_analyzer",
                        "search_analyzer": "turkish_search_analyzer",
                    },
                    "options": {"type": "text", "analyzer": "turkish_analyzer"},
                    "correct_answer": {"type": "keyword"},
                    "explanation": {"type": "text", "analyzer": "turkish_analyzer"},
                    "tags": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            },
        }

    @staticmethod
    def get_user_template() -> dict[str, Any]:
        """Get user activity index template"""
        return {
            "index_patterns": ["kiro2-user-*"],
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "user_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "activity_type": {"type": "keyword"},
                    "exam_type": {"type": "keyword"},
                    "question_id": {"type": "keyword"},
                    "answer": {"type": "keyword"},
                    "is_correct": {"type": "boolean"},
                    "response_time": {"type": "integer"},
                    "timestamp": {"type": "date"},
                    "ip_address": {"type": "ip"},
                    "user_agent": {"type": "text", "index": False},
                }
            },
        }

    @staticmethod
    def get_analytics_template() -> dict[str, Any]:
        """Get analytics index template"""
        return {
            "index_patterns": ["kiro2-analytics-*"],
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "event_type": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "user_id": {"type": "keyword"},
                    "session_id": {"type": "keyword"},
                    "exam_type": {"type": "keyword"},
                    "subject": {"type": "keyword"},
                    "metadata": {"type": "object"},
                    "value": {"type": "double"},
                    "timestamp": {"type": "date"},
                    "date": {"type": "date", "format": "yyyy-MM-dd"},
                }
            },
        }


class QueryBuilder:
    """Elasticsearch query builder with Turkish support"""

    @staticmethod
    def match_query(field: str, text: str, operator: str = "and") -> dict[str, Any]:
        """Create match query with Turkish analyzer"""
        return {
            "match": {
                field: {
                    "query": text,
                    "operator": operator,
                    "analyzer": "turkish_search_analyzer",
                }
            }
        }

    @staticmethod
    def multi_match_query(
        fields: list[str], text: str, boost_fields: dict[str, float] = None
    ) -> dict[str, Any]:
        """Create multi-match query"""
        query_fields = fields.copy()

        if boost_fields:
            query_fields = [f"{field}^{boost_fields.get(field, 1)}" for field in fields]

        return {
            "multi_match": {
                "query": text,
                "fields": query_fields,
                "analyzer": "turkish_search_analyzer",
                "type": "best_fields",
                "tie_breaker": 0.3,
            }
        }

    @staticmethod
    def filter_query(filters: dict[str, Any]) -> dict[str, Any]:
        """Create filter query"""
        must_clauses = []

        for field, value in filters.items():
            if isinstance(value, list):
                must_clauses.append({"terms": {field: value}})
            else:
                must_clauses.append({"term": {field: value}})

        return {"bool": {"must": must_clauses}}

    @staticmethod
    def range_query(
        field: str, gte: Any = None, lte: Any = None, gt: Any = None, lt: Any = None
    ) -> dict[str, Any]:
        """Create range query"""
        range_params = {}
        if gte is not None:
            range_params["gte"] = gte
        if lte is not None:
            range_params["lte"] = lte
        if gt is not None:
            range_params["gt"] = gt
        if lt is not None:
            range_params["lt"] = lt

        return {"range": {field: range_params}}


class UnifiedElasticsearchManager:
    """
    Unified Elasticsearch manager combining all ES functionality:
    - Connection management
    - Turkish text analysis
    - Index management
    - Query building
    - Logging and monitoring
    """

    def __init__(self, config: ElasticsearchConfig | None = None):
        self.config = config or ElasticsearchConfig.from_env()
        self.client: AsyncElasticsearch | None = None
        self.query_builder = QueryBuilder()
        self._initialized = False
        self._templates_created = False

    async def initialize(self) -> None:
        """Initialize Elasticsearch connection"""
        if not ELASTICSEARCH_AVAILABLE:
            logger.warning("Elasticsearch not available - skipping initialization")
            return

        if self._initialized:
            return

        try:
            # Create connection
            connection_params = {
                "hosts": [{"host": self.config.host, "port": self.config.port}],
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
            }

            if self.config.username and self.config.password:
                connection_params["basic_auth"] = (
                    self.config.username,
                    self.config.password,
                )

            if self.config.use_ssl:
                connection_params["use_ssl"] = True
                connection_params["verify_certs"] = self.config.verify_certs
                if self.config.ca_certs:
                    connection_params["ca_certs"] = self.config.ca_certs

            self.client = AsyncElasticsearch(**connection_params)

            # Test connection
            if await self._test_connection():
                self._initialized = True
                logger.info("Elasticsearch connection established")

                # Create index templates
                await self._create_index_templates()
            else:
                logger.error("Elasticsearch connection test failed")

        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch: {e}")
            # Don't raise - allow system to work without ES

    async def shutdown(self) -> None:
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()

    async def _test_connection(self) -> bool:
        """Test Elasticsearch connection"""
        try:
            if self.client:
                info = await self.client.info()
                logger.info(f"Connected to Elasticsearch {info['version']['number']}")
                return True
        except Exception as e:
            logger.error(f"Elasticsearch connection test failed: {e}")
        return False

    async def _create_index_templates(self) -> None:
        """Create index templates"""
        if not self.client or self._templates_created:
            return

        templates = {
            "kiro2-exam-template": IndexTemplate.get_exam_template(),
            "kiro2-user-template": IndexTemplate.get_user_template(),
            "kiro2-analytics-template": IndexTemplate.get_analytics_template(),
        }

        try:
            for template_name, template_body in templates.items():
                await self.client.indices.put_index_template(
                    name=template_name, body=template_body
                )
                logger.debug(f"Created index template: {template_name}")

            self._templates_created = True
            logger.info("Index templates created successfully")

        except Exception as e:
            logger.error(f"Failed to create index templates: {e}")

    def _get_index_name(self, index_type: str, date_suffix: bool = True) -> str:
        """Generate index name with optional date suffix"""
        base_name = f"{self.config.default_index_prefix}-{index_type}"

        if date_suffix:
            date_str = datetime.now().strftime("%Y-%m")
            return f"{base_name}-{date_str}"

        return base_name

    async def index_document(
        self,
        index_type: str,
        document: dict[str, Any],
        doc_id: str | None = None,
        date_suffix: bool = True,
    ) -> bool:
        """Index a document"""
        if not self._initialized or not self.client:
            logger.warning("Elasticsearch not initialized - skipping indexing")
            return False

        try:
            index_name = self._get_index_name(index_type, date_suffix)

            # Add timestamp if not present
            if "timestamp" not in document:
                document["timestamp"] = datetime.now()

            start_time = datetime.now()

            if doc_id:
                result = await self.client.index(
                    index=index_name, id=doc_id, body=document
                )
            else:
                result = await self.client.index(index=index_name, body=document)

            # Log slow queries
            duration = (datetime.now() - start_time).total_seconds()
            if (
                self.config.log_slow_queries
                and duration > self.config.slow_query_threshold
            ):
                logger.warning(
                    f"Slow ES index operation: {duration:.2f}s for index {index_name}"
                )

            if self.config.log_queries:
                logger.debug(f"Indexed document to {index_name}: {result['_id']}")

            return result["result"] in ["created", "updated"]

        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return False

    async def search_documents(
        self,
        index_type: str,
        query: dict[str, Any],
        size: int = 10,
        from_: int = 0,
        sort: list[dict[str, Any]] | None = None,
        date_suffix: bool = True,
    ) -> dict[str, Any]:
        """Search documents"""
        if not self._initialized or not self.client:
            logger.warning("Elasticsearch not initialized - returning empty results")
            return {"hits": {"total": {"value": 0}, "hits": []}}

        try:
            index_name = self._get_index_name(index_type, date_suffix)

            search_body = {"query": query, "size": size, "from": from_}

            if sort:
                search_body["sort"] = sort

            start_time = datetime.now()

            result = await self.client.search(index=index_name, body=search_body)

            # Log slow queries
            duration = (datetime.now() - start_time).total_seconds()
            if (
                self.config.log_slow_queries
                and duration > self.config.slow_query_threshold
            ):
                logger.warning(
                    f"Slow ES search: {duration:.2f}s for index {index_name}"
                )

            if self.config.log_queries:
                logger.debug(
                    f"Search in {index_name}: {result['hits']['total']['value']} results"
                )

            return result

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"hits": {"total": {"value": 0}, "hits": []}}

    async def search_questions(
        self,
        text: str,
        exam_type: str | None = None,
        subject: str | None = None,
        difficulty: int | None = None,
        size: int = 10,
    ) -> list[dict[str, Any]]:
        """Search exam questions with Turkish support"""
        # Build query
        must_clauses = []

        # Text search
        if text:
            must_clauses.append(
                self.query_builder.multi_match_query(
                    fields=["question_text", "explanation", "options"],
                    text=text,
                    boost_fields={"question_text": 2.0, "explanation": 1.5},
                )
            )

        # Filters
        filters = {}
        if exam_type:
            filters["exam_type"] = exam_type
        if subject:
            filters["subject"] = subject
        if difficulty:
            filters["difficulty"] = difficulty

        if filters:
            must_clauses.append(self.query_builder.filter_query(filters))

        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}

        result = await self.search_documents("exam", query, size=size)
        return [hit["_source"] for hit in result["hits"]["hits"]]

    async def log_user_activity(
        self, user_id: str, activity_type: str, metadata: dict[str, Any] = None
    ) -> bool:
        """Log user activity"""
        document = {
            "user_id": user_id,
            "activity_type": activity_type,
            "timestamp": datetime.now(),
            **(metadata or {}),
        }

        return await self.index_document("user", document)

    async def log_analytics_event(
        self,
        event_type: str,
        category: str,
        value: float = 1.0,
        metadata: dict[str, Any] = None,
    ) -> bool:
        """Log analytics event"""
        document = {
            "event_type": event_type,
            "category": category,
            "value": value,
            "timestamp": datetime.now(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            **(metadata or {}),
        }

        return await self.index_document("analytics", document)

    async def get_analytics(
        self, category: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Get analytics data"""
        query = {
            "bool": {
                "must": [
                    {"term": {"category": category}},
                    self.query_builder.range_query(
                        "timestamp", gte=start_date, lte=end_date
                    ),
                ]
            }
        }

        # Aggregation query
        search_body = {
            "query": query,
            "size": 0,
            "aggs": {
                "daily_stats": {
                    "date_histogram": {"field": "timestamp", "fixed_interval": "1d"},
                    "aggs": {
                        "total_value": {"sum": {"field": "value"}},
                        "avg_value": {"avg": {"field": "value"}},
                    },
                },
                "event_types": {"terms": {"field": "event_type", "size": 20}},
            },
        }

        try:
            result = await self.client.search(
                index=self._get_index_name("analytics"), body=search_body
            )

            return {
                "total_events": result["hits"]["total"]["value"],
                "daily_stats": result["aggregations"]["daily_stats"]["buckets"],
                "event_types": result["aggregations"]["event_types"]["buckets"],
            }

        except Exception as e:
            logger.error(f"Analytics query failed: {e}")
            return {"total_events": 0, "daily_stats": [], "event_types": []}

    async def health_check(self) -> dict[str, Any]:
        """Perform Elasticsearch health check"""
        status = {
            "available": ELASTICSEARCH_AVAILABLE,
            "initialized": self._initialized,
            "connected": False,
            "cluster_health": None,
            "templates_created": self._templates_created,
        }

        if self._initialized and self.client:
            try:
                # Test connection
                cluster_health = await self.client.cluster.health()
                status["connected"] = True
                status["cluster_health"] = {
                    "status": cluster_health["status"],
                    "number_of_nodes": cluster_health["number_of_nodes"],
                    "active_primary_shards": cluster_health["active_primary_shards"],
                    "active_shards": cluster_health["active_shards"],
                }

            except Exception as e:
                logger.error(f"Elasticsearch health check failed: {e}")
                status["error"] = str(e)

        return status


# Global instance
_elasticsearch_manager: UnifiedElasticsearchManager | None = None


def get_elasticsearch_manager() -> UnifiedElasticsearchManager:
    """Get global Elasticsearch manager instance"""
    global _elasticsearch_manager
    if _elasticsearch_manager is None:
        _elasticsearch_manager = UnifiedElasticsearchManager()
    return _elasticsearch_manager


async def initialize_elasticsearch():
    """Initialize Elasticsearch system"""
    manager = get_elasticsearch_manager()
    await manager.initialize()


# Backward compatibility aliases
ElasticsearchClient = UnifiedElasticsearchManager
ElasticsearchConfig = ElasticsearchConfig  # Already defined above
ElasticsearchLogger = UnifiedElasticsearchManager
