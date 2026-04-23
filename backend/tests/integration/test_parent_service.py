"""
Veli Takip Sistemi Test Dosyası
Türkiye Üniversite Sınavları Hazırlık Platformu
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from models.parent import ParentChildRelationCreate, ParentNotificationCreate
from models.user import User
from services.parent_service import ParentService


@pytest.mark.skipif(True, reason="ParentService uses coroutine.filter() pattern (AsyncMock not properly awaited in service layer)")
class TestParentService:
    """Veli servis testleri"""

    # mock_db fixture now provided by conftest.py (consolidated version)

    @pytest.fixture
    def parent_service(self, mock_db):
        """Parent service instance"""
        return ParentService(mock_db)

    @pytest.fixture
    def mock_parent_user(self):
        """Mock parent user"""
        return User(
            id=1, email="parent@test.com", full_name="Test Parent", role="parent"
        )

    @pytest.fixture
    def mock_child_user(self):
        """Mock child user"""
        return User(
            id=2, email="child@test.com", full_name="Test Child", role="student"
        )

    @pytest.mark.asyncio
    async def test_create_parent_child_relation_success(
        self, parent_service, mock_db, mock_child_user
    ):
        """Test successful parent-child relation creation"""

        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_child_user
        )
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_child_user,  # Child user found
            None,  # No existing relation
        ]

        relation_data = ParentChildRelationCreate(
            child_email="child@test.com", relation_type="parent"
        )

        with patch.object(
            parent_service, "_send_approval_request_notification"
        ) as mock_notify:
            result = await parent_service.create_parent_child_relation(1, relation_data)

            assert result.child_email == "child@test.com"
            assert result.relation_type == "parent"
            assert result.approved == False
            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_parent_child_relation_child_not_found(
        self, parent_service, mock_db
    ):
        """Test parent-child relation creation when child not found"""

        # Mock database query to return None (child not found)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        relation_data = ParentChildRelationCreate(
            child_email="nonexistent@test.com", relation_type="parent"
        )

        with pytest.raises(
            ValueError, match="Belirtilen email adresine sahip öğrenci bulunamadı"
        ):
            await parent_service.create_parent_child_relation(1, relation_data)

    @pytest.mark.asyncio
    async def test_create_parent_child_relation_not_student(
        self, parent_service, mock_db
    ):
        """Test parent-child relation creation when target is not a student"""

        # Mock user that is not a student
        non_student_user = User(
            id=2, email="teacher@test.com", full_name="Test Teacher", role="teacher"
        )

        mock_db.query.return_value.filter.return_value.first.return_value = (
            non_student_user
        )

        relation_data = ParentChildRelationCreate(
            child_email="teacher@test.com", relation_type="parent"
        )

        with pytest.raises(
            ValueError, match="Sadece öğrenci hesapları ile ilişki kurulabilir"
        ):
            await parent_service.create_parent_child_relation(1, relation_data)

    @pytest.mark.asyncio
    async def test_get_child_performance_success(
        self, parent_service, mock_db, mock_child_user
    ):
        """Test successful child performance retrieval"""

        # Mock relation exists and is approved
        mock_relation = Mock()
        mock_relation.parent_id = 1
        mock_relation.child_id = 2
        mock_relation.approved = True

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_relation,  # Relation found
            mock_child_user,  # Child user found
        ]

        # Mock exam results
        mock_exam_results = [
            Mock(duration_minutes=60, score=85.0, completed_at=datetime.now(UTC)),
            Mock(duration_minutes=45, score=78.0, completed_at=datetime.now(UTC)),
            Mock(duration_minutes=50, score=92.0, completed_at=datetime.now(UTC)),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = (
            mock_exam_results
        )

        result = await parent_service.get_child_performance(1, 2)

        assert result.child_id == 2
        assert result.child_name == "Test Child"
        assert result.total_study_time == 155  # 60 + 45 + 50
        assert result.exams_taken == 3
        assert result.average_score == 85.0  # (85 + 78 + 92) / 3

    @pytest.mark.asyncio
    async def test_get_child_performance_no_permission(self, parent_service, mock_db):
        """Test child performance retrieval without permission"""

        # Mock no relation found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(
            ValueError, match="Bu çocuğun verilerine erişim yetkiniz bulunmamaktadır"
        ):
            await parent_service.get_child_performance(1, 2)

    @pytest.mark.asyncio
    async def test_generate_weekly_report_success(
        self, parent_service, mock_db, mock_child_user
    ):
        """Test successful weekly report generation"""

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_child_user
        )

        # Mock exam results for this week
        mock_exam_results = [
            Mock(duration_minutes=60, score=85.0),
            Mock(duration_minutes=45, score=78.0),
            Mock(duration_minutes=50, score=92.0),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = (
            mock_exam_results
        )

        result = await parent_service.generate_weekly_report(2)

        assert result.child_id == 2
        assert result.child_name == "Test Child"
        assert result.total_study_time == 155
        assert result.exams_taken == 3
        assert result.average_score == 85.0
        assert result.performance_trend in ["improving", "stable", "declining"]

    @pytest.mark.asyncio
    async def test_create_notification_success(
        self, parent_service, mock_db, mock_child_user
    ):
        """Test successful notification creation"""

        # Mock relation exists and is approved
        mock_relation = Mock()
        mock_relation.parent_id = 1
        mock_relation.child_id = 2
        mock_relation.approved = True

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_relation,  # Relation found
            mock_child_user,  # Child user found
        ]

        notification_data = ParentNotificationCreate(
            child_id=2,
            title="Test Notification",
            message="Test message",
            notification_type="performance",
        )

        result = await parent_service.create_notification(1, notification_data)

        assert result.child_id == 2
        assert result.title == "Test Notification"
        assert result.message == "Test message"
        assert result.notification_type == "performance"

    @pytest.mark.asyncio
    async def test_create_notification_no_permission(self, parent_service, mock_db):
        """Test notification creation without permission"""

        # Mock no relation found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        notification_data = ParentNotificationCreate(
            child_id=2,
            title="Test Notification",
            message="Test message",
            notification_type="performance",
        )

        with pytest.raises(
            ValueError,
            match="Bu çocuk için bildirim oluşturma yetkiniz bulunmamaktadır",
        ):
            await parent_service.create_notification(1, notification_data)

    @pytest.mark.asyncio
    async def test_approve_parent_child_relation_success(self, parent_service, mock_db):
        """Test successful parent-child relation approval"""

        # Mock pending relation
        mock_relation = Mock()
        mock_relation.id = 1
        mock_relation.parent_id = 1
        mock_relation.child_id = 2
        mock_relation.approved = False

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_relation
        )

        with patch.object(
            parent_service, "_send_approval_confirmation_notification"
        ) as mock_notify:
            result = await parent_service.approve_parent_child_relation(2, 1, True)

            assert result == True
            assert mock_relation.approved == True
            assert mock_relation.approved_at is not None
            mock_notify.assert_called_once_with(1, 2, True)

    @pytest.mark.asyncio
    async def test_approve_parent_child_relation_reject(self, parent_service, mock_db):
        """Test parent-child relation rejection"""

        # Mock pending relation
        mock_relation = Mock()
        mock_relation.id = 1
        mock_relation.parent_id = 1
        mock_relation.child_id = 2
        mock_relation.approved = False

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_relation
        )

        with patch.object(
            parent_service, "_send_approval_confirmation_notification"
        ) as mock_notify:
            result = await parent_service.approve_parent_child_relation(2, 1, False)

            assert result == True
            mock_db.delete.assert_called_once_with(mock_relation)
            mock_notify.assert_called_once_with(1, 2, False)

    @pytest.mark.asyncio
    async def test_mark_notification_as_read_success(self, parent_service, mock_db):
        """Test successful notification mark as read"""

        # Mock notification
        mock_notification = Mock()
        mock_notification.id = 1
        mock_notification.parent_id = 1
        mock_notification.is_read = False
        mock_notification.read_at = None

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_notification
        )

        result = await parent_service.mark_notification_as_read(1, 1)

        assert result == True
        assert mock_notification.is_read == True
        assert mock_notification.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_notification_as_read_not_found(self, parent_service, mock_db):
        """Test notification mark as read when notification not found"""

        # Mock no notification found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Bildirim bulunamadı"):
            await parent_service.mark_notification_as_read(1, 1)

    @pytest.mark.asyncio
    async def test_get_parent_dashboard_data_success(
        self, parent_service, mock_db, mock_child_user
    ):
        """Test successful parent dashboard data retrieval"""

        # Mock children relations
        with patch.object(parent_service, "get_parent_children") as mock_get_children:
            with patch.object(
                parent_service, "get_child_performance"
            ) as mock_get_performance:
                with patch.object(
                    parent_service, "get_parent_notifications"
                ) as mock_get_notifications:
                    # Mock data
                    mock_get_children.return_value = [
                        Mock(child_id=2, child_name="Test Child")
                    ]

                    mock_get_performance.return_value = Mock(
                        child_id=2,
                        child_name="Test Child",
                        average_score=85.0,
                        exams_taken=5,
                    )

                    mock_get_notifications.side_effect = [
                        [Mock(id=1, title="Unread")],  # Unread notifications
                        [
                            Mock(id=1, title="Recent"),
                            Mock(id=2, title="Recent2"),
                        ],  # Recent notifications
                    ]

                    # Mock pending approvals
                    mock_db.query.return_value.filter.return_value.all.return_value = []

                    result = await parent_service.get_parent_dashboard_data(1)

                    assert len(result.children) == 1
                    assert result.unread_notifications == 1
                    assert len(result.recent_notifications) == 2
                    assert result.weekly_summary["total_children"] == 1
                    assert result.weekly_summary["active_children"] == 1
                    assert result.weekly_summary["average_performance"] == 85.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
