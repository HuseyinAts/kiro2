"""Test database connection"""
import psycopg2
import os

# SECURITY FIX: PostgreSQL connection from environment variables
PG_CONN = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5434")),
    "database": os.getenv("DB_NAME", "turkiye_sinav_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")  # REQUIRED: Must be set via environment
}

try:
    print("Testing PostgreSQL connection...")
    conn = psycopg2.connect(**PG_CONN)
    print("Connection successful!")

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    print(f"Found {count} questions in database")

    cursor.close()
    conn.close()
    print("Test completed successfully!")

except Exception as e:
    print(f"Error: {e}")