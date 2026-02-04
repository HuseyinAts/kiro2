"""
Phase 2: RAG Service Comprehensive Tests
Target: 0% → 35%+ coverage for core/rag_service.py (500+ lines)
Focus: Document retrieval, vector search, embedding, caching, performance optimization
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRAGServiceCore:
    """Test RAG Service core functionality"""

    def test_rag_service_creation(self):
        """Test RAGService instantiation"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService(persist_directory="./test_vector_db")

                assert service.persist_directory == "./test_vector_db"
                assert service.embeddings is not None
                assert service.vector_store is not None
                assert service.text_splitter is not None
                assert isinstance(service._search_cache, dict)
                assert isinstance(service._cache_ttl, int)
                assert isinstance(service._max_cache_size, int)
                assert isinstance(service._batch_size, int)

        except ImportError:
            pytest.skip("RAGService not available")

    def test_rag_service_default_settings(self):
        """Test RAGService default settings"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                with patch.dict(os.environ, {}, clear=True):
                    service = RAGService()

                    assert service.persist_directory == "./vector_db"
                    assert service._cache_ttl == 1800  # 30 minutes default
                    assert service._max_cache_size == 500  # default
                    assert service._batch_size == 50  # default

        except ImportError:
            pytest.skip("RAGService not available")

    def test_rag_service_environment_settings(self):
        """Test RAGService with environment variables"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                env_vars = {
                    "RAG_CACHE_TTL": "3600",
                    "RAG_MAX_CACHE_SIZE": "1000",
                    "RAG_BATCH_SIZE": "100",
                }

                with patch.dict(os.environ, env_vars):
                    service = RAGService()

                    assert service._cache_ttl == 3600
                    assert service._max_cache_size == 1000
                    assert service._batch_size == 100

        except ImportError:
            pytest.skip("RAGService not available")


class TestSimpleEmbeddings:
    """Test SimpleEmbeddings fallback implementation"""

    def test_simple_embeddings_creation(self):
        """Test SimpleEmbeddings can be created"""
        try:
            with patch("core.rag_service.logger"):
                # Mock HuggingFace embeddings to fail and trigger fallback
                with patch(
                    "core.rag_service.HuggingFaceEmbeddings",
                    side_effect=Exception("Mock failure"),
                ):
                    from core.rag_service import RAGService

                    service = RAGService()

                    # Should use SimpleEmbeddings fallback
                    assert service.embeddings is not None
                    assert hasattr(service.embeddings, "embed_documents")
                    assert hasattr(service.embeddings, "embed_query")

        except ImportError:
            pytest.skip("RAGService not available")

    def test_simple_embeddings_functionality(self):
        """Test SimpleEmbeddings embedding functionality"""
        try:
            with patch("core.rag_service.logger"):
                with patch(
                    "core.rag_service.HuggingFaceEmbeddings",
                    side_effect=Exception("Mock failure"),
                ):
                    from core.rag_service import RAGService

                    service = RAGService()
                    embeddings = service.embeddings

                    # Test embed_documents
                    texts = ["test document 1", "test document 2"]
                    doc_embeddings = embeddings.embed_documents(texts)

                    assert isinstance(doc_embeddings, list)
                    assert len(doc_embeddings) == 2
                    assert all(isinstance(emb, list) for emb in doc_embeddings)
                    assert all(
                        len(emb) == 48 for emb in doc_embeddings
                    )  # SHA384 = 48 bytes

                    # Test embed_query
                    query = "test query"
                    query_embedding = embeddings.embed_query(query)

                    assert isinstance(query_embedding, list)
                    assert len(query_embedding) == 48

                    # Same text should produce same embedding
                    same_embedding = embeddings.embed_query(query)
                    assert query_embedding == same_embedding

                    # Different text should produce different embedding
                    different_embedding = embeddings.embed_query("different text")
                    assert query_embedding != different_embedding

        except ImportError:
            pytest.skip("RAGService not available")


