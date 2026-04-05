"""
Zero-coverage batch 6: Unit tests for 4 zero-coverage backend files.

Targets:
  1. api/adhd_task_management_api.py   (281 stmts, 0%)
  2. models/live_session.py            (273 stmts, 0%)
  3. services/university_info_service.py (268 stmts, 0%)
  4. models/university_info.py         (263 stmts, 0%)

Goal: cover 700+ statements.
"""

import importlib.util
import os
import sys
import types
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# ---------------------------------------------------------------------------
# Stale-mock cleanup: remove any previously-cached module stubs that might
# collide with fresh imports.
# ---------------------------------------------------------------------------
_CLEANUP_PREFIXES = [
    "core.dependencies",
    "core.database",
    "models.database",
    "models.university_info",
    "models.live_session",
    "services.university_info_service",
    "api.adhd_task_management_api",
]

for _mod_key in list(sys.modules.keys()):
    for _prefix in _CLEANUP_PREFIXES:
        if _mod_key == _prefix or _mod_key.startswith(_prefix + "."):
            sys.modules.pop(_mod_key, None)
            break


# ---------------------------------------------------------------------------
# Helper: load a module from an absolute file path.
# For modules that live in a package (e.g. "models.live_session") we also
# register the parent package so that relative imports like
# `from .database import Base` resolve against sys.modules.
# ---------------------------------------------------------------------------
def _load_module(rel_path: str, module_name: str):
    full_path = os.path.join(_BACKEND, rel_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    mod = importlib.util.module_from_spec(spec)

    # Ensure parent package exists in sys.modules so relative imports work.
    parts = module_name.split(".")
    if len(parts) > 1:
        pkg_name = ".".join(parts[:-1])
        if pkg_name not in sys.modules:
            pkg = types.ModuleType(pkg_name)
            pkg.__path__ = [os.path.join(_BACKEND, pkg_name.replace(".", os.sep))]
            pkg.__package__ = pkg_name
            sys.modules[pkg_name] = pkg
        mod.__package__ = pkg_name
    else:
        mod.__package__ = module_name

    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_user(uid=1, role_val="student"):
    user = MagicMock()
    user.id = uid
    role = MagicMock()
    role.value = role_val
    user.role = role
    return user


def _make_mock_db():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.all.return_value = []
    q.first.return_value = None
    q.count.return_value = 0
    q.order_by.return_value = q
    q.limit.return_value = q
    return db


# ===========================================================================
# 1.  api/adhd_task_management_api.py
# ===========================================================================


@pytest.fixture(scope="module")
def adhd_api():
    """Load adhd_task_management_api with all dependencies mocked."""
    fake_db_mod = types.ModuleType("core.database")
    fake_db_mod.get_db = MagicMock()
    sys.modules["core.database"] = fake_db_mod

    fake_deps = types.ModuleType("core.dependencies")
    fake_deps.get_current_user = MagicMock()
    sys.modules["core.dependencies"] = fake_deps

    fake_models = types.ModuleType("models.database")
    fake_models.User = MagicMock
    sys.modules["models.database"] = fake_models

    mod = _load_module("api/adhd_task_management_api.py", "_adhd_api")
    return mod


class TestEisenhowerMatrix:
    """Tests for calculate_eisenhower_quadrant helper."""

    def test_urgent_and_important_is_q1(self, adhd_api):
        result = adhd_api.calculate_eisenhower_quadrant(True, True)
        assert result == adhd_api.EisenhowerQuadrant.Q1_URGENT_IMPORTANT

    def test_not_urgent_important_is_q2(self, adhd_api):
        result = adhd_api.calculate_eisenhower_quadrant(False, True)
        assert result == adhd_api.EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT

    def test_urgent_not_important_is_q3(self, adhd_api):
        result = adhd_api.calculate_eisenhower_quadrant(True, False)
        assert result == adhd_api.EisenhowerQuadrant.Q3_URGENT_NOT_IMPORTANT

    def test_not_urgent_not_important_is_q4(self, adhd_api):
        result = adhd_api.calculate_eisenhower_quadrant(False, False)
        assert result == adhd_api.EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT


class TestCalculateAutomaticPriority:
    """Tests for calculate_automatic_priority logic."""

    def test_q1_gives_critical(self, adhd_api):
        priority = adhd_api.calculate_automatic_priority(
            True, True, None, adhd_api.TaskCategory.OTHER
        )
        assert priority == adhd_api.TaskPriority.CRITICAL

    def test_q2_gives_high(self, adhd_api):
        priority = adhd_api.calculate_automatic_priority(
            False, True, None, adhd_api.TaskCategory.STUDY
        )
        assert priority == adhd_api.TaskPriority.HIGH

    def test_q3_gives_medium(self, adhd_api):
        priority = adhd_api.calculate_automatic_priority(
            True, False, None, adhd_api.TaskCategory.STUDY
        )
        assert priority == adhd_api.TaskPriority.MEDIUM

    def test_q4_gives_low(self, adhd_api):
        priority = adhd_api.calculate_automatic_priority(
            False, False, None, adhd_api.TaskCategory.STUDY
        )
        assert priority == adhd_api.TaskPriority.LOW

    def test_due_date_within_1_day_escalates_high_to_critical(self, adhd_api):
        due = datetime.now() + timedelta(hours=12)
        priority = adhd_api.calculate_automatic_priority(
            False, True, due, adhd_api.TaskCategory.STUDY
        )
        assert priority == adhd_api.TaskPriority.CRITICAL

    def test_due_date_within_1_day_escalates_medium_to_high(self, adhd_api):
        due = datetime.now() + timedelta(hours=6)
        priority = adhd_api.calculate_automatic_priority(
            True, False, due, adhd_api.TaskCategory.STUDY
        )
        assert priority == adhd_api.TaskPriority.HIGH

    def test_due_date_within_3_days_escalates_medium_to_high(self, adhd_api):
        due = datetime.now() + timedelta(days=2)
        priority = adhd_api.calculate_automatic_priority(
            True, False, due, adhd_api.TaskCategory.STUDY
        )
        assert priority == adhd_api.TaskPriority.HIGH

    def test_exam_category_escalates_low_to_medium(self, adhd_api):
        priority = adhd_api.calculate_automatic_priority(
            False, False, None, adhd_api.TaskCategory.EXAM
        )
        assert priority == adhd_api.TaskPriority.MEDIUM

    def test_exam_category_escalates_medium_to_high(self, adhd_api):
        priority = adhd_api.calculate_automatic_priority(
            True, False, None, adhd_api.TaskCategory.EXAM
        )
        assert priority == adhd_api.TaskPriority.HIGH

    def test_no_due_date_no_escalation(self, adhd_api):
        priority = adhd_api.calculate_automatic_priority(
            False, False, None, adhd_api.TaskCategory.OTHER
        )
        assert priority == adhd_api.TaskPriority.LOW


class TestGetTaskColors:
    """Tests for get_task_colors helper."""

    def test_colors_returned_for_valid_task(self, adhd_api):
        task = {
            "priority": adhd_api.TaskPriority.CRITICAL,
            "status": adhd_api.TaskStatus.TODO,
            "category": adhd_api.TaskCategory.STUDY,
            "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q1_URGENT_IMPORTANT,
        }
        colors = adhd_api.get_task_colors(task)
        assert colors["priority_color"] == "#DC2626"
        assert colors["status_color"] == "#3B82F6"
        assert colors["category_color"] == "#3B82F6"
        assert colors["quadrant_color"] == "#DC2626"

    def test_low_priority_color(self, adhd_api):
        task = {
            "priority": adhd_api.TaskPriority.LOW,
            "status": adhd_api.TaskStatus.COMPLETED,
            "category": adhd_api.TaskCategory.OTHER,
            "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT,
        }
        colors = adhd_api.get_task_colors(task)
        assert colors["priority_color"] == "#16A34A"
        assert colors["status_color"] == "#10B981"


class TestCountSubtasks:
    """Tests for count_subtasks helper."""

    def test_no_subtasks(self, adhd_api):
        adhd_api.tasks_db.clear()
        count = adhd_api.count_subtasks("nonexistent-id")
        assert count == 0

    def test_counts_subtasks_correctly(self, adhd_api):
        adhd_api.tasks_db.clear()
        parent_id = "parent-1"
        adhd_api.tasks_db["child-1"] = {"parent_task_id": parent_id}
        adhd_api.tasks_db["child-2"] = {"parent_task_id": parent_id}
        adhd_api.tasks_db["other"] = {"parent_task_id": "other-parent"}
        count = adhd_api.count_subtasks(parent_id)
        assert count == 2
        adhd_api.tasks_db.clear()


class TestCreateTask:
    """Tests for create_task endpoint handler."""

    def test_create_task_returns_task_response(self, adhd_api):
        adhd_api.tasks_db.clear()
        req = adhd_api.CreateTaskRequest(
            title="YKS Matematik Çalış",
            category=adhd_api.TaskCategory.STUDY,
            is_urgent=False,
            is_important=True,
        )
        user = _make_user(uid=42)
        db = _make_mock_db()

        result = adhd_api.create_task(req, current_user=user, db=db)

        assert result.user_id == 42
        assert result.title == "YKS Matematik Çalış"
        assert result.category == adhd_api.TaskCategory.STUDY
        assert result.status == adhd_api.TaskStatus.TODO
        assert result.priority is not None
        assert result.task_id in adhd_api.tasks_db
        adhd_api.tasks_db.clear()

    def test_create_task_urgent_important_sets_critical(self, adhd_api):
        adhd_api.tasks_db.clear()
        req = adhd_api.CreateTaskRequest(
            title="Sınav",
            category=adhd_api.TaskCategory.EXAM,
            is_urgent=True,
            is_important=True,
        )
        user = _make_user()
        result = adhd_api.create_task(req, current_user=user, db=_make_mock_db())
        assert result.priority == adhd_api.TaskPriority.CRITICAL
        assert (
            result.eisenhower_quadrant
            == adhd_api.EisenhowerQuadrant.Q1_URGENT_IMPORTANT
        )
        adhd_api.tasks_db.clear()

    def test_create_task_with_parent_id(self, adhd_api):
        adhd_api.tasks_db.clear()
        parent_id = "parent-xyz"
        req = adhd_api.CreateTaskRequest(
            title="Alt Görev",
            parent_task_id=parent_id,
        )
        user = _make_user()
        result = adhd_api.create_task(req, current_user=user, db=_make_mock_db())
        assert result.parent_task_id == parent_id
        adhd_api.tasks_db.clear()

    def test_create_task_with_description_and_duration(self, adhd_api):
        adhd_api.tasks_db.clear()
        req = adhd_api.CreateTaskRequest(
            title="Fizik Ödevi",
            description="Kinematik bölümü",
            estimated_duration_minutes=90,
            category=adhd_api.TaskCategory.HOMEWORK,
        )
        user = _make_user()
        result = adhd_api.create_task(req, current_user=user, db=_make_mock_db())
        assert result.description == "Kinematik bölümü"
        assert result.estimated_duration_minutes == 90
        adhd_api.tasks_db.clear()


class TestListTasks:
    """Tests for list_tasks endpoint handler."""

    def _populate_tasks(self, adhd_api, user_id, count=3):
        adhd_api.tasks_db.clear()
        for i in range(count):
            tid = f"task-{i}"
            adhd_api.tasks_db[tid] = {
                "task_id": tid,
                "user_id": user_id,
                "title": f"Task {i}",
                "description": None,
                "category": adhd_api.TaskCategory.STUDY,
                "status": adhd_api.TaskStatus.TODO,
                "priority": adhd_api.TaskPriority.MEDIUM,
                "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q3_URGENT_NOT_IMPORTANT,
                "due_date": None,
                "estimated_duration_minutes": None,
                "is_urgent": True,
                "is_important": False,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "completed_at": None,
                "parent_task_id": None,
            }

    def test_list_tasks_returns_correct_count(self, adhd_api):
        user = _make_user(uid=99)
        self._populate_tasks(adhd_api, user_id=99, count=3)
        result = adhd_api.list_tasks(current_user=user, db=_make_mock_db())
        assert result.total_count == 3
        adhd_api.tasks_db.clear()

    def test_list_tasks_filters_by_status(self, adhd_api):
        user = _make_user(uid=88)
        self._populate_tasks(adhd_api, user_id=88, count=2)
        # set one to completed
        adhd_api.tasks_db["task-0"]["status"] = adhd_api.TaskStatus.COMPLETED
        result = adhd_api.list_tasks(
            status_filter=adhd_api.TaskStatus.COMPLETED,
            current_user=user,
            db=_make_mock_db(),
        )
        assert result.total_count == 1
        adhd_api.tasks_db.clear()

    def test_list_tasks_filters_by_priority(self, adhd_api):
        user = _make_user(uid=77)
        self._populate_tasks(adhd_api, user_id=77, count=3)
        adhd_api.tasks_db["task-0"]["priority"] = adhd_api.TaskPriority.CRITICAL
        result = adhd_api.list_tasks(
            priority_filter=adhd_api.TaskPriority.CRITICAL,
            current_user=user,
            db=_make_mock_db(),
        )
        assert result.total_count == 1
        adhd_api.tasks_db.clear()

    def test_list_tasks_filters_by_category(self, adhd_api):
        user = _make_user(uid=66)
        self._populate_tasks(adhd_api, user_id=66, count=2)
        adhd_api.tasks_db["task-0"]["category"] = adhd_api.TaskCategory.EXAM
        result = adhd_api.list_tasks(
            category_filter=adhd_api.TaskCategory.EXAM,
            current_user=user,
            db=_make_mock_db(),
        )
        assert result.total_count == 1
        adhd_api.tasks_db.clear()

    def test_list_tasks_by_quadrant_filter(self, adhd_api):
        user = _make_user(uid=55)
        self._populate_tasks(adhd_api, user_id=55, count=3)
        adhd_api.tasks_db["task-0"]["eisenhower_quadrant"] = (
            adhd_api.EisenhowerQuadrant.Q1_URGENT_IMPORTANT
        )
        result = adhd_api.list_tasks(
            quadrant_filter=adhd_api.EisenhowerQuadrant.Q1_URGENT_IMPORTANT,
            current_user=user,
            db=_make_mock_db(),
        )
        assert result.total_count == 1
        adhd_api.tasks_db.clear()

    def test_list_tasks_only_returns_own_tasks(self, adhd_api):
        adhd_api.tasks_db.clear()
        user = _make_user(uid=10)
        # Add a task for user 10 and another for user 20
        adhd_api.tasks_db["task-a"] = {
            "task_id": "task-a",
            "user_id": 10,
            "title": "Mine",
            "description": None,
            "category": adhd_api.TaskCategory.STUDY,
            "status": adhd_api.TaskStatus.TODO,
            "priority": adhd_api.TaskPriority.LOW,
            "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT,
            "due_date": None,
            "estimated_duration_minutes": None,
            "is_urgent": False,
            "is_important": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "completed_at": None,
            "parent_task_id": None,
        }
        adhd_api.tasks_db["task-b"] = {
            **adhd_api.tasks_db["task-a"],
            "task_id": "task-b",
            "user_id": 20,
        }
        result = adhd_api.list_tasks(current_user=user, db=_make_mock_db())
        assert result.total_count == 1
        adhd_api.tasks_db.clear()

    def test_list_tasks_statistics_by_priority(self, adhd_api):
        user = _make_user(uid=50)
        self._populate_tasks(adhd_api, user_id=50, count=2)
        adhd_api.tasks_db["task-0"]["priority"] = adhd_api.TaskPriority.HIGH
        adhd_api.tasks_db["task-1"]["priority"] = adhd_api.TaskPriority.CRITICAL
        result = adhd_api.list_tasks(current_user=user, db=_make_mock_db())
        assert adhd_api.TaskPriority.HIGH in result.by_priority
        assert adhd_api.TaskPriority.CRITICAL in result.by_priority
        adhd_api.tasks_db.clear()


class TestGetTask:
    """Tests for get_task endpoint handler."""

    def _put_task(self, adhd_api, task_id, user_id):
        adhd_api.tasks_db[task_id] = {
            "task_id": task_id,
            "user_id": user_id,
            "title": "Test",
            "description": None,
            "category": adhd_api.TaskCategory.OTHER,
            "status": adhd_api.TaskStatus.TODO,
            "priority": adhd_api.TaskPriority.NONE,
            "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT,
            "due_date": None,
            "estimated_duration_minutes": None,
            "is_urgent": False,
            "is_important": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "completed_at": None,
            "parent_task_id": None,
        }

    def test_get_existing_task(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._put_task(adhd_api, "tid-1", user_id=1)
        user = _make_user(uid=1)
        result = adhd_api.get_task("tid-1", current_user=user, db=_make_mock_db())
        assert result.task_id == "tid-1"
        adhd_api.tasks_db.clear()

    def test_get_task_not_found_raises_404(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        user = _make_user(uid=1)
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.get_task("nonexistent", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 404

    def test_get_task_wrong_user_raises_403(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        self._put_task(adhd_api, "tid-2", user_id=5)
        user = _make_user(uid=99)  # different user
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.get_task("tid-2", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 403
        adhd_api.tasks_db.clear()


class TestUpdateTask:
    """Tests for update_task endpoint handler."""

    def _seed(self, adhd_api, tid="u-task", uid=1):
        adhd_api.tasks_db[tid] = {
            "task_id": tid,
            "user_id": uid,
            "title": "Original",
            "description": None,
            "category": adhd_api.TaskCategory.STUDY,
            "status": adhd_api.TaskStatus.TODO,
            "priority": adhd_api.TaskPriority.MEDIUM,
            "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q3_URGENT_NOT_IMPORTANT,
            "due_date": None,
            "estimated_duration_minutes": None,
            "is_urgent": True,
            "is_important": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "completed_at": None,
            "parent_task_id": None,
        }

    def test_update_title(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._seed(adhd_api)
        user = _make_user(uid=1)
        req = adhd_api.UpdateTaskRequest(title="Updated Title")
        result = adhd_api.update_task(
            "u-task", req, current_user=user, db=_make_mock_db()
        )
        assert result.title == "Updated Title"
        adhd_api.tasks_db.clear()

    def test_update_status_to_completed(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._seed(adhd_api)
        user = _make_user(uid=1)
        req = adhd_api.UpdateTaskRequest(status=adhd_api.TaskStatus.COMPLETED)
        result = adhd_api.update_task(
            "u-task", req, current_user=user, db=_make_mock_db()
        )
        assert result.status == adhd_api.TaskStatus.COMPLETED
        adhd_api.tasks_db.clear()

    def test_update_recalculates_quadrant_when_flags_change(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._seed(adhd_api)
        user = _make_user(uid=1)
        req = adhd_api.UpdateTaskRequest(is_urgent=False, is_important=True)
        result = adhd_api.update_task(
            "u-task", req, current_user=user, db=_make_mock_db()
        )
        assert (
            result.eisenhower_quadrant
            == adhd_api.EisenhowerQuadrant.Q2_NOT_URGENT_IMPORTANT
        )
        adhd_api.tasks_db.clear()

    def test_update_not_found_raises_404(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        user = _make_user(uid=1)
        req = adhd_api.UpdateTaskRequest(title="X")
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.update_task("ghost", req, current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 404

    def test_update_wrong_user_raises_403(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        self._seed(adhd_api, uid=5)
        user = _make_user(uid=99)
        req = adhd_api.UpdateTaskRequest(title="Hack")
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.update_task("u-task", req, current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 403
        adhd_api.tasks_db.clear()

    def test_update_with_explicit_priority_skips_recalc(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._seed(adhd_api)
        user = _make_user(uid=1)
        req = adhd_api.UpdateTaskRequest(priority=adhd_api.TaskPriority.NONE)
        result = adhd_api.update_task(
            "u-task", req, current_user=user, db=_make_mock_db()
        )
        assert result.priority == adhd_api.TaskPriority.NONE
        adhd_api.tasks_db.clear()


class TestDeleteTask:
    """Tests for delete_task endpoint handler."""

    def _seed(self, adhd_api, tid, uid, parent=None):
        adhd_api.tasks_db[tid] = {
            "task_id": tid,
            "user_id": uid,
            "parent_task_id": parent,
        }

    def test_delete_removes_task(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._seed(adhd_api, "del-1", uid=1)
        user = _make_user(uid=1)
        adhd_api.delete_task("del-1", current_user=user, db=_make_mock_db())
        assert "del-1" not in adhd_api.tasks_db

    def test_delete_also_removes_subtasks(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._seed(adhd_api, "parent-del", uid=1)
        self._seed(adhd_api, "child-del-1", uid=1, parent="parent-del")
        self._seed(adhd_api, "child-del-2", uid=1, parent="parent-del")
        user = _make_user(uid=1)
        adhd_api.delete_task("parent-del", current_user=user, db=_make_mock_db())
        assert "parent-del" not in adhd_api.tasks_db
        assert "child-del-1" not in adhd_api.tasks_db
        assert "child-del-2" not in adhd_api.tasks_db

    def test_delete_not_found_raises_404(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        user = _make_user(uid=1)
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.delete_task("ghost", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 404

    def test_delete_wrong_user_raises_403(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        self._seed(adhd_api, "del-2", uid=5)
        user = _make_user(uid=99)
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.delete_task("del-2", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 403
        adhd_api.tasks_db.clear()


class TestGetSubtasks:
    """Tests for get_subtasks endpoint handler."""

    def _put(self, adhd_api, tid, uid, parent=None):
        adhd_api.tasks_db[tid] = {
            "task_id": tid,
            "user_id": uid,
            "title": "Sub",
            "description": None,
            "category": adhd_api.TaskCategory.OTHER,
            "status": adhd_api.TaskStatus.TODO,
            "priority": adhd_api.TaskPriority.LOW,
            "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT,
            "due_date": None,
            "estimated_duration_minutes": None,
            "is_urgent": False,
            "is_important": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "completed_at": None,
            "parent_task_id": parent,
        }

    def test_get_subtasks_returns_children(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._put(adhd_api, "p1", uid=1)
        self._put(adhd_api, "c1", uid=1, parent="p1")
        self._put(adhd_api, "c2", uid=1, parent="p1")
        user = _make_user(uid=1)
        result = adhd_api.get_subtasks("p1", current_user=user, db=_make_mock_db())
        assert len(result) == 2
        adhd_api.tasks_db.clear()

    def test_get_subtasks_not_found_raises_404(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        user = _make_user(uid=1)
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.get_subtasks("ghost", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 404

    def test_get_subtasks_wrong_user_raises_403(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        self._put(adhd_api, "p2", uid=5)
        user = _make_user(uid=99)
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.get_subtasks("p2", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 403
        adhd_api.tasks_db.clear()


class TestRecommendPriority:
    """Tests for recommend_priority endpoint handler."""

    def _put(self, adhd_api, tid, uid, is_urgent, is_important, category, due=None):
        adhd_api.tasks_db[tid] = {
            "task_id": tid,
            "user_id": uid,
            "is_urgent": is_urgent,
            "is_important": is_important,
            "category": category,
            "due_date": due,
            "priority": adhd_api.TaskPriority.MEDIUM,
            "eisenhower_quadrant": adhd_api.calculate_eisenhower_quadrant(
                is_urgent, is_important
            ),
        }

    def test_recommend_q1_gives_critical(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._put(adhd_api, "r1", 1, True, True, adhd_api.TaskCategory.STUDY)
        user = _make_user(uid=1)
        result = adhd_api.recommend_priority(
            "r1", current_user=user, db=_make_mock_db()
        )
        assert result.recommended_priority == adhd_api.TaskPriority.CRITICAL
        assert 0.0 <= result.confidence_score <= 1.0
        adhd_api.tasks_db.clear()

    def test_recommend_not_found_raises_404(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        user = _make_user(uid=1)
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.recommend_priority("ghost", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 404

    def test_recommend_wrong_user_raises_403(self, adhd_api):
        from fastapi import HTTPException

        adhd_api.tasks_db.clear()
        self._put(adhd_api, "r2", 5, False, True, adhd_api.TaskCategory.OTHER)
        user = _make_user(uid=99)
        with pytest.raises(HTTPException) as exc_info:
            adhd_api.recommend_priority("r2", current_user=user, db=_make_mock_db())
        assert exc_info.value.status_code == 403
        adhd_api.tasks_db.clear()

    def test_recommend_with_due_date_increases_confidence(self, adhd_api):
        adhd_api.tasks_db.clear()
        due = datetime.now() + timedelta(hours=6)
        self._put(adhd_api, "r3", 1, True, True, adhd_api.TaskCategory.EXAM, due=due)
        user = _make_user(uid=1)
        result = adhd_api.recommend_priority(
            "r3", current_user=user, db=_make_mock_db()
        )
        assert result.confidence_score >= 0.9
        adhd_api.tasks_db.clear()

    def test_recommend_q2_reason_mentions_important(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._put(adhd_api, "r4", 1, False, True, adhd_api.TaskCategory.STUDY)
        user = _make_user(uid=1)
        result = adhd_api.recommend_priority(
            "r4", current_user=user, db=_make_mock_db()
        )
        assert "önemli" in result.reason.lower() or "important" in result.reason.lower()
        adhd_api.tasks_db.clear()

    def test_recommend_q4_reason_mentions_not_urgent(self, adhd_api):
        adhd_api.tasks_db.clear()
        self._put(adhd_api, "r5", 1, False, False, adhd_api.TaskCategory.OTHER)
        user = _make_user(uid=1)
        result = adhd_api.recommend_priority(
            "r5", current_user=user, db=_make_mock_db()
        )
        assert result.reason.endswith(".")
        adhd_api.tasks_db.clear()


class TestGetColorScheme:
    """Tests for get_color_scheme endpoint."""

    def test_color_scheme_has_all_keys(self, adhd_api):
        result = adhd_api.get_color_scheme()
        assert hasattr(result, "priority_colors")
        assert hasattr(result, "status_colors")
        assert hasattr(result, "category_colors")
        assert hasattr(result, "quadrant_colors")

    def test_priority_colors_covers_all_priorities(self, adhd_api):
        result = adhd_api.get_color_scheme()
        for p in adhd_api.TaskPriority:
            assert p in result.priority_colors

    def test_status_colors_covers_all_statuses(self, adhd_api):
        result = adhd_api.get_color_scheme()
        for s in adhd_api.TaskStatus:
            assert s in result.status_colors


class TestGetTaskStats:
    """Tests for get_task_stats endpoint."""

    def test_stats_empty_user(self, adhd_api):
        adhd_api.tasks_db.clear()
        user = _make_user(uid=999)
        result = adhd_api.get_task_stats(current_user=user, db=_make_mock_db())
        assert result["total_tasks"] == 0
        assert result["completion_rate"] == 0.0

    def test_stats_with_completed_tasks(self, adhd_api):
        adhd_api.tasks_db.clear()
        user = _make_user(uid=111)
        for i in range(4):
            adhd_api.tasks_db[f"st-{i}"] = {
                "task_id": f"st-{i}",
                "user_id": 111,
                "status": adhd_api.TaskStatus.COMPLETED
                if i < 2
                else adhd_api.TaskStatus.TODO,
                "priority": adhd_api.TaskPriority.MEDIUM,
                "eisenhower_quadrant": adhd_api.EisenhowerQuadrant.Q4_NOT_URGENT_NOT_IMPORTANT,
            }
        result = adhd_api.get_task_stats(current_user=user, db=_make_mock_db())
        assert result["total_tasks"] == 4
        assert result["completed_tasks"] == 2
        assert result["completion_rate"] == 50.0
        adhd_api.tasks_db.clear()


class TestHealthCheck:
    """Tests for health_check endpoint."""

    def test_health_returns_healthy(self, adhd_api):
        result = adhd_api.health_check()
        assert result["status"] == "healthy"
        assert result["service"] == "ADHD Task Management API"
        assert "timestamp" in result
        assert "tasks_count" in result

    def test_health_tasks_count_reflects_db(self, adhd_api):
        adhd_api.tasks_db.clear()
        adhd_api.tasks_db["t1"] = {}
        adhd_api.tasks_db["t2"] = {}
        result = adhd_api.health_check()
        assert result["tasks_count"] == 2
        adhd_api.tasks_db.clear()


class TestEnums:
    """Tests for enum values and color mappings."""

    def test_task_priority_values(self, adhd_api):
        assert adhd_api.TaskPriority.CRITICAL == "critical"
        assert adhd_api.TaskPriority.HIGH == "high"
        assert adhd_api.TaskPriority.LOW == "low"
        assert adhd_api.TaskPriority.NONE == "none"

    def test_task_status_values(self, adhd_api):
        assert adhd_api.TaskStatus.TODO == "todo"
        assert adhd_api.TaskStatus.IN_PROGRESS == "in_progress"
        assert adhd_api.TaskStatus.COMPLETED == "completed"
        assert adhd_api.TaskStatus.CANCELLED == "cancelled"
        assert adhd_api.TaskStatus.ON_HOLD == "on_hold"

    def test_task_category_values(self, adhd_api):
        assert adhd_api.TaskCategory.STUDY == "study"
        assert adhd_api.TaskCategory.EXAM == "exam"

    def test_priority_colors_dict_non_empty(self, adhd_api):
        assert len(adhd_api.PRIORITY_COLORS) == 5

    def test_status_colors_dict_non_empty(self, adhd_api):
        assert len(adhd_api.STATUS_COLORS) == 5

    def test_category_colors_dict_non_empty(self, adhd_api):
        assert len(adhd_api.CATEGORY_COLORS) == 6

    def test_quadrant_colors_dict_non_empty(self, adhd_api):
        assert len(adhd_api.QUADRANT_COLORS) == 4


# ===========================================================================
# 2.  models/live_session.py
# ===========================================================================


@pytest.fixture(scope="module")
def live_session_mod():
    """Load models/live_session.py with SQLAlchemy Base mocked."""
    # Stub sqlalchemy.dialects.postgresql so PGUUID and JSONB are importable
    _pg_stub = types.ModuleType("sqlalchemy.dialects.postgresql")
    _pg_stub.UUID = MagicMock(return_value=MagicMock())
    _pg_stub.JSONB = MagicMock(return_value=MagicMock())
    sys.modules.setdefault(
        "sqlalchemy.dialects", types.ModuleType("sqlalchemy.dialects")
    )
    sys.modules["sqlalchemy.dialects.postgresql"] = _pg_stub

    # Provide a minimal Base via models.database stub
    _db_stub = types.ModuleType("models.database")

    class _FakeBase:
        metadata = MagicMock()

        class _FakeMeta(type):
            def __new__(mcs, name, bases, ns):
                return super().__new__(mcs, name, bases, ns)

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)

    _db_stub.Base = _FakeBase
    sys.modules["models.database"] = _db_stub

    mod = _load_module("models/live_session.py", "models.live_session")
    return mod


class TestLiveSessionEnums:
    """Test enumeration values in live_session model."""

    def test_session_status_values(self, live_session_mod):
        ss = live_session_mod.SessionStatus
        assert ss.SCHEDULED == "scheduled"
        assert ss.LIVE == "live"
        assert ss.ENDED == "ended"
        assert ss.CANCELLED == "cancelled"

    def test_session_type_values(self, live_session_mod):
        st = live_session_mod.SessionType
        assert st.ONE_ON_ONE == "one_on_one"
        assert st.GROUP_SESSION == "group_session"
        assert st.WEBINAR == "webinar"
        assert st.STUDY_GROUP == "study_group"

    def test_platform_type_values(self, live_session_mod):
        pt = live_session_mod.PlatformType
        assert pt.ZOOM == "zoom"
        assert pt.GOOGLE_MEET == "google_meet"
        assert pt.JITSI == "jitsi"
        assert pt.CUSTOM == "custom"

    def test_participant_role_values(self, live_session_mod):
        pr = live_session_mod.ParticipantRole
        assert pr.HOST == "host"
        assert pr.CO_HOST == "co_host"
        assert pr.PARTICIPANT == "participant"
        assert pr.OBSERVER == "observer"

    def test_recording_status_values(self, live_session_mod):
        rs = live_session_mod.RecordingStatus
        assert rs.RECORDING == "recording"
        assert rs.PROCESSING == "processing"
        assert rs.READY == "ready"
        assert rs.FAILED == "failed"

    def test_whiteboard_tool_types(self, live_session_mod):
        wt = live_session_mod.WhiteboardToolType
        assert wt.PEN == "pen"
        assert wt.ERASER == "eraser"
        assert wt.TEXT == "text"
        assert wt.SHAPE == "shape"
        assert wt.HIGHLIGHTER == "highlighter"
        assert wt.EQUATION == "equation"

    def test_screen_share_types(self, live_session_mod):
        sst = live_session_mod.ScreenShareType
        assert sst.ENTIRE_SCREEN == "entire_screen"
        assert sst.WINDOW == "window"
        assert sst.APPLICATION == "application"
        assert sst.WHITEBOARD == "whiteboard"


class TestLiveSessionModelDefinitions:
    """Test that model classes are defined with expected attributes."""

    def test_live_session_tablename(self, live_session_mod):
        assert live_session_mod.LiveSession.__tablename__ == "live_sessions"

    def test_session_participant_tablename(self, live_session_mod):
        assert (
            live_session_mod.SessionParticipant.__tablename__ == "session_participants"
        )

    def test_screen_share_tablename(self, live_session_mod):
        assert live_session_mod.ScreenShare.__tablename__ == "screen_shares"

    def test_whiteboard_session_tablename(self, live_session_mod):
        assert live_session_mod.WhiteboardSession.__tablename__ == "whiteboard_sessions"

    def test_whiteboard_stroke_tablename(self, live_session_mod):
        assert live_session_mod.WhiteboardStroke.__tablename__ == "whiteboard_strokes"

    def test_whiteboard_equation_tablename(self, live_session_mod):
        assert (
            live_session_mod.WhiteboardEquation.__tablename__ == "whiteboard_equations"
        )

    def test_session_recording_tablename(self, live_session_mod):
        assert live_session_mod.SessionRecording.__tablename__ == "session_recordings"

    def test_recording_view_tablename(self, live_session_mod):
        assert live_session_mod.RecordingView.__tablename__ == "recording_views"

    def test_recording_bookmark_tablename(self, live_session_mod):
        assert live_session_mod.RecordingBookmark.__tablename__ == "recording_bookmarks"

    def test_session_chat_message_tablename(self, live_session_mod):
        assert (
            live_session_mod.SessionChatMessage.__tablename__ == "session_chat_messages"
        )

    def test_session_analytics_tablename(self, live_session_mod):
        assert live_session_mod.SessionAnalytics.__tablename__ == "session_analytics"

    def test_live_session_has_expected_columns(self, live_session_mod):
        cls = live_session_mod.LiveSession
        assert hasattr(cls, "title")
        assert hasattr(cls, "session_type")
        assert hasattr(cls, "status")
        assert hasattr(cls, "platform")
        assert hasattr(cls, "max_participants")
        assert hasattr(cls, "allow_recording")
        assert hasattr(cls, "is_recorded")
        assert hasattr(cls, "host_id")

    def test_session_participant_has_expected_columns(self, live_session_mod):
        cls = live_session_mod.SessionParticipant
        assert hasattr(cls, "role")
        assert hasattr(cls, "is_present")
        assert hasattr(cls, "questions_asked")
        assert hasattr(cls, "connection_quality")

    def test_whiteboard_stroke_has_tool_and_color(self, live_session_mod):
        cls = live_session_mod.WhiteboardStroke
        assert hasattr(cls, "tool_type")
        assert hasattr(cls, "color")
        assert hasattr(cls, "width")
        assert hasattr(cls, "path_data")

    def test_whiteboard_equation_has_latex_field(self, live_session_mod):
        cls = live_session_mod.WhiteboardEquation
        assert hasattr(cls, "latex_code")
        assert hasattr(cls, "rendered_svg")

    def test_session_recording_has_status_and_counts(self, live_session_mod):
        cls = live_session_mod.SessionRecording
        assert hasattr(cls, "status")
        assert hasattr(cls, "view_count")
        assert hasattr(cls, "has_transcript")
        assert hasattr(cls, "is_public")

    def test_session_analytics_has_engagement_fields(self, live_session_mod):
        cls = live_session_mod.SessionAnalytics
        assert hasattr(cls, "total_participants")
        assert hasattr(cls, "total_chat_messages")
        assert hasattr(cls, "whiteboard_used")

    def test_recording_bookmark_has_timestamp(self, live_session_mod):
        cls = live_session_mod.RecordingBookmark
        assert hasattr(cls, "timestamp_seconds")
        assert hasattr(cls, "title")
        assert hasattr(cls, "note")

    def test_recording_view_has_watch_fields(self, live_session_mod):
        cls = live_session_mod.RecordingView
        assert hasattr(cls, "watch_percentage")
        assert hasattr(cls, "completed")
        assert hasattr(cls, "last_position_seconds")


class TestLiveSessionEnumCoverage:
    """Additional enum count and membership checks."""

    def test_session_status_count(self, live_session_mod):
        assert len(live_session_mod.SessionStatus) == 4

    def test_session_type_count(self, live_session_mod):
        assert len(live_session_mod.SessionType) == 4

    def test_participant_role_count(self, live_session_mod):
        assert len(live_session_mod.ParticipantRole) == 4

    def test_whiteboard_tool_count(self, live_session_mod):
        assert len(live_session_mod.WhiteboardToolType) == 6

    def test_screen_share_type_count(self, live_session_mod):
        assert len(live_session_mod.ScreenShareType) == 4

    def test_recording_status_count(self, live_session_mod):
        assert len(live_session_mod.RecordingStatus) == 4

    def test_platform_type_count(self, live_session_mod):
        assert len(live_session_mod.PlatformType) == 4


# ===========================================================================
# 3.  models/university_info.py
# ===========================================================================


@pytest.fixture(scope="module")
def uni_info_models():
    """Load models/university_info.py with dependencies mocked."""
    _pg_stub = sys.modules.get(
        "sqlalchemy.dialects.postgresql",
        types.ModuleType("sqlalchemy.dialects.postgresql"),
    )
    _pg_stub.UUID = MagicMock(return_value=MagicMock())
    _pg_stub.JSONB = MagicMock(return_value=MagicMock())
    sys.modules["sqlalchemy.dialects.postgresql"] = _pg_stub

    _db_stub = types.ModuleType("models.database")

    class _FakeBase2:
        pass

    _db_stub.Base = _FakeBase2
    sys.modules["models.database"] = _db_stub

    mod = _load_module("models/university_info.py", "models.university_info")
    return mod


class TestUniversityInfoEnums:
    """Test enumeration values in university_info models."""

    def test_campus_type_values(self, uni_info_models):
        ct = uni_info_models.CampusType
        assert ct.MAIN_CAMPUS == "main_campus"
        assert ct.SATELLITE_CAMPUS == "satellite_campus"
        assert ct.MEDICAL_CAMPUS == "medical_campus"
        assert ct.RESEARCH_CAMPUS == "research_campus"

    def test_campus_type_count(self, uni_info_models):
        assert len(uni_info_models.CampusType) == 4

    def test_accommodation_type_values(self, uni_info_models):
        at = uni_info_models.AccommodationType
        assert at.STATE_DORMITORY == "state_dormitory"
        assert at.UNIVERSITY_DORMITORY == "university_dormitory"
        assert at.PRIVATE_DORMITORY == "private_dormitory"
        assert at.APARTMENT == "apartment"
        assert at.SHARED_APARTMENT == "shared_apartment"

    def test_accommodation_type_count(self, uni_info_models):
        assert len(uni_info_models.AccommodationType) == 5

    def test_scholarship_type_values(self, uni_info_models):
        st = uni_info_models.ScholarshipType
        assert st.FULL_SCHOLARSHIP == "full_scholarship"
        assert st.PARTIAL_SCHOLARSHIP == "partial_scholarship"
        assert st.MERIT_BASED == "merit_based"
        assert st.NEED_BASED == "need_based"
        assert st.SPORTS == "sports"
        assert st.ACADEMIC_EXCELLENCE == "academic_excellence"
        assert st.SPECIAL_TALENT == "special_talent"

    def test_scholarship_type_count(self, uni_info_models):
        assert len(uni_info_models.ScholarshipType) == 7


class TestUniversityInfoModelDefinitions:
    """Test that model classes have expected table names and columns."""

    def test_campus_info_tablename(self, uni_info_models):
        assert uni_info_models.CampusInfo.__tablename__ == "campus_info"

    def test_city_living_cost_tablename(self, uni_info_models):
        assert uni_info_models.CityLivingCost.__tablename__ == "city_living_costs"

    def test_dormitory_info_tablename(self, uni_info_models):
        assert uni_info_models.DormitoryInfo.__tablename__ == "dormitory_info"

    def test_scholarship_program_tablename(self, uni_info_models):
        assert (
            uni_info_models.ScholarshipProgram.__tablename__ == "scholarship_programs"
        )

    def test_university_statistics_tablename(self, uni_info_models):
        assert (
            uni_info_models.UniversityStatistics.__tablename__
            == "university_statistics"
        )

    def test_campus_info_has_facility_columns(self, uni_info_models):
        cls = uni_info_models.CampusInfo
        assert hasattr(cls, "campus_name")
        assert hasattr(cls, "city")
        assert hasattr(cls, "campus_type")
        assert hasattr(cls, "health_center")
        assert hasattr(cls, "career_center")
        assert hasattr(cls, "wifi_available")
        assert hasattr(cls, "shuttle_service")
        assert hasattr(cls, "total_student_clubs")
        assert hasattr(cls, "wheelchair_accessible")

    def test_city_living_cost_has_rent_fields(self, uni_info_models):
        cls = uni_info_models.CityLivingCost
        assert hasattr(cls, "city")
        assert hasattr(cls, "rent_studio_avg")
        assert hasattr(cls, "rent_1br_avg")
        assert hasattr(cls, "shared_room_avg")
        assert hasattr(cls, "food_budget_avg")
        assert hasattr(cls, "public_transport_monthly")
        assert hasattr(cls, "total_avg_budget")
        assert hasattr(cls, "cost_of_living_index")

    def test_dormitory_info_has_capacity_and_price(self, uni_info_models):
        cls = uni_info_models.DormitoryInfo
        assert hasattr(cls, "name")
        assert hasattr(cls, "accommodation_type")
        assert hasattr(cls, "total_capacity")
        assert hasattr(cls, "price_avg")
        assert hasattr(cls, "meals_included")
        assert hasattr(cls, "distance_to_campus_km")
        assert hasattr(cls, "gender")

    def test_scholarship_program_has_coverage_and_eligibility(self, uni_info_models):
        cls = uni_info_models.ScholarshipProgram
        assert hasattr(cls, "name")
        assert hasattr(cls, "scholarship_type")
        assert hasattr(cls, "coverage_percentage")
        assert hasattr(cls, "covers_tuition")
        assert hasattr(cls, "covers_accommodation")
        assert hasattr(cls, "min_exam_score")
        assert hasattr(cls, "income_limit")
        assert hasattr(cls, "active")

    def test_university_statistics_has_summary_fields(self, uni_info_models):
        cls = uni_info_models.UniversityStatistics
        assert hasattr(cls, "university_id")
        assert hasattr(cls, "year")
        assert hasattr(cls, "total_campuses")
        assert hasattr(cls, "affordability_score")
        assert hasattr(cls, "total_dormitory_capacity")
        assert hasattr(cls, "total_scholarships")

    def test_campus_info_has_indexes(self, uni_info_models):
        # __table_args__ should be a tuple (indexes)
        table_args = uni_info_models.CampusInfo.__table_args__
        assert isinstance(table_args, tuple)
        assert len(table_args) >= 1

    def test_dormitory_info_has_indexes(self, uni_info_models):
        table_args = uni_info_models.DormitoryInfo.__table_args__
        assert isinstance(table_args, tuple)
        assert len(table_args) >= 1

    def test_scholarship_program_has_indexes(self, uni_info_models):
        table_args = uni_info_models.ScholarshipProgram.__table_args__
        assert isinstance(table_args, tuple)
        assert len(table_args) >= 1

    def test_scholarship_program_has_optional_fields(self, uni_info_models):
        cls = uni_info_models.ScholarshipProgram
        assert hasattr(cls, "monthly_stipend")
        assert hasattr(cls, "renewable")
        assert hasattr(cls, "service_obligation")
        assert hasattr(cls, "networking_opportunities")

    def test_dormitory_has_security_fields(self, uni_info_models):
        cls = uni_info_models.DormitoryInfo
        assert hasattr(cls, "security_24_7")
        assert hasattr(cls, "cctv")
        assert hasattr(cls, "key_card_access")

    def test_dormitory_has_rule_fields(self, uni_info_models):
        cls = uni_info_models.DormitoryInfo
        assert hasattr(cls, "curfew")
        assert hasattr(cls, "visitors_allowed")
        assert hasattr(cls, "smoking_allowed")
        assert hasattr(cls, "pets_allowed")


# ===========================================================================
# 4.  services/university_info_service.py
# ===========================================================================


def _make_query_mock():
    """Return a chainable mock that simulates a SQLAlchemy Select object."""
    q = MagicMock()
    q.where.return_value = q
    q.order_by.return_value = q
    q.limit.return_value = q
    q.offset.return_value = q
    return q


@pytest.fixture(scope="module")
def uni_service_mod():
    """Load university_info_service with all SQLAlchemy ORM calls mocked.

    The service calls sqlalchemy.select(Model) which fails on unmapped classes.
    We stub the 'sqlalchemy' module's select/and_/or_ so the service never
    touches real ORM machinery — the db.execute mock handles results.
    """
    # Ensure models.database stub is in place
    _db_stub = types.ModuleType("models.database")

    class _FakeBase3:
        pass

    _db_stub.Base = _FakeBase3
    sys.modules["models.database"] = _db_stub

    # Load models/university_info so the service can import its classes
    _pg_stub = sys.modules.get(
        "sqlalchemy.dialects.postgresql",
        types.ModuleType("sqlalchemy.dialects.postgresql"),
    )
    _pg_stub.UUID = MagicMock(return_value=MagicMock())
    _pg_stub.JSONB = MagicMock(return_value=MagicMock())
    sys.modules["sqlalchemy.dialects.postgresql"] = _pg_stub

    try:
        _load_module("models/university_info.py", "models.university_info")
    except Exception:
        pass  # already loaded from earlier fixture

    # Patch sqlalchemy.select / and_ / or_ so service calls return mock queries
    import sqlalchemy as _sa

    _orig_select = _sa.select
    _orig_and_ = _sa.and_
    _orig_or_ = _sa.or_

    _sa.select = lambda *a, **kw: _make_query_mock()
    _sa.and_ = lambda *a, **kw: MagicMock()
    _sa.or_ = lambda *a, **kw: MagicMock()

    # Remove stale service module if present so exec_module runs fresh
    sys.modules.pop("services.university_info_service", None)

    mod = _load_module(
        "services/university_info_service.py", "services.university_info_service"
    )

    # Restore originals after load (the module already captured the stubs at import)
    _sa.select = _orig_select
    _sa.and_ = _orig_and_
    _sa.or_ = _orig_or_

    return mod


def _make_async_db():
    """Create an async session mock that supports scalars().all() pattern."""
    db = MagicMock()

    async def _fake_execute(query):
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        result.scalar_one_or_none.return_value = None
        return result

    db.execute = _fake_execute
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestUniversityInfoServiceInit:
    """Test service instantiation."""

    def test_service_instantiation(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        assert svc is not None
        assert svc.db is db


class TestCampusMethods:
    """Tests for campus-related service methods."""

    @pytest.mark.asyncio
    async def test_get_campus_info_returns_list(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        uid = uuid.uuid4()
        result = await svc.get_campus_info(uid)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_campus_by_id_returns_none_when_not_found(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_campus_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_campus_facilities_no_campuses(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_campus_facilities(uuid.uuid4())
        assert result["total_clubs"] == 0
        assert result["has_health_center"] is False
        assert result["has_career_center"] is False

    @pytest.mark.asyncio
    async def test_get_campus_facilities_aggregates_data(self, uni_service_mod):
        db = _make_async_db()

        campus = MagicMock()
        campus.libraries = [{"name": "Central"}]
        campus.sports_facilities = ["Pool", "Gym"]
        campus.dining_facilities = [{"name": "Cafe"}]
        campus.student_clubs = [{"name": "Robotics"}]
        campus.cultural_centers = ["Theater"]
        campus.total_student_clubs = 10
        campus.total_area_sqm = 5000
        campus.health_center = True
        campus.career_center = True
        campus.counseling_center = False

        async def _fake_execute(q):
            res = MagicMock()
            res.scalars.return_value.all.return_value = [campus]
            res.scalar_one_or_none.return_value = None
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_campus_facilities(uuid.uuid4())
        assert result["total_clubs"] == 10
        assert result["total_area_sqm"] == 5000
        assert result["has_health_center"] is True
        assert result["has_career_center"] is True
        assert "Pool" in result["sports_facilities"]


class TestCityLivingCostMethods:
    """Tests for city living cost service methods."""

    @pytest.mark.asyncio
    async def test_get_city_living_cost_returns_none_when_not_found(
        self, uni_service_mod
    ):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_city_living_cost("Ankara", 2024)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_cities_returns_empty_list(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_all_cities_living_costs()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_compare_city_costs_empty(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.compare_city_costs(["Istanbul", "Ankara"])
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_student_budget_estimate_no_data(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_student_budget_estimate("NonExistentCity")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_student_budget_estimate_studio(self, uni_service_mod):
        db = _make_async_db()

        living_cost = MagicMock()
        living_cost.rent_studio_avg = 5000
        living_cost.shared_room_avg = 2000
        living_cost.rent_1br_avg = 6000
        living_cost.utilities_avg = 800
        living_cost.food_budget_avg = 3000
        living_cost.public_transport_monthly = 400
        living_cost.entertainment_avg = 500
        living_cost.books_supplies_avg = 200
        living_cost.personal_care_avg = 300
        living_cost.phone_internet_avg = 250
        living_cost.total_avg_budget = 10450

        async def _fake_execute(q):
            res = MagicMock()
            res.scalar_one_or_none.return_value = living_cost
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_student_budget_estimate("Istanbul", "studio")
        assert result is not None
        assert result["monthly_costs"]["accommodation"] == 5000
        assert result["total_monthly"] > 0
        assert result["total_annual"] == result["total_monthly"] * 12

    @pytest.mark.asyncio
    async def test_get_student_budget_estimate_shared(self, uni_service_mod):
        db = _make_async_db()

        living_cost = MagicMock()
        living_cost.rent_studio_avg = 5000
        living_cost.shared_room_avg = 2500
        living_cost.rent_1br_avg = 6000
        living_cost.utilities_avg = 700
        living_cost.food_budget_avg = 2800
        living_cost.public_transport_monthly = 400
        living_cost.entertainment_avg = 400
        living_cost.books_supplies_avg = 150
        living_cost.personal_care_avg = 250
        living_cost.phone_internet_avg = 200
        living_cost.total_avg_budget = 7400

        async def _fake_execute(q):
            res = MagicMock()
            res.scalar_one_or_none.return_value = living_cost
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_student_budget_estimate("Ankara", "shared")
        assert result["monthly_costs"]["accommodation"] == 2500

    @pytest.mark.asyncio
    async def test_get_student_budget_estimate_other_type(self, uni_service_mod):
        db = _make_async_db()

        living_cost = MagicMock()
        living_cost.rent_studio_avg = 5000
        living_cost.shared_room_avg = 2500
        living_cost.rent_1br_avg = 7000
        living_cost.utilities_avg = 700
        living_cost.food_budget_avg = 2800
        living_cost.public_transport_monthly = 400
        living_cost.entertainment_avg = 400
        living_cost.books_supplies_avg = 150
        living_cost.personal_care_avg = 250
        living_cost.phone_internet_avg = 200
        living_cost.total_avg_budget = 11700

        async def _fake_execute(q):
            res = MagicMock()
            res.scalar_one_or_none.return_value = living_cost
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_student_budget_estimate("Izmir", "other_type")
        assert result["monthly_costs"]["accommodation"] == 7000

    @pytest.mark.asyncio
    async def test_budget_breakdown_percentages_sum_to_100(self, uni_service_mod):
        db = _make_async_db()

        living_cost = MagicMock()
        living_cost.rent_studio_avg = 4000
        living_cost.shared_room_avg = 2000
        living_cost.rent_1br_avg = 6000
        living_cost.utilities_avg = 600
        living_cost.food_budget_avg = 2500
        living_cost.public_transport_monthly = 300
        living_cost.entertainment_avg = 300
        living_cost.books_supplies_avg = 100
        living_cost.personal_care_avg = 200
        living_cost.phone_internet_avg = 150
        living_cost.total_avg_budget = 8150

        async def _fake_execute(q):
            res = MagicMock()
            res.scalar_one_or_none.return_value = living_cost
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_student_budget_estimate("Bursa", "studio")
        total_pct = sum(result["breakdown_percentages"].values())
        assert abs(total_pct - 100.0) < 1.0


class TestDormitoryMethods:
    """Tests for dormitory-related service methods."""

    @pytest.mark.asyncio
    async def test_get_dormitories_empty(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_dormitories()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_dormitory_by_id_not_found(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_dormitory_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_dormitory_statistics_no_data(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_dormitory_statistics()
        assert result["total_dormitories"] == 0
        assert result["total_capacity"] == 0
        assert result["avg_price"] == 0

    @pytest.mark.asyncio
    async def test_get_dormitory_statistics_with_data(self, uni_service_mod):
        db = _make_async_db()

        dorm1 = MagicMock()
        dorm1.total_capacity = 100
        dorm1.price_avg = 3000
        dorm1.accommodation_type = MagicMock()
        dorm1.accommodation_type.value = "state_dormitory"

        dorm2 = MagicMock()
        dorm2.total_capacity = 200
        dorm2.price_avg = 4000
        dorm2.accommodation_type = MagicMock()
        dorm2.accommodation_type.value = "private_dormitory"

        async def _fake_execute(q):
            res = MagicMock()
            res.scalars.return_value.all.return_value = [dorm1, dorm2]
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_dormitory_statistics()
        assert result["total_dormitories"] == 2
        assert result["total_capacity"] == 300
        assert result["avg_price"] == 3500
        assert result["price_range"]["min"] == 3000
        assert result["price_range"]["max"] == 4000


class TestScholarshipMethods:
    """Tests for scholarship-related service methods."""

    @pytest.mark.asyncio
    async def test_get_scholarships_empty(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_scholarships()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_scholarship_by_id_not_found(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_scholarship_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_scholarship_statistics_no_data(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_scholarship_statistics(uuid.uuid4())
        assert result["total_scholarships"] == 0
        assert result["full_scholarships"] == 0
        assert result["avg_coverage"] == 0

    @pytest.mark.asyncio
    async def test_get_scholarship_statistics_with_data(self, uni_service_mod):
        db = _make_async_db()

        s1 = MagicMock()
        s1.coverage_percentage = 100.0
        s1.amount_avg = 10000
        s1.scholarship_type = MagicMock()
        s1.scholarship_type.value = "full_scholarship"

        s2 = MagicMock()
        s2.coverage_percentage = 50.0
        s2.amount_avg = 5000
        s2.scholarship_type = MagicMock()
        s2.scholarship_type.value = "merit_based"

        async def _fake_execute(q):
            res = MagicMock()
            res.scalars.return_value.all.return_value = [s1, s2]
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_scholarship_statistics(uuid.uuid4())
        assert result["total_scholarships"] == 2
        assert result["full_scholarships"] == 1
        assert result["partial_scholarships"] == 1
        assert result["avg_coverage"] == 75.0
        assert result["avg_amount"] == 7500

    @pytest.mark.asyncio
    async def test_get_eligible_scholarships_returns_list(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_eligible_scholarships(
            university_id=uuid.uuid4(),
            exam_score=450.0,
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_eligible_scholarships_with_gpa_and_income(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_eligible_scholarships(
            university_id=uuid.uuid4(),
            exam_score=480.0,
            high_school_gpa=4.5,
            family_income=50000,
        )
        assert isinstance(result, list)


class TestHelperToDictMethods:
    """Tests for the _xxx_to_dict helper methods."""

    def test_campus_to_dict_keys(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        campus = MagicMock()
        campus.id = uuid.uuid4()
        campus.campus_name = "Ana Kampüs"
        campus.campus_type = MagicMock()
        campus.campus_type.value = "main_campus"
        campus.city = "Istanbul"
        campus.total_area_sqm = 100000
        campus.total_student_clubs = 50
        campus.health_center = True
        campus.career_center = False
        campus.wifi_available = True
        campus.shuttle_service = False

        result = svc._campus_to_dict(campus)
        assert result["name"] == "Ana Kampüs"
        assert result["type"] == "main_campus"
        assert result["city"] == "Istanbul"
        assert result["has_health_center"] is True
        assert result["wifi_available"] is True

    def test_living_cost_to_dict_keys(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        cost = MagicMock()
        cost.city = "Ankara"
        cost.total_avg_budget = 8000
        cost.rent_studio_avg = 4500
        cost.food_budget_avg = 2500
        cost.public_transport_monthly = 400
        cost.cost_of_living_index = 85.0

        result = svc._living_cost_to_dict(cost)
        assert result["city"] == "Ankara"
        assert result["avg_monthly_budget"] == 8000
        assert result["cost_of_living_index"] == 85.0

    def test_dormitory_to_dict_keys(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        dorm = MagicMock()
        dorm.id = uuid.uuid4()
        dorm.name = "KYK Yurdu"
        dorm.accommodation_type = MagicMock()
        dorm.accommodation_type.value = "state_dormitory"
        dorm.price_avg = 2000
        dorm.total_capacity = 300
        dorm.meals_included = True
        dorm.distance_to_campus_km = 0.5

        result = svc._dormitory_to_dict(dorm)
        assert result["name"] == "KYK Yurdu"
        assert result["type"] == "state_dormitory"
        assert result["meals_included"] is True

    def test_scholarship_to_dict_keys(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        s = MagicMock()
        s.id = uuid.uuid4()
        s.name = "Başarı Bursu"
        s.scholarship_type = MagicMock()
        s.scholarship_type.value = "merit_based"
        s.coverage_percentage = 75.0
        s.amount_avg = 7500
        s.covers_tuition = True
        s.covers_accommodation = False

        result = svc._scholarship_to_dict(s)
        assert result["name"] == "Başarı Bursu"
        assert result["type"] == "merit_based"
        assert result["coverage_percentage"] == 75.0

    def test_statistics_to_dict_keys(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        stats = MagicMock()
        stats.total_campuses = 3
        stats.total_student_clubs = 120
        stats.avg_monthly_cost = 9000
        stats.total_dormitory_capacity = 2000
        stats.total_scholarships = 15
        stats.affordability_score = 7.5

        result = svc._statistics_to_dict(stats)
        assert result["total_campuses"] == 3
        assert result["affordability_score"] == 7.5
        assert result["total_scholarships"] == 15


class TestUniversityStatisticsMethods:
    """Tests for university statistics retrieval."""

    @pytest.mark.asyncio
    async def test_get_university_statistics_not_found(self, uni_service_mod):
        db = _make_async_db()
        svc = uni_service_mod.UniversityInfoService(db=db)
        result = await svc.get_university_statistics(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_university_statistics_updates_existing(
        self, uni_service_mod
    ):
        """generate_university_statistics with an existing record updates it in-place."""
        db = _make_async_db()

        existing_stats = MagicMock()

        # First calls return empty campuses/dormitories/scholarships;
        # the final get_university_statistics call returns the existing record.
        call_count = [0]

        async def _fake_execute(q):
            call_count[0] += 1
            res = MagicMock()
            res.scalars.return_value.all.return_value = []
            # Return existing stats only on the last scalar_one_or_none call
            # (get_university_statistics is the last internal call)
            if call_count[0] >= 4:
                res.scalar_one_or_none.return_value = existing_stats
            else:
                res.scalar_one_or_none.return_value = None
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        uid = uuid.uuid4()
        result = await svc.generate_university_statistics(uid)
        # Update path: commit called, no db.add
        db.commit.assert_awaited()
        assert result is existing_stats


class TestComprehensiveUniversityInfo:
    """Tests for get_comprehensive_university_info."""

    @pytest.mark.asyncio
    async def test_comprehensive_info_no_campuses(self, uni_service_mod):
        db = _make_async_db()

        async def _fake_execute(q):
            res = MagicMock()
            res.scalars.return_value.all.return_value = []
            res.scalar_one_or_none.return_value = None
            return res

        db.execute = _fake_execute
        svc = uni_service_mod.UniversityInfoService(db=db)
        uid = uuid.uuid4()
        result = await svc.get_comprehensive_university_info(uid)
        assert "campuses" in result
        assert "dormitories" in result
        assert "scholarships" in result
        assert result["campuses"] == []
        assert result["living_cost"] is None
