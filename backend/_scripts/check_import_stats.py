"""
Check Database Statistics After PDF Import
"""
import asyncpg
import asyncio


async def check_import_stats():
    """Check statistics after Wave 2A PDF import"""

    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="changeme_strong_password_here",
        database="turkiye_sinav_db",
    )

    try:
        print("=" * 80)
        print("DATABASE STATISTICS - AFTER PDF IMPORT (WAVE 2A)")
        print("=" * 80)
        print()

        # Total ÖSYM questions
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE source = 'ÖSYM'"
        )
        print(f"Total ÖSYM Questions: {total:,}")

        # With answers
        with_answers = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE source = 'ÖSYM' AND correct_answer IS NOT NULL"
        )
        pct = with_answers * 100.0 / total if total > 0 else 0
        print(f"With Answers: {with_answers:,} ({pct:.1f}%)")
        print()

        print("-" * 80)
        print("SUBJECT BREAKDOWN")
        print("-" * 80)
        print(
            f"{'Subject':<20} {'Total':<10} {'Answered':<12} {'Coverage':<10} {'Avg Length'}"
        )
        print("-" * 80)

        # Subject breakdown
        subjects = await conn.fetch(
            """
            SELECT
                subject,
                COUNT(*) as total,
                COUNT(correct_answer) as with_answer,
                AVG(LENGTH(stem))::int as avg_length
            FROM questions
            WHERE source = 'ÖSYM'
            GROUP BY subject
            ORDER BY total DESC
        """
        )

        for row in subjects:
            coverage = (
                row["with_answer"] * 100.0 / row["total"] if row["total"] > 0 else 0
            )
            print(
                f"{row['subject']:<20} {row['total']:<10} {row['with_answer']:<12} {coverage:>6.1f}%    {row['avg_length']:>4} chars"
            )

        print()
        print("=" * 80)
        print("MATEMATIK FOCUS (Wave 2A Target)")
        print("=" * 80)

        # Matematik specific
        mat_stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total,
                COUNT(correct_answer) as with_answer,
                AVG(LENGTH(stem))::int as avg_length,
                MIN(LENGTH(stem)) as min_length,
                MAX(LENGTH(stem)) as max_length
            FROM questions
            WHERE source = 'ÖSYM' AND subject = 'Matematik'
        """
        )

        if mat_stats:
            mat_coverage = (
                mat_stats["with_answer"] * 100.0 / mat_stats["total"]
                if mat_stats["total"] > 0
                else 0
            )

            print(f"Total Matematik Questions: {mat_stats['total']:,}")
            print(f"With Answers: {mat_stats['with_answer']:,} ({mat_coverage:.1f}%)")
            print(f"Average Length: {mat_stats['avg_length']} chars")
            print(
                f"Length Range: {mat_stats['min_length']}-{mat_stats['max_length']} chars"
            )
            print()

            # Compare with baseline
            print("COMPARISON WITH BASELINE:")
            print("-" * 40)
            print(f"BEFORE (Research): 330 total, 19 answered (5.8%)")
            print(
                f"AFTER (Wave 2A):   {mat_stats['total']:,} total, {mat_stats['with_answer']:,} answered ({mat_coverage:.1f}%)"
            )

            improvement = mat_coverage - 5.8
            print(f"\nIMPROVEMENT: +{improvement:.1f} percentage points")

            if mat_coverage >= 50:
                print("\n[SUCCESS] Target reached! Coverage >= 50%")
            elif mat_coverage >= 30:
                print("\n[GOOD] Significant improvement, but below 50% target")
            else:
                print("\n[WARN] Coverage still low, may need more data")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(check_import_stats())
