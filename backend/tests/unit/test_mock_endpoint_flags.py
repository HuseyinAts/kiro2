"""Unit tests for S196 mock-to-real feature flag layer.

Covers `core/mock_endpoint_flags.py`:
- Default mock when JSON missing/corrupt
- Flag flip via env var override
- Cache invalidation between tests
"""

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _reset_flag_cache():
    """Each test gets a clean cache — no cross-test leakage."""
    from core.mock_endpoint_flags import reset_cache

    reset_cache()
    yield
    reset_cache()


def test_default_returns_mock_when_no_config(monkeypatch, tmp_path):
    """Missing config file → all flags False (mock fallback)."""
    monkeypatch.setenv("MOCK_FLAGS_PATH", str(tmp_path / "missing.json"))
    from core.mock_endpoint_flags import is_real_impl, reset_cache

    reset_cache()
    assert is_real_impl("advanced_reports.irt_analysis") is False
    assert is_real_impl("any.unknown.endpoint") is False


def test_flag_flipped_via_config_file(monkeypatch, tmp_path):
    """Flag set to true in JSON → is_real_impl returns True."""
    cfg = tmp_path / "flags.json"
    cfg.write_text(
        json.dumps({"advanced_reports.irt_analysis": True}), encoding="utf-8"
    )
    monkeypatch.setenv("MOCK_FLAGS_PATH", str(cfg))
    from core.mock_endpoint_flags import is_real_impl, reset_cache

    reset_cache()
    assert is_real_impl("advanced_reports.irt_analysis") is True
    assert is_real_impl("other.endpoint") is False


def test_corrupt_json_does_not_crash(monkeypatch, tmp_path):
    """Malformed JSON → log warning, fall back to all-mock."""
    cfg = tmp_path / "bad.json"
    cfg.write_text("{not valid json}", encoding="utf-8")
    monkeypatch.setenv("MOCK_FLAGS_PATH", str(cfg))
    from core.mock_endpoint_flags import is_real_impl, reset_cache

    reset_cache()
    # Must not raise — endpoints must keep serving mocks even with bad config.
    assert is_real_impl("anything") is False


def test_production_config_defaults_all_mock():
    """S196 invariant: only deliberately-promoted flags may be True.

    Day 1 (2026-05-23): all flags false (sprint baseline).
    Day 3 (2026-05-23): advanced_reports flags reverted to false after live
        smoke test passed — operator flips per endpoint for production.
    Day 4 (2026-05-23): `analytics.d7_retention` promoted because that
        endpoint was already DB-backed; flag is a provenance tag, not a
        mock-vs-real toggle.

    Add new flag slugs to ``PROMOTED_FLAGS`` ONLY after:
    - A real implementation exists and passes schema parity tests.
    - A live smoke test (preferably in `docker exec`) confirms no crash.
    - The promotion is documented in `docs/runbooks/mock_to_real_sprint.md`.
    """
    PROMOTED_FLAGS: set[str] = {
        "analytics.d7_retention",  # S196 Day 4: already-real endpoint, provenance tag only
    }

    config_path = (
        Path(__file__).resolve().parent.parent.parent
        / "config"
        / "mock_endpoint_flags.json"
    )
    assert config_path.exists(), f"Production mock flags config missing: {config_path}"

    flags = {
        k: v
        for k, v in json.loads(config_path.read_text(encoding="utf-8")).items()
        if not k.startswith("_")
    }
    unauthorized = [
        k for k, v in flags.items() if v is True and k not in PROMOTED_FLAGS
    ]
    assert unauthorized == [], (
        f"Flags flipped to True without explicit promotion: {unauthorized}. "
        f"Either add them to PROMOTED_FLAGS here (with rationale comment) "
        f"or revert the flag in mock_endpoint_flags.json."
    )
