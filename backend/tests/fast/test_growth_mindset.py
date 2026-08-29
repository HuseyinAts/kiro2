from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.psychology.growth_mindset_engine import GrowthMindsetEngine


@pytest.mark.asyncio
async def test_growth_mindset_improvement():
    # Arrange
    db = AsyncMock()

    # Mock streak
    streak_mock = MagicMock()
    streak_mock.current_streak = 2

    # Mock performance (latest first, score improved by 15 points vs average)
    now = datetime.now(UTC)
    perf1 = MagicMock(score=75, recorded_at=now)
    perf2 = MagicMock(score=60, recorded_at=now - timedelta(days=1))
    perf3 = MagicMock(score=60, recorded_at=now - timedelta(days=2))

    # Setup mock returns
    mock_result_streak = MagicMock()
    mock_result_streak.scalar_one_or_none.return_value = streak_mock

    mock_result_perf = MagicMock()
    mock_result_perf.scalars.return_value.all.return_value = [perf1, perf2, perf3]

    db.execute.side_effect = [mock_result_streak, mock_result_perf]

    # Act
    result = await GrowthMindsetEngine.generate_message(db, "user-123")

    # Assert
    assert result["type"] == "improvement"
    assert "Gelişim Gözlemlendi" in result["title"]
    assert "15 puan arttı" in result["message"]


@pytest.mark.asyncio
async def test_growth_mindset_resilience():
    # Arrange
    db = AsyncMock()

    # Mock streak
    streak_mock = MagicMock()
    streak_mock.current_streak = 2

    # Mock performance (latest first, score dropped by 15 points vs average)
    now = datetime.now(UTC)
    perf1 = MagicMock(score=45, recorded_at=now)
    perf2 = MagicMock(score=60, recorded_at=now - timedelta(days=1))
    perf3 = MagicMock(score=60, recorded_at=now - timedelta(days=2))

    # Setup mock returns
    mock_result_streak = MagicMock()
    mock_result_streak.scalar_one_or_none.return_value = streak_mock

    mock_result_perf = MagicMock()
    mock_result_perf.scalars.return_value.all.return_value = [perf1, perf2, perf3]

    db.execute.side_effect = [mock_result_streak, mock_result_perf]

    # Act
    result = await GrowthMindsetEngine.generate_message(db, "user-123")

    # Assert
    assert result["type"] == "resilience"
    assert "Öğrenme Fırsatı" in result["title"]
    assert "kalıcı öğrenmenin en doğal parçasıdır" in result["message"]


@pytest.mark.asyncio
async def test_growth_mindset_habit():
    # Arrange
    db = AsyncMock()

    # Mock streak (3 or more days)
    streak_mock = MagicMock()
    streak_mock.current_streak = 5

    # Mock performance (No significant change)
    now = datetime.now(UTC)
    perf1 = MagicMock(score=60, recorded_at=now)
    perf2 = MagicMock(score=60, recorded_at=now - timedelta(days=1))

    # Setup mock returns
    mock_result_streak = MagicMock()
    mock_result_streak.scalar_one_or_none.return_value = streak_mock

    mock_result_perf = MagicMock()
    mock_result_perf.scalars.return_value.all.return_value = [perf1, perf2]

    db.execute.side_effect = [mock_result_streak, mock_result_perf]

    # Act
    result = await GrowthMindsetEngine.generate_message(db, "user-123")

    # Assert
    assert result["type"] == "habit"
    assert "İstikrar Şampiyonu" in result["title"]
    assert "Tam 5 gündür" in result["message"]
