"""
Phase 2: Fast Learning API Comprehensive Tests
Target: 0% → 40%+ coverage for api/fast_learning_api.py (93 lines)
Focus: API endpoints, error handling, response formatting, service integration
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFastLearningAPICore:
    """Test Fast Learning API core functionality"""

    def test_router_creation(self):
        """Test FastAPI router creation and configuration"""
        try:
            from api.fast_learning_api import router

            assert router is not None
            assert router.prefix == "/api/v1/fast-learning"
            assert "Hızlı Öğrenme Stili" in router.tags

            # Test routes are registered
            route_paths = [route.path for route in router.routes]
            expected_paths = [
                "/detect/{student_id}",
                "/recommendations/{student_id}",
                "/explanation/{student_id}",
                "/health",
            ]

            for expected_path in expected_paths:
                assert expected_path in route_paths

        except ImportError:
            pytest.skip("Fast Learning API not available")

    def test_service_instance_creation(self):
        """Test service instance is properly created"""
        try:
            with patch(
                "api.fast_learning_api.FastLearningStyleService"
            ) as mock_service_class:
                mock_service_instance = Mock()
                mock_service_class.return_value = mock_service_instance

                # Re-import to trigger service creation
                import importlib

                import api.fast_learning_api

                importlib.reload(api.fast_learning_api)

                # Verify service was instantiated
                mock_service_class.assert_called_once()

        except ImportError:
            pytest.skip("Fast Learning API not available")


class TestHealthEndpoint:
    """Test health check endpoint"""

    @pytest.mark.asyncio
    async def test_fast_health_check_success(self):
        """Test successful health check"""
        try:
            from api.fast_learning_api import fast_health_check

            result = await fast_health_check()

            assert result["success"] is True
            assert result["status"] == "healthy"
            assert result["mode"] == "fast"
            assert "Hızlı öğrenme stili sistemi çalışıyor" in result["message"]
            assert "features" in result

            # Test expected features
            expected_features = [
                "fast_detection",
                "simple_recommendations",
                "minimal_processing",
            ]
            for feature in expected_features:
                assert feature in result["features"]

        except ImportError:
            pytest.skip("Fast Learning API not available")

    def test_health_endpoint_structure(self):
        """Test health endpoint response structure"""
        try:
            from api.fast_learning_api import fast_health_check

            # Test that function is async
            assert asyncio.iscoroutinefunction(fast_health_check)

        except ImportError:
            pytest.skip("Fast Learning API not available")


class TestDetectLearningStyleEndpoint:
    """Test learning style detection endpoint"""

    @pytest.mark.asyncio
    async def test_fast_detect_learning_style_success(self):
        """Test successful learning style detection"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                # Mock profile object
                mock_profile = Mock()
                mock_profile.student_id = "student123"
                mock_profile.hybrid_code = "VK-A"
                mock_profile.confidence_score = 0.85

                # Mock VARK profile
                mock_vark_profile = Mock()
                mock_vark_dominant = Mock()
                mock_vark_dominant.value = "Visual"
                mock_vark_profile.dominant_vark = mock_vark_dominant
                mock_profile.vark_profile = mock_vark_profile

                mock_service.detect_learning_style = AsyncMock(
                    return_value=mock_profile
                )

                from api.fast_learning_api import fast_detect_learning_style

                result = await fast_detect_learning_style("student123")

                assert result["success"] is True
                assert result["data"]["student_id"] == "student123"
                assert result["data"]["hybrid_code"] == "VK-A"
                assert result["data"]["confidence_score"] == 0.85
                assert result["data"]["vark_dominant"] == "Visual"
                assert result["mode"] == "fast"
                assert "VK-A" in result["message"]

                mock_service.detect_learning_style.assert_called_once_with("student123")

        except ImportError:
            pytest.skip("Fast Learning API not available")

    @pytest.mark.asyncio
    async def test_fast_detect_learning_style_service_error(self):
        """Test learning style detection with service error"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                mock_service.detect_learning_style = AsyncMock(
                    side_effect=Exception("Service error")
                )

                from api.fast_learning_api import fast_detect_learning_style

                with pytest.raises(HTTPException) as exc_info:
                    await fast_detect_learning_style("student123")

                assert exc_info.value.status_code == 500
                assert "Hızlı tespit başarısız" in str(exc_info.value.detail)
                assert "Service error" in str(exc_info.value.detail)

        except ImportError:
            pytest.skip("Fast Learning API not available")

    @pytest.mark.asyncio
    async def test_fast_detect_learning_style_different_students(self):
        """Test learning style detection with different student IDs"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                # Mock different profiles for different students
                def mock_detect_style(student_id):
                    mock_profile = Mock()
                    mock_profile.student_id = student_id
                    mock_profile.hybrid_code = f"CODE-{student_id[-1]}"
                    mock_profile.confidence_score = 0.75

                    mock_vark_profile = Mock()
                    mock_vark_dominant = Mock()
                    mock_vark_dominant.value = "Kinesthetic"
                    mock_vark_profile.dominant_vark = mock_vark_dominant
                    mock_profile.vark_profile = mock_vark_profile

                    return mock_profile

                mock_service.detect_learning_style = AsyncMock(
                    side_effect=mock_detect_style
                )

                from api.fast_learning_api import fast_detect_learning_style

                # Test with different student IDs
                student_ids = ["student001", "student002", "student003"]

                for student_id in student_ids:
                    result = await fast_detect_learning_style(student_id)

                    assert result["success"] is True
                    assert result["data"]["student_id"] == student_id
                    assert result["data"]["hybrid_code"] == f"CODE-{student_id[-1]}"
                    assert result["data"]["vark_dominant"] == "Kinesthetic"

        except ImportError:
            pytest.skip("Fast Learning API not available")


