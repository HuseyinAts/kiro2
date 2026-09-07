"""
Unit tests for coverage improvement.
Files covered:
  - api/diary_api.py
  - api/advanced_reports.py
  - services/question_crud_service.py
  - services/teacher_service.py
  - services/admin_service.py

Uses minimal FastAPI app per router + httpx ASGITransport pattern.
Services tested with AsyncMock DB sessions.
"""

import sys
import types
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub out heavy third-party modules BEFORE any local import
# ---------------------------------------------------------------------------

_ORIG_SYS_MODULES = {}
_STUBBED_KEYS = [
    "slowapi",
    "slowapi.util",
    "slowapi.errors",
    "celery",
    "celery.schedules",
    "redis",
    "redis.asyncio",
    "pgvector",
    "pgvector.sqlalchemy",
    "zemberek",
    "zemberek.morphology",
]
for k in _STUBBED_KEYS:
    if k in sys.modules:
        _ORIG_SYS_MODULES[k] = sys.modules[k]

# SS10.66: `_stub()` var olan modulu AYNEN dondururken, cagiran taraf onun
# ozniteliklerini KOSULSUZ degistiriyordu. Gercek paket zaten iceri alinmissa
# (celery ve slowapi bu depoda KURULU) bu, sureci kalici olarak kirletir:
# asagidaki geri yukleme dongusu yalnizca sys.modules KAYDINI eski haline
# getirir, GERCEK MODULE yazilan ozniteligi geri almaz.
# Olculen zarar: core/celery_app.py app'ini sahte Celery'den uretiyor ve
# tests/test_social_tasks.py::TestCeleryAppSchedule MagicMock uzerinde assert
# ediyordu (CI kosusu 34072269135'te 2 kirmizi).
# Cozum: hangi modulleri BU dosyanin yarattigini kaydet, yalnizca onlari
# ozellestir. Bkz. SS10.63 (ayni kok neden, ilk nusha).
_BIZIM_STUBLARIMIZ: set[str] = set()


def _stub(name: str) -> types.ModuleType:
    """Return existing module or create a lightweight stub."""
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    _BIZIM_STUBLARIMIZ.add(name)
    return mod


def _bizim_mi(name: str) -> bool:
    """Modulu bu dosya mi yaratti? Degilse ozniteligine dokunulmaz."""
    return name in _BIZIM_STUBLARIMIZ


# slowapi stubs (used by learning_path_v2)
#
# NOT (SS10.66, OLCULDU VE GERI ALINDI): asagidaki uc mutasyonu da
# `_bizim_mi(...)` ile korumak DENENDI. Sonuc: gercek `slowapi.Limiter`
# calismaya basliyor ve `redis` MagicMock oldugu icin `limits` kutuphanesi
# surumu "0.0.0" gorup ConfigurationError firlatiyor ->
# tests/fast/test_api_coverage_batch13.py::TestEnhancedChatCoverage'in
# 9 testi setup'ta dusuyor. Yani slowapi mutasyonunun kaldirilmasi BASKA bir
# kirlenmeyi (redis stub'i) aciga cikariyor; ikisini birden cozmek bu PR'in
# konusu degil. CI'da olculen kirmizi celery'den geliyordu ve asagida o
# duzeltildi. Bu blok BILEREK eski halinde birakildi.
_slowapi = _stub("slowapi")
_slowapi.Limiter = MagicMock  # type: ignore[attr-defined]
_slowapi._rate_limit_exceeded_handler = MagicMock  # type: ignore[attr-defined]
_slowapi_util = _stub("slowapi.util")
_slowapi_util.get_remote_address = lambda req: "127.0.0.1"  # type: ignore[attr-defined]
_slowapi_errors = _stub("slowapi.errors")


class MockRateLimitExceeded(Exception):  # noqa: N818
    """slowapi.errors.RateLimitExceeded'in sahtesi.

    N818 (adin 'Error' ile bitmesi) bastirildi: bu sinif taklit ettigi
    yukari-akis adiyla ESLESMEK zorunda, aksi halde stub'in amaci kalmaz.
    """


_slowapi_errors.RateLimitExceeded = MockRateLimitExceeded  # type: ignore[attr-defined]

# celery stubs
_celery = _stub("celery")
if _bizim_mi("celery"):
    _celery.Celery = lambda *args, **kwargs: MagicMock()  # type: ignore[attr-defined]
_stub("celery.schedules")

# redis stubs (for services that import redis directly)
_redis_mod = _stub("redis")
_stub("redis.asyncio")

# pgvector stubs
_stub("pgvector")
_pgvector_sqlalchemy = _stub("pgvector.sqlalchemy")
from sqlalchemy.types import UserDefinedType  # noqa: E402


