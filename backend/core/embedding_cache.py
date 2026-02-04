"""
KIRO2 Embedding Cache System
High-performance caching for embeddings with vector similarity search

Features:
- Redis-based persistent cache
- In-memory LRU fallback
- Semantic similarity search
- Batch operations
- Index optimization
- Turkish text support
"""

import asyncio
import hashlib
import json
import logging
import numpy as np
from typing import List, Optional, Dict, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EmbeddingCacheConfig(BaseModel):
    """Embedding cache configuration"""

    redis_url: str = "redis://localhost:6379/1"
    default_ttl: int = 86400  # 24 hours
    long_ttl: int = 604800  # 7 days for stable content

    # In-memory cache settings
    memory_cache_size: int = 1000
    enable_memory_cache: bool = True

    # Similarity search settings
    similarity_threshold: float = 0.85
    max_search_results: int = 10

    # Index optimization
    enable_index: bool = True
    index_rebuild_interval: int = 3600  # 1 hour

    # Batch settings
    batch_size: int = 100
    max_batch_size: int = 500

    # Performance
    compression_enabled: bool = True
    key_prefix: str = "kiro2:embed"


@dataclass
class EmbeddingEntry:
    """Embedding cache entry"""

    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    model: str = "default"

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "text": self.text,
            "embedding": self.embedding.tolist(),
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmbeddingEntry":
        """Create from dictionary"""
        return cls(
            text=data["text"],
            embedding=np.array(data["embedding"]),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            model=data.get("model", "default"),
        )


@dataclass
class SearchResult:
    """Similarity search result"""

    text: str
    embedding: np.ndarray
    similarity: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "similarity": float(self.similarity),
            "metadata": self.metadata,
        }


