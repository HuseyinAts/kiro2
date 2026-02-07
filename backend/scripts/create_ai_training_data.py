"""
Create AI Training Data from ÖSYM Questions
Formats ÖSYM questions for AI fine-tuning and prompt engineering
"""
import asyncio
import asyncpg
import json
from pathlib import Path
import sys
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
import re


class AITrainingDataGenerator:
    """Generate AI training data from ÖSYM questions"""

    def __init__(self):
        self.conn = None
        self.output_dir = Path("C:/Users/husey/kiro2/backend/ai_training_data")
        self.output_dir.mkdir(exist_ok=True)

    def parse_database_url(self, url: str) -> Dict[str, any]:
        """Parse PostgreSQL connection URL"""
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

    async def fetch_osym_questions(self) -> List[Dict]:
        """Fetch all ÖSYM questions from database"""

        query = """
            SELECT
                question_id, subject, topic, difficulty, exam_type,
                stem, options, correct_answer, year
            FROM questions
            WHERE source = 'ÖSYM'
            ORDER BY year DESC, subject, question_id
        """

        rows = await self.conn.fetch(query)

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
                }
            )

        print(f"Fetched {len(questions)} ÖSYM questions\n")
        return questions

    def create_openai_format(self, questions: List[Dict]) -> List[Dict]:
        """
        Create OpenAI fine-tuning format (JSONL)
        Format: {"messages": [{"role": "system"}, {"role": "user"}, {"role": "assistant"}]}
        """

        training_data = []

        system_prompt = """Sen OSYM formatinda Turkce sinav sorulari olusturan bir uzmansin.
Sorular TYT/AYT formatinda olmali, Bloom taksonomisine uygun, kazanim odakli olmalidir.
Her soru 5 secenekli (A-E) ve tek dogru cevapli olmalidir."""

        for q in questions:
            if not q["correct_answer"]:  # Skip questions without answers
                continue

            # Format options for display
            options_text = "\n".join(
                [f"{key}) {value}" for key, value in q["options"].items()]
            )

            # User prompt (request to generate a similar question)
            user_prompt = f"""Konu: {q['subject']}
Zorluk: {q['difficulty']}
Sinav: {q['exam_type']}

Yukaridaki ozelliklere uygun bir soru olustur."""

            # Assistant response (the actual OSYM question)
            assistant_response = f"""{q['stem']}

{options_text}

Dogru Cevap: {q['correct_answer']}"""

            training_data.append(
                {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": assistant_response},
                    ],
                    "metadata": {
                        "source": "OSYM",
                        "year": q["year"],
                        "exam_type": q["exam_type"],
                        "subject": q["subject"],
                    },
                }
            )

        return training_data

    def save_training_data(self, questions: List[Dict]):
        """Save training data in multiple formats"""

        print("\n" + "=" * 80)
        print("Generating AI Training Data")
        print("=" * 80 + "\n")

        # 1. OpenAI Format (JSONL)
        openai_data = self.create_openai_format(questions)
        openai_file = self.output_dir / "osym_openai_format.jsonl"

        with open(openai_file, "w", encoding="utf-8") as f:
            for item in openai_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"[OK] OpenAI format: {openai_file}")
        print(f"    {len(openai_data)} training examples")

        # 2. Raw JSON (for other uses)
        raw_file = self.output_dir / "osym_questions_raw.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        print(f"[OK] Raw JSON: {raw_file}")
        print(f"    {len(questions)} questions")

        # 3. Subject-specific datasets
        by_subject = {}
        for q in questions:
            subject = q["subject"]
            if subject not in by_subject:
                by_subject[subject] = []
            by_subject[subject].append(q)

        print("\n[OK] Subject-specific datasets:")
        for subject, subject_questions in by_subject.items():
            subject_file = (
                self.output_dir / f"osym_{subject.lower().replace(' ', '_')}.json"
            )
            with open(subject_file, "w", encoding="utf-8") as f:
                json.dump(subject_questions, f, indent=2, ensure_ascii=False)
            print(
                f"    {subject}: {len(subject_questions)} questions -> {subject_file.name}"
            )

        print(f"\n{'='*80}")
        print("Training data generation complete!")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*80}\n")

    async def run(self):
        """Main execution"""
        await self.connect()

        # Fetch questions
        questions = await self.fetch_osym_questions()

        if questions:
            # Generate training data
            self.save_training_data(questions)
        else:
            print("[WARN] No OSYM questions found in database!")

        await self.close()


async def main():
    """Main entry point"""
    generator = AITrainingDataGenerator()
    await generator.run()


if __name__ == "__main__":
    asyncio.run(main())
