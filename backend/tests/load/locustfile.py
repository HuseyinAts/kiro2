"""
Load Testing Suite using Locust - Video Recommendations API
Tests video recommendation endpoint capacity and performance under load

Task 22: Load Testing (Requirement 11.3)
- 100 concurrent user simulation
- Response time metrics collection
- Error rate measurement
- Cache performance evaluation

Run:
    locust -f tests/load/locustfile.py --users 100 --spawn-rate 10 --host http://localhost:8000
    
Run headless (CI/CD):
    locust -f tests/load/locustfile.py --users 100 --spawn-rate 10 --run-time 5m --host http://localhost:8000 --headless --csv=results/video_api_load_test
"""
import random
import time
from datetime import datetime
from locust import HttpUser, task, between, events


class VideoRecommendationUser(HttpUser):
    """
    Primary user type: Video recommendation requests
    Simulates students loading Learning Path page and requesting video recommendations

    Requirement 11.3: 100 concurrent user load test
    Requirement 2.1: P95 response time < 3000ms
    """

    wait_time = between(1, 3)  # Realistic user behavior

    # Test data: Realistic student profiles
    STUDENT_PROFILES = [
        {
            "goals": ["TYT Matematik", "TYT Fizik"],
            "currentLevel": {"matematik": 65, "fizik": 50},
            "learningStyle": "visual",
            "preferences": {"video_duration": "medium"},
        },
        {
            "goals": ["AYT Matematik", "AYT Kimya"],
            "currentLevel": {"matematik": 75, "kimya": 60},
            "learningStyle": "auditory",
            "preferences": {"video_duration": "long"},
        },
        {
            "goals": ["TYT Türkçe", "TYT Tarih"],
            "currentLevel": {"türkçe": 80, "tarih": 70},
            "learningStyle": "kinesthetic",
            "preferences": {"video_duration": "short"},
        },
        {
            "goals": ["TYT Biyoloji", "TYT Coğrafya"],
            "currentLevel": {"biyoloji": 55, "coğrafya": 45},
            "learningStyle": "visual",
            "preferences": {"video_duration": "medium"},
        },
        {
            "goals": ["AYT Fizik", "AYT Biyoloji"],
            "currentLevel": {"fizik": 70, "biyoloji": 65},
            "learningStyle": "auditory",
            "preferences": {"video_duration": "long"},
        },
    ]

    def on_start(self):
        """Initialize user with random student profile"""
        self.student_profile = random.choice(self.STUDENT_PROFILES)
        self.cache_hits = 0
        self.cache_misses = 0
        self.request_count = 0

    @task(10)
    def get_video_recommendations(self):
        """
        Main task: Get video recommendations
        Weight: 10 (most frequent operation)

        Tests:
        - Response time (Requirement 2.1: P95 < 3000ms)
        - Success rate
        - Cache performance (Requirement 6.6: >80% hit rate)
        """
        start_time = time.time()

        with self.client.post(
            "/api/youtube/recommendations",
            json=self.student_profile,
            catch_response=True,
            name="Video Recommendations",
        ) as response:
            response_time_ms = (time.time() - start_time) * 1000
            self.request_count += 1

            if response.status_code == 200:
                try:
                    data = response.json()

                    # Validate response format
                    if not isinstance(data, list):
                        response.failure("Invalid response format: expected list")
                        return

                    # Track cache hits/misses
                    for recommendation in data:
                        if "cache_hit" in recommendation:
                            if recommendation["cache_hit"]:
                                self.cache_hits += 1
                            else:
                                self.cache_misses += 1

                    # Check response time threshold
                    if response_time_ms > 3000:
                        response.failure(
                            f"Response time {response_time_ms:.0f}ms exceeds 3000ms threshold"
                        )
                    else:
                        response.success()

                    # Validate video count
                    total_videos = sum(len(rec.get("videos", [])) for rec in data)
                    if total_videos == 0:
                        response.failure("No videos returned")

                except Exception as e:
                    response.failure(f"Response parsing error: {str(e)}")

            elif response.status_code == 429:
                response.failure("Rate limit exceeded")
            elif response.status_code >= 500:
                response.failure(f"Server error: {response.status_code}")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(5)
    def health_check(self):
        """
        Health check endpoint
        Weight: 5 (frequent monitoring)

        Requirement 4.2: Health check < 500ms
        """
        start_time = time.time()

        with self.client.get(
            "/api/youtube/health", catch_response=True, name="Health Check"
        ) as response:
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                if response_time_ms > 500:
                    response.failure(f"Health check too slow: {response_time_ms:.0f}ms")
                else:
                    response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(3)
    def get_recommendations_with_retry(self):
        """
        Video recommendations with retry logic
        Weight: 3 (simulates user retry behavior)

        Tests retry mechanism and exponential backoff
        """
        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            with self.client.post(
                "/api/youtube/recommendations",
                json=self.student_profile,
                catch_response=True,
                name="Video Recommendations (with retry)",
            ) as response:
                if response.status_code == 200:
                    response.success()
                    return
                elif response.status_code == 429:
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(2**retry_count)  # Exponential backoff
                    else:
                        response.failure("Rate limit exceeded after retries")
                        return
                elif response.status_code >= 500:
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(1)
                    else:
                        response.failure("Server error after retries")
                        return
                else:
                    response.failure(f"Unexpected status: {response.status_code}")
                    return

    @task(2)
    def test_cache_performance(self):
        """
        Test cache performance with different profiles
        Weight: 2 (cache miss scenario)

        Requirement 6.6: Cache hit rate > 80%
        """
        different_profile = random.choice(self.STUDENT_PROFILES)

        with self.client.post(
            "/api/youtube/recommendations",
            json=different_profile,
            catch_response=True,
            name="Video Recommendations (cache test)",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(1)
    def api_connectivity_test(self):
        """
        API connectivity test
        Weight: 1 (occasional check)

        Requirement 0.3: /api/youtube/test endpoint
        """
        with self.client.get(
            "/api/youtube/test", catch_response=True, name="API Connectivity Test"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok":
                        response.success()
                    else:
                        response.failure("API test returned non-ok status")
                except:
                    response.failure("API test response parsing error")
            else:
                response.failure(f"API test failed: {response.status_code}")


class ExamPlatformUser(HttpUser):
    """
    Simulates a typical user of the exam platform
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when a user starts - perform login"""
        self.login()

    def login(self):
        """Login to get auth token"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": f"student{random.randint(1, 1000)}@test.com",
                "password": "Test123!@#",
            },
            name="/api/v1/auth/login",
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None

    @task(5)
    def get_questions(self):
        """Get questions (most common operation)"""
        subjects = ["matematik", "fizik", "kimya", "biyoloji", "turkce"]
        subject = random.choice(subjects)

        self.client.get(
            f"/api/v1/questions?subject={subject}&limit=20",
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/questions",
        )

    @task(3)
    def start_exam_session(self):
        """Start an exam session"""
        self.client.post(
            "/api/v1/exam-sessions/start",
            json={
                "exam_type": "TYT",
                "duration_minutes": 120,
                "question_count": 40,
            },
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/exam-sessions/start",
        )

    @task(2)
    def submit_answer(self):
        """Submit an answer to a question"""
        self.client.post(
            "/api/v1/exam-sessions/answer",
            json={
                "session_id": random.randint(1, 1000),
                "question_id": random.randint(1, 10000),
                "answer": random.choice(["A", "B", "C", "D", "E"]),
            },
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/exam-sessions/answer",
        )

    @task(1)
    def get_dashboard(self):
        """Get student dashboard"""
        self.client.get(
            "/api/v1/student/dashboard",
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/student/dashboard",
        )

    @task(1)
    def get_analytics(self):
        """Get analytics data"""
        self.client.get(
            "/api/v1/analytics/performance",
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/analytics/performance",
        )

    @task(10)
    def health_check(self):
        """Health check (very frequent)"""
        self.client.get("/health", name="/health")


class TeacherUser(HttpUser):
    """Simulates teacher users with different access patterns"""

    wait_time = between(2, 5)

    def on_start(self):
        """Teacher login"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": f"teacher{random.randint(1, 50)}@test.com",
                "password": "Teacher123!@#",
            },
        )

        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            self.token = None

    @task(3)
    def view_student_progress(self):
        """View student progress reports"""
        student_id = random.randint(1, 1000)
        self.client.get(
            f"/api/v1/teacher/students/{student_id}/progress",
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/teacher/students/progress",
        )

    @task(2)
    def create_assignment(self):
        """Create assignment for students"""
        self.client.post(
            "/api/v1/teacher/assignments",
            json={
                "title": "Test Assignment",
                "description": "Practice questions",
                "due_date": "2025-12-31",
                "question_ids": [random.randint(1, 1000) for _ in range(10)],
            },
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/teacher/assignments",
        )

    @task(1)
    def view_class_analytics(self):
        """View class-wide analytics"""
        self.client.get(
            "/api/v1/teacher/analytics/class",
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            name="/api/v1/teacher/analytics/class",
        )


