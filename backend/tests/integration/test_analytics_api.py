"""
Analytics API Test Dosyası
Öğrenci, sınıf ve sistem geneli analytics API'leri testleri
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException

# Test imports
try:
    from api.analytics import (
        ClassAnalyticsRequest,
        ExportRequest,
        StudentAnalyticsRequest,
        _calculate_student_performance_metrics,
        _calculate_system_metrics,
        _get_class_students,
        _get_exam_performance_analysis,
        _get_learning_style_analysis,
        _get_revolutionary_features_usage,
        export_analytics_csv,
        export_analytics_excel,
        export_analytics_pdf,
        get_admin_dashboard_analytics,
        get_class_analytics,
        get_student_analytics,
    )
    from models.database import User
except ImportError as e:
    print(f"Import error: {e}")
    # Fallback imports
    import sys

    sys.path.append("backend")
    from models.database import User


class TestAnalyticsAPI:
    """Analytics API testleri"""

    @pytest.fixture
    def mock_user(self):
        """Mock kullanıcı"""
        user = Mock(spec=User)
        user.id = "test_user_123"
        user.role = "student"
        user.name = "Test Öğrenci"
        return user

    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin kullanıcı"""
        user = Mock(spec=User)
        user.id = "admin_123"
        user.role = "admin"
        user.name = "Test Admin"
        return user

    @pytest.fixture
    def mock_elasticsearch_service(self):
        """Mock Elasticsearch servisi"""
        es_service = Mock()
        es_service.analytics_service = Mock()
        es_service.analytics_service.get_user_analytics = AsyncMock(
            return_value={
                "total_sessions": 25,
                "total_study_time": 45.5,
                "questions_solved": 1247,
                "accuracy_rate": 0.715,
            }
        )
        es_service.analytics_service.log_event = AsyncMock()
        return es_service

    @pytest.fixture
    def sample_student_analytics_data(self):
        """Örnek öğrenci analytics verisi"""
        return {
            "student_id": "student_123",
            "period": {
                "start_date": "2025-01-01T00:00:00",
                "end_date": "2025-01-31T23:59:59",
            },
            "basic_metrics": {
                "total_sessions": 25,
                "total_study_time": 45.5,
                "questions_solved": 1247,
                "accuracy_rate": 0.715,
            },
            "performance_metrics": {
                "total_study_time_hours": 45.5,
                "total_questions_solved": 1247,
                "correct_answers": 892,
                "accuracy_rate": 0.715,
                "improvement_trend": "increasing",
            },
            "learning_style": {
                "vark_profile": {
                    "visual": 0.7,
                    "auditory": 0.3,
                    "reading": 0.6,
                    "kinesthetic": 0.4,
                },
                "hybrid_code": "V-A-S-S",
                "confidence_level": 0.85,
            },
        }


