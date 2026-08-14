import contextlib
import random
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from algorithms.test_assembly import YksBellCurveAssembler
from core.dependencies import get_db
from models.enums_db import ExamType, SubjectArea
from models.exam_db import ExamQuestion, ExamSession, StudentAnswer
from models.question_bank import QuestionBankItem, QuestionStatistics, TopicHierarchy
from models.user_models import User
from services.accessibility.bionic_reading import BionicReadingConverter
from services.leaderboard_service import leaderboard_service

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])

TYT_BLUEPRINT = {
    "TUR": 40,
    "MAT": 40,  # Covers Math + Geo
    "SOS": 20,  # Covers History, Geography, Philosophy, Religion
    "FEN": 20,  # Covers Physics, Chemistry, Biology
}

# Mapping blueprint keys to actual topic codes in DB (based on Level 1 codes)
SUBJECT_MAPPING = {
    "TUR": ["TUR", "TYT-TR-01", "TYT-TR-02"],
    "MAT": ["MAT", "GEO", "TYT-MAT-01"],
    "SOS": ["TAR", "COG", "SOC01", "TYT-COG-01", "SOS"],
    "FEN": ["FIZ", "KIM", "BIY", "FEN", "TYT-FIZ-01", "TYT-KIM-01", "TYT-BIY-01"],
}


class GenerateMockRequest(BaseModel):
    student_id: str
    organization_id: str | None = "org_legacy_default"


class AnswerQuestionRequest(BaseModel):
    question_id: str
    selected_answer: str | None = None
    response_time_seconds: float | None = 0.0


class SubmitExamRequest(BaseModel):
    time_spent_seconds: int | None = 0


# question_statistics.difficulty_level Ingilizce enum tutar (very_easy..very_hard),
# YksBellCurveAssembler ise Turkce anahtar bekler. Eksik/taninmayan deger "orta".
_ZORLUK_BY_DIFFICULTY = {
    "very_easy": "cok_kolay",
    "easy": "kolay",
    "medium": "orta",
    "hard": "zor",
    "very_hard": "cok_zor",
}

# TYT sira araliklari -> brans. Uc ayri yerde tekrarlaniyordu.
_BRANCH_RANGES = ((40, "TUR"), (60, "SOS"), (100, "MAT"))

# Brans kodu -> SubjectArea. Enum uyeleri Turkce (SubjectArea["MAT"] KeyError verir);
# onceki `except KeyError: SubjectArea.MAT` fallback'i de var olmayan uyeye bakiyordu.
_SUBJECT_BY_BRANCH = {
    "TUR": SubjectArea.TURKCE,
    "SOS": SubjectArea.SOSYAL,
    "MAT": SubjectArea.MATEMATIK,
    "FEN": SubjectArea.FEN,
}


def _zorluk(difficulty: object) -> str:
    """QuestionDifficultyLevel -> assembler'in bekledigi Turkce zorluk anahtari."""
    raw = getattr(difficulty, "value", difficulty)
    if not raw:
        return "orta"
    return _ZORLUK_BY_DIFFICULTY.get(str(raw).lower(), "orta")


def _branch_for_order(question_order: int) -> str:
    """TYT soru sirasindan brans kodunu turet (1-40 TUR, 41-60 SOS, 61-100 MAT, 101+ FEN)."""
    for upper, branch in _BRANCH_RANGES:
        if question_order <= upper:
            return branch
    return "FEN"