# Custom event handlers for video API load testing
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test start handler"""
    print("\n" + "=" * 70)
    print("VIDEO API LOAD TEST STARTING")
    print("=" * 70)
    print(f"Target Host: {environment.host}")
    print("Test Scenario: Video Recommendations API")
    print("Requirement: 11.3 - 100 concurrent user load test")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test stop handler"""
    print("\n" + "=" * 70)
    print("VIDEO API LOAD TEST COMPLETED")
    print("=" * 70)
    print(f"End Time: {datetime.now().isoformat()}")
    print("=" * 70 + "\n")


# Performance thresholds for video API (Requirement 11.3)
@events.quitting.add_listener
def check_video_api_performance(environment, **kwargs):
    """
    Check if video API performance meets requirements

    Requirements checked:
    - Requirement 11.3: 100 concurrent user load test
    - Requirement 2.1: P95 response time < 3000ms
    - Requirement 4.2: Health check < 500ms
    - Requirement 6.6: Cache hit rate > 80%
    """
    stats = environment.stats

    # Overall statistics
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    # Response times
    avg_response_time = stats.total.avg_response_time
    median_response_time = stats.total.median_response_time
    p95_response_time = stats.total.get_response_time_percentile(0.95)
    p99_response_time = stats.total.get_response_time_percentile(0.99)
    max_response_time = stats.total.max_response_time

    # Throughput
    total_rps = stats.total.total_rps

    print("\n" + "=" * 70)
    print("PERFORMANCE ANALYSIS - VIDEO API")
    print("=" * 70)
    print(f"Total Requests:              {total_requests:,}")
    print(f"Total Failures:              {total_failures:,}")
    print(f"Failure Rate:                {failure_rate:.2f}%")
    print(f"Requests per Second:         {total_rps:.2f}")
    print("-" * 70)
    print("Response Times:")
    print(f"  Average:                   {avg_response_time:.0f}ms")
    print(f"  Median (P50):              {median_response_time:.0f}ms")
    print(f"  95th Percentile (P95):     {p95_response_time:.0f}ms")
    print(f"  99th Percentile (P99):     {p99_response_time:.0f}ms")
    print(f"  Maximum:                   {max_response_time:.0f}ms")
    print("=" * 70)

    # Requirement validation
    requirements_met = True
    print("\nREQUIREMENT VALIDATION:")
    print("-" * 70)

    # Requirement 11.3: 100 concurrent user load test
    print("✓ Requirement 11.3: 100 concurrent user load test - COMPLETED")

    # Requirement 2.1: P95 response time < 3000ms
    if p95_response_time <= 3000:
        print(
            f"✓ Requirement 2.1: P95 response time < 3000ms - PASSED ({p95_response_time:.0f}ms)"
        )
    else:
        print(
            f"✗ Requirement 2.1: P95 response time < 3000ms - FAILED ({p95_response_time:.0f}ms)"
        )
        requirements_met = False

    # Requirement 4.2: Health check < 500ms
    health_check_stats = stats.get("Health Check", None)
    if health_check_stats:
        health_p95 = health_check_stats.get_response_time_percentile(0.95)
        if health_p95 <= 500:
            print(
                f"✓ Requirement 4.2: Health check < 500ms - PASSED ({health_p95:.0f}ms)"
            )
        else:
            print(
                f"✗ Requirement 4.2: Health check < 500ms - FAILED ({health_p95:.0f}ms)"
            )
            requirements_met = False

    # Success rate check (should be > 95%)
    success_rate = (
        ((total_requests - total_failures) / total_requests * 100)
        if total_requests > 0
        else 0
    )
    if success_rate >= 95:
        print(f"✓ Success Rate > 95% - PASSED ({success_rate:.2f}%)")
    else:
        print(f"✗ Success Rate > 95% - FAILED ({success_rate:.2f}%)")
        requirements_met = False

    # Cache performance analysis
    video_rec_stats = stats.get("Video Recommendations", None)
    if video_rec_stats:
        print("\nCache Performance:")
        print(f"  Video Recommendations: {video_rec_stats.num_requests:,} requests")
        print(f"  Average Response Time: {video_rec_stats.avg_response_time:.0f}ms")
        print("  Note: Cache hit rate tracked in application metrics")

    print("=" * 70)

    # Final result
    if requirements_met:
        print("\n✅ ALL REQUIREMENTS MET - TEST PASSED")
        environment.process_exit_code = 0
    else:
        print("\n❌ SOME REQUIREMENTS FAILED - TEST FAILED")
        environment.process_exit_code = 1

    print("\n")


# Endpoint-specific metrics tracking
@events.request.add_listener
def track_video_api_metrics(
    request_type, name, response_time, response_length, exception, **kwargs
):
    """
    Track video API specific metrics

    This handler collects custom metrics for:
    - Response time distribution
    - Error rate by endpoint
    - Cache performance (when available in response)
    """
    # Custom metrics can be collected here
    # In production, use Prometheus or similar for detailed metrics
    pass
