"""
Soru CRUD İşlemleri Servisi
Task 71: Soru Bankası CRUD Operasyonları

Task 71.1: Soru ekleme (Rich text editor, Image upload)
Task 71.2: Soru güncelleme (Version control, Change history)
Task 71.3: Soru silme (Soft delete, Archive, Restore)
Task 71.4: Soru arama (Full-text search, Advanced filters, Faceted search)
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.question_bank import (
    QuestionBankItem,
    QuestionDifficultyLevel,
    QuestionTag,
    QuestionTagAssociation,
    TopicHierarchy,
)

logger = logging.getLogger(__name__)


class QuestionCRUDService:
    """
    Soru CRUD işlemleri servisi
    REQ-13.1: Makale/Soru içerik yönetimi
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ========================================================================
    # TASK 71.1: Soru Ekleme (Rich Text Editor, Image Upload)
    # ========================================================================

    async def create_question(
        self,
        question_data: dict[str, Any],
        created_by: str,
        image_file: bytes | None = None,
        image_filename: str | None = None,
    ) -> QuestionBankItem:
        """
        Yeni soru oluştur

        Args:
            question_data: Soru verileri
            created_by: Oluşturan kullanıcı ID
            image_file: Görsel dosyası (bytes)
            image_filename: Görsel dosya adı

        Returns:
            QuestionBankItem: Oluşturulan soru
        """
        try:
            # Görsel yükleme işlemi
            image_url = None
            if image_file and image_filename:
                image_url = await self._upload_question_image(
                    image_file, image_filename
                )

            # Konu ID'sini al veya oluştur
            topic_id = await self._get_or_create_topic(
                question_data.get("konu", "Genel"),
                question_data.get("alt_konu"),
            )

            # Zorluk seviyesini enum'a çevir
            difficulty_str = question_data.get("zorluk_seviyesi", "medium").lower()
            difficulty_map = {
                "çok kolay": QuestionDifficultyLevel.VERY_EASY,
                "very_easy": QuestionDifficultyLevel.VERY_EASY,
                "kolay": QuestionDifficultyLevel.EASY,
                "easy": QuestionDifficultyLevel.EASY,
                "orta": QuestionDifficultyLevel.MEDIUM,
                "medium": QuestionDifficultyLevel.MEDIUM,
                "zor": QuestionDifficultyLevel.HARD,
                "hard": QuestionDifficultyLevel.HARD,
                "çok zor": QuestionDifficultyLevel.VERY_HARD,
                "very_hard": QuestionDifficultyLevel.VERY_HARD,
            }
            difficulty = difficulty_map.get(
                difficulty_str, QuestionDifficultyLevel.MEDIUM
            )

            # Seçenekleri parse et
            secenekler = question_data.get("secenekler", [])
            option_a = secenekler[0] if len(secenekler) > 0 else ""
            option_b = secenekler[1] if len(secenekler) > 1 else ""
            option_c = secenekler[2] if len(secenekler) > 2 else ""
            option_d = secenekler[3] if len(secenekler) > 3 else ""
            option_e = secenekler[4] if len(secenekler) > 4 else None

            # Soru nesnesini oluştur
            new_question = QuestionBankItem(
                id=str(uuid.uuid4()),
                # Soru içeriği
                question_text=question_data.get("soru_metni", ""),
                question_html=question_data.get("soru_html"),  # Rich text HTML
                question_latex=question_data.get("soru_latex"),  # LaTeX matematik
                question_image_url=image_url,
                # Seçenekler
                option_a=option_a.replace("A) ", "").replace("A)", "").strip(),
                option_b=option_b.replace("B) ", "").replace("B)", "").strip(),
                option_c=option_c.replace("C) ", "").replace("C)", "").strip(),
                option_d=option_d.replace("D) ", "").replace("D)", "").strip(),
                option_e=option_e.replace("E) ", "").replace("E)", "").strip()
                if option_e
                else None,
                correct_answer=question_data.get("dogru_cevap", "A").upper(),
                # Açıklamalar
                explanation=question_data.get("cozum_aciklamasi"),
                explanation_video_url=question_data.get("cozum_video_url"),
                alternative_solutions=question_data.get("alternatif_cozumler"),
                # Konu ve etiketleme
                primary_topic_id=topic_id,
                secondary_topics=question_data.get("ikincil_konular"),
                bloom_level=question_data.get("bloom_seviyesi", 1),
                bloom_category=question_data.get("bloom_kategorisi", "knowledge"),
                # Zorluk
                difficulty_level=difficulty,
                # Metadata
                exam_type=question_data.get("sinav_tipi", "TYT"),
                subject_area=question_data.get("konu", "Matematik"),
                grade_level=question_data.get("sinif_seviyesi", 12),
                # ÖSYM uyumu
                osym_format_compliant=question_data.get("osym_uyumlu", True),
                osym_year=question_data.get("osym_yili"),
                # Kalite
                quality_score=question_data.get("kalite_skoru", 0.0),
                quality_review_status="pending",
                # Sistem
                created_by=created_by,
                is_active=True,
                is_public=question_data.get("genel_erisim", False),
            )

            # Veritabanına ekle
            self.db.add(new_question)
            await self.db.commit()
            await self.db.refresh(new_question)

            # Etiketleri ekle
            if "etiketler" in question_data:
                await self._add_question_tags(
                    new_question.id, question_data["etiketler"]
                )

            logger.info(f"Yeni soru oluşturuldu: {new_question.id}")
            return new_question

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Soru oluşturma hatası: {e!s}", exc_info=True)
            raise

    async def _upload_question_image(self, image_file: bytes, filename: str) -> str:
        """
        Soru görselini yükle

        Args:
            image_file: Görsel dosyası (bytes)
            filename: Dosya adı

        Returns:
            str: Yüklenen görselin URL'i
        """
        try:
            import os
            from pathlib import Path

            # Upload dizinini oluştur
            upload_dir = Path("uploads/questions")
            upload_dir.mkdir(parents=True, exist_ok=True)

            # Benzersiz dosya adı oluştur
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename

            # Dosyayı kaydet
            with open(file_path, "wb") as f:
                f.write(image_file)

            # URL'i döndür
            image_url = f"/uploads/questions/{unique_filename}"
            logger.info(f"Görsel yüklendi: {image_url}")
            return image_url

        except Exception as e:
            logger.error(f"Görsel yükleme hatası: {e!s}", exc_info=True)
            raise

    async def _get_or_create_topic(
        self, topic_name: str, subtopic_name: str | None = None
    ) -> str:
        """
        Konu ID'sini al veya yeni konu oluştur

        Args:
            topic_name: Ana konu adı
            subtopic_name: Alt konu adı (opsiyonel)

        Returns:
            str: Konu ID'si
        """
        try:
            # Ana konuyu ara
            stmt = select(TopicHierarchy).where(
                and_(
                    TopicHierarchy.name_tr == topic_name,
                    TopicHierarchy.level == 1,
                    TopicHierarchy.is_active == True,
                )
            )
            result = await self.db.execute(stmt)
            topic = result.scalar_one_or_none()

            # Ana konu yoksa oluştur
            if not topic:
                topic = TopicHierarchy(
                    id=str(uuid.uuid4()),
                    level=1,
                    code=f"TOPIC_{uuid.uuid4().hex[:8].upper()}",
                    name_tr=topic_name,
                    is_active=True,
                )
                self.db.add(topic)
                await self.db.commit()
                await self.db.refresh(topic)

            # Alt konu varsa onu ara veya oluştur
            if subtopic_name:
                stmt = select(TopicHierarchy).where(
                    and_(
                        TopicHierarchy.name_tr == subtopic_name,
                        TopicHierarchy.parent_id == topic.id,
                        TopicHierarchy.is_active == True,
                    )
                )
                result = await self.db.execute(stmt)
                subtopic = result.scalar_one_or_none()

                if not subtopic:
                    subtopic = TopicHierarchy(
                        id=str(uuid.uuid4()),
                        level=2,
                        parent_id=topic.id,
                        code=f"{topic.code}.{uuid.uuid4().hex[:8].upper()}",
                        name_tr=subtopic_name,
                        is_active=True,
                    )
                    self.db.add(subtopic)
                    await self.db.commit()
                    await self.db.refresh(subtopic)

                return subtopic.id

            return topic.id

        except Exception as e:
            logger.error(f"Konu oluşturma hatası: {e!s}", exc_info=True)
            raise

    async def _add_question_tags(self, question_id: str, tags: list[str]) -> None:
        """
        Soruya etiket ekle

        Args:
            question_id: Soru ID'si
            tags: Etiket listesi

        Performance: Optimized to use batch query instead of N queries
        """
        try:
            # OPTIMIZATION: Fetch all tags in one query instead of N queries
            # Before: N database queries (one per tag)
            # After: 1 database query
            stmt = select(QuestionTag).where(QuestionTag.tag_name.in_(tags))
            result = await self.db.execute(stmt)
            existing_tags = {tag.tag_name: tag for tag in result.scalars().all()}

            # Process each tag
            for tag_name in tags:
                # Get existing tag or create new one
                tag = existing_tags.get(tag_name)

                if not tag:
                    tag = QuestionTag(
                        id=str(uuid.uuid4()),
                        tag_name=tag_name,
                        tag_category="general",
                        usage_count=0,
                    )
                    self.db.add(tag)
                    await self.db.flush()  # Flush to get tag.id

                # Etiket ilişkisini oluştur
                association = QuestionTagAssociation(
                    id=str(uuid.uuid4()),
                    question_id=question_id,
                    tag_id=tag.id,
                    weight=1.0,
                )
                self.db.add(association)

                # Kullanım sayısını artır
                tag.usage_count += 1

            await self.db.commit()

        except Exception as e:
            logger.error(f"Etiket ekleme hatası: {e!s}", exc_info=True)
            raise

    # ========================================================================
    # TASK 71.2: Soru Güncelleme (Version Control, Change History)
    # ========================================================================

    async def update_question(
        self,
        question_id: str,
        update_data: dict[str, Any],
        updated_by: str,
        create_version: bool = True,
    ) -> QuestionBankItem | None:
        """
        Soruyu güncelle ve versiyon oluştur

        Args:
            question_id: Soru ID'si
            update_data: Güncellenecek veriler
            updated_by: Güncelleyen kullanıcı ID
            create_version: Versiyon oluşturulsun mu

        Returns:
            QuestionBankItem: Güncellenmiş soru
        """
        try:
            # Soruyu getir
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return None

            # Versiyon oluştur (değişiklik geçmişi)
            if create_version:
                await self._create_question_version(question, updated_by)

            # Güncelleme yap
            for key, value in update_data.items():
                if hasattr(question, key):
                    setattr(question, key, value)

            question.updated_at = datetime.now()

            await self.db.commit()
            await self.db.refresh(question)

            logger.info(f"Soru güncellendi: {question_id}")
            return question

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Soru güncelleme hatası: {e!s}", exc_info=True)
            raise

    async def _create_question_version(
        self, question: QuestionBankItem, updated_by: str
    ) -> None:
        """
        Soru versiyonu oluştur (değişiklik geçmişi)

        Args:
            question: Soru nesnesi
            updated_by: Güncelleyen kullanıcı ID
        """
        try:
            # Versiyon tablosu yoksa oluştur (migration gerekebilir)
            version = {
                "id": str(uuid.uuid4()),
                "question_id": question.id,
                "version_number": await self._get_next_version_number(question.id),
                "question_text": question.question_text,
                "question_html": question.question_html,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "option_e": question.option_e,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "difficulty_level": question.difficulty_level.value,
                "irt_difficulty": question.irt_difficulty,
                "irt_discrimination": question.irt_discrimination,
                "irt_guessing": question.irt_guessing,
                "created_by": updated_by,
                "created_at": datetime.now(),
            }

            # Versiyon geçmişini JSON olarak sakla
            if not hasattr(question, "version_history"):
                question.version_history = []

            if isinstance(question.version_history, list):
                question.version_history.append(version)
            else:
                question.version_history = [version]

            logger.info(
                f"Soru versiyonu oluşturuldu: {question.id} v{version['version_number']}"
            )

        except Exception as e:
            logger.error(f"Versiyon oluşturma hatası: {e!s}", exc_info=True)
            # Versiyon oluşturma hatası kritik değil, devam et

    async def _get_next_version_number(self, question_id: str) -> int:
        """
        Sonraki versiyon numarasını al

        Args:
            question_id: Soru ID'si

        Returns:
            int: Sonraki versiyon numarası
        """
        try:
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question or not hasattr(question, "version_history"):
                return 1

            if isinstance(question.version_history, list):
                return len(question.version_history) + 1

            return 1

        except Exception as e:
            logger.error(f"Versiyon numarası alma hatası: {e!s}", exc_info=True)
            return 1

    async def get_question_history(self, question_id: str) -> list[dict[str, Any]]:
        """
        Soru değişiklik geçmişini getir

        Args:
            question_id: Soru ID'si

        Returns:
            List[Dict]: Değişiklik geçmişi
        """
        try:
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return []

            if hasattr(question, "version_history") and isinstance(
                question.version_history, list
            ):
                return question.version_history

            return []

        except Exception as e:
            logger.error(f"Geçmiş getirme hatası: {e!s}", exc_info=True)
            return []

    # ========================================================================
    # TASK 71.3: Soru Silme (Soft Delete, Archive, Restore)
    # ========================================================================

    async def delete_question(
        self, question_id: str, deleted_by: str, permanent: bool = False
    ) -> bool:
        """
        Soruyu sil (soft delete)

        Args:
            question_id: Soru ID'si
            deleted_by: Silen kullanıcı ID
            permanent: Kalıcı silme mi (varsayılan: False)

        Returns:
            bool: Başarılı mı
        """
        try:
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return False

            if permanent:
                # Kalıcı silme
                await self.db.delete(question)
            else:
                # Soft delete - sadece deaktif et
                question.is_active = False
                question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Soru silindi: {question_id} (permanent={permanent})")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Soru silme hatası: {e!s}", exc_info=True)
            return False

    async def archive_question(self, question_id: str, archived_by: str) -> bool:
        """
        Soruyu arşivle

        Args:
            question_id: Soru ID'si
            archived_by: Arşivleyen kullanıcı ID

        Returns:
            bool: Başarılı mı
        """
        try:
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return False

            # Arşiv durumunu işaretle
            question.is_active = False
            question.quality_review_status = "archived"
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Soru arşivlendi: {question_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Soru arşivleme hatası: {e!s}", exc_info=True)
            return False

    async def restore_question(self, question_id: str, restored_by: str) -> bool:
        """
        Arşivlenmiş/silinmiş soruyu geri yükle

        Args:
            question_id: Soru ID'si
            restored_by: Geri yükleyen kullanıcı ID

        Returns:
            bool: Başarılı mı
        """
        try:
            stmt = select(QuestionBankItem).where(QuestionBankItem.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                return False

            # Geri yükle
            question.is_active = True
            if question.quality_review_status == "archived":
                question.quality_review_status = "pending"
            question.updated_at = datetime.now()

            await self.db.commit()

            logger.info(f"Soru geri yüklendi: {question_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Soru geri yükleme hatası: {e!s}", exc_info=True)
            return False

    async def get_archived_questions(
        self, limit: int = 100, offset: int = 0
    ) -> list[QuestionBankItem]:
        """
        Arşivlenmiş soruları getir

        Args:
            limit: Maksimum soru sayısı
            offset: Başlangıç offset'i

        Returns:
            List[QuestionBankItem]: Arşivlenmiş sorular
        """
        try:
            stmt = (
                select(QuestionBankItem)
                .where(
                    and_(
                        QuestionBankItem.is_active == False,
                        QuestionBankItem.quality_review_status == "archived",
                    )
                )
                .limit(limit)
                .offset(offset)
            )

            result = await self.db.execute(stmt)
            questions = result.scalars().all()

            return list(questions)

        except Exception as e:
            logger.error(f"Arşiv sorgusu hatası: {e!s}", exc_info=True)
            return []

    # ========================================================================
    # TASK 71.4: Soru Arama (Full-text Search, Advanced Filters, Faceted Search)
    # ========================================================================

    async def search_questions(
        self,
        search_query: str | None = None,
        filters: dict[str, Any] | None = None,
        facets: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Gelişmiş soru arama

        Args:
            search_query: Arama sorgusu (full-text)
            filters: Filtreler (exam_type, subject, difficulty, etc.)
            facets: Facet alanları (konu, zorluk, sınav türü grupları)
            limit: Maksimum sonuç sayısı
            offset: Başlangıç offset'i

        Returns:
            Dict: Arama sonuçları ve facet'ler
        """
        try:
            # Base query
            stmt = select(QuestionBankItem).where(QuestionBankItem.is_active == True)

            # Full-text search (PostgreSQL için)
            if search_query:
                # Escape LIKE wildcards to prevent pattern injection
                escaped = (
                    search_query.replace("\\", "\\\\")
                    .replace("%", "\\%")
                    .replace("_", "\\_")
                )
                search_pattern = f"%{escaped}%"
                stmt = stmt.where(
                    or_(
                        QuestionBankItem.question_text.ilike(search_pattern),
                        QuestionBankItem.explanation.ilike(search_pattern),
                        QuestionBankItem.option_a.ilike(search_pattern),
                        QuestionBankItem.option_b.ilike(search_pattern),
                        QuestionBankItem.option_c.ilike(search_pattern),
                        QuestionBankItem.option_d.ilike(search_pattern),
                    )
                )

            # Filtreler uygula
            if filters:
                if "exam_type" in filters:
                    stmt = stmt.where(
                        QuestionBankItem.exam_type == filters["exam_type"]
                    )

                if "subject_area" in filters:
                    stmt = stmt.where(
                        QuestionBankItem.subject_area == filters["subject_area"]
                    )

                if "difficulty" in filters:
                    difficulty_str = filters["difficulty"].lower()
                    difficulty_map = {
                        "very_easy": QuestionDifficultyLevel.VERY_EASY,
                        "easy": QuestionDifficultyLevel.EASY,
                        "medium": QuestionDifficultyLevel.MEDIUM,
                        "hard": QuestionDifficultyLevel.HARD,
                        "very_hard": QuestionDifficultyLevel.VERY_HARD,
                    }
                    if difficulty_str in difficulty_map:
                        stmt = stmt.where(
                            QuestionBankItem.difficulty_level
                            == difficulty_map[difficulty_str]
                        )

                if "grade_level" in filters:
                    stmt = stmt.where(
                        QuestionBankItem.grade_level == filters["grade_level"]
                    )

                if "topic_id" in filters:
                    stmt = stmt.where(
                        QuestionBankItem.primary_topic_id == filters["topic_id"]
                    )

                if "min_quality" in filters:
                    stmt = stmt.where(
                        QuestionBankItem.quality_score >= filters["min_quality"]
                    )

                if "irt_difficulty_range" in filters:
                    min_diff, max_diff = filters["irt_difficulty_range"]
                    stmt = stmt.where(
                        and_(
                            QuestionBankItem.irt_difficulty >= min_diff,
                            QuestionBankItem.irt_difficulty <= max_diff,
                        )
                    )

                if "osym_compliant" in filters:
                    stmt = stmt.where(
                        QuestionBankItem.osym_format_compliant
                        == filters["osym_compliant"]
                    )

                if "source_book" in filters:
                    stmt = stmt.where(
                        QuestionBankItem.source_book == filters["source_book"]
                    )

            # Sayfalama
            count_stmt = stmt
            stmt = stmt.limit(limit).offset(offset)

            # Sorguyu çalıştır
            result = await self.db.execute(stmt)
            questions = result.scalars().all()

            # Toplam sayıyı al
            from sqlalchemy import func

            count_result = await self.db.execute(
                select(func.count()).select_from(count_stmt.subquery())
            )
            total_count = count_result.scalar()

            # Facet'leri hesapla
            facet_results = {}
            if facets:
                facet_results = await self._calculate_facets(facets, filters)

            return {
                "questions": list(questions),
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "facets": facet_results,
            }

        except Exception as e:
            logger.error(f"Arama hatası: {e!s}", exc_info=True)
            return {
                "questions": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "facets": {},
            }

    async def _calculate_facets(
        self, facet_fields: list[str], filters: dict[str, Any] | None = None
    ) -> dict[str, dict[str, int]]:
        """
        Facet'leri hesapla (gruplandırılmış sayılar)

        Args:
            facet_fields: Facet alanları
            filters: Mevcut filtreler

        Returns:
            Dict: Facet sonuçları
        """
        try:
            from sqlalchemy import func

            facet_results = {}

            for field in facet_fields:
                if field == "exam_type":
                    stmt = (
                        select(
                            QuestionBankItem.exam_type,
                            func.count(QuestionBankItem.id).label("count"),
                        )
                        .where(QuestionBankItem.is_active == True)
                        .group_by(QuestionBankItem.exam_type)
                    )

                elif field == "subject_area":
                    stmt = (
                        select(
                            QuestionBankItem.subject_area,
                            func.count(QuestionBankItem.id).label("count"),
                        )
                        .where(QuestionBankItem.is_active == True)
                        .group_by(QuestionBankItem.subject_area)
                    )

                elif field == "difficulty":
                    stmt = (
                        select(
                            QuestionBankItem.difficulty_level,
                            func.count(QuestionBankItem.id).label("count"),
                        )
                        .where(QuestionBankItem.is_active == True)
                        .group_by(QuestionBankItem.difficulty_level)
                    )

                elif field == "grade_level":
                    stmt = (
                        select(
                            QuestionBankItem.grade_level,
                            func.count(QuestionBankItem.id).label("count"),
                        )
                        .where(QuestionBankItem.is_active == True)
                        .group_by(QuestionBankItem.grade_level)
                    )

                else:
                    continue

                # Mevcut filtreleri uygula (seçili facet hariç)
                if filters:
                    for filter_key, filter_value in filters.items():
                        if filter_key != field:
                            if filter_key == "exam_type":
                                stmt = stmt.where(
                                    QuestionBankItem.exam_type == filter_value
                                )
                            elif filter_key == "subject_area":
                                stmt = stmt.where(
                                    QuestionBankItem.subject_area == filter_value
                                )

                result = await self.db.execute(stmt)
                rows = result.all()

                facet_results[field] = {
                    str(row[0]): row[1] for row in rows if row[0] is not None
                }

            return facet_results

        except Exception as e:
            logger.error(f"Facet hesaplama hatası: {e!s}", exc_info=True)
            return {}

    async def advanced_search_with_elasticsearch(
        self,
        search_query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[QuestionBankItem]:
        """
        Elasticsearch ile gelişmiş arama

        Args:
            search_query: Arama sorgusu
            filters: Filtreler
            limit: Maksimum sonuç sayısı

        Returns:
            List[QuestionBankItem]: Arama sonuçları
        """
        try:
            from core.elasticsearch_client import get_elasticsearch_client

            es_client = get_elasticsearch_client()

            # Elasticsearch sorgusu oluştur
            es_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": search_query,
                                    "fields": [
                                        "question_text^3",
                                        "explanation^2",
                                        "option_a",
                                        "option_b",
                                        "option_c",
                                        "option_d",
                                    ],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO",
                                }
                            }
                        ],
                        "filter": [{"term": {"is_active": True}}],
                    }
                },
                "size": limit,
            }

            # Filtreleri ekle
            if filters:
                if "exam_type" in filters:
                    es_query["query"]["bool"]["filter"].append(
                        {"term": {"exam_type": filters["exam_type"]}}
                    )

                if "subject_area" in filters:
                    es_query["query"]["bool"]["filter"].append(
                        {"term": {"subject_area": filters["subject_area"]}}
                    )

                if "difficulty" in filters:
                    es_query["query"]["bool"]["filter"].append(
                        {"term": {"difficulty_level": filters["difficulty"]}}
                    )

            # Elasticsearch'te ara
            response = await es_client.search(index="questions", body=es_query)

            # Soru ID'lerini al
            question_ids = [hit["_id"] for hit in response["hits"]["hits"]]

            # Veritabanından soruları getir
            if question_ids:
                stmt = select(QuestionBankItem).where(
                    QuestionBankItem.id.in_(question_ids),
                    QuestionBankItem.is_active == True,
                )
                result = await self.db.execute(stmt)
                questions = result.scalars().all()
                return list(questions)

            return []

        except Exception as e:
            logger.error(f"Elasticsearch arama hatası: {e!s}", exc_info=True)
            # Fallback: Normal arama yap
            search_result = await self.search_questions(
                search_query=search_query, filters=filters, limit=limit
            )
            return search_result["questions"]

    # ========================================================================
    # Yardımcı Metodlar
    # ========================================================================

    async def get_question_by_id(
        self, question_id: str, include_relations: bool = False
    ) -> QuestionBankItem | None:
        """
        ID'ye göre soru getir

        Args:
            question_id: Soru ID'si
            include_relations: İlişkileri dahil et

        Returns:
            QuestionBankItem: Soru nesnesi
        """
        try:
            stmt = select(QuestionBankItem).where(
                QuestionBankItem.id == question_id,
                QuestionBankItem.is_active == True,
            )

            if include_relations:
                stmt = stmt.options(
                    selectinload(QuestionBankItem.primary_topic),
                    selectinload(QuestionBankItem.tag_associations),
                    selectinload(QuestionBankItem.calibration_history),
                )

            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            return question

        except Exception as e:
            logger.error(f"Soru getirme hatası: {e!s}", exc_info=True)
            return None

    async def bulk_create_questions(
        self, questions_data: list[dict[str, Any]], created_by: str
    ) -> dict[str, Any]:
        """
        Toplu soru oluşturma

        Args:
            questions_data: Soru verileri listesi
            created_by: Oluşturan kullanıcı ID

        Returns:
            Dict: Sonuç özeti
        """
        try:
            created_questions = []
            failed_questions = []

            for question_data in questions_data:
                try:
                    question = await self.create_question(question_data, created_by)
                    created_questions.append(question.id)
                except Exception as e:
                    failed_questions.append({"data": question_data, "error": str(e)})

            return {
                "success_count": len(created_questions),
                "failed_count": len(failed_questions),
                "created_ids": created_questions,
                "failures": failed_questions,
            }

        except Exception as e:
            logger.error(f"Toplu oluşturma hatası: {e!s}", exc_info=True)
            return {
                "success_count": 0,
                "failed_count": len(questions_data),
                "created_ids": [],
                "failures": [{"error": str(e)}],
            }

    async def get_question_statistics(self) -> dict[str, Any]:
        """
        Soru bankası istatistikleri

        Returns:
            Dict: İstatistikler
        """
        try:
            from sqlalchemy import func

            # Toplam soru sayısı
            total_stmt = select(func.count(QuestionBankItem.id)).where(
                QuestionBankItem.is_active == True
            )
            total_result = await self.db.execute(total_stmt)
            total_count = total_result.scalar()

            # Sınav türüne göre dağılım
            exam_type_stmt = (
                select(
                    QuestionBankItem.exam_type,
                    func.count(QuestionBankItem.id).label("count"),
                )
                .where(QuestionBankItem.is_active == True)
                .group_by(QuestionBankItem.exam_type)
            )
            exam_type_result = await self.db.execute(exam_type_stmt)
            exam_type_dist = {row[0]: row[1] for row in exam_type_result.all()}

            # Zorluk dağılımı
            difficulty_stmt = (
                select(
                    QuestionBankItem.difficulty_level,
                    func.count(QuestionBankItem.id).label("count"),
                )
                .where(QuestionBankItem.is_active == True)
                .group_by(QuestionBankItem.difficulty_level)
            )
            difficulty_result = await self.db.execute(difficulty_stmt)
            difficulty_dist = {
                str(row[0].value): row[1] for row in difficulty_result.all()
            }

            # Kalibrasyon durumu
            calibrated_stmt = select(func.count(QuestionBankItem.id)).where(
                and_(
                    QuestionBankItem.is_active == True,
                    QuestionBankItem.is_calibrated == True,
                )
            )
            calibrated_result = await self.db.execute(calibrated_stmt)
            calibrated_count = calibrated_result.scalar()

            return {
                "total_questions": total_count,
                "exam_type_distribution": exam_type_dist,
                "difficulty_distribution": difficulty_dist,
                "calibrated_questions": calibrated_count,
                "calibration_percentage": (
                    (calibrated_count / total_count * 100) if total_count > 0 else 0
                ),
            }

        except Exception as e:
            logger.error(f"İstatistik hatası: {e!s}", exc_info=True)
            return {}

    # ================================================================
    # Random Sampling & Source Book Queries
    # ================================================================

    async def get_random_questions(
        self,
        count: int = 10,
        subject_area: str | None = None,
        exam_type: str | None = None,
    ) -> list[QuestionBankItem]:
        """Rastgele soru seçimi (adaptif öğrenme için)."""
        dialect = self.db.bind.dialect.name if self.db.bind else "sqlite"
        if dialect == "postgresql":
            stmt = select(QuestionBankItem).tablesample(func.bernoulli(20)).where(QuestionBankItem.is_active == True)
        else:
            stmt = select(QuestionBankItem).where(QuestionBankItem.is_active == True)

        if subject_area:
            stmt = stmt.where(QuestionBankItem.subject_area == subject_area)
        if exam_type:
            stmt = stmt.where(QuestionBankItem.exam_type == exam_type)

        if dialect == "postgresql":
            stmt = stmt.limit(count)
            result = await self.db.execute(stmt)
            rows = list(result.scalars().all())
            if len(rows) < count:
                stmt_fallback = select(QuestionBankItem).where(QuestionBankItem.is_active == True)
                if subject_area:
                    stmt_fallback = stmt_fallback.where(QuestionBankItem.subject_area == subject_area)
                if exam_type:
                    stmt_fallback = stmt_fallback.where(QuestionBankItem.exam_type == exam_type)
                stmt_fallback = stmt_fallback.limit(count)
                result = await self.db.execute(stmt_fallback)
                rows = list(result.scalars().all())
            return rows
        stmt = stmt.order_by(func.random()).limit(count)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_source_books(
        self,
        subject_area: str | None = None,
        exam_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Kaynak kitap listesi (soru sayılarıyla birlikte)."""
        from sqlalchemy import func

        stmt = (
            select(
                QuestionBankItem.source_book,
                QuestionBankItem.subject_area,
                QuestionBankItem.exam_type,
                func.count(QuestionBankItem.id).label("question_count"),
            )
            .where(
                QuestionBankItem.is_active == True,
                QuestionBankItem.source_book.isnot(None),
            )
            .group_by(
                QuestionBankItem.source_book,
                QuestionBankItem.subject_area,
                QuestionBankItem.exam_type,
            )
            .order_by(func.count(QuestionBankItem.id).desc())
        )

        if subject_area:
            stmt = stmt.where(QuestionBankItem.subject_area == subject_area)
        if exam_type:
            stmt = stmt.where(QuestionBankItem.exam_type == exam_type)

        result = await self.db.execute(stmt)
        rows = result.fetchall()

        return [
            {
                "book_name": row[0],
                "subject_area": row[1],
                "exam_type": row[2],
                "question_count": row[3],
            }
            for row in rows
        ]