class TestSimpleVectorStore:
    """Test SimpleVectorStore fallback implementation"""

    def test_simple_vector_store_creation(self):
        """Test SimpleVectorStore functionality"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                vector_store = service.vector_store

                assert hasattr(vector_store, "documents")
                assert hasattr(vector_store, "add_texts")
                assert hasattr(vector_store, "similarity_search")
                assert hasattr(vector_store, "asimilarity_search")
                assert isinstance(vector_store.documents, list)
                assert len(vector_store.documents) == 0

        except ImportError:
            pytest.skip("RAGService not available")

    def test_simple_vector_store_add_texts(self):
        """Test SimpleVectorStore add_texts functionality"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                vector_store = service.vector_store

                # Test adding texts without metadata
                texts = ["Document 1 content", "Document 2 content"]
                ids = vector_store.add_texts(texts)

                assert isinstance(ids, list)
                assert len(ids) == 2
                assert len(vector_store.documents) == 2

                # Test adding texts with metadata
                metadatas = [{"source": "file1.txt"}, {"source": "file2.txt"}]
                texts2 = ["Document 3 content"]
                ids2 = vector_store.add_texts(texts2, metadatas=[metadatas[0]])

                assert len(vector_store.documents) == 3
                assert vector_store.documents[2]["metadata"]["source"] == "file1.txt"

        except ImportError:
            pytest.skip("RAGService not available")

    def test_simple_vector_store_similarity_search(self):
        """Test SimpleVectorStore similarity search"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                vector_store = service.vector_store

                # Add some test documents
                texts = [
                    "AI and machine learning",
                    "Python programming",
                    "Web development",
                ]
                metadatas = [
                    {"topic": "AI"},
                    {"topic": "programming"},
                    {"topic": "web"},
                ]
                vector_store.add_texts(texts, metadatas)

                # Test similarity search
                results = vector_store.similarity_search("machine learning", k=2)

                assert isinstance(results, list)
                assert len(results) <= 2
                assert all(hasattr(doc, "page_content") for doc in results)
                assert all(hasattr(doc, "metadata") for doc in results)

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_simple_vector_store_async_similarity_search(self):
        """Test SimpleVectorStore async similarity search"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                vector_store = service.vector_store

                # Add some test documents
                texts = ["async document 1", "async document 2"]
                vector_store.add_texts(texts)

                # Test async similarity search
                results = await vector_store.asimilarity_search("async", k=1)

                assert isinstance(results, list)
                assert len(results) <= 1

        except ImportError:
            pytest.skip("RAGService not available")


class TestTextSplitter:
    """Test text splitter functionality"""

    def test_text_splitter_initialization(self):
        """Test text splitter is properly initialized"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                text_splitter = service.text_splitter

                assert text_splitter is not None
                assert hasattr(text_splitter, "split_text")
                assert text_splitter._chunk_size == 1000
                assert text_splitter._chunk_overlap == 200

        except ImportError:
            pytest.skip("RAGService not available")

    def test_text_splitter_functionality(self):
        """Test text splitter splitting functionality"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                text_splitter = service.text_splitter

                # Test with short text (shouldn't be split)
                short_text = "This is a short text that should not be split."
                chunks = text_splitter.split_text(short_text)

                assert isinstance(chunks, list)
                assert len(chunks) == 1
                assert chunks[0] == short_text

                # Test with long text (should be split)
                long_text = "This is a very long text. " * 100  # > 1000 chars
                chunks = text_splitter.split_text(long_text)

                assert isinstance(chunks, list)
                assert len(chunks) > 1
                assert all(isinstance(chunk, str) for chunk in chunks)

        except ImportError:
            pytest.skip("RAGService not available")


class TestCacheGeneration:
    """Test cache key generation and management"""

    def test_generate_search_cache_key(self):
        """Test search cache key generation"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Test basic cache key generation
                key1 = service._generate_search_cache_key("test query", 5)
                key2 = service._generate_search_cache_key("test query", 5)

                assert isinstance(key1, str)
                assert isinstance(key2, str)
                assert key1 == key2  # Same parameters should give same key
                assert len(key1) == 32  # MD5 hash length

                # Test different parameters give different keys
                key3 = service._generate_search_cache_key("different query", 5)
                key4 = service._generate_search_cache_key("test query", 10)

                assert key1 != key3
                assert key1 != key4

        except ImportError:
            pytest.skip("RAGService not available")

    def test_generate_search_cache_key_with_filter(self):
        """Test search cache key generation with filter"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Test cache key with filter
                filter_dict = {"category": "science", "year": 2023}
                key1 = service._generate_search_cache_key("query", 5, filter_dict)
                key2 = service._generate_search_cache_key("query", 5, filter_dict)

                assert key1 == key2

                # Test different filter gives different key
                different_filter = {"category": "math", "year": 2023}
                key3 = service._generate_search_cache_key("query", 5, different_filter)

                assert key1 != key3

        except ImportError:
            pytest.skip("RAGService not available")


