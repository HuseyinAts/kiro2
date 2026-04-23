"""
Soru Üretim Servisi
Otomatik soru üretimi için veritabanı işlemleri ve iş mantığı
"""

import json
import logging
from datetime import datetime
from typing import Any

from models.curriculum import ExamType, GradeLevel, SubjectType
from models.question_generation import (
    CognitiveLevel,
    DifficultyLevel,
    GeneratedQuestion,
    QuestionGenerationRequest,
    QuestionTemplate,
    QuestionType,
    QuestionValidationResult,
)

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    """
    Soru Üretim Veritabanı Servisi

    Otomatik soru üretimi için CRUD işlemleri ve veri yönetimi
    """

    def __init__(self, database_connection=None):
        self.db = database_connection

    # Üretilen Sorular İşlemleri

    async def save_generated_question(self, question: GeneratedQuestion) -> bool:
        """Üretilen soruyu veritabanına kaydet"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock kayıt yapılıyor")
                return True

            query = """
            INSERT INTO generated_questions (
                id, subject, topic_id, topic_name, subtopic,
                question_type, question_text, options, correct_answer, explanation,
                difficulty_level, cognitive_level, estimated_time_seconds,
                osym_compliance_score, meb_compliance_score, quality_score,
                readability_score, uniqueness_score, generation_method,
                generation_parameters, source_materials, is_validated,
                validation_errors, is_approved, approved_by, created_at,
                updated_at, last_used_at, meb_standard_id, learning_outcome_ids
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                question_text = EXCLUDED.question_text,
                options = EXCLUDED.options,
                explanation = EXCLUDED.explanation,
                osym_compliance_score = EXCLUDED.osym_compliance_score,
                meb_compliance_score = EXCLUDED.meb_compliance_score,
                quality_score = EXCLUDED.quality_score,
                is_validated = EXCLUDED.is_validated,
                is_approved = EXCLUDED.is_approved,
                updated_at = EXCLUDED.updated_at
            """

            values = (
                question.id,
                question.subject.value,
                question.topic_id,
                question.topic_name,
                question.subtopic,
                question.question_type.value,
                question.question_text,
                json.dumps(question.options),
                str(question.correct_answer),
                question.explanation,
                question.difficulty_level.value,
                question.cognitive_level.value,
                question.estimated_time_seconds,
                question.osym_compliance_score,
                question.meb_compliance_score,
                question.quality_score,
                question.readability_score,
                question.uniqueness_score,
                question.generation_method,
                json.dumps(question.generation_parameters),
                json.dumps(question.source_materials),
                question.is_validated,
                json.dumps(question.validation_errors),
                question.is_approved,
                question.approved_by,
                question.created_at,
                question.updated_at,
                question.last_used_at,
                question.meb_standard_id,
                json.dumps(question.learning_outcome_ids),
            )

            await self.db.execute(query, values)
            logger.info(f"Üretilen soru kaydedildi: {question.id}")
            return True

        except Exception as e:
            logger.error(f"Soru kaydetme hatası: {e}")
            return False

    async def get_questions_by_topic(
        self,
        topic_id: str,
        limit: int | None = None,
        validated_only: bool = False,
        approved_only: bool = False,
    ) -> list[GeneratedQuestion]:
        """Konuya göre üretilen soruları getir"""
        try:
            if not self.db:
                # Mock data döndür
                return self._get_mock_questions_by_topic(topic_id, limit or 10)

            query = """
            SELECT * FROM generated_questions 
            WHERE topic_id = %s
            """
            params = [topic_id]

            if validated_only:
                query += " AND is_validated = true"

            if approved_only:
                query += " AND is_approved = true"

            query += " ORDER BY created_at DESC"

            if limit:
                query += f" LIMIT {limit}"

            rows = await self.db.fetch_all(query, params)

            questions = []
            for row in rows:
                question = self._row_to_generated_question(row)
                if question:
                    questions.append(question)

            return questions

        except Exception as e:
            logger.error(f"Konuya göre sorular getirme hatası: {e}")
            return []

    async def get_question_by_id(self, question_id: str) -> GeneratedQuestion | None:
        """ID'ye göre soru getir"""
        try:
            if not self.db:
                # Mock data döndür
                return self._get_mock_question_by_id(question_id)

            query = "SELECT * FROM generated_questions WHERE id = %s"
            row = await self.db.fetch_one(query, [question_id])

            if row:
                return self._row_to_generated_question(row)

            return None

        except Exception as e:
            logger.error(f"Soru getirme hatası: {e}")
            return None

    async def update_question_validation(
        self, question_id: str, validation_result: QuestionValidationResult
    ) -> bool:
        """Soru doğrulama sonucunu güncelle"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock güncelleme yapılıyor")
                return True

            query = """
            UPDATE generated_questions SET
                is_validated = %s,
                osym_compliance_score = %s,
                meb_compliance_score = %s,
                quality_score = %s,
                readability_score = %s,
                validation_errors = %s,
                updated_at = %s
            WHERE id = %s
            """

            values = (
                validation_result.is_valid,
                validation_result.osym_compliance_score,
                validation_result.meb_compliance_score,
                validation_result.quality_score,
                validation_result.readability_score,
                json.dumps(validation_result.errors),
                datetime.now(),
                question_id,
            )

            await self.db.execute(query, values)
            logger.info(f"Soru doğrulama güncellendi: {question_id}")
            return True

        except Exception as e:
            logger.error(f"Soru doğrulama güncelleme hatası: {e}")
            return False

    async def approve_question(self, question_id: str, approved_by: str) -> bool:
        """Soruyu onayla"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock onay yapılıyor")
                return True

            query = """
            UPDATE generated_questions SET
                is_approved = true,
                approved_by = %s,
                updated_at = %s
            WHERE id = %s AND is_validated = true
            """

            values = (approved_by, datetime.now(), question_id)
            result = await self.db.execute(query, values)

            if result.rowcount > 0:
                logger.info(f"Soru onaylandı: {question_id}")
                return True
            logger.warning(
                f"Soru onaylanamadı (doğrulanmamış olabilir): {question_id}"
            )
            return False

        except Exception as e:
            logger.error(f"Soru onaylama hatası: {e}")
            return False

    # Soru Üretim Talepleri İşlemleri

    async def save_generation_request(self, request: QuestionGenerationRequest) -> bool:
        """Soru üretim talebini kaydet"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock kayıt yapılıyor")
                return True

            query = """
            INSERT INTO question_generation_requests (
                id, subject, topic_id, exam_type, grade_level,
                question_count, question_types, difficulty_distribution,
                cognitive_distribution, min_quality_score, min_osym_compliance,
                min_meb_compliance, generation_method, use_existing_templates,
                allow_duplicates, requested_by, priority, deadline, status, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            values = (
                request.id,
                request.subject.value,
                request.topic_id,
                request.exam_type.value,
                request.grade_level.value if request.grade_level else None,
                request.question_count,
                json.dumps([qt.value for qt in request.question_types]),
                json.dumps(
                    {k.value: v for k, v in request.difficulty_distribution.items()}
                ),
                json.dumps(
                    {k.value: v for k, v in request.cognitive_distribution.items()}
                ),
                request.min_quality_score,
                request.min_osym_compliance,
                request.min_meb_compliance,
                request.generation_method,
                request.use_existing_templates,
                request.allow_duplicates,
                request.requested_by,
                request.priority,
                request.deadline,
                request.status,
                request.created_at,
            )

            await self.db.execute(query, values)
            logger.info(f"Soru üretim talebi kaydedildi: {request.id}")
            return True

        except Exception as e:
            logger.error(f"Üretim talebi kaydetme hatası: {e}")
            return False

    async def update_generation_request_status(
        self, request_id: str, status: str, result_data: dict[str, Any] | None = None
    ) -> bool:
        """Üretim talebi durumunu güncelle"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock güncelleme yapılıyor")
                return True

            query = """
            UPDATE question_generation_requests SET
                status = %s,
                result_data = %s,
                updated_at = %s
            WHERE id = %s
            """

            values = (
                status,
                json.dumps(result_data) if result_data else None,
                datetime.now(),
                request_id,
            )

            await self.db.execute(query, values)
            logger.info(f"Üretim talebi durumu güncellendi: {request_id} -> {status}")
            return True

        except Exception as e:
            logger.error(f"Üretim talebi güncelleme hatası: {e}")
            return False

    async def get_pending_generation_requests(self) -> list[QuestionGenerationRequest]:
        """Bekleyen üretim taleplerini getir"""
        try:
            if not self.db:
                # Mock data döndür
                return []

            query = """
            SELECT * FROM question_generation_requests 
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            """

            rows = await self.db.fetch_all(query)

            requests = []
            for row in rows:
                request = self._row_to_generation_request(row)
                if request:
                    requests.append(request)

            return requests

        except Exception as e:
            logger.error(f"Bekleyen talepler getirme hatası: {e}")
            return []

    # Soru Şablonları İşlemleri

    async def save_question_template(self, template: QuestionTemplate) -> bool:
        """Soru şablonunu kaydet"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock kayıt yapılıyor")
                return True

            query = """
            INSERT INTO question_templates (
                id, name, description, subject, topic_pattern,
                question_template, options_template, explanation_template,
                template_variables, difficulty_level, cognitive_level,
                usage_count, success_rate, created_by, is_active, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                question_template = EXCLUDED.question_template,
                options_template = EXCLUDED.options_template,
                explanation_template = EXCLUDED.explanation_template,
                template_variables = EXCLUDED.template_variables,
                usage_count = EXCLUDED.usage_count,
                success_rate = EXCLUDED.success_rate,
                updated_at = EXCLUDED.updated_at
            """

            values = (
                template.id,
                template.name,
                template.description,
                template.subject.value,
                template.topic_pattern,
                template.question_template,
                json.dumps(template.options_template),
                template.explanation_template,
                json.dumps(template.template_variables),
                template.difficulty_level.value,
                template.cognitive_level.value,
                template.usage_count,
                template.success_rate,
                template.created_by,
                template.is_active,
                template.created_at,
                template.updated_at,
            )

            await self.db.execute(query, values)
            logger.info(f"Soru şablonu kaydedildi: {template.id}")
            return True

        except Exception as e:
            logger.error(f"Şablon kaydetme hatası: {e}")
            return False

    async def get_templates_by_criteria(
        self,
        subject: SubjectType,
        question_type: QuestionType | None = None,
        difficulty_level: DifficultyLevel | None = None,
        cognitive_level: CognitiveLevel | None = None,
    ) -> list[QuestionTemplate]:
        """Kriterlere göre şablonları getir"""
        try:
            if not self.db:
                # Mock data döndür
                return self._get_mock_templates(subject)

            query = """
            SELECT * FROM question_templates 
            WHERE subject = %s AND is_active = true
            """
            params = [subject.value]

            if difficulty_level:
                query += " AND difficulty_level = %s"
                params.append(difficulty_level.value)

            if cognitive_level:
                query += " AND cognitive_level = %s"
                params.append(cognitive_level.value)

            query += " ORDER BY success_rate DESC, usage_count ASC"

            rows = await self.db.fetch_all(query, params)

            templates = []
            for row in rows:
                template = self._row_to_question_template(row)
                if template:
                    templates.append(template)

            return templates

        except Exception as e:
            logger.error(f"Şablon getirme hatası: {e}")
            return []

    async def update_template_usage(self, template_id: str, success: bool) -> bool:
        """Şablon kullanım istatistiklerini güncelle"""
        try:
            if not self.db:
                logger.warning("Veritabanı bağlantısı yok, mock güncelleme yapılıyor")
                return True

            # Önce mevcut değerleri getir
            query = (
                "SELECT usage_count, success_rate FROM question_templates WHERE id = %s"
            )
            row = await self.db.fetch_one(query, [template_id])

            if not row:
                return False

            current_usage = row["usage_count"]
            current_success_rate = row["success_rate"]

            # Yeni değerleri hesapla
            new_usage = current_usage + 1
            if current_usage == 0:
                new_success_rate = 1.0 if success else 0.0
            else:
                total_successes = current_success_rate * current_usage
                if success:
                    total_successes += 1
                new_success_rate = total_successes / new_usage

            # Güncelle
            update_query = """
            UPDATE question_templates SET
                usage_count = %s,
                success_rate = %s,
                updated_at = %s
            WHERE id = %s
            """

            await self.db.execute(
                update_query, [new_usage, new_success_rate, datetime.now(), template_id]
            )
            logger.info(f"Şablon kullanım istatistikleri güncellendi: {template_id}")
            return True

        except Exception as e:
            logger.error(f"Şablon istatistik güncelleme hatası: {e}")
            return False

    # İstatistik ve Analiz İşlemleri

    async def get_question_statistics_by_topic(self, topic_id: str) -> dict[str, Any]:
        """Konuya göre soru istatistiklerini getir"""
        try:
            if not self.db:
                # Mock data döndür
                return {
                    "total_questions": 850,
                    "validated_questions": 720,
                    "approved_questions": 650,
                    "average_quality_score": 0.78,
                    "average_osym_compliance": 0.82,
                    "average_meb_compliance": 0.85,
                    "difficulty_distribution": {"kolay": 255, "orta": 425, "zor": 170},
                    "cognitive_distribution": {
                        "bilgi": 170,
                        "kavrama": 255,
                        "uygulama": 255,
                        "analiz": 128,
                        "sentez": 42,
                    },
                    "type_distribution": {
                        "multiple_choice": 680,
                        "true_false": 85,
                        "fill_in_blank": 85,
                    },
                }

            query = """
            SELECT 
                COUNT(*) as total_questions,
                COUNT(CASE WHEN is_validated = true THEN 1 END) as validated_questions,
                COUNT(CASE WHEN is_approved = true THEN 1 END) as approved_questions,
                AVG(quality_score) as avg_quality,
                AVG(osym_compliance_score) as avg_osym,
                AVG(meb_compliance_score) as avg_meb,
                difficulty_level,
                cognitive_level,
                question_type,
                COUNT(*) as count_by_category
            FROM generated_questions 
            WHERE topic_id = %s
            GROUP BY difficulty_level, cognitive_level, question_type
            """

            rows = await self.db.fetch_all(query, [topic_id])

            # İstatistikleri organize et
            stats = {
                "total_questions": 0,
                "validated_questions": 0,
                "approved_questions": 0,
                "average_quality_score": 0.0,
                "average_osym_compliance": 0.0,
                "average_meb_compliance": 0.0,
                "difficulty_distribution": {},
                "cognitive_distribution": {},
                "type_distribution": {},
            }

            if rows:
                # Toplam değerleri hesapla
                stats["total_questions"] = sum(row["count_by_category"] for row in rows)
                stats["validated_questions"] = sum(
                    row["validated_questions"] for row in rows
                )
                stats["approved_questions"] = sum(
                    row["approved_questions"] for row in rows
                )

                # Ortalama skorları hesapla
                if stats["total_questions"] > 0:
                    stats["average_quality_score"] = sum(
                        row["avg_quality"] or 0 for row in rows
                    ) / len(rows)
                    stats["average_osym_compliance"] = sum(
                        row["avg_osym"] or 0 for row in rows
                    ) / len(rows)
                    stats["average_meb_compliance"] = sum(
                        row["avg_meb"] or 0 for row in rows
                    ) / len(rows)

                # Dağılımları hesapla
                for row in rows:
                    if row["difficulty_level"]:
                        stats["difficulty_distribution"][row["difficulty_level"]] = row[
                            "count_by_category"
                        ]
                    if row["cognitive_level"]:
                        stats["cognitive_distribution"][row["cognitive_level"]] = row[
                            "count_by_category"
                        ]
                    if row["question_type"]:
                        stats["type_distribution"][row["question_type"]] = row[
                            "count_by_category"
                        ]

            return stats

        except Exception as e:
            logger.error(f"Soru istatistikleri getirme hatası: {e}")
            return {}

    async def get_generation_statistics(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Üretim istatistiklerini getir"""
        try:
            if not self.db:
                # Mock data döndür
                return {
                    "total_requests": 45,
                    "completed_requests": 38,
                    "failed_requests": 7,
                    "total_questions_generated": 3420,
                    "total_questions_validated": 2890,
                    "total_questions_approved": 2650,
                    "average_generation_time": 125.5,
                    "success_rate": 0.844,
                    "average_quality_score": 0.78,
                }

            # Tarih filtresi
            date_filter = ""
            params = []

            if start_date:
                date_filter += " AND created_at >= %s"
                params.append(start_date)

            if end_date:
                date_filter += " AND created_at <= %s"
                params.append(end_date)

            # Talep istatistikleri
            request_query = f"""
            SELECT 
                COUNT(*) as total_requests,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_requests,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_requests
            FROM question_generation_requests 
            WHERE 1=1 {date_filter}
            """

            request_stats = await self.db.fetch_one(request_query, params)

            # Soru istatistikleri
            question_query = f"""
            SELECT 
                COUNT(*) as total_questions,
                COUNT(CASE WHEN is_validated = true THEN 1 END) as validated_questions,
                COUNT(CASE WHEN is_approved = true THEN 1 END) as approved_questions,
                AVG(quality_score) as avg_quality
            FROM generated_questions 
            WHERE 1=1 {date_filter}
            """

            question_stats = await self.db.fetch_one(question_query, params)

            # Sonuçları birleştir
            stats = {
                "total_requests": request_stats["total_requests"]
                if request_stats
                else 0,
                "completed_requests": request_stats["completed_requests"]
                if request_stats
                else 0,
                "failed_requests": request_stats["failed_requests"]
                if request_stats
                else 0,
                "total_questions_generated": question_stats["total_questions"]
                if question_stats
                else 0,
                "total_questions_validated": question_stats["validated_questions"]
                if question_stats
                else 0,
                "total_questions_approved": question_stats["approved_questions"]
                if question_stats
                else 0,
                "average_generation_time": 0.0,  # Bu hesaplama için ek tablo gerekli
                "success_rate": 0.0,
                "average_quality_score": question_stats["avg_quality"]
                if question_stats
                else 0.0,
            }

            # Başarı oranını hesapla
            if stats["total_requests"] > 0:
                stats["success_rate"] = (
                    stats["completed_requests"] / stats["total_requests"]
                )

            return stats

        except Exception as e:
            logger.error(f"Üretim istatistikleri getirme hatası: {e}")
            return {}

    # Yardımcı Metodlar

    def _row_to_generated_question(
        self, row: dict[str, Any]
    ) -> GeneratedQuestion | None:
        """Veritabanı satırını GeneratedQuestion objesine çevir"""
        try:
            from models.question_generation import OSYMQuestionFormat

            # ÖSYM format objesi oluştur
            osym_format = OSYMQuestionFormat(
                question_number=1,
                question_text=row["question_text"],
                options=json.loads(row["options"]) if row["options"] else [],
                correct_answer=row["correct_answer"],
                explanation=row["explanation"],
            )

            question = GeneratedQuestion(
                id=row["id"],
                subject=SubjectType(row["subject"]),
                topic_id=row["topic_id"],
                topic_name=row["topic_name"],
                subtopic=row.get("subtopic"),
                question_type=QuestionType(row["question_type"]),
                question_text=row["question_text"],
                options=json.loads(row["options"]) if row["options"] else [],
                correct_answer=row["correct_answer"],
                explanation=row["explanation"],
                difficulty_level=DifficultyLevel(row["difficulty_level"]),
                cognitive_level=CognitiveLevel(row["cognitive_level"]),
                estimated_time_seconds=row.get("estimated_time_seconds", 120),
                osym_format=osym_format,
                osym_compliance_score=row.get("osym_compliance_score", 0.0),
                meb_compliance_score=row.get("meb_compliance_score", 0.0),
                quality_score=row.get("quality_score", 0.0),
                readability_score=row.get("readability_score", 0.0),
                uniqueness_score=row.get("uniqueness_score", 0.0),
                generation_method=row.get("generation_method", "unknown"),
                generation_parameters=json.loads(row["generation_parameters"])
                if row.get("generation_parameters")
                else {},
                source_materials=json.loads(row["source_materials"])
                if row.get("source_materials")
                else [],
                is_validated=row.get("is_validated", False),
                validation_errors=json.loads(row["validation_errors"])
                if row.get("validation_errors")
                else [],
                is_approved=row.get("is_approved", False),
                approved_by=row.get("approved_by"),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                last_used_at=row.get("last_used_at"),
                meb_standard_id=row.get("meb_standard_id"),
                learning_outcome_ids=json.loads(row["learning_outcome_ids"])
                if row.get("learning_outcome_ids")
                else [],
            )

            return question

        except Exception as e:
            logger.error(f"Soru objesi oluşturma hatası: {e}")
            return None

    def _row_to_generation_request(
        self, row: dict[str, Any]
    ) -> QuestionGenerationRequest | None:
        """Veritabanı satırını QuestionGenerationRequest objesine çevir"""
        try:
            request = QuestionGenerationRequest(
                id=row["id"],
                subject=SubjectType(row["subject"]),
                topic_id=row["topic_id"],
                exam_type=ExamType(row["exam_type"]),
                grade_level=GradeLevel(row["grade_level"])
                if row.get("grade_level")
                else None,
                question_count=row["question_count"],
                question_types=[
                    QuestionType(qt) for qt in json.loads(row["question_types"])
                ],
                difficulty_distribution={
                    DifficultyLevel(k): v
                    for k, v in json.loads(row["difficulty_distribution"]).items()
                },
                cognitive_distribution={
                    CognitiveLevel(k): v
                    for k, v in json.loads(row["cognitive_distribution"]).items()
                },
                min_quality_score=row.get("min_quality_score", 0.7),
                min_osym_compliance=row.get("min_osym_compliance", 0.8),
                min_meb_compliance=row.get("min_meb_compliance", 0.8),
                generation_method=row.get("generation_method", "ai_assisted"),
                use_existing_templates=row.get("use_existing_templates", True),
                allow_duplicates=row.get("allow_duplicates", False),
                requested_by=row["requested_by"],
                priority=row.get("priority", "normal"),
                deadline=row.get("deadline"),
                status=row["status"],
                created_at=row["created_at"],
            )

            return request

        except Exception as e:
            logger.error(f"Üretim talebi objesi oluşturma hatası: {e}")
            return None

    def _row_to_question_template(
        self, row: dict[str, Any]
    ) -> QuestionTemplate | None:
        """Veritabanı satırını QuestionTemplate objesine çevir"""
        try:
            template = QuestionTemplate(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                subject=SubjectType(row["subject"]),
                topic_pattern=row["topic_pattern"],
                question_template=row["question_template"],
                options_template=json.loads(row["options_template"])
                if row["options_template"]
                else [],
                explanation_template=row["explanation_template"],
                template_variables=json.loads(row["template_variables"])
                if row["template_variables"]
                else {},
                difficulty_level=DifficultyLevel(row["difficulty_level"]),
                cognitive_level=CognitiveLevel(row["cognitive_level"]),
                usage_count=row.get("usage_count", 0),
                success_rate=row.get("success_rate", 0.0),
                created_by=row["created_by"],
                is_active=row.get("is_active", True),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

            return template

        except Exception as e:
            logger.error(f"Şablon objesi oluşturma hatası: {e}")
            return None

    # Mock Data Metodları (Test için)

    def _get_mock_questions_by_topic(
        self, topic_id: str, limit: int
    ) -> list[GeneratedQuestion]:
        """Test için mock sorular"""
        from models.question_generation import OSYMQuestionFormat

        mock_questions = []

        for i in range(min(limit, 5)):
            osym_format = OSYMQuestionFormat(
                question_number=i + 1,
                question_text=f"Bu {topic_id} konusu ile ilgili örnek soru {i+1}?",
                options=[
                    f"Seçenek A {i+1}",
                    f"Seçenek B {i+1}",
                    f"Seçenek C {i+1}",
                    f"Seçenek D {i+1}",
                ],
                correct_answer="A",
                explanation=f"Bu sorunun cevabı A'dır çünkü {i+1}. açıklama.",
            )

            question = GeneratedQuestion(
                id=f"mock_question_{topic_id}_{i+1}",
                subject=SubjectType.MATEMATIK,
                topic_id=topic_id,
                topic_name=f"Mock Konu {topic_id}",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text=osym_format.question_text,
                options=osym_format.options,
                correct_answer=osym_format.correct_answer,
                explanation=osym_format.explanation,
                difficulty_level=DifficultyLevel.ORTA,
                cognitive_level=CognitiveLevel.KAVRAMA,
                osym_format=osym_format,
                osym_compliance_score=0.85,
                meb_compliance_score=0.80,
                quality_score=0.75,
                generation_method="mock",
                is_validated=True,
                is_approved=i < 3,  # İlk 3'ü onaylı
            )

            mock_questions.append(question)

        return mock_questions

    def _get_mock_question_by_id(self, question_id: str) -> GeneratedQuestion | None:
        """Test için mock soru"""
        mock_questions = self._get_mock_questions_by_topic("mock_topic", 1)
        if mock_questions:
            question = mock_questions[0]
            question.id = question_id
            return question
        return None

    def _get_mock_templates(self, subject: SubjectType) -> list[QuestionTemplate]:
        """Test için mock şablonlar"""
        mock_templates = []

        for i in range(3):
            template = QuestionTemplate(
                id=f"mock_template_{subject.value}_{i+1}",
                name=f"{subject.value} Şablon {i+1}",
                description=f"{subject.value} dersi için örnek şablon {i+1}",
                subject=subject,
                topic_pattern=f"{subject.value}_*",
                question_template="{{konu}} ile ilgili {{soru_tipi}} sorusu: {{soru_metni}}?",
                options_template=[
                    "{{dogru_cevap}}",
                    "{{celdirici_1}}",
                    "{{celdirici_2}}",
                    "{{celdirici_3}}",
                ],
                explanation_template="Bu sorunun cevabı {{dogru_cevap}}'dır çünkü {{aciklama}}.",
                template_variables={
                    "konu": "string",
                    "soru_tipi": "string",
                    "soru_metni": "string",
                    "dogru_cevap": "string",
                    "celdirici_1": "string",
                    "celdirici_2": "string",
                    "celdirici_3": "string",
                    "aciklama": "string",
                },
                difficulty_level=DifficultyLevel.ORTA,
                cognitive_level=CognitiveLevel.KAVRAMA,
                usage_count=i * 10,
                success_rate=0.8 - (i * 0.1),
                created_by="system",
            )

            mock_templates.append(template)

        return mock_templates
