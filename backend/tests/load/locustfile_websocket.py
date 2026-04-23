"""
Standalone WebSocket Load Test File for KIRO2 Platform

This is a standalone locustfile optimized for CLI usage and production load testing.
Simulates realistic YKS exam preparation platform scenarios with WebSocket + HTTP traffic.

Usage:
------

# Development - Web UI mode (recommended for initial testing)
locust -f locustfile_websocket.py --host http://localhost:8000

# Production - Headless mode with 1000 concurrent users
locust -f locustfile_websocket.py \
    --users 1000 \
    --spawn-rate 50 \
    --run-time 10m \
    --host http://localhost:8000 \
    --headless \
    --csv=results/websocket_load_1k

# Stress test - Maximum load (50K target noted in comments)
locust -f locustfile_websocket.py \
    --users 5000 \
    --spawn-rate 100 \
    --run-time 30m \
    --host http://production-server.com \
    --headless \
    --csv=results/websocket_stress_5k

# Quick smoke test - CI/CD
locust -f locustfile_websocket.py \
    --users 50 \
    --spawn-rate 10 \
    --run-time 2m \
    --host http://localhost:8000 \
    --headless \
    --csv=results/websocket_smoke

Performance Requirements:
--------------------------
- HTTP endpoints: P95 < 500ms
- WebSocket connection: < 2000ms
- Message delivery: < 100ms
- Success rate: > 95%
- Target: 1000 concurrent users (50K for future scaling)
"""
import random
import time
from datetime import datetime
from typing import Any

from locust import HttpUser, between, events, task

# ============================================================================
# TURKISH CONTENT - Realistic YKS Platform Data
# ============================================================================

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
    "Hasan",
    "Hüseyin",
    "Emine",
    "Hatice",
    "İbrahim",
]

TURKISH_SURNAMES = [
    "Yılmaz",
    "Kaya",
    "Demir",
    "Şahin",
    "Çelik",
    "Yıldız",
    "Arslan",
    "Öztürk",
    "Aydın",
    "Özdemir",
]

EXAM_TYPES = ["TYT", "AYT", "YDT", "LGS"]

EXAM_QUESTIONS = {
    "TYT": {
        "Matematik": [
            {"question": "5x + 3 = 18 denkleminde x kaçtır?", "answers": ["A) 2", "B) 3", "C) 4", "D) 5", "E) 6"], "correct": "B"},
            {"question": "Bir üçgenin iç açıları toplamı kaç derecedir?", "answers": ["A) 90", "B) 120", "C) 180", "D) 270", "E) 360"], "correct": "C"},
        ],
        "Türkçe": [
            {"question": "Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?", "answers": ["A", "B", "C", "D", "E"], "correct": "C"},
            {"question": "Mecaz anlam içeren sözcük hangisidir?", "answers": ["A", "B", "C", "D", "E"], "correct": "A"},
        ],
        "Fizik": [
            {"question": "Sürat birimi nedir?", "answers": ["A) m/s²", "B) m/s", "C) kg", "D) N", "E) J"], "correct": "B"},
            {"question": "Newton'un kaçıncı yasası eylemsiz kalma yasasıdır?", "answers": ["A) 1", "B) 2", "C) 3", "D) 4", "E) 5"], "correct": "A"},
        ],
    },
    "AYT": {
        "Matematik": [
            {"question": "İntegral hesabı hangi matematikçi tarafından geliştirilmiştir?", "answers": ["A", "B", "C", "D", "E"], "correct": "A"},
        ],
    },
}

# Performance thresholds
HTTP_P95_THRESHOLD_MS = 500
WS_CONNECTION_THRESHOLD_MS = 2000
MESSAGE_LATENCY_THRESHOLD_MS = 100
SUCCESS_RATE_THRESHOLD = 95.0


# ============================================================================
# WEBSOCKET SIMULATION MIXIN
# ============================================================================

