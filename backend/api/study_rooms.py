"""Study Rooms API — S197 minimal CRUD impl.

Replaces `study_rooms_stub.py` (S180 #5 stub) with real DB-backed CRUD for
the core endpoints frontend depends on for room lifecycle:

- POST   /api/v1/study-rooms              — create room (alias of /create)
- POST   /api/v1/study-rooms/create       — create room (owner becomes first member)
- GET    /api/v1/study-rooms/my-rooms     — owned + joined rooms
- GET    /api/v1/study-rooms/joined       — only joined (non-owner) rooms (S198 W4.1)
- GET    /api/v1/study-rooms/{room_id}    — room detail (must be member or PUBLIC)
- GET    /api/v1/study-rooms/{room_id}/members — room member list (S198 W4.1)
- DELETE /api/v1/study-rooms/{room_id}    — soft delete (owner only)
- POST   /api/v1/study-rooms/{room_id}/join — join (PUBLIC or via invitation)
- POST   /api/v1/study-rooms/{room_id}/leave — leave (non-owner; owner must delete)

Scope explicitly OUT for this iteration:
- Messages, files, whiteboard, video — remain in stub (501) until next sprint
- Password-protected rooms (visibility=PASSWORD)
- Invitation flow (handled by separate RoomInvitation table)
- Member kick/ban/promote
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_session
from core.dependencies import AuthenticatedUser, get_current_user
from models.study_room import (
    MemberRole,
    MemberStatus,
    RoomMember,
    RoomStatus,
    RoomVisibility,
    StudyRoom,
)
from models.user_models import User

router = APIRouter(prefix="/api/v1/study-rooms", tags=["study-rooms"])


class StudyRoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    topic: str | None = Field(None, max_length=255)
    visibility: str = Field("private", pattern="^(public|private)$")
    max_members: int = Field(50, ge=2, le=500)
    tags: list[str] | None = Field(default_factory=list)


class StudyRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    topic: str | None
    owner_id: str
    status: str
    visibility: str
    max_members: int
    current_member_count: int
    tags: list[str]
    created_at: datetime
    user_role: str | None = None


class StudyRoomListResponse(BaseModel):
    rooms: list[StudyRoomResponse]
    total: int


class RoomMemberResponse(BaseModel):
    """Member entry in a room (S198 W4.1)."""

    user_id: str
    username: str
    full_name: str | None = None
    role: str
    status: str
    joined_at: datetime | None = None


class RoomMembersListResponse(BaseModel):
    members: list[RoomMemberResponse]
    total: int


def _serialize_member(member: RoomMember, user: User) -> RoomMemberResponse:
    """Convert RoomMember + User join row to response."""
    role = member.role.value if hasattr(member.role, "value") else str(member.role)
    status = (
        member.status.value if hasattr(member.status, "value") else str(member.status)
    )
    full_name = (
        " ".join(part for part in (user.first_name, user.last_name) if part) or None
    )
    return RoomMemberResponse(
        user_id=user.id,
        username=user.username,
        full_name=full_name,
        role=role,
        status=status,
        joined_at=member.joined_at,
    )


def _serialize_room(room: StudyRoom, user_role: str | None = None) -> StudyRoomResponse:
    """Convert ORM row to response, with optional caller's role attached."""
    return StudyRoomResponse(
        id=room.id,
        name=room.name,
        description=room.description,
        topic=room.topic,
        owner_id=room.owner_id,
        status=room.status.value if hasattr(room.status, "value") else str(room.status),
        visibility=(
            room.visibility.value
            if hasattr(room.visibility, "value")
            else str(room.visibility)
        ),
        max_members=room.max_members,
        current_member_count=room.current_member_count,
        tags=list(room.tags or []),
        created_at=room.created_at,
        user_role=user_role,
    )


