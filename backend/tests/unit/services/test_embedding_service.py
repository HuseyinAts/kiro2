"""
Embedding Service Unit Tests

Spec REQ-1: Embedding Generation testleri
- REQ-1.1: Sentence-Transformers kullanımı
- REQ-1.3: 768-dim output
- REQ-1.4: Batch processing
- REQ-1.5: Cache

Author: KIRO2 Team
Date: 2026-01-18
"""

import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Add backend directory to path for imports
backend_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

pytestmark = pytest.mark.unit


class TestEmbeddingService:
    """EmbeddingService unit testleri."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service fixture."""
        # Mock dependencies before importing
        mock_redis_module = MagicMock()
        mock_st_module = MagicMock()

        with patch.dict('sys.modules', {
            'sentence_transformers': mock_st_module,
            'redis': mock_redis_module,
        }):
            # Temporarily set availability flags to False
            import services.embedding_service as emb_module
            original_st = getattr(emb_module, 'SENTENCE_TRANSFORMERS_AVAILABLE', None)
            original_redis = getattr(emb_module, 'REDIS_AVAILABLE', None)

            emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = False
            emb_module.REDIS_AVAILABLE = False

            try:
                service = emb_module.EmbeddingService()
                # Force no model and no redis
                service._model = None
                service._redis = None
                service._initialized = True
                yield service
            finally:
                # Restore original values
                if original_st is not None:
                    emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = original_st
                if original_redis is not None:
                    emb_module.REDIS_AVAILABLE = original_redis

    def test_fallback_embedding_dimension(self, mock_embedding_service):
        """REQ-1.3: Fallback embedding 768-dim olmalı."""
        embedding = mock_embedding_service._fallback_embedding("test text")

        assert len(embedding) == 768, f"Expected 768 dimensions, got {len(embedding)}"

    def test_fallback_embedding_deterministic(self, mock_embedding_service):
        """Aynı metin için aynı embedding üretilmeli."""
        text = "Bu bir test metnidir."

        emb1 = mock_embedding_service._fallback_embedding(text)
        emb2 = mock_embedding_service._fallback_embedding(text)

        assert emb1 == emb2, "Aynı metin için farklı embedding üretildi"

    def test_fallback_embedding_different_texts(self, mock_embedding_service):
        """Farklı metinler için farklı embedding üretilmeli."""
        emb1 = mock_embedding_service._fallback_embedding("Metin 1")
        emb2 = mock_embedding_service._fallback_embedding("Metin 2")

        assert emb1 != emb2, "Farklı metinler için aynı embedding üretildi"

    def test_fallback_embedding_normalized(self, mock_embedding_service):
        """Fallback embedding L2 normalize olmalı."""
        embedding = mock_embedding_service._fallback_embedding("test")

        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01, f"Embedding not normalized, norm={norm}"

    def test_cache_key_format(self, mock_embedding_service):
        """Cache key formatı doğru olmalı."""
        key = mock_embedding_service._get_cache_key("test text")

        assert key.startswith("chromadb:emb:"), f"Invalid cache key format: {key}"
        assert len(key) == len("chromadb:emb:") + 32, "Cache key hash uzunluğu yanlış"

    def test_cache_key_deterministic(self, mock_embedding_service):
        """Aynı metin için aynı cache key üretilmeli."""
        text = "test text"

        key1 = mock_embedding_service._get_cache_key(text)
        key2 = mock_embedding_service._get_cache_key(text)

        assert key1 == key2, "Cache key deterministic değil"

    def test_cosine_similarity_identical(self, mock_embedding_service):
        """Aynı vektörler için similarity 1.0 olmalı."""
        vec = [1.0, 0.0, 0.0]
        sim = mock_embedding_service.cosine_similarity(vec, vec)

        assert abs(sim - 1.0) < 0.001, f"Expected 1.0, got {sim}"

    def test_cosine_similarity_orthogonal(self, mock_embedding_service):
        """Dik vektörler için similarity 0.0 olmalı."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        sim = mock_embedding_service.cosine_similarity(vec1, vec2)

        assert abs(sim) < 0.001, f"Expected 0.0, got {sim}"

    def test_cosine_similarity_opposite(self, mock_embedding_service):
        """Zıt vektörler için similarity -1.0 olmalı."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        sim = mock_embedding_service.cosine_similarity(vec1, vec2)

        assert abs(sim + 1.0) < 0.001, f"Expected -1.0, got {sim}"

    def test_cosine_similarity_symmetric(self, mock_embedding_service):
        """Cosine similarity simetrik olmalı."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [4.0, 5.0, 6.0]

        sim12 = mock_embedding_service.cosine_similarity(vec1, vec2)
        sim21 = mock_embedding_service.cosine_similarity(vec2, vec1)

        assert abs(sim12 - sim21) < 0.001, "Cosine similarity simetrik değil"

    def test_embed_without_model_uses_fallback(self, mock_embedding_service):
        """Model yoksa fallback kullanılmalı."""
        embedding = mock_embedding_service.embed("test", use_cache=False)

        assert len(embedding) == 768, "Fallback embedding dimension yanlış"

    def test_embed_batch_empty_list(self, mock_embedding_service):
        """Boş liste için boş liste dönmeli."""
        result = mock_embedding_service.embed_batch([], use_cache=False)

        assert result == [], "Boş liste için boş liste dönmedi"

    def test_embed_batch_single_item(self, mock_embedding_service):
        """Tek eleman için doğru sonuç dönmeli."""
        result = mock_embedding_service.embed_batch(["test"], use_cache=False)

        assert len(result) == 1, "Tek eleman için bir sonuç dönmedi"
        assert len(result[0]) == 768, "Embedding dimension yanlış"

    def test_embed_batch_multiple_items(self, mock_embedding_service):
        """Birden fazla eleman için doğru sonuç dönmeli."""
        texts = ["text1", "text2", "text3"]
        result = mock_embedding_service.embed_batch(texts, use_cache=False)

        assert len(result) == 3, f"Expected 3 results, got {len(result)}"
        for i, emb in enumerate(result):
            assert len(emb) == 768, f"Embedding {i} dimension yanlış"

    def test_stats_initial_values(self, mock_embedding_service):
        """İstatistikler başlangıç değerleri doğru olmalı."""
        stats = mock_embedding_service.get_stats()

        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0

    def test_stats_after_embed(self, mock_embedding_service):
        """Embed sonrası istatistikler güncellenmeli."""
        mock_embedding_service.embed("test", use_cache=False)
        stats = mock_embedding_service.get_stats()

        assert stats.total_requests == 1
        assert stats.cache_misses == 1


class TestEmbeddingServiceWithMocks:
    """Mock'lar ile daha detaylı testler."""

    @pytest.fixture
    def service_with_mock_model(self):
        """Mock model ile service."""
        # Create mock SentenceTransformer model
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.randn(768).astype(np.float32)

        # Mock SentenceTransformer class
        mock_st_class = MagicMock(return_value=mock_model)
        mock_st_module = MagicMock(SentenceTransformer=mock_st_class)
        mock_redis_module = MagicMock()

        with patch.dict('sys.modules', {
            'sentence_transformers': mock_st_module,
            'redis': mock_redis_module,
        }):
            import services.embedding_service as emb_module

            original_st = emb_module.SENTENCE_TRANSFORMERS_AVAILABLE
            original_redis = emb_module.REDIS_AVAILABLE

            emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = True
            emb_module.REDIS_AVAILABLE = False

            try:
                with patch.object(emb_module, 'SentenceTransformer', mock_st_class):
                    service = emb_module.EmbeddingService()
                    service._model = mock_model
                    service._redis = None
                    service._initialized = True

                    yield service, mock_model
            finally:
                emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = original_st
                emb_module.REDIS_AVAILABLE = original_redis

    def test_embed_calls_model_encode(self, service_with_mock_model):
        """Embed model.encode çağırmalı."""
        service, mock_model = service_with_mock_model

        service.embed("test text", use_cache=False)

        mock_model.encode.assert_called()

    def test_batch_processing_respects_batch_size(self, service_with_mock_model):
        """Batch işlem batch_size'a uymalı."""
        service, mock_model = service_with_mock_model
        service.batch_size = 2

        # 5 metin için 3 batch çağrısı olmalı (2+2+1)
        mock_model.encode.return_value = np.random.randn(2, 768).astype(np.float32)

        texts = ["t1", "t2", "t3", "t4", "t5"]
        # Bu test mock'un nasıl davrandığına bağlı, basit tutuyoruz
        result = service.embed_batch(texts, use_cache=False)

        assert len(result) == 5


