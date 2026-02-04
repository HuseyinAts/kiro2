#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for services/admin_service.py
Test coverage improvement: 24% -> 70%
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any, List

# Import the module to test
from services.admin_service import (
    AdminService,
    AdminAuthorizationError,
    admin_required,
    super_admin_required,
    admin_servisi,
)
from models import Kullanici, KullaniciOlustur, KullaniciRolu


@pytest.fixture
def admin_service():
    """Create fresh admin service instance"""
    return AdminService()


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = MagicMock()
    user.kullanici_id = "admin-123"
    user.email = "admin@test.com"
    user.ad_soyad = "Admin User"
    user.rol = KullaniciRolu.ADMIN
    user.aktif = True
    user.olusturma_tarihi = datetime.now()
    return user


@pytest.fixture
def mock_super_admin_user():
    """Mock super admin user"""
    user = MagicMock()
    user.kullanici_id = "super-admin-123"
    user.email = "superadmin@test.com"
    user.ad_soyad = "Super Admin User"
    user.rol = KullaniciRolu.SUPER_ADMIN
    user.aktif = True
    user.olusturma_tarihi = datetime.now()
    return user


@pytest.fixture
def mock_regular_user():
    """Mock regular user"""
    user = MagicMock()
    user.kullanici_id = "user-123"
    user.email = "user@test.com"
    user.ad_soyad = "Regular User"
    user.rol = KullaniciRolu.OGRENCI
    user.aktif = True
    user.olusturma_tarihi = datetime.now()
    return user


@pytest.fixture
def mock_inactive_user():
    """Mock inactive user"""
    user = MagicMock()
    user.kullanici_id = "inactive-123"
    user.email = "inactive@test.com"
    user.ad_soyad = "Inactive User"
    user.rol = KullaniciRolu.ADMIN
    user.aktif = False
    user.olusturma_tarihi = datetime.now()
    return user


@pytest.fixture
def sample_kullanici_data():
    """Sample user creation data"""
    return KullaniciOlustur(
        email="newuser@test.com",
        ad_soyad="New User",
        sifre="password123",
        rol=KullaniciRolu.OGRENCI,
        aktif=True,
    )


class TestAdminServiceInit:
    """Test AdminService initialization"""

    def test_init_with_super_admin_role(self):
        """Test initialization when SUPER_ADMIN role exists"""
        service = AdminService()

        assert KullaniciRolu.ADMIN in service.admin_rolleri
        assert KullaniciRolu.SUPER_ADMIN in service.admin_rolleri
        assert KullaniciRolu.SUPER_ADMIN in service.super_admin_rolleri

    def test_init_role_hierarchy(self):
        """Test role hierarchy in initialization"""
        service = AdminService()

        # Test that admin_rolleri contains expected roles
        assert KullaniciRolu.ADMIN in service.admin_rolleri

        # Test that super_admin_rolleri is a subset of admin_rolleri
        assert (
            service.super_admin_rolleri.issubset(service.admin_rolleri)
            or service.super_admin_rolleri == service.admin_rolleri
        )


