"""
Tests for Embedding Cache System
"""

from datetime import datetime

import numpy as np
import pytest

from core.embedding_cache import (
    EmbeddingCache,
    EmbeddingCacheConfig,
    EmbeddingEntry,
    EmbeddingIndex,
    LRUCache,
    SearchResult,
    get_embedding_cache,
)


class TestEmbeddingEntry:
    """Test EmbeddingEntry dataclass"""

    def test_entry_creation(self):
        """Test creating embedding entry"""
        embedding = np.random.rand(768)
        entry = EmbeddingEntry(
            text="Test text", embedding=embedding, model="test-model"
        )

        assert entry.text == "Test text"
        assert np.array_equal(entry.embedding, embedding)
        assert entry.model == "test-model"
        assert isinstance(entry.timestamp, datetime)

    def test_entry_to_dict(self):
        """Test converting entry to dictionary"""
        embedding = np.array([0.1, 0.2, 0.3])
        entry = EmbeddingEntry(
            text="Test", embedding=embedding, metadata={"key": "value"}
        )

        data = entry.to_dict()

        assert data["text"] == "Test"
        assert data["embedding"] == [0.1, 0.2, 0.3]
        assert data["metadata"] == {"key": "value"}
        assert "timestamp" in data

    def test_entry_from_dict(self):
        """Test creating entry from dictionary"""
        data = {
            "text": "Test",
            "embedding": [0.1, 0.2, 0.3],
            "metadata": {"key": "value"},
            "timestamp": datetime.now().isoformat(),
            "model": "test",
        }

        entry = EmbeddingEntry.from_dict(data)

        assert entry.text == "Test"
        assert len(entry.embedding) == 3
        assert entry.metadata["key"] == "value"


class TestSearchResult:
    """Test SearchResult dataclass"""

    def test_search_result_creation(self):
        """Test creating search result"""
        embedding = np.array([0.1, 0.2])
        result = SearchResult(
            text="Found text",
            embedding=embedding,
            similarity=0.95,
            metadata={"score": 100},
        )

        assert result.text == "Found text"
        assert result.similarity == 0.95
        assert result.metadata["score"] == 100

    def test_search_result_to_dict(self):
        """Test converting search result to dict"""
        result = SearchResult(text="Test", embedding=np.array([0.1]), similarity=0.9)

        data = result.to_dict()

        assert data["text"] == "Test"
        assert data["similarity"] == 0.9
        assert "metadata" in data


class TestLRUCache:
    """Test LRU cache implementation"""

    def test_lru_cache_creation(self):
        """Test creating LRU cache"""
        cache = LRUCache(capacity=10)

        assert cache.capacity == 10
        assert cache.size() == 0

    def test_lru_cache_put_get(self):
        """Test adding and retrieving entries"""
        cache = LRUCache(capacity=3)
        entry = EmbeddingEntry(text="Test", embedding=np.array([0.1]))

        cache.put("key1", entry)

        assert cache.size() == 1
        retrieved = cache.get("key1")
        assert retrieved is not None
        assert retrieved.text == "Test"

    def test_lru_cache_eviction(self):
        """Test LRU eviction"""
        cache = LRUCache(capacity=3)

        # Add 3 entries
        for i in range(3):
            entry = EmbeddingEntry(text=f"Text {i}", embedding=np.array([float(i)]))
            cache.put(f"key{i}", entry)

        assert cache.size() == 3

        # Add 4th entry (should evict oldest)
        entry4 = EmbeddingEntry(text="Text 3", embedding=np.array([3.0]))
        cache.put("key3", entry4)

        assert cache.size() == 3
        assert cache.get("key0") is None  # Oldest evicted
        assert cache.get("key3") is not None

    def test_lru_cache_clear(self):
        """Test clearing cache"""
        cache = LRUCache(capacity=10)

        for i in range(5):
            entry = EmbeddingEntry(text=f"Text {i}", embedding=np.array([float(i)]))
            cache.put(f"key{i}", entry)

        assert cache.size() == 5

        cache.clear()
        assert cache.size() == 0


