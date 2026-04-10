"""
KIRO2 — Teacher Classroom API
==============================
Öğretmen sınıf yönetimi endpointleri. Prefix: /api/v1/teacher

Mevcut /api/v1/teachers (marketplace/randevu) ile ayrı sistemdir.

Endpoints:
  GET/POST   /classes
  GET        /students
  GET/POST   /exams
  DELETE     /exams/{id}
  GET/POST   /assignments
  DELETE     /assignments/{id}
  GET/POST   /contents
  DELETE     /contents/{id}
  GET        /reports
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db
from models.teacher_classroom import (
    TeacherAssignment,
    TeacherClassroom,
    TeacherClassroomStudent,
    TeacherContent,
    TeacherExamConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/teacher", tags=["teacher-classroom"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class ClassCreate(BaseModel):
    """Canonical English field names; Turkish aliases retained for legacy callers."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="sinif_adi")
    grade_level: str = Field(..., alias="seviye")
    subject_area: str = Field(..., alias="ders")


class ExamCreate(BaseModel):
    baslik: str
    aciklama: str = ""
    sinav_tipi: str = "TYT"
    soru_sayisi: int = 20
    sure_dakika: int = 60


class AssignmentCreate(BaseModel):
    baslik: str
    aciklama: str = ""
    sinif: str = ""
    teslim_tarihi: str = ""  # datetime-local string from frontend


class ContentCreate(BaseModel):
    baslik: str
    aciklama: str = ""
    tip: str = "diger"
    konu: str = ""
    sinif: str = ""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _fmt_dt(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


@router.get("/classes")
async def list_classes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(TeacherClassroom)
        .where(TeacherClassroom.teacher_user_id == str(current_user.id))
        .order_by(TeacherClassroom.created_at.desc())
    )
    rows = result.scalars().all()

    # Student count per classroom
    student_counts: dict[str, int] = {}
    if rows:
        ids = [r.id for r in rows]
        cnt_result = await db.execute(
            select(
                TeacherClassroomStudent.classroom_id,
                func.count(TeacherClassroomStudent.id).label("cnt"),
            )
            .where(TeacherClassroomStudent.classroom_id.in_(ids))
            .group_by(TeacherClassroomStudent.classroom_id)
        )
        student_counts = {str(r.classroom_id): r.cnt for r in cnt_result}

    data = [
        {
            "sinif_id": str(r.id),
            "sinif_adi": r.sinif_adi,
            "seviye": r.seviye,
            "ders": r.ders,
            "ogrenci_sayisi": student_counts.get(str(r.id), 0),
            "ortalama_basari": 0,
        }
        for r in rows
    ]
    return {"success": True, "data": data}


