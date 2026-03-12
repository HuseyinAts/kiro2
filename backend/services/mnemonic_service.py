"""
Mnemonic Hints Service — F19
AI-generated Turkish memory aids for frequently-missed questions.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.structured_logger import get_logger
from models.question_bank import QuestionBankItem

logger = get_logger("mnemonic_service")


async def get_mnemonic(
    *,
    db: AsyncSession,
    question_id: str,
) -> Optional[dict]:
    """Get the mnemonic hint for a question, if available."""
    result = await db.execute(
        select(
            QuestionBankItem.id,
            QuestionBankItem.mnemonic_hint,
            QuestionBankItem.question_text,
            QuestionBankItem.subject_area,
        ).where(
            QuestionBankItem.id == question_id,
            QuestionBankItem.is_active == True,  # noqa: E712
        )
    )
    row = result.first()

    if not row:
        return None

    return {
        "question_id": str(row.id),
        "mnemonic_hint": row.mnemonic_hint,
        "has_mnemonic": row.mnemonic_hint is not None,
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
    # Get the question
    result = await db.execute(
        select(QuestionBankItem).where(
            QuestionBankItem.id == question_id,
            QuestionBankItem.is_active == True,  # noqa: E712
        )
    )
    question = result.scalar_one_or_none()

    if not question:
        return {"error": "Soru bulunamadı"}

    if question.mnemonic_hint and not force:
        return {
            "question_id": str(question.id),
            "mnemonic_hint": question.mnemonic_hint,
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

        # Store the hint
        question.mnemonic_hint = hint
        await db.flush()

        return {
            "question_id": str(question.id),
            "mnemonic_hint": hint,
            "generated": True,
        }
    except Exception as e:
        logger.error(f"Mnemonic generation failed: {e}")
        return {"error": f"Mnemonic üretilemedi: {str(e)}"}


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

    result = await db.execute(
        select(QuestionBankItem.id)
        .where(
            QuestionBankItem.is_active == True,  # noqa: E712
            QuestionBankItem.subject_area == subject.upper(),
            QuestionBankItem.mnemonic_hint.is_(None),
        )
        .order_by(sa_func.random())
        .limit(limit)
    )
    question_ids = [r[0] for r in result.all()]

    generated = 0
    failed = 0
    for qid in question_ids:
        result = await generate_mnemonic(db=db, question_id=str(qid))
        if result.get("generated"):
            generated += 1
        elif result.get("error"):
            failed += 1

    return {
        "subject": subject,
        "attempted": len(question_ids),
        "generated": generated,
        "failed": failed,
    }
