"""
Unit tests for EmotionalService (REQ-5)

Emotional state tracking, frustration detection, and mood visualization tests.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from api.schemas.diary import EmotionalStateCreate


class TestEmotionalServiceStateTracking:
    """Test REQ-5.1: Emotional State Tracking"""

    @pytest.mark.asyncio
    async def test_track_state(self):
        """Test tracking emotional state"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock execute for _calculate_self_awareness
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = EmotionalService(mock_db)

        data = EmotionalStateCreate(
            confidence_level=7,
            frustration_score=0.2,
        )

        result = await service.track_state(uuid4(), data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_state_with_context(self):
        """Test tracking state with context notes"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock execute for _calculate_self_awareness
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = EmotionalService(mock_db)

        data = EmotionalStateCreate(
            confidence_level=5,
            frustration_score=0.5,
            context_notes="Debugging a tricky async issue",
        )

        result = await service.track_state(uuid4(), data)

        mock_db.add.assert_called_once()


class TestEmotionalServiceFrustrationCalculation:
    """Test REQ-5.2: Frustration Detection"""

    def test_calculate_frustration_high(self):
        """Test frustration calculation with high indicators"""
        from services.emotional_service import EmotionalService

        mock_db = MagicMock()
        service = EmotionalService(mock_db)

        # Test internal frustration calculation with high indicators
        frustration = service._calculate_frustration(
            retry_count=10,
            error_count=5,
            provided_score=0.3
        )

        assert 0.0 <= frustration <= 1.0

    def test_calculate_frustration_low(self):
        """Test frustration calculation with low indicators"""
        from services.emotional_service import EmotionalService

        mock_db = MagicMock()
        service = EmotionalService(mock_db)

        frustration = service._calculate_frustration(
            retry_count=0,
            error_count=0,
            provided_score=0.0
        )

        assert 0.0 <= frustration <= 1.0


class TestEmotionalServiceMoodTrend:
    """Test REQ-5.3: Mood Trend Analysis"""

    @pytest.mark.asyncio
    async def test_get_mood_trend(self):
        """Test getting mood trend data"""
        from services.emotional_service import EmotionalService
        from api.schemas.diary import MoodTrendResponse

        mock_db = AsyncMock()

        # Create mock states
        states = []
        for i in range(7):
            state = MagicMock()
            state.timestamp = datetime.now() - timedelta(days=i)
            state.confidence_level = 7 - i
            state.frustration_score = 0.1 + (i * 0.05)
            state.flow_state = i < 3
            state.productivity_score = 0.8 - (i * 0.05)
            states.append(state)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = states
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        trend = await service.get_mood_trend(uuid4(), days=7)

        # Returns MoodTrendResponse object
        assert isinstance(trend, MoodTrendResponse)
        assert hasattr(trend, 'period_start')
        assert hasattr(trend, 'period_end')
        assert hasattr(trend, 'data_points')

    @pytest.mark.asyncio
    async def test_get_mood_trend_empty(self):
        """Test mood trend with no data"""
        from services.emotional_service import EmotionalService
        from api.schemas.diary import MoodTrendResponse

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        trend = await service.get_mood_trend(uuid4(), days=7)

        assert isinstance(trend, MoodTrendResponse)
        assert trend.data_points == []


class TestEmotionalServiceVisualization:
    """Test REQ-5.4: Mood Visualization"""

    @pytest.mark.asyncio
    async def test_generate_mood_chart(self):
        """Test mood chart generation"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()

        # Create mock states for chart
        states = []
        for i in range(7):
            state = MagicMock()
            state.timestamp = datetime.now() - timedelta(days=i)
            state.confidence_level = 5 + (i % 3)
            state.frustration_score = 0.2 + (i * 0.05)
            state.flow_state = i % 2 == 0
            states.append(state)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = states
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        chart_data = await service.generate_mood_chart(uuid4(), days=7)

        # Should return bytes (PNG image) or None if matplotlib not available
        assert chart_data is None or isinstance(chart_data, bytes)


class TestEmotionalServiceFlowState:
    """Test flow state detection"""

    def test_identify_flow_state_high(self):
        """Test flow state identification with high indicators"""
        from services.emotional_service import EmotionalService

        mock_db = MagicMock()
        service = EmotionalService(mock_db)

        # High indicators should result in flow state
        is_flow = service._identify_flow_state(
            confidence=8,
            productivity=0.9,
            tasks_completed=5,
            provided_flow=False
        )

        assert isinstance(is_flow, bool)
        assert is_flow is True  # High indicators = flow state

    def test_identify_flow_state_low(self):
        """Test flow state identification with low indicators"""
        from services.emotional_service import EmotionalService

        mock_db = MagicMock()
        service = EmotionalService(mock_db)

        # Low indicators should not result in flow state
        is_flow = service._identify_flow_state(
            confidence=3,
            productivity=0.3,
            tasks_completed=1,
            provided_flow=False
        )

        assert isinstance(is_flow, bool)
        assert is_flow is False  # Low indicators = no flow state


class TestEmotionalServiceCRUD:
    """Test CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_states(self):
        """Test getting emotional states"""
        from services.emotional_service import EmotionalService
        from datetime import datetime, timedelta

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        # Use from_date and to_date instead of days
        states = await service.get_states(
            user_id=uuid4(),
            from_date=datetime.now() - timedelta(days=30),
            to_date=datetime.now(),
            limit=50
        )

        assert isinstance(states, list)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_state_by_id(self):
        """Test getting state by ID"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        state = await service.get_state_by_id(uuid4(), uuid4())

        assert state is None

    @pytest.mark.asyncio
    async def test_delete_state(self):
        """Test deleting state"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        result = await service.delete_state(uuid4(), uuid4())

        assert result is False


class TestEmotionalServiceFlowStatistics:
    """Test flow statistics"""

    @pytest.mark.asyncio
    async def test_get_flow_statistics(self):
        """Test getting flow statistics"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()

        # Create mock states
        states = []
        for i in range(10):
            state = MagicMock()
            state.flow_state = i % 3 == 0
            state.timestamp = datetime.now() - timedelta(days=i)
            states.append(state)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = states
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        stats = await service.get_flow_statistics(uuid4(), days=30)

        assert isinstance(stats, dict)


class TestEmotionalServiceValidation:
    """Test input validation"""

    def test_confidence_level_range(self):
        """Test confidence level range validation"""
        data = EmotionalStateCreate(
            confidence_level=7,
            frustration_score=0.3,
        )
        assert 1 <= data.confidence_level <= 10

    def test_frustration_score_range(self):
        """Test frustration score range validation"""
        data = EmotionalStateCreate(
            confidence_level=5,
            frustration_score=0.5,
        )
        assert 0.0 <= data.frustration_score <= 1.0


class TestEmotionalServiceFrustrationPatterns:
    """Test frustration pattern detection"""

    @pytest.mark.asyncio
    async def test_detect_frustration_patterns(self):
        """Test detecting frustration patterns"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()

        # Create mock states with patterns
        states = []
        for i in range(10):
            state = MagicMock()
            state.frustration_score = 0.6 + (i * 0.03)
            state.timestamp = datetime.now() - timedelta(hours=i)
            states.append(state)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = states
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        patterns = await service.detect_frustration_patterns(uuid4(), days=7)

        assert isinstance(patterns, dict)


class TestEmotionalServiceEmotionalPatterns:
    """Test emotional pattern analysis"""

    @pytest.mark.asyncio
    async def test_analyze_emotional_patterns(self):
        """Test analyzing emotional patterns"""
        from services.emotional_service import EmotionalService

        mock_db = AsyncMock()

        states = []
        for i in range(14):
            state = MagicMock()
            state.confidence_level = 5 + (i % 4)
            state.frustration_score = 0.2 + (i % 3) * 0.1
            state.flow_state = i % 2 == 0
            state.timestamp = datetime.now() - timedelta(days=i)
            states.append(state)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = states
        mock_db.execute.return_value = mock_result

        service = EmotionalService(mock_db)

        analysis = await service.analyze_emotional_patterns(uuid4(), days=14)

        assert isinstance(analysis, dict)
