"""S180 smoke tests for core/auth_middleware.py (was 0% coverage).

Targets dataclass + enum surface. The middleware itself needs an HTTP
context to test end-to-end; this file ensures the module loads cleanly
and the public surface is stable.
"""

from __future__ import annotations

from core.auth_middleware import (
    AuthContext,
    AuthenticationMethod,
)


def test_authentication_method_enum_nonempty():
    methods = list(AuthenticationMethod)
    assert len(methods) > 0, "AuthenticationMethod must define at least one value"


def test_authentication_method_has_jwt_or_bearer():
    """KIRO2 uses JWT/Bearer auth + cookie auth; one of these must exist."""
    values = {
        m.value.lower() if hasattr(m, "value") else str(m).lower()
        for m in AuthenticationMethod
    }
    has_token_method = any(
        "jwt" in v or "bearer" in v or "token" in v or "cookie" in v for v in values
    )
    assert has_token_method, f"No JWT/Bearer/cookie auth method found: {values}"


def test_auth_context_is_dataclass():
    """AuthContext is the request-scoped auth state — must be a dataclass."""
    import dataclasses

    assert dataclasses.is_dataclass(AuthContext), (
        "AuthContext must be a dataclass for request.state attachment"
    )


def test_module_imports_without_side_effects():
    """Re-importing the module should not crash — guards against module-level
    side effects added unintentionally (DB connection, network, etc.).
    """
    import subprocess
    import sys
    from pathlib import Path

    backend_dir = str(Path(__file__).parents[2])
    cmd = [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import core.auth_middleware"]
    result = subprocess.run(cmd, cwd=backend_dir, capture_output=True, text=True)
    assert result.returncode == 0, f"Failed to import core.auth_middleware: {result.stderr}"