def _score_answers(
    session: ExamSession, answers_map: dict
) -> tuple[int, int, int, dict[str, dict[str, float]]]:
    """Oturumu puanla; (dogru, yanlis, bos, brans_kirilimi) dondur.

    Yan etki: her StudentAnswer'in `is_correct` alanini gunceller.
    """
    totals = {"correct": 0, "wrong": 0, "empty": 0}
    branch_stats: dict[str, dict[str, float]] = {
        b: {"correct": 0, "wrong": 0, "empty": 0, "net": 0.0}
        for b in ("TUR", "SOS", "MAT", "FEN")
    }

    for eq in session.exam_questions:
        branch = _branch_for_order(eq.question_order)
        q = eq.question
        # correct_answer question_content'te; icerik yoksa soru puanlanamaz.
        correct_answer = getattr(q.content, "correct_answer", None) if q else None
        student_ans = answers_map.get(q.id if q else "")
        selected = student_ans.selected_answer if student_ans else None

        if not selected or not correct_answer:
            # Cevaplanmamis VEYA cevap anahtari eksik -> bos say (yanlis sayma).
            outcome = "empty"
        elif selected.strip().upper() == correct_answer.strip().upper():
            outcome = "correct"
        else:
            outcome = "wrong"

        totals[outcome] += 1
        branch_stats[branch][outcome] += 1
        if student_ans and outcome != "empty":
            student_ans.is_correct = outcome == "correct"

    for stats in branch_stats.values():
        stats["net"] = round(stats["correct"] - (stats["wrong"] * 0.25), 2)

    return totals["correct"], totals["wrong"], totals["empty"], branch_stats


def _build_fsrs_cards(session: ExamSession, answers_map: dict) -> list:
    """Yanlis/bos birakilan sorular icin FSRS tekrar karti uret.

    Cevap anahtari eksik olan soru yanlis SAYILMAZ (veri eksigi ogrencinin
    hatasi degil) — bu yuzden FSRS kuyruguna da girmez.
    """
    from datetime import timedelta

    from models.fsrs_models import FSRSCard

    cards = []
    for eq in session.exam_questions:
        q = eq.question
        content = q.content if q else None
        student_ans = answers_map.get(q.id if q else "")
        selected = student_ans.selected_answer if student_ans else None
        correct_answer = getattr(content, "correct_answer", None)

        if selected and not correct_answer:
            continue  # cevap anahtari yok -> yargilanamaz
        if selected and selected.strip().upper() == correct_answer.strip().upper():
            continue  # dogru
        if not q:
            continue

        solution = getattr(content, "explanation", None) or "Çözüm girilmemiş."
        cards.append(
            FSRSCard(
                organization_id=session.organization_id,
                student_id=session.student_id,
                front_text=getattr(content, "question_text", None)
                or "Soru metni bulunamadı",
                back_text=f"Doğru Cevap: {correct_answer or '-'}\nÇözüm: {solution}",
                subject_area=_SUBJECT_BY_BRANCH[_branch_for_order(eq.question_order)],
                topic=q.primary_topic_id or "Genel",
                state="new",
                due_date=datetime.now(UTC) + timedelta(days=1),
                cultural_factors={"original_question_id": q.id},
            )
        )
    return cards


def _options_from_content(content: object) -> list[dict[str, str]]:
    """QuestionContent'in option_a..option_e alanlarindan secenek listesi kur.

    Icerik yoksa veya secenekler bossa ornek seceneklere duser (UI bos kalmasin).
    """
    options = []
    for letter in ("A", "B", "C", "D", "E"):
        text = getattr(content, f"option_{letter.lower()}", None) if content else None
        if text:
            options.append({"letter": letter, "text": text})
    if options:
        return options
    return [
        {"letter": ltr, "text": f"Seçenek {ltr}"} for ltr in ("A", "B", "C", "D", "E")
    ]