class WebSocketSimulation:
    """
    WebSocket simulation using HTTP endpoints.

    Since Locust doesn't have native WebSocket support, we simulate
    WebSocket behavior using HTTP long-polling and JSON messages.
    """

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        if hasattr(self, "access_token") and self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    def ws_connect(self, exam_session_id: str) -> str | None:
        """
        Connect to WebSocket (simulated).

        Args:
            exam_session_id: Exam session ID

        Returns:
            Connection ID if successful
        """
        start_time = time.time()

        with self.client.post(
            "/api/v1/sinav/ws-connect",
            json={"exam_session_id": exam_session_id},
            headers=self._get_auth_headers(),
            name="[WS] Connect",
            catch_response=True,
        ) as response:
            connection_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                connection_id = data.get("connection_id")

                if connection_time_ms > WS_CONNECTION_THRESHOLD_MS:
                    response.failure(
                        f"Connection time {connection_time_ms:.0f}ms > {WS_CONNECTION_THRESHOLD_MS}ms"
                    )
                else:
                    response.success()

                return connection_id
            response.failure(f"Connection failed: {response.status_code}")
            return None

    def ws_send(self, connection_id: str, message: dict[str, Any]) -> bool:
        """
        Send message via WebSocket (simulated).

        Args:
            connection_id: Connection ID
            message: Message to send

        Returns:
            True if successful
        """
        start_time = time.time()

        with self.client.post(
            f"/api/v1/sinav/ws-send/{connection_id}",
            json=message,
            headers=self._get_auth_headers(),
            name="[WS] Send Message",
            catch_response=True,
        ) as response:
            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                if latency_ms > MESSAGE_LATENCY_THRESHOLD_MS:
                    response.failure(
                        f"Message latency {latency_ms:.0f}ms > {MESSAGE_LATENCY_THRESHOLD_MS}ms"
                    )
                else:
                    response.success()
                return True
            response.failure(f"Send failed: {response.status_code}")
            return False

    def ws_receive(self, connection_id: str) -> list[dict[str, Any]]:
        """
        Receive messages via WebSocket (simulated).

        Args:
            connection_id: Connection ID

        Returns:
            List of received messages
        """
        with self.client.get(
            f"/api/v1/sinav/ws-receive/{connection_id}",
            headers=self._get_auth_headers(),
            name="[WS] Receive",
        ) as response:
            if response.status_code == 200:
                return response.json().get("messages", [])
            return []

    def ws_disconnect(self, connection_id: str) -> None:
        """
        Disconnect WebSocket (simulated).

        Args:
            connection_id: Connection ID
        """
        self.client.delete(
            f"/api/v1/sinav/ws-disconnect/{connection_id}",
            headers=self._get_auth_headers(),
            name="[WS] Disconnect",
        )


# ============================================================================
# USER CLASSES - Different User Behaviors
# ============================================================================

