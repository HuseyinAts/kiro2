"""Unit test: FSRS /due endpoint mercy (catch-up) routing.

Wires get_due_items_with_mercy into the /due endpoint via a `mercy` flag.
No DB/auth — FSRSService is mocked and the route coroutine is called directly,
asserting the flag routes to the correct service method.
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parents[2]))

from app.api import fsrs as fsrs_api


def _make_svc():
    svc = MagicMock()
    svc.get_due_items = AsyncMock(return_value=[])
    svc.get_due_items_with_mercy = AsyncMock(return_value=[])
    return svc


async def test_due_mercy_true_routes_to_mercy():
    """mercy=True → catch-up (get_due_items_with_mercy), normal path skipped."""
    svc = _make_svc()
    user = SimpleNamespace(id="user-1")
    with patch.object(fsrs_api, "FSRSService", return_value=svc):
        await fsrs_api.get_due_items(
            subject_id=None, limit=20, mercy=True, current_user=user, db=MagicMock()
        )
    svc.get_due_items_with_mercy.assert_awaited_once()
    svc.get_due_items.assert_not_awaited()


async def test_due_mercy_false_routes_to_normal():
    """mercy=False (default) → normal get_due_items, mercy path skipped."""
    svc = _make_svc()
    user = SimpleNamespace(id="user-1")
    with patch.object(fsrs_api, "FSRSService", return_value=svc):
        await fsrs_api.get_due_items(
            subject_id=None, limit=20, mercy=False, current_user=user, db=MagicMock()
        )
    svc.get_due_items.assert_awaited_once()
    svc.get_due_items_with_mercy.assert_not_awaited()


async def test_due_mercy_passes_limit_as_cognitive_load():
    """mercy=True forwards the request limit as max_cognitive_load."""
    svc = _make_svc()
    user = SimpleNamespace(id="user-1")
    with patch.object(fsrs_api, "FSRSService", return_value=svc):
        await fsrs_api.get_due_items(
            subject_id=None, limit=15, mercy=True, current_user=user, db=MagicMock()
        )
    _, kwargs = svc.get_due_items_with_mercy.call_args
    assert kwargs.get("max_cognitive_load") == 15