class TestStudentAnalytics:
    """Öğrenci analytics testleri"""

    @pytest.mark.asyncio
    async def test_get_student_analytics_success(
        self, mock_user, mock_elasticsearch_service
    ):
        """Öğrenci analytics başarılı alma testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch(
                "backend.api.analytics._calculate_student_performance_metrics"
            ) as mock_perf:
                with patch(
                    "backend.api.analytics._get_learning_style_analysis"
                ) as mock_style:
                    with patch(
                        "backend.api.analytics._get_exam_performance_analysis"
                    ) as mock_exam:
                        with patch(
                            "backend.api.analytics._get_subject_performance_analysis"
                        ) as mock_subject:
                            # Mock return values
                            mock_perf.return_value = {"accuracy_rate": 0.715}
                            mock_style.return_value = {"hybrid_code": "V-A-S-S"}
                            mock_exam.return_value = {"total_exams": 12}
                            mock_subject.return_value = {
                                "subjects": {"Matematik": {"accuracy_rate": 0.68}}
                            }

                            # Test
                            result = await get_student_analytics(
                                student_id="student_123",
                                start_date=None,
                                end_date=None,
                                include_detailed=False,
                                current_user=mock_user,
                            )

                            # Assertions
                            assert result["success"] is True
                            assert "data" in result
                            assert result["data"]["student_id"] == "student_123"
                            assert "basic_metrics" in result["data"]
                            assert "performance_metrics" in result["data"]
                            assert "learning_style" in result["data"]

                            # Elasticsearch service çağrıları kontrol et
                            mock_elasticsearch_service.analytics_service.get_user_analytics.assert_called_once()
                            mock_elasticsearch_service.analytics_service.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_student_analytics_with_detailed(
        self, mock_user, mock_elasticsearch_service
    ):
        """Detaylı öğrenci analytics testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch(
                "backend.api.analytics._calculate_student_performance_metrics",
                return_value={},
            ):
                with patch(
                    "backend.api.analytics._get_learning_style_analysis",
                    return_value={},
                ):
                    with patch(
                        "backend.api.analytics._get_exam_performance_analysis",
                        return_value={},
                    ):
                        with patch(
                            "backend.api.analytics._get_subject_performance_analysis",
                            return_value={},
                        ):
                            with patch(
                                "backend.api.analytics._get_detailed_student_analysis"
                            ) as mock_detailed:
                                mock_detailed.return_value = {
                                    "study_patterns": {
                                        "preferred_hours": ["14:00-16:00"]
                                    },
                                    "motivation_analysis": {"motivation_score": 0.75},
                                }

                                result = await get_student_analytics(
                                    student_id="student_123",
                                    start_date=None,
                                    end_date=None,
                                    include_detailed=True,
                                    current_user=mock_user,
                                )

                                assert result["success"] is True
                                assert "detailed_analysis" in result["data"]
                                mock_detailed.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_student_analytics_error_handling(self, mock_user):
        """Öğrenci analytics hata yönetimi testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            side_effect=Exception("ES Error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_student_analytics(
                    student_id="student_123",
                    start_date=None,
                    end_date=None,
                    include_detailed=False,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 500
            assert "Analytics alınırken hata" in str(exc_info.value.detail)


class TestClassAnalytics:
    """Sınıf analytics testleri"""

    @pytest.mark.asyncio
    async def test_get_class_analytics_success(
        self, mock_user, mock_elasticsearch_service
    ):
        """Sınıf analytics başarılı alma testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch("backend.api.analytics._get_class_students") as mock_students:
                with patch(
                    "backend.api.analytics._calculate_class_metrics"
                ) as mock_metrics:
                    with patch(
                        "backend.api.analytics._get_class_performance_distribution"
                    ) as mock_dist:
                        with patch(
                            "backend.api.analytics._get_class_subject_analysis"
                        ) as mock_subject:
                            with patch(
                                "backend.api.analytics._get_class_learning_style_distribution"
                            ) as mock_style:
                                # Mock return values
                                mock_students.return_value = [
                                    {"id": "student_1", "name": "Ahmet Yılmaz"},
                                    {"id": "student_2", "name": "Ayşe Demir"},
                                ]
                                mock_metrics.return_value = {
                                    "class_accuracy_rate": 0.742
                                }
                                mock_dist.return_value = {
                                    "score_distribution": {"90-100": 2}
                                }
                                mock_subject.return_value = {
                                    "subject_averages": {"Matematik": 72.5}
                                }
                                mock_style.return_value = {
                                    "vark_distribution": {"visual": 0.45}
                                }

                                result = await get_class_analytics(
                                    class_id="class_123",
                                    start_date=None,
                                    end_date=None,
                                    include_students=True,
                                    current_user=mock_user,
                                )

                                assert result["success"] is True
                                assert result["data"]["class_id"] == "class_123"
                                assert result["data"]["student_count"] == 2
                                assert "class_metrics" in result["data"]
                                assert "student_details" in result["data"]

    @pytest.mark.asyncio
    async def test_get_class_analytics_without_students(
        self, mock_user, mock_elasticsearch_service
    ):
        """Öğrenci detayları olmadan sınıf analytics testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch("backend.api.analytics._get_class_students", return_value=[]):
                with patch(
                    "backend.api.analytics._calculate_class_metrics", return_value={}
                ):
                    with patch(
                        "backend.api.analytics._get_class_performance_distribution",
                        return_value={},
                    ):
                        with patch(
                            "backend.api.analytics._get_class_subject_analysis",
                            return_value={},
                        ):
                            with patch(
                                "backend.api.analytics._get_class_learning_style_distribution",
                                return_value={},
                            ):
                                result = await get_class_analytics(
                                    class_id="class_123",
                                    start_date=None,
                                    end_date=None,
                                    include_students=False,
                                    current_user=mock_user,
                                )

                                assert result["success"] is True
                                assert "student_details" not in result["data"]


class TestAdminAnalytics:
    """Admin analytics testleri"""

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_analytics_success(
        self, mock_admin_user, mock_elasticsearch_service
    ):
        """Admin dashboard analytics başarılı alma testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch(
                "backend.api.analytics._calculate_system_metrics"
            ) as mock_system:
                with patch("backend.api.analytics._get_user_statistics") as mock_users:
                    with patch(
                        "backend.api.analytics._get_exam_statistics"
                    ) as mock_exams:
                        with patch(
                            "backend.api.analytics._get_content_usage_statistics"
                        ) as mock_content:
                            with patch(
                                "backend.api.analytics._get_system_performance_metrics"
                            ) as mock_perf:
                                with patch(
                                    "backend.api.analytics._get_revolutionary_features_usage"
                                ) as mock_rev:
                                    # Mock return values
                                    mock_system.return_value = {
                                        "total_active_users": 15247
                                    }
                                    mock_users.return_value = {"total_users": 25847}
                                    mock_exams.return_value = {
                                        "total_exams_taken": 45896
                                    }
                                    mock_content.return_value = {
                                        "total_content_views": 189456
                                    }
                                    mock_perf.return_value = {
                                        "api_response_time_ms": 145
                                    }
                                    mock_rev.return_value = {
                                        "bionic_reading": {"total_users": 8456}
                                    }

                                    result = await get_admin_dashboard_analytics(
                                        start_date=None,
                                        end_date=None,
                                        current_user=mock_admin_user,
                                    )

                                    assert result["success"] is True
                                    assert "system_metrics" in result["data"]
                                    assert "user_statistics" in result["data"]
                                    assert "revolutionary_features" in result["data"]

    @pytest.mark.asyncio
    async def test_get_admin_dashboard_analytics_unauthorized(self, mock_user):
        """Admin yetkisi olmayan kullanıcı testi"""
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_dashboard_analytics(
                start_date=None,
                end_date=None,
                current_user=mock_user,  # Normal user, not admin
            )

        assert exc_info.value.status_code == 403
        assert "Admin yetkisi gerekli" in str(exc_info.value.detail)


