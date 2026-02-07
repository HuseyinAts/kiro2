"""
KIRO2 Log Management Service
Elasticsearch ILM Policy ve Index Template yönetimi

Bu servis centralized logging için:
- Index Lifecycle Management (ILM) policy'leri
- Index template'leri
- Log index yönetimi
sağlar.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch

logger = logging.getLogger(__name__)


class LogManagementService:
    """
    Elasticsearch Log Management Service

    Features:
    - ILM Policy management (hot-warm-cold-delete)
    - Index template creation with Turkish analyzer
    - Log index rollover management
    - Retention policy enforcement
    """

    def __init__(self, es_client: AsyncElasticsearch):
        """
        Initialize Log Management Service.

        Args:
            es_client: Async Elasticsearch client instance
        """
        self.es_client = es_client
        self.policy_name = "kiro2-logs-policy"
        self.template_name = "kiro2-logs"
        self.index_pattern = "kiro2-logs-*"
        self.rollover_alias = "kiro2-logs"

    async def setup_ilm_policy(self) -> bool:
        """
        ILM policy oluştur veya güncelle.

        Policy phases:
        - Hot: Aktif yazma, rollover 50GB veya 1 gün
        - Warm: 7 gün sonra, read-only, force merge
        - Cold: 14 gün sonra, reduced replicas
        - Delete: 30 gün sonra silme

        Returns:
            bool: Policy başarıyla oluşturuldu mu
        """
        policy_body = {
            "policy": {
                "phases": {
                    # Hot phase - aktif yazma
                    "hot": {
                        "min_age": "0ms",
                        "actions": {
                            "rollover": {
                                "max_primary_shard_size": "50gb",
                                "max_age": "1d",
                                "max_docs": 10000000,  # 10M docs
                            },
                            "set_priority": {"priority": 100},
                        },
                    },
                    # Warm phase - okuma optimizasyonu
                    "warm": {
                        "min_age": "7d",
                        "actions": {
                            "set_priority": {"priority": 50},
                            "readonly": {},
                            "forcemerge": {"max_num_segments": 1},
                            "shrink": {"number_of_shards": 1},
                            "allocate": {"number_of_replicas": 0},
                        },
                    },
                    # Cold phase - düşük erişim
                    "cold": {
                        "min_age": "14d",
                        "actions": {
                            "set_priority": {"priority": 0},
                            "allocate": {
                                "number_of_replicas": 0,
                                "require": {"data": "cold"},
                            },
                        },
                    },
                    # Delete phase - silme
                    "delete": {
                        "min_age": "30d",
                        "actions": {"delete": {}},
                    },
                },
            }
        }

        try:
            await self.es_client.ilm.put_lifecycle(
                name=self.policy_name, body=policy_body
            )
            logger.info(f"ILM policy oluşturuldu: {self.policy_name}")
            return True
        except Exception as e:
            logger.error(f"ILM policy oluşturma hatası: {e}")
            return False

    async def setup_index_template(self) -> bool:
        """
        Log index template oluştur.

        Template özellikleri:
        - Turkish analyzer desteği
        - Structured logging için mapping
        - ILM policy bağlantısı
        - Optimum shard/replica ayarları

        Returns:
            bool: Template başarıyla oluşturuldu mu
        """
        template_body = {
            "index_patterns": [self.index_pattern],
            "template": {
                "settings": {
                    "number_of_shards": 5,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": self.policy_name,
                    "index.lifecycle.rollover_alias": self.rollover_alias,
                    "codec": "best_compression",
                    "refresh_interval": "5s",
                    "analysis": {
                        "analyzer": {
                            "turkish_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "turkish_lowercase",
                                    "apostrophe",
                                    "turkish_stemmer",
                                ],
                            }
                        },
                        "filter": {
                            "turkish_lowercase": {
                                "type": "lowercase",
                                "language": "turkish",
                            },
                            "turkish_stemmer": {
                                "type": "stemmer",
                                "language": "turkish",
                            },
                        },
                    },
                },
                "mappings": {
                    "dynamic": "true",
                    "dynamic_templates": [
                        {
                            "strings_as_keywords": {
                                "match_mapping_type": "string",
                                "mapping": {"type": "keyword", "ignore_above": 1024},
                            }
                        }
                    ],
                    "properties": {
                        # Timestamp fields
                        "@timestamp": {"type": "date"},
                        "log_timestamp": {"type": "date"},
                        "processed_at": {"type": "date"},
                        # Log level
                        "log_level": {"type": "keyword"},
                        "log_level_normalized": {"type": "keyword"},
                        # Event and message
                        "event": {
                            "type": "text",
                            "analyzer": "turkish_analyzer",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "message": {
                            "type": "text",
                            "analyzer": "turkish_analyzer",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        # Correlation and tracing
                        "correlation_id": {"type": "keyword"},
                        "trace_id": {"type": "keyword"},
                        "span_id": {"type": "keyword"},
                        # User context
                        "user_id": {"type": "keyword"},
                        "session_id": {"type": "keyword"},
                        # Service metadata
                        "service_name": {"type": "keyword"},
                        "logger_name": {"type": "keyword"},
                        "platform": {"type": "keyword"},
                        "environment": {"type": "keyword"},
                        # KIRO2 specific
                        "event_category": {"type": "keyword"},
                        "exam_id": {"type": "keyword"},
                        "question_id": {"type": "keyword"},
                        # Performance metrics
                        "response_time_ms": {"type": "float"},
                        "performance_class": {"type": "keyword"},
                        # Request context
                        "client_ip": {"type": "ip"},
                        "user_agent": {"type": "text"},
                        "path": {"type": "keyword"},
                        "method": {"type": "keyword"},
                        "status_code": {"type": "integer"},
                        # GeoIP
                        "geoip": {
                            "properties": {
                                "city_name": {"type": "keyword"},
                                "country_name": {"type": "keyword"},
                                "country_code2": {"type": "keyword"},
                                "region_name": {"type": "keyword"},
                                "location": {"type": "geo_point"},
                                "coordinates": {"type": "geo_point"},
                            }
                        },
                        # User agent parsed
                        "user_agent_parsed": {
                            "properties": {
                                "name": {"type": "keyword"},
                                "os": {"type": "keyword"},
                                "os_name": {"type": "keyword"},
                                "device": {"type": "keyword"},
                            }
                        },
                        # Error context
                        "error": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "message": {"type": "text"},
                                "stack_trace": {"type": "text", "index": False},
                            }
                        },
                        # Tags
                        "tags": {"type": "keyword"},
                    },
                },
            },
            "priority": 500,
            "composed_of": [],
            "version": 1,
            "_meta": {
                "description": "KIRO2 YKS Platform log template",
                "created_by": "log_management_service",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        try:
            await self.es_client.indices.put_index_template(
                name=self.template_name, body=template_body
            )
            logger.info(f"Index template oluşturuldu: {self.template_name}")
            return True
        except Exception as e:
            logger.error(f"Index template oluşturma hatası: {e}")
            return False

    async def create_initial_index(self) -> bool:
        """
        İlk log index'ini oluştur ve alias bağla.

        Returns:
            bool: Index başarıyla oluşturuldu mu
        """
        initial_index = f"kiro2-logs-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}-000001"

        try:
            # Index zaten var mı kontrol et
            exists = await self.es_client.indices.exists(index=initial_index)
            if exists:
                logger.info(f"Index zaten mevcut: {initial_index}")
                return True

            # Yeni index oluştur
            await self.es_client.indices.create(
                index=initial_index,
                body={
                    "aliases": {self.rollover_alias: {"is_write_index": True}},
                },
            )
            logger.info(f"Initial index oluşturuldu: {initial_index}")
            return True
        except Exception as e:
            logger.error(f"Initial index oluşturma hatası: {e}")
            return False

    async def setup_error_index(self) -> bool:
        """
        Error log'ları için ayrı index template oluştur.

        Returns:
            bool: Template başarıyla oluşturuldu mu
        """
        template_body = {
            "index_patterns": ["kiro2-errors-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": self.policy_name,
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "log_level": {"type": "keyword"},
                        "event": {"type": "text"},
                        "error": {
                            "properties": {
                                "type": {"type": "keyword"},
                                "message": {"type": "text"},
                                "stack_trace": {"type": "text"},
                            }
                        },
                        "service_name": {"type": "keyword"},
                        "correlation_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                    }
                },
            },
            "priority": 600,
        }

        try:
            await self.es_client.indices.put_index_template(
                name="kiro2-errors", body=template_body
            )
            logger.info("Error index template oluşturuldu")
            return True
        except Exception as e:
            logger.error(f"Error index template hatası: {e}")
            return False

    async def setup_exam_events_index(self) -> bool:
        """
        Exam events için ayrı index template oluştur.

        Returns:
            bool: Template başarıyla oluşturuldu mu
        """
        template_body = {
            "index_patterns": ["kiro2-exams-*"],
            "template": {
                "settings": {
                    "number_of_shards": 2,
                    "number_of_replicas": 1,
                    "index.lifecycle.name": self.policy_name,
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "event": {"type": "keyword"},
                        "exam_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "question_id": {"type": "keyword"},
                        "answer": {"type": "keyword"},
                        "is_correct": {"type": "boolean"},
                        "response_time_ms": {"type": "float"},
                        "difficulty": {"type": "float"},
                        "subject": {"type": "keyword"},
                        "topic": {"type": "keyword"},
                    }
                },
            },
            "priority": 550,
        }

        try:
            await self.es_client.indices.put_index_template(
                name="kiro2-exams", body=template_body
            )
            logger.info("Exam events index template oluşturuldu")
            return True
        except Exception as e:
            logger.error(f"Exam events index template hatası: {e}")
            return False

    async def initialize_logging_infrastructure(self) -> Dict[str, bool]:
        """
        Tüm logging altyapısını başlat.

        Returns:
            Dict[str, bool]: Her bileşenin başarı durumu
        """
        results = {}

        # 1. ILM Policy
        results["ilm_policy"] = await self.setup_ilm_policy()

        # 2. Main log template
        results["main_template"] = await self.setup_index_template()

        # 3. Error template
        results["error_template"] = await self.setup_error_index()

        # 4. Exam events template
        results["exam_template"] = await self.setup_exam_events_index()

        # 5. Initial index
        results["initial_index"] = await self.create_initial_index()

        logger.info(f"Logging altyapısı başlatıldı: {results}")
        return results

    async def get_ilm_status(self) -> Dict[str, Any]:
        """
        ILM policy ve index durumunu getir.

        Returns:
            Dict: ILM durumu ve istatistikleri
        """
        try:
            # Policy detayları
            policy = await self.es_client.ilm.get_lifecycle(name=self.policy_name)

            # Index'lerin ILM durumu
            indices = await self.es_client.indices.get(index=self.index_pattern)

            ilm_status = {}
            for index_name in indices:
                try:
                    status = await self.es_client.ilm.explain_lifecycle(index=index_name)
                    ilm_status[index_name] = status.get("indices", {}).get(
                        index_name, {}
                    )
                except Exception:
                    ilm_status[index_name] = {"error": "Status unavailable"}

            return {
                "policy": policy,
                "indices": ilm_status,
                "total_indices": len(indices),
            }
        except Exception as e:
            logger.error(f"ILM status hatası: {e}")
            return {"error": str(e)}

    async def force_rollover(self) -> bool:
        """
        Manuel rollover tetikle.

        Returns:
            bool: Rollover başarılı mı
        """
        try:
            result = await self.es_client.indices.rollover(alias=self.rollover_alias)
            logger.info(f"Rollover tamamlandı: {result}")
            return result.get("rolled_over", False)
        except Exception as e:
            logger.error(f"Rollover hatası: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Log index istatistiklerini getir.

        Returns:
            Dict: Index istatistikleri
        """
        try:
            stats = await self.es_client.indices.stats(index=self.index_pattern)

            total = stats.get("_all", {}).get("total", {})
            return {
                "total_docs": total.get("docs", {}).get("count", 0),
                "total_size_bytes": total.get("store", {}).get("size_in_bytes", 0),
                "total_size_gb": round(
                    total.get("store", {}).get("size_in_bytes", 0) / (1024**3), 2
                ),
                "index_count": len(stats.get("indices", {})),
                "indices": {
                    name: {
                        "docs": idx.get("total", {}).get("docs", {}).get("count", 0),
                        "size_bytes": idx.get("total", {})
                        .get("store", {})
                        .get("size_in_bytes", 0),
                    }
                    for name, idx in stats.get("indices", {}).items()
                },
            }
        except Exception as e:
            logger.error(f"Index stats hatası: {e}")
            return {"error": str(e)}

    async def cleanup_old_indices(self, older_than_days: int = 30) -> List[str]:
        """
        Eski index'leri manuel olarak temizle (ILM'e ek olarak).

        Args:
            older_than_days: Kaç günden eski index'ler silinsin

        Returns:
            List[str]: Silinen index isimleri
        """
        deleted = []
        try:
            indices = await self.es_client.indices.get(index=self.index_pattern)

            for index_name in indices:
                # Index adından tarih çıkar
                try:
                    # Format: kiro2-logs-YYYY.MM.dd-000001
                    date_part = index_name.split("-")[2]
                    index_date = datetime.strptime(date_part, "%Y.%m.%d")
                    age_days = (datetime.now(timezone.utc) - index_date).days

                    if age_days > older_than_days:
                        await self.es_client.indices.delete(index=index_name)
                        deleted.append(index_name)
                        logger.info(f"Eski index silindi: {index_name} ({age_days} gün)")
                except (IndexError, ValueError):
                    continue

            return deleted
        except Exception as e:
            logger.error(f"Index cleanup hatası: {e}")
            return deleted


# Global service instance
_log_management_service: Optional[LogManagementService] = None


async def get_log_management_service() -> LogManagementService:
    """
    Log Management Service dependency.

    Returns:
        LogManagementService: Singleton instance
    """
    global _log_management_service

    if _log_management_service is None:
        from elasticsearch import AsyncElasticsearch
        from core.config import settings

        es_client = AsyncElasticsearch(
            hosts=[settings.ELASTICSEARCH_URL or "http://localhost:9200"],
            retry_on_timeout=True,
            max_retries=3,
        )
        _log_management_service = LogManagementService(es_client)

    return _log_management_service


async def initialize_logging_on_startup() -> None:
    """
    Uygulama başlangıcında logging altyapısını başlat.
    main.py startup event'inde çağrılmalı.
    """
    try:
        service = await get_log_management_service()
        results = await service.initialize_logging_infrastructure()
        logger.info(f"Logging infrastructure initialized: {results}")
    except Exception as e:
        logger.error(f"Logging infrastructure initialization failed: {e}")
