"""
Logging Configuration for Production
Simple logging setup for the application
SECURITY FIX: Sensitive data redaction enabled
"""
import logging
import sys
from typing import Any

from .sensitive_data_filter import setup_global_sensitive_data_filter


def setup_production_logging(log_level: str = "INFO") -> None:
    """
    Setup production logging configuration
    SECURITY FIX: Automatically redacts sensitive data from logs
    """

    # Configure basic logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log", encoding="utf-8"),
        ],
    )

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # SECURITY FIX: Setup sensitive data filter globally
    setup_global_sensitive_data_filter(
        redact_email=False,  # Don't redact emails in logs (useful for debugging)
        redact_phone=False,  # Don't redact phones in logs (useful for debugging)
    )
    logging.info(
        "[SECURITY] Sensitive data filter enabled - passwords, tokens, API keys will be redacted"
    )


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def setup_request_logging() -> dict[str, Any]:
    """Setup request logging configuration"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
    }
