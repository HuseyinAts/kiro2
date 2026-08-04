"""
Teacher Classroom Models

Öğretmen sınıf yönetimi için DB modelleri.
Mevcut teacher_pool.py (marketplace) ile ilgisiz.
Bu modül classroom management içindir.
"""

from datetime import datetime
from uuid6 import uuid7
from uuid import uuid4

from sqlalchemy import String, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .database import Base


class TeacherClassroom(Base):
    """Öğretmenin oluşturduğu sınıf."""

    __tablename__ = "teacher_classrooms"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_user_id = Column(String, nullable=False, index=True)
    sinif_adi = Column(String(100), nullable=False)
    seviye = Column(String(10), nullable=False)  # "9", "10", "11", "12"
    ders = Column(String(50), nullable=False)  # "matematik", "fizik", ...
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TeacherClassroomStudent(Base):
    """Sınıf-öğrenci ilişkisi."""

    __tablename__ = "teacher_classroom_students"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    classroom_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("teacher_classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_user_id = Column(String, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TeacherExamConfig(Base):
    """Öğretmenin oluşturduğu sınav konfigürasyonu."""

    __tablename__ = "teacher_exam_configs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_user_id = Column(String, nullable=False, index=True)
    baslik = Column(String(200), nullable=False)
    aciklama = Column(Text, nullable=True)
    sinav_tipi = Column(String(10), nullable=False)  # TYT / AYT / YDT
    soru_sayisi = Column(Integer, nullable=False, default=20)
    sure_dakika = Column(Integer, nullable=False, default=60)
    durum = Column(
        String(20), nullable=False, default="taslak"
    )  # taslak/aktif/tamamlandi
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TeacherAssignment(Base):
    """Öğretmenin verdiği ödev."""

    __tablename__ = "teacher_assignments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_user_id = Column(String, nullable=False, index=True)
    baslik = Column(String(200), nullable=False)
    aciklama = Column(Text, nullable=True)
    sinif = Column(String(50), nullable=True)
    teslim_tarihi = Column(DateTime, nullable=True)
    durum = Column(
        String(20), nullable=False, default="aktif"
    )  # aktif/tamamlandi/iptal
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TeacherContent(Base):
    """Öğretmenin paylaştığı içerik (video, döküman, sunum vb.)."""

    __tablename__ = "teacher_contents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    teacher_user_id = Column(String, nullable=False, index=True)
    baslik = Column(String(200), nullable=False)
    aciklama = Column(Text, nullable=True)
    tip = Column(
        String(20), nullable=False, default="diger"
    )  # video/dokuman/sunum/quiz/diger
    konu = Column(String(100), nullable=True)
    sinif = Column(String(50), nullable=True)
    goruntulenme = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
