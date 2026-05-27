"""S197: Study Rooms minimal CRUD test suite.

Covers:
- Pydantic schema validation (StudyRoomCreate, StudyRoomResponse)
- _serialize_room helper (enum value access, tags default)
- Router registration smoke
- 6 endpoint inventory check

Out of scope for this file (require DB fixtures + auth):
- create_room / join_room / leave_room DB round-trip (covered by integration tests)
- Concurrency on current_member_count
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from api.study_rooms import (
    RoomMemberResponse,
    RoomMembersListResponse,
    StudyRoomCreate,
    StudyRoomListResponse,
    StudyRoomResponse,
    _serialize_member,
    _serialize_room,
    router,
)
from models.study_room import (
    MemberRole,
    MemberStatus,
    RoomMember,
    RoomStatus,
    RoomVisibility,
    StudyRoom,
)


def _make_room_member(role=MemberRole.MEMBER, status=MemberStatus.ACTIVE):
    """Test fixture: RoomMember instance for serialize tests."""
    member = RoomMember(
        room_id="room-1",
        user_id="user-2",
        role=role,
        status=status,
    )
    member.joined_at = datetime(2026, 5, 27, tzinfo=UTC)
    return member


def _make_user(
    user_id="user-2",
    username="ali",
    first_name="Ali",
    last_name="Yılmaz",
):
    """Test fixture: User instance for serialize tests (no DB)."""
    # User has SQLAlchemy descriptors; build a plain object that walks like a duck.
    user = type(
        "U",
        (),
        {
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
        },
    )()
    return user


class TestStudyRoomCreate:
    def test_minimal_valid(self):
        body = StudyRoomCreate(name="Matematik TYT")
        assert body.name == "Matematik TYT"
        assert body.visibility == "private"
        assert body.max_members == 50
        assert body.tags == []

    def test_public_visibility(self):
        body = StudyRoomCreate(name="Public room", visibility="public")
        assert body.visibility == "public"

    def test_password_visibility_rejected(self):
        with pytest.raises(ValidationError):
            StudyRoomCreate(name="X", visibility="password")

    def test_invalid_visibility(self):
        with pytest.raises(ValidationError):
            StudyRoomCreate(name="X", visibility="anything")

    def test_name_required(self):
        with pytest.raises(ValidationError):
            StudyRoomCreate(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            StudyRoomCreate(name="x" * 256)

    def test_max_members_lower_bound(self):
        with pytest.raises(ValidationError):
            StudyRoomCreate(name="X", max_members=1)

    def test_max_members_upper_bound(self):
        with pytest.raises(ValidationError):
            StudyRoomCreate(name="X", max_members=501)

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            StudyRoomCreate(name="X", description="d" * 2001)

    def test_tags_default(self):
        body = StudyRoomCreate(name="X")
        assert body.tags == []

    def test_tags_custom(self):
        body = StudyRoomCreate(name="X", tags=["matematik", "tyt"])
        assert body.tags == ["matematik", "tyt"]


class TestSerializeRoom:
    def _make_room(
        self,
        status=RoomStatus.ACTIVE,
        visibility=RoomVisibility.PRIVATE,
        tags=None,
    ) -> StudyRoom:
        room = StudyRoom(
            id="room-uuid-1",
            name="Test Room",
            description=None,
            topic="matematik",
            owner_id="user-1",
            status=status,
            visibility=visibility,
            max_members=10,
            current_member_count=1,
            tags=tags or [],
        )
        room.created_at = datetime(2026, 5, 23, tzinfo=UTC)
        return room

    def test_serialize_default_no_role(self):
        room = self._make_room()
        result = _serialize_room(room)
        assert isinstance(result, StudyRoomResponse)
        assert result.id == "room-uuid-1"
        assert result.user_role is None
        assert result.status == "active"
        assert result.visibility == "private"

    def test_serialize_with_owner_role(self):
        room = self._make_room()
        result = _serialize_room(room, user_role=MemberRole.OWNER.value)
        assert result.user_role == "owner"

    def test_serialize_enum_string_fallback(self):
        room = self._make_room()
        room.status = "active"
        room.visibility = "public"
        result = _serialize_room(room)
        assert result.status == "active"
        assert result.visibility == "public"

    def test_serialize_tags_none_safe(self):
        room = self._make_room(tags=None)
        result = _serialize_room(room)
        assert result.tags == []

    def test_serialize_tags_preserved(self):
        room = self._make_room(tags=["geometri", "tyt"])
        result = _serialize_room(room)
        assert result.tags == ["geometri", "tyt"]

    def test_public_room(self):
        room = self._make_room(visibility=RoomVisibility.PUBLIC)
        result = _serialize_room(room)
        assert result.visibility == "public"


class TestRouterRegistration:
    def test_endpoint_count(self):
        # Filter out OPTIONS/HEAD auto-generated routes
        # Distinct paths after S198 W4.1 additions:
        #   "" (POST create alias), /create, /my-rooms, /joined,
        #   /{room_id}, /{room_id}/members, /{room_id}/join, /{room_id}/leave
        paths = sorted({r.path for r in router.routes if hasattr(r, "methods")})
        assert len(paths) == 8

    def test_create_endpoint_exists(self):
        assert any(
            r.path == "/api/v1/study-rooms/create" and "POST" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_my_rooms_endpoint_exists(self):
        assert any(
            r.path == "/api/v1/study-rooms/my-rooms" and "GET" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_join_endpoint_exists(self):
        assert any(
            r.path == "/api/v1/study-rooms/{room_id}/join" and "POST" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_leave_endpoint_exists(self):
        assert any(
            r.path == "/api/v1/study-rooms/{room_id}/leave" and "POST" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_room_detail_get(self):
        assert any(
            r.path == "/api/v1/study-rooms/{room_id}" and "GET" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_room_delete(self):
        assert any(
            r.path == "/api/v1/study-rooms/{room_id}" and "DELETE" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_router_prefix(self):
        assert router.prefix == "/api/v1/study-rooms"

    def test_router_tags(self):
        assert "study-rooms" in router.tags


class TestStudyRoomListResponse:
    def test_empty_list(self):
        resp = StudyRoomListResponse(rooms=[], total=0)
        assert resp.rooms == []
        assert resp.total == 0

    def test_with_rooms(self):
        room_data = StudyRoomResponse(
            id="r1",
            name="N",
            description=None,
            topic=None,
            owner_id="u1",
            status="active",
            visibility="public",
            max_members=10,
            current_member_count=2,
            tags=[],
            created_at=datetime(2026, 5, 23, tzinfo=UTC),
        )
        resp = StudyRoomListResponse(rooms=[room_data], total=1)
        assert resp.total == 1
        assert resp.rooms[0].id == "r1"


# ============================================================
# S198 W4.1 — Joined/Members/Create-alias endpoints
# ============================================================


class TestJoinedRoomsEndpoint:
    """GAP 1: GET /api/v1/study-rooms/joined registration."""

    def test_joined_endpoint_registered(self):
        assert any(
            r.path == "/api/v1/study-rooms/joined" and "GET" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_joined_path_resolves_before_room_id(self):
        # Path order matters: /joined must register BEFORE /{room_id}
        # otherwise FastAPI captures "joined" as room_id parameter.
        paths = [r.path for r in router.routes if hasattr(r, "methods")]
        joined_idx = paths.index("/api/v1/study-rooms/joined")
        room_id_idx = paths.index("/api/v1/study-rooms/{room_id}")
        assert joined_idx < room_id_idx


class TestMembersEndpoint:
    """GAP 2: GET /api/v1/study-rooms/{room_id}/members."""

    def test_members_endpoint_registered(self):
        assert any(
            r.path == "/api/v1/study-rooms/{room_id}/members" and "GET" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_serialize_member_basic(self):
        member = _make_room_member(role=MemberRole.OWNER)
        user = _make_user(user_id="u1", username="huseyin")
        result = _serialize_member(member, user)
        assert isinstance(result, RoomMemberResponse)
        assert result.user_id == "u1"
        assert result.username == "huseyin"
        assert result.role == "owner"
        assert result.status == "active"
        assert result.full_name == "Ali Yılmaz"
        assert result.joined_at == datetime(2026, 5, 27, tzinfo=UTC)

    def test_serialize_member_partial_name(self):
        member = _make_room_member()
        user = _make_user(first_name="Ali", last_name=None)
        result = _serialize_member(member, user)
        assert result.full_name == "Ali"

    def test_serialize_member_no_name(self):
        member = _make_room_member()
        user = _make_user(first_name=None, last_name=None)
        result = _serialize_member(member, user)
        assert result.full_name is None

    def test_serialize_member_banned_status(self):
        member = _make_room_member(role=MemberRole.MEMBER, status=MemberStatus.BANNED)
        user = _make_user()
        result = _serialize_member(member, user)
        assert result.status == "banned"

    def test_members_list_response_empty(self):
        resp = RoomMembersListResponse(members=[], total=0)
        assert resp.members == []
        assert resp.total == 0

    def test_members_list_response_with_entries(self):
        member = _make_room_member(role=MemberRole.MEMBER)
        user = _make_user()
        entry = _serialize_member(member, user)
        resp = RoomMembersListResponse(members=[entry], total=1)
        assert resp.total == 1
        assert resp.members[0].username == "ali"


class TestCreateAliasEndpoint:
    """GAP 3: POST /api/v1/study-rooms accepted as alias of /create."""

    def test_root_post_registered(self):
        assert any(
            r.path == "/api/v1/study-rooms" and "POST" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_create_legacy_still_registered(self):
        # Backwards compatibility: /create path must still work
        assert any(
            r.path == "/api/v1/study-rooms/create" and "POST" in r.methods
            for r in router.routes
            if hasattr(r, "methods")
        )

    def test_both_paths_share_same_handler(self):
        # Both POST routes should bind to the same create_room callable
        post_routes = [
            r
            for r in router.routes
            if hasattr(r, "methods")
            and "POST" in r.methods
            and r.path in ("/api/v1/study-rooms", "/api/v1/study-rooms/create")
        ]
        assert len(post_routes) == 2
        assert post_routes[0].endpoint is post_routes[1].endpoint