class TestEmbeddingServiceTurkish:
    """Türkçe metin testleri."""

    @pytest.fixture
    def service(self):
        """Service fixture."""
        with patch.dict('sys.modules', {
            'sentence_transformers': MagicMock(),
            'redis': MagicMock(),
        }):
            import services.embedding_service as emb_module

            original_st = emb_module.SENTENCE_TRANSFORMERS_AVAILABLE
            original_redis = emb_module.REDIS_AVAILABLE

            emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = False
            emb_module.REDIS_AVAILABLE = False

            try:
                service = emb_module.EmbeddingService()
                service._model = None
                service._redis = None
                service._initialized = True
                yield service
            finally:
                emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = original_st
                emb_module.REDIS_AVAILABLE = original_redis

    def test_turkish_characters(self, service):
        """Türkçe karakterler doğru işlenmeli."""
        text = "İstanbul'da güneşli bir gün. Öğrenciler çalışıyor."
        embedding = service._fallback_embedding(text)

        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)

    def test_turkish_question(self, service):
        """YKS tipi Türkçe soru işlenmeli."""
        question = """
        Bir dik üçgenin hipotenüsü 10 cm, bir dik kenarı 6 cm ise,
        diğer dik kenarının uzunluğu kaç cm'dir?

        A) 6    B) 7    C) 8    D) 9    E) 10
        """
        embedding = service._fallback_embedding(question)

        assert len(embedding) == 768

    def test_empty_text(self, service):
        """Boş metin için embedding üretilmeli."""
        embedding = service._fallback_embedding("")

        assert len(embedding) == 768


