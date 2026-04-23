"""
Session Repository - Authentication & Token Management
PHASE 2.5: Replaces in-memory token storage (self.aktif_tokenlar)
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session as DBSession

from models.database import Session, User


class SessionRepository:
    """
    Repository for session/token management
    Replaces: self.aktif_tokenlar: Dict[str, Dict] = {} in user_service.py
    """

    def __init__(self, db: DBSession):
        self.db = db

    def create_session(
        self,
        user_id: str,
        token: str,
        expires_in_seconds: int = 86400,  # 24 hours default
        device_info: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Session:
        """
        Create new session
        Replaces: self.aktif_tokenlar[token] = {...}
        """
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in_seconds)

        session = Session(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            created_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session_by_token(self, token: str) -> Session | None:
        """
        Get session by token
        Replaces: self.aktif_tokenlar.get(token)
        """
        return (
            self.db.query(Session)
            .filter(
                and_(
                    Session.token == token,
                    Session.is_active == True,
                    Session.expires_at > datetime.now(UTC),
                )
            )
            .first()
        )

    def get_active_sessions_for_user(self, user_id: str) -> list[Session]:
        """Get all active sessions for a user"""
        return (
            self.db.query(Session)
            .filter(
                and_(
                    Session.user_id == user_id,
                    Session.is_active == True,
                    Session.expires_at > datetime.now(UTC),
                )
            )
            .order_by(Session.last_activity_at.desc())
            .all()
        )

    def update_activity(self, token: str) -> Session | None:
        """
        Update last activity timestamp
        For keeping session alive
        """
        session = self.get_session_by_token(token)
        if session:
            session.last_activity_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(session)

        return session

    def invalidate_session(self, token: str) -> bool:
        """
        Invalidate session (logout)
        Replaces: del self.aktif_tokenlar[token]
        """
        session = self.get_session_by_token(token)
        if session:
            session.is_active = False
            self.db.commit()
            return True

        return False

    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user
        Useful for password changes, security events
        """
        sessions = self.get_active_sessions_for_user(user_id)

        for session in sessions:
            session.is_active = False

        self.db.commit()

        return len(sessions)

    def cleanup_expired_sessions(self) -> int:
        """
        Delete expired sessions
        Should be called periodically (e.g., daily cron)
        """
        expired_sessions = (
            self.db.query(Session)
            .filter(Session.expires_at < datetime.now(UTC))
            .all()
        )

        count = len(expired_sessions)

        for session in expired_sessions:
            self.db.delete(session)

        self.db.commit()

        return count

    def get_user_from_token(self, token: str) -> User | None:
        """
        Get user from token (convenience method)
        Replaces complex token validation logic
        """
        session = self.get_session_by_token(token)
        if session:
            # Update activity
            self.update_activity(token)
            return session.user

        return None

    def extend_session(self, token: str, additional_seconds: int = 3600) -> Session | None:
        """
        Extend session expiration
        For "remember me" functionality
        """
        session = self.get_session_by_token(token)
        if session:
            session.expires_at = session.expires_at + timedelta(seconds=additional_seconds)
            self.db.commit()
            self.db.refresh(session)

        return session