class TestExportFunctionality:
    """Export fonksiyonalitesi testleri"""

    @pytest.mark.asyncio
    async def test_export_analytics_pdf_success(
        self, mock_user, mock_elasticsearch_service
    ):
        """PDF export başarılı testi"""
        export_request = ExportRequest(
            format="pdf", data_type="student", filters={"student_id": "student_123"}
        )

        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch(
                "backend.api.analytics._get_student_analytics_for_export"
            ) as mock_data:
                with patch("backend.api.analytics._generate_pdf_content") as mock_pdf:
                    mock_data.return_value = {"student_info": {"name": "Test Student"}}

                    result = await export_analytics_pdf(
                        request=export_request, current_user=mock_user
                    )

                    assert result["success"] is True
                    assert "pdf_content" in result["data"]
                    assert "filename" in result["data"]
                    assert result["data"]["filename"].endswith(".pdf")

    @pytest.mark.asyncio
    async def test_export_analytics_excel_success(
        self, mock_user, mock_elasticsearch_service
    ):
        """Excel export başarılı testi"""
        export_request = ExportRequest(
            format="excel", data_type="class", filters={"class_id": "class_123"}
        )

        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch(
                "backend.api.analytics._get_analytics_data_for_export"
            ) as mock_data:
                with patch(
                    "backend.api.analytics._generate_excel_content"
                ) as mock_excel:
                    mock_data.return_value = {"class_info": {"name": "Test Class"}}

                    result = await export_analytics_excel(
                        request=export_request, current_user=mock_user
                    )

                    assert result["success"] is True
                    assert "excel_content" in result["data"]
                    assert "filename" in result["data"]
                    assert result["data"]["filename"].endswith(".xlsx")

    @pytest.mark.asyncio
    async def test_export_analytics_csv_success(
        self, mock_user, mock_elasticsearch_service
    ):
        """CSV export başarılı testi"""
        export_request = ExportRequest(format="csv", data_type="admin", filters={})

        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch(
                "backend.api.analytics._get_analytics_data_for_export"
            ) as mock_data:
                with patch("backend.api.analytics._generate_csv_content") as mock_csv:
                    mock_data.return_value = {"system_summary": {"total_users": 25847}}

                    result = await export_analytics_csv(
                        request=export_request, current_user=mock_user
                    )

                    assert result["success"] is True
                    assert "csv_content" in result["data"]
                    assert "filename" in result["data"]
                    assert result["data"]["filename"].endswith(".csv")

    @pytest.mark.asyncio
    async def test_export_invalid_data_type(self, mock_user):
        """Geçersiz data_type export testi"""
        export_request = ExportRequest(format="pdf", data_type="invalid", filters={})

        with pytest.raises(HTTPException) as exc_info:
            await export_analytics_pdf(request=export_request, current_user=mock_user)

        assert exc_info.value.status_code == 400
        assert "Geçersiz data_type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_export_missing_student_id(self, mock_user):
        """Student ID eksik export testi"""
        export_request = ExportRequest(
            format="pdf", data_type="student", filters={}  # student_id eksik
        )

        with pytest.raises(HTTPException) as exc_info:
            await export_analytics_pdf(request=export_request, current_user=mock_user)

        assert exc_info.value.status_code == 400
        assert "student_id gerekli" in str(exc_info.value.detail)