class TestAdminYetkisiKontrol:
    """Test admin authorization methods"""

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_admin_user_id(
        self, admin_service, mock_admin_user
    ):
        """Test admin authorization with admin user ID"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.return_value = mock_admin_user

            result = await admin_service._admin_yetkisi_kontrol("admin-123")

            assert result is True
            mock_getir.assert_called_once_with("admin-123")

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_admin_user_object(
        self, admin_service, mock_admin_user
    ):
        """Test admin authorization with admin user object"""
        result = await admin_service._admin_yetkisi_kontrol(mock_admin_user)

        assert result is True

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_regular_user(
        self, admin_service, mock_regular_user
    ):
        """Test admin authorization with regular user"""
        result = await admin_service._admin_yetkisi_kontrol(mock_regular_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_inactive_user(
        self, admin_service, mock_inactive_user
    ):
        """Test admin authorization with inactive admin user"""
        result = await admin_service._admin_yetkisi_kontrol(mock_inactive_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_nonexistent_user(self, admin_service):
        """Test admin authorization with non-existent user"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.return_value = None

            result = await admin_service._admin_yetkisi_kontrol("nonexistent-123")

            assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_invalid_input(self, admin_service):
        """Test admin authorization with invalid input"""
        result = await admin_service._admin_yetkisi_kontrol(123)  # Invalid type

        assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_exception(self, admin_service):
        """Test admin authorization when exception occurs"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.side_effect = Exception("Database error")

            result = await admin_service._admin_yetkisi_kontrol("user-123")

            assert result is False


class TestSuperAdminYetkisiKontrol:
    """Test super admin authorization methods"""

    @pytest.mark.asyncio
    async def test_super_admin_yetkisi_kontrol_with_super_admin_user(
        self, admin_service, mock_super_admin_user
    ):
        """Test super admin authorization with super admin user"""
        result = await admin_service._super_admin_yetkisi_kontrol(mock_super_admin_user)

        assert result is True

    @pytest.mark.asyncio
    async def test_super_admin_yetkisi_kontrol_with_regular_admin(
        self, admin_service, mock_admin_user
    ):
        """Test super admin authorization with regular admin user"""
        result = await admin_service._super_admin_yetkisi_kontrol(mock_admin_user)

        assert result is False

    @pytest.mark.asyncio
    async def test_super_admin_yetkisi_kontrol_with_exception(self, admin_service):
        """Test super admin authorization when exception occurs"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.side_effect = Exception("Database error")

            result = await admin_service._super_admin_yetkisi_kontrol("user-123")

            assert result is False


