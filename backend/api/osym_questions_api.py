"""
OSYM Original Questions API Endpoints
Provides access to authentic OSYM exam questions
"""
from typing import Optional
from datetime import datetime
import random
import asyncpg
import json

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/osym", tags=["OSYM Questions"])


async def get_db():
    """Get database connection"""
    from core.config import settings
    import re

    # Parse connection string
    pattern = r"postgresql\+?.*://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
    match = re.match(pattern, settings.database_url)

    if match:
        conn = await asyncpg.connect(
            host=match.group(3),
            port=int(match.group(4)),
            user=match.group(1),
            password=match.group(2),
            database=match.group(5),
        )
        return conn
    raise HTTPException(500, "Database configuration error")


@router.get("/statistics")
async def get_osym_statistics():
    """Get OSYM question bank statistics"""
    try:
        conn = await get_db()

        try:
            # Total questions (removed ÖSYM filter to show all questions)
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM question_bank WHERE is_active = TRUE"
            )

            # By exam type
            by_exam_type = await conn.fetch(
                "SELECT exam_type, COUNT(*) as count FROM question_bank WHERE exam_type IS NOT NULL AND is_active = TRUE GROUP BY exam_type"
            )

            # By subject
            by_subject = await conn.fetch(
                "SELECT subject_area, COUNT(*) as count FROM question_bank WHERE subject_area IS NOT NULL AND is_active = TRUE GROUP BY subject_area ORDER BY count DESC"
            )

            # By year
            by_year = await conn.fetch(
                "SELECT osym_year, COUNT(*) as count FROM question_bank WHERE osym_year IS NOT NULL AND is_active = TRUE GROUP BY osym_year ORDER BY osym_year DESC"
            )

            # With answers
            with_answers = await conn.fetchval(
                "SELECT COUNT(*) FROM question_bank WHERE correct_answer IS NOT NULL AND is_active = TRUE"
            )

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
                        row["osym_year"]: row["count"] for row in by_year if row["osym_year"]
                    },
                    "quality_score": 10.0,
                    "source": "OSYM Official",
                },
            }

        finally:
            await conn.close()

    except Exception as e:
        import logging
        logging.error(f"OSYM API Error: {str(e)}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/subjects")
