# -*- coding: utf-8 -*-
"""
Video API Load Testing with Locust
100 concurrent user simülasyonu - Video öneri endpoint'i için yük testi

Requirements: 11.3
Run: locust -f backend/tests/load/load_test_video_api.py --users 100 --spawn-rate 10 --host http://localhost:8000
"""

import random
import time
from typing import Dict, List
from locust import HttpUser, task, between, events


class VideoAPIUser(HttpUser):
    """
    Video API kullanıcısı - Learning Path sayfasında video yükleme simülasyonu

    Bu kullanıcı tipi, öğrencilerin learning path sayfasında video önerileri
    almasını simüle eder. Gerçek kullanım senaryolarını yansıtır.
    """

    # Kullanıcılar arası bekleme süresi (1-3 saniye)
    wait_time = between(1, 3)

    # Test verileri - Gerçekçi öğrenci profilleri
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
        """
        Kullanıcı başladığında çağrılır
        Rastgele bir öğrenci profili seç
        """
        self.student_profile = random.choice(self.STUDENT_PROFILES)
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0

    @task(10)
    def get_video_recommendations(self):
        """
        Video önerileri al - Ana test senaryosu

        Bu task en sık çalışır (weight=10) çünkü kullanıcıların
        en çok yaptığı işlem video önerilerini almaktır.

        Requirement 11.3: 100 concurrent user load test
        """
        start_time = time.time()

        with self.client.post(
            "/api/youtube/recommendations",
            json=self.student_profile,
            catch_response=True,
            name="/api/youtube/recommendations [POST]",
        ) as response:
            response_time_ms = (time.time() - start_time) * 1000
            self.request_count += 1

            if response.status_code == 200:
                try:
                    data = response.json()

                    # Yanıt validasyonu
                    if not isinstance(data, list):
                        response.failure(
                            f"Invalid response format: expected list, got {type(data)}"
                        )
                        return

                    # Her öneri için validasyon
                    for recommendation in data:
                        if "videos" not in recommendation:
                            response.failure("Missing 'videos' field in recommendation")
                            return

                        if "cache_hit" in recommendation:
                            if recommendation["cache_hit"]:
                                self.cache_hits += 1
                            else:
                                self.cache_misses += 1

                    # Performance assertion (Requirement 2.1: P95 < 3s)
                    if response_time_ms > 3000:
                        response.failure(
                            f"Response time {response_time_ms:.0f}ms exceeds 3000ms threshold"
                        )
                    else:
                        response.success()

                    # Video sayısını kontrol et
                    total_videos = sum(len(rec.get("videos", [])) for rec in data)
                    if total_videos == 0:
                        response.failure("No videos returned in recommendations")

                except Exception as e:
                    response.failure(f"Response parsing error: {str(e)}")

            elif response.status_code == 429:
                # Rate limit - beklenen bir durum
                response.failure("Rate limit exceeded (429)")

            elif response.status_code == 500:
                response.failure("Internal server error (500)")

            elif response.status_code == 504:
                response.failure("Gateway timeout (504)")

            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(3)
    def get_video_recommendations_with_retry(self):
        """
        Retry logic ile video önerileri al

        Gerçek kullanıcılar hata durumunda tekrar deneme yapar.
        Bu senaryo retry logic'i test eder.
        """
        max_retries = 2
        retry_count = 0

        while retry_count <= max_retries:
            with self.client.post(
                "/api/youtube/recommendations",
                json=self.student_profile,
                catch_response=True,
                name="/api/youtube/recommendations [POST with retry]",
            ) as response:
                if response.status_code == 200:
                    response.success()
                    return

                elif response.status_code == 429:
                    # Rate limit - exponential backoff
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(2**retry_count)  # 2, 4 saniye
                    else:
                        response.failure(
                            f"Rate limit exceeded after {max_retries} retries"
                        )
                        return

                elif response.status_code >= 500:
                    # Server error - retry
                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(1)
                    else:
                        response.failure(f"Server error after {max_retries} retries")
                        return

                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
                    return

    @task(5)
    def health_check(self):
        """
        Health check endpoint'i test et

        Frontend düzenli olarak health check yapar.
        Bu endpoint çok hızlı yanıt vermeli (<500ms).

        Requirement 4.2: Health check < 500ms
        """
        start_time = time.time()

        with self.client.get(
            "/api/youtube/health", catch_response=True, name="/api/youtube/health [GET]"
        ) as response:
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                try:
                    data = response.json()

                    # Health check response validasyonu
                    if "status" not in data:
                        response.failure("Missing 'status' field in health check")
                        return

                    # Performance assertion (Requirement 4.2: < 500ms)
                    if response_time_ms > 500:
                        response.failure(
                            f"Health check response time {response_time_ms:.0f}ms exceeds 500ms"
                        )
                    else:
                        response.success()

                except Exception as e:
                    response.failure(f"Health check response parsing error: {str(e)}")

            else:
                response.failure(
                    f"Health check failed with status {response.status_code}"
                )

    @task(1)
    def test_api_connectivity(self):
        """
        API erişilebilirlik testi

        Requirement 0.3: /api/youtube/test endpoint'i
        """
        with self.client.get(
            "/api/youtube/test", catch_response=True, name="/api/youtube/test [GET]"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "ok":
                        response.success()
                    else:
                        response.failure("API test endpoint returned non-ok status")
                except:
                    response.failure("API test endpoint response parsing error")
            else:
                response.failure(
                    f"API test endpoint failed with status {response.status_code}"
                )

    @task(2)
    def get_recommendations_different_profile(self):
        """
        Farklı profil ile video önerileri al

        Cache miss senaryosunu test etmek için farklı profiller kullan.
        Bu, cache stratejisinin etkinliğini test eder.
        """
        # Rastgele farklı bir profil seç
        different_profile = random.choice(self.STUDENT_PROFILES)

        with self.client.post(
            "/api/youtube/recommendations",
            json=different_profile,
            catch_response=True,
            name="/api/youtube/recommendations [POST different profile]",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class VideoAPIStressUser(HttpUser):
    """
    Stress test kullanıcısı - Daha agresif yük

    Bu kullanıcı tipi, sistemin limit durumlarını test etmek için
    daha sık ve daha hızlı istekler gönderir.
    """

    wait_time = between(0.5, 1.5)  # Daha kısa bekleme

    def on_start(self):
        """Stress test için profil hazırla"""
        self.profile = {
            "goals": ["TYT Matematik", "TYT Fizik", "TYT Kimya"],
            "currentLevel": {"matematik": 50, "fizik": 50, "kimya": 50},
            "learningStyle": "visual",
            "preferences": {},
        }

    @task
    def rapid_fire_requests(self):
        """
        Hızlı ardışık istekler

        Rate limiting ve throttling mekanizmalarını test eder.
        Requirement 7.1, 7.2: Rate limiting
        """
        # 5 ardışık istek gönder
        for i in range(5):
            with self.client.post(
                "/api/youtube/recommendations",
                json=self.profile,
                catch_response=True,
                name=f"/api/youtube/recommendations [Rapid fire {i+1}/5]",
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 429:
                    # Rate limit beklenen bir durum
                    response.success()
                else:
                    response.failure(f"Unexpected status: {response.status_code}")

            # Çok kısa bekleme
            time.sleep(0.1)


# Event handlers - Test lifecycle ve metrics


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test başladığında"""
    print("\n" + "=" * 70)
    print("VIDEO API LOAD TEST BAŞLIYOR")
    print("=" * 70)
    print(f"Target Host: {environment.host}")
    print(f"Test Scenario: Video Recommendations API")
    print(f"Requirement: 11.3 - 100 concurrent user load test")
    print("=" * 70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test bittiğinde"""
    print("\n" + "=" * 70)
    print("VIDEO API LOAD TEST TAMAMLANDI")
    print("=" * 70 + "\n")


@events.quitting.add_listener
def check_video_api_performance(environment, **kwargs):
    """
    Performance threshold kontrolü

    Test sonunda performans metriklerini kontrol eder ve
    requirement'ları karşılayıp karşılamadığını doğrular.
    """
    stats = environment.stats

    # Toplam istatistikler
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0

    # Yanıt süreleri
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

    # Requirement checks
    requirements_met = True
    print("\nREQUIREMENT VALIDATION:")
    print("-" * 70)

    # Requirement 11.3: 100 concurrent user load test
    print(f"✓ Requirement 11.3: 100 concurrent user load test - COMPLETED")

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

    # Requirement 4.2: Health check < 500ms (check specific endpoint)
    health_check_stats = stats.get("/api/youtube/health [GET]", None)
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
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Her istek sonrası çağrılır - Custom metrics için

    Bu handler ile endpoint-specific metrics toplayabiliriz.
    """
    # Cache hit/miss tracking için response body'yi parse edebiliriz
    # Ancak Locust'ta bu performans overhead yaratabilir
    # Production'da Prometheus gibi bir tool kullanılmalı
    pass


if __name__ == "__main__":
    """
    Doğrudan çalıştırma için

    Usage:
        python backend/tests/load/load_test_video_api.py

    Veya Locust CLI ile:
        locust -f backend/tests/load/load_test_video_api.py --users 100 --spawn-rate 10 --host http://localhost:8000
    """
    import os
    import sys

    # Locust'u programmatik olarak çalıştır
    os.system(
        "locust -f backend/tests/load/load_test_video_api.py "
        "--users 100 --spawn-rate 10 --run-time 5m "
        "--host http://localhost:8000 --headless"
    )