class TestRecommendationsEndpoint:
    """Test content recommendations endpoint"""

    @pytest.mark.asyncio
    async def test_fast_get_recommendations_success(self):
        """Test successful content recommendations"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                # Mock recommendation object
                mock_recommendation = Mock()
                mock_recommendation.student_id = "student123"
                mock_recommendation.hybrid_code = "VA-M"
                mock_recommendation.recommended_content_types = [
                    "video",
                    "diagram",
                    "interactive",
                ]
                mock_recommendation.learning_strategies = [
                    "visual_notes",
                    "concept_maps",
                ]

                mock_service.generate_content_recommendations = AsyncMock(
                    return_value=mock_recommendation
                )

                from api.fast_learning_api import fast_get_recommendations

                result = await fast_get_recommendations("student123")

                assert result["success"] is True
                assert result["data"]["student_id"] == "student123"
                assert result["data"]["hybrid_code"] == "VA-M"
                assert result["data"]["recommended_content_types"] == [
                    "video",
                    "diagram",
                    "interactive",
                ]
                assert result["data"]["learning_strategies"] == [
                    "visual_notes",
                    "concept_maps",
                ]
                assert result["mode"] == "fast"
                assert "Hızlı öneriler hazırlandı" in result["message"]

                mock_service.generate_content_recommendations.assert_called_once_with(
                    "student123"
                )

        except ImportError:
            pytest.skip("Fast Learning API not available")

    @pytest.mark.asyncio
    async def test_fast_get_recommendations_service_error(self):
        """Test content recommendations with service error"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                mock_service.generate_content_recommendations = AsyncMock(
                    side_effect=Exception("Recommendation service error")
                )

                from api.fast_learning_api import fast_get_recommendations

                with pytest.raises(HTTPException) as exc_info:
                    await fast_get_recommendations("student123")

                assert exc_info.value.status_code == 500
                assert "Hızlı öneriler başarısız" in str(exc_info.value.detail)
                assert "Recommendation service error" in str(exc_info.value.detail)

        except ImportError:
            pytest.skip("Fast Learning API not available")

    @pytest.mark.asyncio
    async def test_fast_get_recommendations_empty_content(self):
        """Test content recommendations with empty content"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                # Mock recommendation with empty lists
                mock_recommendation = Mock()
                mock_recommendation.student_id = "student123"
                mock_recommendation.hybrid_code = "UNKNOWN"
                mock_recommendation.recommended_content_types = []
                mock_recommendation.learning_strategies = []

                mock_service.generate_content_recommendations = AsyncMock(
                    return_value=mock_recommendation
                )

                from api.fast_learning_api import fast_get_recommendations

                result = await fast_get_recommendations("student123")

                assert result["success"] is True
                assert result["data"]["recommended_content_types"] == []
                assert result["data"]["learning_strategies"] == []

        except ImportError:
            pytest.skip("Fast Learning API not available")


class TestExplanationEndpoint:
    """Test learning style explanation endpoint"""

    @pytest.mark.asyncio
    async def test_fast_get_explanation_success(self):
        """Test successful learning style explanation"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                mock_explanation = {
                    "student_id": "student123",
                    "learning_style": "Visual-Kinesthetic",
                    "description": "Görsel ve hareket odaklı öğrenme tarzı",
                    "strengths": ["Görsel algı", "Pratik uygulama"],
                    "recommendations": [
                        "Diyagramlar kullanın",
                        "Hands-on aktiviteler yapın",
                    ],
                }

                mock_service.get_learning_style_explanation = AsyncMock(
                    return_value=mock_explanation
                )

                from api.fast_learning_api import fast_get_explanation

                result = await fast_get_explanation("student123")

                assert result["success"] is True
                assert result["data"] == mock_explanation
                assert result["mode"] == "fast"
                assert "Hızlı açıklama hazırlandı" in result["message"]

                mock_service.get_learning_style_explanation.assert_called_once_with(
                    "student123"
                )

        except ImportError:
            pytest.skip("Fast Learning API not available")

    @pytest.mark.asyncio
    async def test_fast_get_explanation_service_error(self):
        """Test learning style explanation with service error"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                mock_service.get_learning_style_explanation = AsyncMock(
                    side_effect=Exception("Explanation service error")
                )

                from api.fast_learning_api import fast_get_explanation

                with pytest.raises(HTTPException) as exc_info:
                    await fast_get_explanation("student123")

                assert exc_info.value.status_code == 500
                assert "Hızlı açıklama başarısız" in str(exc_info.value.detail)
                assert "Explanation service error" in str(exc_info.value.detail)

        except ImportError:
            pytest.skip("Fast Learning API not available")

    @pytest.mark.asyncio
    async def test_fast_get_explanation_complex_data(self):
        """Test learning style explanation with complex data"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                complex_explanation = {
                    "student_id": "student456",
                    "learning_style": "Multimodal",
                    "description": "Çoklu öğrenme tarzı kombinasyonu",
                    "vark_breakdown": {
                        "Visual": 0.35,
                        "Auditory": 0.25,
                        "Reading": 0.20,
                        "Kinesthetic": 0.20,
                    },
                    "detailed_recommendations": {
                        "content_types": ["mixed_media", "interactive_lessons"],
                        "study_methods": ["varied_approaches", "multi_sensory"],
                        "assessment_types": ["portfolio", "project_based"],
                    },
                    "confidence_metrics": {
                        "overall_confidence": 0.88,
                        "detection_accuracy": 0.92,
                        "recommendation_relevance": 0.85,
                    },
                }

                mock_service.get_learning_style_explanation = AsyncMock(
                    return_value=complex_explanation
                )

                from api.fast_learning_api import fast_get_explanation

                result = await fast_get_explanation("student456")

                assert result["success"] is True
                assert result["data"]["student_id"] == "student456"
                assert result["data"]["learning_style"] == "Multimodal"
                assert "vark_breakdown" in result["data"]
                assert "detailed_recommendations" in result["data"]
                assert "confidence_metrics" in result["data"]

        except ImportError:
            pytest.skip("Fast Learning API not available")


