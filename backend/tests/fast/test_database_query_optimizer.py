"""
Tests for Database Query Optimizer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from core.database_query_optimizer import (
    QueryOptimizer,
    CommonQueryPatterns,
    explain_loading_strategy,
    get_optimizer,
)


class TestQueryOptimizer:
    """Test QueryOptimizer class"""

    @pytest.fixture
    def mock_session(self):
        """Create mock async session"""
        session = AsyncMock()
        return session

    @pytest.fixture
    def optimizer(self, mock_session):
        """Create QueryOptimizer instance"""
        return QueryOptimizer(mock_session)

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.session is not None
        assert optimizer.query_stats["total_queries"] == 0
        assert optimizer.query_stats["total_time"] == 0.0
        assert len(optimizer.query_stats["slow_queries"]) == 0

    def test_get_optimal_loading_strategy_one_to_one(self):
        """Test loading strategy selection for one-to-one"""
        strategy = QueryOptimizer.get_optimal_loading_strategy("one-to-one", "small")
        assert strategy == "joined"

        strategy = QueryOptimizer.get_optimal_loading_strategy("one-to-one", "large")
        assert strategy == "joined"

    def test_get_optimal_loading_strategy_one_to_many(self):
        """Test loading strategy selection for one-to-many"""
        # Small collections -> joined
        strategy = QueryOptimizer.get_optimal_loading_strategy("one-to-many", "small")
        assert strategy == "joined"

        # Medium collections -> selectin
        strategy = QueryOptimizer.get_optimal_loading_strategy("one-to-many", "medium")
        assert strategy == "selectin"

        # Large collections -> selectin
        strategy = QueryOptimizer.get_optimal_loading_strategy("one-to-many", "large")
        assert strategy == "selectin"

    def test_get_optimal_loading_strategy_many_to_many(self):
        """Test loading strategy selection for many-to-many"""
        # Small/medium -> selectin
        strategy = QueryOptimizer.get_optimal_loading_strategy("many-to-many", "small")
        assert strategy == "selectin"

        # Large -> subquery
        strategy = QueryOptimizer.get_optimal_loading_strategy("many-to-many", "large")
        assert strategy == "subquery"

    def test_track_query_normal(self, optimizer):
        """Test tracking normal query"""
        mock_query = "SELECT * FROM users"

        optimizer._track_query(mock_query, 0.1)

        assert optimizer.query_stats["total_queries"] == 1
        assert optimizer.query_stats["total_time"] == 0.1
        assert len(optimizer.query_stats["slow_queries"]) == 0

    def test_track_query_slow(self, optimizer):
        """Test tracking slow query"""
        mock_query = "SELECT * FROM users WHERE complex_condition"

        optimizer._track_query(mock_query, 1.5)

        assert optimizer.query_stats["total_queries"] == 1
        assert optimizer.query_stats["total_time"] == 1.5
        assert len(optimizer.query_stats["slow_queries"]) == 1
        assert optimizer.query_stats["slow_queries"][0]["elapsed"] == 1.5

    def test_get_performance_stats(self, optimizer):
        """Test getting performance statistics"""
        # Simulate some queries
        optimizer._track_query("query1", 0.1)
        optimizer._track_query("query2", 0.2)
        optimizer._track_query("query3", 1.5)  # Slow query

        stats = optimizer.get_performance_stats()

        assert stats["total_queries"] == 3
        assert stats["slow_queries_count"] == 1
        assert "avg_time" in stats

    def test_reset_stats(self, optimizer):
        """Test resetting statistics"""
        # Add some data
        optimizer._track_query("query", 0.5)
        assert optimizer.query_stats["total_queries"] == 1

        # Reset
        optimizer.reset_stats()

        assert optimizer.query_stats["total_queries"] == 0
        assert optimizer.query_stats["total_time"] == 0.0
        assert len(optimizer.query_stats["slow_queries"]) == 0

    @pytest.mark.asyncio
    async def test_load_with_relationships_basic(self, optimizer, mock_session):
        """Test basic relationship loading"""

        # Create mock model
        class MockModel:
            id = MagicMock()
            name = MagicMock()
            profile = MagicMock()

        # Mock execute result
        mock_result = AsyncMock()
        mock_scalars = MagicMock()
        mock_scalars.unique.return_value.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session.execute.return_value = mock_result

        # Execute
        results = await optimizer.load_with_relationships(MockModel, joined=["profile"])

        # Verify
        assert mock_session.execute.called
        assert results == []

    @pytest.mark.asyncio
    async def test_bulk_insert(self, optimizer, mock_session):
        """Test bulk insert operation"""

        class MockModel:
            def __init__(self, **kwargs):
                self.data = kwargs

        data = [{"name": "Test 1"}, {"name": "Test 2"}, {"name": "Test 3"}]

        count = await optimizer.bulk_insert(MockModel, data, batch_size=2)

        assert count == 3
        assert mock_session.commit.called
        assert mock_session.flush.call_count >= 2  # At least 2 batches


class TestCommonQueryPatterns:
    """Test common query patterns"""

    @pytest.mark.asyncio
    async def test_get_student_dashboard_data_not_found(self):
        """Test student dashboard data when student not found"""
        mock_session = AsyncMock()

        # Mock no result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await CommonQueryPatterns.get_student_dashboard_data(
            mock_session, student_id=999
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_student_dashboard_data_found(self):
        """Test student dashboard data when student found"""
        mock_session = AsyncMock()

        # Mock student with relationships
        mock_student = MagicMock()
        mock_student.ogrenme_profili = MagicMock()
        mock_student.sinav_sonuclari = []
        mock_student.ogrenme_yollari = []
        mock_student.cozulen_sorular = []

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_student
        mock_session.execute.return_value = mock_result

        result = await CommonQueryPatterns.get_student_dashboard_data(
            mock_session, student_id=1
        )

        assert result is not None
        assert result["student"] == mock_student
        assert "profile" in result
        assert "exam_results" in result
        assert "learning_paths" in result
        assert "solved_questions" in result

    @pytest.mark.asyncio
    async def test_get_exam_with_questions(self):
        """Test loading exam with questions"""
        mock_session = AsyncMock()

        # Mock exam with questions
        mock_exam = MagicMock()
        mock_exam.sorular = [MagicMock(id=1), MagicMock(id=2)]

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_exam
        mock_session.execute.return_value = mock_result

        result = await CommonQueryPatterns.get_exam_with_questions(
            mock_session, exam_id=1
        )

        assert result is not None
        assert result["exam"] == mock_exam
        assert len(result["questions"]) == 2

    @pytest.mark.asyncio
    async def test_get_class_performance_summary(self):
        """Test class performance summary"""
        mock_session = AsyncMock()

        # Mock scalar results
        mock_session.scalar = AsyncMock()
        mock_session.scalar.side_effect = [
            25,  # student_count
            75.5,  # avg_score
            150,  # total_exams
        ]

        result = await CommonQueryPatterns.get_class_performance_summary(
            mock_session, class_id=11
        )

        assert result["class_id"] == 11
        assert result["student_count"] == 25
        assert result["average_score"] == 75.5
        assert result["total_exams_taken"] == 150


class TestHelperFunctions:
    """Test helper functions"""

    @pytest.mark.asyncio
    async def test_get_optimizer(self):
        """Test get_optimizer helper"""
        mock_session = AsyncMock()

        optimizer = await get_optimizer(mock_session)

        assert isinstance(optimizer, QueryOptimizer)
        assert optimizer.session == mock_session

    def test_explain_loading_strategy_joined(self):
        """Test explaining joined strategy"""
        explanation = explain_loading_strategy("joined")

        assert "JOINED LOADING" in explanation
        assert "One-to-one" in explanation
        assert "SQL JOIN" in explanation

    def test_explain_loading_strategy_selectin(self):
        """Test explaining selectin strategy"""
        explanation = explain_loading_strategy("selectin")

        assert "SELECTIN LOADING" in explanation
        assert "Collections" in explanation
        assert "IN clause" in explanation

    def test_explain_loading_strategy_subquery(self):
        """Test explaining subquery strategy"""
        explanation = explain_loading_strategy("subquery")

        assert "SUBQUERY LOADING" in explanation
        assert "Large collections" in explanation

    def test_explain_loading_strategy_unknown(self):
        """Test explaining unknown strategy"""
        explanation = explain_loading_strategy("invalid")

        assert "Unknown strategy" in explanation


class TestPerformanceTracking:
    """Test performance tracking features"""

    def test_performance_stats_empty(self):
        """Test stats when no queries"""
        mock_session = AsyncMock()
        optimizer = QueryOptimizer(mock_session)

        stats = optimizer.get_performance_stats()

        assert stats["total_queries"] == 0
        assert stats["slow_queries_count"] == 0

    def test_performance_stats_with_queries(self):
        """Test stats with multiple queries"""
        mock_session = AsyncMock()
        optimizer = QueryOptimizer(mock_session)

        # Add normal queries
        for i in range(10):
            optimizer._track_query(f"query_{i}", 0.1)

        # Add slow queries
        for i in range(3):
            optimizer._track_query(f"slow_query_{i}", 1.5)

        stats = optimizer.get_performance_stats()

        assert stats["total_queries"] == 13
        assert stats["slow_queries_count"] == 3

    def test_slow_query_limit(self):
        """Test that only last 5 slow queries are kept in stats"""
        mock_session = AsyncMock()
        optimizer = QueryOptimizer(mock_session)

        # Add 10 slow queries
        for i in range(10):
            optimizer._track_query(f"slow_{i}", 2.0)

        stats = optimizer.get_performance_stats()

        # Should only keep last 5
        assert len(stats["slow_queries"]) == 5


# Integration-style test examples (would require actual DB)
@pytest.mark.skipif(True, reason="Requires database connection")
class TestQueryOptimizerIntegration:
    """Integration tests requiring database"""

    @pytest.mark.asyncio
    async def test_real_student_loading(self):
        """Test loading real student data"""
        from core.database import get_async_session
        from models_unified import Kullanici

        async with get_async_session() as session:
            optimizer = QueryOptimizer(session)

            students = await optimizer.load_students_with_data(
                limit=10, include_profile=True, include_exam_results=True
            )

            assert len(students) <= 10

            # Verify relationships loaded
            if students:
                student = students[0]
                # These should not trigger additional queries
                _ = student.ogrenme_profili
                _ = student.sinav_sonuclari

    @pytest.mark.asyncio
    async def test_real_aggregation_query(self):
        """Test real aggregation query"""
        from core.database import get_async_session

        async with get_async_session() as session:
            optimizer = QueryOptimizer(session)

            stats = await optimizer.get_students_with_exam_stats(min_exam_count=1)

            assert isinstance(stats, list)

            if stats:
                assert "sinav_sayisi" in stats[0]
                assert "ortalama_puan" in stats[0]
