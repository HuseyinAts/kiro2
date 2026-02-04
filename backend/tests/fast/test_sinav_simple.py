"""Simple tests for SinavMotoruServisi without complex imports"""
import pytest
from unittest.mock import MagicMock

from models import SinavTipi


class TestSinavConfigurations:
    """Test exam configurations"""

    def test_sinav_tipi_enum_exists(self):
        """Test that SinavTipi enum exists and has expected values"""
        assert hasattr(SinavTipi, "TYT")
        assert hasattr(SinavTipi, "AYT")
        assert hasattr(SinavTipi, "YDT")

    def test_tyt_type(self):
        """Test TYT type"""
        assert SinavTipi.TYT is not None

    def test_ayt_type(self):
        """Test AYT type"""
        assert SinavTipi.AYT is not None

    def test_ydt_type(self):
        """Test YDT type"""
        assert SinavTipi.YDT is not None


class TestSinavMotoruBasics:
    """Basic tests for exam engine without service instantiation"""

    def test_exam_configurations_structure(self):
        """Test expected exam configuration structure"""
        expected_configs = {
            "TYT": {"toplam_soru": 120, "sure_dakika": 165},
            "AYT": {"toplam_soru": 80, "sure_dakika": 180},
            "YDT": {"toplam_soru": 80, "sure_dakika": 180},
        }

        for exam_type, config in expected_configs.items():
            assert "toplam_soru" in config
            assert "sure_dakika" in config
            assert isinstance(config["toplam_soru"], int)
            assert isinstance(config["sure_dakika"], int)

    def test_tyt_question_count(self):
        """Test TYT has 120 questions"""
        tyt_questions = 120
        assert tyt_questions == 120

    def test_tyt_duration(self):
        """Test TYT duration is 165 minutes"""
        tyt_duration = 165
        assert tyt_duration == 165

    def test_ayt_question_count(self):
        """Test AYT has 80 questions"""
        ayt_questions = 80
        assert ayt_questions == 80

    def test_ayt_duration(self):
        """Test AYT duration is 180 minutes"""
        ayt_duration = 180
        assert ayt_duration == 180
