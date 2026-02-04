import pytest

# -*- coding: utf-8 -*-
"""
Devrimsel AI Özellikler API Integration Test Suite
API endpoint'lerin devrimsel özelliklerle entegrasyonu testleri

Bu test suite, REST API'lerin devrimsel özelliklerle
doğru şekilde entegre olduğunu ve production-ready olduğunu test eder.

Requirements: 10.1-10.7, 11.1-11.6, 12.1-12.6
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# FastAPI app
from main import app

# Test client
client = TestClient(app)


class TestRevolutionaryAPIEndpoints:
    """Devrimsel özellik API endpoint testleri"""

    def setup_method(self):
        """Her test öncesi setup"""
        self.test_student_id = "api_test_student_001"
        self.auth_headers = {"Authorization": "Bearer test_token"}

    def test_learning_style_detection_api(self):
        """Öğrenme stili tespit API testi"""

        # Test data
        request_data = {
            "student_id": self.test_student_id,
            "behavioral_data": [
                {
                    "video_watch_time": 120,
                    "visual_content_performance": 0.85,
                    "interactive_engagement": 45,
                    "text_reading_time": 30,
                    "timestamp": datetime.now().isoformat(),
                }
            ],
            "questionnaire_responses": [
                {
                    "question": "Öğrenme tercihiniz nedir?",
                    "response": "Görsel materyallerle daha iyi öğrenirim",
                    "vark_dimension": "visual",
                    "confidence": 0.9,
                }
            ],
        }

        # API call
        response = client.post(
            "/api/v1/revolutionary/learning-style/detect",
            json=request_data,
            headers=self.auth_headers,
        )

        # Assertions
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] == True

        # Response structure
        result = data["data"]
        assert "student_id" in result
        assert "hybrid_code" in result
        assert "confidence_level" in result
        assert "vark_profile" in result
        assert "felder_profile" in result

        # Data validation
        assert result["student_id"] == self.test_student_id
        assert 0.0 <= result["confidence_level"] <= 1.0
        assert len(result["hybrid_code"]) > 0

        # VARK profile validation
        vark = result["vark_profile"]
        assert all(
            0.0 <= vark[dim] <= 1.0
            for dim in ["visual", "auditory", "reading", "kinesthetic"]
        )

        # Felder profile validation
        felder = result["felder_profile"]
        expected_dimensions = [
            "active_reflective",
            "sensing_intuitive",
            "visual_verbal",
            "sequential_global",
        ]
        assert all(0.0 <= felder[dim] <= 1.0 for dim in expected_dimensions)

    def test_zpd_maarif_calculation_api(self):
        """ZPD Maarif hesaplama API testi"""

        request_data = {
            "student_current_level": 5.0,
            "subject": "Matematik",
            "cultural_context": {
                "group_learning_preference": 0.8,
                "teacher_respect_level": 0.9,
                "family_involvement": 0.7,
                "exam_season": True,
                "ramadan_period": False,
            },
        }

        response = client.post(
            "/api/v1/revolutionary/zpd/calculate",
            json=request_data,
            headers=self.auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] == True

        result = data["data"]
        assert "lower_bound" in result
        assert "upper_bound" in result
        assert "optimal_challenge" in result
        assert "maarif_alignment" in result
        assert "cultural_factors" in result

        # ZPD validation
        assert result["lower_bound"] == 5.0
        assert result["upper_bound"] > result["lower_bound"]
        assert (
            result["lower_bound"]
            <= result["optimal_challenge"]
            <= result["upper_bound"]
        )
        assert 0.0 <= result["maarif_alignment"] <= 1.0

    def test_morphology_irt_analysis_api(self):
        """Morfoloji IRT analiz API testi"""

        request_data = {
            "question": {
                "text": "Çekoslovakyalılaştıramadıklarımızdanmısınız kelimesinin morfolojik yapısını analiz ediniz.",
                "difficulty": 3.5,
                "discrimination": 2.0,
                "subject": "Türkçe",
                "topic": "Morfoloji",
            },
            "student": {
                "id": self.test_student_id,
                "ability": 1.8,
                "morphology_awareness": 0.7,
            },
        }

        response = client.post(
            "/api/v1/revolutionary/morphology-irt/analyze",
            json=request_data,
            headers=self.auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] == True

        result = data["data"]
        assert "probability" in result
        assert "morphological_complexity" in result
        assert "adjusted_difficulty" in result
        assert "processing_time_ms" in result

        # Validation
        assert 0.0 <= result["probability"] <= 1.0
        assert 0.0 <= result["morphological_complexity"] <= 1.0
        assert result["adjusted_difficulty"] > 0
        assert result["processing_time_ms"] > 0

    def test_fsrs_scheduling_api(self):
        """FSRS zamanlama API testi"""

        request_data = {
            "flashcard": {
                "id": "test_card_001",
                "content": "mütalaa",
                "answer": "okuma, inceleme",
                "difficulty": 2.5,
                "last_review": (datetime.now() - timedelta(days=3)).isoformat(),
                "review_count": 5,
                "success_rate": 0.6,
            },
            "grade": 3,  # Good
            "cultural_context": {
                "exam_season": True,
                "ramadan_period": False,
                "group_study": False,
            },
        }

        response = client.post(
            "/api/v1/revolutionary/fsrs/schedule",
            json=request_data,
            headers=self.auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] == True

        result = data["data"]
        assert "scheduled_date" in result
        assert "interval_days" in result
        assert "cultural_factors" in result
        assert "fsrs_parameters" in result

        # Validation
        scheduled_date = datetime.fromisoformat(result["scheduled_date"])
        assert scheduled_date > datetime.now()
        assert result["interval_days"] > 0
        assert len(result["fsrs_parameters"]) == 17  # 17 Turkish-optimized parameters

    def test_text_simplification_api(self):
        """Metin basitleştirme API testi"""

        request_data = {
            "text": "Bu mütalaa çok önemli bir tetkik gerektiriyor ve mütehassıslar tarafından detaylı bir müzakere yapılmalıdır.",
            "target_level": "intermediate",
        }

        response = client.post(
            "/api/v1/revolutionary/simplification/simplify",
            json=request_data,
            headers=self.auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] == True

        result = data["data"]
        assert "original_text" in result
        assert "level1_lexical" in result
        assert "level2_syntactic" in result
        assert "level3_semantic" in result
        assert "complexity_reduction" in result
        assert "readability_score" in result
        assert "processing_time_ms" in result
        assert "applied_rules" in result

        # Validation
        assert result["original_text"] == request_data["text"]
        assert 0.0 <= result["complexity_reduction"] <= 1.0
        assert result["readability_score"] >= 0.0
        assert result["processing_time_ms"] > 0
        assert len(result["applied_rules"]) > 0

        # Simplification should have occurred
        assert "mütalaa" not in result["level1_lexical"]  # Ottoman word replaced
        assert "tetkik" not in result["level1_lexical"]  # Ottoman word replaced

    def test_bionic_reading_api(self):
        """Bionic Reading API testi"""

        request_data = {"text": "Çocuklar bahçede oynuyorlar ve çok eğleniyorlar."}

        response = client.post(
            "/api/v1/revolutionary/bionic-reading/apply",
            json=request_data,
            headers=self.auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] == True

        result = data["data"]
        assert "original_text" in result
        assert "bionic_text" in result
        assert "root_suffix_analysis" in result
        assert "processing_time_ms" in result

        # Validation
        assert result["original_text"] == request_data["text"]
        assert "**" in result["bionic_text"]  # Bold formatting applied
        assert result["processing_time_ms"] > 0
        assert len(result["root_suffix_analysis"]) > 0

    def test_multi_agent_coordination_api(self):
        """Multi-Agent koordinasyon API testi"""

        request_data = {
            "student_id": self.test_student_id,
            "coordination_request": {
                "type": "personalized_content_generation",
                "learning_style": "visual",
                "subject": "Matematik",
                "difficulty_level": "intermediate",
            },
            "target_agents": ["learning_path", "study_buddy", "accessibility"],
        }

        response = client.post(
            "/api/v1/revolutionary/multi-agent/coordinate",
            json=request_data,
            headers=self.auth_headers,
        )

        assert response.status_code == 200

        data = response.json()
        assert data["success"] == True

        result = data["data"]
        assert "coordination_id" in result
        assert "agent_responses" in result
        assert "coordination_time_ms" in result
        assert "synergy_score" in result

        # Validation
        assert len(result["agent_responses"]) == 3  # 3 target agents
        assert result["coordination_time_ms"] > 0
        assert 0.0 <= result["synergy_score"] <= 1.0

        # Each agent should have responded
        agent_ids = [resp["agent_id"] for resp in result["agent_responses"]]
        assert "learning_path" in agent_ids
        assert "study_buddy" in agent_ids
        assert "accessibility" in agent_ids


class TestRevolutionaryAPIPerformance:
    """Devrimsel özellik API performans testleri"""

    def setup_method(self):
        """Setup"""
        self.auth_headers = {"Authorization": "Bearer test_token"}

    def test_concurrent_api_requests(self):
        """Eşzamanlı API istekleri performans testi"""

        import concurrent.futures
        import time

        def make_request(endpoint, data):
            """Tek API isteği"""
            start_time = time.time()
            response = client.post(endpoint, json=data, headers=self.auth_headers)
            end_time = time.time()

            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "endpoint": endpoint,
            }

        # Test data for different endpoints
        test_requests = (
            [
                (
                    "/api/v1/revolutionary/learning-style/detect",
                    {
                        "student_id": f"perf_test_{i}",
                        "behavioral_data": [],
                        "questionnaire_responses": [],
                    },
                )
                for i in range(10)
            ]
            + [
                (
                    "/api/v1/revolutionary/morphology-irt/analyze",
                    {
                        "question": {"text": "Test sorusu", "difficulty": 2.0},
                        "student": {"id": f"perf_test_{i}", "ability": 1.5},
                    },
                )
                for i in range(10)
            ]
            + [
                (
                    "/api/v1/revolutionary/bionic-reading/apply",
                    {"text": f"Test metni {i} için Bionic Reading uygulaması."},
                )
                for i in range(10)
            ]
        )

        # Execute concurrent requests
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(make_request, endpoint, data)
                for endpoint, data in test_requests
            ]

            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        end_time = time.time()
        total_time = end_time - start_time

        # Performance assertions
        successful_requests = [r for r in results if r["status_code"] == 200]
        failed_requests = [r for r in results if r["status_code"] != 200]

        assert len(successful_requests) >= len(test_requests) * 0.9  # 90% success rate
        assert total_time < 10.0  # Total time under 10 seconds

        # Average response time
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(
            successful_requests
        )
        assert avg_response_time < 2.0  # Average under 2 seconds

        return {
            "total_requests": len(test_requests),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "requests_per_second": len(successful_requests) / total_time,
        }

    def test_api_response_time_benchmarks(self):
        """API yanıt süresi benchmark testleri"""

        benchmarks = {
            "/api/v1/revolutionary/learning-style/detect": {
                "data": {
                    "student_id": "benchmark_test",
                    "behavioral_data": [{"video_watch_time": 120}],
                    "questionnaire_responses": [],
                },
                "max_time": 3.0,  # 3 seconds max
            },
            "/api/v1/revolutionary/zpd/calculate": {
                "data": {
                    "student_current_level": 5.0,
                    "subject": "Matematik",
                    "cultural_context": {"group_learning_preference": 0.8},
                },
                "max_time": 1.0,  # 1 second max
            },
            "/api/v1/revolutionary/morphology-irt/analyze": {
                "data": {
                    "question": {
                        "text": "Karmaşık morfolojik yapı analizi",
                        "difficulty": 2.5,
                    },
                    "student": {
                        "id": "benchmark",
                        "ability": 1.5,
                        "morphology_awareness": 0.7,
                    },
                },
                "max_time": 2.0,  # 2 seconds max
            },
            "/api/v1/revolutionary/simplification/simplify": {
                "data": {
                    "text": "Bu mütalaa çok önemli bir tetkik gerektiriyor ve mütehassıslar tarafından detaylı bir müzakere yapılmalıdır.",
                    "target_level": "intermediate",
                },
                "max_time": 5.0,  # 5 seconds max (complex processing)
            },
            "/api/v1/revolutionary/bionic-reading/apply": {
                "data": {"text": "Çocuklar bahçede oynuyorlar ve çok eğleniyorlar."},
                "max_time": 1.0,  # 1 second max
            },
        }

        results = {}

        for endpoint, config in benchmarks.items():
            # Measure response time
            start_time = time.time()
            response = client.post(
                endpoint, json=config["data"], headers=self.auth_headers
            )
            end_time = time.time()

            response_time = end_time - start_time

            # Assertions
            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            assert (
                response_time < config["max_time"]
            ), f"Endpoint {endpoint} too slow: {response_time}s > {config['max_time']}s"

            results[endpoint] = {
                "response_time": response_time,
                "max_allowed": config["max_time"],
                "performance_ratio": response_time / config["max_time"],
            }

        return results


class TestRevolutionaryAPIErrorHandling:
    """Devrimsel özellik API hata yönetimi testleri"""

    def setup_method(self):
        """Setup"""
        self.auth_headers = {"Authorization": "Bearer test_token"}

    def test_invalid_input_handling(self):
        """Geçersiz girdi yönetimi testi"""

        # Test cases with invalid inputs
        invalid_cases = [
            {
                "endpoint": "/api/v1/revolutionary/learning-style/detect",
                "data": {"student_id": ""},  # Empty student ID
                "expected_error": "student_id gerekli",
            },
            {
                "endpoint": "/api/v1/revolutionary/zpd/calculate",
                "data": {"student_current_level": -1.0},  # Negative level
                "expected_error": "student_current_level pozitif olmalı",
            },
            {
                "endpoint": "/api/v1/revolutionary/morphology-irt/analyze",
                "data": {"question": {"text": ""}, "student": {}},  # Empty question
                "expected_error": "question.text gerekli",
            },
            {
                "endpoint": "/api/v1/revolutionary/simplification/simplify",
                "data": {
                    "text": "",
                    "target_level": "invalid",
                },  # Empty text, invalid level
                "expected_error": "text gerekli",
            },
        ]

        for case in invalid_cases:
            response = client.post(
                case["endpoint"], json=case["data"], headers=self.auth_headers
            )

            # Should return 400 Bad Request
            assert response.status_code == 400

            data = response.json()
            assert "success" in data
            assert data["success"] == False
            assert "error" in data
            assert case["expected_error"] in data["error"]["message"]

    def test_service_unavailable_handling(self):
        """Servis erişilemezlik durumu testi"""

        # Mock service failure
        with patch(
            "algorithms.hybrid_learning_style_detector.HybridLearningStyleDetector.detect_hybrid_profile"
        ) as mock_detect:
            mock_detect.side_effect = Exception("Service temporarily unavailable")

            response = client.post(
                "/api/v1/revolutionary/learning-style/detect",
                json={
                    "student_id": "service_test",
                    "behavioral_data": [],
                    "questionnaire_responses": [],
                },
                headers=self.auth_headers,
            )

            # Should return 500 Internal Server Error
            assert response.status_code == 500

            data = response.json()
            assert data["success"] == False
            assert "error" in data
            assert "Geçici bir hata oluştu" in data["error"]["message"]

    def test_timeout_handling(self):
        """Timeout durumu yönetimi testi"""

        # Mock slow service
        async def slow_service(*args, **kwargs):
            await asyncio.sleep(10)  # 10 second delay
            return Mock()

        with patch(
            "algorithms.three_level_turkish_simplification.ThreeLevelTurkishSimplification.revolutionary_simplification"
        ) as mock_simplify:
            mock_simplify.side_effect = slow_service

            response = client.post(
                "/api/v1/revolutionary/simplification/simplify",
                json={"text": "Test timeout handling", "target_level": "intermediate"},
                headers=self.auth_headers,
            )

            # Should handle timeout gracefully
            assert response.status_code in [408, 500]  # Timeout or Internal Error

            data = response.json()
            assert data["success"] == False
            assert "timeout" in data["error"]["message"].lower()


class TestRevolutionaryAPIAuthentication:
    """Devrimsel özellik API kimlik doğrulama testleri"""

    def test_unauthorized_access(self):
        """Yetkisiz erişim testi"""

        endpoints = [
            "/api/v1/revolutionary/learning-style/detect",
            "/api/v1/revolutionary/zpd/calculate",
            "/api/v1/revolutionary/morphology-irt/analyze",
            "/api/v1/revolutionary/fsrs/schedule",
            "/api/v1/revolutionary/simplification/simplify",
            "/api/v1/revolutionary/bionic-reading/apply",
            "/api/v1/revolutionary/multi-agent/coordinate",
        ]

        for endpoint in endpoints:
            # Request without authorization header
            response = client.post(endpoint, json={})

            assert response.status_code == 401  # Unauthorized

            data = response.json()
            assert "error" in data
            assert "authentication" in data["error"]["message"].lower()

    def test_invalid_token(self):
        """Geçersiz token testi"""

        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}

        response = client.post(
            "/api/v1/revolutionary/learning-style/detect",
            json={
                "student_id": "test",
                "behavioral_data": [],
                "questionnaire_responses": [],
            },
            headers=invalid_headers,
        )

        assert response.status_code == 401  # Unauthorized

        data = response.json()
        assert data["success"] == False
        assert "token" in data["error"]["message"].lower()


if __name__ == "__main__":
    # Run revolutionary API integration tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])
