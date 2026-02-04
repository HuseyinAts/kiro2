"""
Müfredat Uyumluluk Servisi
Veritabanı işlemleri ve iş mantığı
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

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

logger = logging.getLogger(__name__)


class CurriculumComplianceService:
    """
    Müfredat Uyumluluk Veritabanı Servisi

    MEB ve ÖSYM standartları için CRUD işlemleri
    """

    def __init__(self, database_connection=None):
        self.db = database_connection

    # MEB Standartları Veritabanı İşlemleri

    async def save_meb_standard(self, standard: MEBCurriculumStandard) -> bool:
        """MEB standardını veritabanına kaydet"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock kayıt yapılıyor")
                return True

            query = """
            INSERT INTO meb_curriculum_standards (
                id, subject, grade_level, unit_name, topic_name,
                learning_outcomes, key_concepts, skills, duration_hours,
                prerequisites, assessment_criteria, created_at, updated_at, is_active
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                topic_name = EXCLUDED.topic_name,
                learning_outcomes = EXCLUDED.learning_outcomes,
                updated_at = EXCLUDED.updated_at
            """

            values = (
                standard.id,
                standard.subject.value,
                standard.grade_level.value,
                standard.unit_name,
                standard.topic_name,
                json.dumps(standard.learning_outcomes),
                json.dumps(standard.key_concepts),
                json.dumps(standard.skills),
                standard.duration_hours,
                json.dumps(standard.prerequisites),
                json.dumps(standard.assessment_criteria),
                standard.created_at,
                standard.updated_at,
                standard.is_active,
            )

            await self.db.execute(query, values)
            logger.info(f"MEB standardı kaydedildi: {standard.id}")
            return True

        except Exception as e:
            logger.error(f"MEB standardı kaydetme hatası: {e}")
            return False

    async def get_meb_standards_by_subject(
        self, subject: SubjectType, grade_level: Optional[GradeLevel] = None
    ) -> List[MEBCurriculumStandard]:
        """Derse göre MEB standartlarını getir"""
        try:
            if not self.db:
                # Mock data döndür
                return self._get_mock_meb_standards(subject, grade_level)

            query = """
            SELECT * FROM meb_curriculum_standards 
            WHERE subject = %s AND is_active = true
            """
            params = [subject.value]

            if grade_level:
                query += " AND grade_level = %s"
                params.append(grade_level.value)

            query += " ORDER BY unit_name, topic_name"

            rows = await self.db.fetch_all(query, params)

            standards = []
            for row in rows:
                standard = MEBCurriculumStandard(
                    id=row["id"],
                    subject=SubjectType(row["subject"]),
                    grade_level=GradeLevel(row["grade_level"]),
                    unit_name=row["unit_name"],
                    topic_name=row["topic_name"],
                    learning_outcomes=json.loads(row["learning_outcomes"] or "[]"),
                    key_concepts=json.loads(row["key_concepts"] or "[]"),
                    skills=json.loads(row["skills"] or "[]"),
                    duration_hours=row["duration_hours"],
                    prerequisites=json.loads(row["prerequisites"] or "[]"),
                    assessment_criteria=json.loads(row["assessment_criteria"] or "[]"),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    is_active=row["is_active"],
                )
                standards.append(standard)

            return standards

        except Exception as e:
            logger.error(f"MEB standartları getirme hatası: {e}")
            return []

    async def get_all_meb_standards(self) -> List[MEBCurriculumStandard]:
        """Tüm MEB standartlarını getir"""
        try:
            if not self.db:
                # Mock data döndür
                all_standards = []
                for subject in SubjectType:
                    standards = self._get_mock_meb_standards(subject)
                    all_standards.extend(standards)
                return all_standards

            query = """
            SELECT * FROM meb_curriculum_standards 
            WHERE is_active = true
            ORDER BY subject, grade_level, unit_name, topic_name
            """

            rows = await self.db.fetch_all(query)

            standards = []
            for row in rows:
                standard = MEBCurriculumStandard(
                    id=row["id"],
                    subject=SubjectType(row["subject"]),
                    grade_level=GradeLevel(row["grade_level"]),
                    unit_name=row["unit_name"],
                    topic_name=row["topic_name"],
                    learning_outcomes=json.loads(row["learning_outcomes"] or "[]"),
                    key_concepts=json.loads(row["key_concepts"] or "[]"),
                    skills=json.loads(row["skills"] or "[]"),
                    duration_hours=row["duration_hours"],
                    prerequisites=json.loads(row["prerequisites"] or "[]"),
                    assessment_criteria=json.loads(row["assessment_criteria"] or "[]"),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    is_active=row["is_active"],
                )
                standards.append(standard)

            return standards

        except Exception as e:
            logger.error(f"Tüm MEB standartları getirme hatası: {e}")
            return []

    async def update_meb_standard(self, standard: MEBCurriculumStandard) -> bool:
        """MEB standardını güncelle"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock güncelleme yapılıyor")
                return True

            query = """
            UPDATE meb_curriculum_standards SET
                topic_name = %s,
                learning_outcomes = %s,
                key_concepts = %s,
                skills = %s,
                duration_hours = %s,
                prerequisites = %s,
                assessment_criteria = %s,
                updated_at = %s
            WHERE id = %s
            """

            values = (
                standard.topic_name,
                json.dumps(standard.learning_outcomes),
                json.dumps(standard.key_concepts),
                json.dumps(standard.skills),
                standard.duration_hours,
                json.dumps(standard.prerequisites),
                json.dumps(standard.assessment_criteria),
                datetime.now(),
                standard.id,
            )

            await self.db.execute(query, values)
            logger.info(f"MEB standardı güncellendi: {standard.id}")
            return True

        except Exception as e:
            logger.error(f"MEB standardı güncelleme hatası: {e}")
            return False

    # ÖSYM Standartları Veritabanı İşlemleri

    async def save_osym_standard(self, standard: OSYMStandard) -> bool:
        """ÖSYM standardını veritabanına kaydet"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock kayıt yapılıyor")
                return True

            query = """
            INSERT INTO osym_standards (
                id, exam_type, subject, topic_code, topic_name,
                priority_level, question_count_range, difficulty_distribution,
                cognitive_levels, exam_frequency, last_exam_appearance,
                created_at, updated_at, is_active
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                topic_name = EXCLUDED.topic_name,
                priority_level = EXCLUDED.priority_level,
                exam_frequency = EXCLUDED.exam_frequency,
                updated_at = EXCLUDED.updated_at
            """

            values = (
                standard.id,
                standard.exam_type.value,
                standard.subject.value,
                standard.topic_code,
                standard.topic_name,
                standard.priority_level,
                json.dumps(standard.question_count_range),
                json.dumps(standard.difficulty_distribution),
                json.dumps(standard.cognitive_levels),
                standard.exam_frequency,
                standard.last_exam_appearance,
                standard.created_at,
                standard.updated_at,
                standard.is_active,
            )

            await self.db.execute(query, values)
            logger.info(f"ÖSYM standardı kaydedildi: {standard.id}")
            return True

        except Exception as e:
            logger.error(f"ÖSYM standardı kaydetme hatası: {e}")
            return False

    async def get_all_osym_standards(self) -> List[OSYMStandard]:
        """Tüm ÖSYM standartlarını getir"""
        try:
            if not self.db:
                # Mock data döndür
                return self._get_mock_osym_standards()

            query = """
            SELECT * FROM osym_standards 
            WHERE is_active = true
            ORDER BY exam_type, subject, priority_level
            """

            rows = await self.db.fetch_all(query)

            standards = []
            for row in rows:
                standard = OSYMStandard(
                    id=row["id"],
                    exam_type=ExamType(row["exam_type"]),
                    subject=SubjectType(row["subject"]),
                    topic_code=row["topic_code"],
                    topic_name=row["topic_name"],
                    priority_level=row["priority_level"],
                    question_count_range=json.loads(
                        row["question_count_range"] or "{}"
                    ),
                    difficulty_distribution=json.loads(
                        row["difficulty_distribution"] or "{}"
                    ),
                    cognitive_levels=json.loads(row["cognitive_levels"] or "[]"),
                    exam_frequency=row["exam_frequency"],
                    last_exam_appearance=row["last_exam_appearance"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    is_active=row["is_active"],
                )
                standards.append(standard)

            return standards

        except Exception as e:
            logger.error(f"Tüm ÖSYM standartları getirme hatası: {e}")
            return []

    async def update_osym_standard(self, standard: OSYMStandard) -> bool:
        """ÖSYM standardını güncelle"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock güncelleme yapılıyor")
                return True

            query = """
            UPDATE osym_standards SET
                topic_name = %s,
                priority_level = %s,
                question_count_range = %s,
                difficulty_distribution = %s,
                cognitive_levels = %s,
                exam_frequency = %s,
                last_exam_appearance = %s,
                updated_at = %s
            WHERE id = %s
            """

            values = (
                standard.topic_name,
                standard.priority_level,
                json.dumps(standard.question_count_range),
                json.dumps(standard.difficulty_distribution),
                json.dumps(standard.cognitive_levels),
                standard.exam_frequency,
                standard.last_exam_appearance,
                datetime.now(),
                standard.id,
            )

            await self.db.execute(query, values)
            logger.info(f"ÖSYM standardı güncellendi: {standard.id}")
            return True

        except Exception as e:
            logger.error(f"ÖSYM standardı güncelleme hatası: {e}")
            return False

    # Öğrenme Kazanımları İşlemleri

    async def get_learning_outcomes_by_standard(
        self, meb_standard_id: str
    ) -> List[LearningOutcome]:
        """MEB standardına göre öğrenme kazanımlarını getir"""
        try:
            if not self.db:
                # Mock data döndür
                return self._get_mock_learning_outcomes(meb_standard_id)

            query = """
            SELECT * FROM learning_outcomes 
            WHERE meb_standard_id = %s
            ORDER BY code
            """

            rows = await self.db.fetch_all(query, [meb_standard_id])

            outcomes = []
            for row in rows:
                outcome = LearningOutcome(
                    id=row["id"],
                    code=row["code"],
                    description=row["description"],
                    subject=SubjectType(row["subject"]),
                    grade_level=GradeLevel(row["grade_level"]),
                    cognitive_level=row["cognitive_level"],
                    bloom_taxonomy=row["bloom_taxonomy"],
                    meb_standard_id=row["meb_standard_id"],
                    assessment_methods=json.loads(row["assessment_methods"] or "[]"),
                    sample_activities=json.loads(row["sample_activities"] or "[]"),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                outcomes.append(outcome)

            return outcomes

        except Exception as e:
            logger.error(f"Öğrenme kazanımları getirme hatası: {e}")
            return []

    # Uyumluluk Eşleştirmeleri İşlemleri

    async def get_all_curriculum_alignments(self) -> List[CurriculumAlignment]:
        """Tüm uyumluluk eşleştirmelerini getir"""
        try:
            if not self.db:
                # Mock data döndür
                return []

            query = """
            SELECT * FROM curriculum_alignments 
            ORDER BY created_at DESC
            """

            rows = await self.db.fetch_all(query)

            alignments = []
            for row in rows:
                alignment = CurriculumAlignment(
                    id=row["id"],
                    meb_standard_id=row["meb_standard_id"],
                    osym_standard_id=row["osym_standard_id"],
                    alignment_score=row["alignment_score"],
                    alignment_type=row["alignment_type"],
                    gaps_identified=json.loads(row["gaps_identified"] or "[]"),
                    recommendations=json.loads(row["recommendations"] or "[]"),
                    verified_by=row["verified_by"],
                    verification_date=row["verification_date"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                alignments.append(alignment)

            return alignments

        except Exception as e:
            logger.error(f"Uyumluluk eşleştirmeleri getirme hatası: {e}")
            return []

    # Soru İstatistikleri İşlemleri

    async def get_question_statistics(self, topic_id: str) -> Dict[str, Any]:
        """Konuya göre soru istatistiklerini getir"""
        try:
            if not self.db:
                # Mock data döndür
                return {
                    "total": 1250,
                    "osym_format": 1100,
                    "meb_aligned": 1200,
                    "difficulty_dist": {"kolay": 400, "orta": 600, "zor": 250},
                }

            query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_osym_format = true THEN 1 END) as osym_format,
                COUNT(CASE WHEN is_meb_aligned = true THEN 1 END) as meb_aligned,
                COUNT(CASE WHEN difficulty_level = 'kolay' THEN 1 END) as easy,
                COUNT(CASE WHEN difficulty_level = 'orta' THEN 1 END) as medium,
                COUNT(CASE WHEN difficulty_level = 'zor' THEN 1 END) as hard
            FROM questions 
            WHERE topic_id = %s AND is_active = true
            """

            row = await self.db.fetch_one(query, [topic_id])

            if row:
                return {
                    "total": row["total"],
                    "osym_format": row["osym_format"],
                    "meb_aligned": row["meb_aligned"],
                    "difficulty_dist": {
                        "kolay": row["easy"],
                        "orta": row["medium"],
                        "zor": row["hard"],
                    },
                }

            return {
                "total": 0,
                "osym_format": 0,
                "meb_aligned": 0,
                "difficulty_dist": {},
            }

        except Exception as e:
            logger.error(f"Soru istatistikleri getirme hatası: {e}")
            return {}

    # Müfredat Güncelleme İşlemleri

    async def save_curriculum_update_request(
        self, update_request: CurriculumUpdateRequest
    ) -> bool:
        """Müfredat güncelleme talebini kaydet"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock kayıt yapılıyor")
                return True

            query = """
            INSERT INTO curriculum_update_requests (
                id, update_type, subject, affected_standards,
                changes_description, source_document, requested_by,
                requested_at, status, reviewed_by, reviewed_at,
                implementation_date, notes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            values = (
                update_request.id,
                update_request.update_type,
                update_request.subject.value,
                json.dumps(update_request.affected_standards),
                update_request.changes_description,
                update_request.source_document,
                update_request.requested_by,
                update_request.requested_at,
                update_request.status,
                update_request.reviewed_by,
                update_request.reviewed_at,
                update_request.implementation_date,
                update_request.notes,
            )

            await self.db.execute(query, values)
            logger.info(f"Müfredat güncelleme talebi kaydedildi: {update_request.id}")
            return True

        except Exception as e:
            logger.error(f"Müfredat güncelleme talebi kaydetme hatası: {e}")
            return False

    # Mock Data Metodları (Test için)

    def _get_mock_meb_standards(
        self, subject: SubjectType, grade_level: Optional[GradeLevel] = None
    ) -> List[MEBCurriculumStandard]:
        """Test için mock MEB standartları"""
        mock_standards = []

        if subject == SubjectType.MATEMATIK:
            topics = [
                "Sayılar ve İşlemler",
                "Cebir",
                "Geometri",
                "Veri İşleme",
                "Olasılık",
            ]
        elif subject == SubjectType.TURKCE:
            topics = ["Okuma", "Yazma", "Dil Bilgisi", "Edebiyat", "Söz Varlığı"]
        else:
            topics = [f"{subject.value} Konu 1", f"{subject.value} Konu 2"]

        for i, topic in enumerate(topics):
            standard = MEBCurriculumStandard(
                id=f"meb_{subject.value}_{i+1}",
                subject=subject,
                grade_level=grade_level or GradeLevel.GRADE_12,
                unit_name=f"Ünite {i+1}",
                topic_name=topic,
                learning_outcomes=[
                    f"{topic} ile ilgili temel kavramları bilir",
                    f"{topic} problemlerini çözer",
                ],
                key_concepts=[f"Kavram {i+1}", f"Kavram {i+2}"],
                skills=["Analiz", "Sentez", "Değerlendirme"],
                duration_hours=20,
                prerequisites=[f"Ön koşul {i}"] if i > 0 else [],
                assessment_criteria=["Yazılı sınav", "Performans görevi"],
            )
            mock_standards.append(standard)

        return mock_standards

    def _get_mock_osym_standards(self) -> List[OSYMStandard]:
        """Test için mock ÖSYM standartları"""
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
    ) -> List[LearningOutcome]:
        """Test için mock öğrenme kazanımları"""
        mock_outcomes = []

        for i in range(3):
            outcome = LearningOutcome(
                id=f"outcome_{meb_standard_id}_{i+1}",
                code=f"K{i+1}",
                description=f"Öğrenci {i+1}. kazanımı gerçekleştirir",
                subject=SubjectType.MATEMATIK,
                grade_level=GradeLevel.GRADE_12,
                cognitive_level="uygulama",
                bloom_taxonomy="C3",
                meb_standard_id=meb_standard_id,
                assessment_methods=["Yazılı sınav", "Proje"],
                sample_activities=["Etkinlik 1", "Etkinlik 2"],
            )
            mock_outcomes.append(outcome)

        return mock_outcomes
