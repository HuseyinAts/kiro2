"""
Semantic Search API Unit Tests

Spec REQ-3: Semantic Question Search testleri
- REQ-3.1: Query embedding
- REQ-3.2: Top-k search
- REQ-3.3: Similarity threshold
- REQ-3.4: Metadata filtering
- REQ-3.5: MMR diversity
- REQ-3.6: Hybrid ranking

Author: KIRO2 Team
Date: 2026-01-18
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Mock chromadb before import to avoid Windows directory creation issues
sys.modules.setdefault('chromadb', MagicMock())
sys.modules.setdefault('chromadb.config', MagicMock())


class TestSearchRequest:
    """SearchRequest model testleri."""

    def test_valid_request(self):
        """Geçerli arama isteği."""
        from api.v1.semantic_search import SearchRequest

        request = SearchRequest(
            query="Matematik sorusu",
            limit=10,
            similarity_threshold=0.7
        )

        assert request.query == "Matematik sorusu"
        assert request.limit == 10
        assert request.similarity_threshold == 0.7

    def test_default_values(self):
        """Varsayılan değerler doğru olmalı."""
        from api.v1.semantic_search import SearchRequest

        request = SearchRequest(query="test")

        assert request.limit == 10
        assert request.similarity_threshold == 0.7
        assert request.use_mmr is False
        assert request.mmr_lambda == 0.5
        assert request.use_hybrid_ranking is False

    def test_with_filters(self):
        """Filtreler ile istek."""
        from api.v1.semantic_search import SearchRequest

        request = SearchRequest(
            query="test",
            subject="matematik",
            exam_type="TYT",
            difficulty_min=-2.0,
            difficulty_max=2.0
        )

        assert request.subject == "matematik"
        assert request.exam_type == "TYT"
        assert request.difficulty_min == -2.0
        assert request.difficulty_max == 2.0

    def test_mmr_enabled(self):
        """MMR aktif istek."""
        from api.v1.semantic_search import SearchRequest

        request = SearchRequest(
            query="test",
            use_mmr=True,
            mmr_lambda=0.7
        )

        assert request.use_mmr is True
        assert request.mmr_lambda == 0.7


class TestSearchResult:
    """SearchResult model testleri."""

    def test_basic_result(self):
        """Temel sonuç."""
        from api.v1.semantic_search import SearchResult

        result = SearchResult(
            id="q1",
            content="Test sorusu",
            similarity=0.85,
            metadata={"subject": "matematik"}
        )

        assert result.id == "q1"
        assert result.similarity == 0.85
        assert result.metadata["subject"] == "matematik"

    def test_with_hybrid_score(self):
        """Hybrid score ile sonuç."""
        from api.v1.semantic_search import SearchResult

        result = SearchResult(
            id="q1",
            content="Test",
            similarity=0.85,
            metadata={},
            hybrid_score=0.82,
            score_breakdown={"similarity": 0.85, "recency": 0.7, "popularity": 0.5}
        )

        assert result.hybrid_score == 0.82
        assert result.score_breakdown["similarity"] == 0.85


class TestSemanticSearchService:
    """SemanticSearchService unit testleri."""

    @pytest.fixture
    def mock_service(self):
        """Mock search service."""
        with patch("api.v1.semantic_search.CHROMADB_AVAILABLE", False):
            from api.v1.semantic_search import SemanticSearchService
            service = SemanticSearchService()
            return service

    def test_build_where_clause_empty(self, mock_service):
        """Filtre yoksa None dönmeli."""
        from api.v1.semantic_search import SearchRequest

        request = SearchRequest(query="test")
        where = mock_service._build_where_clause(request)

        assert where is None

    def test_build_where_clause_single_filter(self, mock_service):
        """Tek filtre doğru olmalı."""
        from api.v1.semantic_search import SearchRequest

        request = SearchRequest(query="test", subject="matematik")
        where = mock_service._build_where_clause(request)

        assert where == {"subject": "matematik"}

    def test_build_where_clause_multiple_filters(self, mock_service):
        """Birden fazla filtre $and ile birleşmeli."""
        from api.v1.semantic_search import SearchRequest

        request = SearchRequest(
            query="test",
            subject="matematik",
            exam_type="TYT"
        )
        where = mock_service._build_where_clause(request)

        assert "$and" in where
        assert len(where["$and"]) == 2


class TestMMRAlgorithm:
    """MMR algoritması testleri."""

    @pytest.fixture
    def service(self):
        """Service fixture."""
        with patch("api.v1.semantic_search.CHROMADB_AVAILABLE", False):
            from api.v1.semantic_search import SemanticSearchService
            return SemanticSearchService()

    @pytest.fixture
    def mock_results(self):
        """Mock sonuçlar."""
        from api.v1.semantic_search import SearchResult

        return [
            SearchResult(
                id="q1",
                content="Soru 1",
                similarity=0.95,
                metadata={"_embedding": [1.0, 0.0, 0.0]}
            ),
            SearchResult(
                id="q2",
                content="Soru 2",
                similarity=0.90,
                metadata={"_embedding": [0.9, 0.1, 0.0]}  # q1'e çok benzer
            ),
            SearchResult(
                id="q3",
                content="Soru 3",
                similarity=0.85,
                metadata={"_embedding": [0.0, 1.0, 0.0]}  # q1'e dik
            ),
            SearchResult(
                id="q4",
                content="Soru 4",
                similarity=0.80,
                metadata={"_embedding": [0.0, 0.0, 1.0]}  # Tamamen farklı
            ),
        ]

    def test_mmr_returns_correct_count(self, service, mock_results):
        """MMR doğru sayıda sonuç dönmeli."""
        query_embedding = [1.0, 0.0, 0.0]

        result = service._apply_mmr(query_embedding, mock_results, 0.5, top_k=2)

        assert len(result) == 2

    def test_mmr_with_lambda_1_keeps_relevance_order(self, service, mock_results):
        """Lambda=1.0 ile relevance sırası korunmalı."""
        query_embedding = [1.0, 0.0, 0.0]

        result = service._apply_mmr(query_embedding, mock_results, 1.0, top_k=4)

        # Lambda=1.0 ile sadece relevance önemli
        # İlk sonuç en yüksek similarity olmalı
        assert result[0].id == "q1"

    def test_mmr_with_lambda_0_maximizes_diversity(self, service, mock_results):
        """Lambda=0.0 ile diversity maksimize edilmeli."""
        query_embedding = [1.0, 0.0, 0.0]

        result = service._apply_mmr(query_embedding, mock_results, 0.0, top_k=3)

        # Lambda=0.0 ile diversity maksimize edilir
        # İlk seçilen sonra, ona en az benzeyen seçilmeli
        # Bu test sonuçların farklı yönlerde olduğunu doğrular
        ids = [r.id for r in result]
        assert len(set(ids)) == 3  # Hepsi farklı

    def test_mmr_removes_embeddings(self, service, mock_results):
        """MMR sonrası embedding'ler temizlenmeli."""
        query_embedding = [1.0, 0.0, 0.0]

        result = service._apply_mmr(query_embedding, mock_results, 0.5, top_k=2)

        for r in result:
            assert "_embedding" not in r.metadata