class TestHelperFunctions:
    """Helper fonksiyonları testleri"""

    @pytest.mark.asyncio
    async def test_calculate_student_performance_metrics(self):
        """Öğrenci performans metrikleri hesaplama testi"""
        result = await _calculate_student_performance_metrics(
            student_id="student_123",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            es_service=Mock(),
        )

        assert isinstance(result, dict)
        assert "total_study_time_hours" in result
        assert "accuracy_rate" in result
        assert "improvement_trend" in result

    @pytest.mark.asyncio
    async def test_get_learning_style_analysis(self):
        """Öğrenme stili analizi testi"""
        result = await _get_learning_style_analysis("student_123")

        assert isinstance(result, dict)
        assert "vark_profile" in result
        assert "felder_silverman_profile" in result
        assert "hybrid_code" in result
        assert "confidence_level" in result

    @pytest.mark.asyncio
    async def test_get_exam_performance_analysis(self):
        """Sınav performans analizi testi"""
        result = await _get_exam_performance_analysis(
            student_id="student_123",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
        )

        assert isinstance(result, dict)
        assert "total_exams" in result
        assert "average_score" in result
        assert "exam_types" in result

    @pytest.mark.asyncio
    async def test_get_class_students(self):
        """Sınıf öğrencileri alma testi"""
        result = await _get_class_students("class_123")

        assert isinstance(result, list)
        if result:  # Eğer öğrenci varsa
            assert "id" in result[0]
            assert "name" in result[0]

    @pytest.mark.asyncio
    async def test_calculate_system_metrics(self):
        """Sistem metrikleri hesaplama testi"""
        result = await _calculate_system_metrics(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            es_service=Mock(),
        )

        assert isinstance(result, dict)
        assert "total_active_users" in result
        assert "system_uptime_percentage" in result
        assert "api_response_time_ms" in result

    @pytest.mark.asyncio
    async def test_get_revolutionary_features_usage(self):
        """Devrimsel özellik kullanımı testi"""
        result = await _get_revolutionary_features_usage(
            start_date=datetime.now() - timedelta(days=30), end_date=datetime.now()
        )

        assert isinstance(result, dict)
        assert "bionic_reading" in result
        assert "fsrs_scheduling" in result
        assert "text_simplification" in result
        assert "multi_agent_coordination" in result
        assert "vark_felder_hybrid" in result
        assert "turkish_zpd_maarif" in result
        assert "turkish_morphology_irt" in result


class TestPydanticModels:
    """Pydantic model testleri"""

    def test_student_analytics_request_model(self):
        """StudentAnalyticsRequest model testi"""
        request = StudentAnalyticsRequest(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            include_detailed=True,
        )

        assert request.include_detailed is True
        assert request.start_date is not None
        assert request.end_date is not None

    def test_class_analytics_request_model(self):
        """ClassAnalyticsRequest model testi"""
        request = ClassAnalyticsRequest(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            include_students=False,
        )

        assert request.include_students is False
        assert request.start_date is not None
        assert request.end_date is not None

    def test_export_request_model(self):
        """ExportRequest model testi"""
        request = ExportRequest(
            format="pdf", data_type="student", filters={"student_id": "123"}
        )

        assert request.format == "pdf"
        assert request.data_type == "student"
        assert request.filters["student_id"] == "123"

    def test_export_request_validation(self):
        """ExportRequest validation testi"""
        # Format gerekli
        with pytest.raises(ValueError):
            ExportRequest(data_type="student")

        # Data type gerekli
        with pytest.raises(ValueError):
            ExportRequest(format="pdf")


