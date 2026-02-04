"""
Locust Load Test Suite for Learning Path API
Teknofest 2025 - Türkiye Üniversite Sınavları Hazırlık Platformu

P1.3 Gap Fix: Load testing for Learning Path system
- Tests 100+ concurrent users
- Simulates realistic usage patterns
- Monitors performance under load
- Validates scalability

Requirements:
- locust >= 2.20.0
- Targets P95 < 5000ms for path creation
- Success rate > 95%

Usage:
    # Run from backend/tests/load/
    locust -f locustfile_learning_path.py --host=http://localhost:8001

    # Run with web UI
    locust -f locustfile_learning_path.py --host=http://localhost:8001 --web-host=0.0.0.0

    # Run headless (CLI mode)
    locust -f locustfile_learning_path.py --host=http://localhost:8001 \
           --users=100 --spawn-rate=10 --run-time=5m --headless

    # Generate HTML report
    locust -f locustfile_learning_path.py --host=http://localhost:8001 \
           --users=100 --spawn-rate=10 --run-time=5m --headless \
           --html=report.html
"""

import logging
import random
import time
from typing import Dict, List, Any

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

logger = logging.getLogger(__name__)


# ==================== Test Data Configuration ====================

# Subjects for testing (Turkish educational subjects)
SUBJECTS = ["matematik", "fizik", "kimya", "biyoloji", "tarih", "coğrafya"]

# Topics by subject
TOPICS_BY_SUBJECT = {
    "matematik": [
        "türev",
        "integral",
        "limit",
        "fonksiyon",
        "geometri",
        "trigonometri",
    ],
    "fizik": ["hareket", "kuvvet", "enerji", "elektrik", "manyetizma", "optik"],
    "kimya": [
        "atom",
        "molekül",
        "reaksiyon",
        "asit-baz",
        "kimyasal denge",
        "organik kimya",
    ],
    "biyoloji": ["hücre", "genetik", "ekosistem", "evrim", "sindirim", "solunum"],
    "tarih": ["osmanlı", "cumhuriyet", "dünya savaşları", "atatürk", "türk tarihi"],
    "coğrafya": [
        "iklim",
        "bitki örtüsü",
        "nüfus",
        "ekonomi",
        "harita",
        "doğal afetler",
    ],
}

# Difficulty levels
DIFFICULTY_LEVELS = ["kolay", "orta", "zor"]

# Grade levels (Turkish education system: 9-12)
GRADE_LEVELS = [9, 10, 11, 12]

# Learning styles
LEARNING_STYLES = ["visual", "auditory", "kinesthetic", "mixed"]

# Exam targets
EXAM_TARGETS = ["TYT", "AYT", "YKS", "LGS"]


# ==================== Helper Functions ====================


def generate_student_id() -> str:
    """Generate a random student ID for testing"""
    return f"LOAD_TEST_STU_{random.randint(10000, 99999)}"


def generate_student_profile() -> Dict[str, Any]:
    """Generate random student profile data"""
    return {
        "student_id": generate_student_id(),
        "name": f"Load Test Student {random.randint(1, 1000)}",
        "grade": str(random.choice(GRADE_LEVELS)),
        "exam_target": random.choice(EXAM_TARGETS),
        "learning_style": random.choice(LEARNING_STYLES),
        "knowledge_level": random.choice(["beginner", "intermediate", "advanced"]),
        "interests": random.sample(SUBJECTS, k=random.randint(2, 4)),
        "goals": [f"YKS başarısı", f"Derste başarılı olmak"],
        "available_time": random.choice([60, 90, 120, 180]),
    }


def generate_learning_path_request() -> Dict[str, Any]:
    """Generate random learning path creation request"""
    subject = random.choice(SUBJECTS)
    return {
        "student_id": generate_student_id(),
        "subject": subject,
        "difficulty_level": random.choice(DIFFICULTY_LEVELS),
        "duration_weeks": random.choice([2, 4, 6, 8]),
        "target_date": None,  # Optional
    }


def generate_resource_search_request() -> Dict[str, Any]:
    """Generate random resource search request"""
    subject = random.choice(SUBJECTS)
    topics = TOPICS_BY_SUBJECT.get(subject, [])
    topic = random.choice(topics) if topics else None

    return {
        "subject": subject,
        "topic": topic,
        "difficulty": random.choice(DIFFICULTY_LEVELS),
        "resource_type": "video",
        "max_results": random.choice([5, 10, 15, 20]),
    }


