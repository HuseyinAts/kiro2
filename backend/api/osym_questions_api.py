"""
OSYM Original Questions API Endpoints
Provides access to authentic OSYM exam questions
"""

import logging
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.cevap_kapisi import cevap_gorebilir, cevaplari_ele
from core.database import get_async_session as get_db
from core.dependencies import AuthenticatedUser, get_current_user
from core.quality_gate import safe_for_beta_sql

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/osym", tags=["OSYM Questions"])


@router.get("/statistics")
async def get_osym_statistics(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get OSYM question bank statistics"""
    try:
        total = (
            await db.execute(
                text("SELECT COUNT(*) FROM question_bank WHERE is_active = TRUE")
            )
        ).scalar()

        by_exam_type = (
            (
                await db.execute(
                    text(
                        "SELECT qm.exam_type, COUNT(*) as count FROM question_bank qb "
                        "JOIN question_metadata qm ON qm.id = qb.id "
                        "WHERE qm.exam_type IS NOT NULL AND qb.is_active = TRUE "
                        "GROUP BY qm.exam_type"
                    )
                )
            )
            .mappings()
            .all()
        )

        by_subject = (
            (
                await db.execute(
                    text(
                        "SELECT qm.subject_area, COUNT(*) as count "
                        "FROM question_bank qb "
                        "JOIN question_metadata qm ON qm.id = qb.id "
                        "WHERE qm.subject_area IS NOT NULL AND qb.is_active = TRUE "
                        "GROUP BY qm.subject_area ORDER BY count DESC"
                    )
                )
            )
            .mappings()
            .all()
        )

        by_year = (
            (
                await db.execute(
                    text(
                        "SELECT qm.osym_year, COUNT(*) as count FROM question_bank qb "
                        "JOIN question_metadata qm ON qm.id = qb.id "
                        "WHERE qm.osym_year IS NOT NULL AND qb.is_active = TRUE "
                        "GROUP BY qm.osym_year ORDER BY qm.osym_year DESC"
                    )
                )
            )
            .mappings()
            .all()
        )

        with_answers = (
            await db.execute(
                text(
                    "SELECT COUNT(*) FROM question_bank qb "
                    "JOIN question_content qc ON qc.id = qb.id "
                    "WHERE qc.correct_answer IS NOT NULL AND qb.is_active = TRUE"
                )
            )
        ).scalar()

        return {
            "success": True,
            "data": {
                "total_questions": total,
                "with_answers": with_answers,
                "without_answers": total - with_answers,
                "by_exam_type": {
                    row["exam_type"]: row["count"] for row in by_exam_type
                },
                "by_subject": {row["subject_area"]: row["count"] for row in by_subject},
                "by_year": {
                    row["osym_year"]: row["count"]
                    for row in by_year
                    if row["osym_year"]
                },
                "quality_score": 10.0,
                "source": "OSYM Official",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OSYM API Error: {e!s}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/subjects")
async def get_available_subjects(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    exam_type: str | None = Query(None),
):
    """Get list of available subjects"""
    try:
        if exam_type:
            result = await db.execute(
                text(
                    "SELECT qm.subject_area, COUNT(*) as count FROM question_bank qb "
                    "JOIN question_metadata qm ON qm.id = qb.id "
                    "WHERE qm.exam_type = :exam_type AND qm.subject_area IS NOT NULL "
                    "AND qb.is_active = TRUE "
                    "GROUP BY qm.subject_area ORDER BY count DESC"
                ),
                {"exam_type": exam_type.upper()},
            )
        else:
            result = await db.execute(
                text(
                    "SELECT qm.subject_area, COUNT(*) as count FROM question_bank qb "
                    "JOIN question_metadata qm ON qm.id = qb.id "
                    "WHERE qm.subject_area IS NOT NULL AND qb.is_active = TRUE "
                    "GROUP BY qm.subject_area ORDER BY count DESC"
                )
            )

        rows = result.mappings().all()
        subjects = [
            {"subject": row["subject_area"], "question_count": row["count"]}
            for row in rows
        ]

        return {"success": True, "data": subjects, "count": len(subjects)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OSYM API Error: {e!s}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/random-questions")
async def get_random_questions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    subject: str | None = Query(None),
    exam_type: str = Query("TYT"),
    count: int = Query(10, ge=1, le=40),
    difficulty: str | None = Query(None),
    with_answers: bool = Query(True),
):
    """Get random OSYM questions for practice"""
    try:
        conditions = ["qb.is_active = TRUE"]
        # Kalite kapısı (core/quality_gate.py) — kapısız sorgu 85.731
        # yargılanmamış/reddedilmiş soruyu öğrenciye servis ediyordu.
        conditions.append(safe_for_beta_sql("qb.id"))
        params: dict = {}

        if subject:
            conditions.append("qm.subject_area = :subject")
            params["subject"] = subject.upper()

        if exam_type:
            conditions.append("qm.exam_type = :exam_type")
            params["exam_type"] = exam_type.upper()

        if difficulty:
            conditions.append("qs.difficulty_level = :difficulty")
            params["difficulty"] = difficulty

        where_clause = " AND ".join(conditions)

        query = text(f"""
            SELECT qb.id, qm.subject_area, qs.difficulty_level, qm.exam_type,
                   qc.question_text, qc.option_a, qc.option_b, qc.option_c,
                   qc.option_d, qc.option_e,
                   qc.correct_answer, qm.osym_year, qs.quality_score
            FROM question_bank qb
            JOIN question_content qc ON qc.id = qb.id
            JOIN question_metadata qm ON qm.id = qb.id
            JOIN question_statistics qs ON qs.id = qb.id
            WHERE {where_clause}
        """)  # nosec B608 - f-string'e YALNIZCA kodun kendi sabit parcalari giriyor
        # (conditions listesi hardcoded kolon/operator dizeleri); tum kullanici
        # degerleri bagli parametre (:subject, :exam_type, vb.)

        rows = (await db.execute(query, params)).mappings().all()

        if not rows:
            return {
                "success": False,
                "data": [],
                "count": 0,
                "message": "No OSYM questions found",
            }

        selected_count = min(count, len(rows))
        selected = random.sample(list(rows), selected_count)

        questions = []
        for row in selected:
            options = {}
            for key in ["a", "b", "c", "d", "e"]:
                val = row.get(f"option_{key}")
                if val:
                    options[key.upper()] = val

            q = {
                "question_id": str(row["id"]),
                "subject": row["subject_area"],
                "difficulty": row["difficulty_level"],
                "exam_type": row["exam_type"],
                "stem": row["question_text"],
                "options": options,
                "year": row["osym_year"],
                "quality_score": float(row["quality_score"])
                if row["quality_score"]
                else 10.0,
            }

            # `with_answers` ISTEMCI kontrollu ve varsayilani True idi -> her ogrenci
            # cevap anahtarini okuyabiliyordu (S241, denetim B2). Bayrak artik yalnizca
            # yetkili rolun cevabi GORMEMEYI secmesine yarar; gormeye yetmez.
            if with_answers and cevap_gorebilir(current_user.role):
                q["correct_answer"] = row["correct_answer"]

            questions.append(q)

        return {
            "success": True,
            "data": questions,
            "count": len(questions),
            "message": f"Selected {len(questions)} random OSYM questions",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OSYM API Error: {e!s}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/practice-exam")
async def generate_practice_exam(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    exam_type: str = Query("TYT"),
    year: int | None = Query(None),
):
    """Generate a full OSYM practice exam"""
    try:
        practice_exam = {
            "exam_type": exam_type.upper(),
            "generated_at": datetime.now().isoformat(),
            "sections": [],
        }

        if exam_type.upper() == "TYT":
            sections = [
                {"subject": "TURKCE", "count": 40},
                {"subject": "MATEMATIK", "count": 40},
                {"subject": "FEN", "count": 20},
                {"subject": "SOSYAL", "count": 20},
            ]
        else:
            sections = [
                {"subject": "MATEMATIK", "count": 40},
                {"subject": "FIZIK", "count": 14},
                {"subject": "KIMYA", "count": 13},
                {"subject": "BIYOLOJI", "count": 13},
            ]

        total_questions = 0

        for section in sections:
            params: dict = {
                "exam_type": exam_type.upper(),
                "subject": section["subject"],
            }

            # Kalite kapısı (core/quality_gate.py) — kapısız sorgu 85.731
            # yargılanmamış/reddedilmiş soruyu öğrenciye servis ediyordu.
            _gate = f"AND {safe_for_beta_sql('qb.id')}"
            _joins = (
                "FROM question_bank qb "
                "JOIN question_content qc ON qc.id = qb.id "
                "JOIN question_metadata qm ON qm.id = qb.id "
                "JOIN question_statistics qs ON qs.id = qb.id "
            )

            if year:
                params["year"] = year
                result = await db.execute(
                    text(
                        # _gate/_joins sabit kod parçası, kullanıcı girdisi yok
                        "SELECT qb.id, qc.question_text, "
                        "qc.option_a, qc.option_b, qc.option_c, "
                        "qc.option_d, qc.option_e, qs.difficulty_level, qm.osym_year "
                        + _joins
                        + "WHERE qm.exam_type = :exam_type "
                        + "AND qm.subject_area = :subject "
                        "AND qm.osym_year = :year AND qb.is_active = TRUE " + _gate
                    ),
                    params,
                )
            else:
                result = await db.execute(
                    text(
                        # _gate/_joins sabit kod parçası, kullanıcı girdisi yok
                        "SELECT qb.id, qc.question_text, "
                        "qc.option_a, qc.option_b, qc.option_c, "
                        "qc.option_d, qc.option_e, qs.difficulty_level, qm.osym_year "
                        + _joins
                        + "WHERE qm.exam_type = :exam_type "
                        + "AND qm.subject_area = :subject "
                        "AND qb.is_active = TRUE " + _gate
                    ),
                    params,
                )

            rows = result.mappings().all()

            selected_count = min(section["count"], len(rows))
            selected = random.sample(list(rows), selected_count) if rows else []

            section_data = {
                "subject": section["subject"],
                "requested_count": section["count"],
                "actual_count": len(selected),
                "questions": [
                    {
                        "question_id": str(row["id"]),
                        "stem": row["question_text"],
                        "options": {
                            k.upper(): row[f"option_{k}"]
                            for k in ["a", "b", "c", "d", "e"]
                            if row.get(f"option_{k}")
                        },
                        "difficulty": row["difficulty_level"],
                        "year": row["osym_year"],
                    }
                    for row in selected
                ],
            }

            practice_exam["sections"].append(section_data)
            total_questions += len(selected)

        return {
            "success": True,
            "data": practice_exam,
            "total_questions": total_questions,
            "message": f"Generated {exam_type} practice exam with {total_questions} questions",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OSYM API Error: {e!s}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/questions")
async def get_questions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    subject: str | None = Query(None),
    exam_type: str | None = Query(None),
    year: int | None = Query(None),
    difficulty: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get OSYM questions with filters"""
    try:
        conditions = ["qb.is_active = TRUE"]
        # Kalite kapısı (core/quality_gate.py) — kapısız sorgu 85.731
        # yargılanmamış/reddedilmiş soruyu öğrenciye servis ediyordu.
        conditions.append(safe_for_beta_sql("qb.id"))
        params: dict = {"limit": limit, "offset": offset}

        if subject:
            conditions.append("qm.subject_area = :subject")
            params["subject"] = subject.upper()

        if exam_type:
            conditions.append("qm.exam_type = :exam_type")
            params["exam_type"] = exam_type.upper()

        if year:
            conditions.append("qm.osym_year = :year")
            params["year"] = year

        if difficulty:
            conditions.append("qs.difficulty_level = :difficulty")
            params["difficulty"] = difficulty

        where_clause = " AND ".join(conditions)

        query = text(f"""
            SELECT qb.id, qm.subject_area, qs.difficulty_level, qm.exam_type,
                   qc.question_text, qc.option_a, qc.option_b, qc.option_c,
                   qc.option_d, qc.option_e,
                   qc.correct_answer, qm.osym_year, qs.quality_score
            FROM question_bank qb
            JOIN question_content qc ON qc.id = qb.id
            JOIN question_metadata qm ON qm.id = qb.id
            JOIN question_statistics qs ON qs.id = qb.id
            WHERE {where_clause}
            LIMIT :limit OFFSET :offset
        """)  # nosec B608 - f-string'e YALNIZCA kodun kendi sabit parcalari giriyor
        # (conditions listesi hardcoded kolon/operator dizeleri); tum kullanici
        # degerleri bagli parametre (:subject, :exam_type, vb.)

        rows = (await db.execute(query, params)).mappings().all()

        questions = []
        for row in rows:
            options = {}
            for key in ["a", "b", "c", "d", "e"]:
                val = row.get(f"option_{key}")
                if val:
                    options[key.upper()] = val

            questions.append(
                {
                    "question_id": str(row["id"]),
                    "subject": row["subject_area"],
                    "difficulty": row["difficulty_level"],
                    "exam_type": row["exam_type"],
                    "stem": row["question_text"],
                    "options": options,
                    "correct_answer": row["correct_answer"],
                    "year": row["osym_year"],
                    "quality_score": float(row["quality_score"])
                    if row["quality_score"]
                    else 10.0,
                }
            )

        return {
            "success": True,
            # Cevap kapisi (S241, denetim B2): bu uc `correct_answer`i KOSULSUZ
            # doluruyordu -> duz ogrenci token'i cevap anahtarini okuyabiliyordu.
            "data": cevaplari_ele(questions, current_user.role),
            "count": len(questions),
            "message": f"Found {len(questions)} OSYM questions",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OSYM API Error: {e!s}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")