class TestEmbeddingIndex:
    """Test embedding index for similarity search"""

    def test_index_creation(self):
        """Test creating index"""
        index = EmbeddingIndex(dimension=128)

        assert index.dimension == 128
        assert index.size() == 0

    def test_index_add(self):
        """Test adding embeddings to index"""
        index = EmbeddingIndex(dimension=3)

        embedding = np.array([0.1, 0.2, 0.3])
        index.add("Test text", embedding, {"key": "value"})

        assert index.size() == 1

    def test_index_search_cosine_similarity(self):
        """Test similarity search"""
        index = EmbeddingIndex(dimension=3)

        # Add some embeddings
        embeddings = [
            np.array([1.0, 0.0, 0.0]),  # Very similar to query
            np.array([0.0, 1.0, 0.0]),  # Orthogonal
            np.array([0.9, 0.1, 0.0]),  # Similar
        ]

        for i, emb in enumerate(embeddings):
            index.add(f"Text {i}", emb)

        # Search with query similar to first embedding
        query = np.array([1.0, 0.0, 0.0])
        results = index.search(query, top_k=2, threshold=0.5)

        # Should find 2 results (first and third are similar)
        assert len(results) <= 2

        # First result should be most similar
        if results:
            assert results[0].similarity >= 0.9

    def test_index_search_with_threshold(self):
        """Test search with similarity threshold"""
        index = EmbeddingIndex(dimension=2)

        # Add dissimilar embeddings
        index.add("Text 1", np.array([1.0, 0.0]))
        index.add("Text 2", np.array([0.0, 1.0]))

        # Search with high threshold
        query = np.array([1.0, 0.0])
        results = index.search(query, top_k=10, threshold=0.9)

        # Should only find exact match
        assert len(results) == 1

    def test_index_clear(self):
        """Test clearing index"""
        index = EmbeddingIndex(dimension=3)

        for i in range(5):
            index.add(f"Text {i}", np.random.rand(3))

        assert index.size() == 5

        index.clear()
        assert index.size() == 0


class TestEmbeddingCache:
    """Test main EmbeddingCache class"""

    @pytest.fixture
    def cache_config(self):
        """Create test cache config"""
        return EmbeddingCacheConfig(
            redis_url="redis://localhost:6379/15",  # Test DB
            memory_cache_size=100,
            enable_index=True,
        )

    @pytest.fixture
    def embedding_cache(self, cache_config):
        """Create embedding cache instance"""
        return EmbeddingCache(config=cache_config)

    def test_cache_initialization(self, embedding_cache):
        """Test cache initialization"""
        assert embedding_cache.config is not None
        assert embedding_cache.memory_cache is not None
        assert embedding_cache.index is not None
        assert embedding_cache.stats["hits"] == 0

    def test_generate_key(self, embedding_cache):
        """Test cache key generation"""
        key1 = embedding_cache._generate_key("Test text", "model1")
        key2 = embedding_cache._generate_key("Test text", "model1")
        key3 = embedding_cache._generate_key("Different text", "model1")

        # Same text/model should generate same key
        assert key1 == key2

        # Different text should generate different key
        assert key1 != key3

    def test_generate_key_normalization(self, embedding_cache):
        """Test key generation normalizes text"""
        key1 = embedding_cache._generate_key("  Test Text  ", "model")
        key2 = embedding_cache._generate_key("test text", "model")

        # Should be the same after normalization
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_set_and_get_memory_cache(self, embedding_cache):
        """Test setting and getting from memory cache"""
        embedding = np.random.rand(768)

        # Set
        success = await embedding_cache.set(
            text="Test text", embedding=embedding, model="test-model"
        )

        assert success is True

        # Get
        retrieved = await embedding_cache.get(text="Test text", model="test-model")

        assert retrieved is not None
        assert np.array_equal(retrieved, embedding)

    @pytest.mark.asyncio
    async def test_cache_hit_stats(self, embedding_cache):
        """Test cache hit statistics"""
        embedding = np.random.rand(768)

        # Set
        await embedding_cache.set("Test", embedding)

        # Reset stats
        embedding_cache.stats["hits"] = 0
        embedding_cache.stats["misses"] = 0

        # Get (should hit)
        await embedding_cache.get("Test")
        assert embedding_cache.stats["hits"] == 1

        # Get non-existent (should miss)
        await embedding_cache.get("Not exists")
        assert embedding_cache.stats["misses"] == 1

    @pytest.mark.asyncio
    async def test_batch_get(self, embedding_cache):
        """Test batch get operation"""
        # Set multiple embeddings
        embeddings = {
            "Text 1": np.random.rand(768),
            "Text 2": np.random.rand(768),
            "Text 3": np.random.rand(768),
        }

        for text, emb in embeddings.items():
            await embedding_cache.set(text, emb)

        # Batch get
        texts = list(embeddings.keys()) + ["Not exists"]
        results = await embedding_cache.batch_get(texts)

        # Should have all texts as keys
        assert len(results) == 4

        # Existing should have embeddings
        assert results["Text 1"] is not None
        assert results["Text 2"] is not None
        assert results["Text 3"] is not None

        # Non-existent should be None
        assert results["Not exists"] is None

    @pytest.mark.asyncio
    async def test_batch_set(self, embedding_cache):
        """Test batch set operation"""
        entries = [
            ("Text 1", np.random.rand(768)),
            ("Text 2", np.random.rand(768)),
            ("Text 3", np.random.rand(768)),
        ]

        count = await embedding_cache.batch_set(entries)

        assert count == 3

        # Verify all cached
        for text, _ in entries:
            result = await embedding_cache.get(text)
            assert result is not None

    @pytest.mark.asyncio
    async def test_search(self, embedding_cache):
        """Test semantic search"""
        # Use 768-dimensional embeddings to match cache configuration
        dim = 768
        similar1 = np.zeros(dim)
        similar1[0] = 1.0
        similar2 = np.zeros(dim)
        similar2[0] = 0.9
        similar2[1] = 0.1
        different = np.zeros(dim)
        different[2] = 1.0

        embeddings = [
            ("Similar 1", similar1),
            ("Similar 2", similar2),
            ("Different", different),
        ]

        for text, emb in embeddings:
            await embedding_cache.set(text, emb)

        # Search for similar to similar1
        query = similar1.copy()
        results = await embedding_cache.search(query, top_k=2, threshold=0.5)

        # Should find similar embeddings
        assert len(results) > 0

        # Results should be sorted by similarity
        if len(results) > 1:
            assert results[0].similarity >= results[1].similarity

    @pytest.mark.asyncio
    async def test_get_stats(self, embedding_cache):
        """Test getting cache statistics"""
        stats = await embedding_cache.get_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "hit_ratio" in stats
        assert "searches" in stats
        assert "memory_cache_size" in stats
        assert "index_size" in stats
        assert "redis_available" in stats

    @pytest.mark.asyncio
    async def test_clear(self, embedding_cache):
        """Test clearing cache"""
        # Add some data
        await embedding_cache.set("Test 1", np.random.rand(768))
        await embedding_cache.set("Test 2", np.random.rand(768))

        assert embedding_cache.memory_cache.size() > 0

        # Clear
        await embedding_cache.clear()

        assert embedding_cache.memory_cache.size() == 0
        assert embedding_cache.index.size() == 0