def generate_quiz_submission(quiz_id: str = "QZ_LOAD_TEST_001") -> Dict[str, Any]:
    """Generate random quiz submission"""
    question_count = 10
    answers = []

    for i in range(1, question_count + 1):
        answers.append(
            {
                "question_id": f"Q{i}",
                "answer": random.choice(["A", "B", "C", "D"]),
                "time_spent": random.randint(10, 120),  # 10-120 seconds per question
            }
        )

    return {"student_id": generate_student_id(), "quiz_id": quiz_id, "answers": answers}


def generate_completion_update() -> Dict[str, Any]:
    """Generate random topic completion update"""
    num_completions = random.randint(1, 5)
    completions = {}

    for i in range(num_completions):
        module_id = f"MOD{random.randint(1, 3)}"
        topic_id = f"TOP{random.randint(1, 10)}"
        node_id = f"{module_id}-{topic_id}"
        completions[node_id] = random.choice([True, False])

    return {"student_id": generate_student_id(), "completions": completions}


# ==================== Locust User Classes ====================


class LearningPathUser(HttpUser):
    """
    Base Learning Path user with realistic behavior

    Simulates a student using the Learning Path system:
    - Creates learning paths
    - Searches for resources
    - Submits quizzes
    - Updates progress
    """

    # Wait time between tasks (simulate realistic user think time)
    wait_time = between(1, 3)  # 1-3 seconds between actions

    # User state
    student_id = None
    current_path_id = None

    def on_start(self):
        """Initialize user session"""
        self.student_id = generate_student_id()
        logger.info(f"User started: {self.student_id}")

    @task(2)
    def create_learning_path(self):
        """
        Task: Create a learning path (weight: 2)

        This is a heavy operation that involves AI agent processing.
        Expected duration: 15-30 seconds
        Target P95: < 5000ms (if cached/optimized)
        """
        request_data = generate_learning_path_request()
        request_data["student_id"] = self.student_id

        with self.client.post(
            "/api/learning-path/create-path",
            json=request_data,
            catch_response=True,
            name="/api/learning-path/create-path",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        self.current_path_id = data.get("learning_path", {}).get(
                            "path_id"
                        )
                        response.success()
                    else:
                        response.failure(f"API returned success=false: {data}")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:200]}")

    @task(7)
    def search_resources(self):
        """
        Task: Search for educational resources (weight: 7)

        This is the most common operation (70% of requests).
        Expected duration: 1-5 seconds
        Target P95: < 3000ms
        """
        request_data = generate_resource_search_request()

        with self.client.post(
            "/api/learning-path/search-resources",
            json=request_data,
            catch_response=True,
            name="/api/learning-path/search-resources",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        resource_count = data.get("total", 0)
                        if resource_count > 0:
                            response.success()
                        else:
                            # Empty results are OK but track them
                            response.success()
                            logger.debug(
                                f"Empty search results for {request_data['subject']}"
                            )
                    else:
                        response.failure(f"API returned success=false")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def submit_quiz(self):
        """
        Task: Submit a quiz (weight: 1)

        Less common operation (10% of requests).
        Expected duration: 0.5-2 seconds
        Target P95: < 2000ms
        """
        quiz_id = f"QZ_LOAD_TEST_{random.randint(1, 100)}"
        request_data = generate_quiz_submission(quiz_id)
        request_data["student_id"] = self.student_id

        with self.client.post(
            f"/api/learning-path/quiz/{quiz_id}/submit",
            json=request_data,
            catch_response=True,
            name="/api/learning-path/quiz/submit",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        score = data.get("score", 0)
                        passed = data.get("passed", False)
                        response.success()
                        logger.debug(f"Quiz submitted: score={score}, passed={passed}")
                    else:
                        response.failure("API returned success=false")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def update_completion_status(self):
        """
        Task: Update topic completion status (weight: 1)

        Moderate operation (10% of requests).
        Expected duration: 0.2-1 seconds
        Target P95: < 1000ms
        """
        request_data = generate_completion_update()
        request_data["student_id"] = self.student_id

        with self.client.put(
            f"/api/learning-path/completion/{self.student_id}",
            json=request_data,
            catch_response=True,
            name="/api/learning-path/completion/update",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        response.success()
                    else:
                        response.failure("API returned success=false")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def get_completion_status(self):
        """
        Task: Get topic completion status (weight: 1)

        Read operation, should be fast.
        Expected duration: 0.1-0.5 seconds
        Target P95: < 500ms
        """
        with self.client.get(
            f"/api/learning-path/completion/{self.student_id}",
            catch_response=True,
            name="/api/learning-path/completion/get",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        response.success()
                    else:
                        response.failure("API returned success=false")
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)
    def health_check(self):
        """
        Task: Health check endpoint (weight: 1)

        Sanity check to ensure API is responsive.
        Expected duration: < 0.1 seconds
        Target P95: < 100ms
        """
        with self.client.get(
            "/api/learning-path/health",
            catch_response=True,
            name="/api/learning-path/health",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


# ==================== Load Test Events ====================


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Event handler: Test started"""
    logger.info("=" * 80)
    logger.info("Learning Path Load Test Started")
    logger.info(f"Host: {environment.host}")
    logger.info(
        f"Users: {environment.parsed_options.num_users if hasattr(environment, 'parsed_options') else 'N/A'}"
    )
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Event handler: Test stopped"""
    logger.info("=" * 80)
    logger.info("Learning Path Load Test Completed")
    logger.info("=" * 80)

    # Print summary if available
    if hasattr(environment, "stats") and environment.stats:
        stats = environment.stats
        logger.info("\n📊 Performance Summary:")
        logger.info(f"Total Requests: {stats.total.num_requests}")
        logger.info(f"Failed Requests: {stats.total.num_failures}")
        logger.info(f"Success Rate: {(1 - stats.total.fail_ratio) * 100:.2f}%")
        logger.info(f"RPS (requests/sec): {stats.total.total_rps:.2f}")
        logger.info(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
        logger.info(
            f"P50 Response Time: {stats.total.get_response_time_percentile(0.50):.2f}ms"
        )
        logger.info(
            f"P95 Response Time: {stats.total.get_response_time_percentile(0.95):.2f}ms"
        )
        logger.info(
            f"P99 Response Time: {stats.total.get_response_time_percentile(0.99):.2f}ms"
        )


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Event handler: Each request completion"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")


# ==================== Custom Load Test Scenarios ====================


class SpikeTestUser(HttpUser):
    """
    Spike test user - simulates sudden traffic spike

    Usage:
        locust -f locustfile_learning_path.py --user-classes=SpikeTestUser
    """

    wait_time = between(0.1, 0.5)  # Aggressive wait time

    @task
    def spike_search(self):
        """Aggressive resource search"""
        request_data = generate_resource_search_request()
        self.client.post("/api/learning-path/search-resources", json=request_data)


class StressTestUser(HttpUser):
    """
    Stress test user - pushes system to limits

    Usage:
        locust -f locustfile_learning_path.py --user-classes=StressTestUser
    """

    wait_time = between(0, 0.1)  # Minimal wait time

    @task(5)
    def stress_search(self):
        """Stress test: resource search"""
        request_data = generate_resource_search_request()
        self.client.post("/api/learning-path/search-resources", json=request_data)

    @task(1)
    def stress_quiz(self):
        """Stress test: quiz submission"""
        quiz_id = f"STRESS_QZ_{random.randint(1, 1000)}"
        request_data = generate_quiz_submission(quiz_id)
        self.client.post(f"/api/learning-path/quiz/{quiz_id}/submit", json=request_data)


# ==================== Test Configuration Presets ====================

"""
Recommended Load Test Configurations:

1. Smoke Test (Quick validation):
   locust -f locustfile_learning_path.py --host=http://localhost:8001 \
          --users=5 --spawn-rate=1 --run-time=1m --headless

2. Normal Load Test:
   locust -f locustfile_learning_path.py --host=http://localhost:8001 \
          --users=50 --spawn-rate=5 --run-time=5m --headless

3. Peak Load Test:
   locust -f locustfile_learning_path.py --host=http://localhost:8001 \
          --users=100 --spawn-rate=10 --run-time=10m --headless

4. Stress Test:
   locust -f locustfile_learning_path.py --host=http://localhost:8001 \
          --user-classes=StressTestUser --users=200 --spawn-rate=20 \
          --run-time=5m --headless

5. Spike Test:
   locust -f locustfile_learning_path.py --host=http://localhost:8001 \
          --user-classes=SpikeTestUser --users=500 --spawn-rate=100 \
          --run-time=2m --headless

Expected Performance Targets:
- Success Rate: > 95%
- P50 Response Time (search): < 1500ms
- P95 Response Time (search): < 3000ms
- P95 Response Time (create-path): < 5000ms
- Throughput: > 100 requests/sec (at 100 users)
"""
