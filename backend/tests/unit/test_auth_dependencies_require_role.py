"""core.auth_dependencies.require_role — SUPER_ADMIN admin yüzey parity."""

from core.auth_dependencies import require_role


def test_require_role_admin_includes_super_admin() -> None:
    dep = require_role("ADMIN")
    assert "admin" in dep.required_roles
    assert "super_admin" in dep.required_roles


def test_require_role_teacher_only_does_not_add_super_admin() -> None:
    dep = require_role("TEACHER")
    assert "teacher" in dep.required_roles
    assert "super_admin" not in dep.required_roles


def test_require_role_empty_defaults_to_admin_and_super_admin() -> None:
    dep = require_role()
    assert dep.required_roles == ["admin", "super_admin"]
