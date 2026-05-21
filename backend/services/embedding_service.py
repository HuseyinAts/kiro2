"""
Embedding Service - KIRO2 YKS Platform

Spec REQ-1: Embedding Generation
- REQ-1.1: Sentence-Transformers kullanımı
- REQ-1.2: Multilingual model (paraphrase-multilingual-mpnet-base-v2)
- REQ-1.3: 768-dim vector output
- REQ-1.4: Batch processing (batch_size: 32)
- REQ-1.5: Redis cache (TTL: 24h)
- REQ-1.6: Cosine similarity distribution kontrolü

Author: KIRO2 Team
Date: 2026-01-18
"""

import hashlib
import logging
import time
from dataclasses import dataclass

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from core.config import EmbeddingConfig

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingStats:
    """Embedding istatistikleri."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_latency_ms: float = 0.0
    model_name: str = ""


class EmbeddingService:
    """
    Metin embedding servisi.

    Spec REQ-1 implementasyonu:
    - Sentence-Transformers ile embedding generation
    - Redis cache ile hızlı erişim
    - Batch processing desteği
    - Türkçe için optimize edilmiş model seçenekleri
    """

    def __init__(
        self,
        model_name: str | None = None,
        cache_ttl: int | None = None,
        batch_size: int | None = None,
        redis_url: str | None = None,
    ):
        """
        EmbeddingService başlat.

        Args:
            model_name: Embedding model adı (varsayılan: config'den)
            cache_ttl: Cache TTL saniye (varsayılan: 86400 = 24h)
            batch_size: Batch işlem boyutu (varsayılan: 32)
            redis_url: Redis URL (varsayılan: config'den)
        """
        self.model_name = model_name or EmbeddingConfig.get_model_name()
        self.cache_ttl = cache_ttl or EmbeddingConfig.CACHE_TTL_SECONDS
        self.batch_size = batch_size or EmbeddingConfig.BATCH_SIZE
        self.dimension = EmbeddingConfig.get_model_dimension()

        self._model: SentenceTransformer | None = None
        self._redis: redis.Redis | None = None
        self._initialized = False

        # İstatistikler
        self._stats = EmbeddingStats(model_name=self.model_name)
        self._latencies: list[float] = []

        # Redis URL
        import os
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

    def _initialize(self) -> bool:
        """
        Model ve cache'i başlat.

        Returns:
            Başarı durumu
        """
        if self._initialized:
            return True

        # Model yükle
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Model loaded successfully: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load model {self.model_name}: {e}", exc_info=True)
                return False
        else:
            logger.warning("sentence-transformers not available, using hash fallback")

        # Redis bağlantısı
        if REDIS_AVAILABLE:
            try:
                self._redis = redis.from_url(
                    self._redis_url,
                    decode_responses=False  # Binary for embeddings
                )
                # Bağlantı testi
                self._redis.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Cache disabled.")
                self._redis = None
        else:
            logger.warning("Redis not available, cache disabled")

        self._initialized = True
        return True

    def _get_cache_key(self, text: str) -> str:
        """
        Cache key oluştur.

        Spec: chromadb:emb:{hash(text)}

        Args:
            text: Metin

        Returns:
            Cache key
        """
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:32]
        return f"chromadb:emb:{text_hash}"

    def _get_from_cache(self, text: str) -> list[float] | None:
        """
        Cache'den embedding al.

        Args:
            text: Metin

        Returns:
            Embedding veya None
        """
        if self._redis is None:
            return None

        try:
            key = self._get_cache_key(text)
            data = self._redis.get(key)

            if data and NUMPY_AVAILABLE:
                embedding = np.frombuffer(data, dtype=np.float32)
                return embedding.tolist()
            return None

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    def _set_to_cache(self, text: str, embedding: list[float]) -> bool:
        """
        Embedding'i cache'e kaydet.

        Args:
            text: Metin
            embedding: Embedding vektörü

        Returns:
            Başarı durumu
        """
        if self._redis is None:
            return False

        try:
            key = self._get_cache_key(text)

            if NUMPY_AVAILABLE:
                data = np.array(embedding, dtype=np.float32).tobytes()
            else:
                # Fallback: JSON
                import json
                data = json.dumps(embedding).encode()

            self._redis.setex(key, self.cache_ttl, data)
            return True

        except Exception as e:
            logger.warning(f"Cache write error: {e}")
            return False

    def embed(self, text: str, use_cache: bool = True) -> list[float]:
        """
        Tek metin için embedding oluştur.

        Spec REQ-1.1, REQ-1.3, REQ-1.5

        Args:
            text: Embedding oluşturulacak metin
            use_cache: Cache kullan (varsayılan: True)

        Returns:
            768-dim embedding vektörü
        """
        if not self._initialize():
            return self._fallback_embedding(text)

        start_time = time.time()
        self._stats.total_requests += 1

        # Cache kontrolü
        if use_cache:
            cached = self._get_from_cache(text)
            if cached is not None:
                self._stats.cache_hits += 1
                return cached

        self._stats.cache_misses += 1

        # Model ile embedding oluştur
        if self._model is not None:
            try:
                embedding = self._model.encode(text, convert_to_numpy=True)
                embedding_list = embedding.tolist()
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}", exc_info=True)
                embedding_list = self._fallback_embedding(text)
        else:
            embedding_list = self._fallback_embedding(text)

        # Cache'e kaydet
        if use_cache:
            self._set_to_cache(text, embedding_list)

        # Latency tracking
        latency_ms = (time.time() - start_time) * 1000
        self._latencies.append(latency_ms)
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]
        self._stats.avg_latency_ms = sum(self._latencies) / len(self._latencies)

        return embedding_list

    def embed_batch(
        self,
        texts: list[str],
        use_cache: bool = True,
        show_progress: bool = False
    ) -> list[list[float]]:
        """
        Batch metin için embedding oluştur.

        Spec REQ-1.4: Batch processing (batch_size: 32)

        Args:
            texts: Embedding oluşturulacak metinler
            use_cache: Cache kullan
            show_progress: Progress göster

        Returns:
            Embedding vektörleri listesi
        """
        if not self._initialize():
            return [self._fallback_embedding(t) for t in texts]

        if not texts:
            return []

        results: list[list[float]] = [None] * len(texts)  # type: ignore
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        # Cache kontrolü
        if use_cache:
            for i, text in enumerate(texts):
                cached = self._get_from_cache(text)
                if cached is not None:
                    results[i] = cached
                    self._stats.cache_hits += 1
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
                    self._stats.cache_misses += 1
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts

        # Cache'de olmayanları batch olarak işle
        if uncached_texts and self._model is not None:
            try:
                # Batch processing
                for batch_start in range(0, len(uncached_texts), self.batch_size):
                    batch_end = min(batch_start + self.batch_size, len(uncached_texts))
                    batch_texts = uncached_texts[batch_start:batch_end]

                    batch_embeddings = self._model.encode(
                        batch_texts,
                        convert_to_numpy=True,
                        show_progress_bar=show_progress
                    )

                    for j, embedding in enumerate(batch_embeddings):
                        idx = uncached_indices[batch_start + j]
                        embedding_list = embedding.tolist()
                        results[idx] = embedding_list

                        # Cache'e kaydet
                        if use_cache:
                            self._set_to_cache(batch_texts[j], embedding_list)

            except Exception as e:
                logger.error(f"Batch embedding failed: {e}", exc_info=True)
                # Fallback
                for i, text in zip(uncached_indices, uncached_texts):
                    results[i] = self._fallback_embedding(text)
        else:
            # Model yok, fallback
            for i, text in zip(uncached_indices, uncached_texts):
                results[i] = self._fallback_embedding(text)

        self._stats.total_requests += len(texts)
        return results

    def _fallback_embedding(self, text: str) -> list[float]:
        """
        Model yoksa hash-based fallback embedding.

        Args:
            text: Metin

        Returns:
            Pseudo-random embedding
        """
        # Deterministic hash-based embedding
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()

        # 768-dim için iteratif hash (768 / 32 = 24 iterasyon)
        all_bytes = hash_bytes
        iterations_needed = (self.dimension // 32) + 1  # 24 for 768-dim
        for i in range(iterations_needed - 1):
            hash_bytes = hashlib.sha256(hash_bytes).digest()
            all_bytes += hash_bytes

        # Normalize to [-1, 1]
        embedding = [float(b) / 127.5 - 1.0 for b in all_bytes[:self.dimension]]

        # L2 normalize
        if NUMPY_AVAILABLE:
            arr = np.array(embedding)
            norm = np.linalg.norm(arr)
            if norm > 0:
                embedding = (arr / norm).tolist()

        return embedding

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        İki vektör arasındaki cosine similarity hesapla.

        Spec REQ-1.6: Cosine similarity distribution kontrolü

        Args:
            vec1: Birinci vektör
            vec2: İkinci vektör

        Returns:
            Similarity değeri (-1 ile 1 arası)
        """
        if NUMPY_AVAILABLE:
            a = np.array(vec1)
            b = np.array(vec2)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            return float(np.dot(a, b) / (norm_a * norm_b))
        # Fallback
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def warm_cache(self, texts: list[str]) -> int:
        """
        Cache'i önceden ısıt.

        Spec REQ-1.5: Cache warming for frequent queries

        Args:
            texts: Cache'lenecek metinler

        Returns:
            Cache'lenen metin sayısı
        """
        if not self._initialize():
            return 0

        # Batch embed (otomatik cache'ler)
        self.embed_batch(texts, use_cache=True)

        return len(texts)

    def get_stats(self) -> EmbeddingStats:
        """
        İstatistikleri döndür.

        Returns:
            EmbeddingStats
        """
        self._stats.avg_latency_ms = (
            sum(self._latencies) / len(self._latencies)
            if self._latencies else 0.0
        )
        return self._stats

    def clear_cache(self, pattern: str = "chromadb:emb:*") -> int:
        """
        Cache'i temizle.

        Args:
            pattern: Silinecek key pattern'i

        Returns:
            Silinen key sayısı
        """
        if self._redis is None:
            return 0

        try:
            keys = list(self._redis.scan_iter(match=pattern, count=1000))
            if keys:
                return self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear failed: {e}", exc_info=True)
            return 0


# Singleton instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service(
    model_name: str | None = None,
    cache_ttl: int | None = None,
    batch_size: int | None = None,
) -> EmbeddingService:
    """
    Singleton EmbeddingService instance döndür.

    Args:
        model_name: Model adı (ilk çağrıda geçerli)
        cache_ttl: Cache TTL
        batch_size: Batch boyutu

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(
            model_name=model_name,
            cache_ttl=cache_ttl,
            batch_size=batch_size,
        )
    return _embedding_service
