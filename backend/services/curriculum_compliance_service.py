"""
Mufredat Uyumluluk Servisi
Veritabani islemleri ve is mantigi

SQLAlchemy ORM ile async veritabani islemleri.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.curriculum import (
    CurriculumAlignment,
    CurriculumUpdateRequest,
    ExamType,
    GradeLevel,
    LearningOutcome,
    MEBCurriculumStandard,
    OSYMStandard,
    SubjectType,
)
from models.curriculum_db import (
    CurriculumAlignmentDB,
    CurriculumUpdateRequestDB,
    LearningOutcomeDB,
    MEBCurriculumStandardDB,
    OSYMStandardDB,
)

logger = logging.getLogger(__name__)


class CurriculumComplianceService:
    """
    Mufredat Uyumluluk Veritabani Servisi

    MEB ve OSYM standartlari icin CRUD islemleri.
    SQLAlchemy ORM ile async veritabani islemleri.
    """

    def __init__(self, session: AsyncSession | None = None):
        """
        Initialize service with async session.

        Args:
            session: SQLAlchemy AsyncSession instance
        """
        self.session = session

    # MEB Standartlari Veritabani Islemleri

    async def save_meb_standard(self, standard: MEBCurriculumStandard) -> bool:
        """MEB standardini veritabanina kaydet (upsert)."""
        try:
            if not self.session:
                logger.warning("Veritabani baglantisi yok, mock kayit yapiliyor")
                return True

            # Convert Pydantic model to ORM model
            db_standard = MEBCurriculumStandardDB(
                id=standard.id,
                subject=standard.subject.value,
                grade_level=standard.grade_level.value,
                unit_name=standard.unit_name,
                topic_name=standard.topic_name,
                learning_outcomes=standard.learning_outcomes,
                key_concepts=standard.key_concepts,
                skills=standard.skills,
                duration_hours=standard.duration_hours,
                prerequisites=standard.prerequisites,
                assessment_criteria=standard.assessment_criteria,
                created_at=standard.created_at,
                updated_at=standard.updated_at,
                is_active=standard.is_active,
            )

            # Use merge for upsert behavior
            await self.session.merge(db_standard)
            await self.session.commit()

            logger.info(f"MEB standardi kaydedildi: {standard.id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"MEB standardi kaydetme hatasi: {e}")
            return False

    async def get_meb_standards_by_subject(
        self, subject: SubjectType, grade_level: GradeLevel | None = None
    ) -> list[MEBCurriculumStandard]:
        """Derse gore MEB standartlarini getir."""
        try:
            if not self.session:
                return self._get_mock_meb_standards(subject, grade_level)

            # Build query using ORM
            stmt = (
                select(MEBCurriculumStandardDB)
                .where(MEBCurriculumStandardDB.subject == subject.value)
                .where(MEBCurriculumStandardDB.is_active == True)  # noqa: E712
            )

            if grade_level:
                stmt = stmt.where(
                    MEBCurriculumStandardDB.grade_level == grade_level.value
                )

            stmt = stmt.order_by(
                MEBCurriculumStandardDB.unit_name,
                MEBCurriculumStandardDB.topic_name,
            )

            result = await self.session.execute(stmt)
            rows = result.scalars().all()

            standards = []
            for row in rows:
                standard = MEBCurriculumStandard(
                    id=row.id,
                    subject=SubjectType(row.subject),
                    grade_level=GradeLevel(row.grade_level),
                    unit_name=row.unit_name,
                    topic_name=row.topic_name,
                    learning_outcomes=row.learning_outcomes or [],
                    key_concepts=row.key_concepts or [],
                    skills=row.skills or [],
                    duration_hours=row.duration_hours,
                    prerequisites=row.prerequisites or [],
                    assessment_criteria=row.assessment_criteria or [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    is_active=row.is_active,
                )
                standards.append(standard)

            return standards

        except Exception as e:
            logger.error(f"MEB standartlari getirme hatasi: {e}")
            return []

    async def get_all_meb_standards(self) -> list[MEBCurriculumStandard]:
        """Tum MEB standartlarini getir."""
        try:
            if not self.session:
                all_standards = []
                for subject in SubjectType:
                    standards = self._get_mock_meb_standards(subject)
                    all_standards.extend(standards)
                return all_standards

            stmt = (
                select(MEBCurriculumStandardDB)
                .where(MEBCurriculumStandardDB.is_active == True)  # noqa: E712
                .order_by(
                    MEBCurriculumStandardDB.subject,
                    MEBCurriculumStandardDB.grade_level,
                    MEBCurriculumStandardDB.unit_name,
                    MEBCurriculumStandardDB.topic_name,
                )
            )

            result = await self.session.execute(stmt)
            rows = result.scalars().all()

            standards = []
            for row in rows:
                standard = MEBCurriculumStandard(
                    id=row.id,
                    subject=SubjectType(row.subject),
                    grade_level=GradeLevel(row.grade_level),
                    unit_name=row.unit_name,
                    topic_name=row.topic_name,
                    learning_outcomes=row.learning_outcomes or [],
                    key_concepts=row.key_concepts or [],
                    skills=row.skills or [],
                    duration_hours=row.duration_hours,
                    prerequisites=row.prerequisites or [],
                    assessment_criteria=row.assessment_criteria or [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    is_active=row.is_active,
                )
                standards.append(standard)

            return standards

        except Exception as e:
            logger.error(f"Tum MEB standartlari getirme hatasi: {e}")
            return []

    async def update_meb_standard(self, standard: MEBCurriculumStandard) -> bool:
        """MEB standardini guncelle."""
        try:
            if not self.session:
                logger.warning("Veritabani baglantisi yok, mock guncelleme yapiliyor")
                return True

            stmt = (
                update(MEBCurriculumStandardDB)
                .where(MEBCurriculumStandardDB.id == standard.id)
                .values(
                    topic_name=standard.topic_name,
                    learning_outcomes=standard.learning_outcomes,
                    key_concepts=standard.key_concepts,
                    skills=standard.skills,
                    duration_hours=standard.duration_hours,
                    prerequisites=standard.prerequisites,
                    assessment_criteria=standard.assessment_criteria,
                    updated_at=datetime.now(),
                )
            )

            await self.session.execute(stmt)
            await self.session.commit()

            logger.info(f"MEB standardi guncellendi: {standard.id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"MEB standardi guncelleme hatasi: {e}")
            return False

    # OSYM Standartlari Veritabani Islemleri

    async def save_osym_standard(self, standard: OSYMStandard) -> bool:
        """OSYM standardini veritabanina kaydet (upsert)."""
        try:
            if not self.session:
                logger.warning("Veritabani baglantisi yok, mock kayit yapiliyor")
                return True

            db_standard = OSYMStandardDB(
                id=standard.id,
                exam_type=standard.exam_type.value,
                subject=standard.subject.value,
                topic_code=standard.topic_code,
                topic_name=standard.topic_name,
                priority_level=standard.priority_level,
                question_count_range=standard.question_count_range,
                difficulty_distribution=standard.difficulty_distribution,
                cognitive_levels=standard.cognitive_levels,
                exam_frequency=standard.exam_frequency,
                last_exam_appearance=standard.last_exam_appearance,
                created_at=standard.created_at,
                updated_at=standard.updated_at,
                is_active=standard.is_active,
            )

            await self.session.merge(db_standard)
            await self.session.commit()

            logger.info(f"OSYM standardi kaydedildi: {standard.id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"OSYM standardi kaydetme hatasi: {e}")
            return False

    async def get_all_osym_standards(self) -> list[OSYMStandard]:
        """Tum OSYM standartlarini getir."""
        try:
            if not self.session:
                return self._get_mock_osym_standards()

            stmt = (
                select(OSYMStandardDB)
                .where(OSYMStandardDB.is_active == True)  # noqa: E712
                .order_by(
                    OSYMStandardDB.exam_type,
                    OSYMStandardDB.subject,
                    OSYMStandardDB.priority_level,
                )
            )

            result = await self.session.execute(stmt)
            rows = result.scalars().all()

            standards = []
            for row in rows:
                standard = OSYMStandard(
                    id=row.id,
                    exam_type=ExamType(row.exam_type),
                    subject=SubjectType(row.subject),
                    topic_code=row.topic_code,
                    topic_name=row.topic_name,
                    priority_level=row.priority_level,
                    question_count_range=row.question_count_range or {},
                    difficulty_distribution=row.difficulty_distribution or {},
                    cognitive_levels=row.cognitive_levels or [],
                    exam_frequency=row.exam_frequency,
                    last_exam_appearance=row.last_exam_appearance,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    is_active=row.is_active,
                )
                standards.append(standard)

            return standards

        except Exception as e:
            logger.error(f"Tum OSYM standartlari getirme hatasi: {e}")
            return []

    async def update_osym_standard(self, standard: OSYMStandard) -> bool:
        """OSYM standardini guncelle."""
        try:
            if not self.session:
                logger.warning("Veritabani baglantisi yok, mock guncelleme yapiliyor")
                return True

            stmt = (
                update(OSYMStandardDB)
                .where(OSYMStandardDB.id == standard.id)
                .values(
                    topic_name=standard.topic_name,
                    priority_level=standard.priority_level,
                    question_count_range=standard.question_count_range,
                    difficulty_distribution=standard.difficulty_distribution,
                    cognitive_levels=standard.cognitive_levels,
                    exam_frequency=standard.exam_frequency,
                    last_exam_appearance=standard.last_exam_appearance,
                    updated_at=datetime.now(),
                )
            )

            await self.session.execute(stmt)
            await self.session.commit()

            logger.info(f"OSYM standardi guncellendi: {standard.id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"OSYM standardi guncelleme hatasi: {e}")
            return False

    # Ogrenme Kazanimlari Islemleri

    async def get_learning_outcomes_by_standard(
        self, meb_standard_id: str
    ) -> list[LearningOutcome]:
        """MEB standardina gore ogrenme kazanimlarini getir."""
        try:
            if not self.session:
                return self._get_mock_learning_outcomes(meb_standard_id)

            stmt = (
                select(LearningOutcomeDB)
                .where(LearningOutcomeDB.meb_standard_id == meb_standard_id)
                .order_by(LearningOutcomeDB.code)
            )

            result = await self.session.execute(stmt)
            rows = result.scalars().all()

            outcomes = []
            for row in rows:
                outcome = LearningOutcome(
                    id=row.id,
                    code=row.code,
                    description=row.description,
                    subject=SubjectType(row.subject),
                    grade_level=GradeLevel(row.grade_level),
                    cognitive_level=row.cognitive_level,
                    bloom_taxonomy=row.bloom_taxonomy,
                    meb_standard_id=row.meb_standard_id,
                    assessment_methods=row.assessment_methods or [],
                    sample_activities=row.sample_activities or [],
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                outcomes.append(outcome)

            return outcomes

        except Exception as e:
            logger.error(f"Ogrenme kazanimlari getirme hatasi: {e}")
            return []

    # Uyumluluk Eslestirmeleri Islemleri

    async def get_all_curriculum_alignments(self) -> list[CurriculumAlignment]:
        """Tum uyumluluk eslestirmelerini getir."""
        try:
            if not self.session:
                return []

            stmt = select(CurriculumAlignmentDB).order_by(
                CurriculumAlignmentDB.created_at.desc()
            )

            result = await self.session.execute(stmt)
            rows = result.scalars().all()

            alignments = []
            for row in rows:
                alignment = CurriculumAlignment(
                    id=row.id,
                    meb_standard_id=row.meb_standard_id,
                    osym_standard_id=row.osym_standard_id,
                    alignment_score=row.alignment_score,
                    alignment_type=row.alignment_type,
                    gaps_identified=row.gaps_identified or [],
                    recommendations=row.recommendations or [],
                    verified_by=row.verified_by,
                    verification_date=row.verification_date,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                alignments.append(alignment)

            return alignments

        except Exception as e:
            logger.error(f"Uyumluluk eslestirmeleri getirme hatasi: {e}")
            return []

    # Soru Istatistikleri Islemleri

    async def get_question_statistics(self, topic_id: str) -> dict[str, Any]:
        """Konuya gore soru istatistiklerini getir."""
        try:
            if not self.session:
                return {
                    "total": 1250,
                    "osym_format": 1100,
                    "meb_aligned": 1200,
                    "difficulty_dist": {"kolay": 400, "orta": 600, "zor": 250},
                }

            # Import Question model locally to avoid circular imports
            from models.content_db import Question

            stmt = select(
                func.count(Question.id).label("total"),
                func.count(
                    func.nullif(Question.is_active == True, False)  # noqa: E712
                ).label("active_count"),
            ).where(Question.topic == topic_id)

            result = await self.session.execute(stmt)
            row = result.one_or_none()

            if row:
                return {
                    "total": row.total or 0,
                    "osym_format": 0,
                    "meb_aligned": 0,
                    "difficulty_dist": {},
                }

            return {
                "total": 0,
                "osym_format": 0,
                "meb_aligned": 0,
                "difficulty_dist": {},
            }

        except Exception as e:
            logger.error(f"Soru istatistikleri getirme hatasi: {e}")
            return {}

    # Mufredat Guncelleme Islemleri

    async def save_curriculum_update_request(
        self, update_request: CurriculumUpdateRequest
    ) -> bool:
        """Mufredat guncelleme talebini kaydet."""
        try:
            if not self.session:
                logger.warning("Veritabani baglantisi yok, mock kayit yapiliyor")
                return True

            db_request = CurriculumUpdateRequestDB(
                id=update_request.id,
                update_type=update_request.update_type,
                subject=update_request.subject.value,
                affected_standards=update_request.affected_standards,
                changes_description=update_request.changes_description,
                source_document=update_request.source_document,
                requested_by=update_request.requested_by,
                requested_at=update_request.requested_at,
                status=update_request.status,
                reviewed_by=update_request.reviewed_by,
                reviewed_at=update_request.reviewed_at,
                implementation_date=update_request.implementation_date,
                notes=update_request.notes,
            )

            self.session.add(db_request)
            await self.session.commit()

            logger.info(f"Mufredat guncelleme talebi kaydedildi: {update_request.id}")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Mufredat guncelleme talebi kaydetme hatasi: {e}")
            return False

    # Mock Data Metodlari (Test icin)

    def _get_mock_meb_standards(
        self, subject: SubjectType, grade_level: GradeLevel | None = None
    ) -> list[MEBCurriculumStandard]:
        """Test icin mock MEB standartlari."""
        mock_standards = []

        if subject == SubjectType.MATEMATIK:
            topics = [
                "Sayilar ve Islemler",
                "Cebir",
                "Geometri",
                "Veri Isleme",
                "Olasilik",
            ]
        elif subject == SubjectType.TURKCE:
            topics = ["Okuma", "Yazma", "Dil Bilgisi", "Edebiyat", "Soz Varligi"]
        else:
            topics = [f"{subject.value} Konu 1", f"{subject.value} Konu 2"]

        for i, topic in enumerate(topics):
            standard = MEBCurriculumStandard(
                id=f"meb_{subject.value}_{i+1}",
                subject=subject,
                grade_level=grade_level or GradeLevel.GRADE_12,
                unit_name=f"Unite {i+1}",
                topic_name=topic,
                learning_outcomes=[
                    f"{topic} ile ilgili temel kavramlari bilir",
                    f"{topic} problemlerini cozer",
                ],
                key_concepts=[f"Kavram {i+1}", f"Kavram {i+2}"],
                skills=["Analiz", "Sentez", "Degerlendirme"],
                duration_hours=20,
                prerequisites=[f"On kosul {i}"] if i > 0 else [],
                assessment_criteria=["Yazili sinav", "Performans gorevi"],
            )
            mock_standards.append(standard)

        return mock_standards

    def _get_mock_osym_standards(self) -> list[OSYMStandard]:
        """Test icin mock OSYM standartlari."""
        mock_standards = []

        subjects = [
            SubjectType.MATEMATIK,
            SubjectType.TURKCE,
            SubjectType.FEN_BILIMLERI,
        ]
        exam_types = [ExamType.TYT, ExamType.AYT]

        for exam_type in exam_types:
            for i, subject in enumerate(subjects):
                standard = OSYMStandard(
                    id=f"osym_{exam_type.value}_{subject.value}_{i+1}",
                    exam_type=exam_type,
                    subject=subject,
                    topic_code=f"{subject.value.upper()[:3]}{i+1:02d}",
                    topic_name=f"{subject.value} Temel Konular",
                    priority_level=i + 1,
                    question_count_range={"min": 5, "max": 15},
                    difficulty_distribution={"kolay": 0.3, "orta": 0.5, "zor": 0.2},
                    cognitive_levels=["bilgi", "kavrama", "uygulama"],
                    exam_frequency=0.8,
                    last_exam_appearance="2024",
                )
                mock_standards.append(standard)

        return mock_standards

    def _get_mock_learning_outcomes(
        self, meb_standard_id: str
    ) -> list[LearningOutcome]:
        """Test icin mock ogrenme kazanimlari."""
        mock_outcomes = []

        for i in range(3):
            outcome = LearningOutcome(
                id=f"outcome_{meb_standard_id}_{i+1}",
                code=f"K{i+1}",
                description=f"Ogrenci {i+1}. kazanimi gerceklestirir",
                subject=SubjectType.MATEMATIK,
                grade_level=GradeLevel.GRADE_12,
                cognitive_level="uygulama",
                bloom_taxonomy="C3",
                meb_standard_id=meb_standard_id,
                assessment_methods=["Yazili sinav", "Proje"],
                sample_activities=["Etkinlik 1", "Etkinlik 2"],
            )
            mock_outcomes.append(outcome)

        return mock_outcomes