async def _get_room_or_404(db: AsyncSession, room_id: str) -> StudyRoom:
    result = await db.execute(
        select(StudyRoom).where(
            and_(StudyRoom.id == room_id, StudyRoom.status != RoomStatus.DELETED)
        )
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise HTTPException(status_code=404, detail="Çalışma odası bulunamadı")
    return room


async def _get_membership(
    db: AsyncSession, room_id: str, user_id: str
) -> RoomMember | None:
    result = await db.execute(
        select(RoomMember).where(
            and_(RoomMember.room_id == room_id, RoomMember.user_id == user_id)
        )
    )
    return result.scalar_one_or_none()


@router.post("", response_model=StudyRoomResponse, status_code=201)
@router.post("/create", response_model=StudyRoomResponse, status_code=201)
async def create_room(
    body: StudyRoomCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> StudyRoomResponse:
    """Create a new study room. Caller becomes OWNER + first ACTIVE member.

    Two paths accepted for backwards compatibility:
    - POST /api/v1/study-rooms        (RESTful, S198 W4.1)
    - POST /api/v1/study-rooms/create (legacy, pre-S198)
    """
    visibility = (
        RoomVisibility.PUBLIC if body.visibility == "public" else RoomVisibility.PRIVATE
    )

    room = StudyRoom(
        name=body.name,
        description=body.description,
        topic=body.topic,
        owner_id=str(current_user.id),
        status=RoomStatus.ACTIVE,
        visibility=visibility,
        max_members=body.max_members,
        current_member_count=1,
        tags=body.tags or [],
    )
    db.add(room)
    await db.flush()

    owner_member = RoomMember(
        room_id=room.id,
        user_id=str(current_user.id),
        role=MemberRole.OWNER,
        status=MemberStatus.ACTIVE,
    )
    db.add(owner_member)

    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Oda oluşturulamadı (FK ihlali)"
        ) from e

    await db.refresh(room)
    return _serialize_room(room, user_role=MemberRole.OWNER.value)


@router.get("/my-rooms", response_model=StudyRoomListResponse)
async def my_rooms(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> StudyRoomListResponse:
    """List active rooms where caller is owner or active member."""
    user_id = str(current_user.id)

    result = await db.execute(
        select(StudyRoom, RoomMember.role)
        .join(RoomMember, RoomMember.room_id == StudyRoom.id)
        .where(
            and_(
                RoomMember.user_id == user_id,
                RoomMember.status == MemberStatus.ACTIVE,
                StudyRoom.status == RoomStatus.ACTIVE,
            )
        )
        .order_by(StudyRoom.created_at.desc())
    )
    rows = result.all()

    items = [
        _serialize_room(
            room,
            user_role=role.value if hasattr(role, "value") else str(role),
        )
        for room, role in rows
    ]
    return StudyRoomListResponse(rooms=items, total=len(items))


@router.get("/joined", response_model=StudyRoomListResponse)
async def joined_rooms(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> StudyRoomListResponse:
    """List active rooms where caller is an ACTIVE member but NOT the owner.

    Counterpart to /my-rooms (owned + joined). Frontend StudyRoomList Tab 2
    uses this to show only joined rooms (S198 W4.1).
    """
    user_id = str(current_user.id)

    result = await db.execute(
        select(StudyRoom, RoomMember.role)
        .join(RoomMember, RoomMember.room_id == StudyRoom.id)
        .where(
            and_(
                RoomMember.user_id == user_id,
                RoomMember.status == MemberStatus.ACTIVE,
                StudyRoom.status == RoomStatus.ACTIVE,
                StudyRoom.owner_id != user_id,
            )
        )
        .order_by(StudyRoom.created_at.desc())
    )
    rows = result.all()

    items = [
        _serialize_room(
            room,
            user_role=role.value if hasattr(role, "value") else str(role),
        )
        for room, role in rows
    ]
    return StudyRoomListResponse(rooms=items, total=len(items))


@router.get("/{room_id}", response_model=StudyRoomResponse)
async def room_detail(
    room_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> StudyRoomResponse:
    """Get room detail. Caller must be active member, OR room must be PUBLIC."""
    room = await _get_room_or_404(db, room_id)
    membership = await _get_membership(db, room_id, str(current_user.id))

    is_active_member = (
        membership is not None and membership.status == MemberStatus.ACTIVE
    )
    is_public = room.visibility == RoomVisibility.PUBLIC

    if not (is_active_member or is_public):
        raise HTTPException(status_code=403, detail="Bu odaya erişiminiz yok")

    user_role = None
    if membership is not None:
        user_role = (
            membership.role.value
            if hasattr(membership.role, "value")
            else str(membership.role)
        )
    return _serialize_room(room, user_role=user_role)


@router.get("/{room_id}/members", response_model=RoomMembersListResponse)
async def room_members(
    room_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> RoomMembersListResponse:
    """List members of a room. Only active members of the room can view.

    Returns user_id, username, full_name (first+last), role, status, joined_at
    for each RoomMember row joined with User. (S198 W4.1)
    """
    await _get_room_or_404(db, room_id)

    caller_membership = await _get_membership(db, room_id, str(current_user.id))
    if caller_membership is None or caller_membership.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Bu odanın üyesi değilsiniz")

    result = await db.execute(
        select(RoomMember, User)
        .join(User, User.id == RoomMember.user_id)
        .where(RoomMember.room_id == room_id)
        .order_by(RoomMember.joined_at.asc().nullslast())
    )
    rows = result.all()

    items = [_serialize_member(member, user) for member, user in rows]
    return RoomMembersListResponse(members=items, total=len(items))


@router.delete("/{room_id}", status_code=204)
async def delete_room(
    room_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Soft-delete a room (status → DELETED). Owner only."""
    room = await _get_room_or_404(db, room_id)
    if room.owner_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Yalnızca oda sahibi silebilir")

    room.status = RoomStatus.DELETED
    await db.commit()


@router.post("/{room_id}/join", response_model=StudyRoomResponse)
async def join_room(
    room_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> StudyRoomResponse:
    """Join a room. Requires PUBLIC visibility (private rooms need invite)."""
    room = await _get_room_or_404(db, room_id)
    user_id = str(current_user.id)

    if room.visibility != RoomVisibility.PUBLIC:
        raise HTTPException(
            status_code=403,
            detail="Bu oda davetiye gerektirir",
        )

    existing = await _get_membership(db, room_id, user_id)
    if existing is not None:
        if existing.status == MemberStatus.BANNED:
            raise HTTPException(status_code=403, detail="Bu odadan engellendiniz")
        if existing.status == MemberStatus.ACTIVE:
            return _serialize_room(
                room,
                user_role=(
                    existing.role.value
                    if hasattr(existing.role, "value")
                    else str(existing.role)
                ),
            )
        existing.status = MemberStatus.ACTIVE
        new_role = existing.role
    else:
        if room.current_member_count >= room.max_members:
            raise HTTPException(status_code=409, detail="Oda dolu")
        new_member = RoomMember(
            room_id=room_id,
            user_id=user_id,
            role=MemberRole.MEMBER,
            status=MemberStatus.ACTIVE,
        )
        db.add(new_member)
        new_role = MemberRole.MEMBER
        room.current_member_count = room.current_member_count + 1

    await db.commit()
    await db.refresh(room)
    return _serialize_room(
        room,
        user_role=(new_role.value if hasattr(new_role, "value") else str(new_role)),
    )


@router.post("/{room_id}/leave", status_code=204)
async def leave_room(
    room_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Leave a room. Owner cannot leave (must delete instead)."""
    room = await _get_room_or_404(db, room_id)
    user_id = str(current_user.id)

    if room.owner_id == user_id:
        raise HTTPException(
            status_code=409,
            detail="Oda sahibi ayrılamaz, oda silinmeli",
        )

    membership = await _get_membership(db, room_id, user_id)
    if membership is None or membership.status != MemberStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Bu odanın üyesi değilsiniz")

    await db.delete(membership)
    room.current_member_count = max(1, room.current_member_count - 1)
    await db.commit()
