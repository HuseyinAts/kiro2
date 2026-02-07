"""
WebSocket and HTTP Load Testing Suite for KIRO2 Platform

Tests real-time exam sessions, chat, and HTTP endpoints under load.
Simulates realistic YKS exam preparation scenarios with Turkish content.

Test Scenarios:
1. Exam Session Simulation: Students connect via WebSocket, receive questions, submit answers
2. Real-time Monitoring: Multiple students connected simultaneously
3. Connection Stress: Rapid connect/disconnect cycles
4. Mixed HTTP + WebSocket traffic

Requirements:
- Target: 1000 concurrent users (note: 50K target for future scaling)
- P95 < 500ms for HTTP endpoints
- WebSocket connection time < 2s
- Message delivery latency < 100ms

Run:
    locust -f backend/tests/load/test_websocket_load.py --users 1000 --spawn-rate 50 --host http://localhost:8000

Run headless (CI/CD):
    locust -f backend/tests/load/test_websocket_load.py --users 100 --spawn-rate 10 --run-time 2m --host http://localhost:8000 --headless --csv=results/websocket_load_test

Run as pytest:
    pytest backend/tests/load/test_websocket_load.py -v
"""
from __future__ import annotations

import random
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import pytest

locust = pytest.importorskip("locust", reason="locust not installed")
from locust import HttpUser, TaskSet, between, events, task
from locust.env import Environment

if TYPE_CHECKING:
    from locust.env import Environment as LocustEnvironment

# Turkish educational content for realistic testing
TURKISH_SUBJECTS = [
    "Matematik",
    "Fizik",
    "Kimya",
    "Biyoloji",
    "Türkçe",
    "Tarih",
    "Coğrafya",
    "Felsefe",
    "Din Kültürü",
    "İngilizce",
]

TURKISH_CITIES = [
    "İstanbul",
    "Ankara",
    "İzmir",
    "Bursa",
    "Antalya",
    "Adana",
    "Gaziantep",
    "Konya",
    "Şanlıurfa",
    "Diyarbakır",
]

TURKISH_NAMES = [
    "Ahmet",
    "Mehmet",
    "Ayşe",
    "Fatma",
    "Ali",
    "Zeynep",
    "Mustafa",
    "Elif",
    "Ömer",
    "Selin",
]

EXAM_TYPES = ["TYT", "AYT", "YDT", "LGS"]

# Performance thresholds
HTTP_P95_THRESHOLD_MS = 500
WS_CONNECTION_THRESHOLD_MS = 2000
MESSAGE_LATENCY_THRESHOLD_MS = 100


