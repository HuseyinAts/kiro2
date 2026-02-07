"""
Import ÖSYM Questions to Database
Loads extracted ÖSYM questions into PostgreSQL database
"""
import asyncio
import asyncpg
import json
from pathlib import Path
import sys
from typing import Dict
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
import re


class OSYMDatabaseImporter:
    """Import ÖSYM questions to database"""

    def __init__(self):
        self.conn = None
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def parse_database_url(self, url: str) -> Dict[str, any]:
        """Parse PostgreSQL connection URL"""
        # Format: postgresql+asyncpg://user:password@host:port/database
        pattern = r"postgresql\+?.*://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
        match = re.match(pattern, url)

        if match:
            return {
                "user": match.group(1),
                "password": match.group(2),
                "host": match.group(3),
                "port": int(match.group(4)),
                "database": match.group(5),
            }
        return {}

    async def connect(self):
        """Connect to database"""
        db_config = self.parse_database_url(settings.database_url)

        print(f"Connecting to database: {db_config.get('database', 'unknown')}")

        self.conn = await asyncpg.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"],
        )

        print("[OK] Connected to database\n")

    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            print("\n[OK] Database connection closed")

    async def check_existing_question(self, stem: str, year: int) -> bool:
        """Check if question already exists in database"""
        query = """
            SELECT question_id FROM questions
            WHERE stem = $1 AND year = $2 AND source = 'ÖSYM'
            LIMIT 1
        """
        result = await self.conn.fetchval(query, stem, year)
        return result is not None

    async def import_question(self, question: Dict) -> bool:
        """Import a single question to database"""

        try:
            # Check if already exists
            if await self.check_existing_question(question["stem"], question["year"]):
                self.skipped_count += 1
                return False

            # Insert question
            query = """
                INSERT INTO questions (
                    subject, topic, subtopic, difficulty, exam_type,
                    stem, options, correct_answer, explanation,
                    bloom_level, source, year, status, quality_score,
                    created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                RETURNING question_id
            """

            question_id = await self.conn.fetchval(
                query,
                question["subject"],
                question["topic"],
                question.get("subtopic"),
                question["difficulty"],
                question["exam_type"],
                question["stem"],
                json.dumps(question["options"], ensure_ascii=False),
                question.get("correct_answer"),
                question.get("explanation"),
                question.get("bloom_level"),
                question["source"],
                question.get("year"),
                question["status"],
                question.get("quality_score", 10.0),
                datetime.now(),
                datetime.now(),
            )

            self.imported_count += 1
            return True

        except Exception as e:
            self.error_count += 1
            print(f"[ERROR] Error importing question: {str(e)[:100]}")
            return False

    async def import_from_json(self, json_path: str):
        """Import questions from extracted JSON file"""

        print(f"{'='*80}")
        print(f"Importing ÖSYM Questions from: {json_path}")
        print(f"{'='*80}\n")

        # Load JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        questions = data.get("questions", [])

        print(f"Exam Type: {metadata.get('exam_type')}")
        print(f"Year: {metadata.get('year')}")
        print(f"Total Questions: {len(questions)}")
        print()

        # Import each question
        print("Importing questions...")
        for i, q in enumerate(questions, 1):
            # Convert to database format
            db_question = {
                "subject": q["subject"],
                "topic": q["subject"],
                "subtopic": None,
                "difficulty": "orta",  # Default ÖSYM difficulty
                "exam_type": q["exam_type"],
                "stem": q["stem"],
                "options": q["options"],
                "correct_answer": q.get("correct_answer"),
                "explanation": None,
                "bloom_level": None,
                "source": "ÖSYM",
                "year": q.get("year"),
                "status": "active",
                "quality_score": 10.0,
            }

            success = await self.import_question(db_question)

            if i % 10 == 0:
                print(f"  Processed {i}/{len(questions)} questions...")

        print(f"\n{'='*80}")
        print("Import Complete!")
        print(f"{'='*80}")
        print(f"[OK] Imported: {self.imported_count}")
        print(f"[SKIP] Skipped (duplicates): {self.skipped_count}")
        print(f"[ERROR] Errors: {self.error_count}")
        print(f"{'='*80}\n")

    async def get_statistics(self):
        """Get database statistics"""
        print("\nDatabase Statistics:")
        print("-" * 40)

        # Total ÖSYM questions
        total = await self.conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE source = 'ÖSYM'"
        )
        print(f"Total ÖSYM Questions: {total}")

        # By exam type
        by_exam = await self.conn.fetch(
            "SELECT exam_type, COUNT(*) as count FROM questions WHERE source = 'ÖSYM' GROUP BY exam_type"
        )
        print("\nBy Exam Type:")
        for row in by_exam:
            print(f"  {row['exam_type']}: {row['count']}")

        # By subject
        by_subject = await self.conn.fetch(
            "SELECT subject, COUNT(*) as count FROM questions WHERE source = 'ÖSYM' GROUP BY subject ORDER BY count DESC"
        )
        print("\nBy Subject:")
        for row in by_subject:
            print(f"  {row['subject']}: {row['count']}")

        # By year
        by_year = await self.conn.fetch(
            "SELECT year, COUNT(*) as count FROM questions WHERE source = 'ÖSYM' AND year IS NOT NULL GROUP BY year ORDER BY year DESC"
        )
        print("\nBy Year:")
        for row in by_year:
            print(f"  {row['year']}: {row['count']}")


async def main():
    """Main import function"""

    importer = OSYMDatabaseImporter()

    try:
        await importer.connect()

        # Import TYT 2024
        json_path = "C:/Users/husey/kiro2/backend/osym_tyt_2024_extracted.json"

        if Path(json_path).exists():
            await importer.import_from_json(json_path)
            await importer.get_statistics()
        else:
            print(f"Error: JSON file not found at {json_path}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await importer.close()


if __name__ == "__main__":
    asyncio.run(main())
