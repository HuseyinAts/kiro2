import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import SinavTipi, SinavDurumu
from services.sinav_motoru_service import SinavMotoruServisi


@pytest.mark.asyncio
async def test_sinav_motoru_init():
    """Test SinavMotoruServisi initialization"""
    service = SinavMotoruServisi()

    assert service.aktif_oturumlar == {}
    assert service.sinav_cevaplari == {}
    assert service.sinav_sonuclari == {}
    assert service.zaman_takip == {}
    assert SinavTipi.TYT in service.sinav_konfigurasyonlari
    assert SinavTipi.AYT in service.sinav_konfigurasyonlari
    assert SinavTipi.YDT in service.sinav_konfigurasyonlari


@pytest.mark.asyncio
async def test_sinav_konfigurasyonlari():
    """Test exam configurations"""
    service = SinavMotoruServisi()

    # TYT config
    tyt_config = service.sinav_konfigurasyonlari[SinavTipi.TYT]
    assert tyt_config["toplam_soru"] == 120
    assert tyt_config["sure_dakika"] == 165
    assert "konu_dagilimi" in tyt_config

    # AYT config
    ayt_config = service.sinav_konfigurasyonlari[SinavTipi.AYT]
    assert ayt_config["toplam_soru"] == 80
    assert ayt_config["sure_dakika"] == 180

    # YDT config
    ydt_config = service.sinav_konfigurasyonlari[SinavTipi.YDT]
    assert ydt_config["toplam_soru"] == 80
    assert ydt_config["sure_dakika"] == 180


@pytest.mark.asyncio
async def test_basic():
    """Basic test"""
    assert True
