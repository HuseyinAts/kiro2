"""
Gamification SQLAlchemy Modelleri

FAZ-2 Gorev 2.1 — Master Plan v2.0
Tablolar: bkt_states, realms, realm_progress, streaks, xp_transactions,
          obalar, oba_uyeler, badges, user_badges, duels, parent_child

KRITIK: BKTState SADECE BURADA tanimlanir.
        FAZ-1'deki migration'dan CIKAR, buraya tasimak gerekirse tasindi.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

# ---------------------------------------------------------------------------
# BKT State
# ---------------------------------------------------------------------------


class BKTState(Base):
    """Bayesian Knowledge Tracing durumu — ogrenci x konu."""

    __tablename__ = "bkt_states"

    student_id = Column(String, ForeignKey("users.id"), primary_key=True)
    topic_id = Column(
        String, primary_key=True
    )  # FK kaldırıldı (primary_topic_id String)
    p_learn = Column(Float(precision=5, asdecimal=False), default=0.05)
    p_transit = Column(Float(precision=5, asdecimal=False), default=0.10)
    p_guess = Column(Float(precision=5, asdecimal=False), default=0.20)
    p_slip = Column(Float(precision=5, asdecimal=False), default=0.10)
    attempt_count = Column(Integer, default=0)
    mastery_status = Column(
        String(20), default="learning"
    )  # learning|mastered|frustrated
    last_attempt = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Realms (Alemler)
# ---------------------------------------------------------------------------


class Realm(Base):
    """YKS konularini temsil eden oyunlastirilmis alemler."""

    __tablename__ = "realms"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    era = Column(String(150))
    npc_name = Column(String(100))
    npc_title = Column(String(100))
    tech_stack = Column(JSON)  # ["threejs", "venn"] gibi
    color_primary = Column(String(7))
    color_secondary = Column(String(7))
    order_index = Column(Integer)
    is_active = Column(Boolean, default=True)

    progress_records = relationship("RealmProgress", back_populates="realm")


class RealmProgress(Base):
    """Ogrenci x Alem ilerleme durumu."""

    __tablename__ = "realm_progress"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    realm_id = Column(Integer, ForeignKey("realms.id"), nullable=False)
    bkt_score = Column(Float(precision=5, asdecimal=False), default=0.0)
    quest_stop = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())

    realm = relationship("Realm", back_populates="progress_records")

    __table_args__ = (UniqueConstraint("student_id", "realm_id"),)


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------


class Streak(Base):
    """Kullanici gunluk giris serisi."""

    __tablename__ = "streaks"

    user_id = Column(String, ForeignKey("users.id"), unique=True, primary_key=True)
    current_streak = Column(Integer, default=0)
    largest_streak = Column(Integer, default=0)
    freeze_count = Column(Integer, default=2)
    last_activity = Column(Date, nullable=True)
    total_days_active = Column(Integer, default=0)


# ---------------------------------------------------------------------------
# XP Transactions
# ---------------------------------------------------------------------------


class XPTransaction(Base):
    """XP kaynak takip tablosu."""

    __tablename__ = "xp_transactions"

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    # kaynak: 'soru'|'3d'|'alim'|'duel'|'streak'|'realm'
    source = Column(String(20), nullable=False)
    topic_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Oba (Kulup / Guild)
# ---------------------------------------------------------------------------


class Oba(Base):
    """Ogrenci toplulugu / kulup."""

    __tablename__ = "obalar"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    xp_pool = Column(Integer, default=0)
    max_members = Column(Integer, default=20)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    members = relationship("ObaUye", back_populates="oba")


class ObaUye(Base):
    """Oba uyelik iliskisi."""

    __tablename__ = "oba_uyeler"

    id = Column(Integer, primary_key=True)
    oba_id = Column(Integer, ForeignKey("obalar.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String(10), default="toycu")  # toycu|noker|bey
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    oba = relationship("Oba", back_populates="members")

    __table_args__ = (UniqueConstraint("user_id"),)


# ---------------------------------------------------------------------------
# Badges (Rozetler)
# ---------------------------------------------------------------------------


class Badge(Base):
    """Kazanilabilir rozet tanimi."""

    __tablename__ = "badges"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String(10))  # emoji
    # kategori: katilim|beceri|basari|sosyal
    category = Column(String(20))
    condition = Column(JSON)  # {"type": "streak", "value": 7}


class UserBadge(Base):
    """Kullanicinin kazandigi rozetler."""

    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    auto_awarded = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="badges")

    __table_args__ = (
        UniqueConstraint("user_id", "badge_id"),
        {"extend_existing": True},
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "badge_id": self.badge_id,
            "earned_at": self.earned_at.isoformat() if self.earned_at else None,
            "auto_awarded": self.auto_awarded,
        }


# ---------------------------------------------------------------------------
# Duel (Duello)
# ---------------------------------------------------------------------------


class Duel(Base):
    """Ogrenciler arasi duello kaydi."""

    __tablename__ = "duels"

    id = Column(Integer, primary_key=True)
    player1_id = Column(String, ForeignKey("users.id"), nullable=False)
    player2_id = Column(String, ForeignKey("users.id"), nullable=False)
    topic_id = Column(String, ForeignKey("topic_hierarchy.id"), nullable=False)
    # durum: pending|active|completed
    status = Column(String(20), default="pending")
    winner_id = Column(Integer, nullable=True)
    player1_score = Column(Integer, default=0)
    player2_score = Column(Integer, default=0)
    elo_delta = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# ParentChild (Veli-Ogrenci)
# ---------------------------------------------------------------------------


class ParentChild(Base):
    """Veli-ogrenci iliskisi."""

    __tablename__ = "parent_child"

    id = Column(Integer, primary_key=True)
    parent_id = Column(String, ForeignKey("users.id"), nullable=False)
    child_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("parent_id", "child_id"),)


# ---------------------------------------------------------------------------
# StudentAbility (IRT kalibrasyonu)
# ---------------------------------------------------------------------------


class DailyQuest(Base):
    """Gunluk gorev tanimlari (sistem tarafindan uretilir)."""

    __tablename__ = "daily_quests"

    id = Column(Integer, primary_key=True)
    quest_date = Column(Date, nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    quest_type = Column(
        String(30), nullable=False
    )  # cat_session|fsrs_review|duel|streak_check|realm_quest
    title = Column(String(200), nullable=False)
    description = Column(String, nullable=True)
    target_value = Column(Integer, default=1)  # kac kez yapmali
    current_value = Column(Integer, default=0)  # kac kez yapildi
    xp_reward = Column(Integer, default=10)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    bonus_claimed = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("quest_date", "student_id", "quest_type"),)


class StudentAbility(Base):
    """IRT theta tahmini per konu."""

    __tablename__ = "student_abilities"

    student_id = Column(String, ForeignKey("users.id"), primary_key=True)
    subject_id = Column(Integer, primary_key=True)
    theta = Column(Float(precision=6, asdecimal=False), default=0.0)
    theta_se = Column(Float(precision=6, asdecimal=False), default=1.0)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
