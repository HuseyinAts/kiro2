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

import contextlib
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import User, get_current_user, get_db
from models.database import User as DBUser
from models.teacher_classroom import (
    TeacherAssignment,
    TeacherClassroom,
    TeacherClassroomStudent,
    TeacherContent,
    TeacherExamConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/teacher", tags=["teacher-classroom"])

# 29 Tem 2026 ÖLÇÜMÜ: bu router'da HİÇ rol kapısı yoktu — `get_current_user`
# yalnız kimlik doğruluyor. Yani herhangi bir öğrenci `POST /teacher/classes`
# ile kendini "öğretmen" ilan edip sınıf açabiliyordu. Roster yazma uçları
# BAŞKA İNSANLARIN ad/soyad/e-postasını döndürdüğü için o boşluk buraya
# taşınmadı. Mevcut uçlara dokunulmadı (ayrı iş) — ama yenilerinin kapısı var.
#
# `core.auth_dependencies.require_role` KULLANILMADI: o bağımlılık isteği
# ham `Request`ten yeniden doğruluyor, yani bu router'a İKİNCİ bir kimlik
# yolu sokuyor. Aynı uçta iki auth yolu hem gereksiz hem de kapının
# davranışını sürülebilir olmaktan çıkarıyor (rol kapısı testi gerçek JWT
# üretmeden yazılamıyordu). Kapı burada, tek yol üzerinde ve açık.
_STAFF_ROLLERI = {"teacher", "ogretmen", "öğretmen", "admin", "super_admin"}


async def _require_staff(current_user: User = Depends(get_current_user)) -> None:
    rol = str(getattr(current_user.role, "value", current_user.role)).lower()
    if rol not in _STAFF_ROLLERI:
        raise HTTPException(
            status_code=403, detail="Bu işlem için öğretmen yetkisi gerekir"
        )


_STAFF_ONLY = Depends(_require_staff)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class ClassCreate(BaseModel):
    """Canonical English field names; Turkish aliases retained for legacy callers."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., alias="sinif_adi")
    grade_level: str = Field(..., alias="seviye")
    subject_area: str = Field(..., alias="ders")


class StudentAdd(BaseModel):
    """Sınıfa öğrenci ekleme — e-posta ile."""

    email: str = Field(..., max_length=254)


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
    _staff: None = _STAFF_ONLY,
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
    """Öğretmenin sınıflarındaki öğrenciler — GERÇEK kimlikle.

    29 Tem 2026'ya kadar `ad`/`soyad`/`email` sabit boş string dönüyordu
    ("student service integration later"), yani öğretmen kimliksiz satırlar
    görüyordu. Uç 200 döndüğü için "çalışıyor" sayılmıştı.
    """
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
    if not rows:
        return {"data": {"students": []}}

    # Kimlikler AYRI ve tek sorguda çekiliyor (join yok): sorgu sayısı satır
    # sayısıyla büyümüyor ve her sorgu tek varlık döndürdüğü için akış
    # taklit edilebilir bir oturumla test edilebiliyor.
    profiller = await _kullanici_profilleri({r.student_user_id for r in rows}, db)

    data = [
        {
            "id": str(r.id),
            "student_user_id": r.student_user_id,
            "sinif": classroom_names.get(str(r.classroom_id), ""),
            "joined_at": _fmt_dt(r.joined_at),
            **profiller.get(
                str(r.student_user_id), {"ad": "", "soyad": "", "email": ""}
            ),
            # Performans alanları ayrı iş (#5 pano): burada UYDURULMUYOR.
            "ortalama": 0,
            "tamamlanan_sinav": 0,
            "toplam_sinav": 0,
        }
        for r in rows
    ]
    return {"data": {"students": data}}


async def _kullanici_profilleri(
    user_ids: set[str], db: AsyncSession
) -> dict[str, dict[str, str]]:
    """id -> {ad, soyad, email}. Bulunamayan id sözlükte yer almaz."""
    if not user_ids:
        return {}
    result = await db.execute(select(DBUser).where(DBUser.id.in_(list(user_ids))))
    return {
        str(u.id): {
            "ad": u.first_name or "",
            "soyad": u.last_name or "",
            "email": u.email or "",
        }
        for u in result.scalars().all()
    }


async def _sahip_olunan_sinif(
    class_id: str, teacher_user_id: str, db: AsyncSession
) -> TeacherClassroom:
    """Sınıfı getir ve ÖĞRETMENE AİT olduğunu doğrula.

    Sahiplik kontrolü bilerek burada, açık bir `if` olarak duruyor —
    `WHERE`e gömülmüş bir kontrol okunamaz ve sorguyu taklit eden hiçbir
    testle doğrulanamaz. Sahip değilse 404 (403 değil): sınıf id'sinin var
    olup olmadığını sızdırmamak için.
    """
    try:
        anahtar = UUID(str(class_id))
    except (ValueError, AttributeError) as exc:
        raise HTTPException(status_code=404, detail="Sınıf bulunamadı") from exc

    result = await db.execute(
        select(TeacherClassroom).where(TeacherClassroom.id == anahtar)
    )
    classroom = result.scalar_one_or_none()
    if classroom is None or str(classroom.teacher_user_id) != str(teacher_user_id):
        raise HTTPException(status_code=404, detail="Sınıf bulunamadı")
    return classroom


@router.post("/classes/{class_id}/students", status_code=200)
async def add_student_to_class(
    class_id: str,
    body: StudentAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _staff: None = _STAFF_ONLY,
) -> dict[str, Any]:
    """Sınıfa e-postayla öğrenci ekle.

    Kapılar: personel rolü (`_STAFF_ONLY`) + sınıf sahipliği + hedefin
    ÖĞRENCİ olması. Sonuncusu olmadan öğretmen bir admin'in e-postasını
    yazıp adını soyadını listede okuyabilirdi.

    NOT (bilinen, kabul edilmiş): kayıtlı/kayıtsız e-posta ayrımı bir
    numaralandırma kanalıdır. Uç personele kapalı ve `_check_rate_limit`
    kapsamına alınabilir; öğretmenin ekleyeceği adresi zaten bilmesi
    beklendiği için ayrım korunuyor — aksi hâlde yanlış yazılan e-posta
    sessizce kaybolurdu.
    """
    classroom = await _sahip_olunan_sinif(class_id, str(current_user.id), db)

    eposta = (body.email or "").strip()
    ogrenci_sonuc = await db.execute(select(DBUser).where(DBUser.email == eposta))
    ogrenci = ogrenci_sonuc.scalar_one_or_none()
    if ogrenci is None:
        raise HTTPException(
            status_code=404, detail="Bu e-postayla kayıtlı bir öğrenci yok"
        )

    rol = getattr(ogrenci.role, "value", ogrenci.role)
    if str(rol).lower() not in {"student", "ogrenci", "öğrenci"}:
        raise HTTPException(
            status_code=400, detail="Yalnızca öğrenci hesapları sınıfa eklenebilir"
        )

    mevcut_sonuc = await db.execute(
        select(TeacherClassroomStudent).where(
            TeacherClassroomStudent.classroom_id == classroom.id,
            TeacherClassroomStudent.student_user_id == str(ogrenci.id),
        )
    )
    mevcut = mevcut_sonuc.scalar_one_or_none()
    if mevcut is not None:
        # Idempotent: tekrar eklemek satır çoğaltmaz, liste ve sayaçlar bozulmaz.
        return {"success": True, "data": _uyelik_govdesi(mevcut, classroom, ogrenci)}

    uyelik = TeacherClassroomStudent(
        classroom_id=classroom.id, student_user_id=str(ogrenci.id)
    )
    db.add(uyelik)
    await db.commit()
    await db.refresh(uyelik)
    logger.info(
        "roster: sınıf=%s öğrenci eklendi (öğretmen=%s)", classroom.id, current_user.id
    )
    return {"success": True, "data": _uyelik_govdesi(uyelik, classroom, ogrenci)}


@router.delete("/classes/{class_id}/students/{student_user_id}")
async def remove_student_from_class(
    class_id: str,
    student_user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _staff: None = _STAFF_ONLY,
) -> dict[str, Any]:
    """Öğrenciyi sınıftan çıkar. Yalnız kendi sınıfından."""
    classroom = await _sahip_olunan_sinif(class_id, str(current_user.id), db)

    result = await db.execute(
        select(TeacherClassroomStudent).where(
            TeacherClassroomStudent.classroom_id == classroom.id,
            TeacherClassroomStudent.student_user_id == str(student_user_id),
        )
    )
    uyelik = result.scalar_one_or_none()
    if uyelik is None:
        raise HTTPException(status_code=404, detail="Öğrenci bu sınıfta değil")

    await db.delete(uyelik)
    await db.commit()
    logger.info(
        "roster: sınıf=%s öğrenci çıkarıldı (öğretmen=%s)",
        classroom.id,
        current_user.id,
    )
    return {"success": True}


def _uyelik_govdesi(
    uyelik: TeacherClassroomStudent, classroom: TeacherClassroom, ogrenci: Any
) -> dict[str, Any]:
    return {
        "id": str(uyelik.id),
        "student_user_id": str(ogrenci.id),
        "ad": ogrenci.first_name or "",
        "soyad": ogrenci.last_name or "",
        "email": ogrenci.email or "",
        "sinif": classroom.sinif_adi,
        "joined_at": _fmt_dt(uyelik.joined_at),
    }


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
    _staff: None = _STAFF_ONLY,
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
    _staff: None = _STAFF_ONLY,
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
    _staff: None = _STAFF_ONLY,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    teslim_tarihi: datetime | None = None
    if body.teslim_tarihi:
        # SIM105 (önceden vardı): sessiz `except: pass` yerine niyeti açık
        # yazan suppress. Davranış aynı — bozuk tarih girdisi teslim tarihini
        # boş bırakır, isteği reddetmez.
        with contextlib.suppress(ValueError):
            teslim_tarihi = datetime.fromisoformat(body.teslim_tarihi)

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
    _staff: None = _STAFF_ONLY,
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
    _staff: None = _STAFF_ONLY,
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
    _staff: None = _STAFF_ONLY,
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

    # DTZ003 (önceden vardı): naive `utcnow()` yerine aware `now(UTC)`.
    # `tzinfo` düşürülüyor ki rapor metninin biçimi AYNI kalsın.
    now = datetime.now(UTC).replace(tzinfo=None).isoformat()
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