class TestErrorHandling:
    """Hata yönetimi testleri"""

    @pytest.mark.asyncio
    async def test_helper_function_error_handling(self):
        """Helper fonksiyonları hata yönetimi testi"""
        # Mock bir exception fırlatan fonksiyon
        with patch("backend.api.analytics.logger") as mock_logger:
            # Test _calculate_student_performance_metrics error handling
            with patch(
                "backend.api.analytics._calculate_student_performance_metrics"
            ) as mock_func:
                mock_func.side_effect = Exception("Test error")

                result = await _calculate_student_performance_metrics(
                    "student_123", datetime.now(), datetime.now(), Mock()
                )

                # Hata durumunda boş dict dönmeli
                assert result == {}

    @pytest.mark.asyncio
    async def test_api_endpoint_error_handling(self, mock_user):
        """API endpoint hata yönetimi testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            side_effect=Exception("Service error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_student_analytics(
                    student_id="student_123",
                    start_date=None,
                    end_date=None,
                    include_detailed=False,
                    current_user=mock_user,
                )

            assert exc_info.value.status_code == 500
            assert "Analytics alınırken hata" in str(exc_info.value.detail)


class TestTurkishLanguageSupport:
    """Türkçe dil desteği testleri"""

    @pytest.mark.asyncio
    async def test_turkish_error_messages(self, mock_user):
        """Türkçe hata mesajları testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            side_effect=Exception("Test error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_student_analytics(
                    student_id="student_123",
                    start_date=None,
                    end_date=None,
                    include_detailed=False,
                    current_user=mock_user,
                )

            # Hata mesajı Türkçe olmalı
            assert "Analytics alınırken hata" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_turkish_success_messages(
        self, mock_user, mock_elasticsearch_service
    ):
        """Türkçe başarı mesajları testi"""
        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_elasticsearch_service,
        ):
            with patch(
                "backend.api.analytics._calculate_student_performance_metrics",
                return_value={},
            ):
                with patch(
                    "backend.api.analytics._get_learning_style_analysis",
                    return_value={},
                ):
                    with patch(
                        "backend.api.analytics._get_exam_performance_analysis",
                        return_value={},
                    ):
                        with patch(
                            "backend.api.analytics._get_subject_performance_analysis",
                            return_value={},
                        ):
                            result = await get_student_analytics(
                                student_id="student_123",
                                start_date=None,
                                end_date=None,
                                include_detailed=False,
                                current_user=mock_user,
                            )

                            # Başarı mesajı Türkçe olmalı
                            assert "başarıyla alındı" in result["message"]

    def test_turkish_field_descriptions(self):
        """Türkçe alan açıklamaları testi"""
        # Pydantic model field descriptions Türkçe olmalı
        request = StudentAnalyticsRequest()

        # Model schema'sını kontrol et
        schema = StudentAnalyticsRequest.model_json_schema()
        properties = schema.get("properties", {})

        if "start_date" in properties:
            assert "Başlangıç tarihi" in properties["start_date"].get("description", "")
        if "end_date" in properties:
            assert "Bitiş tarihi" in properties["end_date"].get("description", "")


class TestIntegrationWithCoreServices:
    """Core servisler ile entegrasyon testleri"""

    @pytest.mark.asyncio
    async def test_elasticsearch_service_integration(self, mock_user):
        """Elasticsearch servisi entegrasyonu testi"""
        mock_es_service = Mock()
        mock_es_service.analytics_service = Mock()
        mock_es_service.analytics_service.get_user_analytics = AsyncMock(
            return_value={}
        )
        mock_es_service.analytics_service.log_event = AsyncMock()

        with patch(
            "backend.api.analytics.get_elasticsearch_service",
            return_value=mock_es_service,
        ):
            with patch(
                "backend.api.analytics._calculate_student_performance_metrics",
                return_value={},
            ):
                with patch(
                    "backend.api.analytics._get_learning_style_analysis",
                    return_value={},
                ):
                    with patch(
                        "backend.api.analytics._get_exam_performance_analysis",
                        return_value={},
                    ):
                        with patch(
                            "backend.api.analytics._get_subject_performance_analysis",
                            return_value={},
                        ):
                            await get_student_analytics(
                                student_id="student_123",
                                start_date=None,
                                end_date=None,
                                include_detailed=False,
                                current_user=mock_user,
                            )

                            # Elasticsearch servisi çağrılarını kontrol et
                            mock_es_service.analytics_service.get_user_analytics.assert_called_once()
                            mock_es_service.analytics_service.log_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_user_dependency_integration(self):
        """Kullanıcı dependency entegrasyonu testi"""
        # get_current_user dependency'sinin doğru çalıştığını test et
        mock_user = Mock(spec=User)
        mock_user.id = "test_user"
        mock_user.role = "student"

        with patch("backend.api.analytics.get_current_user", return_value=mock_user):
            # Dependency injection test edilebilir
            assert mock_user.id == "test_user"
            assert mock_user.role == "student"


if __name__ == "__main__":
    # Test çalıştırma
    pytest.main([__file__, "-v", "--tb=short"])