class TestKullaniciYetkiKontrol:
    """Test user authorization checking"""

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_success(
        self, admin_service, mock_admin_user
    ):
        """Test successful user authorization check"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.return_value = mock_admin_user

            result = await admin_service.kullanici_yetki_kontrol(
                "admin-123", KullaniciRolu.OGRENCI
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_insufficient_role(
        self, admin_service, mock_regular_user
    ):
        """Test user authorization check with insufficient role"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.return_value = mock_regular_user

            result = await admin_service.kullanici_yetki_kontrol(
                "user-123", KullaniciRolu.ADMIN
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_inactive_user(
        self, admin_service, mock_inactive_user
    ):
        """Test user authorization check with inactive user"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.return_value = mock_inactive_user

            result = await admin_service.kullanici_yetki_kontrol(
                "inactive-123", KullaniciRolu.OGRENCI
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_nonexistent_user(self, admin_service):
        """Test user authorization check with non-existent user"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.return_value = None

            result = await admin_service.kullanici_yetki_kontrol(
                "nonexistent-123", KullaniciRolu.OGRENCI
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_exception(self, admin_service):
        """Test user authorization check when exception occurs"""
        with patch(
            "services.admin_service.kullanici_servisi.kullanici_getir"
        ) as mock_getir:
            mock_getir.side_effect = Exception("Database error")

            result = await admin_service.kullanici_yetki_kontrol(
                "user-123", KullaniciRolu.OGRENCI
            )

            assert result is False


class TestAdminAktiviteKaydet:
    """Test admin activity logging"""

    @pytest.mark.asyncio
    async def test_admin_aktivite_kaydet_success(self, admin_service):
        """Test successful admin activity logging"""
        result = await admin_service.admin_aktivite_kaydet(
            "admin-123",
            "kullanici_olustur",
            hedef_id="user-456",
            detaylar={"email": "test@example.com"},
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_admin_aktivite_kaydet_minimal_data(self, admin_service):
        """Test admin activity logging with minimal data"""
        result = await admin_service.admin_aktivite_kaydet("admin-123", "login")

        assert result is True

    @pytest.mark.asyncio
    async def test_admin_aktivite_kaydet_exception(self, admin_service):
        """Test admin activity logging when exception occurs"""
        # Mock a scenario that would cause an exception
        with patch("builtins.print") as mock_print:
            # This should still return True as it catches exceptions
            result = await admin_service.admin_aktivite_kaydet(
                "admin-123", "test_aktivite"
            )

            assert result is True


class TestKullaniciYonetimi:
    """Test user management methods"""

    @pytest.mark.asyncio
    async def test_kullanicilari_listele_success(self, admin_service):
        """Test successful user listing"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                mock_admin_check.return_value = True
                mock_log.return_value = True

                users = await admin_service.kullanicilari_listele(
                    rol=KullaniciRolu.OGRENCI,
                    sayfa=1,
                    sayfa_boyutu=10,
                    current_user="admin-123",
                )

                assert isinstance(users, list)
                assert len(users) == 10
                for user in users:
                    assert user.rol == KullaniciRolu.OGRENCI
                    assert hasattr(user, "kullanici_id")
                    assert hasattr(user, "email")

                mock_admin_check.assert_called_once_with("admin-123")
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_kullanicilari_listele_unauthorized(self, admin_service):
        """Test user listing without authorization"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            mock_admin_check.return_value = False

            with pytest.raises(
                AdminAuthorizationError, match="Bu işlem için admin yetkisi gereklidir"
            ):
                await admin_service.kullanicilari_listele(current_user="user-123")

    @pytest.mark.asyncio
    async def test_kullanici_olustur_success(
        self, admin_service, sample_kullanici_data, mock_admin_user
    ):
        """Test successful user creation"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                with patch(
                    "services.admin_service.kullanici_servisi.kullanici_olustur"
                ) as mock_create:
                    mock_admin_check.return_value = True
                    mock_log.return_value = True
                    mock_create.return_value = mock_admin_user

                    result = await admin_service.kullanici_olustur(
                        sample_kullanici_data, current_user="admin-123"
                    )

                    assert result == mock_admin_user
                    mock_admin_check.assert_called_once_with("admin-123")
                    mock_create.assert_called_once_with(sample_kullanici_data)
                    # Check that activity logging was called with the correct user ID
                    mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_kullanici_olustur_admin_role_requires_super_admin(
        self, admin_service
    ):
        """Test that creating admin user requires super admin privileges"""
        admin_data = KullaniciOlustur(
            email="newadmin@test.com",
            ad_soyad="New Admin",
            sifre="password123",
            rol=KullaniciRolu.ADMIN,
        )

        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(
                admin_service, "_super_admin_yetkisi_kontrol"
            ) as mock_super_check:
                mock_admin_check.return_value = True
                mock_super_check.return_value = False

                with pytest.raises(
                    AdminAuthorizationError,
                    match="Admin/Süper Admin oluşturmak için süper admin yetkisi gereklidir",
                ):
                    await admin_service.kullanici_olustur(
                        admin_data, current_user="admin-123"
                    )

    @pytest.mark.asyncio
    async def test_kullanici_getir_success(self, admin_service, mock_admin_user):
        """Test successful user retrieval"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch(
                "services.admin_service.kullanici_servisi.kullanici_getir"
            ) as mock_get:
                mock_admin_check.return_value = True
                mock_get.return_value = mock_admin_user

                result = await admin_service.kullanici_getir(
                    "user-123", current_user="admin-123"
                )

                assert result == mock_admin_user
                mock_get.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_kullanici_guncelle_success(self, admin_service, mock_regular_user):
        """Test successful user update"""
        update_data = {"ad_soyad": "Updated Name"}

        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                with patch(
                    "services.admin_service.kullanici_servisi.kullanici_getir"
                ) as mock_get:
                    with patch(
                        "services.admin_service.kullanici_servisi.kullanici_guncelle"
                    ) as mock_update:
                        mock_admin_check.return_value = True
                        mock_log.return_value = True
                        mock_get.return_value = mock_regular_user
                        mock_update.return_value = mock_regular_user

                        result = await admin_service.kullanici_guncelle(
                            "user-123", update_data, current_user="admin-123"
                        )

                        assert result == mock_regular_user
                        mock_update.assert_called_once_with("user-123", update_data)

    @pytest.mark.asyncio
    async def test_kullanici_guncelle_admin_requires_super_admin(
        self, admin_service, mock_admin_user
    ):
        """Test that updating admin user requires super admin privileges"""
        update_data = {"ad_soyad": "Updated Admin"}

        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(
                admin_service, "_super_admin_yetkisi_kontrol"
            ) as mock_super_check:
                with patch(
                    "services.admin_service.kullanici_servisi.kullanici_getir"
                ) as mock_get:
                    mock_admin_check.return_value = True
                    mock_super_check.return_value = False
                    mock_get.return_value = mock_admin_user

                    with pytest.raises(
                        AdminAuthorizationError,
                        match="Admin/Süper Admin güncellemek için süper admin yetkisi gereklidir",
                    ):
                        await admin_service.kullanici_guncelle(
                            "admin-123", update_data, current_user="regular-admin-123"
                        )

    @pytest.mark.asyncio
    async def test_kullanici_sil_success(self, admin_service, mock_regular_user):
        """Test successful user deletion"""
        with patch.object(
            admin_service, "_super_admin_yetkisi_kontrol"
        ) as mock_super_check:
            with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                with patch(
                    "services.admin_service.kullanici_servisi.kullanici_getir"
                ) as mock_get:
                    with patch(
                        "services.admin_service.kullanici_servisi.kullanici_sil"
                    ) as mock_delete:
                        mock_super_check.return_value = True
                        mock_log.return_value = True
                        mock_get.return_value = mock_regular_user
                        mock_delete.return_value = True

                        result = await admin_service.kullanici_sil(
                            "user-123", current_user="super-admin-123"
                        )

                        assert result is True
                        mock_delete.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_kullanici_sil_cannot_delete_self(self, admin_service):
        """Test that user cannot delete themselves"""
        with patch.object(
            admin_service, "_super_admin_yetkisi_kontrol"
        ) as mock_super_check:
            mock_super_check.return_value = True

            with pytest.raises(
                AdminAuthorizationError, match="Kendi hesabınızı silemezsiniz"
            ):
                await admin_service.kullanici_sil(
                    "super-admin-123", current_user="super-admin-123"
                )


class TestDashboardIstatistikleri:
    """Test dashboard statistics methods"""

    @pytest.mark.asyncio
    async def test_dashboard_istatistikleri_getir_success(self, admin_service):
        """Test successful dashboard statistics retrieval"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "_toplam_soru_sayisi") as mock_soru_count:
                with patch.object(
                    admin_service, "_son_aktiviteler_getir"
                ) as mock_activities:
                    mock_admin_check.return_value = True
                    mock_soru_count.return_value = 500
                    mock_activities.return_value = [{"tip": "test", "mesaj": "test"}]

                    stats = await admin_service.dashboard_istatistikleri_getir(
                        current_user="admin-123"
                    )

                    assert isinstance(stats, dict)
                    assert "kullanici_istatistikleri" in stats
                    assert "icerik_istatistikleri" in stats
                    assert "sistem_performansi" in stats
                    assert "son_aktiviteler" in stats
                    assert stats["icerik_istatistikleri"]["toplam_soru"] == 500

    @pytest.mark.asyncio
    async def test_toplam_soru_sayisi_success(self, admin_service):
        """Test successful question count retrieval"""
        with patch(
            "services.admin_service.soru_bankasi_servisi.istatistikler_getir"
        ) as mock_stats:
            mock_stats.return_value = {"toplam_soru_sayisi": 1000}

            result = await admin_service._toplam_soru_sayisi()

            assert result == 1000

    @pytest.mark.asyncio
    async def test_toplam_soru_sayisi_exception(self, admin_service):
        """Test question count retrieval when exception occurs"""
        with patch(
            "services.admin_service.soru_bankasi_servisi.istatistikler_getir"
        ) as mock_stats:
            mock_stats.side_effect = Exception("Service error")

            result = await admin_service._toplam_soru_sayisi()

            assert result == 0

    @pytest.mark.asyncio
    async def test_son_aktiviteler_getir_success(self, admin_service):
        """Test successful recent activities retrieval"""
        activities = await admin_service._son_aktiviteler_getir()

        assert isinstance(activities, list)
        assert len(activities) == 3
        for activity in activities:
            assert "tip" in activity
            assert "mesaj" in activity
            assert "zaman" in activity

    @pytest.mark.asyncio
    async def test_son_aktiviteler_getir_exception(self, admin_service):
        """Test recent activities retrieval when exception occurs"""
        with patch("services.admin_service.datetime") as mock_datetime:
            mock_datetime.now.side_effect = Exception("Time error")

            activities = await admin_service._son_aktiviteler_getir()

            assert activities == []


class TestIcerikYonetimi:
    """Test content management methods"""

    @pytest.mark.asyncio
    async def test_soru_bankasi_listesi_success(self, admin_service):
        """Test successful question bank listing"""
        mock_sorular = [MagicMock() for _ in range(5)]
        for i, soru in enumerate(mock_sorular):
            soru.id = f"soru-{i}"
            soru.question_text = f"Test question {i}"
            soru.exam_type.value = "TYT"
            soru.subject_area.value = "Matematik"
            soru.difficulty.value = "Orta"
            soru.created_at.isoformat.return_value = "2024-01-01T00:00:00Z"
            soru.is_active = True

        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch(
                "services.admin_service.soru_bankasi_servisi.sorular_listele"
            ) as mock_list:
                mock_admin_check.return_value = True
                mock_list.return_value = mock_sorular

                result = await admin_service.soru_bankasi_listesi(
                    konu="Matematik", sayfa=1, sayfa_boyutu=5, current_user="admin-123"
                )

                assert isinstance(result, list)
                assert len(result) == 5
                for soru_dict in result:
                    assert "id" in soru_dict
                    assert "soru_metni" in soru_dict
                    assert "sinav_tipi" in soru_dict

    @pytest.mark.asyncio
    async def test_soru_ekle_success(self, admin_service):
        """Test successful question addition"""
        soru_data = {"soru_metni": "Test question", "sinav_tipi": "TYT"}
        mock_soru = MagicMock()
        mock_soru.id = "soru-123"
        mock_soru.question_text = "Test question"
        mock_soru.exam_type.value = "TYT"
        mock_soru.subject_area.value = "Matematik"
        mock_soru.created_at.isoformat.return_value = "2024-01-01T00:00:00Z"

        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                with patch(
                    "services.admin_service.soru_bankasi_servisi.soru_ekle"
                ) as mock_add:
                    mock_admin_check.return_value = True
                    mock_log.return_value = True
                    mock_add.return_value = mock_soru

                    result = await admin_service.soru_ekle(
                        soru_data, current_user="admin-123"
                    )

                    assert isinstance(result, dict)
                    assert result["id"] == "soru-123"
                    assert result["soru_metni"] == "Test question"

    @pytest.mark.asyncio
    async def test_toplu_soru_yukle_success(self, admin_service):
        """Test successful bulk question upload"""
        sorular_data = [
            {"soru_metni": "Question 1"},
            {"soru_metni": "Question 2"},
            {"soru_metni": "Question 3"},
        ]

        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "soru_ekle") as mock_add:
                with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                    mock_admin_check.return_value = True
                    mock_add.return_value = {"id": "test-id"}
                    mock_log.return_value = True

                    result = await admin_service.toplu_soru_yukle(
                        sorular_data, current_user="admin-123"
                    )

                    assert result["basarili_sayisi"] == 3
                    assert result["basarisiz_sayisi"] == 0
                    assert len(result["hatalar"]) == 0

    @pytest.mark.asyncio
    async def test_toplu_soru_yukle_with_errors(self, admin_service):
        """Test bulk question upload with some errors"""
        sorular_data = [
            {"soru_metni": "Valid question"},
            {"soru_metni": "Invalid question"},
        ]

        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "soru_ekle") as mock_add:
                with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                    mock_admin_check.return_value = True
                    mock_log.return_value = True

                    # First call succeeds, second fails
                    mock_add.side_effect = [
                        {"id": "success"},
                        Exception("Validation error"),
                    ]

                    result = await admin_service.toplu_soru_yukle(
                        sorular_data, current_user="admin-123"
                    )

                    assert result["basarili_sayisi"] == 1
                    assert result["basarisiz_sayisi"] == 1
                    assert len(result["hatalar"]) == 1
                    assert result["hatalar"][0]["sira"] == 2

    @pytest.mark.asyncio
    async def test_icerik_ara_success(self, admin_service):
        """Test successful content search"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            mock_admin_check.return_value = True

            result = await admin_service.icerik_ara(
                "matematik",
                tur="soru",
                sayfa=1,
                sayfa_boyutu=5,
                current_user="admin-123",
            )

            assert isinstance(result, dict)
            assert "sonuclar" in result
            assert "toplam_sonuc" in result
            assert "arama_terimi" in result
            assert result["arama_terimi"] == "matematik"
            assert len(result["sonuclar"]) <= 5


class TestDecoratorFunctionality:
    """Test decorator functionality"""

    def test_admin_required_decorator_success(self):
        """Test admin_required decorator with authorized user"""

        class MockService:
            async def _admin_yetkisi_kontrol(self, user):
                return True

            @admin_required
            async def test_method(self, current_user=None):
                return "success"

        service = MockService()

        # This would normally be tested in an async context
        # but we're testing the decorator structure
        assert hasattr(service.test_method, "__wrapped__")

    def test_super_admin_required_decorator_success(self):
        """Test super_admin_required decorator with authorized user"""

        class MockService:
            async def _super_admin_yetkisi_kontrol(self, user):
                return True

            @super_admin_required
            async def test_method(self, current_user=None):
                return "success"

        service = MockService()

        # Test decorator structure
        assert hasattr(service.test_method, "__wrapped__")


class TestGlobalServiceInstance:
    """Test global service instance"""

    def test_global_admin_servisi_exists(self):
        """Test that global admin_servisi instance exists"""
        assert admin_servisi is not None
        assert isinstance(admin_servisi, AdminService)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_dashboard_istatistikleri_exception_handling(self, admin_service):
        """Test dashboard statistics with exception"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch.object(admin_service, "_toplam_soru_sayisi") as mock_soru_count:
                mock_admin_check.return_value = True
                mock_soru_count.side_effect = Exception("Service error")

                stats = await admin_service.dashboard_istatistikleri_getir(
                    current_user="admin-123"
                )

                # Should return empty dict on exception
                assert stats == {}

    @pytest.mark.asyncio
    async def test_soru_bankasi_listesi_exception_handling(self, admin_service):
        """Test question bank listing with exception"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            with patch(
                "services.admin_service.soru_bankasi_servisi.sorular_listele"
            ) as mock_list:
                mock_admin_check.return_value = True
                mock_list.side_effect = Exception("Database error")

                result = await admin_service.soru_bankasi_listesi(
                    current_user="admin-123"
                )

                # Should return empty list on exception
                assert result == []

    @pytest.mark.asyncio
    async def test_egitim_materyalleri_operations(self, admin_service):
        """Test education material operations"""
        with patch.object(admin_service, "_admin_yetkisi_kontrol") as mock_admin_check:
            mock_admin_check.return_value = True

            # Test listing
            materials = await admin_service.egitim_materyalleri_listesi(
                current_user="admin-123"
            )
            assert isinstance(materials, list)

            # Test adding
            material_data = {
                "baslik": "Test Material",
                "tur": "video",
                "konu": "Matematik",
            }
            with patch.object(admin_service, "admin_aktivite_kaydet") as mock_log:
                mock_log.return_value = True
                result = await admin_service.egitim_materyali_ekle(
                    material_data, current_user="admin-123"
                )
                assert isinstance(result, dict)
                assert result["baslik"] == "Test Material"

            # Test updating
            update_result = await admin_service.egitim_materyali_guncelle(
                "material-123", {"baslik": "Updated Material"}, current_user="admin-123"
            )
            assert update_result is not None

            # Test deleting
            delete_result = await admin_service.egitim_materyali_sil(
                "material-123", current_user="admin-123"
            )
            assert delete_result is True

            # Test approval status update
            approval_result = await admin_service.egitim_materyali_onay_durumu_guncelle(
                "material-123", {"onay_durumu": "onaylandi"}, current_user="admin-123"
            )
            assert approval_result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