class TestPreprocessing:
    """Test text preprocessing functionality"""

    def test_preprocess_text(self):
        """Test text preprocessing method"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Test basic preprocessing
                text = "  Hello   World  \n\n  "
                processed = service._preprocess_text(text)

                assert processed == "hello world"

                # Test with mixed case and extra spaces
                text2 = "   THIS   is   A   TEST   "
                processed2 = service._preprocess_text(text2)

                assert processed2 == "this is a test"

                # Test caching (same input should be cached)
                processed3 = service._preprocess_text(text)
                assert processed3 == processed

        except ImportError:
            pytest.skip("RAGService not available")


class TestRedisIntegration:
    """Test Redis integration for caching"""

    @pytest.mark.asyncio
    async def test_redis_connection_test(self):
        """Test Redis connection testing"""
        try:
            with patch("core.rag_service.logger"):
                with patch("core.rag_service.REDIS_AVAILABLE", True):
                    from core.rag_service import RAGService

                    service = RAGService()

                    # Mock Redis client
                    mock_redis = AsyncMock()
                    service._redis_client = mock_redis

                    # Test successful connection
                    mock_redis.ping = AsyncMock()
                    await service._test_redis_connection()
                    mock_redis.ping.assert_called_once()

                    # Test failed connection
                    mock_redis.ping = AsyncMock(
                        side_effect=Exception("Connection failed")
                    )
                    await service._test_redis_connection()
                    assert service._redis_client is None

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_cached_search_results_redis(self):
        """Test cached search results with Redis"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Mock Redis client
                mock_redis = AsyncMock()
                service._redis_client = mock_redis

                cache_key = "test_cache_key"
                test_results = [{"content": "test", "score": 0.9}]

                # Test setting cache
                mock_redis.setex = AsyncMock()
                await service._set_cached_search_results(cache_key, test_results)
                mock_redis.setex.assert_called_once()

                # Test getting cache
                mock_redis.get = AsyncMock(return_value=json.dumps(test_results))
                cached_results = await service._get_cached_search_results(cache_key)

                assert cached_results == test_results

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_cached_search_results_memory_fallback(self):
        """Test cached search results with memory fallback"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                service._redis_client = None  # No Redis

                cache_key = "memory_cache_key"
                test_results = [{"content": "memory test", "score": 0.8}]

                # Test setting cache in memory
                await service._set_cached_search_results(cache_key, test_results)
                assert cache_key in service._search_cache

                # Test getting cache from memory
                cached_results = await service._get_cached_search_results(cache_key)
                assert cached_results == test_results

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_memory_cache_lru_eviction(self):
        """Test memory cache LRU eviction"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                service._redis_client = None  # No Redis
                service._max_cache_size = 2  # Small cache for testing

                # Add items to cache
                test_results1 = [{"content": "test1"}]
                test_results2 = [{"content": "test2"}]
                test_results3 = [{"content": "test3"}]

                await service._set_cached_search_results("key1", test_results1)
                await service._set_cached_search_results("key2", test_results2)

                assert len(service._search_cache) == 2

                # Add third item (should evict oldest)
                await service._set_cached_search_results("key3", test_results3)

                assert len(service._search_cache) == 2
                assert "key3" in service._search_cache

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """Test cache TTL expiration"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()
                service._redis_client = None  # No Redis
                service._cache_ttl = 1  # 1 second TTL for testing

                cache_key = "ttl_test_key"
                test_results = [{"content": "ttl test"}]

                # Set cache
                await service._set_cached_search_results(cache_key, test_results)

                # Should be available immediately
                cached = await service._get_cached_search_results(cache_key)
                assert cached == test_results

                # Wait for expiration and test
                await asyncio.sleep(1.1)  # Wait longer than TTL
                expired_cached = await service._get_cached_search_results(cache_key)
                assert expired_cached is None
                assert cache_key not in service._search_cache  # Should be removed

        except ImportError:
            pytest.skip("RAGService not available")


class TestDocumentManagement:
    """Test document addition and management"""

    @pytest.mark.asyncio
    async def test_add_documents_basic(self):
        """Test basic document addition"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Mock vector store
                mock_vector_store = Mock()
                mock_vector_store.add_documents = Mock(return_value=["id1", "id2"])
                mock_vector_store.persist = Mock()
                service.vector_store = mock_vector_store

                documents = [
                    {
                        "content": "Short document content",
                        "metadata": {"source": "test1.txt"},
                    },
                    {
                        "content": "Another short document",
                        "metadata": {"source": "test2.txt"},
                    },
                ]

                result = await service.add_documents(documents)

                assert result["success"] is True
                assert "2 doküman eklendi" in result["message"]
                assert "document_ids" in result
                mock_vector_store.add_documents.assert_called_once()
                mock_vector_store.persist.assert_called_once()

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_add_documents_with_chunking(self):
        """Test document addition with text chunking"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Mock vector store
                mock_vector_store = Mock()
                mock_vector_store.add_documents = Mock(
                    return_value=["chunk1", "chunk2", "chunk3"]
                )
                mock_vector_store.persist = Mock()
                service.vector_store = mock_vector_store

                # Create a long document that will be chunked
                long_content = (
                    "This is a very long document. " * 100
                )  # > 1000 characters
                documents = [
                    {"content": long_content, "metadata": {"source": "long_doc.txt"}}
                ]

                result = await service.add_documents(documents)

                assert result["success"] is True
                mock_vector_store.add_documents.assert_called_once()

                # Check that multiple chunks were created
                call_args = mock_vector_store.add_documents.call_args[0][0]
                assert len(call_args) > 1  # Should be chunked into multiple documents

                # Check chunk metadata
                for i, doc in enumerate(call_args):
                    assert "chunk_index" in doc.metadata
                    assert doc.metadata["source"] == "long_doc.txt"

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_add_documents_metadata_filtering(self):
        """Test document addition with metadata filtering"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Mock vector store
                mock_vector_store = Mock()
                mock_vector_store.add_documents = Mock(return_value=["id1"])
                mock_vector_store.persist = Mock()
                service.vector_store = mock_vector_store

                documents = [
                    {
                        "content": "Test document",
                        "metadata": {
                            "source": "test.txt",
                            "category": "science",
                            "private_field": "should_be_filtered",
                            "date": "2023-01-01",
                        },
                    }
                ]

                # Only allow certain metadata fields
                metadata_fields = ["source", "category"]
                result = await service.add_documents(documents, metadata_fields)

                assert result["success"] is True

                # Check that metadata was filtered
                call_args = mock_vector_store.add_documents.call_args[0][0]
                doc_metadata = call_args[0].metadata

                assert "source" in doc_metadata
                assert "category" in doc_metadata
                assert "private_field" not in doc_metadata
                assert "date" not in doc_metadata

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_add_documents_empty_list(self):
        """Test adding empty document list"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                result = await service.add_documents([])

                assert result["success"] is False
                assert "Eklenecek doküman bulunamadı" in result["message"]

        except ImportError:
            pytest.skip("RAGService not available")

    @pytest.mark.asyncio
    async def test_add_documents_error_handling(self):
        """Test error handling in document addition"""
        try:
            with patch("core.rag_service.logger"):
                from core.rag_service import RAGService

                service = RAGService()

                # Mock vector store to raise an exception
                mock_vector_store = Mock()
                mock_vector_store.add_documents = Mock(
                    side_effect=Exception("Vector store error")
                )
                service.vector_store = mock_vector_store

                documents = [{"content": "Test document"}]
                result = await service.add_documents(documents)

                assert result["success"] is False
                assert "error" in result
                assert "Vector store error" in result["error"]

        except ImportError:
            pytest.skip("RAGService not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
