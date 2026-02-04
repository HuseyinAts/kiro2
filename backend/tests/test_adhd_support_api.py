"""
ADHD Support API Tests
Test suite for DEHB (Dikkat Eksikliği ve Hiperaktivite Bozukluğu) support endpoints

Requirements: REQ-52.1 - REQ-52.20
"""

import pytest
from fastapi.testclient import TestClient


class TestPomodoroTimer:
    """Test Pomodoro Timer functionality (Task 88.1)"""

    def test_start_pomodoro_work_session(self, client: TestClient, auth_headers: dict):
        """
        Test starting a Pomodoro work session
        REQ-52.1: Platform SHALL Pomodoro timer (25dk çalışma, 5dk mola) sunar
        """
        response = client.post(
            "/api/adhd-support/pomodoro/start",
            json={"session_type": "work", "task_description": "Matematik çalışması"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify session data
        assert "session_id" in data
        assert data["session_type"] == "work"
        assert data["status"] == "active"
        assert data["duration_minutes"] == 25  # Default work duration
        assert data["remaining_seconds"] == 1500  # 25 * 60


class TestVisualTimer:
    """Test Visual Timer functionality (Task 88.2)"""

    def test_get_visual_timer_data(self, client: TestClient, auth_headers: dict):
        """
        Test getting visual timer data
        REQ-52.2: Platform SHALL görsel countdown ve progress ring gösterir
        """
        session_id = "test-session-123"

        response = client.get(
            f"/api/adhd-support/timer/visual/{session_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify visual timer data
        assert "remaining_seconds" in data
        assert "progress_percentage" in data
        assert "time_display" in data


class TestInactivityDetection:
    """Test Inactivity Detection functionality (Task 88.3)"""

    def test_detect_inactivity_short_duration(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Test inactivity detection for short duration (< 60 seconds)
        REQ-52.11: Platform SHALL inactivity detection yapar
        """
        response = client.post(
            "/api/adhd-support/inactivity/detect",
            params={"inactive_duration_seconds": 30},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify alert data
        assert "alert_id" in data
        assert "user_id" in data
        assert data["inactive_duration_seconds"] == 30
        assert data["suggested_action"] == "continue"
        assert "Harika gidiyorsun" in data["alert_message"]

    def test_detect_inactivity_medium_duration(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Test inactivity detection for medium duration (60-180 seconds)
        REQ-52.12: Platform SHALL focus loss alerts gösterir
        """
        response = client.post(
            "/api/adhd-support/inactivity/detect",
            params={"inactive_duration_seconds": 120},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify alert suggests short break
        assert data["inactive_duration_seconds"] == 120
        assert data["suggested_action"] == "short_break"
        assert "mola" in data["alert_message"].lower()

    def test_detect_inactivity_long_duration(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Test inactivity detection for long duration (180-300 seconds)
        REQ-52.13: Platform SHALL re-engagement prompts gösterir
        """
        response = client.post(
            "/api/adhd-support/inactivity/detect",
            params={"inactive_duration_seconds": 240},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify alert suggests walk break
        assert data["inactive_duration_seconds"] == 240
        assert data["suggested_action"] == "walk_break"
        assert "yürüyüş" in data["alert_message"].lower()

    def test_detect_inactivity_very_long_duration(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Test inactivity detection for very long duration (> 300 seconds)
        REQ-52.14: Platform SHALL session restart önerir
        """
        response = client.post(
            "/api/adhd-support/inactivity/detect",
            params={"inactive_duration_seconds": 600},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify alert suggests restart session
        assert data["inactive_duration_seconds"] == 600
        assert data["suggested_action"] == "restart_session"
        assert "Pomodoro" in data["alert_message"]

    def test_get_inactivity_alerts_history(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Test getting inactivity alerts history
        REQ-52.15: Platform SHALL alert history tutar
        """
        response = client.get(
            "/api/adhd-support/inactivity/alerts",
            params={"limit": 10},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total" in data
        assert "alerts" in data
        assert "stats" in data
        assert "total_alerts_today" in data["stats"]
        assert "average_inactive_duration_seconds" in data["stats"]
        assert "most_common_time" in data["stats"]

    def test_inactivity_alert_response_structure(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Test that inactivity alert has all required fields
        """
        response = client.post(
            "/api/adhd-support/inactivity/detect",
            params={"inactive_duration_seconds": 150},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = [
            "alert_id",
            "user_id",
            "detected_at",
            "inactive_duration_seconds",
            "alert_message",
            "suggested_action",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_inactivity_detection_without_auth(self, client: TestClient):
        """
        Test that inactivity detection requires authentication
        """
        response = client.post(
            "/api/adhd-support/inactivity/detect",
            params={"inactive_duration_seconds": 100},
        )

        # Should return 401 or 403 (depending on auth implementation)
        assert response.status_code in [401, 403]


class TestFocusExercises:
    """Test Focus Exercises functionality (Task 88.4)"""

    def test_get_focus_exercises(self, client: TestClient, auth_headers: dict):
        """
        Test getting focus exercises list
        REQ-52.16: Platform SHALL focus training exercises sunar
        """
        response = client.get("/api/adhd-support/focus-exercises", headers=auth_headers)

        assert response.status_code == 200
        exercises = response.json()

        # Verify exercises list
        assert isinstance(exercises, list)
        assert len(exercises) > 0

        # Verify exercise structure
        first_exercise = exercises[0]
        assert "exercise_id" in first_exercise
        assert "title" in first_exercise
        assert "description" in first_exercise
        assert "duration_minutes" in first_exercise
        assert "difficulty" in first_exercise


# Fixtures
@pytest.fixture
def client():
    """Create test client"""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer mock_token"}
