"""Tests for Task 51.2 rate limit tier mapping from role lists."""

from core.rate_limit_config import UserTier, get_user_tier_from_roles
from models.enums_db import UserRole


def test_tier_anonymous_when_no_roles():
    assert get_user_tier_from_roles(None) == UserTier.ANONYMOUS
    assert get_user_tier_from_roles([]) == UserTier.ANONYMOUS


def test_tier_admin_super_admin_slug():
    assert get_user_tier_from_roles(["super_admin"]) == UserTier.ADMIN
    assert get_user_tier_from_roles(["SUPER_ADMIN"]) == UserTier.ADMIN


def test_tier_admin_enum_and_legacy_typo():
    assert get_user_tier_from_roles([UserRole.ADMIN]) == UserTier.ADMIN
    assert get_user_tier_from_roles([UserRole.SUPER_ADMIN]) == UserTier.ADMIN
    assert get_user_tier_from_roles(["superadmin"]) == UserTier.ADMIN


def test_tier_teacher_and_premium():
    assert get_user_tier_from_roles(["teacher"]) == UserTier.PREMIUM
    assert get_user_tier_from_roles(["student"], is_premium=True) == UserTier.PREMIUM
    assert get_user_tier_from_roles(["premium"]) == UserTier.PREMIUM


def test_tier_free_student():
    assert get_user_tier_from_roles(["student"]) == UserTier.FREE
