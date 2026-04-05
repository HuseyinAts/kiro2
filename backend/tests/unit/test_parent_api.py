"""
Unit tests for the parent (veli) API — api/parent.py

Covers:
- Role enforcement: non-parent roles receive 403
- Dashboard endpoint
- Children list and creation
- Child performance and weekly report
- Notifications (create, list, mark-as-read)
- Student approval/rejection of parent relation
- Service-layer exception propagation (ValueError → 400/403, generic → 500)
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parent_user():
    """Return a mock AuthenticatedUser with PARENT role."""
    from models.enums_db import UserRole

    user = MagicMock()
    user.id = "parent-001"
    user.email = "veli@test.com"
    user.username = "veli_test"
    user.role = UserRole.PARENT
    return user


def _make_student_user():
    """Return a mock AuthenticatedUser with STUDENT role."""
    from models.enums_db import UserRole

    user = MagicMock()
    user.id = "student-001"
    user.email = "ogrenci@test.com"
    user.username = "ogrenci_test"
    user.role = UserRole.STUDENT
    return user


def _make_teacher_user():
    """Return a mock AuthenticatedUser with TEACHER role."""
    from models.enums_db import UserRole

    user = MagicMock()
    user.id = "teacher-001"
    user.email = "ogretmen@test.com"
    user.username = "ogretmen_test"
    user.role = UserRole.TEACHER
    return user


def _mock_db():
    """Return a fully mocked AsyncSession."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    db.close = AsyncMock()
    return db


