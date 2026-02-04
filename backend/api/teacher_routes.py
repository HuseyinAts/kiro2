"""
Task 107: Teacher Pool API Routes

API endpoints for teacher registration, profile, availability, and appointments.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime
from uuid import UUID

from core.database import get_db
from services.teacher_service import TeacherService
from models.teacher_pool import (
    TeacherStatus,
    VerificationStatus,
    SubjectExpertise,
    GradeLevel,
    CertificationType,
    DayOfWeek,
    TimeSlotStatus,
    AppointmentStatus,
    AppointmentType,
)

router = APIRouter(prefix="/api/teachers", tags=["teachers"])


# ============================================================
# Request/Response Models
# ============================================================


# Task 107.1: Registration
class TeacherRegistrationRequest(BaseModel):
    full_name: str
    title: str
    bio: str
    phone: str
    email: str
    city: str
    district: str
    years_of_experience: int
    education_level: str
    university: str
    department: str
    graduation_year: int
    hourly_rate: float
    application_notes: Optional[str] = None


class TeacherProfileUpdate(BaseModel):
    title: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    hourly_rate: Optional[float] = None
    is_accepting_students: Optional[bool] = None
    online_teaching: Optional[bool] = None
    in_person_teaching: Optional[bool] = None


class TeacherVerificationRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


# Task 107.2: Expertise
class ExpertiseRequest(BaseModel):
    subject: SubjectExpertise
    grade_levels: List[str]
    proficiency_level: str
    years_teaching_subject: int
    specializations: Optional[List[str]] = None
    exam_types: Optional[List[str]] = None


class CertificationRequest(BaseModel):
    certification_type: CertificationType
    title: str
    issuing_organization: str
    issue_date: date
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    document_url: Optional[str] = None
    description: Optional[str] = None


class CertificationVerificationRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None


# Task 107.3: Availability
class AvailabilitySlotRequest(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    specific_date: Optional[date] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    max_students: int = 1
    is_recurring: bool = True


class AvailabilitySlotUpdate(BaseModel):
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_students: Optional[int] = None
    status: Optional[TimeSlotStatus] = None


# Task 107.4: Appointments
class AppointmentRequest(BaseModel):
    teacher_id: UUID
    scheduled_date: date
    start_time: time
    end_time: time
    appointment_type: AppointmentType
    subject: SubjectExpertise
    topic: str
    description: Optional[str] = None
    availability_slot_id: Optional[UUID] = None


class AppointmentConfirmRequest(BaseModel):
    meeting_url: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    cancellation_reason: str


class AppointmentCompleteRequest(BaseModel):
    session_summary: Optional[str] = None
    homework_assigned: Optional[str] = None


class ReviewRequest(BaseModel):
    overall_rating: int = Field(..., ge=1, le=5)
    title: str
    content: str
    teaching_quality: Optional[int] = Field(None, ge=1, le=5)
    communication: Optional[int] = Field(None, ge=1, le=5)
    punctuality: Optional[int] = Field(None, ge=1, le=5)
    helpfulness: Optional[int] = Field(None, ge=1, le=5)


# ============================================================
# Task 107.1: Teacher Registration Endpoints
# ============================================================


@router.post("/register")
async def register_teacher(
    request: TeacherRegistrationRequest,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Register as a teacher

    Creates a teacher profile with PENDING status awaiting verification.
    """
    service = TeacherService(db)

    # Check if user already has a teacher profile
    existing = await service.get_teacher_by_user_id(user_id)
    if existing:
        raise HTTPException(
            status_code=400, detail="User already has a teacher profile"
        )

    teacher = await service.register_teacher(
        user_id=user_id,
        full_name=request.full_name,
        title=request.title,
        bio=request.bio,
        phone=request.phone,
        email=request.email,
        city=request.city,
        district=request.district,
        years_of_experience=request.years_of_experience,
        education_level=request.education_level,
        university=request.university,
        department=request.department,
        graduation_year=request.graduation_year,
        hourly_rate=request.hourly_rate,
        application_notes=request.application_notes,
    )

    return {
        "id": str(teacher.id),
        "status": teacher.status,
        "message": "Teacher registration submitted. Awaiting verification.",
    }