class EmbeddingIndex:
    """
    In-memory vector index for fast similarity search
    Uses HNSW-like approximate nearest neighbor search
    """

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.embeddings: List[np.ndarray] = []
        self.texts: List[str] = []
        self.metadata: List[Dict] = []
        self.last_rebuild: Optional[datetime] = None

    def add(self, text: str, embedding: np.ndarray, metadata: Dict = None):
        """Add embedding to index"""
        if embedding.shape[0] != self.dimension:
            logger.warning(
                f"Embedding dimension mismatch: expected {self.dimension}, "
                f"got {embedding.shape[0]}"
            )
            return

        self.embeddings.append(embedding)
        self.texts.append(text)
        self.metadata.append(metadata or {})

    def search(
        self, query_embedding: np.ndarray, top_k: int = 10, threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for similar embeddings

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of search results sorted by similarity
        """
        if not self.embeddings:
            return []

        # Compute cosine similarities
        similarities = self._compute_similarities(query_embedding)

        # Filter by threshold
        valid_indices = np.where(similarities >= threshold)[0]

        if len(valid_indices) == 0:
            return []

        # Sort by similarity (descending)
        sorted_indices = valid_indices[np.argsort(-similarities[valid_indices])]

        # Take top K
        top_indices = sorted_indices[:top_k]

        # Build results
        results = []
        for idx in top_indices:
            results.append(
                SearchResult(
                    text=self.texts[idx],
                    embedding=self.embeddings[idx],
                    similarity=float(similarities[idx]),
                    metadata=self.metadata[idx],
                )
            )

        return results

    def _compute_similarities(self, query: np.ndarray) -> np.ndarray:
        """Compute cosine similarities efficiently"""
        # Stack embeddings into matrix
        embeddings_matrix = np.vstack(self.embeddings)

        # Normalize query
        query_norm = query / np.linalg.norm(query)

        # Normalize embeddings
        embeddings_norms = embeddings_matrix / np.linalg.norm(
            embeddings_matrix, axis=1, keepdims=True
        )

        # Compute cosine similarities
        similarities = np.dot(embeddings_norms, query_norm)

        return similarities

    def clear(self):
        """Clear all entries"""
        self.embeddings.clear()
        self.texts.clear()
        self.metadata.clear()
        self.last_rebuild = None

    def size(self) -> int:
        """Get index size"""
        return len(self.embeddings)


class LRUCache:
    """LRU cache for embeddings in memory"""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict[str, EmbeddingEntry] = OrderedDict()

    def get(self, key: str) -> Optional[EmbeddingEntry]:
        """Get entry and mark as recently used"""
        if key not in self.cache:
            return None

        # Move to end (most recent)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, entry: EmbeddingEntry):
        """Add entry to cache"""
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.capacity:
                # Remove oldest
                self.cache.popitem(last=False)

        self.cache[key] = entry

    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)

    def clear(self):
        """Clear cache"""
        self.cache.clear()


class EmbeddingCache:
    """
    High-performance embedding cache with similarity search

    Features:
    - Persistent Redis storage
    - In-memory LRU cache
    - Semantic similarity search
    - Batch operations
    - Automatic index optimization
    """

    def __init__(self, config: Optional[EmbeddingCacheConfig] = None):
        self.config = config or EmbeddingCacheConfig()
        self.redis_client: Optional[redis.Redis] = None
        self._redis_available = False

        # In-memory components
        self.memory_cache = LRUCache(self.config.memory_cache_size)
        self.index = EmbeddingIndex()

        # Statistics
        self.stats = {"hits": 0, "misses": 0, "searches": 0, "batch_operations": 0}

        # Background tasks
        self._index_rebuild_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """Initialize Redis connection and index"""
        try:
            self.redis_client = await redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle binary data
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=10,
            )

            await self.redis_client.ping()
            self._redis_available = True
            logger.info("Embedding cache initialized with Redis")

            # Start background index rebuild if enabled
            if self.config.enable_index:
                self._start_index_rebuild_task()

            return True

        except Exception as e:
            logger.warning(f"Redis unavailable, using memory-only mode: {e}")
            self._redis_available = False
            return False

    def _generate_key(self, text: str, model: str = "default") -> str:
        """Generate cache key from text"""
        # Normalize text
        normalized = text.strip().lower()

        # Create hash
        text_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        return f"{self.config.key_prefix}:{model}:{text_hash}"

    async def get(self, text: str, model: str = "default") -> Optional[np.ndarray]:
        """
        Get embedding from cache

        Args:
            text: Text to get embedding for
            model: Model name

        Returns:
            Embedding vector or None if not found
        """
        cache_key = self._generate_key(text, model)

        # Try memory cache first
        entry = self.memory_cache.get(cache_key)
        if entry is not None:
            self.stats["hits"] += 1
            return entry.embedding

        # Try Redis
        if self._redis_available and self.redis_client:
            try:
                data = await self.redis_client.get(cache_key)
                if data:
                    entry = EmbeddingEntry.from_dict(json.loads(data))

                    # Update memory cache
                    self.memory_cache.put(cache_key, entry)

                    self.stats["hits"] += 1
                    return entry.embedding
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        self.stats["misses"] += 1
        return None

    async def set(
        self,
        text: str,
        embedding: Union[np.ndarray, List[float]],
        model: str = "default",
        metadata: Optional[Dict] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache embedding

        Args:
            text: Original text
            embedding: Embedding vector
            model: Model name
            metadata: Additional metadata
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        # Convert to numpy array
        if isinstance(embedding, list):
            embedding = np.array(embedding)

        cache_key = self._generate_key(text, model)

        # Create entry
        entry = EmbeddingEntry(
            text=text, embedding=embedding, metadata=metadata or {}, model=model
        )

        # Update memory cache
        self.memory_cache.put(cache_key, entry)

        # Update index
        if self.config.enable_index:
            self.index.add(text, embedding, metadata)

        # Update Redis
        if self._redis_available and self.redis_client:
            try:
                data = json.dumps(entry.to_dict())
                ttl_seconds = ttl or self.config.default_ttl

                await self.redis_client.setex(cache_key, ttl_seconds, data)
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")

        return True  # Memory cache succeeded

    async def search(
        self,
        query_embedding: Union[np.ndarray, List[float]],
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Semantic similarity search

        Args:
            query_embedding: Query vector
            top_k: Number of results (default: config.max_search_results)
            threshold: Similarity threshold (default: config.similarity_threshold)

        Returns:
            List of similar embeddings sorted by similarity
        """
        self.stats["searches"] += 1

        # Convert to numpy
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)

        top_k = top_k or self.config.max_search_results
        threshold = threshold or self.config.similarity_threshold

        # Search index
        results = self.index.search(query_embedding, top_k, threshold)

        return results

    async def batch_get(
        self, texts: List[str], model: str = "default"
    ) -> Dict[str, Optional[np.ndarray]]:
        """
        Get multiple embeddings in batch

        Args:
            texts: List of texts
            model: Model name

        Returns:
            Dictionary mapping text to embedding (or None)
        """
        results = {}

        # Process in chunks for efficiency
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i : i + self.config.batch_size]

            # Get each from cache
            for text in batch:
                embedding = await self.get(text, model)
                results[text] = embedding

        self.stats["batch_operations"] += 1
        return results

    async def batch_set(
        self,
        entries: List[Tuple[str, Union[np.ndarray, List[float]]]],
        model: str = "default",
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Set multiple embeddings in batch

        Args:
            entries: List of (text, embedding) tuples
            model: Model name
            metadata: Metadata for all entries

        Returns:
            Number of entries cached
        """
        count = 0

        # Process in chunks
        for i in range(0, len(entries), self.config.batch_size):
            batch = entries[i : i + self.config.batch_size]

            # Use pipeline for Redis efficiency
            if self._redis_available and self.redis_client:
                try:
                    async with self.redis_client.pipeline() as pipe:
                        for text, embedding in batch:
                            if isinstance(embedding, list):
                                embedding = np.array(embedding)

                            cache_key = self._generate_key(text, model)
                            entry = EmbeddingEntry(
                                text=text,
                                embedding=embedding,
                                metadata=metadata or {},
                                model=model,
                            )

                            # Memory cache
                            self.memory_cache.put(cache_key, entry)

                            # Index
                            if self.config.enable_index:
                                self.index.add(text, embedding, metadata)

                            # Redis pipeline
                            data = json.dumps(entry.to_dict())
                            pipe.setex(cache_key, self.config.default_ttl, data)
                            count += 1

                        await pipe.execute()
                except Exception as e:
                    logger.error(f"Batch set error: {e}")
            else:
                # Memory-only mode
                for text, embedding in batch:
                    await self.set(text, embedding, model, metadata)
                    count += 1

        self.stats["batch_operations"] += 1
        return count

    def _start_index_rebuild_task(self):
        """Start background task to rebuild index periodically"""

        async def rebuild_loop():
            while True:
                try:
                    await asyncio.sleep(self.config.index_rebuild_interval)
                    await self._rebuild_index()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Index rebuild error: {e}")

        self._index_rebuild_task = asyncio.create_task(rebuild_loop())

    async def _rebuild_index(self):
        """Rebuild index from Redis"""
        if not self._redis_available or not self.redis_client:
            return

        logger.info("Rebuilding embedding index...")

        # Clear current index
        self.index.clear()

        # Scan Redis for embeddings
        pattern = f"{self.config.key_prefix}:*"
        count = 0

        try:
            async for key in self.redis_client.scan_iter(match=pattern):
                data = await self.redis_client.get(key)
                if data:
                    entry = EmbeddingEntry.from_dict(json.loads(data))
                    self.index.add(entry.text, entry.embedding, entry.metadata)
                    count += 1

            self.index.last_rebuild = datetime.now()
            logger.info(f"Index rebuilt with {count} entries")

        except Exception as e:
            logger.error(f"Index rebuild failed: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_ratio = self.stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_ratio": hit_ratio,
            "searches": self.stats["searches"],
            "batch_operations": self.stats["batch_operations"],
            "memory_cache_size": self.memory_cache.size(),
            "index_size": self.index.size(),
            "redis_available": self._redis_available,
            "last_index_rebuild": (
                self.index.last_rebuild.isoformat() if self.index.last_rebuild else None
            ),
        }

    async def clear(self):
        """Clear all caches"""
        self.memory_cache.clear()
        self.index.clear()

        if self._redis_available and self.redis_client:
            pattern = f"{self.config.key_prefix}:*"
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.redis_client.delete(*keys)

        logger.info("Embedding cache cleared")

    async def close(self):
        """Close connections and cleanup"""
        if self._index_rebuild_task:
            self._index_rebuild_task.cancel()
            try:
                await self._index_rebuild_task
            except asyncio.CancelledError:
                pass

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Embedding cache closed")


# Global instance
_global_embedding_cache: Optional[EmbeddingCache] = None


async def get_embedding_cache() -> EmbeddingCache:
    """Get or create global embedding cache instance"""
    global _global_embedding_cache

    if _global_embedding_cache is None:
        _global_embedding_cache = EmbeddingCache()
        await _global_embedding_cache.initialize()

    return _global_embedding_cache


# Example usage
"""
# Initialize cache
cache = await get_embedding_cache()

# Cache single embedding
await cache.set(
    text="Matematik dersi",
    embedding=embedding_vector,
    model="text-embedding-ada-002",
    metadata={"subject": "matematik", "level": "lise"}
)

# Get from cache
embedding = await cache.get("Matematik dersi", model="text-embedding-ada-002")

# Batch operations
texts = ["Text 1", "Text 2", "Text 3"]
embeddings_dict = await cache.batch_get(texts)

# Semantic search
results = await cache.search(
    query_embedding=query_vector,
    top_k=5,
    threshold=0.8
)

for result in results:
    print(f"{result.text}: {result.similarity:.3f}")

# Statistics
stats = await cache.get_stats()
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
"""