class _MockVector(UserDefinedType):
    def __init__(self, dim=None):
        self.dim = dim

    def get_col_spec(self, **kw):
        return "VECTOR"


_pgvector_sqlalchemy.Vector = _MockVector  # type: ignore[attr-defined]

# zemberek stubs
_stub("zemberek")
_stub("zemberek.morphology")

# Immediately restore original sys.modules to prevent pollution during collection
for k in _STUBBED_KEYS:
    if k in _ORIG_SYS_MODULES:
        sys.modules[k] = _ORIG_SYS_MODULES[k]
    else:
        sys.modules.pop(k, None)


@pytest.fixture(scope="module", autouse=True)
def setup_stubs_fixture():
    orig = {}
    for k in _STUBBED_KEYS:
        if k in sys.modules:
            orig[k] = sys.modules[k]

    # Re-apply the stubs
    sys.modules["slowapi"] = _slowapi
    sys.modules["slowapi.util"] = _slowapi_util
    sys.modules["slowapi.errors"] = _slowapi_errors
    sys.modules["celery"] = _celery
    sys.modules["celery.schedules"] = sys.modules.get("celery.schedules")
    sys.modules["redis"] = _redis_mod
    sys.modules["redis.asyncio"] = sys.modules.get("redis.asyncio")
    sys.modules["pgvector"] = sys.modules.get("pgvector")
    sys.modules["pgvector.sqlalchemy"] = _pgvector_sqlalchemy
    sys.modules["zemberek"] = sys.modules.get("zemberek")
    sys.modules["zemberek.morphology"] = sys.modules.get("zemberek.morphology")

    yield

    for k in _STUBBED_KEYS:
        if k in orig:
            sys.modules[k] = orig[k]
        else:
            sys.modules.pop(k, None)


# ---------------------------------------------------------------------------
# Now import FastAPI / httpx infrastructure
# ---------------------------------------------------------------------------

from fastapi import FastAPI  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

# ===========================================================================
# Helpers
# ===========================================================================


def _make_authenticated_user(role: str = "STUDENT", uid: int = 1):
    """Return an AuthenticatedUser-compatible object."""
    from core.dependencies import AuthenticatedUser
    from models.enums_db import UserRole

    return AuthenticatedUser(
        id=uid,
        username=f"testuser{uid}",
        role=UserRole(role),
        email=f"test{uid}@test.com",
    )


def _make_diary_user():
    """Return a user compatible with diary_api (models.user.User)."""
    user = MagicMock()
    user.id = str(uuid.uuid4())
    return user


def _make_mock_db() -> AsyncMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    db.delete = MagicMock()
    return db


