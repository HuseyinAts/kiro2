"""
Questions API Endpoints
KIRO2 Soru Bankası REST API

Endpoints:
- GET /api/questions - Tüm soruları listele (filtreleme destekli)
- GET /api/questions/{id} - Tek soru detayı
- GET /api/questions/stats - İstatistikler
- GET /api/questions/random - Rastgele soru
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/questions", tags=["questions"])

# Database connection config
DB_CONFIG = {
    "host": "localhost",
    "port": 5434,
    "database": "turkiye_sinav_db",
    "user": "postgres",
    "password": "1470"
}

# Pydantic models
class Question(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    option_e: str
    correct_answer: str
    explanation: Optional[str]
    exam_type: str
    subject: str
    topic: str
    difficulty: float
    discrimination: float
    guessing: float
    created_at: datetime

class QuestionStats(BaseModel):
    total_questions: int
    exam_type_distribution: dict
    subject_distribution: dict
    difficulty_distribution: dict
    irt_averages: dict

def get_db_connection():
    """PostgreSQL bağlantısı oluştur"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@router.get("/", response_model=dict)
async def get_questions(
    exam_type: Optional[str] = Query(None, description="Sınav tipi (TYT, AYT, YDT)"),
    subject: Optional[str] = Query(None, description="Konu"),
    topic: Optional[str] = Query(None, description="Alt konu"),
    min_difficulty: Optional[float] = Query(None, description="Minimum zorluk"),
    max_difficulty: Optional[float] = Query(None, description="Maximum zorluk"),
    limit: Optional[int] = Query(100, description="Maksimum sonuç sayısı"),
    offset: Optional[int] = Query(0, description="Başlangıç offset")
):
    """
    Soruları listele (filtreleme desteğiyle)

    Örnek:
    - /api/questions
    - /api/questions?exam_type=TYT
    - /api/questions?subject=Matematik&limit=20
    - /api/questions?min_difficulty=0.3&max_difficulty=0.7
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Base query - using sorular table with Turkish column names
        query = """
            SELECT
                id,
                metin as question_text,
                secenekler->>'A' as option_a,
                secenekler->>'B' as option_b,
                secenekler->>'C' as option_c,
                secenekler->>'D' as option_d,
                secenekler->>'E' as option_e,
                dogru_cevap as correct_answer,
                sinav_tipi as exam_type,
                konu as subject,
                konu as topic,
                zorluk as difficulty,
                irt_discrimination as discrimination,
                irt_difficulty,
                irt_guessing as guessing,
                olusturma_tarihi as created_at
            FROM sorular
            WHERE aktif = true
        """
        params = []

        # Filters
        if exam_type:
            query += " AND sinav_tipi = %s"
            params.append(exam_type)

        if subject:
            query += " AND konu ILIKE %s"
            params.append(f"%{subject}%")

        if topic:
            query += " AND konu ILIKE %s"
            params.append(f"%{topic}%")

        if min_difficulty is not None:
            query += " AND difficulty >= %s"
            params.append(min_difficulty)

        if max_difficulty is not None:
            query += " AND difficulty <= %s"
            params.append(max_difficulty)

        # Order and pagination
        query += " ORDER BY id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        questions = cursor.fetchall()

        # Total count
        count_query = "SELECT COUNT(*) FROM sorular WHERE aktif = true"
        count_params = []

        if exam_type:
            count_query += " AND sinav_tipi = %s"
            count_params.append(exam_type)

        if subject:
            count_query += " AND konu ILIKE %s"
            count_params.append(f"%{subject}%")

        if topic:
            count_query += " AND konu ILIKE %s"
            count_params.append(f"%{topic}%")

        if min_difficulty is not None:
            count_query += " AND difficulty >= %s"
            count_params.append(min_difficulty)

        if max_difficulty is not None:
            count_query += " AND difficulty <= %s"
            count_params.append(max_difficulty)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "questions": [dict(q) for q in questions]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{question_id}", response_model=Question)
async def get_question_by_id(question_id: int):
    """
    ID'ye göre tek soru getir

    Örnek: /api/questions/1
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                metin as question_text,
                secenekler->>'A' as option_a,
                secenekler->>'B' as option_b,
                secenekler->>'C' as option_c,
                secenekler->>'D' as option_d,
                secenekler->>'E' as option_e,
                dogru_cevap as correct_answer,
                sinav_tipi as exam_type,
                konu as subject,
                konu as topic,
                zorluk as difficulty,
                irt_discrimination as discrimination,
                irt_difficulty,
                irt_guessing as guessing,
                olusturma_tarihi as created_at
            FROM sorular
            WHERE id = %s AND aktif = true
        """, (question_id,))
        question = cursor.fetchone()

        cursor.close()
        conn.close()

        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")

        return dict(question)

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/random/one")
async def get_random_question(
    exam_type: Optional[str] = Query(None),
    subject: Optional[str] = Query(None)
):
    """
    Rastgele bir soru getir

    Örnek:
    - /api/questions/random/one
    - /api/questions/random/one?exam_type=TYT
    - /api/questions/random/one?exam_type=AYT&subject=Matematik
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                id,
                metin as question_text,
                secenekler->>'A' as option_a,
                secenekler->>'B' as option_b,
                secenekler->>'C' as option_c,
                secenekler->>'D' as option_d,
                secenekler->>'E' as option_e,
                dogru_cevap as correct_answer,
                sinav_tipi as exam_type,
                konu as subject,
                konu as topic,
                zorluk as difficulty,
                irt_discrimination as discrimination,
                irt_difficulty,
                irt_guessing as guessing,
                olusturma_tarihi as created_at
            FROM sorular
            WHERE aktif = true
        """
        params = []

        if exam_type:
            query += " AND sinav_tipi = %s"
            params.append(exam_type)

        if subject:
            query += " AND konu ILIKE %s"
            params.append(f"%{subject}%")

        query += " ORDER BY RANDOM() LIMIT 1"

        cursor.execute(query, params)
        question = cursor.fetchone()

        cursor.close()
        conn.close()

        if not question:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")

        return dict(question)

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/stats/summary", response_model=QuestionStats)
async def get_question_stats():
    """
    Soru bankası istatistikleri

    Returns:
    - Toplam soru sayısı
    - Sınav tipi dağılımı
    - Konu dağılımı
    - Zorluk dağılımı
    - IRT ortalama değerleri
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total questions
        cursor.execute("SELECT COUNT(*) as count FROM sorular WHERE aktif = true")
        total = cursor.fetchone()['count']

        # Exam type distribution
        cursor.execute("""
            SELECT sinav_tipi as exam_type, COUNT(*) as count
            FROM sorular
            WHERE aktif = true
            GROUP BY sinav_tipi
        """)
        exam_type_dist = {row['exam_type']: row['count'] for row in cursor.fetchall()}

        # Subject distribution
        cursor.execute("""
            SELECT konu as subject, COUNT(*) as count
            FROM sorular
            WHERE aktif = true
            GROUP BY konu
            ORDER BY count DESC
        """)
        subject_dist = {row['subject']: row['count'] for row in cursor.fetchall()}

        # Difficulty distribution
        cursor.execute("""
            SELECT
                zorluk as level,
                COUNT(*) as count
            FROM sorular
            WHERE aktif = true
            GROUP BY zorluk
        """)
        difficulty_dist = {row['level']: row['count'] for row in cursor.fetchall()}

        # IRT averages
        cursor.execute("""
            SELECT
                AVG(irt_difficulty) as avg_difficulty,
                AVG(irt_discrimination) as avg_discrimination,
                AVG(irt_guessing) as avg_guessing
            FROM sorular
            WHERE aktif = true
        """)
        irt_avg = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "total_questions": total,
            "exam_type_distribution": exam_type_dist,
            "subject_distribution": subject_dist,
            "difficulty_distribution": difficulty_dist,
            "irt_averages": {
                "difficulty": float(irt_avg['avg_difficulty']) if irt_avg['avg_difficulty'] is not None else 0.0,
                "discrimination": float(irt_avg['avg_discrimination']) if irt_avg['avg_discrimination'] is not None else 0.0,
                "guessing": float(irt_avg['avg_guessing']) if irt_avg['avg_guessing'] is not None else 0.25
            }
        }

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/subjects/list")
async def get_subjects():
    """
    Tüm konuları listele

    Returns: List of unique subjects
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT konu as subject, COUNT(*) as count
            FROM sorular
            WHERE aktif = true
            GROUP BY konu
            ORDER BY konu
        """)
        subjects = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "subjects": [dict(s) for s in subjects]
        }

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/topics/list")
async def get_topics(subject: Optional[str] = Query(None)):
    """
    Alt konuları listele

    Örnek:
    - /api/questions/topics/list
    - /api/questions/topics/list?subject=Matematik
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if subject:
            cursor.execute("""
                SELECT DISTINCT alt_konu as topic, COUNT(*) as count
                FROM sorular
                WHERE aktif = true AND konu ILIKE %s
                GROUP BY alt_konu
                ORDER BY alt_konu
            """, (f"%{subject}%",))
        else:
            cursor.execute("""
                SELECT DISTINCT alt_konu as topic, konu as subject, COUNT(*) as count
                FROM sorular
                WHERE aktif = true
                GROUP BY alt_konu, konu
                ORDER BY konu, alt_konu
            """)

        topics = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "topics": [dict(t) for t in topics]
        }

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
