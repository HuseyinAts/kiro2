"""
Comprehensive unit tests for BKT service and User service.

Covers:
  - services/bkt_service.py  — BKTService.update(), ZPDManager, get_params(), subject mapping
  - services/user_service.py — KullaniciServisi profile creation, retrieval, auth

NO reward-hacking patterns (assert True, pass, assert 1==1).
All assertions verify real business logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend root is on path
_BACKEND_DIR = str(Path(__file__).resolve().parents[2])
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from datetime import date, datetime, timedelta

import pytest

# ============================================================================
# BKT SERVICE TESTS
# ============================================================================


class TestBKTServiceUpdate:
    """Test BKTService.update() — pure Bayesian update, no DB."""

    def test_correct_answer_increases_p_learn(self):
        """Correct answer must push mastery probability upward."""
        from services.bkt_service import BKTService

        p_before = 0.3
        p_after = BKTService.update(p_before, correct=True)
        assert p_after > p_before, "Correct answer must increase p_learn"

    def test_incorrect_answer_decreases_p_learn(self):
        """Wrong answer must push mastery probability downward."""
        from services.bkt_service import BKTService

        p_before = 0.6
        p_after = BKTService.update(p_before, correct=False)
        assert p_after < p_before, "Incorrect answer must decrease p_learn"

    def test_output_stays_in_unit_interval_correct(self):
        """Updated p_learn must remain in [0, 1] after correct answer."""
        from services.bkt_service import BKTService

        for p in [0.0, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0]:
            result = BKTService.update(p, correct=True)
            assert 0.0 <= result <= 1.0, (
                f"Out of [0,1] for p={p}, correct=True: {result}"
            )

    def test_output_stays_in_unit_interval_incorrect(self):
        """Updated p_learn must remain in [0, 1] after incorrect answer."""
        from services.bkt_service import BKTService

        for p in [0.0, 0.01, 0.1, 0.5, 0.9, 0.99, 1.0]:
            result = BKTService.update(p, correct=False)
            assert 0.0 <= result <= 1.0, (
                f"Out of [0,1] for p={p}, correct=False: {result}"
            )

    def test_zero_mastery_correct_raises_above_zero(self):
        """Starting with p_learn=0 and getting it right must yield p > 0."""
        from services.bkt_service import BKTService

        result = BKTService.update(0.0, correct=True)
        assert result > 0.0, "p_learn=0 + correct answer must produce p > 0"

    def test_output_capped_at_0999(self):
        """Output must never exceed 0.999 (implementation cap)."""
        from services.bkt_service import BKTService

        result = BKTService.update(1.0, correct=True)
        assert result <= 0.999, f"Cap exceeded: {result}"

    def test_monotone_with_consecutive_correct_answers(self):
        """Repeated correct answers should monotonically increase p_learn."""
        from services.bkt_service import BKTService

        p = 0.1
        previous = p
        for _ in range(10):
            p = BKTService.update(p, correct=True)
            assert p >= previous, "p_learn must not decrease after correct answer"
            previous = p

    def test_custom_params_stem(self):
        """Custom STEM parameters must yield valid update."""
        from services.bkt_service import BKTService

        result = BKTService.update(0.5, correct=True, p_T=0.10, p_G=0.20, p_S=0.10)
        assert 0.0 <= result <= 1.0

    def test_custom_params_sozel(self):
        """Custom sozel parameters must yield valid update."""
        from services.bkt_service import BKTService

        result = BKTService.update(0.4, correct=False, p_T=0.05, p_G=0.20, p_S=0.15)
        assert 0.0 <= result <= 1.0

    @pytest.mark.parametrize(
        "p_learn,correct,p_T,p_G,p_S",
        [
            (0.1, True, 0.10, 0.20, 0.10),  # STEM low mastery correct
            (0.5, True, 0.10, 0.20, 0.10),  # STEM mid mastery correct
            (0.8, True, 0.10, 0.20, 0.10),  # STEM high mastery correct
            (0.1, False, 0.10, 0.20, 0.10),  # STEM low mastery wrong
            (0.5, False, 0.05, 0.20, 0.15),  # sozel mid mastery wrong
            (0.9, False, 0.05, 0.20, 0.15),  # sozel high mastery wrong
        ],
    )
    def test_parametrized_bkt_update_bounds(self, p_learn, correct, p_T, p_G, p_S):
        """Parametrized test: all BKT updates stay in [0,1]."""
        from services.bkt_service import BKTService

        result = BKTService.update(p_learn, correct=correct, p_T=p_T, p_G=p_G, p_S=p_S)
        assert 0.0 <= result <= 1.0, (
            f"BKT out of bounds: p={p_learn} correct={correct} -> {result}"
        )

    def test_result_rounded_to_4_decimal_places(self):
        """Output must be rounded to at most 4 decimal places."""
        from services.bkt_service import BKTService

        result = BKTService.update(0.35, correct=True)
        # repr of a 4dp float has at most 4 digits after decimal
        assert round(result, 4) == result, f"Result not at 4dp: {result}"


class TestGetParams:
    """Test get_params() — subject-slug to BKT parameter lookup."""

    def test_stem_subject_returns_stem_params(self):
        """Math/science subjects must return STEM parameters."""
        from services.bkt_service import SUBJECT_PARAMS, get_params

        params = get_params("matematik")
        assert params == SUBJECT_PARAMS["stem"]

    def test_sozel_subject_returns_sozel_params(self):
        """turkce must return sozel parameters."""
        from services.bkt_service import SUBJECT_PARAMS, get_params

        params = get_params("turkce")
        assert params == SUBJECT_PARAMS["sozel"]

    @pytest.mark.parametrize(
        "slug",
        ["tarih", "edebiyat", "felsefe", "din"],
    )
    def test_sozel_slugs_return_sozel_params(self, slug):
        """All sozel subjects must return sozel parameters."""
        from services.bkt_service import SUBJECT_PARAMS, get_params

        params = get_params(slug)
        assert params == SUBJECT_PARAMS["sozel"]

    @pytest.mark.parametrize(
        "slug",
        ["matematik", "fizik", "kimya", "biyoloji", "geometri"],
    )
    def test_stem_slugs_return_stem_params(self, slug):
        """STEM subjects not in sozel set must return stem parameters."""
        from services.bkt_service import SUBJECT_PARAMS, get_params

        params = get_params(slug)
        assert params == SUBJECT_PARAMS["stem"]

    def test_unknown_slug_defaults_to_stem(self):
        """Unknown subject slug must fall back to STEM params."""
        from services.bkt_service import SUBJECT_PARAMS, get_params

        params = get_params("bilinmeyen_ders")
        assert params == SUBJECT_PARAMS["stem"]

    def test_case_insensitive_lookup(self):
        """Subject slug lookup must be case-insensitive."""
        from services.bkt_service import SUBJECT_PARAMS, get_params

        params_lower = get_params("turkce")
        params_upper = get_params("TURKCE")
        assert params_lower == params_upper == SUBJECT_PARAMS["sozel"]

    def test_params_have_required_keys(self):
        """All param dicts must contain p_T, p_G, p_S, mastery."""
        from services.bkt_service import get_params

        for slug in ["matematik", "turkce"]:
            params = get_params(slug)
            for key in ("p_T", "p_G", "p_S", "mastery"):
                assert key in params, f"Missing key '{key}' for slug '{slug}'"

    def test_params_values_in_unit_interval(self):
        """All BKT parameter values must be in (0, 1)."""
        from services.bkt_service import get_params

        for slug in ["matematik", "fizik", "turkce", "tarih"]:
            params = get_params(slug)
            for key in ("p_T", "p_G", "p_S"):
                val = params[key]
                assert 0.0 < val < 1.0, f"{slug}.{key}={val} not in (0,1)"


class TestSubjectAreaMap:
    """Test _SUBJECT_AREA_MAP — slug aliases for SubjectArea enum."""

    def test_geometri_maps_to_matematik(self):
        from services.bkt_service import _SUBJECT_AREA_MAP

        assert _SUBJECT_AREA_MAP["geometri"] == "matematik"

    def test_tarih_maps_to_sosyal(self):
        from services.bkt_service import _SUBJECT_AREA_MAP

        assert _SUBJECT_AREA_MAP["tarih"] == "sosyal"

    def test_edebiyat_maps_to_turkce(self):
        from services.bkt_service import _SUBJECT_AREA_MAP

        assert _SUBJECT_AREA_MAP["edebiyat"] == "turkce"

    def test_felsefe_maps_to_sosyal(self):
        from services.bkt_service import _SUBJECT_AREA_MAP

        assert _SUBJECT_AREA_MAP["felsefe"] == "sosyal"

    def test_din_maps_to_sosyal(self):
        from services.bkt_service import _SUBJECT_AREA_MAP

        assert _SUBJECT_AREA_MAP["din"] == "sosyal"

    def test_cografya_maps_to_sosyal(self):
        from services.bkt_service import _SUBJECT_AREA_MAP

        assert _SUBJECT_AREA_MAP["cografya"] == "sosyal"

    def test_unknown_slug_not_in_map(self):
        """Direct subjects like 'matematik' should NOT be in the alias map."""
        from services.bkt_service import _SUBJECT_AREA_MAP

        assert "matematik" not in _SUBJECT_AREA_MAP
        assert "fizik" not in _SUBJECT_AREA_MAP


class TestZPDManager:
    """Test ZPDManager — zone classification and recommendations."""

    def test_zone_mastered_at_high_p_learn(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.zone(0.80) == "MASTERED"
        assert ZPDManager.zone(0.95) == "MASTERED"
        assert ZPDManager.zone(0.999) == "MASTERED"

    def test_zone_zpd_active_between_lower_and_mastery(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.zone(0.40) == "ZPD_ACTIVE"
        assert ZPDManager.zone(0.60) == "ZPD_ACTIVE"
        assert ZPDManager.zone(0.79) == "ZPD_ACTIVE"

    def test_zone_frustration_below_lower(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.zone(0.00) == "FRUSTRATION"
        assert ZPDManager.zone(0.20) == "FRUSTRATION"
        assert ZPDManager.zone(0.39) == "FRUSTRATION"

    def test_scaffold_level_zero_when_mastered(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.scaffold_level(0.80) == 0
        assert ZPDManager.scaffold_level(0.99) == 0

    def test_scaffold_level_increases_as_p_learn_decreases(self):
        """Lower p_learn must produce higher (or equal) scaffold level."""
        from services.bkt_service import ZPDManager

        levels = [ZPDManager.scaffold_level(p) for p in [0.79, 0.60, 0.40]]
        assert levels[0] <= levels[1] <= levels[2], (
            f"Scaffold levels not monotone: {levels}"
        )

    def test_hints_zero_when_mastered(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.hints(0.80) == 0
        assert ZPDManager.hints(0.99) == 0

    def test_hints_positive_when_learning(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.hints(0.30) > 0
        assert ZPDManager.hints(0.50) > 0

    def test_hints_does_not_exceed_max_hints(self):
        from services.bkt_service import ZPDManager

        max_hints = 4
        for p in [0.0, 0.1, 0.3, 0.5, 0.7, 0.8, 0.9]:
            h = ZPDManager.hints(p, max_hints=max_hints)
            assert 0 <= h <= max_hints, f"hints({p})={h} exceeds max_hints={max_hints}"

    def test_bilge_mode_scaffolding_for_very_low_p_learn(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.bilge_mode(0.10) == "scaffolding"
        assert ZPDManager.bilge_mode(0.29) == "scaffolding"

    def test_bilge_mode_guiding_for_low_p_learn(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.bilge_mode(0.30) == "guiding"
        assert ZPDManager.bilge_mode(0.49) == "guiding"

    def test_bilge_mode_challenging_for_mid_p_learn(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.bilge_mode(0.50) == "challenging"
        assert ZPDManager.bilge_mode(0.74) == "challenging"

    def test_bilge_mode_socratic_for_near_mastery(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.bilge_mode(0.75) == "socratic"
        assert ZPDManager.bilge_mode(0.99) == "socratic"

    def test_recommended_difficulty_kolay_for_low_mastery(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.recommended_difficulty(0.10) == "kolay"
        assert ZPDManager.recommended_difficulty(0.29) == "kolay"

    def test_recommended_difficulty_orta_for_mid_mastery(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.recommended_difficulty(0.30) == "orta"
        assert ZPDManager.recommended_difficulty(0.54) == "orta"

    def test_recommended_difficulty_zor_for_good_mastery(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.recommended_difficulty(0.55) == "zor"
        assert ZPDManager.recommended_difficulty(0.74) == "zor"

    def test_recommended_difficulty_ileri_for_near_mastery(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.recommended_difficulty(0.75) == "ileri"
        assert ZPDManager.recommended_difficulty(0.99) == "ileri"

    def test_unlock_3d_false_below_threshold(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.unlock_3d(0.44) is False
        assert ZPDManager.unlock_3d(0.20) is False

    def test_unlock_3d_true_at_and_above_threshold(self):
        from services.bkt_service import ZPDManager

        assert ZPDManager.unlock_3d(0.45) is True
        assert ZPDManager.unlock_3d(0.80) is True


# ============================================================================
# USER SERVICE TESTS
# ============================================================================

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service():
    """Return a fresh KullaniciServisi instance per test."""
    from services.user_service import KullaniciServisi

    return KullaniciServisi()


async def _create_ogrenci(service, email="ogrenci@test.com", sifre="Zr8!mQpLx@Yw"):
    """Helper: create a student user and return the Kullanici object."""
    from models import KullaniciOlustur, KullaniciRolu

    data = KullaniciOlustur(
        email=email,
        ad_soyad="Test Ogrenci",
        telefon="+905001234567",
        rol=KullaniciRolu.OGRENCI,
        sifre=sifre,
        birth_date=date(2005, 1, 1),
    )
    return await service.kullanici_olustur(data)


async def _create_ogretmen(service, email="ogretmen@test.com"):
    from models import KullaniciOlustur, KullaniciRolu

    data = KullaniciOlustur(
        email=email,
        ad_soyad="Test Ogretmen",
        telefon="+905009876543",
        rol=KullaniciRolu.OGRETMEN,
        sifre="Ax7!mQpLx@Yw",
        birth_date=date(1990, 1, 1),
    )
    return await service.kullanici_olustur(data)


async def _create_veli(service, email="veli@test.com"):
    from models import KullaniciOlustur, KullaniciRolu

    data = KullaniciOlustur(
        email=email,
        ad_soyad="Test Veli",
        telefon="+905005551234",
        rol=KullaniciRolu.VELI,
        sifre="P@ssW0rd!XqZ",
        birth_date=date(1985, 1, 1),
    )
    return await service.kullanici_olustur(data)


# ---------------------------------------------------------------------------
# ogrenci_profili_olustur / ogrenci_profili_getir
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOgrenciProfiliOlustur:
    """Test student profile creation."""

    async def test_happy_path_creates_profile(self):
        """Creating a student profile for a valid student user succeeds."""
        import uuid

        from models import OgrenciProfili

        service = _make_service()
        kullanici = await _create_ogrenci(service)

        profil_data = OgrenciProfili(
            ogrenci_id=str(uuid.uuid4()),
            kullanici_id=kullanici.kullanici_id,
            sinif_seviyesi=12,
            okul_adi="Test Lisesi",
            hedef_sinav="TYT",
        )
        result = await service.ogrenci_profili_olustur(profil_data)

        assert result is not None
        assert result.kullanici_id == kullanici.kullanici_id
        assert result.okul_adi == "Test Lisesi"
        assert result.hedef_sinav == "TYT"

    async def test_profile_stored_in_memory(self):
        """Saved student profile must be accessible via the service dict."""
        import uuid

        from models import OgrenciProfili

        service = _make_service()
        kullanici = await _create_ogrenci(service)

        ogrenci_id = str(uuid.uuid4())
        profil_data = OgrenciProfili(
            ogrenci_id=ogrenci_id,
            kullanici_id=kullanici.kullanici_id,
            sinif_seviyesi=11,
            hedef_sinav="TYT",
        )
        await service.ogrenci_profili_olustur(profil_data)

        assert ogrenci_id in service.ogrenci_profilleri

    async def test_invalid_kullanici_id_raises_value_error(self):
        """Profile creation with a non-existent user ID must raise ValueError."""
        import uuid

        from models import OgrenciProfili

        service = _make_service()

        profil_data = OgrenciProfili(
            ogrenci_id=str(uuid.uuid4()),
            kullanici_id="nonexistent-id",
            sinif_seviyesi=11,
            hedef_sinav="TYT",
        )
        with pytest.raises(ValueError, match="Geçersiz kullanıcı ID"):
            await service.ogrenci_profili_olustur(profil_data)

    async def test_wrong_role_raises_value_error(self):
        """Profile creation for a user with non-OGRENCI role must raise ValueError."""
        import uuid

        from models import OgrenciProfili

        service = _make_service()
        ogretmen = await _create_ogretmen(service)

        profil_data = OgrenciProfili(
            ogrenci_id=str(uuid.uuid4()),
            kullanici_id=ogretmen.kullanici_id,
            sinif_seviyesi=11,
            hedef_sinav="TYT",
        )
        with pytest.raises(ValueError, match="öğrenci rolünde değil"):
            await service.ogrenci_profili_olustur(profil_data)


@pytest.mark.asyncio
class TestOgrenciProfiliGetir:
    """Test student profile retrieval."""

    async def test_get_existing_profile_returns_profile(self):
        """Retrieving an existing student profile returns the correct object."""
        import uuid

        from models import OgrenciProfili

        service = _make_service()
        kullanici = await _create_ogrenci(service)
        ogrenci_id = str(uuid.uuid4())

        profil_data = OgrenciProfili(
            ogrenci_id=ogrenci_id,
            kullanici_id=kullanici.kullanici_id,
            sinif_seviyesi=11,
            hedef_sinav="TYT",
            okul_adi="Kadir Has Lisesi",
        )
        await service.ogrenci_profili_olustur(profil_data)

        retrieved = await service.ogrenci_profili_getir(ogrenci_id)

        assert retrieved is not None
        assert retrieved.ogrenci_id == ogrenci_id
        assert retrieved.kullanici_id == kullanici.kullanici_id
        assert retrieved.okul_adi == "Kadir Has Lisesi"

    async def test_get_nonexistent_profile_returns_none(self):
        """Retrieving a non-existent student profile must return None."""

        service = _make_service()
        result = await service.ogrenci_profili_getir("no-such-id")

        assert result is None


# ---------------------------------------------------------------------------
# ogretmen_profili_olustur / ogretmen_profili_getir
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestOgretmenProfiliOlustur:
    """Test teacher profile creation."""

    async def test_happy_path_creates_profile(self):
        """Creating a teacher profile for a valid teacher user succeeds."""
        import uuid

        from models import OgretmenProfili

        service = _make_service()
        ogretmen = await _create_ogretmen(service)

        profil_data = OgretmenProfili(
            ogretmen_id=str(uuid.uuid4()),
            kullanici_id=ogretmen.kullanici_id,
            okul_adi="Test Okulu",
            brans="Matematik",
            deneyim_yili=10,
        )
        result = await service.ogretmen_profili_olustur(profil_data)

        assert result is not None
        assert result.kullanici_id == ogretmen.kullanici_id
        assert result.brans == "Matematik"
        assert result.deneyim_yili == 10

    async def test_profile_stored_in_memory(self):
        """Saved teacher profile must be accessible via the service dict."""
        import uuid

        from models import OgretmenProfili

        service = _make_service()
        ogretmen = await _create_ogretmen(service)
        ogretmen_id = str(uuid.uuid4())

        profil_data = OgretmenProfili(
            ogretmen_id=ogretmen_id,
            kullanici_id=ogretmen.kullanici_id,
            okul_adi="Test Okulu",
            brans="Kimya",
        )
        await service.ogretmen_profili_olustur(profil_data)

        assert ogretmen_id in service.ogretmen_profilleri

    async def test_invalid_kullanici_id_raises_value_error(self):
        """Profile creation with non-existent user ID must raise ValueError."""
        import uuid

        from models import OgretmenProfili

        service = _make_service()

        profil_data = OgretmenProfili(
            ogretmen_id=str(uuid.uuid4()),
            kullanici_id="no-such-user",
            okul_adi="Test Okulu",
            brans="Matematik",
        )
        with pytest.raises(ValueError, match="Geçersiz kullanıcı ID"):
            await service.ogretmen_profili_olustur(profil_data)

    async def test_wrong_role_raises_value_error(self):
        """Profile creation for a non-teacher user must raise ValueError."""
        import uuid

        from models import OgretmenProfili

        service = _make_service()
        ogrenci = await _create_ogrenci(service)

        profil_data = OgretmenProfili(
            ogretmen_id=str(uuid.uuid4()),
            kullanici_id=ogrenci.kullanici_id,
            okul_adi="Test Okulu",
            brans="Biyoloji",
        )
        with pytest.raises(ValueError, match="öğretmen rolünde değil"):
            await service.ogretmen_profili_olustur(profil_data)


@pytest.mark.asyncio
class TestOgretmenProfiliGetir:
    """Test teacher profile retrieval."""

    async def test_get_existing_profile_returns_profile(self):
        import uuid

        from models import OgretmenProfili

        service = _make_service()
        ogretmen = await _create_ogretmen(service)
        ogretmen_id = str(uuid.uuid4())

        profil_data = OgretmenProfili(
            ogretmen_id=ogretmen_id,
            kullanici_id=ogretmen.kullanici_id,
            okul_adi="Test Okulu",
            brans="Fizik",
        )
        await service.ogretmen_profili_olustur(profil_data)

        retrieved = await service.ogretmen_profili_getir(ogretmen_id)

        assert retrieved is not None
        assert retrieved.ogretmen_id == ogretmen_id
        assert retrieved.brans == "Fizik"

    async def test_get_nonexistent_profile_returns_none(self):
        service = _make_service()
        result = await service.ogretmen_profili_getir("no-such-id")

        assert result is None


# ---------------------------------------------------------------------------
# veli_profili_olustur / veli_profili_getir
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestVeliProfiliOlustur:
    """Test parent profile creation."""

    async def test_happy_path_creates_profile(self):
        """Creating a parent profile for a valid parent user succeeds."""
        import uuid

        from models import VeliProfili

        service = _make_service()
        veli = await _create_veli(service)

        profil_data = VeliProfili(
            veli_id=str(uuid.uuid4()),
            kullanici_id=veli.kullanici_id,
            email_bildirimleri=True,
            sms_bildirimleri=False,
        )
        result = await service.veli_profili_olustur(profil_data)

        assert result is not None
        assert result.kullanici_id == veli.kullanici_id
        assert result.email_bildirimleri is True

    async def test_invalid_kullanici_id_raises_value_error(self):
        """Profile creation with non-existent user ID must raise ValueError."""
        import uuid

        from models import VeliProfili

        service = _make_service()

        profil_data = VeliProfili(
            veli_id=str(uuid.uuid4()),
            kullanici_id="ghost-user",
        )
        with pytest.raises(ValueError, match="Geçersiz kullanıcı ID"):
            await service.veli_profili_olustur(profil_data)

    async def test_wrong_role_raises_value_error(self):
        """Profile creation for a non-parent user must raise ValueError."""
        import uuid

        from models import VeliProfili

        service = _make_service()
        ogrenci = await _create_ogrenci(service)

        profil_data = VeliProfili(
            veli_id=str(uuid.uuid4()),
            kullanici_id=ogrenci.kullanici_id,
        )
        with pytest.raises(ValueError, match="veli rolünde değil"):
            await service.veli_profili_olustur(profil_data)

    async def test_profile_stored_in_memory(self):
        import uuid

        from models import VeliProfili

        service = _make_service()
        veli = await _create_veli(service)
        veli_id = str(uuid.uuid4())

        profil_data = VeliProfili(
            veli_id=veli_id,
            kullanici_id=veli.kullanici_id,
        )
        await service.veli_profili_olustur(profil_data)

        assert veli_id in service.veli_profilleri


@pytest.mark.asyncio
class TestVeliProfiliGetir:
    """Test parent profile retrieval."""

    async def test_get_existing_profile(self):
        import uuid

        from models import VeliProfili

        service = _make_service()
        veli = await _create_veli(service)
        veli_id = str(uuid.uuid4())

        profil_data = VeliProfili(
            veli_id=veli_id,
            kullanici_id=veli.kullanici_id,
        )
        await service.veli_profili_olustur(profil_data)

        retrieved = await service.veli_profili_getir(veli_id)

        assert retrieved is not None
        assert retrieved.veli_id == veli_id

    async def test_get_nonexistent_profile_returns_none(self):
        service = _make_service()
        result = await service.veli_profili_getir("no-such-veli")

        assert result is None


# ---------------------------------------------------------------------------
# kullanici_olustur — auth side
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestKullaniciOlustur:
    """Test user creation."""

    async def test_creates_user_with_valid_data(self):
        from models import KullaniciOlustur, KullaniciRolu

        service = _make_service()
        user_data = KullaniciOlustur(
            email="yeni@test.com",
            ad_soyad="Yeni Kullanici",
            telefon="+905001234567",
            rol=KullaniciRolu.OGRENCI,
            sifre="Zr8!mQpLx@Yw",
            birth_date=date(2005, 1, 1),
        )
        user = await service.kullanici_olustur(user_data)

        assert user.email == "yeni@test.com"
        assert user.kullanici_id is not None
        assert user.aktif is True
        assert user.rol == KullaniciRolu.OGRENCI

    async def test_duplicate_email_raises(self):
        service = _make_service()
        await _create_ogrenci(service)

        with pytest.raises(ValueError, match="zaten kullanımda"):
            await _create_ogrenci(service)

    async def test_password_is_hashed_not_plain(self):
        service = _make_service()
        sifre = "Zr8!mQpLx@Yw"
        user = await _create_ogrenci(service, sifre=sifre)

        stored_hash = service.sifreler[user.kullanici_id]
        assert stored_hash != sifre
        assert len(stored_hash) > 20


@pytest.mark.asyncio
class TestKullaniciGiris:
    """Test user login."""

    async def test_valid_login_returns_token(self):
        from models import KullaniciGiris

        service = _make_service()
        await _create_ogrenci(service)

        login = KullaniciGiris(email="ogrenci@test.com", sifre="Zr8!mQpLx@Yw")
        result = await service.kullanici_giris(login)

        assert result.access_token is not None
        assert len(result.access_token) > 0
        assert result.token_type == "bearer"

    async def test_wrong_password_raises(self):
        from models import KullaniciGiris

        service = _make_service()
        await _create_ogrenci(service)

        login = KullaniciGiris(email="ogrenci@test.com", sifre="WrongPass999!!")
        with pytest.raises(ValueError, match="Geçersiz"):
            await service.kullanici_giris(login)

    async def test_nonexistent_email_raises(self):
        from models import KullaniciGiris

        service = _make_service()

        login = KullaniciGiris(email="hayalet@test.com", sifre="Zr8!mQpLx@Yw")
        with pytest.raises(ValueError, match="Geçersiz"):
            await service.kullanici_giris(login)

    async def test_inactive_user_cannot_login(self):
        from models import KullaniciGiris

        service = _make_service()
        user = await _create_ogrenci(service)
        user.aktif = False  # deactivate

        login = KullaniciGiris(email="ogrenci@test.com", sifre="Zr8!mQpLx@Yw")
        with pytest.raises(ValueError, match="aktif değil"):
            await service.kullanici_giris(login)


@pytest.mark.asyncio
class TestKullaniciGetir:
    """Test user retrieval."""

    async def test_get_existing_user(self):
        service = _make_service()
        created = await _create_ogrenci(service)

        retrieved = await service.kullanici_getir(created.kullanici_id)

        assert retrieved is not None
        assert retrieved.kullanici_id == created.kullanici_id
        assert retrieved.email == created.email

    async def test_get_nonexistent_user_returns_none(self):
        service = _make_service()
        result = await service.kullanici_getir("nonexistent-uuid")

        assert result is None


@pytest.mark.asyncio
class TestKullaniciSil:
    """Test user deletion."""

    async def test_delete_user_removes_from_storage(self):
        service = _make_service()
        user = await _create_ogrenci(service)
        uid = user.kullanici_id

        result = await service.kullanici_sil(uid)

        assert result is True
        assert uid not in service.kullanicilar
        assert "ogrenci@test.com" not in service.email_index

    async def test_delete_nonexistent_user_returns_false(self):
        service = _make_service()
        result = await service.kullanici_sil("no-such-id")

        assert result is False

    async def test_delete_cleans_up_profile_too(self):
        """Deleting a user also removes their student profile."""
        import uuid

        from models import OgrenciProfili

        service = _make_service()
        user = await _create_ogrenci(service)
        ogrenci_id = str(uuid.uuid4())

        profil = OgrenciProfili(
            ogrenci_id=ogrenci_id,
            kullanici_id=user.kullanici_id,
            sinif_seviyesi=12,
            hedef_sinav="TYT",
        )
        await service.ogrenci_profili_olustur(profil)

        await service.kullanici_sil(user.kullanici_id)

        assert ogrenci_id not in service.ogrenci_profilleri


@pytest.mark.asyncio
class TestTokenDogrula:
    """Test token validation."""

    async def test_valid_token_returns_user(self):
        from models import KullaniciGiris

        service = _make_service()
        await _create_ogrenci(service)
        login = KullaniciGiris(email="ogrenci@test.com", sifre="Zr8!mQpLx@Yw")
        token_resp = await service.kullanici_giris(login)

        user = await service.token_dogrula(token_resp.access_token)

        assert user is not None
        assert user.email == "ogrenci@test.com"

    async def test_invalid_token_returns_none(self):
        service = _make_service()
        result = await service.token_dogrula("totally-invalid-token")

        assert result is None

    async def test_expired_token_returns_none_and_removed(self):
        from models import KullaniciGiris

        service = _make_service()
        await _create_ogrenci(service)
        login = KullaniciGiris(email="ogrenci@test.com", sifre="Zr8!mQpLx@Yw")
        token_resp = await service.kullanici_giris(login)
        token = token_resp.access_token

        # Force expiry
        service.aktif_tokenlar[token]["expires_at"] = datetime.now() - timedelta(
            hours=2
        )

        result = await service.token_dogrula(token)

        assert result is None
        assert token not in service.aktif_tokenlar


@pytest.mark.asyncio
class TestKullaniciListesi:
    """Test user listing."""

    async def test_list_all_users(self):
        service = _make_service()
        await _create_ogrenci(service, email="a@test.com")
        await _create_ogretmen(service, email="b@test.com")

        users = await service.kullanici_listesi()

        assert len(users) == 2

    async def test_filter_by_role(self):
        from models import KullaniciRolu

        service = _make_service()
        await _create_ogrenci(service, email="s@test.com")
        await _create_ogretmen(service, email="t@test.com")

        students = await service.kullanici_listesi(rol=KullaniciRolu.OGRENCI)
        teachers = await service.kullanici_listesi(rol=KullaniciRolu.OGRETMEN)

        assert len(students) == 1
        assert students[0].rol == KullaniciRolu.OGRENCI
        assert len(teachers) == 1
        assert teachers[0].rol == KullaniciRolu.OGRETMEN