def _scalar_result(value):
    """Build a mock execute() result that returns value from scalar_one_or_none()."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    return r


def _scalars_result(values):
    """Build a mock execute() result that returns values from scalars().all()."""
    r = MagicMock()
    r.scalars.return_value.all.return_value = values
    return r


# ===========================================================================
# SECTION 1: api/advanced_reports.py
# ===========================================================================


class TestAdvancedReportsHelpers:
    """Tests for the pure helper functions in advanced_reports.py."""

    def test_karsilastir_parametre_ideal(self):
        from api.advanced_reports import _karsilastir_parametre

        result = _karsilastir_parametre(1.2, 0.3, 1.0)
        assert result["durum"] == "ideal"
        assert result["skor"] == 100.0
        assert result["deger"] == 1.2

    def test_karsilastir_parametre_acceptable(self):
        from api.advanced_reports import _karsilastir_parametre

        result = _karsilastir_parametre(0.5, 0.3, 1.0)
        assert result["durum"] == "kabul_edilebilir"
        assert result["skor"] == 70.0

    def test_karsilastir_parametre_insufficient(self):
        from api.advanced_reports import _karsilastir_parametre

        result = _karsilastir_parametre(0.1, 0.3, 1.0)
        assert result["durum"] == "yetersiz"
        assert result["skor"] == 30.0

    def test_karsilastir_zorluk_within_range(self):
        from api.advanced_reports import _karsilastir_zorluk

        result = _karsilastir_zorluk(0.5, (-2.0, 2.0))
        assert result["durum"] == "uygun"
        assert result["skor"] == 100.0

    def test_karsilastir_zorluk_outside_range(self):
        from api.advanced_reports import _karsilastir_zorluk

        result = _karsilastir_zorluk(5.0, (-2.0, 2.0))
        assert result["durum"] == "uygun_degil"
        assert result["skor"] == 30.0

    def test_karsilastir_sans_faktoru_ok(self):
        from api.advanced_reports import _karsilastir_sans_faktoru

        result = _karsilastir_sans_faktoru(0.2, 0.25)
        assert result["durum"] == "uygun"
        assert result["skor"] == 100.0

    def test_karsilastir_sans_faktoru_high(self):
        from api.advanced_reports import _karsilastir_sans_faktoru

        result = _karsilastir_sans_faktoru(0.5, 0.25)
        assert result["durum"] == "yuksek"
        assert result["skor"] == 30.0

    def test_hesapla_genel_uyum_skoru(self):
        from api.advanced_reports import _hesapla_genel_uyum_skoru

        karsilastirma = {
            "ayirt_edicilik_durumu": {"skor": 100.0},
            "zorluk_durumu": {"skor": 70.0},
            "sans_faktoru_durumu": {"skor": 100.0},
        }
        result = _hesapla_genel_uyum_skoru(karsilastirma)
        assert abs(result - 90.0) < 0.01

    def test_belirle_karsilastirma_sonucu_both_above_90(self):
        from api.advanced_reports import _belirle_karsilastirma_sonucu

        result = _belirle_karsilastirma_sonucu(95.0, 92.0)
        assert "aşıyor" in result

    def test_belirle_karsilastirma_sonucu_both_above_70(self):
        from api.advanced_reports import _belirle_karsilastirma_sonucu

        result = _belirle_karsilastirma_sonucu(75.0, 80.0)
        assert "uygun" in result

    def test_belirle_karsilastirma_sonucu_below_70(self):
        from api.advanced_reports import _belirle_karsilastirma_sonucu

        result = _belirle_karsilastirma_sonucu(50.0, 50.0)
        assert "altında" in result

    def test_generate_improvement_suggestions(self):
        from api.advanced_reports import _generate_improvement_suggestions

        osym = {
            "ayirt_edicilik_durumu": {"skor": 50.0},
            "zorluk_durumu": {"skor": 50.0},
            "sans_faktoru_durumu": {"skor": 50.0},
        }
        params = {"morfoloji_avantaji": 0.15}
        suggestions = _generate_improvement_suggestions(osym, {}, params)
        assert isinstance(suggestions, list)
        assert len(suggestions) >= 1

    def test_get_onerilen_ogrenme_yontemi_visual(self):
        from api.advanced_reports import _get_onerilen_ogrenme_yontemi

        vark = {"visual": 0.9, "auditory": 0.2, "reading": 0.3, "kinesthetic": 0.1}
        felder: dict[str, object] = {}
        result = _get_onerilen_ogrenme_yontemi("test_konu", vark, felder)
        assert result == "görsel_materyaller"

    def test_get_onerilen_ogrenme_yontemi_karma(self):
        from api.advanced_reports import _get_onerilen_ogrenme_yontemi

        vark = {"visual": 0.5, "auditory": 0.5, "reading": 0.5, "kinesthetic": 0.5}
        felder: dict[str, object] = {}
        result = _get_onerilen_ogrenme_yontemi("test_konu", vark, felder)
        assert result == "karma_yontem"

    def test_get_hibrit_profil_aciklamasi(self):
        from api.advanced_reports import _get_hibrit_profil_aciklamasi

        result = _get_hibrit_profil_aciklamasi("V-R-A-S")
        assert "V-R-A-S" in result


class TestAdvancedReportsAsync:
    """Tests for async helper functions in advanced_reports.py."""

    def _make_sinav_sonucu(self):
        """Build a minimal SinavSonucu."""
        from models.enums import SinavTipi
        from models.exam import KonuPerformansi, SinavSonucu

        konu = KonuPerformansi(
            konu="Matematik",
            toplam_soru=10,
            dogru_sayisi=7,
            yanlis_sayisi=2,
            bos_sayisi=1,
            basari_yuzdesi=70.0,
        )
        return SinavSonucu(
            sonuc_id=str(uuid.uuid4()),
            sinav_id="test-sinav-123",
            ogrenci_id="ogrenci-1",
            sinav_tipi=SinavTipi.TYT,
            toplam_soru=10,
            dogru_sayisi=7,
            yanlis_sayisi=2,
            bos_sayisi=1,
            net_sayisi=6.33,
            ham_puan=70.0,
            konu_performanslari=[konu],
            zayif_konular=["Geometri"],
            guclu_konular=["Cebir"],
        )

    @pytest.mark.asyncio
    async def test_get_irt_morfoloji_analizi_returns_dict(self):
        from api.advanced_reports import _get_irt_morfoloji_analizi

        sonuc = self._make_sinav_sonucu()
        result = await _get_irt_morfoloji_analizi("sinav-1", sonuc)
        assert isinstance(result, dict)
        assert "soru_analizleri" in result or "hata" in result

    @pytest.mark.asyncio
    async def test_get_zpd_analizi_returns_dict(self):
        from api.advanced_reports import _get_zpd_analizi

        sonuc = self._make_sinav_sonucu()
        result = await _get_zpd_analizi("ogrenci-1", sonuc)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_hibrit_ogrenme_stili_analizi_returns_dict(self):
        from api.advanced_reports import _get_hibrit_ogrenme_stili_analizi

        sonuc = self._make_sinav_sonucu()
        result = await _get_hibrit_ogrenme_stili_analizi("ogrenci-1", sonuc)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_osym_ets_karsilastirmasi_returns_dict(self):
        from api.advanced_reports import _get_osym_ets_karsilastirmasi

        sonuc = self._make_sinav_sonucu()
        result = await _get_osym_ets_karsilastirmasi("sinav-1", sonuc)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_generate_personalized_recommendations(self):
        from api.advanced_reports import _generate_personalized_recommendations

        sonuc = self._make_sinav_sonucu()
        result = await _generate_personalized_recommendations(
            "ogrenci-1", sonuc, {}, {}, {}
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_performance_trend_returns_dict(self):
        from api.advanced_reports import _get_performance_trend
        from models.enums import SinavTipi

        result = await _get_performance_trend("ogrenci-1", SinavTipi.TYT)
        assert isinstance(result, dict)
        assert "son_5_sinav" in result

    @pytest.mark.asyncio
    async def test_generate_development_suggestions_low_score(self):
        from api.advanced_reports import _generate_development_suggestions

        sonuc = self._make_sinav_sonucu()
        sonuc.ham_puan = 50.0
        result = await _generate_development_suggestions("ogrenci-1", sonuc, {}, {})
        assert isinstance(result, list)
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_generate_development_suggestions_high_score(self):
        from api.advanced_reports import _generate_development_suggestions

        sonuc = self._make_sinav_sonucu()
        sonuc.ham_puan = 85.0
        result = await _generate_development_suggestions("ogrenci-1", sonuc, {}, {})
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_serialize_temel_sonuc(self):
        from api.advanced_reports import _serialize_temel_sonuc

        sonuc = self._make_sinav_sonucu()
        serialized = _serialize_temel_sonuc(sonuc)
        assert serialized["sinav_id"] == "test-sinav-123"
        assert "konu_performanslari" in serialized
        assert serialized["ham_puan"] == 70.0


class TestAdvancedReportsAPI:
    """Test the HTTP API endpoints of advanced_reports.py."""

    def _build_app(self, sinav_sonucu_mock=None):
        from api.advanced_reports import router
        from core.dependencies import get_current_user

        app = FastAPI()
        auth_user = _make_authenticated_user("STUDENT", 1)
        app.dependency_overrides[get_current_user] = lambda: auth_user
        app.include_router(router)
        return app

    @pytest.mark.asyncio
    async def test_download_pdf_non_pdf_returns_400(self):
        from api.advanced_reports import router
        from core.dependencies import get_current_user

        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user()
        app.include_router(router)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/reports/download/malicious.exe")
            assert resp.status_code in (400, 404)

    @pytest.mark.asyncio
    async def test_get_advanced_exam_report_404_when_no_session(self):
        from api.advanced_reports import router
        from core.dependencies import get_current_user

        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user()
        app.include_router(router)
        with patch(
            "api.advanced_reports.session_to_sinav_sonucu", AsyncMock(return_value=None)
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/reports/exam/nonexistent-id/advanced")
                assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_irt_analysis_404_when_no_session(self):
        from api.advanced_reports import router
        from core.dependencies import get_current_user

        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user()
        app.include_router(router)
        with patch(
            "api.advanced_reports.session_to_sinav_sonucu", AsyncMock(return_value=None)
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/reports/exam/abc/irt-analysis")
                assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_zpd_recommendations_404_when_no_session(self):
        from api.advanced_reports import router
        from core.dependencies import get_current_user

        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: _make_authenticated_user()
        app.include_router(router)
        with patch(
            "api.advanced_reports.session_to_sinav_sonucu", AsyncMock(return_value=None)
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/reports/exam/abc/zpd-recommendations")
                assert resp.status_code == 404


# ===========================================================================
# SECTION 2: services/admin_service.py
# ===========================================================================


class TestAdminServiceAuth:
    """Tests for AdminService authorization helpers."""

    def _make_admin_user(self, rol_value: str, aktif: bool = True):
        from models.enums import KullaniciRolu

        user = MagicMock()
        user.aktif = aktif
        user.rol = KullaniciRolu(rol_value)
        return user

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_returns_true_for_admin(self):
        from services.admin_service import AdminService

        service = AdminService()
        admin_user = self._make_admin_user("admin")

        # Pass user object directly (has .rol attribute)
        result = await service._admin_yetkisi_kontrol(admin_user)
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_returns_false_for_student(self):
        from services.admin_service import AdminService

        service = AdminService()
        student_user = self._make_admin_user("ogrenci")

        result = await service._admin_yetkisi_kontrol(student_user)
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_returns_false_inactive_user(self):
        from services.admin_service import AdminService

        service = AdminService()
        inactive_admin = self._make_admin_user("admin", aktif=False)

        result = await service._admin_yetkisi_kontrol(inactive_admin)
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_yetkisi_kontrol_returns_false_for_none(self):
        from services.admin_service import AdminService

        service = AdminService()
        result = await service._admin_yetkisi_kontrol(None)
        assert result is False

    @pytest.mark.asyncio
    async def test_super_admin_yetkisi_kontrol_returns_true_for_super_admin(self):
        from services.admin_service import AdminService

        service = AdminService()
        super_admin = self._make_admin_user("super_admin")

        result = await service._super_admin_yetkisi_kontrol(super_admin)
        assert result is True

    @pytest.mark.asyncio
    async def test_super_admin_yetkisi_kontrol_returns_false_for_admin(self):
        from services.admin_service import AdminService

        service = AdminService()
        admin_user = self._make_admin_user("admin")

        result = await service._super_admin_yetkisi_kontrol(admin_user)
        assert result is False

    @pytest.mark.asyncio
    async def test_admin_aktivite_kaydet_returns_true(self):
        from services.admin_service import AdminService

        service = AdminService()
        result = await service.admin_aktivite_kaydet(
            "admin-1",
            "kullanici_listele",
            hedef_id="user-1",
            detaylar={"key": "value"},
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_admin_aktivite_kaydet_without_details(self):
        from services.admin_service import AdminService

        service = AdminService()
        result = await service.admin_aktivite_kaydet("admin-1", "dashboard_view")
        assert result is True


class TestAdminServiceRoleHierarchy:
    """Tests for role hierarchy checks in AdminService."""

    def _make_user_with_role(self, rol_str: str):
        from models.enums import KullaniciRolu

        user = MagicMock()
        user.aktif = True
        user.rol = KullaniciRolu(rol_str)
        return user

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_with_mock_service(self):
        import services.admin_service as admin_mod
        from models.enums import KullaniciRolu
        from services.admin_service import AdminService

        service = AdminService()
        teacher_user = self._make_user_with_role("ogretmen")

        with patch.object(
            admin_mod.kullanici_servisi,
            "kullanici_getir",
            AsyncMock(return_value=teacher_user),
        ):
            result = await service.kullanici_yetki_kontrol(
                "teacher-id", KullaniciRolu.OGRENCI
            )
            assert result is True  # ogretmen >= ogrenci

    @pytest.mark.asyncio
    async def test_kullanici_yetki_kontrol_insufficient_role(self):
        import services.admin_service as admin_mod
        from models.enums import KullaniciRolu
        from services.admin_service import AdminService

        service = AdminService()
        student_user = self._make_user_with_role("ogrenci")

        with patch.object(
            admin_mod.kullanici_servisi,
            "kullanici_getir",
            AsyncMock(return_value=student_user),
        ):
            result = await service.kullanici_yetki_kontrol(
                "student-id", KullaniciRolu.ADMIN
            )
            assert result is False  # ogrenci < admin

    @pytest.mark.asyncio
    async def test_kullanicilari_listele_raises_without_admin(self):
        from services.admin_service import AdminAuthorizationError, AdminService

        service = AdminService()
        student_user = self._make_user_with_role("ogrenci")

        with pytest.raises(AdminAuthorizationError):
            await service.kullanicilari_listele(current_user=student_user)

    @pytest.mark.asyncio
    async def test_kullanicilari_listele_returns_list_for_admin(self):
        from services.admin_service import AdminService

        service = AdminService()
        admin_user = self._make_user_with_role("admin")

        result = await service.kullanicilari_listele(current_user=admin_user)
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_dashboard_istatistikleri_raises_without_admin(self):
        from services.admin_service import AdminAuthorizationError, AdminService

        service = AdminService()
        student_user = self._make_user_with_role("ogrenci")

        with pytest.raises(AdminAuthorizationError):
            await service.dashboard_istatistikleri_getir(current_user=student_user)


# ===========================================================================
# SECTION 4: services/teacher_service.py
# ===========================================================================


class TestTeacherServiceRegistration:
    """Tests for teacher registration and profile management."""

    def _make_teacher_mock(self, uid=None):
        teacher = MagicMock()
        teacher.id = uuid.uuid4()
        teacher.user_id = uid or uuid.uuid4()
        teacher.full_name = "Test Teacher"
        return teacher

    @pytest.mark.asyncio
    async def test_register_teacher_adds_to_db(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        service = TeacherService(mock_db)

        user_id = uuid.uuid4()
        _teacher = await service.register_teacher(
            user_id=user_id,
            full_name="Ali Veli",
            title="Dr.",
            bio="Experienced math teacher",
            phone="5551234567",
            email="ali@example.com",
            city="Istanbul",
            district="Kadikoy",
            years_of_experience=10,
            education_level="master",
            university="ITU",
            department="Mathematics",
            graduation_year=2010,
            hourly_rate=200.0,
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_teacher_profile_by_id(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_teacher = self._make_teacher_mock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_teacher
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.get_teacher_profile(mock_teacher.id)
        assert result is mock_teacher

    @pytest.mark.asyncio
    async def test_get_teacher_profile_not_found_returns_none(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.get_teacher_profile(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_teacher_by_user_id(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_teacher = self._make_teacher_mock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_teacher
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.get_teacher_by_user_id(mock_teacher.user_id)
        assert result is mock_teacher

    @pytest.mark.asyncio
    async def test_update_teacher_profile_not_found(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        # Simulate get_teacher_profile returning None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.update_teacher_profile(uuid.uuid4(), bio="New bio")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_teacher_profile_success(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_teacher = self._make_teacher_mock()
        mock_teacher.bio = "Old bio"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_teacher
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        _result = await service.update_teacher_profile(mock_teacher.id, bio="New bio")
        assert mock_teacher.bio == "New bio"
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_verify_teacher_approved(self):
        from services.teacher_service import (
            TeacherService,
            TeacherStatus,
            VerificationStatus,
        )

        mock_db = _make_mock_db()
        mock_teacher = self._make_teacher_mock()
        mock_teacher.status = None
        mock_teacher.verification_status = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_teacher
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        admin_id = uuid.uuid4()
        _result = await service.verify_teacher(
            mock_teacher.id, verified_by=admin_id, approved=True
        )
        assert mock_teacher.status == TeacherStatus.VERIFIED
        assert mock_teacher.verification_status == VerificationStatus.APPROVED
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_verify_teacher_rejected(self):
        from services.teacher_service import (
            TeacherService,
            TeacherStatus,
            VerificationStatus,
        )

        mock_db = _make_mock_db()
        mock_teacher = self._make_teacher_mock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_teacher
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        _result = await service.verify_teacher(
            mock_teacher.id,
            verified_by=uuid.uuid4(),
            approved=False,
            rejection_reason="Eksik belge",
        )
        assert mock_teacher.status == TeacherStatus.REJECTED
        assert mock_teacher.verification_status == VerificationStatus.REJECTED
        assert mock_teacher.rejection_reason == "Eksik belge"

    @pytest.mark.asyncio
    async def test_verify_teacher_not_found_returns_none(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.verify_teacher(
            uuid.uuid4(), verified_by=uuid.uuid4(), approved=True
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_search_teachers_returns_list(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_teacher = self._make_teacher_mock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_teacher]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        results = await service.search_teachers(city="Istanbul", limit=10)
        assert isinstance(results, list)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_add_expertise_adds_to_db(self):
        from services.teacher_service import SubjectExpertise, TeacherService

        mock_db = _make_mock_db()
        service = TeacherService(mock_db)

        teacher_id = uuid.uuid4()
        _expertise = await service.add_expertise(
            teacher_id=teacher_id,
            subject=SubjectExpertise.MATHEMATICS,
            grade_levels=["11", "12"],
            proficiency_level="expert",
            years_teaching_subject=5,
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_teacher_expertise_returns_list(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_exp = MagicMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_exp]
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.get_teacher_expertise(uuid.uuid4())
        assert isinstance(result, list)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_delete_expertise_success(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.delete_expertise(uuid.uuid4())
        assert result is True
        mock_db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_delete_expertise_not_found_returns_false(self):
        from services.teacher_service import TeacherService

        mock_db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = TeacherService(mock_db)
        result = await service.delete_expertise(uuid.uuid4())
        assert result is False


# ===========================================================================
# SECTION 5: api/diary_api.py — helper / pure functions
# ===========================================================================


class TestDiaryHelpers:
    """Tests for pure helper functions in diary_api."""

    @pytest.fixture(autouse=True)
    def unpoison_diary_schemas(self):
        import sys
        from unittest.mock import MagicMock, Mock

        if "api.schemas.diary" in sys.modules and isinstance(
            sys.modules["api.schemas.diary"], Mock | MagicMock
        ):
            del sys.modules["api.schemas.diary"]

    def _make_goal_mock(self):
        from models.diary import GoalStatus

        goal = MagicMock()
        goal.id = uuid.uuid4()
        goal.user_id = uuid.uuid4()
        goal.title = "Matematik Hedefi"
        goal.description = "Her gun 2 saat matematik"
        goal.progress = 50.0
        goal.current_value = 50.0
        goal.target_value = 100.0
        goal.unit = "soru"
        goal.status = GoalStatus.ACTIVE
        goal.milestones = []
        goal.is_at_risk = False
        goal.risk_factors = []
        goal.velocity = 1.5
        goal.predicted_completion = None
        goal.start_date = date.today()  # noqa: DTZ011
        goal.target_date = date.today()  # noqa: DTZ011
        goal.completed_at = None
        goal.category = "akademik"
        goal.priority = 3
        goal.days_remaining = 30
        goal.created_at = datetime.now()
        goal.updated_at = datetime.now()
        return goal

    def test_goal_to_response_basic(self):
        from api.diary_api import _goal_to_response

        goal = self._make_goal_mock()
        response = _goal_to_response(goal)
        assert response.title == "Matematik Hedefi"
        assert response.progress == 50.0

    def test_goal_to_response_with_milestones(self):
        from api.diary_api import _goal_to_response

        goal = self._make_goal_mock()
        goal.milestones = [
            {"percentage": 25, "title": "Milestone 1", "achieved": False}
        ]
        response = _goal_to_response(goal)
        assert len(response.milestones) == 1
        assert response.milestones[0].percentage == 25

    def test_goal_to_response_no_days_remaining_attr(self):
        from api.diary_api import _goal_to_response

        goal = self._make_goal_mock()
        del goal.days_remaining
        response = _goal_to_response(goal)
        assert response.days_remaining == 0

    def _make_insight_mock(self):
        from api.schemas.diary import InsightCategory

        insight = MagicMock()
        insight.id = uuid.uuid4()
        insight.diary_entry_id = uuid.uuid4()
        insight.user_id = uuid.uuid4()
        insight.category = InsightCategory.TECHNICAL
        insight.pattern = "Sabah verimli"
        insight.confidence = 0.9
        insight.evidence_count = 5
        insight.recommendation = "Sabah calis"
        insight.priority = 2
        insight.root_cause = None
        insight.correlation = None
        insight.created_at = datetime.now()
        return insight

    def test_insight_to_response(self):
        from api.diary_api import _insight_to_response
        from api.schemas.diary import InsightCategory

        insight = self._make_insight_mock()
        response = _insight_to_response(insight)
        assert response.category == InsightCategory.TECHNICAL
        assert response.confidence == 0.9

    def _make_reflection_mock(self):
        from api.schemas.diary import ReflectionDepth

        reflection = MagicMock()
        reflection.id = uuid.uuid4()
        reflection.diary_entry_id = uuid.uuid4()
        reflection.user_id = uuid.uuid4()
        reflection.what_went_well = "Iyi giden: Sorular"
        reflection.what_could_improve = "Gelistirilebilecek: Hiz"
        reflection.what_did_i_learn = "Ogrendim: Integral"
        reflection.what_will_i_do_differently = "Degistirecegim: Tempo"
        reflection.additional_notes = None
        reflection.depth = ReflectionDepth.DEEP
        reflection.depth_score = 0.85
        reflection.extracted_learnings = ["Integral kavramı"]
        reflection.action_items = []
        reflection.created_at = datetime.now()
        reflection.updated_at = datetime.now()
        return reflection

    def test_reflection_to_response(self):
        from api.diary_api import _reflection_to_response
        from api.schemas.diary import ReflectionDepth

        reflection = self._make_reflection_mock()
        response = _reflection_to_response(reflection)
        assert response.depth == ReflectionDepth.DEEP
        assert len(response.extracted_learnings) == 1

    def _make_learning_entry_mock(self):
        entry = MagicMock()
        entry.id = uuid.uuid4()
        entry.user_id = uuid.uuid4()
        entry.title = "Integral Ogrendim"
        entry.content = "Integral hesaplama yontemleri"
        entry.summary = "Kisa ozet"
        entry.tags = ["matematik", "integral"]
        entry.domain = "matematik"
        entry.skill_type = "analytical"
        entry.related_concepts = ["turev", "fonksiyon"]
        entry.next_review = None
        entry.review_count = 0
        entry.retention_score = 0.8
        entry.mastery_level = 0.6  # float
        entry.importance = 3  # int
        entry.created_at = datetime.now()
        entry.updated_at = datetime.now()
        return entry

    def test_learning_to_response(self):
        from api.diary_api import _learning_to_response

        entry = self._make_learning_entry_mock()
        response = _learning_to_response(entry)
        assert response.title == "Integral Ogrendim"
        assert "matematik" in response.tags

    def _make_emotional_state_mock(self):
        state = MagicMock()
        state.id = uuid.uuid4()
        state.user_id = uuid.uuid4()
        state.timestamp = datetime.now()
        state.confidence_level = 7  # int
        state.frustration_score = 0.3
        state.retry_count = 2
        state.error_count = 1
        state.flow_state = True
        state.productivity_score = 0.8
        state.tasks_completed = 5
        state.task_type = "solving"
        state.trigger_factors = {"time": "morning"}
        state.self_awareness_score = 0.75
        return state

    def test_emotional_to_response(self):
        from api.diary_api import _emotional_to_response

        state = self._make_emotional_state_mock()
        response = _emotional_to_response(state)
        assert response.confidence_level == 7
        assert response.flow_state is True


class TestDiaryAPIEndpoints:
    """HTTP endpoint tests for diary_api."""

    def _build_diary_app(self, diary_service_mock=None):
        """Build a minimal FastAPI app with diary router."""
        from api.diary_api import get_current_user, router
        from core.database import get_db

        app = FastAPI()
        fake_user = _make_diary_user()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()
        app.include_router(router)
        return app, fake_user

    @pytest.mark.asyncio
    async def test_get_goals_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.goal_service import GoalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(GoalService, "get_goals", AsyncMock(return_value=[])):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/goals")
                assert resp.status_code == 200
                assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_active_goals_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.goal_service import GoalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(GoalService, "get_active_goals", AsyncMock(return_value=[])):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/goals/active")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_goal_statistics_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.goal_service import GoalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        stats = {"total": 5, "completed": 2}
        with patch.object(
            GoalService, "get_goal_statistics", AsyncMock(return_value=stats)
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/goals/statistics")
                assert resp.status_code == 200
                assert resp.json()["total"] == 5

    @pytest.mark.asyncio
    async def test_get_insights_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.insight_service import InsightService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(InsightService, "get_insights", AsyncMock(return_value=[])):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/insights")
                assert resp.status_code == 200
                assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_reflections_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.reflection_service import ReflectionService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(
            ReflectionService, "get_reflections", AsyncMock(return_value=[])
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/reflections")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_emotional_states_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.emotional_service import EmotionalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(EmotionalService, "get_states", AsyncMock(return_value=[])):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/emotional")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_learning_entries_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.learning_journal_service import LearningJournalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(
            LearningJournalService, "get_entries", AsyncMock(return_value=[])
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/learning")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_exports_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.export_service import ExportService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(ExportService, "get_exports", AsyncMock(return_value=[])):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/exports")
                assert resp.status_code == 200
                assert resp.json() == []

    @pytest.mark.asyncio
    async def test_get_peer_comparison_history_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        # diary_api calls service.get_comparison_history — patch the whole service
        with patch("api.diary_api.PeerComparisonService") as MockSvc:
            inst = MockSvc.return_value
            inst.get_comparison_history = AsyncMock(return_value=[])
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/peer-comparison/history")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_due_reviews_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.learning_journal_service import LearningJournalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(
            LearningJournalService, "get_due_reviews", AsyncMock(return_value=[])
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/learning/review")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_at_risk_goals_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.goal_service import GoalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(GoalService, "get_at_risk_goals", AsyncMock(return_value=[])):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/goals/at-risk")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_frustration_alerts_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch("api.diary_api.EmotionalService") as MockSvc:
            inst = MockSvc.return_value
            inst.get_frustration_alerts = AsyncMock(return_value=[])
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/emotional/frustration-alerts")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_knowledge_graph_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.learning_journal_service import LearningJournalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(
            LearningJournalService,
            "get_knowledge_graph",
            AsyncMock(return_value={"nodes": [], "edges": []}),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/learning/graph")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_knowledge_gaps_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db
        from services.learning_journal_service import LearningJournalService

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch.object(
            LearningJournalService, "detect_gaps", AsyncMock(return_value=[])
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/diary/learning/gaps")
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_for_insights_returns_200(self):
        from api.diary_api import get_current_user, router
        from core.database import get_db

        fake_user = _make_diary_user()
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: _make_mock_db()
        app.include_router(router)

        with patch("api.diary_api.InsightService") as MockSvc:
            inst = MockSvc.return_value
            inst.analyze_and_generate_insights = AsyncMock(return_value=[])
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/v1/diary/insights/analyze")
                assert resp.status_code == 200