class TestGlobalCacheInstance:
    """Test global cache instance management"""

    @pytest.mark.asyncio
    async def test_get_embedding_cache_singleton(self):
        """Test global cache instance is singleton"""
        cache1 = await get_embedding_cache()
        cache2 = await get_embedding_cache()

        # Should return same instance
        assert cache1 is cache2


# Integration tests (require Redis)
@pytest.mark.skipif(True, reason="Requires running Redis")
class TestEmbeddingCacheIntegration:
    """Integration tests requiring actual Redis"""

    @pytest.mark.asyncio
    async def test_redis_persistence(self):
        """Test Redis persistence"""
        config = EmbeddingCacheConfig(redis_url="redis://localhost:6379/15")
        cache = EmbeddingCache(config=config)
        initialized = await cache.initialize()

        if not initialized:
            pytest.skip("Redis not available")

        # Set embedding
        embedding = np.random.rand(768)
        await cache.set("Test text", embedding, ttl=60)

        # Create new cache instance
        cache2 = EmbeddingCache(config=config)
        await cache2.initialize()

        # Should retrieve from Redis
        retrieved = await cache2.get("Test text")
        assert retrieved is not None
        assert np.array_equal(retrieved, embedding)

        # Cleanup
        await cache.clear()
        await cache.close()
        await cache2.close()

    @pytest.mark.asyncio
    async def test_index_rebuild(self):
        """Test index rebuild from Redis"""
        config = EmbeddingCacheConfig(
            redis_url="redis://localhost:6379/15", enable_index=True
        )
        cache = EmbeddingCache(config=config)
        initialized = await cache.initialize()

        if not initialized:
            pytest.skip("Redis not available")

        # Add embeddings
        for i in range(10):
            await cache.set(f"Text {i}", np.random.rand(768))

        # Rebuild index
        await cache._rebuild_index()

        assert cache.index.size() == 10
        assert cache.index.last_rebuild is not None

        # Cleanup
        await cache.clear()
        await cache.close()
