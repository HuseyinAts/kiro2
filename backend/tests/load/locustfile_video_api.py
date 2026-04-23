"""
Load Testing - Video API
Locust load test for video recommendation endpoint

Requirements: 2.1, 2.5
Target: 100 concurrent users, P95 < 3s
"""

import random
import time
from datetime import datetime

from locust import HttpUser, between, events, task


class VideoAPIUser(HttpUser):
    """
    Simulated user for video API load testing
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a user starts"""
        self.student_profiles = self.generate_student_profiles()
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def generate_student_profiles(self):
        """Generate diverse student profiles for testing"""
        subjects = ["matematik", "fizik", "kimya", "biyoloji", "türkçe"]
        learning_styles = ["visual", "auditory", "kinesthetic"]

        profiles = []
        for i in range(10):
            profile = {
                "goals": random.sample(subjects, k=random.randint(1, 3)),
                "currentLevel": {
                    subject: random.randint(30, 90) for subject in subjects
                },
                "learningStyle": random.choice(learning_styles),
                "preferences": {
                    "video_duration": random.choice(["short", "medium", "long"]),
                    "channel_preference": [],
                },
            }
            profiles.append(profile)

        return profiles

    @task(10)
    def get_video_recommendations(self):
        """
        Main task: Get video recommendations
        Weight: 10 (most common operation)
        """
        profile = random.choice(self.student_profiles)

        start_time = time.time()

        with self.client.post(
            "/api/youtube/recommendations",
            json=profile,
            catch_response=True,
            name="Get Video Recommendations",
        ) as response:
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Track cache hits/misses
                if isinstance(data, list) and len(data) > 0:
                    cache_hit = data[0].get("cache_hit", False)
                    if cache_hit:
                        self.cache_hits += 1
                    else:
                        self.cache_misses += 1

                self.request_count += 1

                # Check response time
                if response_time > 3.0:
                    response.failure(
                        f"Response time {response_time:.2f}s exceeds 3s target"
                    )
                else:
                    response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def health_check(self):
        """
        Task: Health check endpoint
        Weight: 2 (occasional monitoring)
        """
        with self.client.get(
            "/api/youtube/health", catch_response=True, name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Health check failed with status {response.status_code}"
                )

    @task(1)
    def test_endpoint(self):
        """
        Task: Test endpoint connectivity
        Weight: 1 (rare)
        """
        with self.client.get(
            "/api/youtube/test", catch_response=True, name="Test Endpoint"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure("Test endpoint failed")


class CacheOptimizedUser(HttpUser):
    """
    User that repeatedly requests same content (cache optimization test)
    """

    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Initialize with fixed profile for cache testing"""
        self.profile = {
            "goals": ["matematik", "fizik"],
            "currentLevel": {"matematik": 50, "fizik": 50},
            "learningStyle": "visual",
            "preferences": {},
        }

    @task
    def get_cached_recommendations(self):
        """Request same profile repeatedly to test cache"""
        with self.client.post(
            "/api/youtube/recommendations",
            json=self.profile,
            catch_response=True,
            name="Cached Recommendations",
        ) as response:
            if response.status_code == 200:
                # Should be fast due to caching
                if response.elapsed.total_seconds() > 0.5:
                    response.failure(
                        f"Cached response too slow: {response.elapsed.total_seconds():.2f}s"
                    )
                else:
                    response.success()
            else:
                response.failure("Request failed")


# Event listeners for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("\n" + "=" * 60)
    print("LOAD TEST STARTED - Video API")
    print("=" * 60)
    print(f"Start Time: {datetime.now().isoformat()}")
    print("Target: 100 concurrent users")
    print("Performance Target: P95 < 3s")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("\n" + "=" * 60)
    print("LOAD TEST COMPLETED")
    print("=" * 60)
    print(f"End Time: {datetime.now().isoformat()}")

    # Calculate statistics
    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures

    if total_requests > 0:
        failure_rate = (total_failures / total_requests) * 100
        print("\nResults:")
        print(f"  Total Requests:  {total_requests}")
        print(f"  Total Failures:  {total_failures}")
        print(f"  Failure Rate:    {failure_rate:.2f}%")
        print(f"  Avg Response:    {stats.total.avg_response_time:.0f}ms")
        print(f"  Min Response:    {stats.total.min_response_time:.0f}ms")
        print(f"  Max Response:    {stats.total.max_response_time:.0f}ms")
        print(f"  RPS:             {stats.total.total_rps:.2f}")

    print("=" * 60 + "\n")


# Custom shape for ramping load test
from locust import LoadTestShape


class RampUpShape(LoadTestShape):
    """
    Ramp up load test:
    - Start with 10 users
    - Ramp up to 100 users over 5 minutes
    - Hold at 100 users for 10 minutes
    - Ramp down to 0 over 2 minutes
    """

    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 180, "users": 50, "spawn_rate": 5},
        {"duration": 300, "users": 100, "spawn_rate": 10},
        {"duration": 900, "users": 100, "spawn_rate": 0},  # Hold
        {"duration": 1020, "users": 0, "spawn_rate": 10},  # Ramp down
    ]

    def tick(self):
        """Return user count and spawn rate for current time"""
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])

        return None
