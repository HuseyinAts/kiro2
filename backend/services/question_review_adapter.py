"""
QuestionBank ↔ FSRS Adaptör Servisi

Soru bankası (QuestionBankItem) ile FSRS spaced repetition sistemi arasında köprü.
Yanlış cevaplanan soruları FSRS kartlarına dönüştürür ve tekrar kuyruğu yönetir.

Bilimsel dayanak:
- FSRS-6 SM-2'ye karşı %99.6 üstün (Expertium 2024 benchmark)
- Spaced retrieval: Yanlış cevap → 24-48h sonra tekrar (d=1.29)

NOT: Basitleştirilmiş FSRS güncelleme kullanılıyor. Tam 17-parametreli algoritma
turkish_optimized_fsrs.py'de mevcut — gelecekte entegre edilebilir.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.quality_gate import safe_for_beta_gate
from models.enums_db import SubjectArea
from models.fsrs_models import FSRSCard as DBFSRSCard
from models.question_bank import QuestionBankItem

logger = logging.getLogger(__name__)

# question_bank_id'yi cultural_factors JSON'da saklıyoruz
_QB_ID_KEY = "question_bank_id"


class QuestionReviewAdapter:
    """
    QuestionBankItem ↔ FSRSCard köprüsü.

    - create_review_card(): Yanlış cevaplanan soruyu FSRS kartına dönüştür
    - get_due_questions(): Tekrarı gelen soruları QuestionBankItem olarak döndür
    - submit_review(): Tekrar sonucunu kaydet ve FSRS parametrelerini güncelle
    """

    async def create_review_card(
        self,
        student_id: str,
        question_id: str,
        db: AsyncSession,
        error_type: str | None = None,
    ) -> DBFSRSCard | None:
        """
        Yanlış cevaplanan soruyu FSRS tekrar kartına dönüştür.

        Aynı öğrenci-soru çifti için mevcut kart varsa yeni oluşturmaz (idempotent).
        """
        # Mevcut kart kontrolü (idempotent)
        existing = await db.execute(
            select(DBFSRSCard).where(
                DBFSRSCard.student_id == student_id,
                DBFSRSCard.cultural_factors[_QB_ID_KEY].as_string() == question_id,
            )
        )
        if existing.scalar_one_or_none():
            logger.debug(f"Review card zaten mevcut: student={student_id}, q={question_id}")
            return None

        # QuestionBankItem'ı getir
        q_result = await db.execute(
            select(QuestionBankItem).where(
                QuestionBankItem.id == question_id,
                QuestionBankItem.is_active == True,
                # Kalite kapısı (core/quality_gate.py): kapısız soru KALICI FSRS
                # kuyruğuna girmesin — kart bir kez yazıldıktan sonra öğrenciye
                # tekrar tekrar gösterilir, yani sızıntı burada kalıcılaşır.
                safe_for_beta_gate(QuestionBankItem.id),
            )
        )
        question = q_result.scalar_one_or_none()
        if not question:
            logger.warning(f"Soru bulunamadı: {question_id}")
            return None

        # FSRS kartı oluştur — SubjectArea enum dönüşümü (UPPERCASE → lowercase)
        now = datetime.now(UTC)
        try:
            subject = SubjectArea(question.subject_area) if question.subject_area else SubjectArea.MATEMATIK
        except (ValueError, KeyError):
            subject = SubjectArea.MATEMATIK

        card = DBFSRSCard(
            id=str(uuid.uuid4()),
            student_id=student_id,
            front_text=question.question_text or "",
            back_text=question.explanation or question.correct_answer or "",
            subject_area=subject,
            topic=str(question.primary_topic_id or "genel"),
            stability=0.0,
            difficulty=0.0,
            elapsed_days=0,
            scheduled_days=1,
            reps=0,
            lapses=0,
            state="new",
            due_date=now + timedelta(hours=24),
            last_review=None,
            cultural_factors={
                _QB_ID_KEY: str(question_id),
                **({"error_type": error_type} if error_type else {}),
            },
        )

        db.add(card)
        await db.flush()
        logger.info(f"Review card oluşturuldu: card={card.id}, q={question_id}")
        return card

    async def get_due_questions(
        self,
        student_id: str,
        limit: int = 20,
        db: AsyncSession = None,
    ) -> list[dict]:
        """
        Tekrarı gelen soruları QuestionBankItem bilgileriyle birlikte döndür.

        Returns:
            Her dict: question_bank verileri + FSRS card_id + retention bilgisi
        """
        if not db:
            return []

        now = datetime.now(UTC)

        # Vadesi gelen kartları getir
        cards_result = await db.execute(
            select(DBFSRSCard)
            .where(
                DBFSRSCard.student_id == student_id,
                or_(
                    DBFSRSCard.due_date <= now,
                    DBFSRSCard.due_date.is_(None),
                ),
            )
            .order_by(DBFSRSCard.due_date.asc().nullsfirst())
            .limit(limit)
        )
        due_cards = cards_result.scalars().all()

        if not due_cards:
            return []

        # question_bank_id'leri topla
        qb_ids = []
        card_map: dict[str, DBFSRSCard] = {}
        for card in due_cards:
            factors = card.cultural_factors or {}
            qb_id = factors.get(_QB_ID_KEY)
            if qb_id:
                qb_ids.append(qb_id)
                card_map[qb_id] = card

        if not qb_ids:
            return []

        # QuestionBankItem'ları tek sorguda getir
        questions_result = await db.execute(
            select(QuestionBankItem).where(
                QuestionBankItem.id.in_(qb_ids),
                QuestionBankItem.is_active == True,
                # Kalite kapısı: geçmişten kalmış kapısız kartları da eler.
                safe_for_beta_gate(QuestionBankItem.id),
            )
        )
        questions = {str(q.id): q for q in questions_result.scalars().all()}

        # Birleştir
        result = []
        for qb_id, card in card_map.items():
            q = questions.get(qb_id)
            if not q:
                continue

            result.append({
                "card_id": card.id,
                "question_id": str(q.id),
                "question_text": q.question_text,
                "options": {
                    "A": q.option_a,
                    "B": q.option_b,
                    "C": q.option_c,
                    "D": q.option_d,
                    "E": getattr(q, "option_e", None),
                },
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "explanation_video_url": getattr(q, "explanation_video_url", None),
                "difficulty_level": q.difficulty_level,
                "subject_area": q.subject_area,
                "fsrs": {
                    "stability": card.stability,
                    "difficulty": card.difficulty,
                    "state": card.state,
                    "reps": card.reps,
                    "due_date": card.due_date.isoformat() if card.due_date else None,
                },
            })

        logger.debug(f"get_due_questions: {len(result)} soru döndürülüyor (student={student_id})")
        return result

    async def submit_review(
        self,
        card_id: str,
        grade: int,
        db: AsyncSession,
        student_id: str | None = None,
    ) -> DBFSRSCard | None:
        """
        Tekrar sonucunu kaydet ve FSRS parametrelerini güncelle.

        Grade: 1=AGAIN, 2=HARD, 3=GOOD, 4=EASY
        student_id: Verilirse kart sahipliği doğrulanır (IDOR koruması).
        """
        if grade < 1 or grade > 4:
            logger.warning(f"Geçersiz grade: {grade}")
            return None

        card_result = await db.execute(
            select(DBFSRSCard).where(DBFSRSCard.id == card_id)
        )
        card = card_result.scalar_one_or_none()
        if not card:
            logger.warning(f"Kart bulunamadı: {card_id}")
            return None

        # Kart sahipliği kontrolü (IDOR koruması)
        if student_id and card.student_id != student_id:
            logger.warning(f"Kart sahiplik ihlali: card.student={card.student_id}, request={student_id}")
            return None

        now = datetime.now(UTC)

        # Basit FSRS güncelleme (tam algoritma turkish_optimized_fsrs.py'de)
        interval_map = {
            1: 0.25,   # AGAIN: 6 saat sonra
            2: 1.0,    # HARD: 1 gün sonra
            3: 2.5,    # GOOD: 2.5 gün sonra (stability * 2.5)
            4: 7.0,    # EASY: 1 hafta sonra
        }

        base_interval = interval_map[grade]

        # Stability ve difficulty güncelle
        if grade == 1:  # AGAIN
            card.lapses += 1
            card.stability = max(0.1, card.stability * 0.5)
            card.difficulty = min(10.0, card.difficulty + 1.0)
        elif grade == 2:  # HARD
            card.stability = max(0.1, card.stability * 1.2)
            card.difficulty = min(10.0, card.difficulty + 0.15)
        elif grade == 3:  # GOOD
            card.stability = card.stability * 2.5 if card.stability > 0 else 1.0
            card.difficulty = max(0.0, card.difficulty - 0.15)
        else:  # EASY
            card.stability = card.stability * 3.5 if card.stability > 0 else 2.0
            card.difficulty = max(0.0, card.difficulty - 0.5)

        # elapsed_days: ÖNCE hesapla, SONRA last_review güncelle
        old_last_review = card.last_review or card.created_at
        card.elapsed_days = int((now - old_last_review).total_seconds() / 86400) if old_last_review else 0

        # Sonraki tekrar tarihini hesapla
        actual_interval = max(base_interval, card.stability) if card.stability > 0 else base_interval
        card.due_date = now + timedelta(days=actual_interval)
        card.last_review = now
        card.reps += 1
        card.scheduled_days = int(actual_interval)
        card.state = "review" if grade >= 2 else "relearning"

        await db.flush()
        logger.info(
            f"Review kaydedildi: card={card_id}, grade={grade}, "
            f"next_due={card.due_date.isoformat()}"
        )
        return card

    async def register_wrong_answers(
        self,
        student_id: str,
        question_ids: list[str],
        db: AsyncSession,
        error_types: dict[str, str] | None = None,
    ) -> int:
        """
        Toplu yanlış cevap kaydı — quiz sonunda çağrılır.

        Args:
            error_types: Optional {question_id: error_type} mapping from F8 ErrorTypeSelector.
                         Valid types: concept, procedural, careless, knowledge_gap.

        Returns:
            Oluşturulan kart sayısı
        """
        valid_error_types = {"concept", "procedural", "careless", "knowledge_gap"}
        created = 0
        for qid in question_ids:
            et = (error_types or {}).get(qid)
            if et and et not in valid_error_types:
                et = None  # Reject invalid types silently
            card = await self.create_review_card(student_id, qid, db, error_type=et)
            if card:
                created += 1

        logger.info(f"register_wrong_answers: {created}/{len(question_ids)} kart oluşturuldu")
        return created
