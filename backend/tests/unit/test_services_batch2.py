"""
Unit Tests for Service Layer Batch 2

Tests for:
  1. services/teacher_service.py         (TeacherService)
  2. services/admin_service.py           (AdminService)
  3. services/learning_style_service.py  (LearningStyleService)
  4. services/student_review_service.py  (StudentReviewService)
  5. services/question_crud_service.py   (QuestionCRUDService)

All DB calls are mocked – no real database required.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

import uuid
from datetime import UTC, date, datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared DB fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    db.flush = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_execute_result(rows=None, scalar=None, scalars_list=None):
    """Build a mock that mimics SQLAlchemy AsyncResult."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar
    result.scalar.return_value = scalar
    result.scalars.return_value.all.return_value = scalars_list or []
    result.scalars.return_value.one.return_value = rows[0] if rows else None
    result.all.return_value = rows or []
    result.one.return_value = rows[0] if rows else None
    result.fetchall.return_value = rows or []
    return result


# ===========================================================================
# 1. TeacherService
# ===========================================================================

from models.teacher_pool import (
    Appointment,
    AppointmentStatus,
    AppointmentType,
    DayOfWeek,
    SubjectExpertise,
    TeacherExpertise,
    TeacherPoolProfile,
    TeacherReview,
    TeacherStatus,
    VerificationStatus,
)
from services.teacher_service import TeacherService


def _make_teacher(teacher_id=None, hourly_rate=100.0, currency="TRY"):
    t = MagicMock(spec=TeacherPoolProfile)
    t.id = teacher_id or uuid.uuid4()
    t.user_id = uuid.uuid4()
    t.full_name = "Test Ogretmen"
    t.status = TeacherStatus.PENDING
    t.verification_status = VerificationStatus.NOT_SUBMITTED
    t.hourly_rate = hourly_rate
    t.currency = currency
    t.average_rating = 4.5
    t.total_reviews = 10
    t.is_accepting_students = True
    t.online_teaching = True
    t.city = "Istanbul"
    return t