@router.post("/classes")
async def create_class(
    body: ClassCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    classroom = TeacherClassroom(
        teacher_user_id=str(current_user.id),
        sinif_adi=body.name,
        seviye=body.grade_level,
        ders=body.subject_area,
    )
    db.add(classroom)
    await db.commit()
    await db.refresh(classroom)
    return {
        "success": True,
        "data": {
            "sinif_id": str(classroom.id),
            "sinif_adi": classroom.sinif_adi,
            "seviye": classroom.seviye,
            "ders": classroom.ders,
            "ogrenci_sayisi": 0,
            "ortalama_basari": 0,
        },
    }


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------


@router.get("/students")
async def list_students(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # Return students enrolled in this teacher's classrooms
    classrooms_result = await db.execute(
        select(TeacherClassroom.id, TeacherClassroom.sinif_adi).where(
            TeacherClassroom.teacher_user_id == str(current_user.id)
        )
    )
    classrooms = classrooms_result.all()
    classroom_ids = [r.id for r in classrooms]
    classroom_names = {str(r.id): r.sinif_adi for r in classrooms}

    if not classroom_ids:
        return {"data": {"students": []}}

    students_result = await db.execute(
        select(TeacherClassroomStudent)
        .where(TeacherClassroomStudent.classroom_id.in_(classroom_ids))
        .order_by(TeacherClassroomStudent.joined_at.desc())
    )
    rows = students_result.scalars().all()

    data = [
        {
            "id": str(r.id),
            "student_user_id": r.student_user_id,
            "sinif": classroom_names.get(str(r.classroom_id), ""),
            "joined_at": _fmt_dt(r.joined_at),
            # Extended profile fields (filled by student service integration later)
            "ad": "",
            "soyad": "",
            "email": "",
            "ortalama": 0,
            "tamamlanan_sinav": 0,
            "toplam_sinav": 0,
        }
        for r in rows
    ]
    return {"data": {"students": data}}


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------


@router.get("/exams")
async def list_exams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(TeacherExamConfig)
        .where(TeacherExamConfig.teacher_user_id == str(current_user.id))
        .order_by(TeacherExamConfig.created_at.desc())
    )
    rows = result.scalars().all()
    data = [
        {
            "id": str(r.id),
            "baslik": r.baslik,
            "aciklama": r.aciklama or "",
            "sinav_tipi": r.sinav_tipi,
            "soru_sayisi": r.soru_sayisi,
            "sure_dakika": r.sure_dakika,
            "durum": r.durum,
            "olusturma_tarihi": _fmt_dt(r.created_at),
            "katilimci_sayisi": 0,
        }
        for r in rows
    ]
    return {"data": {"exams": data}}


@router.post("/exams", status_code=201)
async def create_exam(
    body: ExamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    exam = TeacherExamConfig(
        teacher_user_id=str(current_user.id),
        baslik=body.baslik,
        aciklama=body.aciklama,
        sinav_tipi=body.sinav_tipi,
        soru_sayisi=body.soru_sayisi,
        sure_dakika=body.sure_dakika,
        durum="taslak",
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)
    return {
        "data": {
            "id": str(exam.id),
            "baslik": exam.baslik,
            "aciklama": exam.aciklama or "",
            "sinav_tipi": exam.sinav_tipi,
            "soru_sayisi": exam.soru_sayisi,
            "sure_dakika": exam.sure_dakika,
            "durum": exam.durum,
            "olusturma_tarihi": _fmt_dt(exam.created_at),
            "katilimci_sayisi": 0,
        }
    }


@router.delete("/exams/{exam_id}")
async def delete_exam(
    exam_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(TeacherExamConfig).where(
            TeacherExamConfig.id == exam_id,
            TeacherExamConfig.teacher_user_id == str(current_user.id),
        )
    )
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Sınav bulunamadı")
    await db.delete(exam)
    await db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


@router.get("/assignments")
async def list_assignments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(TeacherAssignment)
        .where(TeacherAssignment.teacher_user_id == str(current_user.id))
        .order_by(TeacherAssignment.created_at.desc())
    )
    rows = result.scalars().all()
    data = [
        {
            "id": str(r.id),
            "baslik": r.baslik,
            "aciklama": r.aciklama or "",
            "sinif": r.sinif or "",
            "teslim_tarihi": _fmt_dt(r.teslim_tarihi),
            "olusturma_tarihi": _fmt_dt(r.created_at),
            "durum": r.durum,
            "teslim_eden": 0,
            "toplam_ogrenci": 0,
        }
        for r in rows
    ]
    return {"data": {"assignments": data}}


@router.post("/assignments", status_code=201)
async def create_assignment(
    body: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    teslim_tarihi: datetime | None = None
    if body.teslim_tarihi:
        try:
            teslim_tarihi = datetime.fromisoformat(body.teslim_tarihi)
        except ValueError:
            pass

    assignment = TeacherAssignment(
        teacher_user_id=str(current_user.id),
        baslik=body.baslik,
        aciklama=body.aciklama,
        sinif=body.sinif,
        teslim_tarihi=teslim_tarihi,
        durum="aktif",
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return {
        "data": {
            "id": str(assignment.id),
            "baslik": assignment.baslik,
            "aciklama": assignment.aciklama or "",
            "sinif": assignment.sinif or "",
            "teslim_tarihi": _fmt_dt(assignment.teslim_tarihi),
            "olusturma_tarihi": _fmt_dt(assignment.created_at),
            "durum": assignment.durum,
            "teslim_eden": 0,
            "toplam_ogrenci": 0,
        }
    }


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(TeacherAssignment).where(
            TeacherAssignment.id == assignment_id,
            TeacherAssignment.teacher_user_id == str(current_user.id),
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Ödev bulunamadı")
    await db.delete(assignment)
    await db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# Contents
# ---------------------------------------------------------------------------


@router.get("/contents")
async def list_contents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(TeacherContent)
        .where(TeacherContent.teacher_user_id == str(current_user.id))
        .order_by(TeacherContent.created_at.desc())
    )
    rows = result.scalars().all()
    data = [
        {
            "id": str(r.id),
            "baslik": r.baslik,
            "aciklama": r.aciklama or "",
            "tip": r.tip,
            "konu": r.konu or "",
            "sinif": r.sinif or "",
            "tarih": _fmt_dt(r.created_at),
            "boyut": "—",
            "goruntulenme": r.goruntulenme,
        }
        for r in rows
    ]
    return {"data": {"contents": data}}


@router.post("/contents", status_code=201)
async def create_content(
    body: ContentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    content = TeacherContent(
        teacher_user_id=str(current_user.id),
        baslik=body.baslik,
        aciklama=body.aciklama,
        tip=body.tip,
        konu=body.konu,
        sinif=body.sinif,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)
    return {
        "data": {
            "id": str(content.id),
            "baslik": content.baslik,
            "aciklama": content.aciklama or "",
            "tip": content.tip,
            "konu": content.konu or "",
            "sinif": content.sinif or "",
            "tarih": _fmt_dt(content.created_at),
            "boyut": "—",
            "goruntulenme": content.goruntulenme,
        }
    }


@router.delete("/contents/{content_id}")
async def delete_content(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(TeacherContent).where(
            TeacherContent.id == content_id,
            TeacherContent.teacher_user_id == str(current_user.id),
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    await db.delete(content)
    await db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@router.get("/reports")
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    teacher_id = str(current_user.id)

    # Aggregate counts from teacher's own data
    classroom_count = (
        await db.execute(
            select(func.count(TeacherClassroom.id)).where(
                TeacherClassroom.teacher_user_id == teacher_id
            )
        )
    ).scalar_one()

    student_count = (
        await db.execute(
            select(func.count(TeacherClassroomStudent.id)).where(
                TeacherClassroomStudent.classroom_id.in_(
                    select(TeacherClassroom.id).where(
                        TeacherClassroom.teacher_user_id == teacher_id
                    )
                )
            )
        )
    ).scalar_one()

    assignment_count = (
        await db.execute(
            select(func.count(TeacherAssignment.id)).where(
                TeacherAssignment.teacher_user_id == teacher_id
            )
        )
    ).scalar_one()

    now = datetime.utcnow().isoformat()
    reports = [
        {
            "id": "rpt-classes",
            "baslik": "Sınıf Özeti",
            "aciklama": f"Toplam {classroom_count} sınıf",
            "tarih": now,
            "tip": "sinif",
            "format": "pdf",
            "boyut": "—",
        },
        {
            "id": "rpt-students",
            "baslik": "Öğrenci Listesi",
            "aciklama": f"Toplam {student_count} öğrenci",
            "tarih": now,
            "tip": "ogrenci",
            "format": "excel",
            "boyut": "—",
        },
        {
            "id": "rpt-assignments",
            "baslik": "Ödev Raporu",
            "aciklama": f"Toplam {assignment_count} ödev",
            "tarih": now,
            "tip": "genel",
            "format": "pdf",
            "boyut": "—",
        },
    ]
    return {"data": {"reports": reports}}
