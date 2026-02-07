"""
SQLite'tan PostgreSQL'e Emergency Content Migration
41 ÖSYM sorusunu taşır
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import json
import os

# Database bağlantıları
SQLITE_DB = "turkiye_sinav.db"
# SECURITY FIX: PostgreSQL connection from environment variables
PG_CONN = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "database": os.getenv("DB_NAME", "turkiye_sinav_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")  # REQUIRED: Must be set via environment
}

def migrate_questions():
    """SQLite'tan PostgreSQL'e soru migration'ı"""

    # SQLite'tan oku
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()

    print(f"✓ SQLite'tan {len(questions)} soru okundu")

    # PostgreSQL'e yaz
    pg_conn = psycopg2.connect(**PG_CONN)
    pg_cursor = pg_conn.cursor()

    # Önce tabloyu oluştur
    pg_cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id SERIAL PRIMARY KEY,
            question_text TEXT NOT NULL,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            option_d TEXT,
            option_e TEXT,
            correct_answer VARCHAR(1),
            explanation TEXT,
            exam_type VARCHAR(50),
            subject VARCHAR(100),
            topic VARCHAR(200),
            difficulty FLOAT,
            discrimination FLOAT,
            guessing FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    print("✓ PostgreSQL tablosu oluşturuldu")

    # Verileri kopyala
    insert_query = """
        INSERT INTO questions (
            question_text, option_a, option_b, option_c, option_d, option_e,
            correct_answer, explanation, exam_type, subject, topic,
            difficulty, discrimination, guessing
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = []
    for q in questions:
        data.append((
            q['question_text'],
            q['option_a'] or '',
            q['option_b'] or '',
            q['option_c'] or '',
            q['option_d'] or '',
            q['option_e'] or '',
            q['correct_answer'],
            q['explanation'] or '',
            q['exam_type'] or 'TYT',
            q['subject_area'] or 'Matematik',  # subject_area olarak değiştirildi
            q['topic'] or '',
            float(q['irt_difficulty'] or 0.0),  # irt_ prefix'i eklendi
            float(q['irt_discrimination'] or 1.2),
            float(q['irt_guessing'] or 0.25)
        ))

    execute_batch(pg_cursor, insert_query, data)
    pg_conn.commit()

    print(f"✓ {len(data)} soru PostgreSQL'e kopyalandı")

    # Doğrulama
    pg_cursor.execute("SELECT COUNT(*), exam_type FROM questions GROUP BY exam_type")
    results = pg_cursor.fetchall()

    print("\n📊 PostgreSQL Soru Dağılımı:")
    for count, exam_type in results:
        print(f"   {exam_type}: {count} soru")

    # Temizlik
    sqlite_conn.close()
    pg_cursor.close()
    pg_conn.close()

    print("\n✅ Migration tamamlandı!")

if __name__ == "__main__":
    try:
        migrate_questions()
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
