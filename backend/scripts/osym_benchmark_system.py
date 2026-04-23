"""
ÖSYM Benchmark System
Compare AI-generated questions with ÖSYM gold standard questions
"""
import asyncio
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).parent.parent))

import re

from core.config import settings


class OSYMBenchmarkSystem:
    """Benchmark AI questions against ÖSYM standards"""

    def __init__(self):
        self.conn = None
        self.output_dir = Path("C:/Users/husey/kiro2/backend/benchmark_reports")
        self.output_dir.mkdir(exist_ok=True)

    def parse_database_url(self, url: str) -> dict[str, any]:
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

    async def fetch_questions_by_source(self, source: str) -> list[dict]:
        """Fetch questions by source"""

        query = """
            SELECT
                question_id, subject, topic, difficulty, exam_type,
                stem, options, correct_answer, year, quality_score,
                created_at
            FROM questions
            WHERE source = $1
            ORDER BY subject, created_at DESC
        """

        rows = await self.conn.fetch(query, source)

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
                    else None,
                    "created_at": row["created_at"].isoformat()
                    if row["created_at"]
                    else None,
                }
            )

        return questions

    def calculate_question_metrics(self, question: dict) -> dict:
        """Calculate quality metrics for a question"""

        metrics = {
            "stem_length": len(question["stem"]),
            "stem_word_count": len(question["stem"].split()),
            "options_count": len(question["options"]),
            "avg_option_length": statistics.mean(
                [len(opt) for opt in question["options"].values()]
            )
            if question["options"]
            else 0,
            "has_correct_answer": question["correct_answer"] is not None,
            "quality_score": question.get("quality_score", 0),
        }

        return metrics

    def compare_datasets(
        self, osym_questions: list[dict], ai_questions: list[dict]
    ) -> dict:
        """Compare ÖSYM and AI question datasets"""

        print("\n" + "=" * 80)
        print("BENCHMARK ANALYSIS: ÖSYM vs AI Questions")
        print("=" * 80 + "\n")

        comparison = {
            "osym": {
                "total": len(osym_questions),
                "by_subject": {},
                "by_difficulty": {},
                "by_exam_type": {},
                "metrics": {
                    "avg_stem_length": 0,
                    "avg_word_count": 0,
                    "with_answers": 0,
                },
            },
            "ai": {
                "total": len(ai_questions),
                "by_subject": {},
                "by_difficulty": {},
                "by_exam_type": {},
                "metrics": {
                    "avg_stem_length": 0,
                    "avg_word_count": 0,
                    "with_answers": 0,
                },
            },
        }

        # Analyze ÖSYM questions
        osym_stem_lengths = []
        osym_word_counts = []

        for q in osym_questions:
            # Subject distribution
            subject = q["subject"]
            comparison["osym"]["by_subject"][subject] = (
                comparison["osym"]["by_subject"].get(subject, 0) + 1
            )

            # Difficulty distribution
            diff = q["difficulty"]
            comparison["osym"]["by_difficulty"][diff] = (
                comparison["osym"]["by_difficulty"].get(diff, 0) + 1
            )

            # Exam type distribution
            exam = q["exam_type"]
            comparison["osym"]["by_exam_type"][exam] = (
                comparison["osym"]["by_exam_type"].get(exam, 0) + 1
            )

            # Metrics
            metrics = self.calculate_question_metrics(q)
            osym_stem_lengths.append(metrics["stem_length"])
            osym_word_counts.append(metrics["stem_word_count"])

            if metrics["has_correct_answer"]:
                comparison["osym"]["metrics"]["with_answers"] += 1

        if osym_stem_lengths:
            comparison["osym"]["metrics"]["avg_stem_length"] = statistics.mean(
                osym_stem_lengths
            )
            comparison["osym"]["metrics"]["avg_word_count"] = statistics.mean(
                osym_word_counts
            )

        # Analyze AI questions
        ai_stem_lengths = []
        ai_word_counts = []

        for q in ai_questions:
            # Subject distribution
            subject = q["subject"]
            comparison["ai"]["by_subject"][subject] = (
                comparison["ai"]["by_subject"].get(subject, 0) + 1
            )

            # Difficulty distribution
            diff = q["difficulty"]
            comparison["ai"]["by_difficulty"][diff] = (
                comparison["ai"]["by_difficulty"].get(diff, 0) + 1
            )

            # Exam type distribution
            exam = q["exam_type"]
            comparison["ai"]["by_exam_type"][exam] = (
                comparison["ai"]["by_exam_type"].get(exam, 0) + 1
            )

            # Metrics
            metrics = self.calculate_question_metrics(q)
            ai_stem_lengths.append(metrics["stem_length"])
            ai_word_counts.append(metrics["stem_word_count"])

            if metrics["has_correct_answer"]:
                comparison["ai"]["metrics"]["with_answers"] += 1

        if ai_stem_lengths:
            comparison["ai"]["metrics"]["avg_stem_length"] = statistics.mean(
                ai_stem_lengths
            )
            comparison["ai"]["metrics"]["avg_word_count"] = statistics.mean(
                ai_word_counts
            )

        return comparison

    def print_comparison_report(self, comparison: dict):
        """Print formatted comparison report"""

        print("\n" + "=" * 80)
        print("BENCHMARK REPORT")
        print("=" * 80 + "\n")

        # Overall Statistics
        print("OVERALL STATISTICS")
        print("-" * 80)
        print(f"{'Source':<15} {'Total Questions':<20} {'With Answers':<20}")
        print("-" * 80)
        print(
            f"{'ÖSYM':<15} {comparison['osym']['total']:<20} {comparison['osym']['metrics']['with_answers']:<20}"
        )
        print(
            f"{'AI':<15} {comparison['ai']['total']:<20} {comparison['ai']['metrics']['with_answers']:<20}"
        )

        # Subject Distribution
        print("\n\nSUBJECT DISTRIBUTION")
        print("-" * 80)
        print(f"{'Subject':<25} {'ÖSYM':<15} {'AI':<15}")
        print("-" * 80)

        all_subjects = set(comparison["osym"]["by_subject"].keys()) | set(
            comparison["ai"]["by_subject"].keys()
        )
        for subject in sorted(all_subjects):
            osym_count = comparison["osym"]["by_subject"].get(subject, 0)
            ai_count = comparison["ai"]["by_subject"].get(subject, 0)
            print(f"{subject:<25} {osym_count:<15} {ai_count:<15}")

        # Quality Metrics
        print("\n\nQUALITY METRICS")
        print("-" * 80)
        print(f"{'Metric':<30} {'ÖSYM':<20} {'AI':<20}")
        print("-" * 80)
        print(
            f"{'Avg Stem Length (chars)':<30} {comparison['osym']['metrics']['avg_stem_length']:<20.1f} {comparison['ai']['metrics']['avg_stem_length']:<20.1f}"
        )
        print(
            f"{'Avg Word Count':<30} {comparison['osym']['metrics']['avg_word_count']:<20.1f} {comparison['ai']['metrics']['avg_word_count']:<20.1f}"
        )

        # Difficulty Distribution
        print("\n\nDIFFICULTY DISTRIBUTION")
        print("-" * 80)
        print(f"{'Difficulty':<25} {'ÖSYM':<15} {'AI':<15}")
        print("-" * 80)

        all_difficulties = set(comparison["osym"]["by_difficulty"].keys()) | set(
            comparison["ai"]["by_difficulty"].keys()
        )
        for diff in sorted(all_difficulties):
            osym_count = comparison["osym"]["by_difficulty"].get(diff, 0)
            ai_count = comparison["ai"]["by_difficulty"].get(diff, 0)
            print(f"{diff:<25} {osym_count:<15} {ai_count:<15}")

        print("\n" + "=" * 80 + "\n")

    def save_benchmark_report(self, comparison: dict):
        """Save benchmark report to JSON"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"benchmark_report_{timestamp}.json"

        report = {
            "generated_at": datetime.now().isoformat(),
            "comparison": comparison,
            "summary": {
                "osym_questions": comparison["osym"]["total"],
                "ai_questions": comparison["ai"]["total"],
                "osym_with_answers": comparison["osym"]["metrics"]["with_answers"],
                "ai_with_answers": comparison["ai"]["metrics"]["with_answers"],
            },
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"[OK] Benchmark report saved: {report_file}")

    async def run(self):
        """Main execution"""

        await self.connect()

        # Fetch ÖSYM questions
        print("Fetching ÖSYM questions...")
        osym_questions = await self.fetch_questions_by_source("ÖSYM")
        print(f"[OK] Found {len(osym_questions)} ÖSYM questions\n")

        # Fetch AI questions (non-ÖSYM)
        print("Fetching AI-generated questions...")
        all_questions = await self.conn.fetch(
            "SELECT DISTINCT source FROM questions WHERE source != 'ÖSYM'"
        )
        ai_sources = [row["source"] for row in all_questions]

        ai_questions = []
        for source in ai_sources:
            questions = await self.fetch_questions_by_source(source)
            ai_questions.extend(questions)

        print(
            f"[OK] Found {len(ai_questions)} AI-generated questions from {len(ai_sources)} sources\n"
        )

        if not osym_questions:
            print("[WARN] No ÖSYM questions found! Import ÖSYM PDFs first.")
            await self.close()
            return

        # Compare datasets
        comparison = self.compare_datasets(osym_questions, ai_questions)

        # Print and save report
        self.print_comparison_report(comparison)
        self.save_benchmark_report(comparison)

        await self.close()


async def main():
    """Main entry point"""
    benchmark = OSYMBenchmarkSystem()
    await benchmark.run()


if __name__ == "__main__":
    asyncio.run(main())
