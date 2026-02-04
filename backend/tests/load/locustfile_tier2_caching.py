"""
Tier 2 Endpoint Caching Load Tests

Tests performance improvements for:
- /api/v1/student-dashboard/performans-trendi (performance trend)
- /api/v1/gamification/points (gamification points)

Run with:
    locust -f locustfile_tier2_caching.py --host=http://localhost:9000 --users=50 --spawn-rate=10 --run-time=2m --headless
"""

import random
from locust import HttpUser, task, between, events
from datetime import datetime

# Performance metrics tracking
performance_metrics = {
    "performans_trendi": {"uncached": [], "cached": []},
    "gamification_points": {"uncached": [], "cached": []},
}


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track response times for analysis"""
    if exception is None:
        if "performans-trendi" in name:
            performance_metrics["performans_trendi"]["cached"].append(response_time)
        elif "gamification/points" in name:
            performance_metrics["gamification_points"]["cached"].append(response_time)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print performance summary when test ends"""
    print("\n" + "=" * 80)
    print("TIER 2 CACHING PERFORMANCE SUMMARY")
    print("=" * 80)

    for endpoint, metrics in performance_metrics.items():
        if metrics["cached"]:
            avg_cached = sum(metrics["cached"]) / len(metrics["cached"])
            p95_cached = sorted(metrics["cached"])[int(len(metrics["cached"]) * 0.95)]

            print(f"\n{endpoint.upper()}:")
            print(f"  Requests: {len(metrics['cached'])}")
            print(f"  Avg Response Time: {avg_cached:.0f}ms")
            print(f"  P95 Response Time: {p95_cached:.0f}ms")
            print(f"  Min: {min(metrics['cached']):.0f}ms")
            print(f"  Max: {max(metrics['cached']):.0f}ms")

    print("\n" + "=" * 80)


class Tier2CachingUser(HttpUser):
    """
    User that simulates typical usage patterns for Tier 2 endpoints

    Task weights:
    - Performance trend: 5 (checked less frequently)
    - Gamification points: 7 (checked more frequently)
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Initialize user session"""
        # Simulate 100 different users
        self.user_id = f"user_{random.randint(1, 100)}"
        self.user_num = random.randint(1, 100)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] User {self.user_id} started")

    @task(5)
    def test_performance_trend_7_days(self):
        """Test performance trend - 7 days (fastest)"""
        with self.client.get(
            f"/api/v1/student-dashboard/performans-trendi?gun_sayisi=7",
            name="/performans-trendi [7 days]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(3)
    def test_performance_trend_30_days(self):
        """Test performance trend - 30 days (default)"""
        with self.client.get(
            f"/api/v1/student-dashboard/performans-trendi?gun_sayisi=30",
            name="/performans-trendi [30 days]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(2)
    def test_performance_trend_90_days(self):
        """Test performance trend - 90 days (slower)"""
        with self.client.get(
            f"/api/v1/student-dashboard/performans-trendi?gun_sayisi=90",
            name="/performans-trendi [90 days]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def test_performance_trend_365_days(self):
        """Test performance trend - 365 days (slowest - expects biggest improvement)"""
        with self.client.get(
            f"/api/v1/student-dashboard/performans-trendi?gun_sayisi=365",
            name="/performans-trendi [365 days]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(7)
    def test_gamification_points(self):
        """Test gamification points endpoint (most frequent)"""
        with self.client.get(
            f"/api/v1/gamification/points?user_id={self.user_id}",
            name="/gamification/points",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    json_data = response.json()
                    if json_data.get("success"):
                        response.success()
                    else:
                        response.failure(f"API returned success=false")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Failed with status {response.status_code}")


class StressTestUser(HttpUser):
    """
    Stress test user - high concurrency for cache hit rate testing

    All users query same parameters to maximize cache hits
    """

    wait_time = between(0.5, 1.5)  # Faster requests

    def on_start(self):
        """All stress test users use same parameters to test cache hits"""
        self.user_id = "stress_user_1"  # Same user to maximize cache hits

    @task(5)
    def stress_performance_trend(self):
        """Stress test - 30 days (most common query)"""
        self.client.get(
            "/api/v1/student-dashboard/performans-trendi?gun_sayisi=30",
            name="[STRESS] /performans-trendi",
        )

    @task(7)
    def stress_gamification_points(self):
        """Stress test - same user (maximize cache hits)"""
        self.client.get(
            f"/api/v1/gamification/points?user_id={self.user_id}",
            name="[STRESS] /gamification/points",
        )


# Usage Examples:
"""
# Normal load test (50 users, 2 minutes):
locust -f locustfile_tier2_caching.py --host=http://localhost:9000 --users=50 --spawn-rate=10 --run-time=2m --headless

# Stress test (200 users, 1 minute) - Test cache under pressure:
locust -f locustfile_tier2_caching.py --host=http://localhost:9000 --users=200 --spawn-rate=50 --run-time=1m --headless --user-classes StressTestUser

# Interactive mode (with web UI on http://localhost:8089):
locust -f locustfile_tier2_caching.py --host=http://localhost:9000

# Custom test (100 users, 5 minute ramp-up, 10 minute run):
locust -f locustfile_tier2_caching.py --host=http://localhost:9000 --users=100 --spawn-rate=20 --run-time=10m --headless
"""