class StudentUser(HttpUser, WebSocketSimulation):
    """
    Primary user type: Student taking exams.

    Simulates:
    - Login
    - Start exam session
    - WebSocket connection
    - Receiving questions
    - Submitting answers
    - Getting results

    Weight: 70% of traffic
    """

    wait_time = between(2, 5)  # Think time between actions
    weight = 70  # 70% of users are students

    def on_start(self):
        """Initialize student and login."""
        self.name = random.choice(TURKISH_NAMES)
        self.surname = random.choice(TURKISH_SURNAMES)
        self.email = f"{self.name.lower()}.{self.surname.lower()}{random.randint(1, 9999)}@test.com"
        self.access_token = None
        self.exam_session_id = None
        self.ws_connection_id = None

        # Login
        self.login()

    def login(self):
        """Perform login."""
        response = self.client.post(
            "/api/v1/auth/giris",
            json={"email": self.email, "sifre": "Test123!@#"},
            name="[HTTP] Login",
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token") or data.get("token")
        else:
            # Use test token if login fails (user might not exist)
            self.access_token = f"test_token_{random.randint(1000, 9999)}"

    @task(20)
    def health_check(self):
        """
        Health check - most frequent operation.
        Weight: 20
        """
        start_time = time.time()

        with self.client.get("/health", name="[HTTP] Health Check", catch_response=True) as response:
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                if response_time_ms > HTTP_P95_THRESHOLD_MS:
                    response.failure(f"Too slow: {response_time_ms:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(10)
    def get_exam_configs(self):
        """
        Get exam configurations.
        Weight: 10
        """
        exam_type = random.choice(EXAM_TYPES)
        self.client.get(
            f"/api/v1/osym-exam/exam-configs?exam_type={exam_type}",
            headers=self._get_auth_headers(),
            name="[HTTP] Get Exam Configs",
        )

    @task(8)
    def view_profile(self):
        """
        View profile.
        Weight: 8
        """
        self.client.get(
            "/api/v1/auth/profil",
            headers=self._get_auth_headers(),
            name="[HTTP] View Profile",
        )

    @task(5)
    def view_dashboard(self):
        """
        View student dashboard.
        Weight: 5
        """
        self.client.get(
            "/api/v1/student/dashboard",
            headers=self._get_auth_headers(),
            name="[HTTP] Dashboard",
        )

    @task(3)
    def browse_questions(self):
        """
        Browse questions by subject.
        Weight: 3
        """
        subject = random.choice(TURKISH_SUBJECTS)
        self.client.get(
            f"/api/v1/sorular?subject={subject}&limit=10",
            headers=self._get_auth_headers(),
            name="[HTTP] Browse Questions",
        )

    @task(1)
    def take_exam(self):
        """
        Complete exam session with WebSocket.
        Weight: 1 (complex operation, less frequent)

        Flow:
        1. Start exam session (HTTP)
        2. Connect WebSocket
        3. Receive questions
        4. Submit answers
        5. Finish exam
        6. Get results
        7. Disconnect
        """
        # 1. Start exam session
        exam_type = random.choice(EXAM_TYPES)
        subjects = random.sample(TURKISH_SUBJECTS, k=min(3, len(TURKISH_SUBJECTS)))

        response = self.client.post(
            "/api/v1/sinav/start",
            json={
                "exam_type": exam_type,
                "duration_minutes": 30,  # Shorter for load test
                "selected_subjects": subjects,
            },
            headers=self._get_auth_headers(),
            name="[HTTP] Start Exam",
        )

        if response.status_code != 200:
            return

        self.exam_session_id = response.json().get("session_id")
        if not self.exam_session_id:
            return

        # 2. Connect WebSocket
        self.ws_connection_id = self.ws_connect(self.exam_session_id)
        if not self.ws_connection_id:
            return

        # 3. Receive questions
        messages = self.ws_receive(self.ws_connection_id)
        questions = [msg for msg in messages if msg.get("type") == "question"]

        # 4. Submit answers (up to 5 questions)
        for i, question in enumerate(questions[:5]):
            # Simulate think time
            time.sleep(random.uniform(3, 8))

            # Submit answer
            answer_msg = {
                "type": "submit_answer",
                "question_id": question.get("id", i),
                "answer": random.choice(["A", "B", "C", "D", "E"]),
                "time_spent_seconds": random.randint(30, 180),
            }

            self.ws_send(self.ws_connection_id, answer_msg)

        # 5. Finish exam
        self.client.post(
            f"/api/v1/sinav/finish/{self.exam_session_id}",
            headers=self._get_auth_headers(),
            name="[HTTP] Finish Exam",
        )

        # 6. Get results
        self.client.get(
            f"/api/v1/sinav/results/{self.exam_session_id}",
            headers=self._get_auth_headers(),
            name="[HTTP] Get Results",
        )

        # 7. Disconnect WebSocket
        self.ws_disconnect(self.ws_connection_id)


class TeacherUser(HttpUser):
    """
    Teacher user: Monitor student progress.

    Simulates:
    - Login
    - View class analytics
    - Monitor student progress
    - Create assignments

    Weight: 20% of traffic
    """

    wait_time = between(5, 10)  # Teachers interact less frequently
    weight = 20  # 20% of users are teachers

    def on_start(self):
        """Initialize teacher and login."""
        self.email = f"ogretmen{random.randint(1, 100)}@test.com"
        self.access_token = None
        self.login()

    def login(self):
        """Perform login."""
        response = self.client.post(
            "/api/v1/auth/giris",
            json={"email": self.email, "sifre": "Teacher123!@#"},
            name="[HTTP] Teacher Login",
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token") or data.get("token")
        else:
            self.access_token = f"teacher_test_{random.randint(1000, 9999)}"

    def _get_auth_headers(self) -> dict[str, str]:
        """Get auth headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    @task(5)
    def view_class_analytics(self):
        """View class analytics."""
        self.client.get(
            "/api/v1/teacher/analytics/class",
            headers=self._get_auth_headers(),
            name="[HTTP] Teacher - Class Analytics",
        )

    @task(3)
    def view_student_progress(self):
        """View student progress."""
        student_id = random.randint(1, 1000)
        self.client.get(
            f"/api/v1/teacher/students/{student_id}/progress",
            headers=self._get_auth_headers(),
            name="[HTTP] Teacher - Student Progress",
        )

    @task(1)
    def create_assignment(self):
        """Create assignment."""
        self.client.post(
            "/api/v1/teacher/assignments",
            json={
                "title": f"Ödev {random.randint(1, 100)}",
                "description": "Matematik çalışma ödevi",
                "due_date": "2025-12-31",
                "question_ids": [random.randint(1, 1000) for _ in range(10)],
            },
            headers=self._get_auth_headers(),
            name="[HTTP] Teacher - Create Assignment",
        )


class StressTestUser(HttpUser, WebSocketSimulation):
    """
    Stress test user: Rapid connect/disconnect.

    Tests:
    - Connection pooling
    - Resource cleanup
    - Memory leak detection

    Weight: 10% of traffic
    """

    wait_time = between(0.1, 1)  # Very short wait time
    weight = 10  # 10% of users are stress testers

    def _get_auth_headers(self) -> dict[str, str]:
        """Get auth headers."""
        return {"Authorization": "Bearer stress_test_token"}

    @task
    def rapid_connect_disconnect(self):
        """Rapidly connect and disconnect."""
        # Start minimal exam
        response = self.client.post(
            "/api/v1/sinav/start",
            json={
                "exam_type": "TYT",
                "duration_minutes": 5,
                "selected_subjects": ["Matematik"],
            },
            headers=self._get_auth_headers(),
            name="[STRESS] Start Exam",
        )

        if response.status_code == 200:
            session_id = response.json().get("session_id")

            # Connect and immediately disconnect
            connection_id = self.ws_connect(session_id)
            if connection_id:
                self.ws_disconnect(connection_id)


# ============================================================================
# EVENT HANDLERS - Performance Analysis
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test start handler."""
    print("\n" + "=" * 80)
    print("🚀 KIRO2 WEBSOCKET + HTTP LOAD TEST")
    print("=" * 80)
    print(f"📍 Host: {environment.host}")
    print("📊 Scenarios:")
    print("   • Student Exam Sessions (WebSocket) - 70%")
    print("   • Teacher Monitoring (HTTP) - 20%")
    print("   • Stress Testing (Rapid Connect/Disconnect) - 10%")
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Target: 1000 concurrent users (50K future scaling)")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test stop handler."""
    print("\n" + "=" * 80)
    print("🏁 KIRO2 LOAD TEST COMPLETED")
    print("=" * 80)
    print(f"⏰ End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


@events.quitting.add_listener
def check_requirements(environment, **kwargs):
    """
    Check performance requirements.

    Requirements:
    - HTTP P95 < 500ms
    - WebSocket connection < 2000ms
    - Message latency < 100ms
    - Success rate > 95%
    """
    stats = environment.stats

    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    success_rate = 100 - failure_rate

    p95_response_time = stats.total.get_response_time_percentile(0.95)
    p99_response_time = stats.total.get_response_time_percentile(0.99)
    avg_response_time = stats.total.avg_response_time
    total_rps = stats.total.total_rps

    print("\n" + "=" * 80)
    print("📊 PERFORMANCE ANALYSIS")
    print("=" * 80)
    print(f"Total Requests:          {total_requests:,}")
    print(f"Total Failures:          {total_failures:,}")
    print(f"Success Rate:            {success_rate:.2f}%")
    print(f"Requests/sec:            {total_rps:.2f}")
    print("-" * 80)
    print("Response Times:")
    print(f"  Average:               {avg_response_time:.0f}ms")
    print(f"  P95:                   {p95_response_time:.0f}ms")
    print(f"  P99:                   {p99_response_time:.0f}ms")
    print("=" * 80)

    # Validate requirements
    requirements_met = True
    print("\n🎯 REQUIREMENT VALIDATION:")
    print("-" * 80)

    # HTTP P95
    if p95_response_time <= HTTP_P95_THRESHOLD_MS:
        print(f"✅ HTTP P95 < {HTTP_P95_THRESHOLD_MS}ms: PASSED ({p95_response_time:.0f}ms)")
    else:
        print(f"❌ HTTP P95 < {HTTP_P95_THRESHOLD_MS}ms: FAILED ({p95_response_time:.0f}ms)")
        requirements_met = False

    # Success rate
    if success_rate >= SUCCESS_RATE_THRESHOLD:
        print(f"✅ Success Rate > {SUCCESS_RATE_THRESHOLD}%: PASSED ({success_rate:.2f}%)")
    else:
        print(f"❌ Success Rate > {SUCCESS_RATE_THRESHOLD}%: FAILED ({success_rate:.2f}%)")
        requirements_met = False

    # WebSocket connection time
    ws_connect = stats.get("[WS] Connect", None)
    if ws_connect:
        ws_p95 = ws_connect.get_response_time_percentile(0.95)
        if ws_p95 <= WS_CONNECTION_THRESHOLD_MS:
            print(f"✅ WS Connection < {WS_CONNECTION_THRESHOLD_MS}ms: PASSED ({ws_p95:.0f}ms)")
        else:
            print(f"❌ WS Connection < {WS_CONNECTION_THRESHOLD_MS}ms: FAILED ({ws_p95:.0f}ms)")
            requirements_met = False

    # Message latency
    ws_send = stats.get("[WS] Send Message", None)
    if ws_send:
        msg_p95 = ws_send.get_response_time_percentile(0.95)
        if msg_p95 <= MESSAGE_LATENCY_THRESHOLD_MS:
            print(f"✅ Message Latency < {MESSAGE_LATENCY_THRESHOLD_MS}ms: PASSED ({msg_p95:.0f}ms)")
        else:
            print(f"❌ Message Latency < {MESSAGE_LATENCY_THRESHOLD_MS}ms: FAILED ({msg_p95:.0f}ms)")
            requirements_met = False

    print("=" * 80)

    if requirements_met:
        print("\n✅ ALL REQUIREMENTS MET - TEST PASSED")
        environment.process_exit_code = 0
    else:
        print("\n❌ SOME REQUIREMENTS FAILED - TEST FAILED")
        environment.process_exit_code = 1

    print("\n")
