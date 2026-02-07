"""
Task 107: Teacher Service

Service layer for teacher registration, profile management, availability, and appointments.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, List
from uuid import UUID
import logging

from models.teacher_pool import (
    TeacherPoolProfile,  # Renamed from TeacherProfile to avoid conflict with models.database.TeacherProfile
    TeacherExpertise,
    TeacherCertification,
    TeacherAvailability,
    Appointment,
    AppointmentReminder,
    TeacherReview,
    TeacherStatus,
    VerificationStatus,
    SubjectExpertise,
    CertificationType,
    DayOfWeek,
    TimeSlotStatus,
    AppointmentStatus,
    AppointmentType,
)

# Alias for backward compatibility in this file
TeacherProfile = TeacherPoolProfile

logger = logging.getLogger(__name__)


class TeacherService:
    """Service for managing teachers"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Task 107.1: Teacher Registration System
    # ============================================================

    async def register_teacher(
        self,
        user_id: UUID,
        full_name: str,
        title: str,
        bio: str,
        phone: str,
        email: str,
        city: str,
        district: str,
        years_of_experience: int,
        education_level: str,
        university: str,
        department: str,
        graduation_year: int,
        hourly_rate: float,
        application_notes: Optional[str] = None,
    ) -> TeacherProfile:
        """
        Register a new teacher

        Creates a teacher profile with PENDING status awaiting verification.
        """
        teacher = TeacherProfile(
            user_id=user_id,
            full_name=full_name,
            title=title,
            bio=bio,
            phone=phone,
            email=email,
            city=city,
            district=district,
            years_of_experience=years_of_experience,
            education_level=education_level,
            university=university,
            department=department,
            graduation_year=graduation_year,
            hourly_rate=hourly_rate,
            application_notes=application_notes,
            status=TeacherStatus.PENDING,
            verification_status=VerificationStatus.NOT_SUBMITTED,
        )

        self.db.add(teacher)
        await self.db.commit()
        await self.db.refresh(teacher)

        logger.info(f"Teacher registered: {teacher.id} ({full_name})")
        return teacher

    async def get_teacher_profile(self, teacher_id: UUID) -> Optional[TeacherProfile]:
        """Get teacher profile by ID with all relationships"""
        query = (
            select(TeacherProfile)
            .options(
                selectinload(TeacherProfile.expertise),
                selectinload(TeacherProfile.certifications),
                selectinload(TeacherProfile.availability),
                selectinload(TeacherProfile.reviews),
            )
            .where(TeacherProfile.id == teacher_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_teacher_by_user_id(self, user_id: UUID) -> Optional[TeacherProfile]:
        """Get teacher profile by user ID"""
        query = select(TeacherProfile).where(TeacherProfile.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_teacher_profile(
        self, teacher_id: UUID, **kwargs
    ) -> Optional[TeacherProfile]:
        """Update teacher profile"""
        teacher = await self.get_teacher_profile(teacher_id)
        if not teacher:
            return None

        for key, value in kwargs.items():
            if hasattr(teacher, key):
                setattr(teacher, key, value)

        teacher.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(teacher)

        return teacher

    async def verify_teacher(
        self,
        teacher_id: UUID,
        verified_by: UUID,
        approved: bool,
        rejection_reason: Optional[str] = None,
    ) -> Optional[TeacherProfile]:
        """
        Verify or reject teacher application

        Admin action to approve or reject teacher registration.
        """
        teacher = await self.get_teacher_profile(teacher_id)
        if not teacher:
            return None

        if approved:
            teacher.status = TeacherStatus.VERIFIED
            teacher.verification_status = VerificationStatus.APPROVED
            teacher.verified_at = datetime.now(timezone.utc)
            teacher.verified_by = verified_by
        else:
            teacher.status = TeacherStatus.REJECTED
            teacher.verification_status = VerificationStatus.REJECTED
            teacher.rejection_reason = rejection_reason

        await self.db.commit()
        await self.db.refresh(teacher)

        logger.info(f"Teacher {'verified' if approved else 'rejected'}: {teacher_id}")
        return teacher

    async def search_teachers(
        self,
        subject: Optional[SubjectExpertise] = None,
        grade_level: Optional[str] = None,
        min_rating: Optional[float] = None,
        city: Optional[str] = None,
        online_only: bool = False,
        max_hourly_rate: Optional[float] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[TeacherProfile]:
        """
        Search for teachers with filters
        """
        query = select(TeacherProfile).where(
            TeacherProfile.status == TeacherStatus.VERIFIED,
            TeacherProfile.is_accepting_students == True,
        )

        # Apply filters
        if subject:
            # Join with expertise
            query = query.join(TeacherExpertise).where(
                TeacherExpertise.subject == subject
            )

        if min_rating:
            query = query.where(TeacherProfile.average_rating >= min_rating)

        if city:
            query = query.where(TeacherProfile.city.ilike(f"%{city}%"))

        if online_only:
            query = query.where(TeacherProfile.online_teaching == True)

        if max_hourly_rate:
            query = query.where(TeacherProfile.hourly_rate <= max_hourly_rate)

        # Order by rating
        query = query.order_by(TeacherProfile.average_rating.desc())

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Task 107.2: Subject Expertise & Specialization
    # ============================================================

    async def add_expertise(
        self,
        teacher_id: UUID,
        subject: SubjectExpertise,
        grade_levels: List[str],
        proficiency_level: str,
        years_teaching_subject: int,
        specializations: Optional[List[str]] = None,
        exam_types: Optional[List[str]] = None,
    ) -> TeacherExpertise:
        """Add subject expertise for teacher"""
        expertise = TeacherExpertise(
            teacher_id=teacher_id,
            subject=subject,
            grade_levels=grade_levels,
            proficiency_level=proficiency_level,
            years_teaching_subject=years_teaching_subject,
            specializations=specializations or [],
            exam_types=exam_types or [],
        )

        self.db.add(expertise)
        await self.db.commit()
        await self.db.refresh(expertise)

        return expertise

    async def get_teacher_expertise(self, teacher_id: UUID) -> List[TeacherExpertise]:
        """Get all expertise areas for a teacher"""
        query = select(TeacherExpertise).where(
            TeacherExpertise.teacher_id == teacher_id
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_expertise(
        self, expertise_id: UUID, **kwargs
    ) -> Optional[TeacherExpertise]:
        """Update expertise details"""
        query = select(TeacherExpertise).where(TeacherExpertise.id == expertise_id)
        result = await self.db.execute(query)
        expertise = result.scalar_one_or_none()

        if not expertise:
            return None

        for key, value in kwargs.items():
            if hasattr(expertise, key):
                setattr(expertise, key, value)

        await self.db.commit()
        await self.db.refresh(expertise)

        return expertise

    async def delete_expertise(self, expertise_id: UUID) -> bool:
        """Remove expertise"""
        query = delete(TeacherExpertise).where(TeacherExpertise.id == expertise_id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

    # ============================================================
    # Task 107.2: Certifications
    # ============================================================

    async def add_certification(
        self,
        teacher_id: UUID,
        certification_type: CertificationType,
        title: str,
        issuing_organization: str,
        issue_date: date,
        expiry_date: Optional[date] = None,
        credential_id: Optional[str] = None,
        document_url: Optional[str] = None,
        description: Optional[str] = None,
    ) -> TeacherCertification:
        """Add certification for teacher"""
        certification = TeacherCertification(
            teacher_id=teacher_id,
            certification_type=certification_type,
            title=title,
            issuing_organization=issuing_organization,
            issue_date=issue_date,
            expiry_date=expiry_date,
            credential_id=credential_id,
            document_url=document_url,
            description=description,
        )

        self.db.add(certification)
        await self.db.commit()
        await self.db.refresh(certification)

        return certification

    async def verify_certification(
        self,
        certification_id: UUID,
        verified_by: UUID,
        approved: bool,
        rejection_reason: Optional[str] = None,
    ) -> Optional[TeacherCertification]:
        """Verify or reject certification"""
        query = select(TeacherCertification).where(
            TeacherCertification.id == certification_id
        )
        result = await self.db.execute(query)
        certification = result.scalar_one_or_none()

        if not certification:
            return None

        if approved:
            certification.verification_status = VerificationStatus.APPROVED
            certification.verified_at = datetime.now(timezone.utc)
            certification.verified_by = verified_by
        else:
            certification.verification_status = VerificationStatus.REJECTED
            certification.rejection_reason = rejection_reason

        await self.db.commit()
        await self.db.refresh(certification)

        return certification

    async def get_teacher_certifications(
        self, teacher_id: UUID
    ) -> List[TeacherCertification]:
        """Get all certifications for a teacher"""
        query = (
            select(TeacherCertification)
            .where(TeacherCertification.teacher_id == teacher_id)
            .order_by(
                TeacherCertification.display_order,
                TeacherCertification.issue_date.desc(),
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Task 107.3: Availability Calendar
    # ============================================================

    async def add_availability_slot(
        self,
        teacher_id: UUID,
        day_of_week: DayOfWeek,
        start_time: time,
        end_time: time,
        specific_date: Optional[date] = None,
        valid_from: Optional[date] = None,
        valid_until: Optional[date] = None,
        max_students: int = 1,
        is_recurring: bool = True,
    ) -> TeacherAvailability:
        """Add availability time slot"""
        availability = TeacherAvailability(
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            specific_date=specific_date,
            valid_from=valid_from,
            valid_until=valid_until,
            max_students=max_students,
            is_recurring=is_recurring,
        )

        self.db.add(availability)
        await self.db.commit()
        await self.db.refresh(availability)

        return availability

    async def get_teacher_availability(
        self,
        teacher_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[TeacherAvailability]:
        """Get teacher availability slots"""
        query = select(TeacherAvailability).where(
            TeacherAvailability.teacher_id == teacher_id,
            TeacherAvailability.status == TimeSlotStatus.AVAILABLE,
        )

        if start_date and end_date:
            query = query.where(
                or_(
                    TeacherAvailability.specific_date.between(start_date, end_date),
                    and_(
                        TeacherAvailability.is_recurring == True,
                        or_(
                            TeacherAvailability.valid_until == None,
                            TeacherAvailability.valid_until >= start_date,
                        ),
                    ),
                )
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_availability_slot(
        self, slot_id: UUID, **kwargs
    ) -> Optional[TeacherAvailability]:
        """Update availability slot"""
        query = select(TeacherAvailability).where(TeacherAvailability.id == slot_id)
        result = await self.db.execute(query)
        slot = result.scalar_one_or_none()

        if not slot:
            return None

        for key, value in kwargs.items():
            if hasattr(slot, key):
                setattr(slot, key, value)

        await self.db.commit()
        await self.db.refresh(slot)

        return slot

    async def delete_availability_slot(self, slot_id: UUID) -> bool:
        """Delete availability slot"""
        query = delete(TeacherAvailability).where(TeacherAvailability.id == slot_id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

    async def block_time_slot(self, slot_id: UUID) -> Optional[TeacherAvailability]:
        """Block a time slot (make unavailable)"""
        return await self.update_availability_slot(
            slot_id, status=TimeSlotStatus.BLOCKED
        )

    # ============================================================
    # Task 107.4: Appointment System
    # ============================================================

    async def create_appointment(
        self,
        teacher_id: UUID,
        student_id: UUID,
        scheduled_date: date,
        start_time: time,
        end_time: time,
        appointment_type: AppointmentType,
        subject: SubjectExpertise,
        topic: str,
        description: Optional[str] = None,
        availability_slot_id: Optional[UUID] = None,
    ) -> Appointment:
        """
        Create new appointment (booking)

        Creates appointment with PENDING status awaiting teacher confirmation.
        """
        # Calculate duration
        start_dt = datetime.combine(scheduled_date, start_time)
        end_dt = datetime.combine(scheduled_date, end_time)
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

        # Get teacher's hourly rate
        teacher = await self.get_teacher_profile(teacher_id)
        if not teacher:
            raise ValueError("Teacher not found")

        price = (duration_minutes / 60) * teacher.hourly_rate

        appointment = Appointment(
            teacher_id=teacher_id,
            student_id=student_id,
            availability_slot_id=availability_slot_id,
            appointment_type=appointment_type,
            subject=subject,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            topic=topic,
            description=description,
            price=price,
            currency=teacher.currency,
        )

        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)

        # Update availability slot if specified
        if availability_slot_id:
            await self._increment_slot_booking(availability_slot_id)

        logger.info(f"Appointment created: {appointment.id}")
        return appointment

    async def confirm_appointment(
        self,
        appointment_id: UUID,
        confirmed_by: UUID,
        meeting_url: Optional[str] = None,
    ) -> Optional[Appointment]:
        """Teacher confirms appointment"""
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await self.db.execute(query)
        appointment = result.scalar_one_or_none()

        if not appointment:
            return None

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.confirmed_at = datetime.now(timezone.utc)
        appointment.confirmed_by = confirmed_by

        if meeting_url:
            appointment.meeting_url = meeting_url

        await self.db.commit()
        await self.db.refresh(appointment)

        # Schedule reminders
        await self._schedule_reminders(appointment)

        return appointment

    async def cancel_appointment(
        self, appointment_id: UUID, cancelled_by: UUID, cancellation_reason: str
    ) -> Optional[Appointment]:
        """Cancel appointment"""
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await self.db.execute(query)
        appointment = result.scalar_one_or_none()

        if not appointment:
            return None

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.now(timezone.utc)
        appointment.cancelled_by = cancelled_by
        appointment.cancellation_reason = cancellation_reason

        await self.db.commit()
        await self.db.refresh(appointment)

        # Free up availability slot
        if appointment.availability_slot_id:
            await self._decrement_slot_booking(appointment.availability_slot_id)

        return appointment

    async def complete_appointment(
        self,
        appointment_id: UUID,
        session_summary: Optional[str] = None,
        homework_assigned: Optional[str] = None,
    ) -> Optional[Appointment]:
        """Mark appointment as completed"""
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await self.db.execute(query)
        appointment = result.scalar_one_or_none()

        if not appointment:
            return None

        appointment.status = AppointmentStatus.COMPLETED
        appointment.completed_at = datetime.now(timezone.utc)
        appointment.session_summary = session_summary
        appointment.homework_assigned = homework_assigned

        await self.db.commit()
        await self.db.refresh(appointment)

        # Update teacher statistics
        await self._update_teacher_stats(appointment.teacher_id)

        return appointment

    async def get_teacher_appointments(
        self,
        teacher_id: UUID,
        status: Optional[AppointmentStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Appointment]:
        """Get teacher's appointments"""
        query = select(Appointment).where(Appointment.teacher_id == teacher_id)

        if status:
            query = query.where(Appointment.status == status)

        if start_date and end_date:
            query = query.where(
                Appointment.scheduled_date.between(start_date, end_date)
            )

        query = query.order_by(Appointment.scheduled_date, Appointment.start_time)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_student_appointments(
        self, student_id: UUID, status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """Get student's appointments"""
        query = select(Appointment).where(Appointment.student_id == student_id)

        if status:
            query = query.where(Appointment.status == status)

        query = query.order_by(
            Appointment.scheduled_date.desc(), Appointment.start_time.desc()
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Task 107.4: Reminder Notifications
    # ============================================================

    async def _schedule_reminders(self, appointment: Appointment):
        """Schedule reminders for appointment"""
        # 24 hours before
        remind_24h = datetime.combine(
            appointment.scheduled_date, appointment.start_time
        ) - timedelta(hours=24)
        if remind_24h > datetime.now(timezone.utc):
            await self._create_reminder(
                appointment.id,
                appointment.student_id,
                remind_24h,
                "student",
                "24h_before",
            )
            await self._create_reminder(
                appointment.id,
                appointment.teacher_id,
                remind_24h,
                "teacher",
                "24h_before",
            )

        # 1 hour before
        remind_1h = datetime.combine(
            appointment.scheduled_date, appointment.start_time
        ) - timedelta(hours=1)
        if remind_1h > datetime.now(timezone.utc):
            await self._create_reminder(
                appointment.id,
                appointment.student_id,
                remind_1h,
                "student",
                "1h_before",
            )
            await self._create_reminder(
                appointment.id,
                appointment.teacher_id,
                remind_1h,
                "teacher",
                "1h_before",
            )

    async def _create_reminder(
        self,
        appointment_id: UUID,
        recipient_id: UUID,
        remind_at: datetime,
        recipient_type: str,
        message_template: str,
    ):
        """Create reminder notification"""
        reminder = AppointmentReminder(
            appointment_id=appointment_id,
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            remind_at=remind_at,
            reminder_type="email",  # Can be extended to SMS, push
            message_template=message_template,
        )

        self.db.add(reminder)
        await self.db.commit()

    async def get_pending_reminders(self) -> List[AppointmentReminder]:
        """Get reminders that need to be sent"""
        query = select(AppointmentReminder).where(
            AppointmentReminder.is_sent == False,
            AppointmentReminder.remind_at <= datetime.now(timezone.utc),
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_reminder_sent(
        self, reminder_id: UUID, success: bool, error_message: Optional[str] = None
    ):
        """Mark reminder as sent"""
        query = select(AppointmentReminder).where(AppointmentReminder.id == reminder_id)
        result = await self.db.execute(query)
        reminder = result.scalar_one_or_none()

        if reminder:
            reminder.is_sent = True
            reminder.sent_at = datetime.now(timezone.utc)
            reminder.delivery_status = "sent" if success else "failed"
            reminder.error_message = error_message
            await self.db.commit()

    # ============================================================
    # Reviews & Ratings
    # ============================================================

    async def add_review(
        self,
        teacher_id: UUID,
        student_id: UUID,
        appointment_id: UUID,
        overall_rating: int,
        title: str,
        content: str,
        teaching_quality: Optional[int] = None,
        communication: Optional[int] = None,
        punctuality: Optional[int] = None,
        helpfulness: Optional[int] = None,
    ) -> TeacherReview:
        """Add student review for teacher"""
        review = TeacherReview(
            teacher_id=teacher_id,
            student_id=student_id,
            appointment_id=appointment_id,
            overall_rating=overall_rating,
            title=title,
            content=content,
            teaching_quality=teaching_quality,
            communication=communication,
            punctuality=punctuality,
            helpfulness=helpfulness,
        )

        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)

        # Update teacher's average rating
        await self._update_teacher_rating(teacher_id)

        return review

    async def get_teacher_reviews(
        self, teacher_id: UUID, limit: int = 20, offset: int = 0
    ) -> List[TeacherReview]:
        """Get reviews for a teacher"""
        query = (
            select(TeacherReview)
            .where(
                TeacherReview.teacher_id == teacher_id, TeacherReview.is_hidden == False
            )
            .order_by(TeacherReview.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # Helper Methods
    # ============================================================

    async def _increment_slot_booking(self, slot_id: UUID):
        """Increment booking count for availability slot"""
        query = select(TeacherAvailability).where(TeacherAvailability.id == slot_id)
        result = await self.db.execute(query)
        slot = result.scalar_one_or_none()

        if slot:
            slot.current_bookings += 1
            if slot.current_bookings >= slot.max_students:
                slot.status = TimeSlotStatus.BOOKED
            await self.db.commit()

    async def _decrement_slot_booking(self, slot_id: UUID):
        """Decrement booking count for availability slot"""
        query = select(TeacherAvailability).where(TeacherAvailability.id == slot_id)
        result = await self.db.execute(query)
        slot = result.scalar_one_or_none()

        if slot and slot.current_bookings > 0:
            slot.current_bookings -= 1
            slot.status = TimeSlotStatus.AVAILABLE
            await self.db.commit()

    async def _update_teacher_rating(self, teacher_id: UUID):
        """Recalculate teacher's average rating"""
        query = select(
            func.avg(TeacherReview.overall_rating), func.count(TeacherReview.id)
        ).where(
            TeacherReview.teacher_id == teacher_id, TeacherReview.is_hidden == False
        )
        result = await self.db.execute(query)
        avg_rating, total_reviews = result.one()

        teacher = await self.get_teacher_profile(teacher_id)
        if teacher:
            teacher.average_rating = float(avg_rating) if avg_rating else 0.0
            teacher.total_reviews = total_reviews or 0
            await self.db.commit()

    async def _update_teacher_stats(self, teacher_id: UUID):
        """Update teacher statistics after session completion"""
        # This would update TeacherStatistics table
        # Implementation can be expanded based on requirements
        pass
