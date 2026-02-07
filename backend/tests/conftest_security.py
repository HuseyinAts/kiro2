"""Shared setup for security middleware tests.

Patches broken imports so security_middleware.py can be loaded
even when fastapi.middleware.base is unavailable (FastAPI >= 0.128).
"""

import sys
from unittest.mock import MagicMock

# Ensure fastapi.middleware.base exists as a module with BaseHTTPMiddleware
_fake_base = MagicMock()

# Use the real Starlette class so isinstance / __new__ work
from starlette.middleware.base import BaseHTTPMiddleware

_fake_base.BaseHTTPMiddleware = BaseHTTPMiddleware
sys.modules.setdefault("fastapi.middleware", MagicMock())
sys.modules["fastapi.middleware.base"] = _fake_base