@router.post("/generate-mock", status_code=status.HTTP_201_CREATED)
async def generate_mock_exam(
    req: GenerateMockRequest, db: AsyncSession = Depends(get_db)
):
    """
    Generates a full TYT Mock Exam (120 questions).
    """
    session = ExamSession(
        student_id=req.student_id,
        organization_id=req.organization_id or "org_legacy_default",
        exam_type=ExamType.TYT,
        exam_name="TYT Deneme Sınavı",
        total_questions=120,
        duration_minutes=165,
        status="in_progress",
        started_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()

    exam_questions_to_add = []
    current_order = 1

    for branch, count in TYT_BLUEPRINT.items():
        topic_codes = SUBJECT_MAPPING.get(branch, [])

        topics_query = await db.execute(
            select(TopicHierarchy.id).where(TopicHierarchy.code.in_(topic_codes))
        )
        topic_ids = [row[0] for row in topics_query.all()]

        selected_questions = []
        if topic_ids:
            questions_query = await db.execute(
                select(QuestionBankItem.id, QuestionStatistics.difficulty_level)
                .outerjoin(
                    QuestionStatistics, QuestionStatistics.id == QuestionBankItem.id
                )
                .where(
                    and_(
                        QuestionBankItem.is_active.is_(True),
                        QuestionBankItem.primary_topic_id.in_(topic_ids),
                    )
                )
            )

            # Create the pool for the assembler
            pool = [
                {"id": row[0], "zorluk": _zorluk(row[1])}
                for row in questions_query.all()
            ]

            # Assemble the test for this branch using Bell Curve
            assembled = YksBellCurveAssembler.assemble_test(pool, count)
            selected_questions = [q["id"] for q in assembled]

        # Fallback if topic questions count is smaller than blueprint requirement
        if len(selected_questions) < count:
            remaining = count - len(selected_questions)
            fallback_query = await db.execute(
                select(QuestionBankItem.id, QuestionStatistics.difficulty_level)
                .outerjoin(
                    QuestionStatistics, QuestionStatistics.id == QuestionBankItem.id
                )
                .where(
                    and_(
                        QuestionBankItem.is_active.is_(True),
                        # true(): ciplak Python True SQL ifadesi degil (mypy arg-type)
                        QuestionBankItem.id.not_in(selected_questions)
                        if selected_questions
                        else true(),
                    )
                )
            )
            fallback_pool = [
                {"id": row[0], "zorluk": _zorluk(row[1])}
                for row in fallback_query.all()
            ]

            # Get the remaining questions needed, preserving as much curve as possible
            fallback_assembled = YksBellCurveAssembler.assemble_test(
                fallback_pool, remaining
            )
            fallback_ids = [q["id"] for q in fallback_assembled]
            selected_questions.extend(fallback_ids)

        for qid in selected_questions:
            exam_questions_to_add.append(
                ExamQuestion(
                    exam_session_id=session.id,
                    question_id=qid,
                    question_order=current_order,
                )
            )
            current_order += 1

    db.add_all(exam_questions_to_add)
    session.total_questions = len(exam_questions_to_add)

    await db.commit()
    await db.refresh(session)

    return {
        "status": "success",
        "exam_session_id": session.id,
        "total_questions": session.total_questions,
    }


@router.get("/{session_id}")
async def get_exam_session(
    session_id: str, bionic_reading: bool = False, db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the exam session with ordered questions and current student answers.
    """
    result = await db.execute(
        select(ExamSession)
        .where(ExamSession.id == session_id)
        .options(
            selectinload(ExamSession.exam_questions)
            .selectinload(ExamQuestion.question)
            .selectinload(QuestionBankItem.content),
            selectinload(ExamSession.student_answers),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam session not found"
        )

    answers_map = {
        ans.question_id: ans.selected_answer for ans in session.student_answers
    }

    questions_data = []
    sorted_eq = sorted(session.exam_questions, key=lambda eq: eq.question_order)
    for eq in sorted_eq:
        q = eq.question
        # Soru metni/secenekleri question_bank'ta DEGIL, question_content'te.
        content = q.content if q else None
        text = (
            getattr(content, "question_text", None) or f"Örnek soru {eq.question_order}"
        )
        if bionic_reading:
            text = BionicReadingConverter.convert_text(text)

        questions_data.append(
            {
                "id": q.id if q else f"dummy-{eq.question_order}",
                "order": eq.question_order,
                "text": text,
                "options": _options_from_content(content),
                "branch": _branch_for_order(eq.question_order),
                "selected_answer": answers_map.get(q.id if q else ""),
            }
        )

    return {
        "id": session.id,
        "exam_name": session.exam_name,
        "exam_type": session.exam_type,
        "total_questions": session.total_questions,
        "duration_minutes": session.duration_minutes,
        "status": session.status,
        "questions": questions_data,
    }


@router.post("/{session_id}/answer")
async def save_answer(
    session_id: str, req: AnswerQuestionRequest, db: AsyncSession = Depends(get_db)
):
    """
    Saves or updates a candidate's answer for a specific question in real-time.
    """
    session_res = await db.execute(
        select(ExamSession).where(ExamSession.id == session_id)
    )
    session = session_res.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam session not found"
        )

    ans_res = await db.execute(
        select(StudentAnswer).where(
            and_(
                StudentAnswer.exam_session_id == session_id,
                StudentAnswer.question_id == req.question_id,
            )
        )
    )
    student_ans = ans_res.scalar_one_or_none()

    if student_ans:
        student_ans.selected_answer = req.selected_answer
        student_ans.response_time_seconds += req.response_time_seconds or 0.0
        student_ans.answer_changes += 1
    else:
        student_ans = StudentAnswer(
            exam_session_id=session_id,
            question_id=req.question_id,
            selected_answer=req.selected_answer,
            response_time_seconds=req.response_time_seconds or 0.0,
        )
        db.add(student_ans)

    await db.commit()
    return {
        "status": "success",
        "question_id": req.question_id,
        "selected_answer": req.selected_answer,
    }


@router.post("/{session_id}/submit")
async def submit_exam(
    session_id: str, req: SubmitExamRequest, db: AsyncSession = Depends(get_db)
):
    """
    Finalizes the exam session, calculates scores and branch breakdowns, and returns results.
    """
    result = await db.execute(
        select(ExamSession)
        .where(ExamSession.id == session_id)
        .options(
            selectinload(ExamSession.exam_questions)
            .selectinload(ExamQuestion.question)
            .selectinload(QuestionBankItem.content),
            selectinload(ExamSession.student_answers),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Exam session not found"
        )

    answers_map = {ans.question_id: ans for ans in session.student_answers}

    total_correct, total_wrong, total_empty, branch_stats = _score_answers(
        session, answers_map
    )
    raw_score = total_correct - (total_wrong * 0.25)

    session.status = "completed"
    session.completed_at = datetime.now(UTC)
    session.total_correct = total_correct
    session.total_wrong = total_wrong
    session.total_empty = total_empty
    session.raw_score = round(raw_score, 2)
    session.time_spent_seconds = req.time_spent_seconds or 0

    # --- FSRS MISTAKE TRACKING ---
    fsrs_cards_to_add = _build_fsrs_cards(session, answers_map)
    if fsrs_cards_to_add:
        db.add_all(fsrs_cards_to_add)

    # --- GAMIFICATION & ECONOMY ---
    total_questions = total_correct + total_wrong + total_empty
    score_percentage = (
        (total_correct / total_questions * 100) if total_questions > 0 else 0
    )
    xp_earned = 0
    coins_earned = 0
    # time_spent_seconds varsayilani 0; avg_time asagida kosulsuz okunuyor.
    # Onceden yalnizca if-govdesinde atanıyordu -> suresiz + >=%80 gonderimde
    # UnboundLocalError (500). Anti-cheat esigini gecemedigi icin 0.0 dogru varsayilan.
    avg_time = 0.0

    if total_questions > 0 and session.time_spent_seconds > 0:
        avg_time = session.time_spent_seconds / total_questions
        if avg_time >= 5.0:  # Anti-cheat: at least 5 seconds per question
            base_points = int(50 + (score_percentage / 100) * 50)
            question_bonus = min(total_questions * 2, 50)
            xp_earned = base_points + question_bonus

    if xp_earned > 0 or score_percentage >= 80:
        # Fetch user
        user = await db.scalar(select(User).where(User.id == session.student_id))
        if user:
            if xp_earned > 0:
                user.total_xp += xp_earned
                # update leaderboard — Redis yoksa sinav gonderimi dusmemeli
                with contextlib.suppress(Exception):
                    await leaderboard_service.add_xp(str(user.id), xp_earned)

            # RNG Loot drop if performance > 80%
            if score_percentage >= 80 and avg_time >= 5.0:
                # Oyunlastirma odulu — kriptografik amac yok
                coins_earned = random.randint(1, 3)  # noqa: S311  # nosec B311
                user.virtual_currency += coins_earned

    await db.commit()

    return {
        "status": "success",
        "session_id": session.id,
        "total_correct": total_correct,
        "total_wrong": total_wrong,
        "total_empty": total_empty,
        "raw_score": session.raw_score,
        "branch_breakdown": branch_stats,
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
    }
