"""
Social Tasks Unit Tests
Validates Celery task implementations and registration.
"""

import importlib.util
import sys
from pathlib import Path

# Ensure backend root is in sys.path for direct module imports
_backend_root = str(Path(__file__).resolve().parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)


def _import_module(module_name: str, file_path: str):
    """Import a module by file path (avoids conftest sys.path issues)."""
    # Ensure backend root is first so core/models/etc resolve
    if _backend_root not in sys.path or sys.path[0] != _backend_root:
        sys.path.insert(0, _backend_root)
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestSocialTaskImports:
    """Verify social task modules import correctly."""

    def test_social_tasks_module_imports(self):
        mod = _import_module(
            "tasks.social_tasks",
            str(Path(_backend_root) / "tasks" / "social_tasks.py"),
        )
        assert hasattr(mod, "_check_birlikte_streaks_impl")
        assert hasattr(mod, "_expire_duel_voting_impl")
        assert hasattr(mod, "_expire_oba_challenges_impl")

    def test_celery_task_functions_exist(self):
        """Tasks should be registered when celery_app is available."""
        mod = _import_module(
            "tasks.social_tasks",
            str(Path(_backend_root) / "tasks" / "social_tasks.py"),
        )
        if mod.celery_app is not None:
            assert hasattr(mod, "check_birlikte_streaks")
            assert hasattr(mod, "expire_duel_voting")
            assert hasattr(mod, "expire_oba_challenges")


class TestSocialSummaryAPI:
    """Verify social summary API module structure."""

    def test_social_summary_imports(self):
        mod = _import_module(
            "api.social_summary_api",
            str(Path(_backend_root) / "api" / "social_summary_api.py"),
        )
        assert hasattr(mod, "router")
        assert hasattr(mod, "get_social_summary")

    def test_router_prefix(self):
        mod = _import_module(
            "api.social_summary_api",
            str(Path(_backend_root) / "api" / "social_summary_api.py"),
        )
        assert mod.router.prefix == "/api/v1/social"


class TestCeleryAppSchedule:
    """Verify social tasks are in the Celery beat schedule."""

    def test_social_beat_entries(self):
        mod = _import_module(
            "core.celery_app",
            str(Path(_backend_root) / "core" / "celery_app.py"),
        )
        beat = mod.celery_app.conf.beat_schedule

        assert "social-birlikte-streak-check" in beat
        assert (
            beat["social-birlikte-streak-check"]["task"]
            == "tasks.social_tasks.check_birlikte_streaks"
        )

        assert "social-duel-voting-expiry" in beat
        assert (
            beat["social-duel-voting-expiry"]["task"]
            == "tasks.social_tasks.expire_duel_voting"
        )
        assert beat["social-duel-voting-expiry"]["schedule"] == 1800.0

        assert "social-oba-challenge-expiry" in beat
        assert (
            beat["social-oba-challenge-expiry"]["task"]
            == "tasks.social_tasks.expire_oba_challenges"
        )

    def test_social_tasks_in_include(self):
        mod = _import_module(
            "core.celery_app",
            str(Path(_backend_root) / "core" / "celery_app.py"),
        )
        assert "tasks.social_tasks" in mod.celery_app.conf.include


class TestSocialNavigationEntry:
    """Verify the social summary router is registered in loader."""

    def test_social_summary_in_router_mapping(self):
        from routers.loader import ROUTER_MAPPING

        assert "api.social_summary_api" in ROUTER_MAPPING
        category, module = ROUTER_MAPPING["api.social_summary_api"]
        assert category == "social"
        assert module == "api.social_summary_api"
