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
                "SELECT COUNT(*) FROM questions"
            )

            # By exam type
            by_exam_type = await conn.fetch(
                "SELECT exam_type, COUNT(*) as count FROM questions WHERE exam_type IS NOT NULL GROUP BY exam_type"
            )

            # By subject
            by_subject = await conn.fetch(
                "SELECT subject, COUNT(*) as count FROM questions WHERE subject IS NOT NULL GROUP BY subject ORDER BY count DESC"
            )

            # By year
            by_year = await conn.fetch(
                "SELECT year, COUNT(*) as count FROM questions WHERE year IS NOT NULL GROUP BY year ORDER BY year DESC"
            )

            # With answers (correct_option is the column name in schema)
            with_answers = await conn.fetchval(
                "SELECT COUNT(*) FROM questions WHERE correct_option IS NOT NULL"
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
                    "by_subject": {row["subject"]: row["count"] for row in by_subject},
                    "by_year": {
                        row["year"]: row["count"] for row in by_year if row["year"]
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
                    SELECT subject, COUNT(*) as count
                    FROM questions
                    WHERE exam_type = $1 AND subject IS NOT NULL
                    GROUP BY subject
                    ORDER BY count DESC
                    """,
                    exam_type.upper(),
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT subject, COUNT(*) as count
                    FROM questions
                    WHERE subject IS NOT NULL
                    GROUP BY subject
                    ORDER BY count DESC
                    """
                )

            subjects = [
                {"subject": row["subject"], "question_count": row["count"]}
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
                conditions.append(f"subject = ${param_counter}")
                params.append(subject)
                param_counter += 1

            if exam_type:
                conditions.append(f"exam_type = ${param_counter}")
                params.append(exam_type.upper())
                param_counter += 1

            if difficulty:
                conditions.append(f"CAST(difficulty AS NUMERIC) = ${param_counter}")
                params.append(float(difficulty))
                param_counter += 1

            where_clause = " AND ".join(conditions)

            # Get all matching questions (using correct column names)
            query = f"""
                SELECT id, subject, topic, difficulty, exam_type,
                       stem, options, correct_option, year
                FROM questions
                WHERE {where_clause}
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
                q = {
                    "question_id": str(row["question_id"]),
                    "subject": row["subject"],
                    "topic": row["topic"],
                    "difficulty": row["difficulty"],
                    "exam_type": row["exam_type"],
                    "stem": row["stem"],
                    "options": json.loads(row["options"])
                    if isinstance(row["options"], str)
                    else row["options"],
                    "year": row["year"],
                    "quality_score": 10.0,
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
                    {"subject": "Turkce", "count": 40},
                    {"subject": "Matematik", "count": 40},
                    {"subject": "Fen Bilimleri", "count": 20},
                    {"subject": "Sosyal Bilimler", "count": 20},
                ]
            else:
                sections = [
                    {"subject": "Matematik", "count": 40},
                    {"subject": "Fizik", "count": 14},
                    {"subject": "Kimya", "count": 13},
                    {"subject": "Biyoloji", "count": 13},
                ]

            total_questions = 0

            for section in sections:
                # Build query
                if year:
                    rows = await conn.fetch(
                        """
                        SELECT question_id, stem, options, difficulty, year
                        FROM questions
                        WHERE source = 'ÖSYM' AND exam_type = $1 AND subject = $2 AND year = $3
                        """,
                        exam_type.upper(),
                        section["subject"],
                        year,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT question_id, stem, options, difficulty, year
                        FROM questions
                        WHERE source = 'ÖSYM' AND exam_type = $1 AND subject = $2
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
                            "question_id": str(row["question_id"]),
                            "stem": row["stem"],
                            "options": json.loads(row["options"])
                            if isinstance(row["options"], str)
                            else row["options"],
                            "difficulty": row["difficulty"],
                            "year": row["year"],
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
            conditions = ["source = 'ÖSYM'"]
            params = []
            param_counter = 1

            if subject:
                conditions.append(f"subject = ${param_counter}")
                params.append(subject)
                param_counter += 1

            if exam_type:
                conditions.append(f"exam_type = ${param_counter}")
                params.append(exam_type.upper())
                param_counter += 1

            if year:
                conditions.append(f"year = ${param_counter}")
                params.append(year)
                param_counter += 1

            if difficulty:
                conditions.append(f"difficulty = ${param_counter}")
                params.append(difficulty)
                param_counter += 1

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT question_id, subject, topic, difficulty, exam_type,
                       stem, options, correct_answer, year, quality_score
                FROM questions
                WHERE {where_clause}
                LIMIT ${param_counter} OFFSET ${param_counter + 1}
            """

            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            questions = []
            for row in rows:
                questions.append(
                    {
                        "question_id": str(row["question_id"]),
                        "subject": row["subject"],
                        "topic": row["topic"],
                        "difficulty": row["difficulty"],
                        "exam_type": row["exam_type"],
                        "stem": row["stem"],
                        "options": json.loads(row["options"])
                        if isinstance(row["options"], str)
                        else row["options"],
                        "correct_answer": row["correct_answer"],
                        "year": row["year"],
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
