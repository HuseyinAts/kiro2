"""Unit tests for code-based parent<->student linking.

Covers the pure/logic parts of the code-linking flow WITHOUT a live DB:
- compute_initials: Turkish-aware 2-letter derivation
- generate_link_code: 6-digit format, 10-min expiry, unique-code retry loop
- verify_link_code: invalid -> {valid: false}, non-student -> {valid: false},
  valid + existing relation -> relation shape, valid + new relation -> insert path

The AsyncSession is mocked the same way as tests/unit/test_parent_api.py
(AsyncMock + MagicMock results). No PostgreSQL required.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.enums_db import UserRole
from services.parent_service import ParentService, compute_initials

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _result(*, scalar=None, first=None) -> MagicMock:
    """Build a mock SQLAlchemy Result with configured scalar/first returns."""
    res = MagicMock()
    res.scalar_one_or_none.return_value = scalar
    res.first.return_value = first
    return res


def _mock_db(execute_returns=None) -> AsyncMock:
    """Return a mocked AsyncSession.

    execute_returns: if a list -> used as execute side_effect (sequential);
    otherwise a single default result (scalar=None, first=None) is returned.
    """
    db = AsyncMock()
    if execute_returns is None:
        db.execute = AsyncMock(return_value=_result())
    else:
        db.execute = AsyncMock(side_effect=execute_returns)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_child(role=UserRole.STUDENT, first="Ali", last="Yilmaz") -> MagicMock:
    child = MagicMock()
    child.id = "student-001"
    child.role = role
    child.first_name = first
    child.last_name = last
    return child


def _make_link(student_id="student-001") -> MagicMock:
    link = MagicMock()
    link.student_id = student_id
    link.consumed = False
    return link


# ---------------------------------------------------------------------------
# 1. compute_initials (pure)
# ---------------------------------------------------------------------------


class TestComputeInitials:
    @pytest.mark.parametrize(
        "first,last,expected",
        [
            ("Ali", "Yilmaz", "AY"),
            ("Huseyin", "Ates", "HA"),
            ("irem", "sahin", "İS"),  # Turkish i -> İ
            ("ismail", "çelik", "İÇ"),  # i -> İ, ç -> Ç
            ("Ada", "", "A"),
            ("", "", ""),
            (None, None, ""),
            ("  ayse  ", "  demir  ", "AD"),  # strips whitespace
        ],
    )
    def test_initials(self, first, last, expected):
        assert compute_initials(first, last) == expected


# ---------------------------------------------------------------------------
# 2. generate_link_code
# ---------------------------------------------------------------------------


class TestGenerateLinkCode:
    @pytest.mark.asyncio
    async def test_returns_6_digit_code_and_10min_expiry(self):
        """Code is a 6-char digit string; expiry ~= now + 10 minutes."""
        db = _mock_db()  # default result: first()=None -> unique on first try
        svc = ParentService(db)

        before = datetime.now(UTC)
        result = await svc.generate_link_code("student-001")
        after = datetime.now(UTC)

        assert re.fullmatch(r"\d{6}", result["code"]), result["code"]
        # tz-aware and within the expected 10-min window
        exp = result["expires_at"]
        assert exp.tzinfo is not None
        assert before + timedelta(minutes=10) - timedelta(seconds=5) <= exp
        assert exp <= after + timedelta(minutes=10) + timedelta(seconds=5)
        db.add.assert_called_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_leading_zero_codes_preserved(self):
        """A drawn value < 100000 keeps its leading zeros (str, not int)."""
        db = _mock_db()
        svc = ParentService(db)
        with patch("services.parent_service.secrets.randbelow", return_value=42):
            result = await svc.generate_link_code("student-001")
        assert result["code"] == "000042"

    @pytest.mark.asyncio
    async def test_retries_on_collision(self):
        """First drawn code collides (row exists) -> retry until unique."""
        # execute call order: 1) UPDATE invalidate, 2) collision select,
        # 3) unique select
        db = _mock_db(
            execute_returns=[
                _result(),  # UPDATE prior codes
                _result(first=("existing-id",)),  # collision
                _result(first=None),  # unique
            ]
        )
        svc = ParentService(db)
        with patch(
            "services.parent_service.secrets.randbelow",
            side_effect=[111111, 222222],
        ):
            result = await svc.generate_link_code("student-001")
        assert result["code"] == "222222"
        assert db.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_raises_when_no_unique_code_found(self):
        """50 consecutive collisions -> ValueError."""
        db = _mock_db()
        db.execute = AsyncMock(return_value=_result(first=("dup",)))
        svc = ParentService(db)
        with pytest.raises(ValueError, match="Benzersiz"):
            await svc.generate_link_code("student-001")


# ---------------------------------------------------------------------------
# 3. verify_link_code
# ---------------------------------------------------------------------------


class TestVerifyLinkCode:
    @pytest.mark.asyncio
    async def test_invalid_code_returns_valid_false(self):
        """No matching (unconsumed, unexpired) code -> {valid: False}."""
        db = _mock_db(execute_returns=[_result(scalar=None)])
        svc = ParentService(db)

        out = await svc.verify_link_code("parent-001", "000000")

        assert out == {"valid": False}
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_code_returns_valid_false(self):
        """Empty/blank code never matches -> {valid: False}."""
        db = _mock_db(execute_returns=[_result(scalar=None)])
        svc = ParentService(db)
        out = await svc.verify_link_code("parent-001", "   ")
        assert out == {"valid": False}

    @pytest.mark.asyncio
    async def test_non_student_target_returns_valid_false(self):
        """Code resolves to a non-STUDENT account -> {valid: False}."""
        db = _mock_db(
            execute_returns=[
                _result(scalar=_make_link()),  # code found
                _result(scalar=_make_child(role=UserRole.TEACHER)),  # not student
            ]
        )
        svc = ParentService(db)

        out = await svc.verify_link_code("parent-001", "123456")

        assert out == {"valid": False}
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_valid_code_existing_relation_returns_shape(self):
        """Valid code + existing relation -> returns that relation's shape."""
        existing_relation = MagicMock()
        existing_relation.id = 42
        db = _mock_db(
            execute_returns=[
                _result(scalar=_make_link()),  # code found
                _result(scalar=_make_child()),  # student
                _result(scalar=existing_relation),  # relation already exists
            ]
        )
        svc = ParentService(db)

        out = await svc.verify_link_code("parent-001", "123456")

        assert out["valid"] is True
        assert out["child_name"] == "Ali Yilmaz"
        assert out["child_initials"] == "AY"
        assert out["relation_id"] == "42"
        # existing relation -> no new insert, but code is consumed
        db.add.assert_not_called()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_valid_code_new_relation_creates_and_consumes(self):
        """Valid code + no existing relation -> insert approved=False + consume."""
        db = _mock_db(
            execute_returns=[
                _result(scalar=_make_link()),  # code found
                _result(scalar=_make_child()),  # student
                _result(scalar=None),  # no existing relation
            ]
        )

        # flush() assigns the DB-generated id to the freshly-added relation
        # (real ParentChildRelation instance; id is None until flush).
        def _assign_id():
            db.add.call_args.args[0].id = 99

        db.flush = AsyncMock(side_effect=_assign_id)
        svc = ParentService(db)

        out = await svc.verify_link_code("parent-001", "123456")

        assert out["valid"] is True
        assert out["child_name"] == "Ali Yilmaz"
        assert out["child_initials"] == "AY"
        assert out["relation_id"] == "99"
        # a new relation was inserted with approved=False
        db.add.assert_called_once()
        added = db.add.call_args.args[0]
        assert added.parent_id == "parent-001"
        assert added.child_id == "student-001"
        assert added.approved is False
        db.flush.assert_awaited_once()
        db.commit.assert_awaited_once()
