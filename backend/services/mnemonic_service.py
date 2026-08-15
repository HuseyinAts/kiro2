"""
Mnemonic Hints Service — F19
AI-generated Turkish memory aids for frequently-missed questions.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.structured_logger import get_logger
from models.question_bank import (
    QuestionBankItem,
    QuestionContent,
    QuestionMetadata,
)

logger = get_logger("mnemonic_service")


async def get_mnemonic(
    *,
    db: AsyncSession,
    question_id: str,
) -> dict | None:
    """Get the mnemonic hint for a question, if available."""
    # Note: mnemonic_hint and is_active columns not in DB yet
    # Using fallback approach - get question without these columns
    result = await db.execute(
        select(
            QuestionBankItem.id,
            QuestionContent.question_text,
            QuestionMetadata.subject_area,
        )
        .select_from(QuestionBankItem)
        .join(QuestionContent, QuestionContent.id == QuestionBankItem.id)
        .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
        .where(
            QuestionBankItem.id == question_id,
        )
    )
    row = result.first()

    if not row:
        return None

    return {
        "question_id": str(row.id),
        "mnemonic_hint": None,  # Column not in DB yet
        "has_mnemonic": False,  # Column not in DB yet
        "subject": row.subject_area,
    }


async def generate_mnemonic(
    *,
    db: AsyncSession,
    question_id: str,
    force: bool = False,
) -> dict:
    """Generate a Turkish mnemonic hint using LLM.

    Only generates if question doesn't already have one (unless force=True).
    """
    # Get the question.
    # #485 split: aşağıda `question.question_text` / `.correct_answer` (content)
    # ve `.subject_area` (metadata_info) ÖRNEK düzeyinde okunuyor. Bu ilişkiler
    # lazy='select' — async oturumda eager-load'suz erişim MissingGreenlet atar.
    result = await db.execute(
        select(QuestionBankItem)
        .options(
            selectinload(QuestionBankItem.content),
            selectinload(QuestionBankItem.metadata_info),
        )
        .where(
            QuestionBankItem.id == question_id,
            QuestionBankItem.is_active == True,  # noqa: E712
        )
    )
    question = result.scalar_one_or_none()

    if not question:
        return {"error": "Soru bulunamadı"}

    # Note: mnemonic_hint column not in DB yet - always generate new
    if not force:
        return {
            "question_id": str(question.id),
            "mnemonic_hint": None,
            "generated": False,
        }

    # Generate using LLM
    prompt = _build_mnemonic_prompt(
        question_text=question.question_text or "",
        correct_answer=question.correct_answer or "",
        subject=question.subject_area or "",
    )

    try:
        from core.llm_service import LLMService

        llm = LLMService()
        hint = await llm.generate(prompt, max_tokens=300)

        # Note: mnemonic_hint column not in DB yet - cannot store
        # question.mnemonic_hint = hint
        # await db.flush()

        return {
            "question_id": str(question.id),
            "mnemonic_hint": hint,
            "generated": True,
        }
    except Exception as e:
        logger.error(f"Mnemonic generation failed: {e}", exc_info=True)
        return {"error": f"Mnemonic üretilemedi: {e!s}"}


def _build_mnemonic_prompt(
    *,
    question_text: str,
    correct_answer: str,
    subject: str,
) -> str:
    """Build the LLM prompt for Turkish mnemonic generation."""
    return f"""Sen bir Türk eğitim uzmanısın. Aşağıdaki YKS sorusu için kısa, akılda kalıcı bir hafıza tekniği (mnemonic) oluştur.

Konu: {subject}
Soru: {question_text}
Doğru Cevap: {correct_answer}

Kurallar:
1. Türkçe yaz
2. Kısa tut (1-3 cümle)
3. Görsel imgelem, kafiye veya kısaltma kullan
4. Öğrencinin doğru cevabı hatırlamasına yardımcı ol
5. Kavramı basitleştir

Hafıza İpucu:"""


async def batch_generate_mnemonics(
    *,
    db: AsyncSession,
    subject: str,
    limit: int = 100,
) -> dict:
    """Generate mnemonics for the most-missed questions without hints.

    This is a batch job — should be run via Celery task.
    Prioritizes questions with high error rates.
    """
    # Find questions without mnemonics, ordered by error frequency
    # (proxy: random for now, will use error_type counts when available)
    from sqlalchemy import func as sa_func

    # Note: mnemonic_hint and is_active columns not in DB yet
    # NOT: select(...).tablesample() SQLAlchemy 2.0'da YOK — postgresql dalı
    # AttributeError ile patlıyordu. func.random() her iki dialect'te de çalışır
    # (bkz offline_sync_service.py:112).
    result = await db.execute(
        select(QuestionBankItem.id)
        .select_from(QuestionBankItem)
        .join(QuestionMetadata, QuestionMetadata.id == QuestionBankItem.id)
        .where(
            QuestionMetadata.subject_area == subject.upper(),
        )
        .order_by(sa_func.random())
        .limit(limit)
    )
    question_ids = [r[0] for r in result.all()]

    generated = 0
    failed = 0
    for qid in question_ids:
        # Ayrı ad: `result` yukarıda SQLAlchemy `Result`; aynı adı dict ile
        # ezmek mypy'da 3 hata üretiyordu (HEAD'de de vardı).
        outcome = await generate_mnemonic(db=db, question_id=str(qid))
        if outcome.get("generated"):
            generated += 1
        elif outcome.get("error"):
            failed += 1

    return {
        "subject": subject,
        "attempted": len(question_ids),
        "generated": generated,
        "failed": failed,
    }
