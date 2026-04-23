"""
Load Testing for Question Bank v2.0 - Week 3
Test system performance with 1000 concurrent users
"""
import random

from locust import HttpUser, between, events, task


class QuestionBankV2User(HttpUser):
    """Simulate user behavior for Question Bank v2.0"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Setup user session"""
        self.student_id = f"test-student-{random.randint(1000, 9999)}"
        self.session_id = None
        self.current_question_id = None

    @task(5)
    def start_cat_session(self):
        """Start CAT session (high frequency task)"""
        konular = ["Matematik", "Fizik", "Kimya", "Biyoloji"]

        response = self.client.post(
            "/api/v2/cat/start",
            json={
                "student_id": self.student_id,
                "konu": random.choice(konular),
                "sinav_tipi": "TYT",
            },
            name="/api/v2/cat/start",
        )

        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
            first_question = data.get("first_question")
            if first_question:
                self.current_question_id = first_question.get("id")

    @task(8)
    def submit_cat_response(self):
        """Submit CAT response (highest frequency task)"""
        if not self.session_id or not self.current_question_id:
            # Need to start session first
            self.start_cat_session()
            return

        response = self.client.post(
            "/api/v2/cat/submit",
            json={
                "session_id": self.session_id,
                "question_id": self.current_question_id,
                "is_correct": random.choice([True, False]),
                "response_time_seconds": random.randint(15, 120),
            },
            name="/api/v2/cat/submit",
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "in_progress":
                next_question = data.get("next_question")
                if next_question:
                    self.current_question_id = next_question.get("id")
            else:
                # Session complete, start new one
                self.session_id = None
                self.current_question_id = None

    @task(3)
    def get_knowledge_graph_stats(self):
        """Get knowledge graph statistics"""
        self.client.get(
            "/api/v2/knowledge-graph/stats", name="/api/v2/knowledge-graph/stats"
        )

    @task(2)
    def get_student_gaps(self):
        """Get student knowledge gaps"""
        self.client.get(
            f"/api/v2/knowledge-graph/student/{self.student_id}/gaps",
            name="/api/v2/knowledge-graph/student/gaps",
        )

    @task(2)
    def get_recommendations(self):
        """Get question recommendations"""
        if not self.current_question_id:
            return

        self.client.post(
            "/api/v2/knowledge-graph/recommendations",
            json={
                "student_id": self.student_id,
                "current_question_id": self.current_question_id,
                "limit": 10,
            },
            name="/api/v2/knowledge-graph/recommendations",
        )

    @task(1)
    def generate_question(self):
        """Generate AI question (low frequency - expensive operation)"""
        konular = ["Matematik", "Fizik", "Kimya", "Biyoloji"]
        alt_konular = {
            "Matematik": ["Türev", "İntegral", "Limit", "Fonksiyonlar"],
            "Fizik": ["Hareket", "Kuvvet", "Enerji", "Elektrik"],
            "Kimya": ["Atomlar", "Moleküller", "Reaksiyonlar", "Periyodik Tablo"],
            "Biyoloji": ["Hücre", "Genetik", "Ekoloji", "Evrim"],
        }

        konu = random.choice(konular)
        alt_konu = random.choice(alt_konular[konu])

        self.client.post(
            "/api/v2/questions/generate",
            json={
                "konu": konu,
                "alt_konu": alt_konu,
                "kazanim": f"{alt_konu} konusunu uygulama",
                "zorluk": random.choice(["easy", "medium", "hard"]),
                "bloom_level": random.choice(
                    ["remember", "understand", "apply", "analyze"]
                ),
            },
            name="/api/v2/questions/generate",
        )

    @task(2)
    def get_hitl_leaderboard(self):
        """Get expert leaderboard"""
        self.client.get(
            "/api/v2/hitl/leaderboard?limit=10", name="/api/v2/hitl/leaderboard"
        )

    @task(1)
    def health_check(self):
        """Check system health"""
        self.client.get("/api/v2/health", name="/api/v2/health")


class ExpertUser(HttpUser):
    """Simulate expert reviewer behavior"""

    wait_time = between(10, 30)  # Experts take longer between actions

    def on_start(self):
        """Setup expert session"""
        self.expert_id = f"test-expert-{random.randint(100, 999)}"

    @task(5)
    def get_dashboard(self):
        """Get expert dashboard"""
        self.client.get(
            f"/api/v2/hitl/dashboard/{self.expert_id}", name="/api/v2/hitl/dashboard"
        )

    @task(3)
    def submit_review(self):
        """Submit question review"""
        # Mock task_id (in real scenario, would come from dashboard)
        task_id = f"task-{random.randint(1000, 9999)}"

        self.client.post(
            f"/api/v2/hitl/tasks/{task_id}/review",
            json={
                "task_id": task_id,
                "expert_id": self.expert_id,
                "decision": random.choice(["approve", "needs_revision", "reject"]),
                "pedagogy_score": random.randint(60, 100),
                "comments": "Reviewed by load test",
                "review_time_seconds": random.randint(60, 300),
            },
            name="/api/v2/hitl/tasks/review",
        )

    @task(1)
    def get_leaderboard(self):
        """Get expert leaderboard"""
        self.client.get(
            "/api/v2/hitl/leaderboard?limit=20", name="/api/v2/hitl/leaderboard"
        )


# Event handlers for statistics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start message"""
    print("\n" + "=" * 80)
    print("QUESTION BANK v2.0 LOAD TEST - STARTING")
    print("=" * 80)
    print("Target: 1000 concurrent users")
    print("Test duration: As configured in Locust UI")
    print("=" * 80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test completion message"""
    stats = environment.stats

    print("\n" + "=" * 80)
    print("QUESTION BANK v2.0 LOAD TEST - COMPLETED")
    print("=" * 80)
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median response time: {stats.total.median_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")
    print("=" * 80 + "\n")

    # Print slowest endpoints
    print("SLOWEST ENDPOINTS:")
    print("-" * 80)

    sorted_stats = sorted(
        [(name, stat) for name, stat in stats.entries.items()],
        key=lambda x: x[1].avg_response_time,
        reverse=True,
    )[:10]

    for name, stat in sorted_stats:
        print(
            f"{name[1]:<50} {stat.avg_response_time:>10.2f}ms (n={stat.num_requests})"
        )

    print("=" * 80 + "\n")

    # Check if performance targets met
    print("PERFORMANCE TARGETS:")
    print("-" * 80)

    avg_response_time = stats.total.avg_response_time
    p95_response_time = stats.total.get_response_time_percentile(0.95)
    failure_rate = (
        stats.total.num_failures / stats.total.num_requests * 100
        if stats.total.num_requests > 0
        else 0
    )

    checks = [
        (
            "Average response time < 200ms",
            avg_response_time < 200,
            f"{avg_response_time:.2f}ms",
        ),
        (
            "P95 response time < 500ms",
            p95_response_time < 500,
            f"{p95_response_time:.2f}ms",
        ),
        ("Failure rate < 1%", failure_rate < 1, f"{failure_rate:.2f}%"),
        (
            "Throughput > 100 req/s",
            stats.total.total_rps > 100,
            f"{stats.total.total_rps:.2f} req/s",
        ),
    ]

    passed = 0
    for check_name, check_passed, check_value in checks:
        status = "✅ PASS" if check_passed else "❌ FAIL"
        print(f"{status} - {check_name}: {check_value}")
        if check_passed:
            passed += 1

    print("-" * 80)
    print(f"OVERALL: {passed}/{len(checks)} checks passed")
    print("=" * 80 + "\n")


# Load testing scenarios
class LoadTestScenario:
    """Load test scenario configuration"""

    @staticmethod
    def get_scenario(scenario_name: str) -> dict:
        """
        Get load test scenario configuration

        Args:
            scenario_name: Scenario identifier

        Returns:
            Scenario configuration
        """
        scenarios = {
            "smoke": {
                "users": 10,
                "spawn_rate": 2,
                "duration": "1m",
                "description": "Smoke test - verify basic functionality",
            },
            "load": {
                "users": 100,
                "spawn_rate": 10,
                "duration": "5m",
                "description": "Load test - typical production load",
            },
            "stress": {
                "users": 500,
                "spawn_rate": 50,
                "duration": "10m",
                "description": "Stress test - high load scenario",
            },
            "spike": {
                "users": 1000,
                "spawn_rate": 200,
                "duration": "2m",
                "description": "Spike test - sudden traffic surge",
            },
            "endurance": {
                "users": 200,
                "spawn_rate": 20,
                "duration": "30m",
                "description": "Endurance test - sustained load over time",
            },
        }

        return scenarios.get(scenario_name, scenarios["load"])


if __name__ == "__main__":
    print(
        """
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                QUESTION BANK v2.0 LOAD TEST - WEEK 3                      ║
    ╚═══════════════════════════════════════════════════════════════════════════╝

    USAGE:
    ------
    # Basic load test (100 users)
    locust -f locustfile_week3.py --host=http://localhost:8000

    # Stress test (1000 users)
    locust -f locustfile_week3.py --host=http://localhost:8000 \\
           --users 1000 --spawn-rate 100 --run-time 5m --headless

    # With web UI
    locust -f locustfile_week3.py --host=http://localhost:8000 --web-host 127.0.0.1 --web-port 8089

    SCENARIOS:
    ----------
    1. Smoke Test:     10 users,   2/s spawn,   1 min
    2. Load Test:     100 users,  10/s spawn,   5 min  [DEFAULT]
    3. Stress Test:   500 users,  50/s spawn,  10 min
    4. Spike Test:   1000 users, 200/s spawn,   2 min  [WEEK 3 TARGET]
    5. Endurance:     200 users,  20/s spawn,  30 min

    PERFORMANCE TARGETS:
    --------------------
    ✅ Average response time: < 200ms
    ✅ P95 response time: < 500ms
    ✅ Failure rate: < 1%
    ✅ Throughput: > 100 req/s

    ENDPOINTS TESTED:
    -----------------
    - POST /api/v2/cat/start            (5 weight)
    - POST /api/v2/cat/submit           (8 weight) [Most frequent]
    - GET  /api/v2/knowledge-graph/*    (7 weight)
    - POST /api/v2/questions/generate   (1 weight) [Most expensive]
    - GET  /api/v2/hitl/*               (3 weight)
    - GET  /api/v2/health               (1 weight)

    ═══════════════════════════════════════════════════════════════════════════
    """
    )