class TestHybridRanking:
    """Hybrid ranking testleri."""

    @pytest.fixture
    def service(self):
        """Service fixture."""
        with patch("api.v1.semantic_search.CHROMADB_AVAILABLE", False):
            from api.v1.semantic_search import SemanticSearchService
            return SemanticSearchService()

    @pytest.fixture
    def mock_results(self):
        """Mock sonuçlar."""
        from api.v1.semantic_search import SearchResult

        now = datetime.now()
        return [
            SearchResult(
                id="q1",
                content="Eski popüler",
                similarity=0.80,
                metadata={
                    "created_at": (now - timedelta(days=300)).isoformat(),
                    "view_count": 100
                }
            ),
            SearchResult(
                id="q2",
                content="Yeni unpopüler",
                similarity=0.75,
                metadata={
                    "created_at": (now - timedelta(days=7)).isoformat(),
                    "view_count": 5
                }
            ),
            SearchResult(
                id="q3",
                content="Orta",
                similarity=0.85,
                metadata={
                    "created_at": (now - timedelta(days=30)).isoformat(),
                    "view_count": 50
                }
            ),
        ]

    def test_hybrid_ranking_adds_scores(self, service, mock_results):
        """Hybrid ranking score eklemeli."""
        result = service._apply_hybrid_ranking(mock_results)

        for r in result:
            assert r.hybrid_score is not None
            assert r.score_breakdown is not None
            assert "similarity" in r.score_breakdown
            assert "recency" in r.score_breakdown
            assert "popularity" in r.score_breakdown

    def test_hybrid_ranking_sorts_by_score(self, service, mock_results):
        """Sonuçlar hybrid score'a göre sıralanmalı."""
        result = service._apply_hybrid_ranking(mock_results)

        scores = [r.hybrid_score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_hybrid_ranking_custom_weights(self, service, mock_results):
        """Özel ağırlıklar kullanılabilmeli."""
        custom_weights = {"similarity": 0.9, "recency": 0.05, "popularity": 0.05}
        result = service._apply_hybrid_ranking(mock_results, weights=custom_weights)

        # Similarity ağırlığı çok yüksek, en yüksek similarity ilk olmalı
        assert result[0].id == "q3"  # 0.85 similarity

    def test_hybrid_ranking_empty_list(self, service):
        """Boş liste için boş liste dönmeli."""
        result = service._apply_hybrid_ranking([])

        assert result == []


class TestSimilarRequest:
    """SimilarRequest model testleri."""

    def test_valid_request(self):
        """Geçerli benzer soru isteği."""
        from api.v1.semantic_search import SimilarRequest

        request = SimilarRequest(
            question_id="q123",
            limit=5
        )

        assert request.question_id == "q123"
        assert request.limit == 5
        assert request.exclude_same_subject is False


class TestSearchHealth:
    """Search health endpoint testleri."""

    @pytest.mark.asyncio
    async def test_health_returns_status(self):
        """Health endpoint status dönmeli."""
        with patch("api.v1.semantic_search.CHROMADB_AVAILABLE", False):
            from api.v1.semantic_search import search_health

            result = await search_health()

            assert "status" in result
            assert "chromadb_available" in result
            assert result["chromadb_available"] is False
            assert result["status"] == "unhealthy"


class TestIntegrationScenarios:
    """Entegrasyon senaryoları."""

    @pytest.fixture
    def mock_chromadb(self):
        """Mock ChromaDB."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["q1", "q2", "q3"]],
            "documents": [["Soru 1", "Soru 2", "Soru 3"]],
            "metadatas": [[
                {"subject": "matematik", "difficulty": 0.5},
                {"subject": "fizik", "difficulty": 0.3},
                {"subject": "matematik", "difficulty": 0.7}
            ]],
            "distances": [[0.1, 0.2, 0.3]],
            "embeddings": [[[0.1] * 768, [0.2] * 768, [0.3] * 768]]
        }
        mock_collection.count.return_value = 100

        return mock_collection

    @pytest.mark.asyncio
    async def test_search_with_filters(self, mock_chromadb):
        """Filtreli arama senaryosu."""
        with patch("api.v1.semantic_search.CHROMADB_AVAILABLE", True):
            with patch("api.v1.semantic_search.chromadb") as mock_chroma:
                mock_client = MagicMock()
                mock_client.get_or_create_collection.return_value = mock_chromadb
                mock_chroma.Client.return_value = mock_client

                with patch("api.v1.semantic_search.get_embedding_service") as mock_emb:
                    mock_emb_service = MagicMock()
                    mock_emb_service.embed.return_value = [0.1] * 768
                    mock_emb.return_value = mock_emb_service

                    from api.v1.semantic_search import SemanticSearchService, SearchRequest

                    service = SemanticSearchService()
                    request = SearchRequest(
                        query="integral hesaplama",
                        subject="matematik",
                        limit=5
                    )

                    response = await service.search(request)

                    assert response.query == "integral hesaplama"
                    assert response.filters_applied["subject"] == "matematik"
