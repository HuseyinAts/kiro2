"""
Task 107: Teacher Pool Models

Database models for teacher registration, expertise, availability, and appointments.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    Date,
    Time,
    ForeignKey,
    Enum as SQLEnum,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from enum import Enum

from .database import Base


# ============================================================
# Enumerations
# ============================================================


class TeacherStatus(str, Enum):
    """Teacher account status"""

    PENDING = "pending"  # Awaiting verification
    VERIFIED = "verified"  # Verified and active
    SUSPENDED = "suspended"  # Temporarily suspended
    REJECTED = "rejected"  # Application rejected


class VerificationStatus(str, Enum):
    """Document verification status"""

    NOT_SUBMITTED = "not_submitted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SubjectExpertise(str, Enum):
    """Subject areas for teaching"""

    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    TURKISH = "turkish"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    ENGLISH = "english"
    PHILOSOPHY = "philosophy"
    LITERATURE = "literature"
    GEOMETRY = "geometry"


class GradeLevel(str, Enum):
    """Grade levels for teaching"""

    GRADE_9 = "grade_9"
    GRADE_10 = "grade_10"
    GRADE_11 = "grade_11"
    GRADE_12 = "grade_12"
    UNIVERSITY_PREP = "university_prep"
    ALL_GRADES = "all_grades"


class CertificationType(str, Enum):
    """Types of teaching certifications"""

    TEACHING_LICENSE = "teaching_license"  # MEB teaching license
    UNIVERSITY_DEGREE = "university_degree"
    MASTERS_DEGREE = "masters_degree"
    PHD_DEGREE = "phd_degree"
    TRAINING_CERTIFICATE = "training_certificate"
    EXPERIENCE_CERTIFICATE = "experience_certificate"


class DayOfWeek(str, Enum):
    """Days of the week"""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TimeSlotStatus(str, Enum):
    """Availability time slot status"""

    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"  # Teacher blocked this slot


class AppointmentStatus(str, Enum):
    """Appointment booking status"""

    PENDING = "pending"  # Awaiting teacher confirmation
    CONFIRMED = "confirmed"  # Teacher confirmed
    CANCELLED = "cancelled"  # Cancelled by student or teacher
    COMPLETED = "completed"  # Session completed
    NO_SHOW = "no_show"  # Student didn't show up


class AppointmentType(str, Enum):
    """Types of appointments"""

    ONE_ON_ONE = "one_on_one"  # Private tutoring
    GROUP_SESSION = "group_session"  # Small group
    QUESTION_ANSWER = "question_answer"  # Q&A session
    EXAM_PREP = "exam_prep"  # Exam preparation


# ============================================================
# Teacher Profile
# ============================================================


class TeacherPoolProfile(Base):
    """
    Teacher pool profile and registration information (renamed to avoid conflict with models.database.TeacherProfile)

    Covers Task 107.1: Teacher registration and profile
    """

    __tablename__ = "teacher_pool_profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=uuid4)
    user_id = Column(
        String, ForeignKey("users.id"), nullable=False, unique=True
    )

    # Basic Information
    full_name = Column(String(255), nullable=False)
    title = Column(String(100))  # e.g., "Matematik Öğretmeni", "Dr."
    bio = Column(Text)  # Teacher biography
    profile_photo_url = Column(String(500))

    # Contact
    phone = Column(String(20))
    email = Column(String(255))
    city = Column(String(100))
    district = Column(String(100))

    # Professional Information
    years_of_experience = Column(Integer, default=0)
    education_level = Column(String(100))  # e.g., "Lisans", "Yüksek Lisans", "Doktora"
    university = Column(String(255))
    department = Column(String(255))
    graduation_year = Column(Integer)

    # Status
    status = Column(
        SQLEnum(TeacherStatus), default=TeacherStatus.PENDING, nullable=False
    )
    verification_status = Column(
        SQLEnum(VerificationStatus), default=VerificationStatus.NOT_SUBMITTED
    )
    verified_at = Column(DateTime(timezone=True))
    verified_by = Column(
        String, ForeignKey("users.id")
    )  # Admin who verified

    # Ratings & Statistics
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    total_students = Column(Integer, default=0)

    # Pricing
    hourly_rate = Column(Float)  # Price per hour
    currency = Column(String(10), default="TRY")

    # Settings
    is_accepting_students = Column(Boolean, default=True)
    max_students = Column(Integer, default=50)  # Maximum concurrent students
    online_teaching = Column(Boolean, default=True)
    in_person_teaching = Column(Boolean, default=False)

    # Metadata
    application_notes = Column(Text)  # Notes from teacher's application
    admin_notes = Column(Text)  # Internal admin notes
    rejection_reason = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    expertise = relationship(
        "TeacherExpertise", back_populates="teacher", cascade="all, delete-orphan"
    )
    certifications = relationship(
        "TeacherCertification", back_populates="teacher", cascade="all, delete-orphan"
    )
    availability = relationship(
        "TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan"
    )
    appointments = relationship(
        "Appointment", back_populates="teacher", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "TeacherReview", back_populates="teacher", cascade="all, delete-orphan"
    )


# ============================================================
# Teacher Expertise
# ============================================================


class TeacherExpertise(Base):
    """
    Teacher subject expertise and grade level specialization

    Covers Task 107.2: Subject expertise and grade level specialization
    """

    __tablename__ = "teacher_expertise"

    id = Column(String, primary_key=True, default=uuid4)
    teacher_id = Column(
        String, ForeignKey("teacher_pool_profiles.id"), nullable=False
    )

    # Expertise Details
    subject = Column(SQLEnum(SubjectExpertise), nullable=False)
    grade_levels = Column(ARRAY(String), default=list)  # Array of grade levels

    # Proficiency
    proficiency_level = Column(String(50))  # e.g., "Uzman", "İleri", "Orta"
    years_teaching_subject = Column(Integer, default=0)

    # Specializations within subject
    specializations = Column(
        JSONB, default=list
    )  # e.g., ["Geometri", "Analitik Geometri"]

    # Exam expertise
    exam_types = Column(JSONB, default=list)  # e.g., ["TYT", "AYT", "YKS"]

    # Verification
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    teacher = relationship("TeacherPoolProfile", back_populates="expertise")


# ============================================================
# Teacher Certifications
# ============================================================


class TeacherCertification(Base):
    """
    Teacher certifications and credentials

    Covers Task 107.2: Certification display
    """

    __tablename__ = "teacher_certifications"

    id = Column(String, primary_key=True, default=uuid4)
    teacher_id = Column(
        String, ForeignKey("teacher_pool_profiles.id"), nullable=False
    )

    # Certification Details
    certification_type = Column(SQLEnum(CertificationType), nullable=False)
    title = Column(
        String(255), nullable=False
    )  # e.g., "Matematik Öğretmenliği Belgesi"
    issuing_organization = Column(String(255))  # e.g., "MEB", university name
    issue_date = Column(Date)
    expiry_date = Column(Date)  # If applicable
    credential_id = Column(String(100))  # Certificate number

    # Documentation
    document_url = Column(String(500))  # Uploaded certificate image/PDF
    description = Column(Text)

    # Verification
    verification_status = Column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    verified_at = Column(DateTime(timezone=True))
    verified_by = Column(String, ForeignKey("users.id"))
    rejection_reason = Column(Text)

    # Display
    is_featured = Column(Boolean, default=False)  # Show prominently on profile
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    teacher = relationship("TeacherPoolProfile", back_populates="certifications")


# ============================================================
# Teacher Availability
# ============================================================


class TeacherAvailability(Base):
    """
    Teacher availability calendar and time slots

    Covers Task 107.3: Availability calendar and time slot management
    """

    __tablename__ = "teacher_availability"

    id = Column(String, primary_key=True, default=uuid4)
    teacher_id = Column(
        String, ForeignKey("teacher_pool_profiles.id"), nullable=False
    )

    # Time Slot
    day_of_week = Column(SQLEnum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Date Range (for specific date overrides)
    specific_date = Column(Date)  # If set, overrides day_of_week
    valid_from = Column(Date)  # Recurring availability start date
    valid_until = Column(Date)  # Recurring availability end date

    # Status
    status = Column(SQLEnum(TimeSlotStatus), default=TimeSlotStatus.AVAILABLE)

    # Capacity
    max_students = Column(Integer, default=1)  # For group sessions
    current_bookings = Column(Integer, default=0)

    # Metadata
    notes = Column(Text)  # Teacher's notes about this slot
    is_recurring = Column(Boolean, default=True)  # Recurring weekly slot

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    teacher = relationship("TeacherPoolProfile", back_populates="availability")


# ============================================================
# Appointments
# ============================================================


class Appointment(Base):
    """
    Student appointments with teachers

    Covers Task 107.4: Appointment scheduling and management
    """

    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=uuid4)
    teacher_id = Column(
        String, ForeignKey("teacher_pool_profiles.id"), nullable=False
    )
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    availability_slot_id = Column(
        String, ForeignKey("teacher_availability.id")
    )

    # Appointment Details
    appointment_type = Column(
        SQLEnum(AppointmentType), default=AppointmentType.ONE_ON_ONE
    )
    subject = Column(SQLEnum(SubjectExpertise))

    # Schedule
    scheduled_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=60)

    # Status
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING)

    # Student Information
    topic = Column(String(255))  # What student wants to learn
    description = Column(Text)  # Detailed description
    student_notes = Column(Text)  # Student's notes

    # Teacher Information
    teacher_notes = Column(Text)  # Teacher's private notes
    preparation_materials = Column(JSONB, default=list)  # Links to materials

    # Confirmation
    confirmed_at = Column(DateTime(timezone=True))
    confirmed_by = Column(String, ForeignKey("users.id"))

    # Cancellation
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(String, ForeignKey("users.id"))
    cancellation_reason = Column(Text)

    # Completion
    completed_at = Column(DateTime(timezone=True))
    session_summary = Column(Text)  # Teacher's session summary
    homework_assigned = Column(Text)

    # Meeting Details
    meeting_url = Column(String(500))  # Video conference link
    meeting_id = Column(String(100))
    meeting_password = Column(String(100))

    # Reminders
    reminder_sent_at = Column(DateTime(timezone=True))
    reminder_count = Column(Integer, default=0)

    # Pricing
    price = Column(Float)
    currency = Column(String(10), default="TRY")
    payment_status = Column(String(50))  # e.g., "paid", "pending", "refunded"

    # Metadata
    meta_data = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    teacher = relationship("TeacherPoolProfile", back_populates="appointments")
    reminders = relationship(
        "AppointmentReminder",
        back_populates="appointment",
        cascade="all, delete-orphan",
    )


# ============================================================
# Appointment Reminders
# ============================================================


class AppointmentReminder(Base):
    """
    Appointment reminder notifications

    Covers Task 107.4: Reminder notifications
    """

    __tablename__ = "appointment_reminders"

    id = Column(String, primary_key=True, default=uuid4)
    appointment_id = Column(
        String, ForeignKey("appointments.id"), nullable=False
    )

    # Reminder Details
    remind_at = Column(DateTime(timezone=True), nullable=False)
    reminder_type = Column(String(50))  # e.g., "email", "sms", "push"

    # Status
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))

    # Recipient
    recipient_type = Column(String(50))  # "student" or "teacher"
    recipient_id = Column(String, ForeignKey("users.id"))

    # Message
    message_template = Column(String(100))  # Template identifier
    message_sent = Column(Text)  # Actual message sent

    # Delivery
    delivery_status = Column(String(50))  # "sent", "delivered", "failed"
    error_message = Column(Text)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    appointment = relationship("Appointment", back_populates="reminders")


# ============================================================
# Teacher Reviews
# ============================================================


class TeacherReview(Base):
    """
    Student reviews and ratings for teachers
    """

    __tablename__ = "teacher_reviews"

    id = Column(String, primary_key=True, default=uuid4)
    teacher_id = Column(
        String, ForeignKey("teacher_pool_profiles.id"), nullable=False
    )
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    appointment_id = Column(String, ForeignKey("appointments.id"))

    # Rating (1-5 stars)
    overall_rating = Column(Integer, nullable=False)
    teaching_quality = Column(Integer)  # 1-5
    communication = Column(Integer)  # 1-5
    punctuality = Column(Integer)  # 1-5
    helpfulness = Column(Integer)  # 1-5

    # Review Text
    title = Column(String(255))
    content = Column(Text)

    # Response
    teacher_response = Column(Text)
    responded_at = Column(DateTime(timezone=True))

    # Moderation
    is_verified = Column(Boolean, default=True)  # Verified purchase/session
    is_featured = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)  # Hidden by admin

    # Helpfulness
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    teacher = relationship("TeacherPoolProfile", back_populates="reviews")


# ============================================================
# Teacher Statistics
# ============================================================


class TeacherStatistics(Base):
    """
    Aggregated statistics for teacher performance
    """

    __tablename__ = "teacher_statistics"

    id = Column(String, primary_key=True, default=uuid4)
    teacher_id = Column(
        String,
        ForeignKey("teacher_pool_profiles.id"),
        nullable=False,
        unique=True,
    )

    # Session Statistics
    total_sessions = Column(Integer, default=0)
    completed_sessions = Column(Integer, default=0)
    cancelled_sessions = Column(Integer, default=0)
    no_show_sessions = Column(Integer, default=0)

    # Student Statistics
    total_students = Column(Integer, default=0)
    active_students = Column(Integer, default=0)

    # Rating Statistics
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    five_star_count = Column(Integer, default=0)
    four_star_count = Column(Integer, default=0)
    three_star_count = Column(Integer, default=0)
    two_star_count = Column(Integer, default=0)
    one_star_count = Column(Integer, default=0)

    # Response Statistics
    average_response_time_minutes = Column(Integer, default=0)

    # Financial Statistics
    total_earnings = Column(Float, default=0.0)
    this_month_earnings = Column(Float, default=0.0)

    # Time Statistics
    total_teaching_hours = Column(Float, default=0.0)
    this_month_hours = Column(Float, default=0.0)

    # Subject Breakdown
    subject_stats = Column(JSONB, default=dict)  # Statistics per subject

    # Monthly Data
    monthly_data = Column(JSONB, default=dict)  # Historical monthly statistics

    last_calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
