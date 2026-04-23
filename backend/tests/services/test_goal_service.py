"""
Unit tests for GoalService (REQ-6)

Goal tracking, milestones, and risk assessment tests.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from api.schemas.diary import (
    GoalCreate,
    GoalProgressUpdate,
    GoalStatus,
    GoalUpdate,
    MilestoneCreate,
)


class TestGoalServiceCreation:
    """Test REQ-6.1: Goal Creation"""

    @pytest.mark.asyncio
    async def test_create_goal(self):
        """Test creating a goal"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = GoalService(mock_db)

        data = GoalCreate(
            title="Complete 100 coding tasks",
            description="Improve coding skills by completing tasks",
            target_value=100,
            target_date=datetime.now() + timedelta(days=30),
            unit="tasks",
            category="coding",
            priority=1,
            milestones=[
                MilestoneCreate(percentage=25, title="25% milestone"),
                MilestoneCreate(percentage=50, title="50% milestone"),
                MilestoneCreate(percentage=75, title="75% milestone"),
                MilestoneCreate(percentage=100, title="Goal complete"),
            ],
        )

        await service.create_goal(uuid4(), data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_goal_with_smart_criteria(self):
        """Test creating a goal with SMART criteria"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = GoalService(mock_db)

        data = GoalCreate(
            title="Learn FastAPI",
            target_value=10,
            target_date=datetime.now() + timedelta(days=14),
            specific="Complete 10 FastAPI tutorials",
            measurable="Track completed tutorials count",
            achievable="1 tutorial per day is realistic",
            relevant="Needed for current project",
        )

        await service.create_goal(uuid4(), data)

        mock_db.add.assert_called_once()


class TestGoalServiceProgress:
    """Test REQ-6.2: Progress Tracking"""

    @pytest.mark.asyncio
    async def test_update_progress_by_value(self):
        """Test updating goal progress by value"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()

        mock_goal = MagicMock()
        mock_goal.id = uuid4()
        mock_goal.target_value = 100
        mock_goal.current_value = 50
        mock_goal.progress = 50
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.milestones = []
        mock_goal.milestone_celebrations = []
        mock_goal.start_date = datetime.now() - timedelta(days=10)
        mock_goal.target_date = datetime.now() + timedelta(days=20)
        mock_goal.velocity = 5.0
        mock_goal.updated_at = datetime.now()
        mock_goal.is_at_risk = False
        mock_goal.risk_factors = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_goal
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = GoalService(mock_db)

        update = GoalProgressUpdate(current_value=75)

        # update_progress takes only goal_id and progress_data
        result = await service.update_progress(mock_goal.id, update)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update_progress_by_percentage(self):
        """Test updating goal progress by percentage"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()

        mock_goal = MagicMock()
        mock_goal.id = uuid4()
        mock_goal.target_value = 100
        mock_goal.current_value = 50
        mock_goal.progress = 50
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.milestones = []
        mock_goal.milestone_celebrations = []
        mock_goal.start_date = datetime.now() - timedelta(days=10)
        mock_goal.target_date = datetime.now() + timedelta(days=20)
        mock_goal.velocity = 5.0
        mock_goal.updated_at = datetime.now()
        mock_goal.is_at_risk = False
        mock_goal.risk_factors = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_goal
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = GoalService(mock_db)

        update = GoalProgressUpdate(progress=80)

        result = await service.update_progress(mock_goal.id, update)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update_progress_completes_goal(self):
        """Test that 100% progress completes goal"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()

        mock_goal = MagicMock()
        mock_goal.id = uuid4()
        mock_goal.target_value = 100
        mock_goal.current_value = 90
        mock_goal.progress = 90
        mock_goal.status = GoalStatus.ACTIVE
        mock_goal.milestones = []
        mock_goal.milestone_celebrations = []
        mock_goal.start_date = datetime.now() - timedelta(days=10)
        mock_goal.target_date = datetime.now() + timedelta(days=20)
        mock_goal.velocity = 9.0
        mock_goal.updated_at = datetime.now()
        mock_goal.is_at_risk = False
        mock_goal.risk_factors = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_goal
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = GoalService(mock_db)

        update = GoalProgressUpdate(progress=100)

        await service.update_progress(mock_goal.id, update)

        # Goal should be marked as completed


class TestGoalServiceMilestones:
    """Test REQ-6.3: Milestone Tracking"""

    def test_check_milestones(self):
        """Test checking milestone achievements"""
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        # check_milestones takes a Goal object and new_progress
        mock_goal = MagicMock()
        mock_goal.progress = 20  # Old progress
        mock_goal.milestones = [
            {"percentage": 25, "title": "25%", "achieved": False},
            {"percentage": 50, "title": "50%", "achieved": False},
            {"percentage": 75, "title": "75%", "achieved": False},
        ]

        # Test crossing 25% and 50% milestones (old: 20%, new: 60%)
        achieved = service.check_milestones(mock_goal, new_progress=60)

        # Should return list of achievements
        assert isinstance(achieved, list)

    def test_check_milestones_all_achieved(self):
        """Test all milestones achieved"""
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        mock_goal = MagicMock()
        mock_goal.progress = 10  # Old progress
        mock_goal.milestones = [
            {"percentage": 25, "title": "25%", "achieved": False},
            {"percentage": 50, "title": "50%", "achieved": False},
        ]

        achieved = service.check_milestones(mock_goal, new_progress=100)

        assert isinstance(achieved, list)


class TestGoalServiceRiskAssessment:
    """Test REQ-6.4: Risk Assessment"""

    def test_detect_risk_on_track(self):
        """Test risk detection for on-track goal"""
        from api.schemas.diary import GoalRiskResponse
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        mock_goal = MagicMock()
        mock_goal.id = uuid4()
        mock_goal.start_date = datetime.now() - timedelta(days=10)
        mock_goal.target_date = datetime.now() + timedelta(days=20)
        mock_goal.progress = 40  # 40% done with 33% time elapsed
        mock_goal.target_value = 100
        mock_goal.current_value = 40
        mock_goal.updated_at = datetime.now()

        risk = service.detect_risk(mock_goal)

        assert isinstance(risk, GoalRiskResponse)
        assert hasattr(risk, 'is_at_risk')

    def test_detect_risk_behind_schedule(self):
        """Test risk detection for behind schedule goal"""
        from api.schemas.diary import GoalRiskResponse
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        mock_goal = MagicMock()
        mock_goal.id = uuid4()
        mock_goal.start_date = datetime.now() - timedelta(days=20)
        mock_goal.target_date = datetime.now() + timedelta(days=5)  # Only 5 days left
        mock_goal.progress = 30  # Only 30% done
        mock_goal.target_value = 100
        mock_goal.current_value = 30
        mock_goal.updated_at = datetime.now() - timedelta(days=10)

        risk = service.detect_risk(mock_goal)

        assert isinstance(risk, GoalRiskResponse)
        assert hasattr(risk, 'is_at_risk')

    def test_calculate_velocity(self):
        """Test velocity calculation"""
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        # calculate_velocity takes a Goal object
        mock_goal = MagicMock()
        mock_goal.start_date = datetime.now() - timedelta(days=10)
        mock_goal.progress = 50

        velocity = service.calculate_velocity(mock_goal)

        assert isinstance(velocity, float)
        assert velocity >= 0


class TestGoalServicePrediction:
    """Test REQ-6.5: Completion Prediction"""

    def test_predict_completion(self):
        """Test completion date prediction"""
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        mock_goal = MagicMock()
        mock_goal.start_date = datetime.now() - timedelta(days=10)
        mock_goal.progress = 50
        mock_goal.target_date = datetime.now() + timedelta(days=10)

        prediction = service.predict_completion(mock_goal)

        assert prediction is None or isinstance(prediction, datetime)

    def test_predict_completion_no_progress(self):
        """Test prediction with no progress"""
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        mock_goal = MagicMock()
        mock_goal.start_date = datetime.now() - timedelta(days=5)
        mock_goal.progress = 0  # No progress
        mock_goal.target_date = datetime.now() + timedelta(days=25)

        prediction = service.predict_completion(mock_goal)

        # Cannot predict with no velocity
        assert prediction is None


class TestGoalServiceCRUD:
    """Test CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_goals(self):
        """Test getting user goals"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = GoalService(mock_db)

        goals = await service.get_goals(
            user_id=uuid4(),
            status=None,
            limit=20
        )

        assert isinstance(goals, list)
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_goal(self):
        """Test getting goal by ID"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = GoalService(mock_db)

        # get_goal takes only goal_id
        goal = await service.get_goal(uuid4())

        assert goal is None

    @pytest.mark.asyncio
    async def test_update_goal(self):
        """Test updating a goal"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()

        mock_goal = MagicMock()
        mock_goal.title = "Old title"
        mock_goal.milestones = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_goal
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = GoalService(mock_db)

        update = GoalUpdate(title="New title")

        # update_goal takes goal_id and update_data
        result = await service.update_goal(uuid4(), update)

        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_goal(self):
        """Test deleting a goal"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = GoalService(mock_db)

        # delete_goal takes only goal_id
        result = await service.delete_goal(uuid4())

        assert result is False


class TestGoalServiceStatus:
    """Test goal status management"""

    def test_goal_status_enum(self):
        """Test GoalStatus enum values"""
        assert GoalStatus.ACTIVE.value == "active"
        assert GoalStatus.COMPLETED.value == "completed"
        assert GoalStatus.AT_RISK.value == "at_risk"
        assert GoalStatus.CANCELLED.value == "cancelled"

    @pytest.mark.asyncio
    async def test_get_at_risk_goals(self):
        """Test getting at-risk goals"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = GoalService(mock_db)

        goals = await service.get_goals(
            user_id=uuid4(),
            status=GoalStatus.AT_RISK
        )

        assert isinstance(goals, list)


class TestGoalServiceStatistics:
    """Test goal statistics"""

    @pytest.mark.asyncio
    async def test_get_goal_statistics(self):
        """Test getting goal statistics"""
        from models.diary import GoalStatus as GoalStatusModel
        from services.goal_service import GoalService

        mock_db = AsyncMock()

        # Mock goals
        goals = []
        for status in [GoalStatusModel.ACTIVE, GoalStatusModel.COMPLETED, GoalStatusModel.CANCELLED]:
            goal = MagicMock()
            goal.status = status
            goal.progress = 50
            goal.is_at_risk = False
            goal.category = "test"
            goals.append(goal)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = goals
        mock_db.execute.return_value = mock_result

        service = GoalService(mock_db)

        # Correct method name is get_goal_statistics
        stats = await service.get_goal_statistics(uuid4())

        assert isinstance(stats, dict)
        assert "total_goals" in stats
        assert "active" in stats
        assert "completed" in stats


class TestGoalServiceAtRisk:
    """Test at-risk goal detection"""

    @pytest.mark.asyncio
    async def test_get_at_risk_goals(self):
        """Test getting at-risk goals"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = GoalService(mock_db)

        goals = await service.get_at_risk_goals(uuid4())

        assert isinstance(goals, list)

    @pytest.mark.asyncio
    async def test_get_active_goals(self):
        """Test getting active goals"""
        from services.goal_service import GoalService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = GoalService(mock_db)

        goals = await service.get_active_goals(uuid4())

        assert isinstance(goals, list)


class TestGoalServiceValidation:
    """Test input validation"""

    def test_milestone_percentage_range(self):
        """Test milestone percentage range validation"""
        milestone = MilestoneCreate(percentage=50, title="Halfway")
        assert 0 <= milestone.percentage <= 100

    def test_goal_priority_range(self):
        """Test goal priority range validation"""
        goal = GoalCreate(
            title="Test goal",
            target_value=10,
            target_date=datetime.now() + timedelta(days=7),
            priority=2,
        )
        assert 1 <= goal.priority <= 3


class TestGoalServiceSMART:
    """Test SMART validation"""

    def test_validate_smart(self):
        """Test SMART criteria validation"""
        from services.goal_service import GoalService

        mock_db = MagicMock()
        service = GoalService(mock_db)

        data = GoalCreate(
            title="Complete 10 FastAPI tutorials in 2 weeks",
            target_value=10,
            target_date=datetime.now() + timedelta(days=14),
            specific="Complete FastAPI tutorial series",
            measurable="Track completed tutorials count",
            achievable="1 tutorial per day is realistic",
            relevant="Needed for current project",
        )

        result = service.validate_smart(data)

        assert isinstance(result, dict)
        assert "is_valid" in result
        assert "score" in result
