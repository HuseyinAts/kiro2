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
    StudyRoomCreate,
    StudyRoomListResponse,
    StudyRoomResponse,
    _serialize_room,
    router,
)
from models.study_room import (
    MemberRole,
    RoomStatus,
    RoomVisibility,
    StudyRoom,
)


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
    def test_six_endpoints_registered(self):
        # Filter out OPTIONS/HEAD auto-generated routes
        paths = sorted({r.path for r in router.routes if hasattr(r, "methods")})
        assert len(paths) == 5  # 6 endpoints, 2 share /{room_id} path (GET+DELETE)

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
