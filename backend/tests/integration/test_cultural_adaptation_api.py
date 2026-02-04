"""
Kültürel Adaptasyon API Test Dosyası

Bu dosya, kültürel adaptasyon API endpoint'lerinin tüm fonksiyonlarını test eder.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

# Removed duplicate - using global test_client from conftest.py


@pytest.fixture
def mock_current_user():
    """Mock current user fixture"""
    return {"id": "test_user_123", "role": "student", "username": "test_student"}


@pytest.fixture
def mock_admin_user():
    """Mock admin user fixture"""
    return {"id": "admin_123", "role": "admin", "username": "test_admin"}


@pytest.fixture
def mock_teacher_user():
    """Mock teacher user fixture"""
    return {"id": "teacher_123", "role": "teacher", "username": "test_teacher"}


class TestCulturalAdaptationAPI:
    """Kültürel Adaptasyon API testleri"""

    def test_get_student_cultural_adaptation_success(
        self, test_client, mock_current_user
    ):
        """Başarılı öğrenci kültürel adaptasyon getirme testi"""
        student_id = "test_student_123"

        # Mock service response
        mock_adaptation_data = {
            "student_id": student_id,
            "cultural_adaptation": {
                "current_period": "normal",
                "adaptation_multiplier": 1.0,
                "recommended_study_hours": 4,
                "optimal_study_times": ["08:00-10:00", "19:00-21:00"],
                "content_difficulty_adjustment": 1.0,
                "social_learning_emphasis": 0.6,
                "individual_focus_emphasis": 0.4,
                "motivational_message_type": "balanced_motivation",
                "cultural_context_explanation": "Normal dönem açıklaması",
            },
            "context_analysis": {
                "cultural_analysis": {
                    "family_involvement_level": 0.8,
                    "study_preference_type": "group_oriented",
                    "authority_respect_level": 0.7,
                    "peer_interaction_style": {"competition_level": 0.6},
                    "identified_pattern": "traditional_family_oriented",
                }
            },
            "cultural_factors": {
                "family_pressure_level": 0.8,
                "social_environment_influence": 0.7,
            },
            "recommendations": {"study_schedule": {"daily_hours": 4}},
            "last_updated": datetime.now().isoformat(),
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
            return_value=mock_adaptation_data,
        ) as mock_service:
            response = test_client.get(
                f"/api/v1/cultural-adaptation/student/{student_id}"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["student_id"] == student_id
            assert "cultural_adaptation" in data["data"]
            assert "context_analysis" in data["data"]
            assert (
                "Kültürel adaptasyon bilgileri başarıyla getirildi" in data["message"]
            )

            mock_service.assert_called_once_with(
                student_id=student_id, force_refresh=False
            )

    def test_get_student_cultural_adaptation_with_force_refresh(
        self, test_client, mock_current_user
    ):
        """Force refresh ile kültürel adaptasyon getirme testi"""
        student_id = "test_student_123"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
            return_value={"student_id": student_id},
        ) as mock_service:
            response = test_client.get(
                f"/api/v1/cultural-adaptation/student/{student_id}?force_refresh=true"
            )

            assert response.status_code == 200
            mock_service.assert_called_once_with(
                student_id=student_id, force_refresh=True
            )

    def test_get_student_cultural_adaptation_unauthorized(self, test_client):
        """Yetkisiz erişim testi"""
        student_id = "other_student_123"
        unauthorized_user = {
            "id": "different_user_456",
            "role": "student",
            "username": "different_student",
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=unauthorized_user,
        ):
            response = test_client.get(
                f"/api/v1/cultural-adaptation/student/{student_id}"
            )

            assert response.status_code == 403
            data = response.json()
            assert "erişim yetkiniz yok" in data["detail"]

    def test_get_student_cultural_adaptation_admin_access(
        self, test_client, mock_admin_user
    ):
        """Admin kullanıcı erişim testi"""
        student_id = "any_student_123"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_admin_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
            return_value={"student_id": student_id},
        ) as mock_service:
            response = test_client.get(
                f"/api/v1/cultural-adaptation/student/{student_id}"
            )

            assert response.status_code == 200
            mock_service.assert_called_once()

    def test_get_student_cultural_adaptation_teacher_access(
        self, test_client, mock_teacher_user
    ):
        """Öğretmen kullanıcı erişim testi"""
        student_id = "student_in_class_123"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_teacher_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
            return_value={"student_id": student_id},
        ) as mock_service:
            response = test_client.get(
                f"/api/v1/cultural-adaptation/student/{student_id}"
            )

            assert response.status_code == 200
            mock_service.assert_called_once()

    def test_get_student_cultural_adaptation_not_found(
        self, test_client, mock_current_user
    ):
        """Öğrenci bulunamadı testi"""
        student_id = "nonexistent_student"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
            side_effect=ValueError("Öğrenci bulunamadı"),
        ):
            response = test_client.get(
                f"/api/v1/cultural-adaptation/student/{student_id}"
            )

            assert response.status_code == 404
            data = response.json()
            assert "Öğrenci bulunamadı" in data["detail"]

    def test_get_student_cultural_adaptation_server_error(
        self, test_client, mock_current_user
    ):
        """Sunucu hatası testi"""
        student_id = "test_student_123"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
            side_effect=Exception("Database connection error"),
        ):
            response = test_client.get(
                f"/api/v1/cultural-adaptation/student/{student_id}"
            )

            assert response.status_code == 500
            data = response.json()
            assert "bir hata oluştu" in data["detail"]

    def test_update_student_behavioral_data_success(
        self, test_client, mock_current_user
    ):
        """Başarılı davranış verisi güncelleme testi"""
        student_id = "test_student_123"
        update_data = {
            "group_study_sessions": 5,
            "parent_account_activity": 0.9,
            "study_time_preference": "morning",
        }

        mock_updated_data = {
            "student_id": student_id,
            "cultural_adaptation": {"updated": True},
            "last_updated": datetime.now().isoformat(),
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.update_cultural_context",
            return_value=mock_updated_data,
        ) as mock_service:
            response = test_client.put(
                f"/api/v1/cultural-adaptation/student/{student_id}/behavioral-update",
                json=update_data,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["student_id"] == student_id
            assert "güncellendi" in data["message"]

            mock_service.assert_called_once_with(
                student_id=student_id, behavioral_update=update_data
            )

    def test_update_student_behavioral_data_partial_update(
        self, test_client, mock_current_user
    ):
        """Kısmi davranış verisi güncelleme testi"""
        student_id = "test_student_123"
        update_data = {
            "group_study_sessions": 3,
            "parent_account_activity": None,  # None değerler filtrelenmeli
            "study_time_preference": "evening",
        }

        expected_filtered_data = {
            "group_study_sessions": 3,
            "study_time_preference": "evening",
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.update_cultural_context",
            return_value={"student_id": student_id},
        ) as mock_service:
            response = test_client.put(
                f"/api/v1/cultural-adaptation/student/{student_id}/behavioral-update",
                json=update_data,
            )

            assert response.status_code == 200
            mock_service.assert_called_once_with(
                student_id=student_id, behavioral_update=expected_filtered_data
            )

    def test_update_student_behavioral_data_empty_update(
        self, test_client, mock_current_user
    ):
        """Boş güncelleme verisi testi"""
        student_id = "test_student_123"
        update_data = {"group_study_sessions": None, "parent_account_activity": None}

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ):
            response = test_client.put(
                f"/api/v1/cultural-adaptation/student/{student_id}/behavioral-update",
                json=update_data,
            )

            assert response.status_code == 400
            data = response.json()
            assert "Güncellenecek davranış verisi bulunamadı" in data["detail"]

    def test_update_student_behavioral_data_unauthorized(self, test_client):
        """Yetkisiz davranış güncelleme testi"""
        student_id = "other_student_123"
        unauthorized_user = {"id": "different_user_456", "role": "student"}
        update_data = {"group_study_sessions": 5}

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=unauthorized_user,
        ):
            response = test_client.put(
                f"/api/v1/cultural-adaptation/student/{student_id}/behavioral-update",
                json=update_data,
            )

            assert response.status_code == 403
            data = response.json()
            assert "güncelleme yetkiniz yok" in data["detail"]

    def test_get_current_cultural_period_success(self, test_client, mock_current_user):
        """Başarılı kültürel dönem getirme testi"""
        mock_period_info = {
            "current_period": "normal",
            "period_name": "Normal Dönem",
            "period_description": "Normal çalışma programı uygulanacak.",
            "general_recommendations": ["Düzenli çalışma programınızı sürdürün"],
            "date_checked": datetime.now().isoformat(),
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_cultural_period_info",
            return_value=mock_period_info,
        ) as mock_service:
            response = test_client.get("/api/v1/cultural-adaptation/cultural-period")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["current_period"] == "normal"
            assert "başarıyla getirildi" in data["message"]

            mock_service.assert_called_once()

    def test_get_current_cultural_period_with_date(
        self, test_client, mock_current_user
    ):
        """Belirli tarih ile kültürel dönem getirme testi"""
        test_date = "2024-06-15"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_cultural_period_info",
            return_value={"current_period": "sinav_donemi"},
        ) as mock_service:
            response = test_client.get(
                f"/api/v1/cultural-adaptation/cultural-period?date={test_date}"
            )

            assert response.status_code == 200
            # Servis datetime objesi ile çağrılmalı
            mock_service.assert_called_once()
            call_args = mock_service.call_args[0]
            assert call_args[0].year == 2024
            assert call_args[0].month == 6
            assert call_args[0].day == 15

    def test_get_current_cultural_period_invalid_date(
        self, test_client, mock_current_user
    ):
        """Geçersiz tarih formatı testi"""
        invalid_date = "invalid-date-format"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ):
            response = test_client.get(
                f"/api/v1/cultural-adaptation/cultural-period?date={invalid_date}"
            )

            assert response.status_code == 400
            data = response.json()
            assert "Geçersiz tarih formatı" in data["detail"]

    def test_get_regional_culture_info_success(self, test_client, mock_current_user):
        """Başarılı bölgesel kültür bilgisi getirme testi"""
        region = "marmara"
        mock_regional_info = {
            "region": region,
            "cultural_factors": {
                "modernization_level": 0.9,
                "traditional_values": 0.6,
                "education_priority": 0.95,
                "family_pressure": 0.8,
            },
            "characteristics": "Modern yaşam tarzı, yüksek eğitim beklentisi",
            "education_approach": "Teknoloji destekli, bireysel başarı odaklı",
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ), patch(
            "backend.api.cultural_adaptation_api.cultural_service.get_regional_culture_info",
            return_value=mock_regional_info,
        ) as mock_service:
            response = test_client.get(
                f"/api/v1/cultural-adaptation/regional-culture/{region}"
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["region"] == region
            assert "cultural_factors" in data["data"]
            assert f"{region} bölgesi kültür bilgileri" in data["message"]

            mock_service.assert_called_once_with(region)

    def test_get_adaptation_summary_success(self, test_client, mock_current_user):
        """Kültürel adaptasyon özeti getirme testi"""
        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ):
            response = test_client.get("/api/v1/cultural-adaptation/adaptation-summary")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "system_info" in data["data"]
            assert "supported_periods" in data["data"]
            assert "supported_regions" in data["data"]
            assert "age_groups" in data["data"]
            assert "cultural_factors" in data["data"]
            assert "features" in data["data"]

            # System info kontrolü
            system_info = data["data"]["system_info"]
            assert system_info["name"] == "Türk Kültürü Adaptasyon Motoru"
            assert system_info["version"] == "1.0.0"

            # Desteklenen dönemler kontrolü
            periods = data["data"]["supported_periods"]
            assert len(periods) == 8
            assert any(p["key"] == "ramazan" for p in periods)
            assert any(p["key"] == "sinav_donemi" for p in periods)

            # Desteklenen bölgeler kontrolü
            regions = data["data"]["supported_regions"]
            assert len(regions) == 7
            assert any(r["key"] == "marmara" for r in regions)
            assert any(r["key"] == "dogu_anadolu" for r in regions)

    def test_test_cultural_adaptation_admin_only(self, test_client, mock_admin_user):
        """Kültürel adaptasyon testi - sadece admin testi"""
        test_data = {
            "student_id": "test_student_123",
            "age": 16,
            "region": "marmara",
            "cultural_factors": {"family_pressure": 0.8, "social_influence": 0.7},
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_admin_user,
        ):
            response = test_client.post(
                "/api/v1/cultural-adaptation/test-adaptation", json=test_data
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "test_student_id" in data["data"]
            assert "input_data" in data["data"]
            assert "adaptation_result" in data["data"]
            assert "test_timestamp" in data["data"]

            # Test sonucu kontrolü
            adaptation_result = data["data"]["adaptation_result"]
            assert "current_period" in adaptation_result
            assert "adaptation_multiplier" in adaptation_result
            assert "recommended_study_hours" in adaptation_result

    def test_test_cultural_adaptation_non_admin_forbidden(
        self, test_client, mock_current_user
    ):
        """Kültürel adaptasyon testi - admin olmayan kullanıcı testi"""
        test_data = {
            "student_id": "test_student_123",
            "age": 16,
            "region": "marmara",
            "cultural_factors": {},
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ):
            response = test_client.post(
                "/api/v1/cultural-adaptation/test-adaptation", json=test_data
            )

            assert response.status_code == 403
            data = response.json()
            assert "sadece admin kullanıcılar" in data["detail"]

    def test_test_cultural_adaptation_missing_fields(
        self, test_client, mock_admin_user
    ):
        """Kültürel adaptasyon testi - eksik alan testi"""
        incomplete_test_data = {
            "student_id": "test_student_123",
            "age": 16
            # region ve cultural_factors eksik
        }

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_admin_user,
        ):
            response = test_client.post(
                "/api/v1/cultural-adaptation/test-adaptation", json=incomplete_test_data
            )

            assert response.status_code == 400
            data = response.json()
            assert "Eksik test verileri" in data["detail"]
            assert "region" in data["detail"]
            assert "cultural_factors" in data["detail"]


@pytest.mark.integration
class TestCulturalAdaptationAPIIntegration:
    """API entegrasyon testleri"""

    def test_full_api_workflow(self, test_client, mock_current_user):
        """Tam API iş akışı testi"""
        student_id = "integration_test_student"

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ):
            # 1. Kültürel dönem bilgisi al
            period_response = test_client.get(
                "/api/v1/cultural-adaptation/cultural-period"
            )
            assert period_response.status_code == 200

            # 2. Bölgesel bilgi al
            region_response = test_client.get(
                "/api/v1/cultural-adaptation/regional-culture/marmara"
            )
            assert region_response.status_code == 200

            # 3. Sistem özeti al
            summary_response = test_client.get(
                "/api/v1/cultural-adaptation/adaptation-summary"
            )
            assert summary_response.status_code == 200

            # 4. Öğrenci adaptasyonu al (mock ile)
            with patch(
                "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
                return_value={"student_id": student_id},
            ):
                adaptation_response = test_client.get(
                    f"/api/v1/cultural-adaptation/student/{student_id}"
                )
                assert adaptation_response.status_code == 200

            # 5. Davranış güncelle (mock ile)
            update_data = {"group_study_sessions": 5}

            with patch(
                "backend.api.cultural_adaptation_api.cultural_service.update_cultural_context",
                return_value={"student_id": student_id},
            ):
                update_response = test_client.put(
                    f"/api/v1/cultural-adaptation/student/{student_id}/behavioral-update",
                    json=update_data,
                )
                assert update_response.status_code == 200

    def test_api_error_handling_consistency(self, test_client, mock_current_user):
        """API hata yönetimi tutarlılık testi"""

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ):
            # Tüm endpoint'lerde aynı hata formatı dönmeli
            error_responses = []

            # 1. Öğrenci bulunamadı hatası
            with patch(
                "backend.api.cultural_adaptation_api.cultural_service.get_student_cultural_adaptation",
                side_effect=ValueError("Test error"),
            ):
                response = test_client.get(
                    "/api/v1/cultural-adaptation/student/nonexistent"
                )
                error_responses.append(response)

            # 2. Sunucu hatası
            with patch(
                "backend.api.cultural_adaptation_api.cultural_service.get_cultural_period_info",
                side_effect=Exception("Server error"),
            ):
                response = test_client.get(
                    "/api/v1/cultural-adaptation/cultural-period"
                )
                error_responses.append(response)

            # 3. Bölgesel bilgi hatası
            with patch(
                "backend.api.cultural_adaptation_api.cultural_service.get_regional_culture_info",
                side_effect=Exception("Region error"),
            ):
                response = test_client.get(
                    "/api/v1/cultural-adaptation/regional-culture/invalid"
                )
                error_responses.append(response)

            # Tüm hata yanıtları aynı formatta olmalı
            for response in error_responses:
                assert response.status_code in [404, 500]
                data = response.json()
                assert "detail" in data
                assert isinstance(data["detail"], str)

    def test_api_response_format_consistency(self, test_client, mock_current_user):
        """API yanıt formatı tutarlılık testi"""

        with patch(
            "backend.api.cultural_adaptation_api.get_current_user",
            return_value=mock_current_user,
        ):
            # Başarılı yanıtlar aynı formatta olmalı
            success_responses = []

            # 1. Dönem bilgisi
            with patch(
                "backend.api.cultural_adaptation_api.cultural_service.get_cultural_period_info",
                return_value={"current_period": "normal"},
            ):
                response = test_client.get(
                    "/api/v1/cultural-adaptation/cultural-period"
                )
                success_responses.append(response)

            # 2. Bölgesel bilgi
            with patch(
                "backend.api.cultural_adaptation_api.cultural_service.get_regional_culture_info",
                return_value={"region": "test"},
            ):
                response = test_client.get(
                    "/api/v1/cultural-adaptation/regional-culture/marmara"
                )
                success_responses.append(response)

            # 3. Sistem özeti
            response = test_client.get("/api/v1/cultural-adaptation/adaptation-summary")
            success_responses.append(response)

            # Tüm başarılı yanıtlar aynı formatta olmalı
            for response in success_responses:
                assert response.status_code == 200
                data = response.json()
                assert "success" in data
                assert "data" in data
                assert "message" in data
                assert data["success"] is True
                assert isinstance(data["data"], dict)
                assert isinstance(data["message"], str)

    def test_api_authentication_consistency(self, test_client):
        """API kimlik doğrulama tutarlılık testi"""

        # Kimlik doğrulama olmadan erişim denemeleri
        endpoints_to_test = [
            "/api/v1/cultural-adaptation/student/test123",
            "/api/v1/cultural-adaptation/cultural-period",
            "/api/v1/cultural-adaptation/regional-culture/marmara",
            "/api/v1/cultural-adaptation/adaptation-summary",
        ]

        # get_current_user dependency'si mock'lanmadığında hata vermeli
        for endpoint in endpoints_to_test:
            response = test_client.get(endpoint)
            # Dependency injection hatası beklenir (gerçek uygulamada 401 olur)
            assert response.status_code in [401, 422, 500]  # Dependency hatası