class TestAPIResponseFormat:
    """Test API response format consistency"""

    @pytest.mark.asyncio
    async def test_response_format_consistency(self):
        """Test all endpoints return consistent response format"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                # Setup mocks
                mock_profile = Mock()
                mock_profile.student_id = "test_student"
                mock_profile.hybrid_code = "TEST"
                mock_profile.confidence_score = 0.8
                mock_vark = Mock()
                mock_vark.dominant_vark.value = "Visual"
                mock_profile.vark_profile = mock_vark

                mock_recommendation = Mock()
                mock_recommendation.student_id = "test_student"
                mock_recommendation.hybrid_code = "TEST"
                mock_recommendation.recommended_content_types = ["test"]
                mock_recommendation.learning_strategies = ["test"]

                mock_explanation = {"test": "explanation"}

                mock_service.detect_learning_style = AsyncMock(
                    return_value=mock_profile
                )
                mock_service.generate_content_recommendations = AsyncMock(
                    return_value=mock_recommendation
                )
                mock_service.get_learning_style_explanation = AsyncMock(
                    return_value=mock_explanation
                )

                from api.fast_learning_api import (
                    fast_detect_learning_style,
                    fast_get_explanation,
                    fast_get_recommendations,
                    fast_health_check,
                )

                # Test all endpoints
                endpoints = [
                    (fast_detect_learning_style, "test_student"),
                    (fast_get_recommendations, "test_student"),
                    (fast_get_explanation, "test_student"),
                    (fast_health_check, None),
                ]

                for endpoint_func, student_id in endpoints:
                    if student_id:
                        result = await endpoint_func(student_id)
                    else:
                        result = await endpoint_func()

                    # Test common response structure
                    assert "success" in result
                    assert "mode" in result
                    assert "message" in result
                    assert result["success"] is True
                    assert result["mode"] == "fast"

                    # Test that data or status is present
                    assert "data" in result or "status" in result

        except ImportError:
            pytest.skip("Fast Learning API not available")


class TestLoggingIntegration:
    """Test logging integration"""

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test that errors are properly logged"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                with patch("api.fast_learning_api.logger") as mock_logger:
                    error_message = "Test service error"
                    mock_service.detect_learning_style = AsyncMock(
                        side_effect=Exception(error_message)
                    )

                    from api.fast_learning_api import fast_detect_learning_style

                    with pytest.raises(HTTPException):
                        await fast_detect_learning_style("test_student")

                    # Verify error was logged
                    mock_logger.error.assert_called_once()
                    log_call_args = mock_logger.error.call_args[0][0]
                    assert "Hızlı tespit hatası" in log_call_args
                    assert error_message in log_call_args

        except ImportError:
            pytest.skip("Fast Learning API not available")


class TestAPIErrorHandling:
    """Test API error handling patterns"""

    @pytest.mark.asyncio
    async def test_http_exception_details(self):
        """Test HTTPException details for different endpoints"""
        try:
            with patch("api.fast_learning_api.fast_service") as mock_service:
                error_scenarios = [
                    (
                        "detect_learning_style",
                        "Detection error",
                        "Hızlı tespit başarısız",
                    ),
                    (
                        "generate_content_recommendations",
                        "Recommendation error",
                        "Hızlı öneriler başarısız",
                    ),
                    (
                        "get_learning_style_explanation",
                        "Explanation error",
                        "Hızlı açıklama başarısız",
                    ),
                ]

                from api.fast_learning_api import (
                    fast_detect_learning_style,
                    fast_get_explanation,
                    fast_get_recommendations,
                )

                endpoint_map = {
                    "detect_learning_style": fast_detect_learning_style,
                    "generate_content_recommendations": fast_get_recommendations,
                    "get_learning_style_explanation": fast_get_explanation,
                }

                for service_method, error_msg, expected_prefix in error_scenarios:
                    # Setup mock to raise exception
                    setattr(
                        mock_service,
                        service_method,
                        AsyncMock(side_effect=Exception(error_msg)),
                    )

                    endpoint_func = endpoint_map[service_method]

                    with pytest.raises(HTTPException) as exc_info:
                        await endpoint_func("test_student")

                    assert exc_info.value.status_code == 500
                    assert expected_prefix in str(exc_info.value.detail)
                    assert error_msg in str(exc_info.value.detail)

        except ImportError:
            pytest.skip("Fast Learning API not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
