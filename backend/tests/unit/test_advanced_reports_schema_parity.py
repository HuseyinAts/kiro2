"""Schema parity tests for S196 Day 3 mock→real wiring.

Asserts that every ``_real`` implementation in ``api.advanced_reports``
returns the SAME top-level key set as its ``_mock`` counterpart, so that
flipping ``mock_endpoint_flags.json`` cannot break the frontend contract.

These tests use ``unittest.mock`` to stub DB sessions and services — they
do NOT require a live database. The intent is regression coverage on the
mock-real contract, not service-level behaviour (covered elsewhere).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from models import SinavSonucu, SinavTipi
from models.exam import KonuPerformansi


def _make_temel_sonuc() -> SinavSonucu:
    """Minimal 2-konu exam result used as fixture for parity tests."""
    return SinavSonucu(
        sonuc_id="test-1",
        sinav_id="s1",
        ogrenci_id="o1",
        sinav_tipi=SinavTipi.TYT,
        toplam_soru=40,
        dogru_sayisi=30,
        yanlis_sayisi=8,
        bos_sayisi=2,
        net_sayisi=28.0,
        ham_puan=70.0,
        konu_performanslari=[
            KonuPerformansi(
                konu="Matematik",
                toplam_soru=20,
                dogru_sayisi=15,
                yanlis_sayisi=4,
                bos_sayisi=1,
                basari_yuzdesi=75.0,
            ),
            KonuPerformansi(
                konu="Türkçe",
                toplam_soru=20,
                dogru_sayisi=15,
                yanlis_sayisi=4,
                bos_sayisi=1,
                basari_yuzdesi=75.0,
            ),
        ],
        zayif_konular=["Türkçe"],
        guclu_konular=["Matematik"],
    )


@pytest.mark.asyncio
async def test_zpd_real_keys_match_mock():
    """``_get_zpd_analizi_real`` must emit the same top-level keys as mock."""
    from api.advanced_reports import (
        _get_zpd_analizi_mock,
        _get_zpd_analizi_real,
    )

    temel = _make_temel_sonuc()
    mock_result = await _get_zpd_analizi_mock("o1", temel)

    # Stub the service call — return a TurkZPDAraligi-like object.
    fake_zpd = SimpleNamespace(
        ogrenci_id="o1",
        konu="Matematik",
        mevcut_seviye=7.5,
        alt_sinir=7.0,
        ust_sinir=9.0,
        optimal_zorluk=8.5,
        kulturel_carpan=1.2,
        maarif_uyum_katsayisi=0.8,
        grup_calismasi_bonusu=0.3,
        ogretmen_rehberlik_faktoru=0.2,
        hesaplama_guveni=0.85,
        kulturel_uyum_guveni=0.78,
    )
    with patch(
        "api.advanced_reports.zpd_maarif_service.hesapla_turk_zpd",
        new=AsyncMock(return_value=fake_zpd),
    ):
        real_result = await _get_zpd_analizi_real("o1", temel)

    assert set(real_result.keys()) == set(mock_result.keys()), (
        f"ZPD schema drift: real-only={set(real_result) - set(mock_result)}, "
        f"mock-only={set(mock_result) - set(real_result)}"
    )


@pytest.mark.asyncio
async def test_learning_style_real_keys_match_mock():
    """``_get_hibrit_ogrenme_stili_analizi_real`` must match mock keys."""
    from api.advanced_reports import (
        _get_hibrit_ogrenme_stili_analizi_mock,
        _get_hibrit_ogrenme_stili_analizi_real,
    )

    temel = _make_temel_sonuc()
    mock_result = await _get_hibrit_ogrenme_stili_analizi_mock("o1", temel)

    fake_profile = {
        "vark_visual": 0.7,
        "vark_auditory": 0.5,
        "vark_reading": 0.8,
        "vark_kinesthetic": 0.4,
        "felder_active_reflective": 0.3,
        "felder_sensing_intuitive": -0.2,
        "felder_visual_verbal": 0.6,
        "felder_sequential_global": -0.4,
        "hybrid_code": "V-R-A-S-V-S",
        "dominant_vark_style": "reading",
        "dominant_felder_dimension": "visual_verbal",
        "confidence_score": 0.82,
        "profile_description": "test profile",
    }

    @asynccontextmanager
    async def _fake_ctx():
        yield AsyncMock()

    with (
        patch(
            "api.advanced_reports.learning_style_service.detect_learning_style",
            new=AsyncMock(return_value=fake_profile),
        ),
        patch("core.database.get_db_session_context", new=_fake_ctx),
    ):
        real_result = await _get_hibrit_ogrenme_stili_analizi_real("o1", temel)

    assert set(real_result.keys()) == set(mock_result.keys()), (
        f"LearningStyle schema drift: real-only={set(real_result) - set(mock_result)}, "
        f"mock-only={set(mock_result) - set(real_result)}"
    )


@pytest.mark.asyncio
async def test_osym_ets_real_keys_match_mock():
    """``_get_osym_ets_karsilastirmasi_real`` must match mock keys.

    Also verifies the nested ``osym_karsilastirma`` / ``ets_karsilastirma``
    structure — these are the IRT comparison payloads the frontend reads.
    """
    from api.advanced_reports import (
        _get_osym_ets_karsilastirmasi_mock,
        _get_osym_ets_karsilastirmasi_real,
    )

    temel = _make_temel_sonuc()
    mock_result = await _get_osym_ets_karsilastirmasi_mock("s1", temel)

    fake_agg = {
        "avg_difficulty": 0.5,
        "avg_discrimination": 1.0,
        "avg_guessing": 0.2,
        "sample_size": 100,
    }
    with patch(
        "api.advanced_reports._get_subject_irt_aggregate",
        new=AsyncMock(return_value=fake_agg),
    ):
        real_result = await _get_osym_ets_karsilastirmasi_real("s1", temel)

    assert set(real_result.keys()) == set(mock_result.keys()), (
        f"OSYM-ETS schema drift: real-only={set(real_result) - set(mock_result)}, "
        f"mock-only={set(mock_result) - set(real_result)}"
    )
    # Nested contract — these are what the frontend renders.
    for nested in ("osym_karsilastirma", "ets_karsilastirma"):
        assert set(real_result[nested].keys()) == set(mock_result[nested].keys()), (
            f"{nested} nested drift"
        )


@pytest.mark.asyncio
async def test_performance_trend_real_keys_match_mock():
    """``_get_performance_trend_real`` must match mock keys.

    Empty-data path (no ExamSession found) — exercises the early-return
    branch which is the only deterministic path without a real DB.
    """
    from api.advanced_reports import (
        _get_performance_trend_mock,
        _get_performance_trend_real,
    )

    mock_result = await _get_performance_trend_mock("o1", SinavTipi.TYT)

    # Mock DB query → returns None (no exam session) → empty_response branch.
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock(
        return_value=SimpleNamespace(scalar_one_or_none=lambda: None)
    )

    @asynccontextmanager
    async def _fake_ctx():
        yield fake_db

    with patch("core.database.get_db_session_context", new=_fake_ctx):
        real_result = await _get_performance_trend_real("o1", SinavTipi.TYT)

    assert set(real_result.keys()) == set(mock_result.keys()), (
        f"PerfTrend schema drift: real-only={set(real_result) - set(mock_result)}, "
        f"mock-only={set(mock_result) - set(real_result)}"
    )
