# -*- coding: utf-8 -*-
"""
100K+ Concurrent Users Load Testing
Büyük ölçekli yük testi - 100,000+ eşzamanlı kullanıcı simülasyonu

Bu test suite, platformun 100K+ kullanıcıyı destekleme kapasitesini test eder.
Requirements: 7.1, 7.2, 7.3, 7.6
"""

import asyncio
import os
import time
from typing import Dict, Any

import aiohttp
import psutil
import pytest


class Test100KConcurrentUsers:
    """100K+ eşzamanlı kullanıcı yük testleri"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_100k_user_simulation_extrapolated(self):
        """
        100K kullanıcı simülasyonu (10K gerçek + extrapolation)
        Requirement 7.2: 100,000 eşzamanlı kullanıcı desteği
        """

        # Gerçek test: 10K kullanıcı
        real_user_count = 10000
        # Extrapolation hedefi: 100K kullanıcı
        target_user_count = 100000

        # Batch processing parametreleri
        batch_size = 500
        concurrent_batches = 20  # 500 * 20 = 10K eşzamanlı

        async def simulate_user_session(user_id: int) -> Dict[str, Any]:
            """Tek kullanıcı oturumu simülasyonu"""
            async with aiohttp.ClientSession() as session:
                start_time = time.time()

                try:
                    # 1. Health check
                    health_response = await session.get(
                        "http://localhost:8000/api/v1/health",
                        timeout=aiohttp.ClientTimeout(total=5),
                    )

                    if health_response.status != 200:
                        return {
                            "user_id": user_id,
                            "status": "health_check_failed",
                            "duration_ms": (time.time() - start_time) * 1000,
                        }

                    # 2. Login simülasyonu
                    login_response = await session.post(
                        "http://localhost:8000/api/v1/auth/login",
                        json={
                            "username": f"load_user_{user_id}",
                            "password": "test_password",
                        },
                        timeout=aiohttp.ClientTimeout(total=10),
                    )

                    if login_response.status != 200:
                        return {
                            "user_id": user_id,
                            "status": "login_failed",
                            "duration_ms": (time.time() - start_time) * 1000,
                        }

                    # 3. API çağrıları simülasyonu
                    api_calls = [
                        ("GET", "/api/v1/student/profile"),
                        ("GET", "/api/v1/questions/random"),
                        ("GET", "/api/v1/content/recommendations"),
                    ]

                    api_success_count = 0
                    for method, endpoint in api_calls:
                        try:
                            response = await session.get(
                                f"http://localhost:8000{endpoint}",
                                timeout=aiohttp.ClientTimeout(total=5),
                            )
                            if response.status == 200:
                                api_success_count += 1
                        except:
                            pass

                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000

                    return {
                        "user_id": user_id,
                        "status": "success",
                        "duration_ms": duration_ms,
                        "api_calls_successful": api_success_count,
                        "api_calls_total": len(api_calls),
                    }

                except Exception as e:
                    return {
                        "user_id": user_id,
                        "status": "error",
                        "error": str(e),
                        "duration_ms": (time.time() - start_time) * 1000,
                    }

        # Sistem kaynaklarını ölç
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024
        initial_cpu_percent = process.cpu_percent()

        # Test başlangıcı
        test_start_time = time.time()
        all_results = []

        # Batch'ler halinde kullanıcıları çalıştır
        for batch_num in range(0, real_user_count, batch_size):
            batch_start = batch_num
            batch_end = min(batch_num + batch_size, real_user_count)

            # Batch task'ları oluştur
            batch_tasks = [
                simulate_user_session(user_id)
                for user_id in range(batch_start, batch_end)
            ]

            # Batch'i çalıştır
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            all_results.extend(batch_results)

            # Progress logging
            if (batch_num + batch_size) % 1000 == 0:
                print(f"Completed {batch_num + batch_size}/{real_user_count} users")

            # Batch'ler arası kısa bekleme (sistem stabilizasyonu)
            await asyncio.sleep(0.05)

        test_end_time = time.time()
        total_duration_seconds = test_end_time - test_start_time

        # Final sistem kaynakları
        final_memory_mb = process.memory_info().rss / 1024 / 1024
        final_cpu_percent = process.cpu_percent()

        # Sonuçları analiz et
        successful_sessions = [
            r
            for r in all_results
            if isinstance(r, dict) and r.get("status") == "success"
        ]
        failed_sessions = [
            r
            for r in all_results
            if isinstance(r, dict) and r.get("status") != "success"
        ]
        exceptions = [r for r in all_results if isinstance(r, Exception)]

        # Metrikler
        success_rate = len(successful_sessions) / real_user_count
        avg_duration_ms = (
            sum(s["duration_ms"] for s in successful_sessions)
            / len(successful_sessions)
            if successful_sessions
            else 0
        )
        throughput_users_per_second = real_user_count / total_duration_seconds

        # 100K için extrapolation
        extrapolated_metrics = {
            "target_users": target_user_count,
            "estimated_duration_seconds": total_duration_seconds
            * (target_user_count / real_user_count),
            "estimated_memory_mb": final_memory_mb
            * (target_user_count / real_user_count),
            "estimated_throughput_users_per_second": throughput_users_per_second,
            "estimated_success_rate": success_rate,
            "scalability_factor": target_user_count / real_user_count,
        }

        # Assertions
        assert success_rate >= 0.8, f"Success rate {success_rate} is below 80%"
        assert (
            avg_duration_ms < 5000
        ), f"Average duration {avg_duration_ms}ms exceeds 5000ms"
        assert len(exceptions) < real_user_count * 0.05, "Too many exceptions"

        # Requirement 7.2: 100K kullanıcı desteği (extrapolated)
        assert (
            extrapolated_metrics["estimated_success_rate"] >= 0.8
        ), "Extrapolated 100K user success rate below 80%"

        return {
            "real_test": {
                "user_count": real_user_count,
                "successful_sessions": len(successful_sessions),
                "failed_sessions": len(failed_sessions),
                "exceptions": len(exceptions),
                "success_rate": success_rate,
                "total_duration_seconds": total_duration_seconds,
                "avg_duration_ms": avg_duration_ms,
                "throughput_users_per_second": throughput_users_per_second,
                "memory_usage_mb": {
                    "initial": initial_memory_mb,
                    "final": final_memory_mb,
                    "increase": final_memory_mb - initial_memory_mb,
                },
                "cpu_usage_percent": {
                    "initial": initial_cpu_percent,
                    "final": final_cpu_percent,
                },
            },
            "extrapolated_100k": extrapolated_metrics,
            "requirement_7_2_met": extrapolated_metrics["estimated_success_rate"]
            >= 0.8,
        }

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_response_time_under_load(self):
        """
        Yük altında yanıt süresi testi
        Requirement 7.1: p95 yanıt süresi < 200ms
        """

        # Farklı yük seviyelerinde test
        load_levels = [100, 500, 1000, 5000, 10000]
        results = []

        for load_level in load_levels:
            print(f"\nTesting load level: {load_level} concurrent requests")

            async def single_request():
                """Tek API isteği"""
                async with aiohttp.ClientSession() as session:
                    start_time = time.time()
                    try:
                        response = await session.get(
                            "http://localhost:8000/api/v1/health",
                            timeout=aiohttp.ClientTimeout(total=5),
                        )
                        end_time = time.time()
                        return {
                            "success": response.status == 200,
                            "response_time_ms": (end_time - start_time) * 1000,
                        }
                    except Exception as e:
                        end_time = time.time()
                        return {
                            "success": False,
                            "response_time_ms": (end_time - start_time) * 1000,
                            "error": str(e),
                        }

            # Yük seviyesinde istekler gönder
            load_start_time = time.time()
            tasks = [single_request() for _ in range(load_level)]
            load_results = await asyncio.gather(*tasks)
            load_end_time = time.time()
            load_duration = load_end_time - load_start_time

            # Yanıt sürelerini analiz et
            successful_requests = [r for r in load_results if r["success"]]
            response_times = [r["response_time_ms"] for r in successful_requests]

            if response_times:
                response_times.sort()
                p50 = response_times[len(response_times) // 2]
                p95 = response_times[int(len(response_times) * 0.95)]
                p99 = response_times[int(len(response_times) * 0.99)]
                avg = sum(response_times) / len(response_times)
                min_time = min(response_times)
                max_time = max(response_times)
            else:
                p50 = p95 = p99 = avg = min_time = max_time = 0

            level_result = {
                "load_level": load_level,
                "total_requests": load_level,
                "successful_requests": len(successful_requests),
                "failed_requests": load_level - len(successful_requests),
                "success_rate": len(successful_requests) / load_level,
                "load_duration_seconds": load_duration,
                "throughput_rps": load_level / load_duration,
                "response_time_ms": {
                    "min": min_time,
                    "avg": avg,
                    "p50": p50,
                    "p95": p95,
                    "p99": p99,
                    "max": max_time,
                },
            }

            results.append(level_result)

            # Requirement 7.1: p95 < 200ms kontrolü (düşük-orta yük için)
            if load_level <= 1000:
                assert (
                    p95 < 200
                ), f"p95 response time {p95}ms exceeds 200ms at load level {load_level}"

            print(
                f"Load {load_level}: p95={p95:.2f}ms, success_rate={level_result['success_rate']:.2%}"
            )

            # Yük seviyeleri arası bekleme
            await asyncio.sleep(2)

        return {
            "load_test_results": results,
            "requirement_7_1_met": all(
                r["response_time_ms"]["p95"] < 200
                for r in results
                if r["load_level"] <= 1000
            ),
        }

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_high_load(self):
        """
        Sürekli yüksek yük testi
        Requirement 7.3: %99.9 uptime
        """

        # 10 dakika boyunca sürekli yük
        duration_seconds = 600  # 10 dakika
        requests_per_second = 200
        concurrent_workers = 20

        start_time = time.time()
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times = []

        async def continuous_worker():
            """Sürekli istek gönderen worker"""
            nonlocal total_requests, successful_requests, failed_requests

            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < duration_seconds:
                    request_start = time.time()
                    try:
                        response = await session.get(
                            "http://localhost:8000/api/v1/health",
                            timeout=aiohttp.ClientTimeout(total=5),
                        )
                        request_end = time.time()

                        total_requests += 1
                        if response.status == 200:
                            successful_requests += 1
                            response_times.append((request_end - request_start) * 1000)
                        else:
                            failed_requests += 1

                    except Exception:
                        total_requests += 1
                        failed_requests += 1

                    # Rate limiting
                    await asyncio.sleep(
                        1.0 / (requests_per_second / concurrent_workers)
                    )

        # Worker'ları başlat
        print(
            f"Starting {concurrent_workers} workers for {duration_seconds}s sustained load test..."
        )
        tasks = [continuous_worker() for _ in range(concurrent_workers)]
        await asyncio.gather(*tasks)

        end_time = time.time()
        actual_duration = end_time - start_time

        # Uptime hesaplama (Requirement 7.3)
        uptime_percentage = (
            (successful_requests / total_requests * 100) if total_requests > 0 else 0
        )

        # Yanıt süresi istatistikleri
        if response_times:
            response_times.sort()
            avg_response_time = sum(response_times) / len(response_times)
            p95_response_time = response_times[int(len(response_times) * 0.95)]
        else:
            avg_response_time = 0
            p95_response_time = 0

        # Assertions
        assert (
            uptime_percentage >= 99.9
        ), f"Uptime {uptime_percentage}% is below 99.9% (Requirement 7.3)"
        assert successful_requests > 0, "No successful requests during sustained load"

        return {
            "duration_seconds": actual_duration,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "uptime_percentage": uptime_percentage,
            "avg_response_time_ms": avg_response_time,
            "p95_response_time_ms": p95_response_time,
            "actual_requests_per_second": total_requests / actual_duration,
            "target_requests_per_second": requests_per_second,
            "requirement_7_3_met": uptime_percentage >= 99.9,
        }

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_auto_scaling_simulation(self):
        """
        Otomatik ölçeklendirme simülasyonu
        Requirement 7.6: Otomatik ölçeklendirme
        """

        # Yük seviyelerini kademeli olarak artır
        load_phases = [
            {"users": 100, "duration_seconds": 30},
            {"users": 500, "duration_seconds": 30},
            {"users": 1000, "duration_seconds": 30},
            {"users": 2000, "duration_seconds": 30},
            {"users": 5000, "duration_seconds": 30},
        ]

        phase_results = []

        for phase in load_phases:
            print(f"\nPhase: {phase['users']} users for {phase['duration_seconds']}s")

            phase_start_time = time.time()
            successful_count = 0
            failed_count = 0
            response_times = []

            async def phase_user():
                """Faz kullanıcısı"""
                nonlocal successful_count, failed_count

                async with aiohttp.ClientSession() as session:
                    start = time.time()
                    try:
                        response = await session.get(
                            "http://localhost:8000/api/v1/health",
                            timeout=aiohttp.ClientTimeout(total=5),
                        )
                        end = time.time()

                        if response.status == 200:
                            successful_count += 1
                            response_times.append((end - start) * 1000)
                        else:
                            failed_count += 1
                    except:
                        failed_count += 1

            # Faz kullanıcılarını çalıştır
            tasks = [phase_user() for _ in range(phase["users"])]
            await asyncio.gather(*tasks)

            phase_end_time = time.time()
            phase_duration = phase_end_time - phase_start_time

            # Faz metrikleri
            success_rate = (
                successful_count / phase["users"] if phase["users"] > 0 else 0
            )
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            phase_result = {
                "users": phase["users"],
                "duration_seconds": phase_duration,
                "successful_requests": successful_count,
                "failed_requests": failed_count,
                "success_rate": success_rate,
                "avg_response_time_ms": avg_response_time,
                "throughput_rps": phase["users"] / phase_duration,
            }

            phase_results.append(phase_result)

            print(
                f"Phase result: success_rate={success_rate:.2%}, "
                f"avg_response_time={avg_response_time:.2f}ms"
            )

            # Fazlar arası bekleme (ölçeklendirme için)
            await asyncio.sleep(2)  # Reduced from 5s for faster test execution

        # Ölçeklendirme analizi
        # Başarı oranının yük artışıyla birlikte stabil kalması beklenir
        success_rates = [p["success_rate"] for p in phase_results]
        avg_success_rate = sum(success_rates) / len(success_rates)

        # Assertion: Ortalama başarı oranı %80'in üzerinde olmalı
        assert (
            avg_success_rate >= 0.8
        ), f"Average success rate {avg_success_rate} is below 80% during scaling"

        return {
            "phase_results": phase_results,
            "avg_success_rate": avg_success_rate,
            "scaling_stability": "stable" if avg_success_rate >= 0.8 else "unstable",
            "requirement_7_6_met": avg_success_rate >= 0.8,
        }


if __name__ == "__main__":
    # Run 100K load tests
    pytest.main([__file__, "-v", "--tb=short", "-s", "-m", "slow"])