async def get_available_subjects(exam_type: Optional[str] = Query(None)):
    """Get list of available subjects"""
    try:
        conn = await get_db()

        try:
            if exam_type:
                rows = await conn.fetch(
                    """
                    SELECT subject_area, COUNT(*) as count
                    FROM question_bank
                    WHERE exam_type = $1 AND subject_area IS NOT NULL AND is_active = TRUE
                    GROUP BY subject_area
                    ORDER BY count DESC
                    """,
                    exam_type.upper(),
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT subject_area, COUNT(*) as count
                    FROM question_bank
                    WHERE subject_area IS NOT NULL AND is_active = TRUE
                    GROUP BY subject_area
                    ORDER BY count DESC
                    """
                )

            subjects = [
                {"subject": row["subject_area"], "question_count": row["count"]}
                for row in rows
            ]

            return {"success": True, "data": subjects, "count": len(subjects)}

        finally:
            await conn.close()

    except Exception as e:
        import logging
        logging.error(f"OSYM API Error: {str(e)}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/random-questions")
async def get_random_questions(
    subject: Optional[str] = Query(None),
    exam_type: str = Query("TYT"),
    count: int = Query(10, ge=1, le=40),
    difficulty: Optional[str] = Query(None),
    with_answers: bool = Query(True),
):
    """Get random OSYM questions for practice"""
    try:
        conn = await get_db()

        try:
            # Build query
            conditions = ["1=1"]  # Always true base condition
            params = []
            param_counter = 1

            if subject:
                conditions.append(f"subject_area = ${param_counter}")
                params.append(subject.upper())
                param_counter += 1

            if exam_type:
                conditions.append(f"exam_type = ${param_counter}")
                params.append(exam_type.upper())
                param_counter += 1

            if difficulty:
                conditions.append(f"difficulty_level = ${param_counter}")
                params.append(difficulty)
                param_counter += 1

            where_clause = " AND ".join(conditions)

            # Get all matching questions
            query = f"""
                SELECT id, subject_area, difficulty_level, exam_type,
                       question_text, option_a, option_b, option_c, option_d, option_e,
                       correct_answer, osym_year, quality_score
                FROM question_bank
                WHERE {where_clause} AND is_active = TRUE
            """

            rows = await conn.fetch(query, *params)

            if not rows:
                return {
                    "success": False,
                    "data": [],
                    "count": 0,
                    "message": "No OSYM questions found",
                }

            # Random sample
            selected_count = min(count, len(rows))
            selected = random.sample(list(rows), selected_count)

            # Format response
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
                    "quality_score": float(row["quality_score"]) if row["quality_score"] else 10.0,
                }

                if with_answers:
                    q["correct_answer"] = row["correct_answer"]

                questions.append(q)

            return {
                "success": True,
                "data": questions,
                "count": len(questions),
                "message": f"Selected {len(questions)} random OSYM questions",
            }

        finally:
            await conn.close()

    except Exception as e:
        import logging
        logging.error(f"OSYM API Error: {str(e)}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/practice-exam")
async def generate_practice_exam(
    exam_type: str = Query("TYT"), year: Optional[int] = Query(None)
):
    """Generate a full OSYM practice exam"""
    try:
        conn = await get_db()

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
                # Build query
                if year:
                    rows = await conn.fetch(
                        """
                        SELECT id, question_text, option_a, option_b, option_c, option_d, option_e,
                               difficulty_level, osym_year
                        FROM question_bank
                        WHERE exam_type = $1 AND subject_area = $2 AND osym_year = $3 AND is_active = TRUE
                        """,
                        exam_type.upper(),
                        section["subject"],
                        year,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, question_text, option_a, option_b, option_c, option_d, option_e,
                               difficulty_level, osym_year
                        FROM question_bank
                        WHERE exam_type = $1 AND subject_area = $2 AND is_active = TRUE
                        """,
                        exam_type.upper(),
                        section["subject"],
                    )

                # Random sample
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

        finally:
            await conn.close()

    except Exception as e:
        import logging
        logging.error(f"OSYM API Error: {str(e)}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")


@router.get("/questions")
async def get_questions(
    subject: Optional[str] = Query(None),
    exam_type: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    difficulty: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get OSYM questions with filters"""
    try:
        conn = await get_db()

        try:
            # Build query
            conditions = ["1=1"]
            params = []
            param_counter = 1

            if subject:
                conditions.append(f"subject_area = ${param_counter}")
                params.append(subject.upper())
                param_counter += 1

            if exam_type:
                conditions.append(f"exam_type = ${param_counter}")
                params.append(exam_type.upper())
                param_counter += 1

            if year:
                conditions.append(f"osym_year = ${param_counter}")
                params.append(year)
                param_counter += 1

            if difficulty:
                conditions.append(f"difficulty_level = ${param_counter}")
                params.append(difficulty)
                param_counter += 1

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT id, subject_area, difficulty_level, exam_type,
                       question_text, option_a, option_b, option_c, option_d, option_e,
                       correct_answer, osym_year, quality_score
                FROM question_bank
                WHERE {where_clause} AND is_active = TRUE
                LIMIT ${param_counter} OFFSET ${param_counter + 1}
            """

            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

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
                "data": questions,
                "count": len(questions),
                "message": f"Found {len(questions)} OSYM questions",
            }

        finally:
            await conn.close()

    except Exception as e:
        import logging
        logging.error(f"OSYM API Error: {str(e)}")
        raise HTTPException(500, "Soru bankası verilerine erişilirken bir hata oluştu")
