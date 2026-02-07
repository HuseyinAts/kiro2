#!/usr/bin/env python3
"""
Clean Questions Database Import Script

Bu script temizlenmiş ÖSYM sorularını PostgreSQL veritabanına yükler.

Author: Claude AI
Date: 2026-01-23
"""

import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "ai_training_data"
CLEAN_QUESTIONS_FILE = DATA_DIR / "osym_clean_questions.json"


async def get_database_url() -> str:
    """Get database URL from environment or config."""
    import os
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
    return os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:changeme@localhost:5434/kiro2_db"
    )


async def check_table_exists(session: AsyncSession, table_name: str) -> bool:
    """Check if a table exists in the database."""
    result = await session.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = :table_name
            )
        """),
        {"table_name": table_name}
    )
    return result.scalar()


async def create_sorular_table(session: AsyncSession):
    """Create sorular table if it doesn't exist."""
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS sorular (
            id UUID PRIMARY KEY,
            metin TEXT NOT NULL,
            secenekler JSONB NOT NULL,
            dogru_cevap VARCHAR(1) NOT NULL,
            ders VARCHAR(50) NOT NULL,
            konu VARCHAR(100),
            sinav_tipi VARCHAR(20) NOT NULL,
            zorluk VARCHAR(20) DEFAULT 'orta',
            yil INTEGER DEFAULT 2024,
            kalite VARCHAR(20) DEFAULT 'clean',
            kaynak VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    await session.commit()
    print("[OK] sorular tablosu oluşturuldu/kontrol edildi")


async def import_questions(session: AsyncSession, questions: list) -> dict:
    """Import questions into database."""
    stats = {
        'total': len(questions),
        'inserted': 0,
        'skipped': 0,
        'errors': 0,
    }

    for q in questions:
        try:
            # Check if question already exists
            result = await session.execute(
                text("SELECT id FROM sorular WHERE id = :id"),
                {"id": q['question_id']}
            )
            if result.fetchone():
                stats['skipped'] += 1
                continue

            # Insert question
            await session.execute(
                text("""
                    INSERT INTO sorular (
                        id, metin, secenekler, dogru_cevap, ders, konu,
                        sinav_tipi, zorluk, yil, kalite, kaynak
                    ) VALUES (
                        :id, :metin, :secenekler, :dogru_cevap, :ders, :konu,
                        :sinav_tipi, :zorluk, :yil, :kalite, :kaynak
                    )
                """),
                {
                    "id": q['question_id'],
                    "metin": q['stem'],
                    "secenekler": json.dumps(q['options'], ensure_ascii=False),
                    "dogru_cevap": q['correct_answer'],
                    "ders": q['subject'],
                    "konu": q.get('topic', 'Genel'),
                    "sinav_tipi": q['exam_type'],
                    "zorluk": q.get('difficulty', 'orta'),
                    "yil": q.get('year', 2024),
                    "kalite": q.get('quality', 'clean'),
                    "kaynak": q.get('original_file', 'osym_clean'),
                }
            )
            stats['inserted'] += 1

        except Exception as e:
            print(f"[ERROR] Soru eklenemedi {q['question_id']}: {e}")
            stats['errors'] += 1

    await session.commit()
    return stats


async def main():
    """Main entry point."""
    print("=" * 60)
    print("Clean Questions Database Import")
    print("=" * 60)

    # Load clean questions
    if not CLEAN_QUESTIONS_FILE.exists():
        print(f"[ERROR] {CLEAN_QUESTIONS_FILE} bulunamadı!")
        print("Önce repair_osym_questions.py çalıştırın.")
        return

    with open(CLEAN_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"[OK] {len(questions)} temiz soru yüklendi")

    # Connect to database
    try:
        db_url = await get_database_url()
        print(f"[CONNECTING] {db_url.split('@')[1] if '@' in db_url else db_url}")

        engine = create_async_engine(db_url, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Create table if needed
            await create_sorular_table(session)

            # Import questions
            stats = await import_questions(session, questions)

            print("\n" + "=" * 60)
            print("SONUÇLAR")
            print("=" * 60)
            print(f"Toplam: {stats['total']}")
            print(f"Eklenen: {stats['inserted']}")
            print(f"Atlanan (zaten var): {stats['skipped']}")
            print(f"Hata: {stats['errors']}")

            # Verify count
            result = await session.execute(
                text("SELECT COUNT(*) FROM sorular")
            )
            total_in_db = result.scalar()
            print(f"\nVeritabanında toplam soru: {total_in_db}")

        await engine.dispose()
        print("\n[OK] İşlem tamamlandı")

    except Exception as e:
        print(f"[ERROR] Veritabanı bağlantı hatası: {e}")
        print("\nNot: PostgreSQL'in çalıştığından emin olun:")
        print("  docker-compose up -d postgres")
        return


if __name__ == '__main__':
    asyncio.run(main())