def _make_app(override_user=None):
    """Build an isolated FastAPI app that includes the parent router.

    override_user: callable that returns the current user (defaults to parent).
    """
    from api.parent import router
    from core.dependencies import get_current_user, get_db

    app = FastAPI()
    app.include_router(router)

    mock_db = _mock_db()
    user_fn = override_user if override_user is not None else _make_parent_user

    app.dependency_overrides[get_current_user] = user_fn
    app.dependency_overrides[get_db] = lambda: mock_db

    return app, mock_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def child_relation_response():
    """Sample ParentChildRelationResponse payload."""
    return {
        "id": 1,
        "parent_id": "parent-001",
        "child_id": "student-001",
        "child_name": "Ali Yilmaz",
        "child_email": "ogrenci@test.com",
        "relation_type": "parent",
        "approved": True,
        "created_at": datetime.utcnow().isoformat(),
        "approved_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def performance_response():
    """Sample ChildPerformanceData payload."""
    return {
        "child_id": "student-001",
        "child_name": "Ali Yilmaz",
        "total_study_time": 120,
        "exams_taken": 5,
        "average_score": 72.5,
        "last_exam_date": datetime.utcnow().isoformat(),
        "last_exam_score": 80.0,
        "weak_subjects": ["fizik"],
        "strong_subjects": ["matematik"],
        "recent_achievements": ["Ilk Sinav"],
    }


@pytest.fixture
def weekly_report_response():
    """Sample WeeklyReportData payload."""
    return {
        "child_id": "student-001",
        "child_name": "Ali Yilmaz",
        "week_start": datetime.utcnow().isoformat(),
        "week_end": datetime.utcnow().isoformat(),
        "total_study_time": 300,
        "exams_taken": 3,
        "average_score": 68.0,
        "subjects_studied": ["matematik", "turkce"],
        "achievements": [],
        "performance_trend": "improving",
        "recommendations": ["Fizik konularini tekrar et"],
    }


@pytest.fixture
def notification_response():
    """Sample ParentNotificationResponse payload."""
    return {
        "id": 10,
        "child_id": "student-001",
        "child_name": "Ali Yilmaz",
        "title": "Sinav Sonucu",
        "message": "Ali bugun bir sinav tamamladi.",
        "notification_type": "exam",
        "is_read": False,
        "created_at": datetime.utcnow().isoformat(),
        "read_at": None,
    }


@pytest.fixture
def dashboard_response(
    child_relation_response, performance_response, notification_response
):
    """Sample ParentDashboardData payload."""
    return {
        "children": [performance_response],
        "unread_notifications": 1,
        "recent_notifications": [notification_response],
        "weekly_summary": {"total_study_time": 300, "exams_taken": 3},
        "pending_approvals": [child_relation_response],
    }


# ---------------------------------------------------------------------------
# 1. Role enforcement — non-parent users get 403 on parent-only endpoints
# ---------------------------------------------------------------------------


class TestRoleEnforcement:
    """All parent-only endpoints must return 403 for non-parent callers."""

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("GET", "/api/v1/parent/dashboard", None),
            ("GET", "/api/v1/parent/children", None),
            (
                "POST",
                "/api/v1/parent/children",
                {"child_email": "x@x.com", "relation_type": "parent"},
            ),
            ("GET", "/api/v1/parent/children/student-001/performance", None),
            ("GET", "/api/v1/parent/children/student-001/weekly-report", None),
            ("GET", "/api/v1/parent/notifications", None),
            (
                "POST",
                "/api/v1/parent/notifications",
                {
                    "child_id": "student-001",
                    "title": "T",
                    "message": "M",
                    "notification_type": "exam",
                },
            ),
            ("PUT", "/api/v1/parent/notifications/1/read", None),
        ],
    )
    def test_teacher_role_gets_403(self, method, path, body):
        """TEACHER role must be rejected (403) on all parent-only endpoints."""
        app, _ = _make_app(override_user=_make_teacher_user)
        client = TestClient(app, raise_server_exceptions=False)

        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json=body)
        else:  # PUT
            response = client.put(path)

        assert response.status_code == 403, (
            f"{method} {path} should return 403 for TEACHER, got {response.status_code}"
        )

    @pytest.mark.parametrize(
        "method,path,body",
        [
            ("GET", "/api/v1/parent/dashboard", None),
            ("GET", "/api/v1/parent/children", None),
            ("GET", "/api/v1/parent/children/student-001/performance", None),
        ],
    )
    def test_student_role_gets_403_on_parent_endpoints(self, method, path, body):
        """STUDENT role must not access parent-only endpoints."""
        app, _ = _make_app(override_user=_make_student_user)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(path)
        assert response.status_code == 403

    def test_student_role_can_access_approval_endpoint(self):
        """The /approval/{id} endpoint is student-only — student should NOT get 403."""
        app, _ = _make_app(override_user=_make_student_user)

        with patch("api.parent.ParentService") as MockSvc:
            svc_instance = AsyncMock()
            svc_instance.approve_parent_child_relation = AsyncMock(return_value=None)
            MockSvc.return_value = svc_instance
            client = TestClient(app, raise_server_exceptions=False)
            response = client.put("/api/v1/parent/approval/1?approved=true")

        # The student call should succeed (2xx) rather than 403
        assert response.status_code != 403

    def test_parent_role_gets_403_on_approval_endpoint(self):
        """The /approval/{id} endpoint is student-only — parent should receive 403."""
        app, _ = _make_app(override_user=_make_parent_user)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/approval/1?approved=true")
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# 2. Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    """Tests for GET /api/v1/parent/dashboard"""

    @patch("api.parent.ParentService")
    def test_dashboard_returns_200_with_data(self, MockSvc, dashboard_response):
        """Dashboard returns 200 with the full ParentDashboardData structure."""
        from models.parent import ParentDashboardData

        svc_instance = AsyncMock()
        svc_instance.get_parent_dashboard_data = AsyncMock(
            return_value=ParentDashboardData(**dashboard_response)
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert "children" in data
        assert "unread_notifications" in data
        assert isinstance(data["children"], list)
        assert isinstance(data["unread_notifications"], int)

    @patch("api.parent.ParentService")
    def test_dashboard_service_exception_returns_500(self, MockSvc):
        """Unhandled service exception maps to 500."""
        svc_instance = AsyncMock()
        svc_instance.get_parent_dashboard_data = AsyncMock(
            side_effect=RuntimeError("db failure")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/dashboard")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# 3. Children — list & create
# ---------------------------------------------------------------------------


class TestChildren:
    """Tests for /api/v1/parent/children"""

    @patch("api.parent.ParentService")
    def test_list_children_returns_200(self, MockSvc, child_relation_response):
        """GET /children returns 200 with a list of relations."""
        from models.parent import ParentChildRelationResponse

        svc_instance = AsyncMock()
        svc_instance.get_parent_children = AsyncMock(
            return_value=[ParentChildRelationResponse(**child_relation_response)]
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["child_email"] == child_relation_response["child_email"]
        assert data[0]["approved"] is True

    @patch("api.parent.ParentService")
    def test_list_children_empty_list(self, MockSvc):
        """GET /children returns 200 with empty list when no children linked."""
        svc_instance = AsyncMock()
        svc_instance.get_parent_children = AsyncMock(return_value=[])
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children")

        assert response.status_code == 200
        assert response.json() == []

    @patch("api.parent.ParentService")
    def test_create_child_relation_success(self, MockSvc, child_relation_response):
        """POST /children creates a relation and returns 200 with the new record."""
        from models.parent import ParentChildRelationResponse

        svc_instance = AsyncMock()
        svc_instance.create_parent_child_relation = AsyncMock(
            return_value=ParentChildRelationResponse(**child_relation_response)
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        payload = {"child_email": "ogrenci@test.com", "relation_type": "parent"}
        response = client.post("/api/v1/parent/children", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["child_email"] == "ogrenci@test.com"
        assert data["parent_id"] == "parent-001"

    @patch("api.parent.ParentService")
    def test_create_child_relation_value_error_returns_400(self, MockSvc):
        """POST /children — service ValueError (e.g. student not found) returns 400."""
        svc_instance = AsyncMock()
        svc_instance.create_parent_child_relation = AsyncMock(
            side_effect=ValueError("Student not found")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        payload = {"child_email": "unknown@test.com", "relation_type": "parent"}
        response = client.post("/api/v1/parent/children", json=payload)

        assert response.status_code == 400

    @patch("api.parent.ParentService")
    def test_create_child_relation_generic_exception_returns_500(self, MockSvc):
        """POST /children — unexpected service exception returns 500."""
        svc_instance = AsyncMock()
        svc_instance.create_parent_child_relation = AsyncMock(
            side_effect=Exception("unexpected")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        payload = {"child_email": "ogrenci@test.com", "relation_type": "parent"}
        response = client.post("/api/v1/parent/children", json=payload)

        assert response.status_code == 500

    @patch("api.parent.ParentService")
    def test_list_children_exception_returns_500(self, MockSvc):
        """GET /children — unexpected service exception returns 500."""
        svc_instance = AsyncMock()
        svc_instance.get_parent_children = AsyncMock(
            side_effect=RuntimeError("db timeout")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# 4. Child performance
# ---------------------------------------------------------------------------


class TestChildPerformance:
    """Tests for GET /api/v1/parent/children/{child_id}/performance"""

    @patch("api.parent.ParentService")
    def test_get_performance_success(self, MockSvc, performance_response):
        """Returns 200 with ChildPerformanceData when relation exists."""
        from models.parent import ChildPerformanceData

        svc_instance = AsyncMock()
        svc_instance.get_child_performance = AsyncMock(
            return_value=ChildPerformanceData(**performance_response)
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children/student-001/performance")

        assert response.status_code == 200
        data = response.json()
        assert data["child_id"] == "student-001"
        assert isinstance(data["weak_subjects"], list)
        assert isinstance(data["strong_subjects"], list)
        assert data["exams_taken"] >= 0

    @patch("api.parent.ParentService")
    def test_get_performance_unauthorized_child_returns_403(self, MockSvc):
        """ValueError (unauthorised child access) maps to 403."""
        svc_instance = AsyncMock()
        svc_instance.get_child_performance = AsyncMock(
            side_effect=ValueError("No approved relation")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children/other-student/performance")

        assert response.status_code == 403

    @patch("api.parent.ParentService")
    def test_get_performance_generic_exception_returns_500(self, MockSvc):
        """Unexpected error returns 500."""
        svc_instance = AsyncMock()
        svc_instance.get_child_performance = AsyncMock(
            side_effect=RuntimeError("db down")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children/student-001/performance")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# 5. Weekly report
# ---------------------------------------------------------------------------


class TestWeeklyReport:
    """Tests for GET /api/v1/parent/children/{child_id}/weekly-report"""

    @patch("api.parent.ParentService")
    def test_get_weekly_report_success(
        self, MockSvc, performance_response, weekly_report_response
    ):
        """Returns 200 with WeeklyReportData when caller is authorised parent."""
        from models.parent import ChildPerformanceData, WeeklyReportData

        svc_instance = AsyncMock()
        svc_instance.get_child_performance = AsyncMock(
            return_value=ChildPerformanceData(**performance_response)
        )
        svc_instance.generate_weekly_report = AsyncMock(
            return_value=WeeklyReportData(**weekly_report_response)
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children/student-001/weekly-report")

        assert response.status_code == 200
        data = response.json()
        assert data["child_id"] == "student-001"
        assert data["performance_trend"] in ("improving", "stable", "declining")
        assert isinstance(data["recommendations"], list)

    @patch("api.parent.ParentService")
    def test_weekly_report_unauthorised_returns_403(self, MockSvc):
        """ValueError from ownership check maps to 403."""
        svc_instance = AsyncMock()
        svc_instance.get_child_performance = AsyncMock(
            side_effect=ValueError("Not your child")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children/other-student/weekly-report")

        assert response.status_code == 403

    @patch("api.parent.ParentService")
    def test_weekly_report_generic_exception_returns_500(
        self, MockSvc, performance_response
    ):
        """Unexpected generate error maps to 500."""
        from models.parent import ChildPerformanceData

        svc_instance = AsyncMock()
        svc_instance.get_child_performance = AsyncMock(
            return_value=ChildPerformanceData(**performance_response)
        )
        svc_instance.generate_weekly_report = AsyncMock(
            side_effect=RuntimeError("report gen failed")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/children/student-001/weekly-report")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# 6. Notifications
# ---------------------------------------------------------------------------


class TestNotifications:
    """Tests for /api/v1/parent/notifications"""

    @patch("api.parent.ParentService")
    def test_get_notifications_returns_list(self, MockSvc, notification_response):
        """GET /notifications returns list of notifications."""
        from models.parent import ParentNotificationResponse

        svc_instance = AsyncMock()
        svc_instance.get_parent_notifications = AsyncMock(
            return_value=[ParentNotificationResponse(**notification_response)]
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/notifications")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["notification_type"] == "exam"
        assert data[0]["is_read"] is False

    @patch("api.parent.ParentService")
    def test_get_notifications_unread_only_filter(self, MockSvc, notification_response):
        """unread_only=true is forwarded to the service."""
        from models.parent import ParentNotificationResponse

        svc_instance = AsyncMock()
        svc_instance.get_parent_notifications = AsyncMock(
            return_value=[ParentNotificationResponse(**notification_response)]
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/notifications?unread_only=true")

        assert response.status_code == 200
        # Confirm the service was called with unread_only=True
        svc_instance.get_parent_notifications.assert_awaited_once_with(
            "parent-001", True
        )

    @patch("api.parent.ParentService")
    def test_get_notifications_exception_returns_500(self, MockSvc):
        """Unexpected error in notification fetch returns 500."""
        svc_instance = AsyncMock()
        svc_instance.get_parent_notifications = AsyncMock(
            side_effect=RuntimeError("db error")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/parent/notifications")

        assert response.status_code == 500

    @patch("api.parent.ParentService")
    def test_create_notification_success(self, MockSvc, notification_response):
        """POST /notifications creates and returns a notification."""
        from models.parent import ParentNotificationResponse

        svc_instance = AsyncMock()
        svc_instance.create_notification = AsyncMock(
            return_value=ParentNotificationResponse(**notification_response)
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        payload = {
            "child_id": "student-001",
            "title": "Sinav Sonucu",
            "message": "Bugün bir sınav tamamlandı.",
            "notification_type": "exam",
        }
        response = client.post("/api/v1/parent/notifications", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["notification_type"] == "exam"
        assert data["child_id"] == "student-001"

    @patch("api.parent.ParentService")
    def test_create_notification_value_error_returns_400(self, MockSvc):
        """ValueError from notification creation maps to 400."""
        svc_instance = AsyncMock()
        svc_instance.create_notification = AsyncMock(
            side_effect=ValueError("Invalid child")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        payload = {
            "child_id": "nonexistent",
            "title": "Test",
            "message": "Msg",
            "notification_type": "exam",
        }
        response = client.post("/api/v1/parent/notifications", json=payload)

        assert response.status_code == 400

    @patch("api.parent.ParentService")
    def test_create_notification_invalid_type_rejected(self, MockSvc):
        """Pydantic validation rejects notification_type not in the allowed pattern."""
        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        payload = {
            "child_id": "student-001",
            "title": "Test",
            "message": "Msg",
            "notification_type": "invalid_type",
        }
        response = client.post("/api/v1/parent/notifications", json=payload)

        # Pydantic pattern validation should reject this at the schema level
        assert response.status_code == 422

    @patch("api.parent.ParentService")
    def test_mark_notification_as_read_success(self, MockSvc):
        """PUT /notifications/{id}/read returns success message on 200."""
        svc_instance = AsyncMock()
        svc_instance.mark_notification_as_read = AsyncMock(return_value=None)
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/notifications/10/read")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "okundu" in data["message"].lower()

    @patch("api.parent.ParentService")
    def test_mark_notification_as_read_not_found_returns_404(self, MockSvc):
        """ValueError from mark-as-read maps to 404."""
        svc_instance = AsyncMock()
        svc_instance.mark_notification_as_read = AsyncMock(
            side_effect=ValueError("Notification not found")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/notifications/999/read")

        assert response.status_code == 404

    @patch("api.parent.ParentService")
    def test_mark_notification_as_read_exception_returns_500(self, MockSvc):
        """Unexpected error in mark-as-read returns 500."""
        svc_instance = AsyncMock()
        svc_instance.mark_notification_as_read = AsyncMock(
            side_effect=RuntimeError("db crash")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/notifications/10/read")

        assert response.status_code == 500


# ---------------------------------------------------------------------------
# 7. Approval endpoint (student-side)
# ---------------------------------------------------------------------------


class TestApprovalEndpoint:
    """Tests for PUT /api/v1/parent/approval/{relation_id}"""

    @patch("api.parent.ParentService")
    def test_student_approves_relation(self, MockSvc):
        """Student can approve a parent relation request."""
        svc_instance = AsyncMock()
        svc_instance.approve_parent_child_relation = AsyncMock(return_value=None)
        MockSvc.return_value = svc_instance

        app, _ = _make_app(override_user=_make_student_user)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/approval/5?approved=true")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "onaylandı" in data["message"]

    @patch("api.parent.ParentService")
    def test_student_rejects_relation(self, MockSvc):
        """Student can reject a parent relation request."""
        svc_instance = AsyncMock()
        svc_instance.approve_parent_child_relation = AsyncMock(return_value=None)
        MockSvc.return_value = svc_instance

        app, _ = _make_app(override_user=_make_student_user)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/approval/5?approved=false")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reddedildi" in data["message"]

    @patch("api.parent.ParentService")
    def test_approval_value_error_returns_400(self, MockSvc):
        """ValueError (e.g. relation already processed) maps to 400."""
        svc_instance = AsyncMock()
        svc_instance.approve_parent_child_relation = AsyncMock(
            side_effect=ValueError("Relation not found or already processed")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app(override_user=_make_student_user)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/approval/99?approved=true")

        assert response.status_code == 400

    @patch("api.parent.ParentService")
    def test_approval_generic_exception_returns_500(self, MockSvc):
        """Unexpected error in approval returns 500."""
        svc_instance = AsyncMock()
        svc_instance.approve_parent_child_relation = AsyncMock(
            side_effect=RuntimeError("db failure")
        )
        MockSvc.return_value = svc_instance

        app, _ = _make_app(override_user=_make_student_user)
        client = TestClient(app, raise_server_exceptions=False)
        response = client.put("/api/v1/parent/approval/5?approved=true")

        assert response.status_code == 500
