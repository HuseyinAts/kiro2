"""
Notification ORM Model - Dashboard Service
Part of Mock Data Cleanup Phase 2
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text

from .base import Base


class Notification(Base):
    """User notification model for dashboard"""

    __tablename__ = "notifications"
    __table_args__ = {"extend_existing": True}

    # Primary Key
    id = Column(String, primary_key=True, index=True)

    # Foreign Keys
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Notification Data
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(20), nullable=False)  # 'basari', 'uyari', 'bilgi', 'hata'

    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)

    # Optional Action
    action_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships (optional - if User model exists)
    # user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user={self.user_id}, type={self.notification_type}, read={self.is_read})>"

    @property
    def is_recent(self) -> bool:
        """Check if notification is from last 24 hours"""
        from datetime import timedelta
        if self.created_at is None:
            return False
        now = datetime.now(timezone.utc)
        return bool((now - self.created_at) < timedelta(hours=24))

    def mark_as_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True  # type: ignore[assignment]

    def mark_as_unread(self) -> None:
        """Mark notification as unread"""
        self.is_read = False  # type: ignore[assignment]
