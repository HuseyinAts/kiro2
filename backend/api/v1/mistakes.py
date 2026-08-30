from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from algorithms.isomorphic_generator import IsomorphicGenerator
from core.dependencies import get_db
from models.fsrs_models import FSRSCard

router = APIRouter(prefix="/api/v1/mistakes", tags=["mistakes", "fsrs"])


@router.get("/due")
async def get_due_mistakes(student_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the FSRSCards (mistakes) that are due for review for a given student.
    Uses IsomorphicGenerator to present a fresh variation of the question.
    """
    now_utc = datetime.now(UTC)

    # Query FSRS cards that belong to student and are due or overdue
    query = (
        select(FSRSCard)
        .where(and_(FSRSCard.student_id == student_id, FSRSCard.due_date <= now_utc))
        .limit(20)
    )  # Max 20 reviews per session

    result = await db.execute(query)
    cards = result.scalars().all()

    due_questions = []
    for card in cards:
        # Reconstruct a generic "question" structure from the card
        # In a full system, you would fetch the original question ID
        # from card.cultural_factors["original_question_id"] and merge options
        original_question = {
            "id": card.id,  # We use card ID to submit answers later
            "content": card.front_text,
            "options": [
                {"letter": "A", "text": "10"},
                {"letter": "B", "text": "20"},
                {"letter": "C", "text": "30"},
                {"letter": "D", "text": "40"},
                {"letter": "E", "text": "50"},
            ],
            "subject": card.subject_area.name if card.subject_area else "MAT",
        }

        # Pass it through the IsomorphicGenerator so it's fresh.
        # NOT: IsomorphicGenerator henuz bir LLM/matematik motoru degil (kendi
        # docstring'i bunu "placeholder" olarak isaretliyor) -- sayisal bir
        # soruda content'teki sayilar degistiginde, secenekler YENIDEN
        # hesaplanmiyor, sadece rastgele kaydiriliyor ("mock simulation").
        # Yani donen secenekler arasinda dogru cevap olmayabilir. Bu endpoint
        # şu an hicbir frontend tarafindan tuketilmiyor (orphan router,
        # bu commit'le sadece kayit ediliyor) -- bir istemci baglanmadan once
        # bu sinirlama ya duzeltilmeli ya da UI'da acikca isaretlenmeli.
        iso_question = IsomorphicGenerator.generate_isomorphic_question(
            original_question
        )
        due_questions.append(iso_question)

    return {
        "status": "success",
        "count": len(due_questions),
        "due_questions": due_questions,
    }
