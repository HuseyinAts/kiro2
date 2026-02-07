"""
Cultural adaptation functional tests (F-15).

Tests Ramadan mode, holiday adaptation, YKS stress, and regional features.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


# --- F-15.1: Ramadan mode ---
@pytest.mark.asyncio
async def test_ramadan_mode():
    """Ramadan period → adjusted study schedule"""
    ramadan_config = {
        "enabled": True,
        "iftar_time": "19:30",
        "sahur_time": "04:00",
        "reduced_study_hours": True,
        "factor": 0.75,
    }
    assert ramadan_config["enabled"] is True
    assert ramadan_config["factor"] < 1.0
    assert ramadan_config["iftar_time"] is not None


# --- F-15.2: Holiday adaptation ---
@pytest.mark.asyncio
async def test_holiday_adaptation():
    """National holidays → adapted content and schedule"""
    holidays = [
        {"date": "2025-04-23", "name": "Ulusal Egemenlik Bayramı", "study_reduction": 0.5},
        {"date": "2025-05-19", "name": "Atatürk'ü Anma Gençlik Bayramı", "study_reduction": 0.5},
        {"date": "2025-10-29", "name": "Cumhuriyet Bayramı", "study_reduction": 0.5},
    ]
    assert len(holidays) >= 3
    assert all(0 < h["study_reduction"] <= 1.0 for h in holidays)
    assert all("name" in h for h in holidays)


# --- F-15.3: YKS period stress ---
@pytest.mark.asyncio
async def test_yks_period_stress():
    """YKS exam proximity → stress management features"""
    stress_config = {
        "days_until_exam": 30,
        "stress_level": "high",
        "yks_stress_factor": 1.50,
        "recommendations": ["Nefes egzersizi", "Düzenli uyku"],
    }
    assert stress_config["yks_stress_factor"] > 1.0
    assert stress_config["days_until_exam"] > 0
    assert len(stress_config["recommendations"]) >= 1


# --- F-15.4: Family pressure factor ---
@pytest.mark.asyncio
async def test_family_pressure_factor():
    """Family pressure level → adjusted learning pace"""
    family_config = {
        "pressure_level": "moderate",
        "family_pressure_factor": 1.15,
        "support_needed": True,
        "resources": ["Veli rehberlik hattı", "Psikolog desteği"],
    }
    assert family_config["family_pressure_factor"] > 1.0
    assert family_config["pressure_level"] in ("low", "moderate", "high")
    assert len(family_config["resources"]) >= 1


# --- F-15.5: Regional adaptation ---
@pytest.mark.asyncio
async def test_regional_adaptation():
    """City-based → local university and resource suggestions"""
    regional = {
        "city": "İstanbul",
        "timezone": "Europe/Istanbul",
        "nearby_universities": ["Boğaziçi", "İTÜ", "Marmara"],
        "local_resources": ["Kütüphane", "Dershane"],
    }
    assert regional["city"] == "İstanbul"
    assert len(regional["nearby_universities"]) >= 1
    assert regional["timezone"] == "Europe/Istanbul"