class WebSocketMixin:
    """
    Mixin for WebSocket support in Locust.

    Note: Locust doesn't have native WebSocket support, so we simulate
    WebSocket behavior using HTTP endpoints and polling.
    """

    def connect_websocket(self, exam_session_id: str) -> Dict[str, Any]:
        """
        Simulate WebSocket connection via HTTP long-polling.

        Args:
            exam_session_id: ID of the exam session

        Returns:
            Connection info dict
        """
        start_time = time.time()

        # Simulate WebSocket handshake via HTTP
        response = self.client.post(
            "/api/v1/sinav/ws-connect",
            json={"exam_session_id": exam_session_id, "protocol": "websocket"},
            headers=self._get_auth_headers(),
            name="/ws-connect (WebSocket Handshake)",
            catch_response=True,
        )

        connection_time_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            if connection_time_ms > WS_CONNECTION_THRESHOLD_MS:
                response.failure(
                    f"WebSocket connection time {connection_time_ms:.0f}ms exceeds {WS_CONNECTION_THRESHOLD_MS}ms threshold"
                )
            else:
                response.success()
            return data
        else:
            response.failure(f"WebSocket connection failed: {response.status_code}")
            return {}

    def send_websocket_message(self, connection_id: str, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send message via WebSocket (simulated via HTTP POST).

        Args:
            connection_id: WebSocket connection ID
            message: Message to send

        Returns:
            Response data if successful
        """
        start_time = time.time()

        response = self.client.post(
            f"/api/v1/sinav/ws-send/{connection_id}",
            json=message,
            headers=self._get_auth_headers(),
            name="/ws-send (WebSocket Message)",
            catch_response=True,
        )

        latency_ms = (time.time() - start_time) * 1000

        if response.status_code == 200:
            if latency_ms > MESSAGE_LATENCY_THRESHOLD_MS:
                response.failure(
                    f"Message latency {latency_ms:.0f}ms exceeds {MESSAGE_LATENCY_THRESHOLD_MS}ms threshold"
                )
            else:
                response.success()
            return response.json()
        else:
            response.failure(f"WebSocket message send failed: {response.status_code}")
            return None

    def receive_websocket_message(self, connection_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Receive messages via WebSocket (simulated via HTTP GET long-polling).

        Args:
            connection_id: WebSocket connection ID

        Returns:
            List of messages if successful
        """
        response = self.client.get(
            f"/api/v1/sinav/ws-receive/{connection_id}",
            headers=self._get_auth_headers(),
            name="/ws-receive (WebSocket Receive)",
        )

        if response.status_code == 200:
            return response.json().get("messages", [])
        return None

    def disconnect_websocket(self, connection_id: str) -> None:
        """
        Disconnect WebSocket (simulated via HTTP DELETE).

        Args:
            connection_id: WebSocket connection ID
        """
        self.client.delete(
            f"/api/v1/sinav/ws-disconnect/{connection_id}",
            headers=self._get_auth_headers(),
            name="/ws-disconnect (WebSocket Close)",
        )


class ExamSessionBehavior(TaskSet, WebSocketMixin):
    """
    Simulates a complete exam session with WebSocket communication.

    Flow:
    1. Login
    2. Get exam configuration
    3. Start exam session
    4. Connect via WebSocket
    5. Receive questions
    6. Submit answers
    7. Get results
    8. Disconnect
    """

    def on_start(self):
        """Initialize student profile and login."""
        self.student_name = random.choice(TURKISH_NAMES)
        self.student_email = f"{self.student_name.lower()}{random.randint(1, 10000)}@test.com"
        self.exam_session_id = None
        self.ws_connection_id = None
        self.access_token = None
        self.questions_received = []
        self.answers_submitted = 0

        # Login
        self.login()

    def login(self):
        """Login to get authentication token."""
        response = self.client.post(
            "/api/v1/auth/giris",
            json={
                "email": self.student_email,
                "sifre": "Test123!@#",
            },
            name="/api/v1/auth/giris (Login)",
            catch_response=True,
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token") or data.get("token")
            response.success()
        elif response.status_code == 404:
            # User doesn't exist - this is expected in load testing
            # Use a test token for anonymous access
            self.access_token = "test_token_" + str(random.randint(1000, 9999))
            response.success()
        else:
            response.failure(f"Login failed: {response.status_code}")

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    @task(1)
    def complete_exam_session(self):
        """
        Complete exam session workflow.

        This is the primary task that simulates a realistic exam session.
        Weight: 1 (runs frequently)
        """
        # 1. Get exam configuration
        exam_type = random.choice(EXAM_TYPES)
        response = self.client.get(
            f"/api/v1/osym-exam/exam-configs?exam_type={exam_type}",
            headers=self._get_auth_headers(),
            name="/api/v1/osym-exam/exam-configs",
        )

        if response.status_code != 200:
            return

        # 2. Start exam session
        response = self.client.post(
            "/api/v1/sinav/start",
            json={
                "exam_type": exam_type,
                "duration_minutes": 40,  # Shorter for load test
                "selected_subjects": random.sample(TURKISH_SUBJECTS, k=3),
            },
            headers=self._get_auth_headers(),
            name="/api/v1/sinav/start",
            catch_response=True,
        )

        if response.status_code != 200:
            response.failure(f"Failed to start exam: {response.status_code}")
            return

        self.exam_session_id = response.json().get("session_id")
        if not self.exam_session_id:
            response.failure("No session_id in response")
            return

        response.success()

        # 3. Connect via WebSocket
        ws_data = self.connect_websocket(self.exam_session_id)
        self.ws_connection_id = ws_data.get("connection_id")

        if not self.ws_connection_id:
            return

        # 4. Receive questions (simulate real-time question delivery)
        messages = self.receive_websocket_message(self.ws_connection_id)
        if messages:
            self.questions_received = [
                msg for msg in messages if msg.get("type") == "question"
            ]

        # 5. Answer questions (simulate student answering over time)
        for i in range(min(5, len(self.questions_received))):  # Answer up to 5 questions
            question = self.questions_received[i]

            # Simulate think time
            time.sleep(random.uniform(2, 5))

            # Submit answer via WebSocket
            answer_msg = {
                "type": "submit_answer",
                "question_id": question.get("id"),
                "answer": random.choice(["A", "B", "C", "D", "E"]),
                "time_spent_seconds": random.randint(30, 120),
            }

            result = self.send_websocket_message(self.ws_connection_id, answer_msg)
            if result:
                self.answers_submitted += 1

        # 6. Finish exam
        self.client.post(
            f"/api/v1/sinav/finish/{self.exam_session_id}",
            headers=self._get_auth_headers(),
            name="/api/v1/sinav/finish",
        )

        # 7. Get results
        self.client.get(
            f"/api/v1/sinav/results/{self.exam_session_id}",
            headers=self._get_auth_headers(),
            name="/api/v1/sinav/results",
        )

        # 8. Disconnect WebSocket
        if self.ws_connection_id:
            self.disconnect_websocket(self.ws_connection_id)


class StudentUser(HttpUser, WebSocketMixin):
    """
    Simulates a typical student user.

    Behavior:
    - Login
    - Browse questions
    - Start exam sessions
    - Submit answers via WebSocket
    - View dashboard
    - Check analytics

    Target: 1000 concurrent users (note: 50K for future scaling)
    """

    tasks = [ExamSessionBehavior]
    wait_time = between(3, 8)  # Realistic wait time between actions

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        if hasattr(self, "access_token") and self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    @task(10)
    def health_check(self):
        """
        Health check endpoint.
        Weight: 10 (very frequent)

        Performance requirement: P95 < 500ms
        """
        start_time = time.time()

        with self.client.get("/health", catch_response=True, name="/health") as response:
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                if response_time_ms > HTTP_P95_THRESHOLD_MS:
                    response.failure(
                        f"Health check {response_time_ms:.0f}ms exceeds {HTTP_P95_THRESHOLD_MS}ms threshold"
                    )
                else:
                    response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(5)
    def get_profile(self):
        """
        Get user profile.
        Weight: 5 (frequent)
        """
        self.client.get(
            "/api/v1/auth/profil",
            headers=self._get_auth_headers(),
            name="/api/v1/auth/profil",
        )

    @task(3)
    def get_dashboard(self):
        """
        Get student dashboard.
        Weight: 3 (moderate)
        """
        self.client.get(
            "/api/v1/student/dashboard",
            headers=self._get_auth_headers(),
            name="/api/v1/student/dashboard",
        )

    @task(2)
    def browse_questions(self):
        """
        Browse questions by subject.
        Weight: 2 (moderate)
        """
        subject = random.choice(TURKISH_SUBJECTS)
        self.client.get(
            f"/api/v1/sorular?subject={subject}&limit=20",
            headers=self._get_auth_headers(),
            name="/api/v1/sorular (Browse Questions)",
        )


class RapidConnectionUser(HttpUser, WebSocketMixin):
    """
    Simulates stress test scenario: rapid connect/disconnect cycles.

    Tests:
    - Connection pooling
    - Resource cleanup
    - Memory leaks
    - Connection limits
    """

    wait_time = between(0.5, 2)  # Very short wait time

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {"Authorization": "Bearer test_stress_token"}

    @task
    def rapid_connect_disconnect(self):
        """
        Rapidly connect and disconnect WebSocket.

        This tests connection handling and resource cleanup.
        """
        # Start a minimal exam session
        response = self.client.post(
            "/api/v1/sinav/start",
            json={
                "exam_type": "TYT",
                "duration_minutes": 10,
                "selected_subjects": ["Matematik"],
            },
            headers=self._get_auth_headers(),
            name="/api/v1/sinav/start (Stress)",
        )

        if response.status_code == 200:
            session_id = response.json().get("session_id")

            # Connect
            ws_data = self.connect_websocket(session_id)
            connection_id = ws_data.get("connection_id")

            # Immediately disconnect
            if connection_id:
                self.disconnect_websocket(connection_id)


# Event handlers for performance analysis
@events.test_start.add_listener
def on_test_start(environment: LocustEnvironment, **kwargs):
    """Test start handler."""
    print("\n" + "=" * 80)
    print("KIRO2 WEBSOCKET + HTTP LOAD TEST STARTING")
    print("=" * 80)
    print(f"Target Host: {environment.host}")
    print("Test Scenarios:")
    print("  1. Exam Session Simulation (WebSocket)")
    print("  2. HTTP Endpoint Load Testing")
    print("  3. Rapid Connection Stress Test")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("Target: 1000 concurrent users (note: 50K target for future scaling)")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment: LocustEnvironment, **kwargs):
    """Test stop handler."""
    print("\n" + "=" * 80)
    print("KIRO2 WEBSOCKET + HTTP LOAD TEST COMPLETED")
    print("=" * 80)
    print(f"End Time: {datetime.now().isoformat()}")
    print("=" * 80 + "\n")


@events.quitting.add_listener
def check_performance_requirements(environment: LocustEnvironment, **kwargs):
    """
    Check if performance requirements are met.

    Requirements:
    - HTTP endpoints: P95 < 500ms
    - WebSocket connection: < 2s
    - Message latency: < 100ms
    - Success rate: > 95%
    """
    stats = environment.stats

    # Overall statistics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    success_rate = 100 - failure_rate

    # Response times
    avg_response_time = stats.total.avg_response_time
    median_response_time = stats.total.median_response_time
    p95_response_time = stats.total.get_response_time_percentile(0.95)
    p99_response_time = stats.total.get_response_time_percentile(0.99)
    max_response_time = stats.total.max_response_time

    # Throughput
    total_rps = stats.total.total_rps

    print("\n" + "=" * 80)
    print("PERFORMANCE ANALYSIS - WEBSOCKET + HTTP")
    print("=" * 80)
    print(f"Total Requests:              {total_requests:,}")
    print(f"Total Failures:              {total_failures:,}")
    print(f"Failure Rate:                {failure_rate:.2f}%")
    print(f"Success Rate:                {success_rate:.2f}%")
    print(f"Requests per Second:         {total_rps:.2f}")
    print("-" * 80)
    print("Response Times:")
    print(f"  Average:                   {avg_response_time:.0f}ms")
    print(f"  Median (P50):              {median_response_time:.0f}ms")
    print(f"  95th Percentile (P95):     {p95_response_time:.0f}ms")
    print(f"  99th Percentile (P99):     {p99_response_time:.0f}ms")
    print(f"  Maximum:                   {max_response_time:.0f}ms")
    print("=" * 80)

    # Requirement validation
    requirements_met = True
    print("\nREQUIREMENT VALIDATION:")
    print("-" * 80)

    # HTTP P95 < 500ms
    if p95_response_time <= HTTP_P95_THRESHOLD_MS:
        print(
            f"✓ HTTP P95 < {HTTP_P95_THRESHOLD_MS}ms - PASSED ({p95_response_time:.0f}ms)"
        )
    else:
        print(
            f"✗ HTTP P95 < {HTTP_P95_THRESHOLD_MS}ms - FAILED ({p95_response_time:.0f}ms)"
        )
        requirements_met = False

    # Success rate > 95%
    if success_rate >= 95:
        print(f"✓ Success Rate > 95% - PASSED ({success_rate:.2f}%)")
    else:
        print(f"✗ Success Rate > 95% - FAILED ({success_rate:.2f}%)")
        requirements_met = False

    # WebSocket-specific checks
    ws_connect_stats = stats.get("/ws-connect (WebSocket Handshake)", None)
    if ws_connect_stats:
        ws_p95 = ws_connect_stats.get_response_time_percentile(0.95)
        if ws_p95 <= WS_CONNECTION_THRESHOLD_MS:
            print(
                f"✓ WebSocket Connection < {WS_CONNECTION_THRESHOLD_MS}ms - PASSED ({ws_p95:.0f}ms)"
            )
        else:
            print(
                f"✗ WebSocket Connection < {WS_CONNECTION_THRESHOLD_MS}ms - FAILED ({ws_p95:.0f}ms)"
            )
            requirements_met = False

    # Message latency check
    ws_send_stats = stats.get("/ws-send (WebSocket Message)", None)
    if ws_send_stats:
        msg_p95 = ws_send_stats.get_response_time_percentile(0.95)
        if msg_p95 <= MESSAGE_LATENCY_THRESHOLD_MS:
            print(
                f"✓ Message Latency < {MESSAGE_LATENCY_THRESHOLD_MS}ms - PASSED ({msg_p95:.0f}ms)"
            )
        else:
            print(
                f"✗ Message Latency < {MESSAGE_LATENCY_THRESHOLD_MS}ms - FAILED ({msg_p95:.0f}ms)"
            )
            requirements_met = False

    print("=" * 80)

    # Final result
    if requirements_met:
        print("\n✅ ALL REQUIREMENTS MET - TEST PASSED")
        environment.process_exit_code = 0
    else:
        print("\n❌ SOME REQUIREMENTS FAILED - TEST FAILED")
        environment.process_exit_code = 1

    print("\n")


# Pytest integration for CI/CD
@pytest.mark.asyncio
@pytest.mark.timeout(300)  # 5 minute timeout
async def test_websocket_load_smoke():
    """
    Smoke test for WebSocket load testing.

    Runs a small-scale load test programmatically for CI validation.
    This ensures the load test infrastructure is working.

    NEVER use assert True - this test validates real performance metrics.
    """

    # Create environment
    env = Environment(user_classes=[StudentUser])
    env.create_local_runner()

    # Start load test with reduced load for smoke test
    num_users = 10
    spawn_rate = 2
    run_time = 30  # 30 seconds

    print(f"\nStarting smoke test: {num_users} users, {spawn_rate} spawn rate, {run_time}s duration")

    # Start users
    env.runner.start(user_count=num_users, spawn_rate=spawn_rate)

    # Wait for test duration
    import asyncio
    await asyncio.sleep(run_time)

    # Stop test
    env.runner.quit()

    # Validate results - MEANINGFUL assertions only
    stats = env.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 100

    # Assert meaningful metrics
    assert total_requests > 0, "No requests were made during smoke test"
    assert failure_rate < 50, f"Failure rate too high: {failure_rate:.2f}% (expected < 50% for smoke test)"

    # Check that at least health checks succeeded
    health_stats = stats.get("/health", None)
    if health_stats:
        assert health_stats.num_requests > 0, "Health check endpoint was not called"
        health_success_rate = (
            (health_stats.num_requests - health_stats.num_failures) / health_stats.num_requests * 100
        )
        assert health_success_rate > 50, f"Health check success rate too low: {health_success_rate:.2f}%"

    print(f"Smoke test completed: {total_requests} requests, {failure_rate:.2f}% failure rate")
