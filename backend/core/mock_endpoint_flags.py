"""Lightweight per-endpoint mock→real toggle.

Reads ``config/mock_endpoint_flags.json`` once and exposes ``is_real_impl(name)``.
Defaults to **mock** when the flag is missing — safe rollback path.

This is intentionally a separate, minimal module from ``feature_flags.py``
(which is video-discovery specific with enum/dataclass overhead). The
mock→real sprint flips one endpoint per day; an enum + manager is overkill.

Schema (``config/mock_endpoint_flags.json``)::

    {
        "advanced_reports.irt_analysis": true,
        "advanced_reports.zpd_recommendations": false,
        ...
    }

Override path: set ``MOCK_FLAGS_PATH`` env var to point at a different file
(useful for tests).

Usage in endpoint::

    from core.mock_endpoint_flags import is_real_impl

    if is_real_impl("advanced_reports.irt_analysis"):
        result = await real_irt_analysis(...)
    else:
        result = await mock_irt_analysis(...)
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

_DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "mock_endpoint_flags.json"
)


@lru_cache(maxsize=1)
def _load_flags() -> dict[str, bool]:
    """Read flag JSON exactly once per process.

    File missing → empty dict (everything stays mock). JSON corruption is
    logged but never raises — endpoints must continue serving mock data
    rather than crashing.
    """
    path = Path(os.environ.get("MOCK_FLAGS_PATH", _DEFAULT_PATH))
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        import logging

        logging.getLogger(__name__).warning(
            "mock_endpoint_flags: failed to load %s (%s); using all-mock defaults",
            path,
            exc,
        )
        return {}


def is_real_impl(name: str) -> bool:
    """Return True when the real implementation is enabled for ``name``."""
    return bool(_load_flags().get(name, False))


def reset_cache() -> None:
    """Test helper — forget cached flags so tests can swap config files."""
    _load_flags.cache_clear()


__all__ = ["is_real_impl", "reset_cache"]
