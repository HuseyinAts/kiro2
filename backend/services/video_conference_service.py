"""
Task 108: Video Conference Service

Service for managing video conferences with Zoom and Google Meet integration.
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.live_session import (
    LiveSession,
    ParticipantRole,
    PlatformType,
    RecordingStatus,
    ScreenShare,
    ScreenShareType,
    SessionAnalytics,
    SessionChatMessage,
    SessionParticipant,
    SessionRecording,
    SessionStatus,
    SessionType,
)

logger = logging.getLogger(__name__)


class VideoConferenceService:
    """
    Service for video conference management

    Task 108.1: Video conference integration (Zoom/Meet)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 108.1: Session Management
    # ============================================================

    async def create_session(
        self,
        host_id: UUID,
        title: str,
        description: str,
        scheduled_start: datetime,
        scheduled_end: datetime,
        session_type: SessionType,
        platform: PlatformType = PlatformType.ZOOM,
        subject: str | None = None,
        topics: list[str] | None = None,
        max_participants: int = 50,
        auto_record: bool = False,
        require_password: bool = True,
        teacher_id: UUID | None = None,
    ) -> LiveSession:
        """
        Create a new live session

        Creates session and integrates with video conference platform.
        """
        duration_minutes = int((scheduled_end - scheduled_start).total_seconds() / 60)

        session = LiveSession(
            # GF36 fix: coerce UUID -> str because LiveSession.id is VARCHAR and
            # asyncpg refuses UUID objects as VARCHAR params (same trap as GF26).
            id=str(uuid4()),
            title=title,
            description=description,
            host_id=str(host_id) if host_id is not None else None,
            teacher_id=str(teacher_id) if teacher_id is not None else None,
            session_type=session_type,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=duration_minutes,
            platform=platform,
            subject=subject,
            topics=topics or [],
            max_participants=max_participants,
            auto_record=auto_record,
            require_password=require_password,
        )

        # Generate meeting credentials based on platform
        if platform == PlatformType.ZOOM:
            meeting_data = await self._create_zoom_meeting(session)
            session.zoom_meeting_data = meeting_data
            session.meeting_id = meeting_data.get("id")
            session.meeting_url = meeting_data.get("join_url")
            session.join_url = meeting_data.get("join_url")
            session.host_url = meeting_data.get("start_url")
            session.meeting_password = meeting_data.get("password")

        elif platform == PlatformType.GOOGLE_MEET:
            meeting_data = await self._create_google_meet(session)
            session.meet_event_data = meeting_data
            session.meeting_url = meeting_data.get("hangoutLink")
            session.join_url = meeting_data.get("hangoutLink")
            session.meeting_id = meeting_data.get("id")

        elif platform == PlatformType.JITSI:
            # Jitsi uses room names
            room_name = self._generate_jitsi_room_name(session)
            session.meeting_id = room_name
            session.meeting_url = f"https://meet.jit.si/{room_name}"
            session.join_url = session.meeting_url

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Live session created: {session.id} on {platform}")
        return session

    async def start_session(self, session_id: UUID) -> LiveSession | None:
        """Start a scheduled session"""
        session = await self.get_session(session_id)
        if not session:
            return None

        session.status = SessionStatus.LIVE
        session.actual_start = datetime.now(UTC)

        # Start recording if auto-record is enabled
        if session.auto_record and session.allow_recording:
            await self.start_recording(session_id)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session started: {session_id}")
        return session

    async def end_session(self, session_id: UUID) -> LiveSession | None:
        """End a live session"""
        session = await self.get_session(session_id)
        if not session:
            return None

        session.status = SessionStatus.ENDED
        session.actual_end = datetime.now(UTC)

        if session.actual_start:
            duration = session.actual_end - session.actual_start
            session.duration_minutes = int(duration.total_seconds() / 60)

        # End all active recordings
        await self._end_active_recordings(session_id)

        # Update participant durations
        await self._update_participant_durations(session_id)

        # Generate analytics
        await self._generate_session_analytics(session_id)

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session ended: {session_id}")
        return session

    async def get_session(self, session_id: UUID) -> LiveSession | None:
        """Get session by ID"""
        query = select(LiveSession).where(LiveSession.id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self,
        user_id: UUID,
        status: SessionStatus | None = None,
        upcoming_only: bool = False,
    ) -> list[LiveSession]:
        """Get sessions for a user (as host or participant)"""
        # Get sessions where user is host
        host_query = select(LiveSession).where(LiveSession.host_id == user_id)

        # Get sessions where user is participant
        participant_query = (
            select(LiveSession)
            .join(SessionParticipant)
            .where(SessionParticipant.user_id == user_id)
        )

        # Combine queries
        query = host_query.union(participant_query)

        if status:
            query = query.where(LiveSession.status == status)

        if upcoming_only:
            query = query.where(
                LiveSession.scheduled_start > datetime.now(UTC),
                LiveSession.status == SessionStatus.SCHEDULED,
            )

        query = query.order_by(LiveSession.scheduled_start.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Task 108.1: Platform Integration (Placeholders)
    # ============================================================

    async def _create_zoom_meeting(self, session: LiveSession) -> dict[str, Any]:
        """
        Create Zoom meeting

        PLACEHOLDER: Integrate with Zoom API in production
        https://marketplace.zoom.us/docs/api-reference/zoom-api/methods/#operation/meetingCreate
        """
        # Production implementation would use Zoom SDK/API:
        # from zoom import ZoomClient
        # client = ZoomClient(api_key, api_secret)
        # meeting = client.meeting.create(...)

        # Mock response for development
        meeting_id = f"zoom_{secrets.token_hex(8)}"
        password = secrets.token_urlsafe(8)

        return {
            "id": meeting_id,
            "join_url": f"https://zoom.us/j/{meeting_id}?pwd={password}",
            "start_url": f"https://zoom.us/s/{meeting_id}?zak=...",
            "password": password,
            "host_email": "host@example.com",
            "topic": session.title,
            "duration": session.duration_minutes,
            "start_time": session.scheduled_start.isoformat(),
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": False,
                "mute_upon_entry": session.enable_mute_on_join,
                "waiting_room": session.enable_waiting_room,
                "auto_recording": "cloud" if session.auto_record else "none",
            },
        }

    async def _create_google_meet(self, session: LiveSession) -> dict[str, Any]:
        """
        Create Google Meet session

        PLACEHOLDER: Integrate with Google Calendar/Meet API in production
        https://developers.google.com/calendar/api/guides/create-events
        """
        # Production implementation would use Google Calendar API:
        # from googleapiclient.discovery import build
        # service = build('calendar', 'v3', credentials=creds)
        # event = service.events().insert(calendarId='primary', conferenceDataVersion=1, body=event_data).execute()

        # Mock response for development
        event_id = f"meet_{secrets.token_hex(8)}"

        return {
            "id": event_id,
            "htmlLink": f"https://calendar.google.com/event?eid={event_id}",
            "hangoutLink": f"https://meet.google.com/{secrets.token_urlsafe(10)}",
            "summary": session.title,
            "description": session.description,
            "start": {
                "dateTime": session.scheduled_start.isoformat(),
                "timeZone": "UTC",
            },
            "end": {"dateTime": session.scheduled_end.isoformat(), "timeZone": "UTC"},
            "conferenceData": {"conferenceSolution": {"name": "Google Meet"}},
        }

    def _generate_jitsi_room_name(self, session: LiveSession) -> str:
        """Generate unique Jitsi room name"""
        # Create a unique, readable room name
        hash_input = f"{session.id}{session.title}{datetime.now(UTC)}"
        hash_short = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        safe_title = "".join(c for c in session.title if c.isalnum())[:20]
        return f"kiro_{safe_title}_{hash_short}"

    # ============================================================
    # Participant Management
    # ============================================================

    async def add_participant(
        self,
        session_id: UUID,
        user_id: UUID,
        role: ParticipantRole = ParticipantRole.PARTICIPANT,
    ) -> SessionParticipant:
        """Add participant to session"""
        participant = SessionParticipant(
            session_id=session_id, user_id=user_id, role=role
        )

        self.db.add(participant)
        await self.db.commit()
        await self.db.refresh(participant)

        return participant

    async def join_session(
        self, session_id: UUID, user_id: UUID
    ) -> SessionParticipant | None:
        """Mark participant as joined"""
        query = select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == user_id,
        )
        result = await self.db.execute(query)
        participant = result.scalar_one_or_none()

        if not participant:
            participant = await self.add_participant(session_id, user_id)

        participant.is_present = True
        participant.joined_at = datetime.now(UTC)

        # Update session participant count
        session = await self.get_session(session_id)
        if session:
            session.current_participants += 1

        await self.db.commit()
        await self.db.refresh(participant)

        return participant

    async def leave_session(
        self, session_id: UUID, user_id: UUID
    ) -> SessionParticipant | None:
        """Mark participant as left"""
        query = select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == user_id,
        )
        result = await self.db.execute(query)
        participant = result.scalar_one_or_none()

        if not participant:
            return None

        participant.is_present = False
        participant.left_at = datetime.now(UTC)

        if participant.joined_at:
            duration = participant.left_at - participant.joined_at
            participant.duration_minutes = int(duration.total_seconds() / 60)

        # Update session participant count
        session = await self.get_session(session_id)
        if session and session.current_participants > 0:
            session.current_participants -= 1

        await self.db.commit()
        await self.db.refresh(participant)

        return participant

    # ============================================================
    # Task 108.2: Screen Sharing
    # ============================================================

    async def start_screen_share(
        self,
        session_id: UUID,
        user_id: UUID,
        share_type: ScreenShareType,
        window_title: str | None = None,
        application_name: str | None = None,
    ) -> ScreenShare:
        """Track screen share start"""
        screen_share = ScreenShare(
            session_id=session_id,
            user_id=user_id,
            share_type=share_type,
            window_title=window_title,
            application_name=application_name,
            started_at=datetime.now(UTC),
        )

        self.db.add(screen_share)

        # Update participant status
        query = select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == user_id,
        )
        result = await self.db.execute(query)
        participant = result.scalar_one_or_none()
        if participant:
            participant.is_sharing_screen = True

        await self.db.commit()
        await self.db.refresh(screen_share)

        logger.info(f"Screen share started: {screen_share.id}")
        return screen_share

    async def end_screen_share(self, screen_share_id: UUID) -> ScreenShare | None:
        """Track screen share end"""
        query = select(ScreenShare).where(ScreenShare.id == screen_share_id)
        result = await self.db.execute(query)
        screen_share = result.scalar_one_or_none()

        if not screen_share:
            return None

        screen_share.ended_at = datetime.now(UTC)
        duration = screen_share.ended_at - screen_share.started_at
        screen_share.duration_seconds = int(duration.total_seconds())

        # Update participant status
        query = select(SessionParticipant).where(
            SessionParticipant.session_id == screen_share.session_id,
            SessionParticipant.user_id == screen_share.user_id,
        )
        result = await self.db.execute(query)
        participant = result.scalar_one_or_none()
        if participant:
            participant.is_sharing_screen = False

        await self.db.commit()
        await self.db.refresh(screen_share)

        return screen_share

    # ============================================================
    # Task 108.4: Recording Management
    # ============================================================

    async def start_recording(
        self, session_id: UUID, title: str | None = None
    ) -> SessionRecording:
        """Start session recording"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        recording = SessionRecording(
            session_id=session_id,
            title=title or f"Recording: {session.title}",
            description=session.description,
            started_at=datetime.now(UTC),
            status=RecordingStatus.RECORDING,
        )

        self.db.add(recording)
        session.is_recorded = True

        await self.db.commit()
        await self.db.refresh(recording)

        logger.info(f"Recording started: {recording.id}")
        return recording

    async def stop_recording(self, recording_id: UUID) -> SessionRecording | None:
        """Stop recording"""
        query = select(SessionRecording).where(SessionRecording.id == recording_id)
        result = await self.db.execute(query)
        recording = result.scalar_one_or_none()

        if not recording:
            return None

        recording.ended_at = datetime.now(UTC)
        recording.status = RecordingStatus.PROCESSING

        if recording.started_at:
            duration = recording.ended_at - recording.started_at
            recording.duration_seconds = int(duration.total_seconds())

        await self.db.commit()
        await self.db.refresh(recording)

        # Trigger async processing (placeholder)
        await self._process_recording(recording_id)

        logger.info(f"Recording stopped: {recording_id}")
        return recording

    async def _process_recording(self, recording_id: UUID):
        """
        Process recording (convert, upload to CDN, generate thumbnail)

        PLACEHOLDER: Implement actual video processing in production
        """
        # Production implementation would:
        # 1. Convert video to web-friendly format (H.264/MP4)
        # 2. Generate multiple resolutions
        # 3. Upload to CDN/cloud storage (S3, CloudFlare)
        # 4. Generate thumbnail
        # 5. Extract audio for transcription
        # 6. Update recording with URLs

        query = select(SessionRecording).where(SessionRecording.id == recording_id)
        result = await self.db.execute(query)
        recording = result.scalar_one_or_none()

        if recording:
            recording.status = RecordingStatus.READY
            recording.processing_completed_at = datetime.now(UTC)
            recording.file_url = (
                f"https://cdn.example.com/recordings/{recording_id}.mp4"
            )
            recording.thumbnail_url = (
                f"https://cdn.example.com/thumbnails/{recording_id}.jpg"
            )
            await self.db.commit()

    async def get_session_recordings(self, session_id: UUID) -> list[SessionRecording]:
        """Get all recordings for a session"""
        query = (
            select(SessionRecording)
            .where(
                SessionRecording.session_id == session_id,
                SessionRecording.status == RecordingStatus.READY,
            )
            .order_by(SessionRecording.created_at)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Chat Management
    # ============================================================

    async def send_chat_message(
        self,
        session_id: UUID,
        user_id: UUID,
        message: str,
        recipient_id: UUID | None = None,
    ) -> SessionChatMessage:
        """Send chat message in session"""
        chat_message = SessionChatMessage(
            session_id=session_id,
            user_id=user_id,
            message=message,
            recipient_id=recipient_id,
            is_private=recipient_id is not None,
        )

        self.db.add(chat_message)
        await self.db.commit()
        await self.db.refresh(chat_message)

        return chat_message

    async def get_session_chat(
        self,
        session_id: UUID,
        limit: int = 100,
        *,
        viewer_user_id: str,
        viewer_is_session_host: bool = False,
    ) -> list[SessionChatMessage]:
        """Get chat messages visible to viewer (public + own DMs; host sees all)."""
        filters = [
            SessionChatMessage.session_id == session_id,
            SessionChatMessage.is_deleted == False,
        ]
        if not viewer_is_session_host:
            vid = str(viewer_user_id)
            filters.append(
                or_(
                    SessionChatMessage.is_private == False,
                    cast(SessionChatMessage.user_id, String) == vid,
                    cast(SessionChatMessage.recipient_id, String) == vid,
                )
            )
        query = (
            select(SessionChatMessage)
            .where(and_(*filters))
            .order_by(SessionChatMessage.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Helper Methods
    # ============================================================

    async def _end_active_recordings(self, session_id: UUID):
        """End all active recordings for session"""
        query = select(SessionRecording).where(
            SessionRecording.session_id == session_id,
            SessionRecording.status == RecordingStatus.RECORDING,
        )
        result = await self.db.execute(query)
        recordings = result.scalars().all()

        for recording in recordings:
            await self.stop_recording(recording.id)

    async def _update_participant_durations(self, session_id: UUID):
        """Update duration for all participants"""
        query = select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.is_present == True,
        )
        result = await self.db.execute(query)
        participants = result.scalars().all()

        for participant in participants:
            if participant.joined_at:
                duration = datetime.now(UTC) - participant.joined_at
                participant.duration_minutes = int(duration.total_seconds() / 60)
                participant.is_present = False
                participant.left_at = datetime.now(UTC)

        await self.db.commit()

    async def _generate_session_analytics(self, session_id: UUID):
        """Generate analytics for completed session"""
        # Count participants
        participant_query = select(func.count(SessionParticipant.id)).where(
            SessionParticipant.session_id == session_id
        )
        result = await self.db.execute(participant_query)
        total_participants = result.scalar() or 0

        # Create analytics
        analytics = SessionAnalytics(
            session_id=session_id, total_participants=total_participants
        )

        self.db.add(analytics)
        await self.db.commit()
