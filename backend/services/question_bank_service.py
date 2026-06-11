"""
Soru Bankası Servisi
Teknofest 2025 Eğitim Eylemci Platformu

Task 70 Implementation:
- Question CRUD operations
- Topic hierarchy management
- IRT parameter updates
- Dynamic difficulty adjustment
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

# Note: IRTValidationError is raised by validators - re-exported for external use
from core.irt_validators import IRTValidationError as IRTValidationError
from core.irt_validators import (
    validate_irt_difficulty,
    validate_irt_discrimination,
    validate_irt_guessing,
    validate_irt_upper_asymptote,
)
from models.question_bank import (
    IRTCalibrationHistory,
    QuestionBankItem,
    QuestionDifficultyLevel,
    QuestionTag,
    QuestionTagAssociation,
    TopicHierarchy,
    calculate_irt_based_difficulty,
    should_update_difficulty,
)
from core.resilience import db_retry


class QuestionBankService:
    """Soru bankası yönetim servisi"""

    def __init__(self, db: Session):
        self.db = db

    # ========================================================================
    # TASK 70.1: Question CRUD Operations
    # ========================================================================

    @db_retry
    async def create_question(
        self, question_data: dict[str, Any], created_by: str | None = None
    ) -> QuestionBankItem:
        """
        Yeni soru oluştur

        Args:
            question_data: Soru verileri
            created_by: Oluşturan kullanıcı ID

        Returns:
            QuestionBankItem: Oluşturulan soru
        """
        question = QuestionBankItem(
            **question_data, created_by=created_by, created_at=datetime.now()
        )

        # IRT bazlı zorluk hesapla
        question.irt_based_difficulty = calculate_irt_based_difficulty(
            question.irt_difficulty
        )

        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)

        return question

    async def get_question(self, question_id: str) -> QuestionBankItem | None:
        """Soru detayını getir"""
        result = await self.db.execute(
            select(QuestionBankItem)
            .options(
                joinedload(QuestionBankItem.primary_topic),
                selectinload(QuestionBankItem.tag_associations),
                selectinload(QuestionBankItem.calibration_history),
            )
            .where(QuestionBankItem.id == question_id)
        )
        return result.scalar_one_or_none()

    @db_retry
    async def update_question(
        self, question_id: str, update_data: dict[str, Any]
    ) -> QuestionBankItem | None:
        """Soru güncelle"""
        question = await self.get_question(question_id)
        if not question:
            return None

        for key, value in update_data.items():
            setattr(question, key, value)

        question.updated_at = datetime.now()

        await self.db.commit()
        await self.db.refresh(question)

        return question

    @db_retry
    async def delete_question(self, question_id: str) -> bool:
        """Soru sil (soft delete)"""
        question = await self.get_question(question_id)
        if not question:
            return False

        question.is_active = False
        question.updated_at = datetime.now()

        await self.db.commit()
        return True

    # ========================================================================
    # TASK 70.2: Topic Hierarchy Management
    # ========================================================================

    @db_retry
    async def create_topic(
        self,
        code: str,
        name_tr: str,
        level: int,
        parent_id: str | None = None,
        **kwargs,
    ) -> TopicHierarchy:
        """
        Yeni konu oluştur

        Args:
            code: Konu kodu (örn: MAT.GEO.UCG)
            name_tr: Türkçe konu adı
            level: Hiyerarşi seviyesi (1-5)
            parent_id: Üst konu ID

        Returns:
            TopicHierarchy: Oluşturulan konu
        """
        topic = TopicHierarchy(
            code=code, name_tr=name_tr, level=level, parent_id=parent_id, **kwargs
        )

        self.db.add(topic)
        await self.db.commit()
        await self.db.refresh(topic)

        return topic

    async def get_topic_hierarchy(
        self, parent_id: str | None = None
    ) -> list[TopicHierarchy]:
        """
        Konu hiyerarşisini getir

        Args:
            parent_id: Üst konu ID (None ise kök konular)

        Returns:
            List[TopicHierarchy]: Konu listesi
        """
        query = select(TopicHierarchy).where(TopicHierarchy.is_active.is_(True))

        if parent_id:
            query = query.where(TopicHierarchy.parent_id == parent_id)
        else:
            query = query.where(TopicHierarchy.parent_id.is_(None))

        query = query.order_by(TopicHierarchy.code)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_topic_path(self, topic_id: str) -> list[TopicHierarchy]:
        """
        Konunun tam yolunu getir (kökten başlayarak)

        PERFORMANCE FIX: Recursive CTE kullanarak sadece gerekli topic'leri fetch eder.
        Önceki: Tüm topic'leri memory'e yükle (O(n) memory, 1000+ row)
        Şimdi: Sadece path'teki topic'ler (O(depth) memory, max 5 row)

        Args:
            topic_id: Konu ID

        Returns:
            List[TopicHierarchy]: Kök'ten hedefe kadar tüm konular
        """
        from sqlalchemy import text

        # Recursive CTE ile sadece path'teki topic'leri getir
        # PostgreSQL WITH RECURSIVE kullanır
        cte_query = text("""
            WITH RECURSIVE topic_path AS (
                -- Base case: hedef topic
                SELECT id, parent_id, code, name_tr, level, 1 as depth
                FROM topic_hierarchy
                WHERE id = :topic_id AND is_active = true

                UNION ALL

                -- Recursive case: parent'lara git
                SELECT t.id, t.parent_id, t.code, t.name_tr, t.level, tp.depth + 1
                FROM topic_hierarchy t
                INNER JOIN topic_path tp ON t.id = tp.parent_id
                WHERE t.is_active = true AND tp.depth < 5
            )
            SELECT id FROM topic_path ORDER BY depth DESC
        """)

        try:
            result = await self.db.execute(cte_query, {"topic_id": topic_id})
            path_ids = [row[0] for row in result.fetchall()]

            if not path_ids:
                return []

            # Path ID'leri ile topic objelerini getir (tek query)
            topics_result = await self.db.execute(
                select(TopicHierarchy)
                .where(TopicHierarchy.id.in_(path_ids))
                .where(TopicHierarchy.is_active.is_(True))
            )
            topics_map = {t.id: t for t in topics_result.scalars().all()}

            # Path sırasına göre döndür (kökten hedefe)
            return [topics_map[tid] for tid in path_ids if tid in topics_map]

        except Exception:
            # Fallback: CTE desteklenmeyen DB'ler için (SQLite gibi)
            # Basit iteratif yaklaşım
            path = []
            current_id = topic_id
            max_depth = 5

            while current_id and len(path) < max_depth:
                result = await self.db.execute(
                    select(TopicHierarchy)
                    .where(TopicHierarchy.id == current_id)
                    .where(TopicHierarchy.is_active.is_(True))
                )
                topic = result.scalar_one_or_none()
                if not topic:
                    break
                path.append(topic)
                current_id = topic.parent_id

            path.reverse()
            return path

    @db_retry
    async def add_question_tags(
        self, question_id: str, tag_names: list[str]
    ) -> list[QuestionTagAssociation]:
        """
        Soruya etiket ekle

        Args:
            question_id: Soru ID
            tag_names: Etiket isimleri

        Returns:
            List[QuestionTagAssociation]: Oluşturulan ilişkiler
        """
        associations = []

        # FIX N+1: Fetch all tags at once instead of querying in loop
        result = await self.db.execute(
            select(QuestionTag).where(QuestionTag.tag_name.in_(tag_names))
        )
        existing_tags = {tag.tag_name: tag for tag in result.scalars().all()}

        for tag_name in tag_names:
            # Check if tag exists in fetched results
            tag = existing_tags.get(tag_name)

            # Create new tag if not found
            if not tag:
                tag = QuestionTag(tag_name=tag_name, tag_category="general")
                self.db.add(tag)
                await self.db.flush()
                existing_tags[tag_name] = tag

            # İlişki oluştur
            association = QuestionTagAssociation(question_id=question_id, tag_id=tag.id)
            self.db.add(association)
            associations.append(association)

            # Etiket kullanım sayısını artır
            tag.usage_count += 1

        await self.db.commit()
        return associations

    # ========================================================================
    # TASK 70.3: Dynamic Difficulty Adjustment
    # ========================================================================

    @db_retry
    async def update_question_difficulty(
        self, question_id: str, force: bool = False
    ) -> QuestionBankItem | None:
        """
        Sorunun zorluk seviyesini dinamik olarak güncelle

        Args:
            question_id: Soru ID
            force: Zorla güncelle (minimum deneme kontrolü yapma)

        Returns:
            QuestionBankItem: Güncellenmiş soru
        """
        question = await self.get_question(question_id)
        if not question:
            return None

        # Güncelleme gerekli mi kontrol et
        if not force and not should_update_difficulty(question):
            return question

        # Başarı oranını hesapla
        if question.times_asked > 0:
            question.student_success_rate = (
                question.times_correct / question.times_asked
            )

        # IRT bazlı zorluk seviyesini güncelle
        new_difficulty = calculate_irt_based_difficulty(question.irt_difficulty)

        if new_difficulty != question.irt_based_difficulty:
            question.irt_based_difficulty = new_difficulty
            question.last_difficulty_update = datetime.now()
            question.difficulty_update_count += 1

            # Enum değerini de güncelle
            difficulty_map = {
                "very_easy": QuestionDifficultyLevel.VERY_EASY,
                "easy": QuestionDifficultyLevel.EASY,
                "medium": QuestionDifficultyLevel.MEDIUM,
                "hard": QuestionDifficultyLevel.HARD,
                "very_hard": QuestionDifficultyLevel.VERY_HARD,
            }
            question.difficulty_level = difficulty_map[new_difficulty]

        await self.db.commit()
        await self.db.refresh(question)

        return question

    @db_retry
    async def batch_update_difficulties(self, min_attempts: int = 100) -> int:
        """
        Tüm soruların zorluk seviyelerini toplu güncelle

        Args:
            min_attempts: Minimum deneme sayısı

        Returns:
            int: Güncellenen soru sayısı
        """
        # Güncellenmesi gereken soruları bul
        result = await self.db.execute(
            select(QuestionBankItem).where(
                and_(
                    QuestionBankItem.is_active == True,
                    QuestionBankItem.times_asked >= min_attempts,
                    or_(
                        QuestionBankItem.last_difficulty_update.is_(None),
                        QuestionBankItem.last_difficulty_update
                        < datetime.now() - timedelta(days=30),
                    ),
                )
            )
        )
        questions = result.scalars().all()

        # FIX N+1: Update all questions in memory, then commit once
        updated_count = 0
        difficulty_map = {
            "very_easy": QuestionDifficultyLevel.VERY_EASY,
            "easy": QuestionDifficultyLevel.EASY,
            "medium": QuestionDifficultyLevel.MEDIUM,
            "hard": QuestionDifficultyLevel.HARD,
            "very_hard": QuestionDifficultyLevel.VERY_HARD,
        }

        for question in questions:
            # Calculate success rate
            if question.times_asked > 0:
                question.student_success_rate = (
                    question.times_correct / question.times_asked
                )

            # Calculate new difficulty
            new_difficulty = calculate_irt_based_difficulty(question.irt_difficulty)

            if new_difficulty != question.irt_based_difficulty:
                question.irt_based_difficulty = new_difficulty
                question.last_difficulty_update = datetime.now()
                question.difficulty_update_count += 1
                question.difficulty_level = difficulty_map[new_difficulty]
                updated_count += 1

        # Single commit for all updates
        if updated_count > 0:
            await self.db.commit()

        return updated_count

    # ========================================================================
    # TASK 70.4: IRT Parameter Management
    # ========================================================================

    @db_retry
    async def calibrate_question_irt(
        self,
        question_id: str,
        new_discrimination: float,
        new_difficulty: float,
        new_guessing: float,
        new_upper_asymptote: float,
        calibration_method: str,
        sample_size: int,
        **kwargs,
    ) -> IRTCalibrationHistory:
        """
        Sorunun IRT parametrelerini kalibre et ve geçmişe kaydet

        Args:
            question_id: Soru ID
            new_discrimination: Yeni a parametresi
            new_difficulty: Yeni b parametresi
            new_guessing: Yeni c parametresi
            new_upper_asymptote: Yeni d parametresi
            calibration_method: Kalibrasyon yöntemi (EM, MLE, Bayesian)
            sample_size: Kullanılan öğrenci sayısı

        Returns:
            IRTCalibrationHistory: Kalibrasyon kaydı

        Raises:
            IRTValidationError: IRT parametreleri CLAUDE.md araliklari disindaysa
            ValueError: Soru bulunamazsa
        """
        # VALIDATION FIRST: CLAUDE.md IRT parameter ranges
        # difficulty: [-4.0, 4.0], discrimination: [0.2, 4.0]
        # guessing: [0.0, 0.35], upper_asymptote: [0.0, 1.0]
        validate_irt_difficulty(new_difficulty, strict=True)
        validate_irt_discrimination(new_discrimination, strict=True)
        validate_irt_guessing(new_guessing, strict=True)
        validate_irt_upper_asymptote(new_upper_asymptote, strict=True)

        question = await self.get_question(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Eski parametreleri kaydet
        calibration_history = IRTCalibrationHistory(
            question_id=question_id,
            calibration_date=datetime.now(),
            calibration_method=calibration_method,
            sample_size=sample_size,
            old_discrimination=question.irt_discrimination,
            old_difficulty=question.irt_difficulty,
            old_guessing=question.irt_guessing,
            old_upper_asymptote=question.irt_upper_asymptote,
            new_discrimination=new_discrimination,
            new_difficulty=new_difficulty,
            new_guessing=new_guessing,
            new_upper_asymptote=new_upper_asymptote,
            **kwargs,
        )

        self.db.add(calibration_history)

        # Yeni parametreleri uygula
        question.irt_discrimination = new_discrimination
        question.irt_difficulty = new_difficulty
        question.irt_guessing = new_guessing
        question.irt_upper_asymptote = new_upper_asymptote
        question.is_calibrated = True
        question.calibration_sample_size = sample_size
        question.last_calibration_date = datetime.now()

        # IRT bazlı zorluk seviyesini güncelle
        question.irt_based_difficulty = calculate_irt_based_difficulty(new_difficulty)

        await self.db.commit()
        await self.db.refresh(calibration_history)

        return calibration_history

    async def get_calibration_history(
        self, question_id: str, limit: int = 10
    ) -> list[IRTCalibrationHistory]:
        """
        Sorunun kalibrasyon geçmişini getir

        Args:
            question_id: Soru ID
            limit: Maksimum kayıt sayısı

        Returns:
            List[IRTCalibrationHistory]: Kalibrasyon kayıtları
        """
        result = await self.db.execute(
            select(IRTCalibrationHistory)
            .where(IRTCalibrationHistory.question_id == question_id)
            .order_by(IRTCalibrationHistory.calibration_date.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_questions_needing_calibration(
        self, min_attempts: int = 200, days_since_calibration: int = 90
    ) -> list[QuestionBankItem]:
        """
        Kalibrasyona ihtiyaç duyan soruları getir

        Args:
            min_attempts: Minimum deneme sayısı
            days_since_calibration: Son kalibrasyondan bu yana geçen gün sayısı

        Returns:
            List[QuestionBankItem]: Kalibrasyon gereken sorular
        """
        cutoff_date = datetime.now() - timedelta(days=days_since_calibration)

        result = await self.db.execute(
            select(QuestionBankItem).where(
                and_(
                    QuestionBankItem.is_active == True,
                    QuestionBankItem.times_asked >= min_attempts,
                    or_(
                        QuestionBankItem.is_calibrated == False,
                        QuestionBankItem.last_calibration_date < cutoff_date,
                    ),
                )
            )
        )
        return result.scalars().all()

    # ========================================================================
    # Search and Filter Operations
    # ========================================================================

    async def search_questions(
        self,
        exam_type: str | None = None,
        subject_area: str | None = None,
        topic_id: str | None = None,
        difficulty_level: QuestionDifficultyLevel | None = None,
        min_quality_score: float = 0.0,
        is_calibrated: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[QuestionBankItem]:
        """
        Soru ara ve filtrele

        FIX N+1: Eager loading eklendi

        Args:
            exam_type: Sınav tipi (TYT, AYT, YDT)
            subject_area: Ders alanı
            topic_id: Konu ID
            difficulty_level: Zorluk seviyesi
            min_quality_score: Minimum kalite skoru
            is_calibrated: Kalibre edilmiş mi
            limit: Maksimum sonuç sayısı
            offset: Başlangıç offset

        Returns:
            List[QuestionBankItem]: Bulunan sorular
        """
        # FIX N+1: Eager loading ile ilişkili verileri tek sorguda getir
        query = (
            select(QuestionBankItem)
            .options(
                joinedload(QuestionBankItem.primary_topic),
                selectinload(QuestionBankItem.tag_associations),
            )
            .where(QuestionBankItem.is_active == True)
        )

        if exam_type:
            query = query.where(QuestionBankItem.exam_type == exam_type)

        if subject_area:
            query = query.where(QuestionBankItem.subject_area == subject_area)

        if topic_id:
            query = query.where(QuestionBankItem.primary_topic_id == topic_id)

        if difficulty_level:
            query = query.where(QuestionBankItem.difficulty_level == difficulty_level)

        if min_quality_score > 0:
            query = query.where(QuestionBankItem.quality_score >= min_quality_score)

        if is_calibrated is not None:
            query = query.where(QuestionBankItem.is_calibrated == is_calibrated)

        query = query.order_by(QuestionBankItem.quality_score.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ========================================================================
    # Analytics and Statistics
    # ========================================================================

    async def get_question_statistics(self, question_id: str) -> dict[str, Any]:
        """
        Soru istatistiklerini getir

        Args:
            question_id: Soru ID

        Returns:
            Dict: İstatistik verileri
        """
        question = await self.get_question(question_id)
        if not question:
            return {}

        return {
            "question_id": question.id,
            "times_asked": question.times_asked,
            "times_correct": question.times_correct,
            "times_wrong": question.times_wrong,
            "times_skipped": question.times_skipped,
            "success_rate": question.student_success_rate,
            "average_response_time": question.average_response_time,
            "difficulty_level": question.difficulty_level.value,
            "irt_difficulty": question.irt_difficulty,
            "irt_discrimination": question.irt_discrimination,
            "is_calibrated": question.is_calibrated,
            "calibration_sample_size": question.calibration_sample_size,
            "quality_score": question.quality_score,
            "exposure_rate": question.exposure_rate,
        }

    async def get_topic_statistics(self, topic_id: str) -> dict[str, Any]:
        """
        Konu istatistiklerini getir

        Args:
            topic_id: Konu ID

        Returns:
            Dict: İstatistik verileri
        """
        topic = await self.db.get(TopicHierarchy, topic_id)
        if not topic:
            return {}

        # Konuya ait soruları say
        result = await self.db.execute(
            select(func.count(QuestionBankItem.id)).where(
                and_(
                    QuestionBankItem.primary_topic_id == topic_id,
                    QuestionBankItem.is_active == True,
                )
            )
        )
        total_questions = result.scalar()

        # Ortalama zorluk hesapla
        result = await self.db.execute(
            select(func.avg(QuestionBankItem.irt_difficulty)).where(
                and_(
                    QuestionBankItem.primary_topic_id == topic_id,
                    QuestionBankItem.is_active == True,
                )
            )
        )
        avg_difficulty = result.scalar() or 0.0

        return {
            "topic_id": topic.id,
            "topic_name": topic.name_tr,
            "topic_code": topic.code,
            "level": topic.level,
            "total_questions": total_questions,
            "average_difficulty": avg_difficulty,
            "osym_relevance": topic.osym_relevance,
            "osym_frequency": topic.osym_frequency,
        }
