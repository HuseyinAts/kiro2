"""
Comprehensive tests for Learning Style API Endpoints
Target: 80%+ test coverage
VARK + Felder-Silverman Hibrit Öğrenme Stili API testi
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List

from fastapi import HTTPException
from fastapi.testclient import TestClient

# API endpoint import
from api.learning_style import (
    router,
    detect_learning_style,
    get_content_recommendations,
    update_behavioral_data,
    submit_questionnaire,
    get_learning_style_explanation,
    get_all_hybrid_codes,
    get_learning_style_statistics,
    export_learning_profile,
    get_content_explanation,
    update_recommendations_based_on_performance,
    health_check,
)

# Mock models and services
from models.learning_style import BehavioralData, QuestionnaireResponse


@pytest.fixture
def mock_learning_style_service():
    """Mock learning style service for testing"""
    with patch("api.learning_style.learning_style_service") as mock_service:
        # Set up basic mock attributes
        mock_service.profiles_cache = {}
        mock_service.behavioral_data_cache = {"student1": [{"interaction": "test"}]}
        mock_service.questionnaire_cache = {"student1": [{"response": "test"}]}
        mock_service.recommendations_cache = {}
        yield mock_service


class TestDetectLearningStyleEndpoint:
    """Test /detect/{student_id} endpoint"""

    @pytest.mark.asyncio
    async def test_detect_learning_style_success(self, mock_learning_style_service):
        """Test successful learning style detection"""
        # Mock profile response
        mock_profile = Mock()
        mock_profile.student_id = "student1"
        mock_profile.hybrid_code = "VARK_V_FELDER_AR"
        mock_profile.vark_profile = Mock()
        mock_profile.vark_profile.visual = 0.8
        mock_profile.vark_profile.auditory = 0.6
        mock_profile.vark_profile.reading = 0.4
        mock_profile.vark_profile.kinesthetic = 0.3
        mock_profile.vark_profile.dominant_vark = Mock()
        mock_profile.vark_profile.dominant_vark.value = "visual"
        mock_profile.felder_profile = Mock()
        mock_profile.felder_profile.active_reflective = 0.7
        mock_profile.felder_profile.sensing_intuitive = 0.5
        mock_profile.felder_profile.visual_verbal = 0.8
        mock_profile.felder_profile.sequential_global = 0.6
        mock_profile.felder_profile.learning_preferences = ["visual", "active"]
        mock_profile.confidence_score = 0.85
        mock_profile.confidence_level = Mock()
        mock_profile.confidence_level.value = "high"
        mock_profile.data_points_used = 15
        mock_profile.detection_date = datetime.now()
        mock_profile.last_updated = datetime.now()

        mock_learning_style_service.detect_learning_style.return_value = mock_profile

        result = await detect_learning_style("student1", False)

        assert result["success"] is True
        assert result["data"]["student_id"] == "student1"
        assert result["data"]["hybrid_code"] == "VARK_V_FELDER_AR"
        assert result["data"]["vark_profile"]["dominant"] == "visual"
        assert result["data"]["felder_profile"]["preferences"] == ["visual", "active"]
        assert result["data"]["confidence"]["score"] == 0.85
        assert result["data"]["confidence"]["level"] == "high"
        assert "hibrit öğrenme stili tespit edildi" in result["message"].lower()

        mock_learning_style_service.detect_learning_style.assert_called_once_with(
            student_id="student1", force_recalculation=False
        )

    @pytest.mark.asyncio
    async def test_detect_learning_style_force_recalculation(
        self, mock_learning_style_service
    ):
        """Test learning style detection with force recalculation"""
        mock_profile = Mock()
        mock_profile.student_id = "student1"
        mock_profile.hybrid_code = "NEW_CODE"
        mock_profile.vark_profile = Mock()
        mock_profile.vark_profile.visual = 0.7
        mock_profile.vark_profile.auditory = 0.5
        mock_profile.vark_profile.reading = 0.3
        mock_profile.vark_profile.kinesthetic = 0.4
        mock_profile.vark_profile.dominant_vark = Mock()
        mock_profile.vark_profile.dominant_vark.value = "visual"
        mock_profile.felder_profile = Mock()
        mock_profile.felder_profile.active_reflective = 0.6
        mock_profile.felder_profile.sensing_intuitive = 0.7
        mock_profile.felder_profile.visual_verbal = 0.8
        mock_profile.felder_profile.sequential_global = 0.5
        mock_profile.felder_profile.learning_preferences = ["visual"]
        mock_profile.confidence_score = 0.9
        mock_profile.confidence_level = Mock()
        mock_profile.confidence_level.value = "very_high"
        mock_profile.data_points_used = 25
        mock_profile.detection_date = datetime.now()
        mock_profile.last_updated = datetime.now()

        mock_learning_style_service.detect_learning_style.return_value = mock_profile

        result = await detect_learning_style("student1", True)

        assert result["success"] is True
        assert result["data"]["hybrid_code"] == "NEW_CODE"
        mock_learning_style_service.detect_learning_style.assert_called_once_with(
            student_id="student1", force_recalculation=True
        )

    @pytest.mark.asyncio
    async def test_detect_learning_style_error(self, mock_learning_style_service):
        """Test learning style detection with error"""
        mock_learning_style_service.detect_learning_style.side_effect = Exception(
            "Service error"
        )

        with pytest.raises(HTTPException) as exc_info:
            await detect_learning_style("student1", False)

        assert exc_info.value.status_code == 500
        assert "öğrenme stili tespit edilemedi" in exc_info.value.detail.lower()


class TestContentRecommendationsEndpoint:
    """Test /recommendations/{student_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_content_recommendations_success(
        self, mock_learning_style_service
    ):
        """Test successful content recommendations"""
        mock_recommendation = Mock()
        mock_recommendation.student_id = "student1"
        mock_recommendation.hybrid_code = "VARK_V_FELDER_AR"
        mock_recommendation.recommended_content_types = [
            "visual",
            "interactive",
            "video",
        ]
        mock_recommendation.content_weights = {
            "visual": 0.8,
            "interactive": 0.7,
            "video": 0.6,
        }
        mock_recommendation.learning_strategies = ["visualization", "practice"]
        mock_recommendation.study_techniques = ["mind_maps", "diagrams"]
        mock_recommendation.difficulty_adjustment = 0.1
        mock_recommendation.pace_adjustment = -0.05
        mock_recommendation.confidence_score = 0.85
        mock_recommendation.generated_at = datetime.now()

        mock_learning_style_service.generate_content_recommendations.return_value = (
            mock_recommendation
        )

        result = await get_content_recommendations(
            "student1", "matematik", "orta", False
        )

        assert result["success"] is True
        assert result["data"]["student_id"] == "student1"
        assert result["data"]["hybrid_code"] == "VARK_V_FELDER_AR"
        assert result["data"]["subject_area"] == "matematik"
        assert result["data"]["difficulty_level"] == "orta"
        assert len(result["data"]["recommended_content_types"]) == 3
        assert "visual" in result["data"]["recommended_content_types"]
        assert result["data"]["adjustments"]["difficulty"] == 0.1
        assert result["data"]["adjustments"]["pace"] == -0.05
        assert "3 içerik türü önerildi" in result["message"]

        mock_learning_style_service.generate_content_recommendations.assert_called_once_with(
            student_id="student1",
            subject_area="matematik",
            difficulty_level="orta",
            force_refresh=False,
        )

    @pytest.mark.asyncio
    async def test_get_content_recommendations_default_params(
        self, mock_learning_style_service
    ):
        """Test content recommendations with default parameters"""
        mock_recommendation = Mock()
        mock_recommendation.student_id = "student1"
        mock_recommendation.hybrid_code = "TEST_CODE"
        mock_recommendation.recommended_content_types = ["text", "audio"]
        mock_recommendation.content_weights = {"text": 0.7, "audio": 0.6}
        mock_recommendation.learning_strategies = ["reading"]
        mock_recommendation.study_techniques = ["notes"]
        mock_recommendation.difficulty_adjustment = 0.0
        mock_recommendation.pace_adjustment = 0.0
        mock_recommendation.confidence_score = 0.75
        mock_recommendation.generated_at = datetime.now()

        mock_learning_style_service.generate_content_recommendations.return_value = (
            mock_recommendation
        )

        # Call with default parameters
        result = await get_content_recommendations("student1")

        assert result["success"] is True
        assert result["data"]["subject_area"] == "matematik"  # default
        assert result["data"]["difficulty_level"] == "orta"  # default

        mock_learning_style_service.generate_content_recommendations.assert_called_once_with(
            student_id="student1",
            subject_area="matematik",
            difficulty_level="orta",
            force_refresh=False,
        )

    @pytest.mark.asyncio
    async def test_get_content_recommendations_error(self, mock_learning_style_service):
        """Test content recommendations with error"""
        mock_learning_style_service.generate_content_recommendations.side_effect = (
            Exception("Recommendation error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_content_recommendations("student1")

        assert exc_info.value.status_code == 500
        assert "içerik önerisi oluşturulamadı" in exc_info.value.detail.lower()


class TestBehavioralDataEndpoint:
    """Test /behavioral-data/{student_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_behavioral_data_profile_updated(
        self, mock_learning_style_service
    ):
        """Test behavioral data update with profile change"""
        # Create mock behavioral data
        behavioral_data = BehavioralData(
            student_id="student1",
            video_watch_time=300.0,
            text_reading_time=120.0,
            interactive_engagement=60.0,
            quiz_completion_rate=0.8,
            note_taking_frequency=5,
            question_asking_frequency=3,
            peer_interaction_count=2,
            help_seeking_behavior=1,
            visual_content_performance=0.85,
            auditory_content_performance=0.7,
            text_content_performance=0.75,
            hands_on_performance=0.9,
            recorded_at=datetime.now(),
        )

        # Mock updated profile
        mock_updated_profile = Mock()
        mock_updated_profile.hybrid_code = "NEW_HYBRID_CODE"
        mock_updated_profile.confidence_score = 0.9
        mock_updated_profile.last_updated = datetime.now()

        mock_learning_style_service.update_behavioral_data.return_value = (
            mock_updated_profile
        )

        result = await update_behavioral_data("student1", behavioral_data)

        assert result["success"] is True
        assert result["data"]["profile_updated"] is True
        assert result["data"]["new_hybrid_code"] == "NEW_HYBRID_CODE"
        assert result["data"]["confidence_score"] == 0.9
        assert "öğrenme stili güncellendi" in result["message"].lower()

        # Verify student_id was set
        assert behavioral_data.student_id == "student1"

        mock_learning_style_service.update_behavioral_data.assert_called_once_with(
            student_id="student1", new_data=behavioral_data
        )

    @pytest.mark.asyncio
    async def test_update_behavioral_data_no_profile_change(
        self, mock_learning_style_service
    ):
        """Test behavioral data update without profile change"""
        behavioral_data = BehavioralData(
            student_id="student1",
            video_watch_time=100.0,
            text_reading_time=50.0,
            interactive_engagement=30.0,
            quiz_completion_rate=0.7,
            recorded_at=datetime.now(),
        )

        mock_learning_style_service.update_behavioral_data.return_value = None

        result = await update_behavioral_data("student1", behavioral_data)

        assert result["success"] is True
        assert result["data"]["profile_updated"] is False
        assert result["data"]["data_recorded"] is True
        assert "davranışsal veri kaydedildi" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_update_behavioral_data_error(self, mock_learning_style_service):
        """Test behavioral data update with error"""
        behavioral_data = BehavioralData(
            student_id="student1", video_watch_time=300.0, recorded_at=datetime.now()
        )

        mock_learning_style_service.update_behavioral_data.side_effect = Exception(
            "Update error"
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_behavioral_data("student1", behavioral_data)

        assert exc_info.value.status_code == 500
        assert "davranışsal veri güncellenemedi" in exc_info.value.detail.lower()


class TestQuestionnaireEndpoint:
    """Test /questionnaire/{student_id} endpoint"""

    @pytest.mark.asyncio
    async def test_submit_questionnaire_success(self, mock_learning_style_service):
        """Test successful questionnaire submission"""
        questionnaire_response = QuestionnaireResponse(
            student_id="student1",
            questionnaire_type="VARK",
            responses={"question_1": "A", "question_2": "B"},
            completion_time=180.0,
            completed_at=datetime.now(),
            version="1.0",
        )

        result = await submit_questionnaire("student1", questionnaire_response)

        assert result["success"] is True
        assert result["data"]["questionnaire_type"] == "VARK"
        assert result["data"]["completion_time"] == 180.0
        assert result["data"]["responses_count"] == 2
        assert "anket yanıtları kaydedildi" in result["message"].lower()

        # Verify student_id was set
        assert questionnaire_response.student_id == "student1"

        # Verify cache operations
        assert "student1" in mock_learning_style_service.questionnaire_cache
        assert len(mock_learning_style_service.questionnaire_cache["student1"]) == 1
        assert (
            mock_learning_style_service.questionnaire_cache["student1"][0]
            == questionnaire_response
        )

    @pytest.mark.asyncio
    async def test_submit_questionnaire_existing_cache(
        self, mock_learning_style_service
    ):
        """Test questionnaire submission with existing cache"""
        # Set up existing cache
        mock_learning_style_service.questionnaire_cache = {
            "student1": ["existing_response"]
        }
        mock_learning_style_service.profiles_cache = {"student1": "existing_profile"}

        questionnaire_response = QuestionnaireResponse(
            student_id="student1",
            questionnaire_type="Felder",
            responses={"question_1": "C"},
            completion_time=150.0,
            completed_at=datetime.now(),
        )

        result = await submit_questionnaire("student1", questionnaire_response)

        assert result["success"] is True
        # Verify new response was appended
        assert len(mock_learning_style_service.questionnaire_cache["student1"]) == 2
        # Verify profile cache was cleared
        assert "student1" not in mock_learning_style_service.profiles_cache

    @pytest.mark.asyncio
    async def test_submit_questionnaire_error(self, mock_learning_style_service):
        """Test questionnaire submission with error"""
        questionnaire_response = QuestionnaireResponse(
            student_id="student1",
            questionnaire_type="VARK",
            responses={"question_1": "A"},
            completion_time=120.0,
            completed_at=datetime.now(),
        )

        # Mock an error in cache operations
        mock_learning_style_service.questionnaire_cache = None

        with pytest.raises(HTTPException) as exc_info:
            await submit_questionnaire("student1", questionnaire_response)

        assert exc_info.value.status_code == 500
        assert "anket kaydedilemedi" in exc_info.value.detail.lower()


class TestExplanationEndpoint:
    """Test /explanation/{student_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_learning_style_explanation_success(
        self, mock_learning_style_service
    ):
        """Test successful learning style explanation"""
        mock_explanation = {
            "hybrid_code": "VARK_V_FELDER_AR",
            "explanation": "Bu profil görsel öğrenmeyi tercih eder...",
            "characteristics": ["Görsel", "Aktif", "Pratik"],
            "recommendations": ["Diyagramlar kullanın", "Uygulamalı çalışın"],
        }

        mock_learning_style_service.get_learning_style_explanation.return_value = (
            mock_explanation
        )

        result = await get_learning_style_explanation("student1")

        assert result["success"] is True
        assert result["data"] == mock_explanation
        assert "öğrenme stili açıklaması hazırlandı" in result["message"].lower()

        mock_learning_style_service.get_learning_style_explanation.assert_called_once_with(
            "student1"
        )

    @pytest.mark.asyncio
    async def test_get_learning_style_explanation_error(
        self, mock_learning_style_service
    ):
        """Test learning style explanation with error"""
        mock_learning_style_service.get_learning_style_explanation.side_effect = (
            Exception("Explanation error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_learning_style_explanation("student1")

        assert exc_info.value.status_code == 500
        assert "açıklama oluşturulamadı" in exc_info.value.detail.lower()


class TestHybridCodesEndpoint:
    """Test /hybrid-codes endpoint"""

    @pytest.mark.asyncio
    async def test_get_all_hybrid_codes_success(self, mock_learning_style_service):
        """Test successful hybrid codes retrieval"""
        mock_hybrid_codes = [
            {"code": "VARK_V_FELDER_AR", "description": "Visual-Active-Reflective"},
            {"code": "VARK_A_FELDER_SI", "description": "Auditory-Sensing-Intuitive"},
            {"code": "VARK_R_FELDER_VV", "description": "Reading-Visual-Verbal"},
        ]

        mock_learning_style_service.get_all_hybrid_codes.return_value = (
            mock_hybrid_codes
        )

        result = await get_all_hybrid_codes()

        assert result["success"] is True
        assert result["data"]["total_combinations"] == 3
        assert result["data"]["hybrid_codes"] == mock_hybrid_codes
        assert "3 hibrit kod kombinasyonu" in result["message"]

        mock_learning_style_service.get_all_hybrid_codes.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_hybrid_codes_error(self, mock_learning_style_service):
        """Test hybrid codes retrieval with error"""
        mock_learning_style_service.get_all_hybrid_codes.side_effect = Exception(
            "Hybrid codes error"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_all_hybrid_codes()

        assert exc_info.value.status_code == 500
        assert "hibrit kodlar alınamadı" in exc_info.value.detail.lower()


class TestStatisticsEndpoint:
    """Test /statistics endpoint"""

    @pytest.mark.asyncio
    async def test_get_learning_style_statistics_success(
        self, mock_learning_style_service
    ):
        """Test successful statistics retrieval"""
        mock_statistics = {
            "total_students": 150,
            "most_common_vark": "Visual",
            "most_common_felder": "Active-Sensing",
            "average_confidence": 0.82,
            "distribution": {
                "Visual": 45,
                "Auditory": 30,
                "Reading": 25,
                "Kinesthetic": 50,
            },
        }

        mock_learning_style_service.get_learning_style_statistics.return_value = (
            mock_statistics
        )

        result = await get_learning_style_statistics()

        assert result["success"] is True
        assert result["data"] == mock_statistics
        assert "istatistikler hazırlandı" in result["message"].lower()

        mock_learning_style_service.get_learning_style_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_learning_style_statistics_error(
        self, mock_learning_style_service
    ):
        """Test statistics retrieval with error"""
        mock_learning_style_service.get_learning_style_statistics.side_effect = (
            Exception("Statistics error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_learning_style_statistics()

        assert exc_info.value.status_code == 500
        assert "istatistikler alınamadı" in exc_info.value.detail.lower()


class TestExportEndpoint:
    """Test /export/{student_id} endpoint"""

    @pytest.mark.asyncio
    async def test_export_learning_profile_success(self, mock_learning_style_service):
        """Test successful profile export"""
        mock_export_data = {
            "student_id": "student1",
            "profile": {
                "hybrid_code": "VARK_V_FELDER_AR",
                "vark_scores": {"V": 0.8, "A": 0.6, "R": 0.4, "K": 0.3},
                "felder_scores": {"AR": 0.7, "SI": 0.5, "VV": 0.8, "SG": 0.6},
            },
            "history": ["2024-01-01: First detection", "2024-01-15: Updated"],
            "recommendations": ["Use visual aids", "Practice actively"],
        }

        mock_learning_style_service.export_learning_profile.return_value = (
            mock_export_data
        )

        result = await export_learning_profile("student1")

        assert result["success"] is True
        assert result["data"] == mock_export_data
        assert "öğrenme profili dışa aktarıldı" in result["message"].lower()

        mock_learning_style_service.export_learning_profile.assert_called_once_with(
            "student1"
        )

    @pytest.mark.asyncio
    async def test_export_learning_profile_error(self, mock_learning_style_service):
        """Test profile export with error"""
        mock_learning_style_service.export_learning_profile.side_effect = Exception(
            "Export error"
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_learning_profile("student1")

        assert exc_info.value.status_code == 500
        assert "profil dışa aktarılamadı" in exc_info.value.detail.lower()


class TestContentExplanationEndpoint:
    """Test /content-explanation/{hybrid_code}/{content_type} endpoint"""

    @pytest.mark.asyncio
    async def test_get_content_explanation_success(self, mock_learning_style_service):
        """Test successful content explanation"""
        mock_explanation = (
            "Bu hibrit kod için video içerikleri en etkili öğrenme yöntemidir..."
        )

        mock_recommender = Mock()
        mock_recommender.get_content_explanation.return_value = mock_explanation
        mock_learning_style_service.recommender = mock_recommender

        result = await get_content_explanation("VARK_V_FELDER_AR", "video")

        assert result["success"] is True
        assert result["data"]["hybrid_code"] == "VARK_V_FELDER_AR"
        assert result["data"]["content_type"] == "video"
        assert result["data"]["explanation"] == mock_explanation
        assert "içerik açıklaması hazırlandı" in result["message"].lower()

        mock_recommender.get_content_explanation.assert_called_once_with(
            hybrid_code="VARK_V_FELDER_AR", content_type="video"
        )

    @pytest.mark.asyncio
    async def test_get_content_explanation_error(self, mock_learning_style_service):
        """Test content explanation with error"""
        mock_recommender = Mock()
        mock_recommender.get_content_explanation.side_effect = Exception(
            "Explanation error"
        )
        mock_learning_style_service.recommender = mock_recommender

        with pytest.raises(HTTPException) as exc_info:
            await get_content_explanation("VARK_V_FELDER_AR", "video")

        assert exc_info.value.status_code == 500
        assert "açıklama oluşturulamadı" in exc_info.value.detail.lower()


class TestUpdateRecommendationsEndpoint:
    """Test /update-recommendations/{student_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_recommendations_based_on_performance_success(
        self, mock_learning_style_service
    ):
        """Test successful performance-based recommendation update"""
        # Mock current recommendation
        mock_current_rec = Mock()
        mock_current_rec.student_id = "student1"

        # Mock updated recommendation
        mock_updated_rec = Mock()
        mock_updated_rec.student_id = "student1"
        mock_updated_rec.recommended_content_types = ["video", "interactive"]
        mock_updated_rec.difficulty_adjustment = 0.15
        mock_updated_rec.pace_adjustment = 0.1
        mock_updated_rec.generated_at = datetime.now()

        mock_learning_style_service.generate_content_recommendations.return_value = (
            mock_current_rec
        )

        mock_recommender = Mock()
        mock_recommender.update_recommendations_based_on_performance.return_value = (
            mock_updated_rec
        )
        mock_learning_style_service.recommender = mock_recommender

        performance_data = {"accuracy": 0.85, "speed": 0.7, "engagement": 0.9}

        result = await update_recommendations_based_on_performance(
            "student1", performance_data
        )

        assert result["success"] is True
        assert result["data"]["student_id"] == "student1"
        assert result["data"]["updated_content_types"] == ["video", "interactive"]
        assert result["data"]["difficulty_adjustment"] == 0.15
        assert result["data"]["pace_adjustment"] == 0.1
        assert (
            "öneriler performans verilerine göre güncellendi"
            in result["message"].lower()
        )

        # Verify cache update
        cache_key = "student1_matematik_orta"
        assert (
            mock_learning_style_service.recommendations_cache[cache_key]
            == mock_updated_rec
        )

        mock_learning_style_service.generate_content_recommendations.assert_called_once_with(
            "student1"
        )
        mock_recommender.update_recommendations_based_on_performance.assert_called_once_with(
            student_id="student1",
            current_recommendation=mock_current_rec,
            performance_data=performance_data,
        )

    @pytest.mark.asyncio
    async def test_update_recommendations_based_on_performance_error(
        self, mock_learning_style_service
    ):
        """Test performance-based recommendation update with error"""
        mock_learning_style_service.generate_content_recommendations.side_effect = (
            Exception("Update error")
        )

        performance_data = {"accuracy": 0.8}

        with pytest.raises(HTTPException) as exc_info:
            await update_recommendations_based_on_performance(
                "student1", performance_data
            )

        assert exc_info.value.status_code == 500
        assert "öneriler güncellenemedi" in exc_info.value.detail.lower()


class TestHealthCheckEndpoint:
    """Test /health endpoint"""

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_learning_style_service):
        """Test successful health check"""
        result = await health_check()

        assert result["success"] is True
        assert result["data"]["system_status"] == "healthy"
        assert result["data"]["total_profiles"] == 0  # Empty cache
        assert result["data"]["total_behavioral_data_points"] == 1  # From fixture
        assert result["data"]["total_questionnaire_responses"] == 1  # From fixture
        assert result["data"]["available_hybrid_combinations"] == 64
        assert result["data"]["detector_status"] == "active"
        assert result["data"]["recommender_status"] == "active"
        assert "hibrit öğrenme stili sistemi çalışıyor" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_health_check_with_data(self, mock_learning_style_service):
        """Test health check with cached data"""
        # Set up cache data
        mock_learning_style_service.profiles_cache = {
            "student1": "profile1",
            "student2": "profile2",
        }
        mock_learning_style_service.behavioral_data_cache = {
            "student1": [{"data1": "value1"}, {"data2": "value2"}],
            "student2": [{"data3": "value3"}],
        }
        mock_learning_style_service.questionnaire_cache = {"student1": [{"q1": "a1"}]}

        result = await health_check()

        assert result["success"] is True
        assert result["data"]["total_profiles"] == 2
        assert result["data"]["total_behavioral_data_points"] == 3
        assert result["data"]["total_questionnaire_responses"] == 1

    @pytest.mark.asyncio
    async def test_health_check_error(self, mock_learning_style_service):
        """Test health check with error"""
        # Force an error by making the cache access fail
        mock_learning_style_service.profiles_cache = None

        with pytest.raises(HTTPException) as exc_info:
            await health_check()

        assert exc_info.value.status_code == 500
        assert "sistem sağlık kontrolü başarısız" in exc_info.value.detail.lower()


class TestAPIEndpointParameters:
    """Test API endpoint parameter validation and edge cases"""

    @pytest.mark.asyncio
    async def test_content_recommendations_custom_params(
        self, mock_learning_style_service
    ):
        """Test content recommendations with custom parameters"""
        mock_recommendation = Mock()
        mock_recommendation.student_id = "student1"
        mock_recommendation.hybrid_code = "TEST"
        mock_recommendation.recommended_content_types = ["custom"]
        mock_recommendation.content_weights = {"custom": 1.0}
        mock_recommendation.learning_strategies = ["custom_strategy"]
        mock_recommendation.study_techniques = ["custom_technique"]
        mock_recommendation.difficulty_adjustment = 0.2
        mock_recommendation.pace_adjustment = 0.15
        mock_recommendation.confidence_score = 0.95
        mock_recommendation.generated_at = datetime.now()

        mock_learning_style_service.generate_content_recommendations.return_value = (
            mock_recommendation
        )

        result = await get_content_recommendations(
            "student1", "fen_bilgisi", "zor", True
        )

        assert result["success"] is True
        assert result["data"]["subject_area"] == "fen_bilgisi"
        assert result["data"]["difficulty_level"] == "zor"

        mock_learning_style_service.generate_content_recommendations.assert_called_once_with(
            student_id="student1",
            subject_area="fen_bilgisi",
            difficulty_level="zor",
            force_refresh=True,
        )

    @pytest.mark.asyncio
    async def test_special_characters_in_student_id(self, mock_learning_style_service):
        """Test handling of special characters in student IDs"""
        special_student_id = "student-123_test@domain.com"

        mock_profile = Mock()
        mock_profile.student_id = special_student_id
        mock_profile.hybrid_code = "TEST_CODE"
        mock_profile.vark_profile = Mock()
        mock_profile.vark_profile.visual = 0.8
        mock_profile.vark_profile.auditory = 0.6
        mock_profile.vark_profile.reading = 0.4
        mock_profile.vark_profile.kinesthetic = 0.3
        mock_profile.vark_profile.dominant_vark = Mock()
        mock_profile.vark_profile.dominant_vark.value = "visual"
        mock_profile.felder_profile = Mock()
        mock_profile.felder_profile.active_reflective = 0.7
        mock_profile.felder_profile.sensing_intuitive = 0.5
        mock_profile.felder_profile.visual_verbal = 0.8
        mock_profile.felder_profile.sequential_global = 0.6
        mock_profile.felder_profile.learning_preferences = ["visual"]
        mock_profile.confidence_score = 0.85
        mock_profile.confidence_level = Mock()
        mock_profile.confidence_level.value = "high"
        mock_profile.data_points_used = 15
        mock_profile.detection_date = datetime.now()
        mock_profile.last_updated = datetime.now()

        mock_learning_style_service.detect_learning_style.return_value = mock_profile

        result = await detect_learning_style(special_student_id, False)

        assert result["success"] is True
        assert result["data"]["student_id"] == special_student_id


class TestLearningStyleAPIIntegration:
    """Integration tests for Learning Style API"""

    @pytest.mark.asyncio
    async def test_full_workflow_detect_and_recommend(
        self, mock_learning_style_service
    ):
        """Test complete workflow: detection -> recommendations"""
        # Mock profile
        mock_profile = Mock()
        mock_profile.student_id = "student1"
        mock_profile.hybrid_code = "VR-ASVS"
        mock_profile.vark_profile = Mock()
        mock_profile.vark_profile.visual = 0.8
        mock_profile.vark_profile.auditory = 0.3
        mock_profile.vark_profile.reading = 0.7
        mock_profile.vark_profile.kinesthetic = 0.4
        mock_profile.vark_profile.dominant_vark = Mock()
        mock_profile.vark_profile.dominant_vark.value = "visual"
        mock_profile.felder_profile = Mock()
        mock_profile.felder_profile.active_reflective = -0.5
        mock_profile.felder_profile.sensing_intuitive = -0.7
        mock_profile.felder_profile.visual_verbal = -0.8
        mock_profile.felder_profile.sequential_global = -0.6
        mock_profile.felder_profile.learning_preferences = [
            "active",
            "sensing",
            "visual",
            "sequential",
        ]
        mock_profile.confidence_score = 0.88
        mock_profile.confidence_level = Mock()
        mock_profile.confidence_level.value = "high"
        mock_profile.data_points_used = 20
        mock_profile.detection_date = datetime.now()
        mock_profile.last_updated = datetime.now()

        mock_learning_style_service.detect_learning_style.return_value = mock_profile

        # Mock recommendation
        mock_recommendation = Mock()
        mock_recommendation.student_id = "student1"
        mock_recommendation.hybrid_code = "VR-ASVS"
        mock_recommendation.recommended_content_types = [
            "visual_diagrams",
            "reading_materials",
            "interactive_simulations",
        ]
        mock_recommendation.content_weights = {
            "visual_diagrams": 0.8,
            "reading_materials": 0.7,
            "interactive_simulations": 0.6,
        }
        mock_recommendation.learning_strategies = [
            "visual_organization",
            "step_by_step",
            "hands_on_practice",
        ]
        mock_recommendation.study_techniques = [
            "mind_maps",
            "flow_charts",
            "concept_diagrams",
        ]
        mock_recommendation.difficulty_adjustment = 0.0
        mock_recommendation.pace_adjustment = -0.1
        mock_recommendation.confidence_score = 0.85
        mock_recommendation.generated_at = datetime.now()

        mock_learning_style_service.generate_content_recommendations.return_value = (
            mock_recommendation
        )

        # Step 1: Detect learning style
        detect_result = await detect_learning_style("student1", False)
        assert detect_result["success"] is True
        assert detect_result["data"]["hybrid_code"] == "VR-ASVS"

        # Step 2: Get recommendations
        recommend_result = await get_content_recommendations(
            "student1", "matematik", "orta", False
        )
        assert recommend_result["success"] is True
        assert recommend_result["data"]["hybrid_code"] == "VR-ASVS"
        assert len(recommend_result["data"]["recommended_content_types"]) == 3

        # Verify service calls
        mock_learning_style_service.detect_learning_style.assert_called_once()
        mock_learning_style_service.generate_content_recommendations.assert_called_once()


if __name__ == "__main__":
    pytest.main(
        [__file__, "-v", "--cov=api.learning_style", "--cov-report=term-missing"]
    )