@router.get("/profile/{teacher_id}")
async def get_teacher_profile(teacher_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get teacher profile with all details"""
    service = TeacherService(db)
    teacher = await service.get_teacher_profile(teacher_id)

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "id": str(teacher.id),
        "user_id": str(teacher.user_id),
        "full_name": teacher.full_name,
        "title": teacher.title,
        "bio": teacher.bio,
        "profile_photo_url": teacher.profile_photo_url,
        "city": teacher.city,
        "district": teacher.district,
        "years_of_experience": teacher.years_of_experience,
        "education_level": teacher.education_level,
        "university": teacher.university,
        "department": teacher.department,
        "status": teacher.status,
        "verification_status": teacher.verification_status,
        "average_rating": teacher.average_rating,
        "total_reviews": teacher.total_reviews,
        "total_sessions": teacher.total_sessions,
        "hourly_rate": teacher.hourly_rate,
        "currency": teacher.currency,
        "is_accepting_students": teacher.is_accepting_students,
        "online_teaching": teacher.online_teaching,
        "in_person_teaching": teacher.in_person_teaching,
        "expertise": [
            {
                "id": str(exp.id),
                "subject": exp.subject,
                "grade_levels": exp.grade_levels,
                "proficiency_level": exp.proficiency_level,
                "years_teaching_subject": exp.years_teaching_subject,
                "specializations": exp.specializations,
                "exam_types": exp.exam_types,
            }
            for exp in teacher.expertise
        ],
        "certifications": [
            {
                "id": str(cert.id),
                "certification_type": cert.certification_type,
                "title": cert.title,
                "issuing_organization": cert.issuing_organization,
                "issue_date": str(cert.issue_date),
                "verification_status": cert.verification_status,
            }
            for cert in teacher.certifications
        ],
        "created_at": teacher.created_at.isoformat(),
        "updated_at": teacher.updated_at.isoformat(),
    }


@router.get("/my-profile")
async def get_my_teacher_profile(
    user_id: UUID = Query(...), db: AsyncSession = Depends(get_db)
):
    """Get current user's teacher profile"""
    service = TeacherService(db)
    teacher = await service.get_teacher_by_user_id(user_id)

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")

    return await get_teacher_profile(teacher.id, db)


@router.put("/profile/{teacher_id}")
async def update_teacher_profile(
    teacher_id: UUID,
    request: TeacherProfileUpdate,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Update teacher profile"""
    service = TeacherService(db)

    # Verify ownership
    teacher = await service.get_teacher_profile(teacher_id)
    if not teacher or teacher.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    updated_teacher = await service.update_teacher_profile(
        teacher_id=teacher_id, **request.dict(exclude_unset=True)
    )

    return {
        "message": "Profile updated successfully",
        "teacher_id": str(updated_teacher.id),
    }


@router.post("/verify/{teacher_id}")
async def verify_teacher(
    teacher_id: UUID,
    request: TeacherVerificationRequest,
    verified_by: UUID = Query(...),  # Admin user ID
    db: AsyncSession = Depends(get_db),
):
    """
    Verify or reject teacher application (Admin only)
    """
    service = TeacherService(db)

    teacher = await service.verify_teacher(
        teacher_id=teacher_id,
        verified_by=verified_by,
        approved=request.approved,
        rejection_reason=request.rejection_reason,
    )

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "message": "Teacher verified successfully"
        if request.approved
        else "Teacher application rejected",
        "teacher_id": str(teacher.id),
        "status": teacher.status,
    }


@router.get("/search")
async def search_teachers(
    subject: Optional[SubjectExpertise] = None,
    grade_level: Optional[str] = None,
    min_rating: Optional[float] = None,
    city: Optional[str] = None,
    online_only: bool = False,
    max_hourly_rate: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Search for teachers with filters"""
    service = TeacherService(db)

    teachers = await service.search_teachers(
        subject=subject,
        grade_level=grade_level,
        min_rating=min_rating,
        city=city,
        online_only=online_only,
        max_hourly_rate=max_hourly_rate,
        limit=limit,
        offset=offset,
    )

    return {
        "teachers": [
            {
                "id": str(t.id),
                "full_name": t.full_name,
                "title": t.title,
                "bio": t.bio[:200] if t.bio else None,  # Short preview
                "city": t.city,
                "average_rating": t.average_rating,
                "total_reviews": t.total_reviews,
                "hourly_rate": t.hourly_rate,
                "years_of_experience": t.years_of_experience,
                "online_teaching": t.online_teaching,
                "in_person_teaching": t.in_person_teaching,
            }
            for t in teachers
        ],
        "count": len(teachers),
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# Task 107.2: Expertise Endpoints
# ============================================================


@router.post("/{teacher_id}/expertise")
async def add_expertise(
    teacher_id: UUID,
    request: ExpertiseRequest,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Add subject expertise for teacher"""
    service = TeacherService(db)

    # Verify ownership
    teacher = await service.get_teacher_profile(teacher_id)
    if not teacher or teacher.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    expertise = await service.add_expertise(
        teacher_id=teacher_id,
        subject=request.subject,
        grade_levels=request.grade_levels,
        proficiency_level=request.proficiency_level,
        years_teaching_subject=request.years_teaching_subject,
        specializations=request.specializations,
        exam_types=request.exam_types,
    )

    return {
        "message": "Expertise added successfully",
        "expertise_id": str(expertise.id),
    }


@router.get("/{teacher_id}/expertise")
async def get_teacher_expertise(teacher_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get all expertise areas for teacher"""
    service = TeacherService(db)
    expertise_list = await service.get_teacher_expertise(teacher_id)

    return {
        "expertise": [
            {
                "id": str(exp.id),
                "subject": exp.subject,
                "grade_levels": exp.grade_levels,
                "proficiency_level": exp.proficiency_level,
                "years_teaching_subject": exp.years_teaching_subject,
                "specializations": exp.specializations,
                "exam_types": exp.exam_types,
                "is_verified": exp.is_verified,
            }
            for exp in expertise_list
        ]
    }


@router.delete("/expertise/{expertise_id}")
async def delete_expertise(
    expertise_id: UUID, user_id: UUID = Query(...), db: AsyncSession = Depends(get_db)
):
    """Delete expertise"""
    service = TeacherService(db)
    success = await service.delete_expertise(expertise_id)

    if not success:
        raise HTTPException(status_code=404, detail="Expertise not found")

    return {"message": "Expertise deleted successfully"}


# ============================================================
# Task 107.2: Certification Endpoints
# ============================================================


@router.post("/{teacher_id}/certifications")
async def add_certification(
    teacher_id: UUID,
    request: CertificationRequest,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Add certification for teacher"""
    service = TeacherService(db)

    # Verify ownership
    teacher = await service.get_teacher_profile(teacher_id)
    if not teacher or teacher.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    certification = await service.add_certification(
        teacher_id=teacher_id,
        certification_type=request.certification_type,
        title=request.title,
        issuing_organization=request.issuing_organization,
        issue_date=request.issue_date,
        expiry_date=request.expiry_date,
        credential_id=request.credential_id,
        document_url=request.document_url,
        description=request.description,
    )

    return {
        "message": "Certification added successfully. Awaiting verification.",
        "certification_id": str(certification.id),
    }


@router.get("/{teacher_id}/certifications")
async def get_teacher_certifications(
    teacher_id: UUID, db: AsyncSession = Depends(get_db)
):
    """Get all certifications for teacher"""
    service = TeacherService(db)
    certifications = await service.get_teacher_certifications(teacher_id)

    return {
        "certifications": [
            {
                "id": str(cert.id),
                "certification_type": cert.certification_type,
                "title": cert.title,
                "issuing_organization": cert.issuing_organization,
                "issue_date": str(cert.issue_date),
                "expiry_date": str(cert.expiry_date) if cert.expiry_date else None,
                "credential_id": cert.credential_id,
                "document_url": cert.document_url,
                "verification_status": cert.verification_status,
                "is_featured": cert.is_featured,
            }
            for cert in certifications
        ]
    }


@router.post("/certifications/{certification_id}/verify")
async def verify_certification(
    certification_id: UUID,
    request: CertificationVerificationRequest,
    verified_by: UUID = Query(...),  # Admin user ID
    db: AsyncSession = Depends(get_db),
):
    """Verify or reject certification (Admin only)"""
    service = TeacherService(db)

    certification = await service.verify_certification(
        certification_id=certification_id,
        verified_by=verified_by,
        approved=request.approved,
        rejection_reason=request.rejection_reason,
    )

    if not certification:
        raise HTTPException(status_code=404, detail="Certification not found")

    return {
        "message": "Certification verified"
        if request.approved
        else "Certification rejected",
        "certification_id": str(certification.id),
        "verification_status": certification.verification_status,
    }


# ============================================================
# Task 107.3: Availability Endpoints
# ============================================================


@router.post("/{teacher_id}/availability")
async def add_availability_slot(
    teacher_id: UUID,
    request: AvailabilitySlotRequest,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Add availability time slot"""
    service = TeacherService(db)

    # Verify ownership
    teacher = await service.get_teacher_profile(teacher_id)
    if not teacher or teacher.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    slot = await service.add_availability_slot(
        teacher_id=teacher_id,
        day_of_week=request.day_of_week,
        start_time=request.start_time,
        end_time=request.end_time,
        specific_date=request.specific_date,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
        max_students=request.max_students,
        is_recurring=request.is_recurring,
    )

    return {"message": "Availability slot added successfully", "slot_id": str(slot.id)}


@router.get("/{teacher_id}/availability")
async def get_teacher_availability(
    teacher_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get teacher's availability slots"""
    service = TeacherService(db)
    slots = await service.get_teacher_availability(teacher_id, start_date, end_date)

    return {
        "availability": [
            {
                "id": str(slot.id),
                "day_of_week": slot.day_of_week,
                "start_time": str(slot.start_time),
                "end_time": str(slot.end_time),
                "specific_date": str(slot.specific_date)
                if slot.specific_date
                else None,
                "is_recurring": slot.is_recurring,
                "status": slot.status,
                "max_students": slot.max_students,
                "current_bookings": slot.current_bookings,
            }
            for slot in slots
        ]
    }


@router.put("/availability/{slot_id}")
async def update_availability_slot(
    slot_id: UUID,
    request: AvailabilitySlotUpdate,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Update availability slot"""
    service = TeacherService(db)

    slot = await service.update_availability_slot(
        slot_id=slot_id, **request.dict(exclude_unset=True)
    )

    if not slot:
        raise HTTPException(status_code=404, detail="Availability slot not found")

    return {"message": "Availability slot updated successfully"}


@router.delete("/availability/{slot_id}")
async def delete_availability_slot(
    slot_id: UUID, user_id: UUID = Query(...), db: AsyncSession = Depends(get_db)
):
    """Delete availability slot"""
    service = TeacherService(db)
    success = await service.delete_availability_slot(slot_id)

    if not success:
        raise HTTPException(status_code=404, detail="Availability slot not found")

    return {"message": "Availability slot deleted successfully"}


@router.post("/availability/{slot_id}/block")
async def block_time_slot(
    slot_id: UUID, user_id: UUID = Query(...), db: AsyncSession = Depends(get_db)
):
    """Block a time slot (make unavailable)"""
    service = TeacherService(db)
    slot = await service.block_time_slot(slot_id)

    if not slot:
        raise HTTPException(status_code=404, detail="Availability slot not found")

    return {"message": "Time slot blocked successfully"}


# ============================================================
# Task 107.4: Appointment Endpoints
# ============================================================


@router.post("/appointments")
async def create_appointment(
    request: AppointmentRequest,
    student_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Create new appointment (student books teacher)"""
    service = TeacherService(db)

    appointment = await service.create_appointment(
        teacher_id=request.teacher_id,
        student_id=student_id,
        scheduled_date=request.scheduled_date,
        start_time=request.start_time,
        end_time=request.end_time,
        appointment_type=request.appointment_type,
        subject=request.subject,
        topic=request.topic,
        description=request.description,
        availability_slot_id=request.availability_slot_id,
    )

    return {
        "message": "Appointment created. Awaiting teacher confirmation.",
        "appointment_id": str(appointment.id),
        "price": appointment.price,
        "currency": appointment.currency,
    }


@router.post("/appointments/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: UUID,
    request: AppointmentConfirmRequest,
    confirmed_by: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Confirm appointment (teacher confirms)"""
    service = TeacherService(db)

    appointment = await service.confirm_appointment(
        appointment_id=appointment_id,
        confirmed_by=confirmed_by,
        meeting_url=request.meeting_url,
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return {
        "message": "Appointment confirmed successfully",
        "appointment_id": str(appointment.id),
        "meeting_url": appointment.meeting_url,
    }


@router.post("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: UUID,
    request: AppointmentCancelRequest,
    cancelled_by: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Cancel appointment"""
    service = TeacherService(db)

    appointment = await service.cancel_appointment(
        appointment_id=appointment_id,
        cancelled_by=cancelled_by,
        cancellation_reason=request.cancellation_reason,
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return {"message": "Appointment cancelled successfully"}


@router.post("/appointments/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: UUID,
    request: AppointmentCompleteRequest,
    user_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Mark appointment as completed (teacher)"""
    service = TeacherService(db)

    appointment = await service.complete_appointment(
        appointment_id=appointment_id,
        session_summary=request.session_summary,
        homework_assigned=request.homework_assigned,
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return {"message": "Appointment marked as completed"}


@router.get("/{teacher_id}/appointments")
async def get_teacher_appointments(
    teacher_id: UUID,
    status: Optional[AppointmentStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get teacher's appointments"""
    service = TeacherService(db)
    appointments = await service.get_teacher_appointments(
        teacher_id=teacher_id, status=status, start_date=start_date, end_date=end_date
    )

    return {
        "appointments": [
            {
                "id": str(appt.id),
                "student_id": str(appt.student_id),
                "scheduled_date": str(appt.scheduled_date),
                "start_time": str(appt.start_time),
                "end_time": str(appt.end_time),
                "duration_minutes": appt.duration_minutes,
                "appointment_type": appt.appointment_type,
                "subject": appt.subject,
                "topic": appt.topic,
                "status": appt.status,
                "price": appt.price,
                "meeting_url": appt.meeting_url,
            }
            for appt in appointments
        ]
    }


@router.get("/my-appointments")
async def get_my_appointments(
    student_id: UUID = Query(...),
    status: Optional[AppointmentStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get student's appointments"""
    service = TeacherService(db)
    appointments = await service.get_student_appointments(
        student_id=student_id, status=status
    )

    return {
        "appointments": [
            {
                "id": str(appt.id),
                "teacher_id": str(appt.teacher_id),
                "scheduled_date": str(appt.scheduled_date),
                "start_time": str(appt.start_time),
                "end_time": str(appt.end_time),
                "duration_minutes": appt.duration_minutes,
                "appointment_type": appt.appointment_type,
                "subject": appt.subject,
                "topic": appt.topic,
                "status": appt.status,
                "price": appt.price,
                "meeting_url": appt.meeting_url,
            }
            for appt in appointments
        ]
    }


# ============================================================
# Reviews Endpoints
# ============================================================


@router.post("/{teacher_id}/reviews")
async def add_review(
    teacher_id: UUID,
    request: ReviewRequest,
    student_id: UUID = Query(...),
    appointment_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Add review for teacher"""
    service = TeacherService(db)

    review = await service.add_review(
        teacher_id=teacher_id,
        student_id=student_id,
        appointment_id=appointment_id,
        overall_rating=request.overall_rating,
        title=request.title,
        content=request.content,
        teaching_quality=request.teaching_quality,
        communication=request.communication,
        punctuality=request.punctuality,
        helpfulness=request.helpfulness,
    )

    return {"message": "Review added successfully", "review_id": str(review.id)}


@router.get("/{teacher_id}/reviews")
async def get_teacher_reviews(
    teacher_id: UUID,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Get reviews for teacher"""
    service = TeacherService(db)
    reviews = await service.get_teacher_reviews(teacher_id, limit, offset)

    return {
        "reviews": [
            {
                "id": str(review.id),
                "student_id": str(review.student_id),
                "overall_rating": review.overall_rating,
                "teaching_quality": review.teaching_quality,
                "communication": review.communication,
                "punctuality": review.punctuality,
                "helpfulness": review.helpfulness,
                "title": review.title,
                "content": review.content,
                "teacher_response": review.teacher_response,
                "created_at": review.created_at.isoformat(),
                "helpful_count": review.helpful_count,
            }
            for review in reviews
        ],
        "count": len(reviews),
    }
