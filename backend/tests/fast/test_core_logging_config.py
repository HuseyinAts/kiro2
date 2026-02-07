"""
Tests for core/logging_config.py
Simple logging configuration tests
"""
import logging
from unittest.mock import patch


class TestSetupProductionLogging:
    """Test setup_production_logging function"""

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_default_log_level(self, mock_get_logger, mock_basic_config):
        """Test setup with default INFO level"""
        from core.logging_config import setup_production_logging

        setup_production_logging()

        # Verify basicConfig was called
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.INFO

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_custom_log_level(self, mock_get_logger, mock_basic_config):
        """Test setup with custom log level"""
        from core.logging_config import setup_production_logging

        setup_production_logging(log_level="DEBUG")

        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG

    @patch("logging.basicConfig")
    @patch("logging.getLogger")
    def test_setup_warning_log_level(self, mock_get_logger, mock_basic_config):
        """Test setup with WARNING level"""
        from core.logging_config import setup_production_logging

        setup_production_logging(log_level="WARNING")

        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.WARNING


class TestGetLogger:
    """Test get_logger function"""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a Logger instance"""
        from core.logging_config import get_logger

        logger = get_logger("test_logger")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_different_names(self):
        """Test get_logger with different names returns different loggers"""
        from core.logging_config import get_logger

        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")

        assert logger1.name == "logger1"
        assert logger2.name == "logger2"
        assert logger1 is not logger2


class TestSetupRequestLogging:
    """Test setup_request_logging function"""

    def test_returns_dict(self):
        """Test setup_request_logging returns a dictionary"""
        from core.logging_config import setup_request_logging

        config = setup_request_logging()

        assert isinstance(config, dict)

    def test_has_version(self):
        """Test config has version key"""
        from core.logging_config import setup_request_logging

        config = setup_request_logging()

        assert "version" in config
        assert config["version"] == 1

    def test_has_formatters(self):
        """Test config has formatters"""
        from core.logging_config import setup_request_logging

        config = setup_request_logging()

        assert "formatters" in config
        assert "default" in config["formatters"]

    def test_has_handlers(self):
        """Test config has handlers"""
        from core.logging_config import setup_request_logging

        config = setup_request_logging()

        assert "handlers" in config
        assert "default" in config["handlers"]

    def test_has_root_config(self):
        """Test config has root configuration"""
        from core.logging_config import setup_request_logging

        config = setup_request_logging()

        assert "root" in config
        assert config["root"]["level"] == "INFO"
        assert "handlers" in config["root"]

    def test_disable_existing_loggers_false(self):
        """Test disable_existing_loggers is False"""
        from core.logging_config import setup_request_logging

        config = setup_request_logging()

        assert config["disable_existing_loggers"] is False