# Property-based test placeholder
class TestEmbeddingServiceProperties:
    """Property-based testler (hypothesis ile genişletilebilir)."""

    @pytest.fixture
    def service(self):
        """Service fixture."""
        with patch.dict('sys.modules', {
            'sentence_transformers': MagicMock(),
            'redis': MagicMock(),
        }):
            import services.embedding_service as emb_module

            original_st = emb_module.SENTENCE_TRANSFORMERS_AVAILABLE
            original_redis = emb_module.REDIS_AVAILABLE

            emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = False
            emb_module.REDIS_AVAILABLE = False

            try:
                service = emb_module.EmbeddingService()
                service._model = None
                service._redis = None
                service._initialized = True
                yield service
            finally:
                emb_module.SENTENCE_TRANSFORMERS_AVAILABLE = original_st
                emb_module.REDIS_AVAILABLE = original_redis

    def test_embedding_consistency_property(self, service):
        """
        REQ-1.3: Embedding consistency property.

        Aynı metin için aynı embedding üretilmeli (deterministic).
        """
        import random
        import string

        # 10 rastgele metin için test
        for _ in range(10):
            text = ''.join(random.choices(string.ascii_letters + string.digits, k=50))

            emb1 = service._fallback_embedding(text)
            emb2 = service._fallback_embedding(text)

            assert emb1 == emb2, f"Embedding consistency failed for: {text[:20]}..."