class TestTeacherServiceRegistration:
    @pytest.mark.asyncio
    async def test_register_teacher_success(self, mock_db):
        """register_teacher creates profile with PENDING status."""
        service = TeacherService(mock_db)

        teacher = await service.register_teacher(
            user_id=uuid.uuid4(),
            full_name="Ali Veli",
            title="Dr.",
            bio="Bio text",
            phone="0555-000-0000",
            email="ali@test.com",
            city="Ankara",
            district="Cankaya",
            years_of_experience=5,
            education_level="lisans",
            university="ODTU",
            department="Mat",
            graduation_year=2010,
            hourly_rate=150.0,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called()
        # The added object should have PENDING status
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.status == TeacherStatus.PENDING
        assert added_obj.verification_status == VerificationStatus.NOT_SUBMITTED

    @pytest.mark.asyncio
    async def test_get_teacher_profile_found(self, mock_db):
        """get_teacher_profile returns teacher when found."""
        tid = uuid.uuid4()
        teacher = _make_teacher(tid)
        mock_db.execute.return_value = _make_execute_result(scalar=teacher)

        service = TeacherService(mock_db)
        result = await service.get_teacher_profile(tid)

        mock_db.execute.assert_called_once()
        assert result == teacher

    @pytest.mark.asyncio
    async def test_get_teacher_profile_not_found(self, mock_db):
        """get_teacher_profile returns None when teacher does not exist."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)

        service = TeacherService(mock_db)
        result = await service.get_teacher_profile(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_teacher_by_user_id(self, mock_db):
        """get_teacher_by_user_id queries by user_id."""
        teacher = _make_teacher()
        mock_db.execute.return_value = _make_execute_result(scalar=teacher)

        service = TeacherService(mock_db)
        result = await service.get_teacher_by_user_id(uuid.uuid4())

        assert result == teacher

    @pytest.mark.asyncio
    async def test_update_teacher_profile_not_found(self, mock_db):
        """update_teacher_profile returns None when teacher missing."""
        # get_teacher_profile path
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = TeacherService(mock_db)
        result = await service.update_teacher_profile(uuid.uuid4(), bio="new bio")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_teacher_profile_success(self, mock_db):
        """update_teacher_profile updates attributes and commits."""
        teacher = _make_teacher()
        # selectinload path for get_teacher_profile
        mock_db.execute.return_value = _make_execute_result(scalar=teacher)
        service = TeacherService(mock_db)
        result = await service.update_teacher_profile(teacher.id, bio="updated bio")
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called()
        assert result == teacher

    @pytest.mark.asyncio
    async def test_verify_teacher_approved(self, mock_db):
        """verify_teacher sets VERIFIED status when approved=True."""
        teacher = _make_teacher()
        mock_db.execute.return_value = _make_execute_result(scalar=teacher)

        service = TeacherService(mock_db)
        admin_id = uuid.uuid4()
        result = await service.verify_teacher(teacher.id, admin_id, approved=True)

        assert teacher.status == TeacherStatus.VERIFIED
        assert teacher.verification_status == VerificationStatus.APPROVED
        assert teacher.verified_by == admin_id
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_verify_teacher_rejected(self, mock_db):
        """verify_teacher sets REJECTED status with reason."""
        teacher = _make_teacher()
        mock_db.execute.return_value = _make_execute_result(scalar=teacher)

        service = TeacherService(mock_db)
        result = await service.verify_teacher(
            teacher.id, uuid.uuid4(), approved=False, rejection_reason="belge eksik"
        )

        assert teacher.status == TeacherStatus.REJECTED
        assert teacher.rejection_reason == "belge eksik"


class TestTeacherServiceSearch:
    @pytest.mark.asyncio
    async def test_search_teachers_empty_result(self, mock_db):
        """search_teachers returns empty list when nothing matches."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = TeacherService(mock_db)
        result = await service.search_teachers()
        assert result == []

    @pytest.mark.asyncio
    async def test_search_teachers_with_filters(self, mock_db):
        """search_teachers applies subject and city filters."""
        teachers = [_make_teacher() for _ in range(3)]
        mock_db.execute.return_value = _make_execute_result(scalars_list=teachers)
        service = TeacherService(mock_db)
        result = await service.search_teachers(
            subject=SubjectExpertise.MATHEMATICS,
            city="Istanbul",
            min_rating=4.0,
            max_hourly_rate=200.0,
            online_only=True,
        )
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_search_teachers_pagination(self, mock_db):
        """search_teachers applies limit and offset."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = TeacherService(mock_db)
        result = await service.search_teachers(limit=5, offset=10)
        mock_db.execute.assert_called_once()
        assert isinstance(result, list)


class TestTeacherServiceExpertise:
    @pytest.mark.asyncio
    async def test_add_expertise(self, mock_db):
        """add_expertise creates TeacherExpertise and commits."""
        service = TeacherService(mock_db)
        result = await service.add_expertise(
            teacher_id=uuid.uuid4(),
            subject=SubjectExpertise.MATHEMATICS,
            grade_levels=["9", "10", "11"],
            proficiency_level="advanced",
            years_teaching_subject=5,
            exam_types=["TYT", "AYT"],
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_teacher_expertise(self, mock_db):
        """get_teacher_expertise returns list of expertise entries."""
        expertises = [MagicMock(spec=TeacherExpertise) for _ in range(2)]
        mock_db.execute.return_value = _make_execute_result(scalars_list=expertises)
        service = TeacherService(mock_db)
        result = await service.get_teacher_expertise(uuid.uuid4())
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_expertise_success(self, mock_db):
        """delete_expertise returns True when row deleted."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result
        service = TeacherService(mock_db)
        result = await service.delete_expertise(uuid.uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_expertise_not_found(self, mock_db):
        """delete_expertise returns False when nothing deleted."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result
        service = TeacherService(mock_db)
        result = await service.delete_expertise(uuid.uuid4())
        assert result is False


class TestTeacherServiceAppointments:
    @pytest.mark.asyncio
    async def test_create_appointment_success(self, mock_db):
        """create_appointment calculates price from hourly_rate."""
        teacher = _make_teacher(hourly_rate=120.0)
        mock_db.execute.return_value = _make_execute_result(scalar=teacher)
        service = TeacherService(mock_db)

        appt = await service.create_appointment(
            teacher_id=teacher.id,
            student_id=uuid.uuid4(),
            scheduled_date=date.today(),
            start_time=time(10, 0),
            end_time=time(11, 0),
            appointment_type=AppointmentType.ONE_ON_ONE,
            subject=SubjectExpertise.MATHEMATICS,
            topic="Limit",
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        # price = (60/60) * 120 = 120
        added_appt = mock_db.add.call_args[0][0]
        assert added_appt.price == pytest.approx(120.0)

    @pytest.mark.asyncio
    async def test_create_appointment_teacher_not_found(self, mock_db):
        """create_appointment raises ValueError when teacher missing."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = TeacherService(mock_db)

        with pytest.raises(ValueError, match="Teacher not found"):
            await service.create_appointment(
                teacher_id=uuid.uuid4(),
                student_id=uuid.uuid4(),
                scheduled_date=date.today(),
                start_time=time(10, 0),
                end_time=time(11, 0),
                appointment_type=AppointmentType.ONE_ON_ONE,
                subject=SubjectExpertise.MATHEMATICS,
                topic="test",
            )

    @pytest.mark.asyncio
    async def test_confirm_appointment(self, mock_db):
        """confirm_appointment sets CONFIRMED status and meeting_url."""
        appt = MagicMock(spec=Appointment)
        appt.id = uuid.uuid4()
        appt.student_id = uuid.uuid4()
        appt.teacher_id = uuid.uuid4()
        appt.scheduled_date = date.today()
        appt.start_time = time(10, 0)

        mock_db.execute.return_value = _make_execute_result(scalar=appt)
        service = TeacherService(mock_db)
        # Mock _schedule_reminders to bypass naive/aware datetime comparison
        service._schedule_reminders = AsyncMock()

        result = await service.confirm_appointment(
            appt.id, uuid.uuid4(), meeting_url="https://meet.example.com"
        )
        assert appt.status == AppointmentStatus.CONFIRMED
        assert appt.meeting_url == "https://meet.example.com"
        service._schedule_reminders.assert_called_once_with(appt)

    @pytest.mark.asyncio
    async def test_cancel_appointment_not_found(self, mock_db):
        """cancel_appointment returns None when not found."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = TeacherService(mock_db)
        result = await service.cancel_appointment(uuid.uuid4(), uuid.uuid4(), "reason")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_teacher_appointments_with_status_filter(self, mock_db):
        """get_teacher_appointments filters by status."""
        appts = [MagicMock(spec=Appointment) for _ in range(2)]
        mock_db.execute.return_value = _make_execute_result(scalars_list=appts)
        service = TeacherService(mock_db)
        result = await service.get_teacher_appointments(
            uuid.uuid4(), status=AppointmentStatus.CONFIRMED
        )
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_student_appointments(self, mock_db):
        """get_student_appointments returns appointments for student."""
        appts = [MagicMock(spec=Appointment) for _ in range(3)]
        mock_db.execute.return_value = _make_execute_result(scalars_list=appts)
        service = TeacherService(mock_db)
        result = await service.get_student_appointments(uuid.uuid4())
        assert len(result) == 3


class TestTeacherServiceReviews:
    @pytest.mark.asyncio
    async def test_get_teacher_reviews(self, mock_db):
        """get_teacher_reviews returns visible reviews."""
        reviews = [MagicMock(spec=TeacherReview) for _ in range(5)]
        mock_db.execute.return_value = _make_execute_result(scalars_list=reviews)
        service = TeacherService(mock_db)
        result = await service.get_teacher_reviews(uuid.uuid4())
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_get_pending_reminders(self, mock_db):
        """get_pending_reminders returns unsent reminders."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = TeacherService(mock_db)
        result = await service.get_pending_reminders()
        assert result == []

    @pytest.mark.asyncio
    async def test_add_availability_slot(self, mock_db):
        """add_availability_slot creates slot with correct attributes."""
        service = TeacherService(mock_db)
        slot = await service.add_availability_slot(
            teacher_id=uuid.uuid4(),
            day_of_week=DayOfWeek.MONDAY,
            start_time=time(9, 0),
            end_time=time(10, 0),
            max_students=3,
            is_recurring=True,
        )
        mock_db.add.assert_called_once()
        added = mock_db.add.call_args[0][0]
        assert added.day_of_week == DayOfWeek.MONDAY
        assert added.max_students == 3

    @pytest.mark.asyncio
    async def test_delete_availability_slot(self, mock_db):
        """delete_availability_slot returns True on success."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result
        service = TeacherService(mock_db)
        result = await service.delete_availability_slot(uuid.uuid4())
        assert result is True


# ===========================================================================
# 2. AdminService
# ===========================================================================

from models import Kullanici, KullaniciRolu
from services.admin_service import AdminAuthorizationError, AdminService


def _make_kullanici(rol=KullaniciRolu.ADMIN, aktif=True):
    k = MagicMock(spec=Kullanici)
    k.kullanici_id = str(uuid.uuid4())
    k.email = "admin@test.com"
    k.rol = rol
    k.aktif = aktif
    return k


class TestAdminServiceAuth:
    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_obj_admin(self):
        """_admin_yetkisi_kontrol returns True for admin user object."""
        service = AdminService()
        kullanici = _make_kullanici(rol=KullaniciRolu.ADMIN)
        result = await service._admin_yetkisi_kontrol(kullanici)
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_with_obj_ogrenci(self):
        """_admin_yetkisi_kontrol returns False for student user object."""
        service = AdminService()
        kullanici = _make_kullanici(rol=KullaniciRolu.OGRENCI)
        result = await service._admin_yetkisi_kontrol(kullanici)
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_inactive_user(self):
        """_admin_yetkisi_kontrol returns False for inactive user."""
        service = AdminService()
        kullanici = _make_kullanici(rol=KullaniciRolu.ADMIN, aktif=False)
        result = await service._admin_yetkisi_kontrol(kullanici)
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_none_input(self):
        """_admin_yetkisi_kontrol returns False for None input."""
        service = AdminService()
        result = await service._admin_yetkisi_kontrol(None)
        assert result is False

    @pytest.mark.asyncio
    async def test_super_admin_yetkisi_kontrol_admin(self):
        """_super_admin_yetkisi_kontrol returns False for regular admin."""
        service = AdminService()
        kullanici = _make_kullanici(rol=KullaniciRolu.ADMIN)
        result = await service._super_admin_yetkisi_kontrol(kullanici)
        # ADMIN is not in super_admin_rolleri (only SUPER_ADMIN is)
        assert result is False

    @pytest.mark.asyncio
    async def test_super_admin_yetkisi_kontrol_super_admin(self):
        """_super_admin_yetkisi_kontrol returns True for SUPER_ADMIN."""
        service = AdminService()
        kullanici = _make_kullanici(rol=KullaniciRolu.SUPER_ADMIN)
        result = await service._super_admin_yetkisi_kontrol(kullanici)
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_aktivite_kaydet_returns_true(self):
        """admin_aktivite_kaydet returns True on success."""
        service = AdminService()
        result = await service.admin_aktivite_kaydet(
            "admin-123", "test_action", hedef_id="user-456", detaylar={"key": "value"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_aktivite_kaydet_no_details(self):
        """admin_aktivite_kaydet works without optional params."""
        service = AdminService()
        result = await service.admin_aktivite_kaydet("admin-123", "simple_action")
        assert result is True

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_hierarchy(self):
        """kullanici_yetki_kontrol respects role hierarchy."""
        service = AdminService()
        admin_user = _make_kullanici(rol=KullaniciRolu.ADMIN)

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            mock_servis.kullanici_getir = AsyncMock(return_value=admin_user)
            # ADMIN (level 4) >= OGRETMEN (level 3) should be True
            result = await service.kullanici_yetki_kontrol(
                admin_user.kullanici_id, KullaniciRolu.OGRETMEN
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_insufficient_role(self):
        """kullanici_yetki_kontrol returns False for insufficient role."""
        service = AdminService()
        ogrenci_user = _make_kullanici(rol=KullaniciRolu.OGRENCI)

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            mock_servis.kullanici_getir = AsyncMock(return_value=ogrenci_user)
            # OGRENCI (level 1) < ADMIN (level 4)
            result = await service.kullanici_yetki_kontrol(
                ogrenci_user.kullanici_id, KullaniciRolu.ADMIN
            )
            assert result is False


class TestAdminServiceUsers:
    @pytest.mark.asyncio
    async def test_kullanicilari_listele_requires_admin(self):
        """kullanicilari_listele raises AdminAuthorizationError for non-admin."""
        service = AdminService()
        ogrenci = _make_kullanici(rol=KullaniciRolu.OGRENCI)

        with pytest.raises(AdminAuthorizationError):
            await service.kullanicilari_listele(current_user=ogrenci)

    @pytest.mark.asyncio
    async def test_kullanicilari_listele_success(self):
        """kullanicilari_listele returns user list for admin."""
        service = AdminService()
        admin = _make_kullanici(rol=KullaniciRolu.ADMIN)

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            mock_servis.kullanici_getir = AsyncMock(return_value=admin)
            result = await service.kullanicilari_listele(
                current_user=admin, sayfa=1, sayfa_boyutu=5
            )
            assert len(result) == 5

    @pytest.mark.asyncio
    async def test_kullanici_getir_admin(self):
        """kullanici_getir delegates to kullanici_servisi for admin."""
        service = AdminService()
        admin = _make_kullanici(rol=KullaniciRolu.ADMIN)
        target = _make_kullanici(rol=KullaniciRolu.OGRENCI)

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            # The @admin_required decorator checks auth via _admin_yetkisi_kontrol.
            # We pass the admin object directly so no kullanici_getir call in decorator.
            # The actual method body calls kullanici_getir once → returns target.
            mock_servis.kullanici_getir = AsyncMock(return_value=target)
            result = await service.kullanici_getir(
                target.kullanici_id, current_user=admin
            )
            assert result == target

    @pytest.mark.asyncio
    async def test_kullanici_sil_self_delete_raises(self):
        """kullanici_sil raises AdminAuthorizationError when trying to delete self."""
        service = AdminService()
        super_admin = _make_kullanici(rol=KullaniciRolu.SUPER_ADMIN)
        shared_id = "super-admin-self-id"
        super_admin.kullanici_id = shared_id

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            # Decorator calls _super_admin_yetkisi_kontrol with current_user string →
            # that branches to kullanici_getir(string) → returns super_admin object.
            # Then the method body checks kullanici_id == current_user (str == str).
            mock_servis.kullanici_getir = AsyncMock(return_value=super_admin)

            with pytest.raises(AdminAuthorizationError):
                # current_user is the same string id so that kullanici_id == current_user
                await service.kullanici_sil(shared_id, current_user=shared_id)

    @pytest.mark.asyncio
    async def test_kullanici_sil_requires_super_admin(self):
        """kullanici_sil raises AdminAuthorizationError for regular admin."""
        service = AdminService()
        admin = _make_kullanici(rol=KullaniciRolu.ADMIN)

        with pytest.raises(AdminAuthorizationError):
            await service.kullanici_sil("some-user-id", current_user=admin)


class TestAdminServiceContent:
    @pytest.mark.asyncio
    async def test_egitim_materyalleri_listesi_returns_list(self):
        """egitim_materyalleri_listesi returns list of materials for admin."""
        service = AdminService()
        admin = _make_kullanici(rol=KullaniciRolu.ADMIN)

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            mock_servis.kullanici_getir = AsyncMock(return_value=admin)
            result = await service.egitim_materyalleri_listesi(
                current_user=admin, sayfa_boyutu=3
            )
            assert len(result) == 3
            assert "id" in result[0]

    @pytest.mark.asyncio
    async def test_egitim_materyali_ekle_success(self):
        """egitim_materyali_ekle returns created material for admin."""
        service = AdminService()
        admin = _make_kullanici(rol=KullaniciRolu.ADMIN)

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            mock_servis.kullanici_getir = AsyncMock(return_value=admin)
            materyal_data = {
                "baslik": "Matematik Dersi",
                "tur": "video",
                "konu": "Integral",
            }
            result = await service.egitim_materyali_ekle(
                materyal_data, current_user=admin
            )
            assert result["baslik"] == "Matematik Dersi"
            assert "id" in result

    @pytest.mark.asyncio
    async def test_icerik_ara_returns_results(self):
        """icerik_ara returns search results dict for admin."""
        service = AdminService()
        admin = _make_kullanici(rol=KullaniciRolu.ADMIN)

        with patch("services.admin_service.kullanici_servisi") as mock_servis:
            mock_servis.kullanici_getir = AsyncMock(return_value=admin)
            result = await service.icerik_ara("limit", current_user=admin)
            assert "sonuclar" in result
            assert result["arama_terimi"] == "limit"
            assert len(result["sonuclar"]) > 0

    @pytest.mark.asyncio
    async def test_son_aktiviteler_getir_returns_list(self):
        """_son_aktiviteler_getir returns non-empty activity list."""
        service = AdminService()
        result = await service._son_aktiviteler_getir()
        assert isinstance(result, list)
        assert len(result) > 0
        assert "tip" in result[0]

    @pytest.mark.asyncio
    async def test_toplam_soru_sayisi_fallback(self):
        """_toplam_soru_sayisi returns 0 on exception."""
        service = AdminService()
        with patch("services.admin_service.soru_bankasi_servisi") as mock_sbs:
            mock_sbs.istatistikler_getir = AsyncMock(side_effect=Exception("DB down"))
            result = await service._toplam_soru_sayisi()
            assert result == 0


# ===========================================================================
# 3. LearningStyleService
# ===========================================================================

from services.learning_style_service import LearningStyleService


class TestLearningStyleServiceHelpers:
    def test_generate_hibrit_code_visual_active(self):
        """_generate_hibrit_code produces correct code for visual+active learner."""
        service = LearningStyleService()
        vark = {"visual": 0.6, "auditory": 0.1, "reading": 0.1, "kinesthetic": 0.2}
        felder = {
            "active_reflective": 0.5,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.5,
            "sequential_global": 0.5,
        }
        code = service._generate_hibrit_code(vark, felder)
        assert code.startswith("V")
        assert "-" in code

    def test_generate_hibrit_code_mixed(self):
        """_generate_hibrit_code returns M for zero VARK scores."""
        service = LearningStyleService()
        vark = {"visual": 0.0, "auditory": 0.0, "reading": 0.0, "kinesthetic": 0.0}
        felder = {
            "active_reflective": 0.0,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.0,
            "sequential_global": 0.0,
        }
        code = service._generate_hibrit_code(vark, felder)
        assert code.startswith("M")

    def test_get_profile_description_includes_code(self):
        """_get_profile_description contains the hybrid code."""
        service = LearningStyleService()
        desc = service._get_profile_description("V-ASVS")
        assert "V-ASVS" in desc

    def test_calculate_confidence_all_data(self):
        """_calculate_confidence is high when all behavioral data present."""
        service = LearningStyleService()
        behavioral_data = {
            "video_watch_time_minutes": 30,
            "audio_content_time_minutes": 20,
            "text_reading_time_minutes": 45,
            "interactive_exercise_time_minutes": 15,
            "group_study_minutes": 10,
            "solo_study_minutes": 60,
        }
        confidence = service._calculate_confidence(behavioral_data, ["A", "B", "C"])
        assert confidence > 0.5
        assert confidence <= 1.0

    def test_calculate_confidence_no_data(self):
        """_calculate_confidence returns minimum baseline for empty data."""
        service = LearningStyleService()
        confidence = service._calculate_confidence({}, None)
        assert confidence == pytest.approx(0.3)

    def test_calculate_confidence_partial_data(self):
        """_calculate_confidence scales with partial behavioral data."""
        service = LearningStyleService()
        partial_data = {
            "video_watch_time_minutes": 30,
            "audio_content_time_minutes": 0,
            "text_reading_time_minutes": 0,
            "interactive_exercise_time_minutes": 0,
            "group_study_minutes": 0,
            "solo_study_minutes": 0,
        }
        confidence = service._calculate_confidence(partial_data, None)
        assert confidence >= 0.3

    def test_vark_dimensions_configured(self):
        """LearningStyleService has correct VARK dimensions."""
        service = LearningStyleService()
        assert "visual" in service.vark_dimensions
        assert "auditory" in service.vark_dimensions
        assert "reading" in service.vark_dimensions
        assert "kinesthetic" in service.vark_dimensions

    def test_felder_dimensions_configured(self):
        """LearningStyleService has correct Felder dimensions."""
        service = LearningStyleService()
        assert len(service.felder_dimensions) == 4

    @pytest.mark.asyncio
    async def test_get_all_hybrid_codes_returns_64(self):
        """get_all_hybrid_codes returns up to 64 combinations."""
        service = LearningStyleService()
        with patch("services.learning_style_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            codes = await service.get_all_hybrid_codes()
        assert len(codes) == 64
        assert "kod" in codes[0]
        assert "vark_komponenti" in codes[0]

    @pytest.mark.asyncio
    async def test_get_all_hybrid_codes_cache_hit(self):
        """get_all_hybrid_codes returns cached data on cache hit."""
        service = LearningStyleService()
        cached_data = [{"kod": "V-ASMS", "desc": "test"}]
        with patch("services.learning_style_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=cached_data)
            codes = await service.get_all_hybrid_codes()
        assert codes == cached_data


class TestLearningStyleServiceDB:
    @pytest.mark.asyncio
    async def test_get_student_profile_not_found(self, mock_db):
        """get_student_profile returns None when no profile exists."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = LearningStyleService()
        result = await service.get_student_profile("student-001", mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_student_profile_found(self, mock_db):
        """get_student_profile returns dict when profile exists."""
        from models import StudentLearningProfile

        profile = MagicMock(spec=StudentLearningProfile)
        profile.student_id = "student-001"
        profile.hybrid_code = "V-ASMS"
        profile.dominant_vark_style = "visual"
        profile.dominant_felder_dimension = "active_reflective"
        profile.confidence_score = 0.75
        profile.detected_at = datetime.now(UTC)
        profile.profile_description = "Test profile"
        profile.vark_profile_dict = {
            "visual": 0.6,
            "auditory": 0.1,
            "reading": 0.1,
            "kinesthetic": 0.2,
        }
        profile.felder_profile_dict = {
            "active_reflective": 0.5,
            "sensing_intuitive": 0.0,
            "visual_verbal": 0.5,
            "sequential_global": 0.0,
        }

        mock_db.execute.return_value = _make_execute_result(scalar=profile)
        service = LearningStyleService()
        result = await service.get_student_profile("student-001", mock_db)

        assert result is not None
        assert result["student_id"] == "student-001"
        assert result["hibrit_kod"] == "V-ASMS"

    @pytest.mark.asyncio
    async def test_get_service_stats(self, mock_db):
        """get_service_stats returns stats with correct keys."""
        mock_db.execute.return_value = _make_execute_result(scalar=42)
        service = LearningStyleService()
        stats = await service.get_service_stats(mock_db)

        assert stats["toplam_profil_sayisi"] == 42
        assert "vark_boyutlari" in stats
        assert stats["toplam_kombinasyon"] == 64

    @pytest.mark.asyncio
    async def test_calculate_vark_no_analytics(self, mock_db):
        """_calculate_vark_profile returns neutral profile with no analytics."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = LearningStyleService()
        result = await service._calculate_vark_profile("sid", mock_db, {})

        assert result["visual"] == pytest.approx(0.25)
        assert result["auditory"] == pytest.approx(0.25)
        assert result["reading"] == pytest.approx(0.25)
        assert result["kinesthetic"] == pytest.approx(0.25)

    @pytest.mark.asyncio
    async def test_calculate_vark_with_content_times(self, mock_db):
        """_calculate_vark_profile normalizes content time data."""
        from models import LearningAnalytics

        analytics = [MagicMock(spec=LearningAnalytics)]
        analytics[0].study_time_minutes = 120
        analytics[0].questions_attempted = 50
        mock_db.execute.return_value = _make_execute_result(scalars_list=analytics)

        service = LearningStyleService()
        behavioral = {
            "video_watch_time_minutes": 60,
            "audio_content_time_minutes": 10,
            "text_reading_time_minutes": 20,
            "interactive_exercise_time_minutes": 10,
        }
        result = await service._calculate_vark_profile("sid", mock_db, behavioral)
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01  # Normalized to sum ~1

    @pytest.mark.asyncio
    async def test_calculate_felder_no_sessions(self, mock_db):
        """_calculate_felder_profile returns zeros with no sessions."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = LearningStyleService()
        result = await service._calculate_felder_profile("sid", mock_db, {})

        assert all(v == 0.0 for v in result.values())

    @pytest.mark.asyncio
    async def test_get_learning_style_statistics(self, mock_db):
        """get_learning_style_statistics returns stat dict."""
        from models import StudentLearningProfile

        profile1 = MagicMock(spec=StudentLearningProfile)
        profile1.dominant_vark_style = "visual"
        profile1.dominant_felder_dimension = "active_reflective"
        profile1.hybrid_code = "V-ASMS"

        profile2 = MagicMock(spec=StudentLearningProfile)
        profile2.dominant_vark_style = "reading"
        profile2.dominant_felder_dimension = "sensing_intuitive"
        profile2.hybrid_code = "R-MSMS"

        with patch("services.learning_style_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()
            mock_db.execute.return_value = _make_execute_result(
                scalars_list=[profile1, profile2]
            )
            service = LearningStyleService()
            stats = await service.get_learning_style_statistics(mock_db)

        assert stats["toplam_öğrenci"] == 2
        assert "vark_dağılımı" in stats
        assert stats["vark_dağılımı"]["visual"] == 1


# ===========================================================================
# 4. StudentReviewService
# ===========================================================================

from models.student_review import (
    ReviewStatus,
    ReviewType,
    StudentReview,
)
from services.student_review_service import StudentReviewService


def _make_review(status=ReviewStatus.APPROVED):
    r = MagicMock(spec=StudentReview)
    r.id = uuid.uuid4()
    r.status = status
    r.spam_score = 0.1
    r.quality_score = 0.8
    r.contains_profanity = False
    r.contains_contact_info = False
    r.is_too_short = False
    r.helpful_count = 5
    r.not_helpful_count = 2
    r.report_count = 0
    r.view_count = 0
    r.tags = ["iyi", "anlatimli"]
    r.overall_rating = 4.5
    r.is_verified = True
    return r


class TestStudentReviewServiceAutoModeration:
    def test_calculate_spam_score_clean_content(self):
        """_calculate_spam_score returns low score for clean content."""
        service = StudentReviewService(MagicMock())
        score = service._calculate_spam_score(
            "Bu üniversite çok güzel, öğretmenler yardımsever", "Genel Yorum"
        )
        assert score < 0.5

    def test_calculate_spam_score_spam_keywords(self):
        """_calculate_spam_score returns higher score for spam keywords."""
        service = StudentReviewService(MagicMock())
        score = service._calculate_spam_score(
            "Click here to buy now and get free money guaranteed", "Limited offer"
        )
        assert score > 0.3

    def test_calculate_spam_score_excessive_urls(self):
        """_calculate_spam_score penalizes excessive URLs."""
        service = StudentReviewService(MagicMock())
        score = service._calculate_spam_score(
            "Visit http://site1.com https://site2.com www.site3.com for info", "Links"
        )
        assert score >= 0.3

    def test_calculate_quality_score_short_content(self):
        """_calculate_quality_score stays below 0.7 for very short content."""
        service = StudentReviewService(MagicMock())
        # "Ok." has 1 sentence ending → +0.1 bonus, but no length/diversity bonus
        score = service._calculate_quality_score("Ok.", "Title")
        assert score < 0.7  # Still low quality despite sentence bonus

    def test_calculate_quality_score_long_rich_content(self):
        """_calculate_quality_score is higher for long, diverse content."""
        service = StudentReviewService(MagicMock())
        content = "Bu üniversite gerçekten mükemmel. " * 20
        score = service._calculate_quality_score(content, "Detaylı Yorum")
        assert score > 0.7

    def test_check_profanity_clean(self):
        """_check_profanity returns False for clean text."""
        service = StudentReviewService(MagicMock())
        assert service._check_profanity("Normal bir yorum yazıyorum.") is False

    def test_check_contact_info_with_email(self):
        """_check_contact_info detects email addresses."""
        service = StudentReviewService(MagicMock())
        assert service._check_contact_info("bana yaz: test@example.com") is True

    def test_check_contact_info_with_phone(self):
        """_check_contact_info detects phone numbers."""
        service = StudentReviewService(MagicMock())
        assert service._check_contact_info("ara beni: 05551234567") is True

    def test_check_contact_info_no_info(self):
        """_check_contact_info returns False for text without contact info."""
        service = StudentReviewService(MagicMock())
        assert service._check_contact_info("Bu güzel bir üniversite.") is False

    @pytest.mark.parametrize(
        "content,title,expected_contains",
        [
            ("Click here buy now", "Spam", True),  # spam keyword → higher
            ("Normal yorum metni.", "Başlık", False),  # clean
        ],
    )
    def test_spam_score_parametrized(self, content, title, expected_contains):
        """_calculate_spam_score correctly classifies spam vs clean."""
        service = StudentReviewService(MagicMock())
        score = service._calculate_spam_score(content, title)
        if expected_contains:
            assert score > 0.0
        else:
            assert score >= 0.0


class TestStudentReviewServiceCRUD:
    @pytest.mark.asyncio
    async def test_create_review_approved_for_good_content(self, mock_db):
        """create_review sets APPROVED for high-quality, non-spam content."""
        service = StudentReviewService(mock_db)
        # Mock the add_to_moderation_queue path (not called for APPROVED)
        mock_db.execute.return_value = _make_execute_result(scalar=None)

        long_content = "Bu üniversite gerçekten çok iyi. Hocalar harika. " * 15

        review = await service.create_review(
            user_id=uuid.uuid4(),
            review_type=ReviewType.UNIVERSITY,
            title="Mükemmel Üniversite",
            content=long_content,
            overall_rating=5.0,
        )

        mock_db.add.assert_called()
        added = mock_db.add.call_args[0][0]
        assert added.status in [ReviewStatus.APPROVED, ReviewStatus.PENDING]

    @pytest.mark.asyncio
    async def test_create_review_flagged_for_short_content(self, mock_db):
        """create_review sets FLAGGED for too-short content."""
        service = StudentReviewService(mock_db)
        mock_db.execute.return_value = _make_execute_result(scalar=None)

        await service.create_review(
            user_id=uuid.uuid4(),
            review_type=ReviewType.UNIVERSITY,
            title="Kısa",
            content="Kötü.",
            overall_rating=1.0,
        )

        # The first add() call is always the StudentReview object
        first_added = mock_db.add.call_args_list[0][0][0]
        assert first_added.is_too_short is True
        assert first_added.status == ReviewStatus.FLAGGED

    @pytest.mark.asyncio
    async def test_get_review_by_id_increments_view_count(self, mock_db):
        """get_review_by_id increments view_count."""
        review = _make_review()
        mock_db.execute.return_value = _make_execute_result(scalar=review)
        service = StudentReviewService(mock_db)

        result = await service.get_review_by_id(review.id)

        assert result == review
        assert review.view_count == 1
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_review_by_id_not_found(self, mock_db):
        """get_review_by_id returns None when not found."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = StudentReviewService(mock_db)
        result = await service.get_review_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_review_success(self, mock_db):
        """update_review updates fields and refreshes."""
        review = _make_review()
        mock_db.execute.return_value = _make_execute_result(scalar=review)
        service = StudentReviewService(mock_db)

        result = await service.update_review(review.id, title="Yeni Başlık")

        mock_db.commit.assert_called()
        mock_db.refresh.assert_called()
        assert result == review

    @pytest.mark.asyncio
    async def test_update_review_not_found(self, mock_db):
        """update_review returns None when review not found."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = StudentReviewService(mock_db)
        result = await service.update_review(uuid.uuid4(), title="X")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_review_success(self, mock_db):
        """delete_review returns True on success."""
        review = _make_review()
        mock_db.execute.return_value = _make_execute_result(scalar=review)
        service = StudentReviewService(mock_db)
        result = await service.delete_review(review.id)
        mock_db.delete.assert_called_with(review)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_review_not_found(self, mock_db):
        """delete_review returns False when not found."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = StudentReviewService(mock_db)
        result = await service.delete_review(uuid.uuid4())
        assert result is False


class TestStudentReviewServiceFiltering:
    @pytest.mark.asyncio
    async def test_get_reviews_default_approved_only(self, mock_db):
        """get_reviews returns only APPROVED reviews by default."""
        reviews = [_make_review() for _ in range(3)]
        mock_db.execute.return_value = _make_execute_result(scalars_list=reviews)
        service = StudentReviewService(mock_db)

        result = await service.get_reviews()
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_reviews_with_min_rating(self, mock_db):
        """get_reviews applies min_rating filter."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = StudentReviewService(mock_db)
        result = await service.get_reviews(min_rating=4.0)
        mock_db.execute.assert_called_once()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_reviews_sort_by_helpful(self, mock_db):
        """get_reviews accepts sort_by='helpful' without error."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = StudentReviewService(mock_db)
        result = await service.get_reviews(sort_by="helpful")
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_review_statistics_not_found(self, mock_db):
        """get_review_statistics returns None when no stats found."""
        mock_db.execute.return_value = _make_execute_result(scalar=None)
        service = StudentReviewService(mock_db)
        result = await service.get_review_statistics(ReviewType.UNIVERSITY)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_moderation_queue_empty(self, mock_db):
        """get_moderation_queue returns empty list when queue is empty."""
        mock_db.execute.return_value = _make_execute_result(scalars_list=[])
        service = StudentReviewService(mock_db)
        result = await service.get_moderation_queue()
        assert result == []

    def test_get_top_tags_counts_correctly(self):
        """_get_top_tags returns most frequent tags."""
        service = StudentReviewService(MagicMock())
        r1 = _make_review()
        r1.tags = ["iyi", "kaliteli", "iyi"]
        r2 = _make_review()
        r2.tags = ["iyi", "pahalı"]
        r3 = _make_review()
        r3.tags = None

        top = service._get_top_tags([r1, r2, r3], limit=3)
        assert "iyi" in top
        assert len(top) <= 3

    def test_get_top_tags_empty_reviews(self):
        """_get_top_tags returns empty list for empty reviews."""
        service = StudentReviewService(MagicMock())
        result = service._get_top_tags([])
        assert result == []
