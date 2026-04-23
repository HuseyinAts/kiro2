"""
Task 109: Study Room Service

Service for managing study rooms, members, chat, and file sharing.
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.study_room import (
    FileType,
    FileVersion,
    MemberRole,
    MemberStatus,
    MessageType,
    RoomChatMessage,
    RoomInvitation,
    RoomMember,
    RoomSettings,
    RoomStatus,
    RoomVisibility,
    SharedFile,
    StudyRoom,
)

logger = logging.getLogger(__name__)


class StudyRoomService:
    """Service for study room management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 109.1: Room Creation and Settings
    # ============================================================

    async def create_room(
        self,
        owner_id: UUID,
        name: str,
        description: str,
        topic: str | None = None,
        visibility: RoomVisibility = RoomVisibility.PRIVATE,
        password: str | None = None,
        max_members: int = 50,
        tags: list[str] | None = None,
    ) -> StudyRoom:
        """Create new study room"""
        room = StudyRoom(
            owner_id=owner_id,
            name=name,
            description=description,
            topic=topic,
            visibility=visibility,
            max_members=max_members,
            tags=tags or [],
            current_member_count=1,  # Owner is first member
        )

        # Hash password if provided
        if password and visibility == RoomVisibility.PASSWORD:
            room.password_hash = self._hash_password(password)

        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)

        # Add owner as first member
        await self.add_member(room.id, owner_id, MemberRole.OWNER)

        # Create default settings
        settings = RoomSettings(room_id=room.id)
        self.db.add(settings)
        await self.db.commit()

        logger.info(f"Study room created: {room.id} by {owner_id}")
        return room

    async def get_room(self, room_id: UUID) -> StudyRoom | None:
        """Get room by ID"""
        query = select(StudyRoom).where(StudyRoom.id == room_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_room(self, room_id: UUID, **kwargs) -> StudyRoom | None:
        """Update room settings"""
        room = await self.get_room(room_id)
        if not room:
            return None

        # Handle password update
        if "password" in kwargs:
            password = kwargs.pop("password")
            if password:
                room.password_hash = self._hash_password(password)

        for key, value in kwargs.items():
            if hasattr(room, key):
                setattr(room, key, value)

        room.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(room)

        return room

    async def delete_room(self, room_id: UUID) -> bool:
        """Soft delete room"""
        room = await self.get_room(room_id)
        if not room:
            return False

        room.status = RoomStatus.DELETED
        await self.db.commit()
        return True

    async def verify_room_password(self, room_id: UUID, password: str) -> bool:
        """Verify room password"""
        room = await self.get_room(room_id)
        if not room or not room.password_hash:
            return False

        return room.password_hash == self._hash_password(password)

    # ============================================================
    # Task 109.2: Member Management
    # ============================================================

    async def add_member(
        self,
        room_id: UUID,
        user_id: UUID,
        role: MemberRole = MemberRole.MEMBER,
        invited_by: UUID | None = None,
    ) -> RoomMember:
        """Add member to room"""
        member = RoomMember(
            room_id=room_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
            status=MemberStatus.ACTIVE,
        )

        # Set permissions based on role
        if role == MemberRole.OWNER or role == MemberRole.ADMIN:
            member.can_invite_members = True
            member.can_delete_messages = True
            member.can_delete_files = True
        elif role == MemberRole.MODERATOR:
            member.can_delete_messages = True

        self.db.add(member)

        # Update room member count
        room = await self.get_room(room_id)
        if room:
            room.current_member_count += 1

        await self.db.commit()
        await self.db.refresh(member)

        logger.info(f"Member added to room {room_id}: {user_id}")
        return member

    async def remove_member(self, room_id: UUID, user_id: UUID) -> bool:
        """Remove member from room"""
        query = select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            return False

        await self.db.delete(member)

        # Update room member count
        room = await self.get_room(room_id)
        if room and room.current_member_count > 0:
            room.current_member_count -= 1

        await self.db.commit()
        return True

    async def update_member_role(
        self, room_id: UUID, user_id: UUID, new_role: MemberRole
    ) -> RoomMember | None:
        """Update member role"""
        query = select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            return None

        member.role = new_role

        # Update permissions based on new role
        if new_role in [MemberRole.OWNER, MemberRole.ADMIN]:
            member.can_invite_members = True
            member.can_delete_messages = True
            member.can_delete_files = True
        elif new_role == MemberRole.MODERATOR:
            member.can_delete_messages = True
            member.can_invite_members = False
            member.can_delete_files = False

        await self.db.commit()
        await self.db.refresh(member)

        return member

    async def get_room_members(
        self, room_id: UUID, status: MemberStatus | None = MemberStatus.ACTIVE
    ) -> list[RoomMember]:
        """Get all members of a room"""
        query = select(RoomMember).where(RoomMember.room_id == room_id)

        if status:
            query = query.where(RoomMember.status == status)

        query = query.order_by(RoomMember.role, RoomMember.joined_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def ban_member(self, room_id: UUID, user_id: UUID) -> RoomMember | None:
        """Ban member from room"""
        query = select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            return None

        member.status = MemberStatus.BANNED
        member.can_send_messages = False
        member.can_share_files = False

        await self.db.commit()
        await self.db.refresh(member)

        return member

    # ============================================================
    # Task 109.2: Invitations
    # ============================================================

    async def create_invitation(
        self,
        room_id: UUID,
        inviter_id: UUID,
        invitee_id: UUID | None = None,
        invitee_email: str | None = None,
        message: str | None = None,
        expires_in_days: int = 7,
    ) -> RoomInvitation:
        """Create room invitation"""
        invitation = RoomInvitation(
            room_id=room_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            invitee_email=invitee_email,
            message=message,
            invitation_code=secrets.token_urlsafe(16),
            expires_at=datetime.now(UTC) + timedelta(days=expires_in_days),
        )

        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        return invitation

    async def accept_invitation(
        self, invitation_id: UUID, user_id: UUID
    ) -> RoomMember | None:
        """Accept room invitation"""
        query = select(RoomInvitation).where(RoomInvitation.id == invitation_id)
        result = await self.db.execute(query)
        invitation = result.scalar_one_or_none()

        if not invitation or invitation.is_accepted or invitation.is_declined:
            return None

        # Check expiration
        if invitation.expires_at and invitation.expires_at < datetime.now(UTC):
            return None

        invitation.is_accepted = True
        invitation.accepted_at = datetime.now(UTC)

        # Add member to room
        member = await self.add_member(
            room_id=invitation.room_id,
            user_id=user_id,
            invited_by=invitation.inviter_id,
        )

        await self.db.commit()

        return member

    # ============================================================
    # Task 109.3: Chat Messages
    # ============================================================

    async def send_message(
        self,
        room_id: UUID,
        user_id: UUID,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        file_id: UUID | None = None,
        reply_to_id: UUID | None = None,
        mentions: list[str] | None = None,
    ) -> RoomChatMessage:
        """Send chat message"""
        chat_message = RoomChatMessage(
            room_id=room_id,
            user_id=user_id,
            message=message,
            message_type=message_type,
            file_id=file_id,
            reply_to_id=reply_to_id,
            mentions=mentions or [],
        )

        self.db.add(chat_message)

        # Update room message count
        room = await self.get_room(room_id)
        if room:
            room.total_messages += 1

        # Update member message count
        query = select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()
        if member:
            member.messages_sent += 1

        await self.db.commit()
        await self.db.refresh(chat_message)

        return chat_message

    async def get_messages(
        self, room_id: UUID, limit: int = 50, before_id: UUID | None = None
    ) -> list[RoomChatMessage]:
        """Get chat messages"""
        query = select(RoomChatMessage).where(
            RoomChatMessage.room_id == room_id, RoomChatMessage.is_deleted == False
        )

        if before_id:
            query = query.where(RoomChatMessage.id < before_id)

        query = query.order_by(RoomChatMessage.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

    async def add_reaction(
        self, message_id: UUID, user_id: UUID, emoji: str
    ) -> RoomChatMessage | None:
        """Add emoji reaction to message"""
        query = select(RoomChatMessage).where(RoomChatMessage.id == message_id)
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return None

        # Initialize reactions if needed
        if not message.reactions:
            message.reactions = {}

        # Add reaction
        user_id_str = str(user_id)
        if emoji not in message.reactions:
            message.reactions[emoji] = []

        if user_id_str not in message.reactions[emoji]:
            message.reactions[emoji].append(user_id_str)

        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def delete_message(self, message_id: UUID, deleted_by: UUID) -> bool:
        """Delete message"""
        query = select(RoomChatMessage).where(RoomChatMessage.id == message_id)
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return False

        message.is_deleted = True
        message.deleted_at = datetime.now(UTC)
        message.deleted_by = deleted_by

        await self.db.commit()
        return True

    # ============================================================
    # Task 109.4: File Sharing
    # ============================================================

    async def upload_file(
        self,
        room_id: UUID,
        user_id: UUID,
        filename: str,
        file_path: str,
        file_type: FileType,
        file_size_bytes: int,
        mime_type: str,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> SharedFile:
        """Upload file to room"""
        # Generate safe filename
        original_filename = filename
        safe_filename = f"{secrets.token_hex(8)}_{filename}"

        file = SharedFile(
            room_id=room_id,
            uploaded_by=user_id,
            filename=safe_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            description=description,
            tags=tags or [],
        )

        self.db.add(file)

        # Update room file count
        room = await self.get_room(room_id)
        if room:
            room.total_files += 1

        # Update member file count
        query = select(RoomMember).where(
            RoomMember.room_id == room_id, RoomMember.user_id == user_id
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()
        if member:
            member.files_shared += 1

        await self.db.commit()
        await self.db.refresh(file)

        logger.info(f"File uploaded to room {room_id}: {file.id}")
        return file

    async def get_room_files(
        self, room_id: UUID, file_type: FileType | None = None, limit: int = 50
    ) -> list[SharedFile]:
        """Get files in room"""
        query = select(SharedFile).where(
            SharedFile.room_id == room_id, SharedFile.is_deleted == False
        )

        if file_type:
            query = query.where(SharedFile.file_type == file_type)

        query = query.order_by(SharedFile.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_file_version(
        self,
        file_id: UUID,
        user_id: UUID,
        file_path: str,
        file_size_bytes: int,
        change_description: str | None = None,
    ) -> FileVersion:
        """Create new version of file"""
        # Get original file
        query = select(SharedFile).where(SharedFile.id == file_id)
        result = await self.db.execute(query)
        file = result.scalar_one_or_none()

        if not file:
            raise ValueError("File not found")

        # Increment version number
        new_version_number = file.version_number + 1

        # Create version record
        version = FileVersion(
            file_id=file_id,
            version_number=new_version_number,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            uploaded_by=user_id,
            change_description=change_description,
        )

        self.db.add(version)

        # Update file
        file.version_number = new_version_number
        file.file_path = file_path
        file.file_size_bytes = file_size_bytes
        file.updated_at = datetime.now(UTC)

        await self.db.commit()
        await self.db.refresh(version)

        return version

    async def delete_file(self, file_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete file"""
        query = select(SharedFile).where(SharedFile.id == file_id)
        result = await self.db.execute(query)
        file = result.scalar_one_or_none()

        if not file:
            return False

        file.is_deleted = True
        file.deleted_at = datetime.now(UTC)
        file.deleted_by = deleted_by

        await self.db.commit()
        return True

    # ============================================================
    # Search & Discovery
    # ============================================================

    async def search_rooms(
        self,
        query_text: str | None = None,
        tags: list[str] | None = None,
        visibility: RoomVisibility | None = None,
        limit: int = 20,
    ) -> list[StudyRoom]:
        """Search for study rooms"""
        query = select(StudyRoom).where(StudyRoom.status == RoomStatus.ACTIVE)

        if visibility:
            query = query.where(StudyRoom.visibility == visibility)
        else:
            # Only show public rooms in search
            query = query.where(StudyRoom.visibility == RoomVisibility.PUBLIC)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(
                or_(
                    StudyRoom.name.ilike(search_pattern),
                    StudyRoom.description.ilike(search_pattern),
                    StudyRoom.topic.ilike(search_pattern),
                )
            )

        if tags:
            query = query.where(StudyRoom.tags.overlap(tags))

        query = query.order_by(StudyRoom.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_rooms(
        self, user_id: UUID, status: MemberStatus | None = MemberStatus.ACTIVE
    ) -> list[StudyRoom]:
        """Get rooms where user is a member"""
        query = select(StudyRoom).join(RoomMember).where(RoomMember.user_id == user_id)

        if status:
            query = query.where(RoomMember.status == status)

        query = query.where(StudyRoom.status == RoomStatus.ACTIVE)
        query = query.order_by(StudyRoom.updated_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Helper Methods
    # ============================================================

    def _hash_password(self, password: str) -> str:
        """Hash password for room"""
        return hashlib.sha256(password.encode()).hexdigest()

    async def check_member_permission(
        self, room_id: UUID, user_id: UUID, permission: str
    ) -> bool:
        """Check if member has specific permission"""
        query = select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
            RoomMember.status == MemberStatus.ACTIVE,
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            return False

        return getattr(member, permission, False)
